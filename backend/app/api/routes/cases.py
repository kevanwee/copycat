from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Artifact, Case, CaseReport, Job
from app.db.schemas import AnalyzeResponse, ArtifactResponse, CaseCreateRequest, CaseReportResponse, CaseResponse
from app.db.session import get_db
from app.services.extraction.video import probe_duration_seconds
from app.services.storage import LocalStorage
from app.tasks.analyze_case import run_case_analysis
from app.utils_hash import sha256_bytes

router = APIRouter()
settings = get_settings()
storage = LocalStorage()

TEXT_EXTENSIONS = {".txt", ".pdf", ".docx"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}


def _get_case_or_404(db: Session, case_id: str) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("", response_model=CaseResponse)
def create_case(payload: CaseCreateRequest, db: Session = Depends(get_db)) -> CaseResponse:
    jurisdiction = payload.jurisdiction.upper().strip()
    if jurisdiction not in settings.allowed_jurisdictions_list:
        raise HTTPException(status_code=400, detail=f"Unsupported jurisdiction: {jurisdiction}")

    case = Case(jurisdiction=jurisdiction, status="created", metadata_json=payload.metadata)
    db.add(case)
    db.commit()
    db.refresh(case)
    return CaseResponse(case_id=case.id, jurisdiction=case.jurisdiction, status=case.status, created_at=case.created_at)


@router.post("/{case_id}/artifacts", response_model=ArtifactResponse)
async def upload_artifact(
    case_id: str,
    role: str = Form(...),
    media_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ArtifactResponse:
    case = _get_case_or_404(db, case_id)

    role = role.lower().strip()
    media_type = media_type.lower().strip()
    if role not in {"original", "alleged"}:
        raise HTTPException(status_code=400, detail="role must be original or alleged")
    if media_type not in {"text", "video"}:
        raise HTTPException(status_code=400, detail="media_type must be text or video")

    filename = file.filename or "upload.bin"
    suffix = filename.lower().rsplit(".", 1)
    extension = f".{suffix[-1]}" if len(suffix) > 1 else ""

    if media_type == "text" and extension not in TEXT_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported text file extension: {extension}")
    if media_type == "video" and extension not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported video file extension: {extension}")

    content = await file.read()
    size_bytes = len(content)

    max_size_mb = settings.max_text_mb if media_type == "text" else settings.max_video_mb
    if size_bytes > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {max_size_mb}MB for {media_type}.")

    artifact = Artifact(
        case_id=case.id,
        role=role,
        media_type=media_type,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        checksum_sha256=sha256_bytes(content),
        storage_path="",
    )
    db.add(artifact)
    db.flush()

    path = storage.write_artifact(case.id, artifact.id, filename, content)
    artifact.storage_path = str(path)

    if media_type == "video":
        try:
            duration = probe_duration_seconds(path)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to inspect video: {exc}") from exc
        if duration > settings.max_video_seconds:
            raise HTTPException(status_code=400, detail=f"Video too long. Max {settings.max_video_seconds} seconds.")

    existing_same_role = (
        db.query(Artifact)
        .filter(
            Artifact.case_id == case.id,
            Artifact.role == role,
            Artifact.id != artifact.id,
        )
        .all()
    )
    for old in existing_same_role:
        db.delete(old)

    case.status = "artifact_uploaded"
    db.add(case)
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ArtifactResponse(
        artifact_id=artifact.id,
        case_id=case.id,
        role=artifact.role,
        media_type=artifact.media_type,
        filename=artifact.filename,
        size_bytes=artifact.size_bytes,
    )


@router.post("/{case_id}/analyze", response_model=AnalyzeResponse)
def analyze_case(case_id: str, db: Session = Depends(get_db)) -> AnalyzeResponse:
    case = _get_case_or_404(db, case_id)
    artifacts = db.query(Artifact).filter(Artifact.case_id == case.id).all()

    if len(artifacts) != 2:
        raise HTTPException(status_code=400, detail="Exactly two artifacts are required before analysis")

    media_types = {a.media_type for a in artifacts}
    if len(media_types) != 1:
        raise HTTPException(status_code=400, detail="Cross-medium comparisons are not supported")

    job = Job(case_id=case.id, status="queued", stage="queued", progress=0.0)
    case.status = "queued"
    db.add(case)
    db.add(job)
    db.commit()
    db.refresh(job)

    run_case_analysis.delay(case_id=case.id, job_id=job.id)

    return AnalyzeResponse(job_id=job.id, case_id=case.id, status=job.status)


@router.get("/{case_id}/report", response_model=CaseReportResponse)
def get_case_report(case_id: str, db: Session = Depends(get_db)) -> CaseReportResponse:
    _get_case_or_404(db, case_id)
    report = db.query(CaseReport).filter(CaseReport.case_id == case_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not ready")
    return CaseReportResponse(case_id=case_id, report=report.report_json)


@router.get("/{case_id}/report.pdf")
def get_case_report_pdf(case_id: str, db: Session = Depends(get_db)) -> FileResponse:
    _get_case_or_404(db, case_id)
    report = db.query(CaseReport).filter(CaseReport.case_id == case_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not ready")

    pdf_path = settings.report_root / f"{case_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not generated")

    return FileResponse(path=str(pdf_path), filename=f"copycat_report_{case_id}.pdf", media_type="application/pdf")