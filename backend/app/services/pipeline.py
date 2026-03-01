from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Artifact, Case, CaseReport, Job, SimilarityMetric
from app.services.extraction.text import extract_text
from app.services.extraction.video import extract_video, probe_duration_seconds
from app.services.legal.engine import compute_risk_band, evaluate_rulepack
from app.services.legal.rulepack_loader import load_rulepack
from app.services.reports.builder import build_report_payload
from app.services.reports.pdf_renderer import render_report_pdf
from app.services.similarity.text_similarity import compute_text_similarity
from app.services.similarity.video_similarity import compute_video_similarity


settings = get_settings()


def _update_job(db: Session, job: Job, *, status: str, stage: str, progress: float, error: str | None = None) -> None:
    job.status = status
    job.stage = stage
    job.progress = progress
    job.error = error
    db.add(job)
    db.commit()
    db.refresh(job)


def _artifact_by_role(artifacts: list[Artifact], role: str) -> Artifact:
    for artifact in artifacts:
        if artifact.role == role:
            return artifact
    raise ValueError(f"Missing artifact role={role}")


def _validate_pair(artifacts: list[Artifact]) -> str:
    if len(artifacts) != 2:
        raise ValueError("Exactly two artifacts are required (original and alleged).")

    roles = {a.role for a in artifacts}
    if roles != {"original", "alleged"}:
        raise ValueError("Artifacts must include one original and one alleged file.")

    media_types = {a.media_type for a in artifacts}
    if len(media_types) != 1:
        raise ValueError("Cross-medium comparisons are not supported in v1.")

    media_type = next(iter(media_types))
    if media_type not in {"text", "video"}:
        raise ValueError(f"Unsupported media_type={media_type}")

    return media_type


def _upsert_metric(db: Session, case_id: str, metric_code: str, score: float, payload: dict) -> None:
    existing = db.query(SimilarityMetric).filter(SimilarityMetric.case_id == case_id, SimilarityMetric.metric_code == metric_code).first()
    if existing is None:
        existing = SimilarityMetric(case_id=case_id, metric_code=metric_code, score=score, component_payload=payload)
    else:
        existing.score = score
        existing.component_payload = payload
    db.add(existing)


def analyze_case_job(db: Session, *, case_id: str, job_id: str) -> dict:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise ValueError(f"Case not found: {case_id}")

    job = db.query(Job).filter(Job.id == job_id, Job.case_id == case_id).first()
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    artifacts = db.query(Artifact).filter(Artifact.case_id == case_id).order_by(Artifact.created_at.asc()).all()
    media_type = _validate_pair(artifacts)

    _update_job(db, job, status="running", stage="extract", progress=0.1)

    original = _artifact_by_role(artifacts, "original")
    alleged = _artifact_by_role(artifacts, "alleged")

    if media_type == "text":
        original_extraction = extract_text(original.storage_path)
        alleged_extraction = extract_text(alleged.storage_path)

        _update_job(db, job, status="running", stage="score_text", progress=0.4)

        sim = compute_text_similarity(original_extraction.text, alleged_extraction.text)
        similarity_payload = {
            "headline_score": sim.headline_score,
            "component_scores": sim.component_scores,
            "evidence": {
                "matched_passages": sim.matched_passages,
                "languages": {
                    "original": original_extraction.language,
                    "alleged": alleged_extraction.language,
                },
                "lengths": {
                    "original_tokens": sim.normalized_original_length,
                    "alleged_tokens": sim.normalized_alleged_length,
                },
            },
        }

    else:
        if probe_duration_seconds(original.storage_path) > settings.max_video_seconds:
            raise ValueError("Original video exceeds max duration.")
        if probe_duration_seconds(alleged.storage_path) > settings.max_video_seconds:
            raise ValueError("Alleged video exceeds max duration.")

        case_work = settings.report_root / case_id
        original_work = case_work / "original"
        alleged_work = case_work / "alleged"

        original_extraction = extract_video(original.storage_path, original_work)
        alleged_extraction = extract_video(alleged.storage_path, alleged_work)

        _update_job(db, job, status="running", stage="score_video", progress=0.55)

        sim = compute_video_similarity(
            original_frames=original_extraction.frames,
            alleged_frames=alleged_extraction.frames,
            original_transcript=original_extraction.transcript,
            alleged_transcript=alleged_extraction.transcript,
        )

        similarity_payload = {
            "headline_score": sim.headline_score,
            "component_scores": sim.component_scores,
            "evidence": {
                "timeline_matches": sim.timeline_matches,
                "transcript_excerpt_matches": sim.transcript_excerpt_matches,
                "transcript_lengths": {
                    "original_chars": len(original_extraction.transcript),
                    "alleged_chars": len(alleged_extraction.transcript),
                },
            },
        }

    _upsert_metric(
        db,
        case_id=case_id,
        metric_code=f"{media_type.upper()}_COMPOSITE",
        score=similarity_payload["headline_score"],
        payload=similarity_payload,
    )
    db.commit()

    _update_job(db, job, status="running", stage="legal_triage", progress=0.75)

    legal_inputs = dict(case.metadata_json.get("legal_inputs", {})) if isinstance(case.metadata_json, dict) else {}
    legal_facts = {
        "work_category_supported": legal_inputs.get("work_category_supported", True),
        "originality_evidence": legal_inputs.get("originality_evidence", True),
        "fixation_evidence": legal_inputs.get("fixation_evidence", True),
        "sg_connection": legal_inputs.get("sg_connection", case.jurisdiction == "SG"),
        "term_active": legal_inputs.get("term_active", True),
        "ownership_asserted": legal_inputs.get("ownership_asserted", True),
        "acts_covered": legal_inputs.get("acts_covered", True),
        "authorization_present": legal_inputs.get("authorization_present", False),
        "access_evidence": legal_inputs.get("access_evidence", similarity_payload["headline_score"] >= 0.25),
        "similarity_score": similarity_payload["headline_score"],
        "qualitative_importance_flag": legal_inputs.get("qualitative_importance_flag", similarity_payload["headline_score"] >= 0.5),
        "fair_use_indicator": legal_inputs.get("fair_use_indicator", False),
    }

    rulepack = load_rulepack()
    node_results, node_answers = evaluate_rulepack(rulepack=rulepack, facts=legal_facts)
    risk_band = compute_risk_band(node_answers=node_answers, similarity_score=similarity_payload["headline_score"])

    _update_job(db, job, status="running", stage="report", progress=0.9)

    report_payload = build_report_payload(
        case=case,
        artifacts=artifacts,
        media_type=media_type,
        similarity=similarity_payload,
        legal_nodes=node_results,
        risk_band=risk_band,
        rulepack=rulepack,
    )

    stored = db.query(CaseReport).filter(CaseReport.case_id == case_id).first()
    if stored is None:
        stored = CaseReport(case_id=case_id, report_json=report_payload)
    else:
        stored.report_json = report_payload
    db.add(stored)

    pdf_path = settings.report_root / f"{case_id}.pdf"
    render_report_pdf(report_payload, pdf_path)

    case.status = "completed"
    db.add(case)
    db.commit()

    _update_job(db, job, status="completed", stage="completed", progress=1.0)
    return report_payload