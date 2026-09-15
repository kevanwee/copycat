from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
from importlib.metadata import version, PackageNotFoundError
from app.core.config import get_settings


def fingerprint(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build_report_payload(case, artifacts, media_type, similarity, legal_nodes, outcome, rulepack):
    settings = get_settings()
    sources = [dict(role=a.role, filename=a.filename, sha256=a.checksum_sha256, size_bytes=a.size_bytes)
               for a in sorted(artifacts, key=lambda a: a.role)]
    dependencies = {}
    for package in ("pypdf", "python-docx", "Pillow", "numpy", "opencv-python-headless", "scikit-image", "ImageHash"):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = "unavailable"
    content = dict(schema_version="2.0", jurisdiction=case.jurisdiction, media_type=media_type,
        intake=case.metadata_json.get("intake", {}), artifacts=sources,
        similarity=similarity, legal_flow=[asdict(n) for n in legal_nodes], assessment=outcome,
        scoring_version=settings.scoring_version, rule_pack_version=rulepack["version"],
        rule_pack_id=rulepack["rule_pack_id"], rule_pack_sha256=fingerprint(rulepack), dependencies=dependencies)
    report = dict(content, report_id=fingerprint(content), generated_at=datetime.now(UTC).isoformat(), case_id=case.id,
        headline_overlap_percentage=round(similarity["headline_score"] * 100, 2),
        headline_score=similarity["headline_score"], component_scores=similarity["component_scores"],
        evidence=similarity.get("evidence", {}), citations=rulepack["citations"],
        legal_reviewed_on=rulepack["reviewed_on"], source_status=rulepack["source_status"],
        disclaimers=["Triage aid. User assessments and evidence references have not been independently verified.",
            "Similarity is an algorithmic index, not the percentage copied or the probability of infringement.",
            "Report identity covers input roles, names, facts, methods, dependency versions and outputs; case ID and generation time are excluded.",
            f"Case access expires {settings.retention_hours} hours after creation; active-service cleanup deletes source files, derived files and reports."])
    return report
