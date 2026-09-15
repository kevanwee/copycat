from pathlib import Path
import hashlib
import secrets
import io
import zipfile
import logging
import shutil
from starlette.concurrency import run_in_threadpool
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import Artifact, Case, CaseReport, Job, SimilarityMetric
from app.db.schemas import (
    CaseCreateRequest,
    CaseResponse,
    ArtifactResponse,
    AnalyzeResponse,
    CaseReportResponse,
)
from app.db.session import get_db
from app.services.access import require_case, expires_at
from app.services.capabilities import capabilities
from app.services.extraction.video import probe_duration_seconds
from app.services.legal.intake import LegalIntake
from app.services.legal.rulepack_loader import load_rulepack
from app.services.retention import delete_case_data
from app.services.storage import LocalStorage
from app.tasks.analyze_case import run_case_analysis
from app.utils_hash import sha256_bytes

router = APIRouter()
settings = get_settings()
storage = LocalStorage()
BUSY = {"queued", "running", "uploading"}


def claim_mutation(db, case, status):
    changed = db.execute(
        update(Case)
        .where(Case.id == case.id, Case.status.not_in(BUSY))
        .values(status=status)
    ).rowcount
    if not changed:
        db.rollback()
        raise HTTPException(
            409, "Case is busy. Wait for the current operation to finish."
        )
    db.commit()


def invalidate_report(db, case_id):
    db.query(CaseReport).filter_by(case_id=case_id).delete()
    db.query(SimilarityMetric).filter_by(case_id=case_id).delete()
    (settings.report_root / f"{case_id}.pdf").unlink(missing_ok=True)
    derived = (settings.report_root / case_id).resolve()
    if derived.parent != settings.report_root.resolve():
        raise ValueError("Unsafe derived-file path")
    if derived.exists():
        shutil.rmtree(derived)


@router.get("/questionnaire")
def questionnaire():
    return {"rulepack": load_rulepack(), "capabilities": capabilities()}


@router.post("", response_model=CaseResponse)
def create_case(payload: CaseCreateRequest, db: Session = Depends(get_db)):
    if payload.jurisdiction.strip().upper() != "SG":
        raise HTTPException(422, "Only Singapore is supported")
    if payload.metadata:
        raise HTTPException(
            422, "Use typed intake; unvalidated metadata is no longer accepted"
        )
    token = secrets.token_urlsafe(32)
    case = Case(
        jurisdiction="SG",
        status="created",
        metadata_json={
            "intake": payload.intake.model_dump(mode="json"),
            "access_hash": hashlib.sha256(token.encode()).hexdigest(),
        },
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return CaseResponse(
        case_id=case.id,
        jurisdiction="SG",
        status=case.status,
        created_at=case.created_at,
        access_token=token,
    )


@router.get("/{case_id}")
def get_case(
    case_id: str, x_case_token: str | None = Header(None), db: Session = Depends(get_db)
):
    case = require_case(db, case_id, x_case_token)
    job = (
        db.query(Job).filter_by(case_id=case_id).order_by(Job.created_at.desc()).first()
    )
    artifacts = db.query(Artifact).filter_by(case_id=case_id).all()
    return dict(
        case_id=case.id,
        status=case.status,
        intake=case.metadata_json.get("intake", {}),
        expires_at=expires_at(case),
        job_id=job.id if job else None,
        artifacts=[
            dict(
                artifact_id=a.id,
                role=a.role,
                media_type=a.media_type,
                filename=a.filename,
                size_bytes=a.size_bytes,
            )
            for a in artifacts
        ],
    )


@router.put("/{case_id}/intake")
def update_intake(
    case_id: str,
    payload: LegalIntake,
    x_case_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    case = require_case(db, case_id, x_case_token)
    claim_mutation(db, case, "uploading")
    try:
        case.metadata_json = dict(
            case.metadata_json, intake=payload.model_dump(mode="json")
        )
        invalidate_report(db, case_id)
        case.status = "ready"
        db.commit()
    except Exception:
        db.rollback()
        case.status = "failed"
        db.commit()
        raise
    return {"status": "ready"}


def validate_content(content, extension, media_type):
    if not content:
        raise ValueError("Empty files cannot be compared")
    if extension == ".txt":
        text = content.decode("utf-8-sig")
        if "\x00" in text or not text.strip():
            raise ValueError("Upload readable UTF-8 text")
    elif extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("The file is not a PDF")
    elif extension == ".docx":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if (
                "word/document.xml" not in archive.namelist()
                or sum(i.file_size for i in archive.infolist()) > 50 * 1024 * 1024
            ):
                raise ValueError("Invalid or oversized DOCX contents")
    elif media_type == "image":
        from PIL import Image

        with Image.open(io.BytesIO(content)) as image:
            if (
                image.width * image.height > 25_000_000
                or getattr(image, "n_frames", 1) > 1
            ):
                raise ValueError("Use a still image of at most 25 megapixels")
            image.verify()


@router.post("/{case_id}/artifacts", response_model=ArtifactResponse)
async def upload_artifact(
    case_id: str,
    role: str = Form(...),
    media_type: str = Form(...),
    file: UploadFile = File(...),
    x_case_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    case = require_case(db, case_id, x_case_token)
    media = capabilities()["media"].get(media_type)
    if role not in {"original", "alleged"} or not media:
        raise HTTPException(422, "Choose a supported role and media type")
    if not media["available"]:
        raise HTTPException(
            503, "This server does not have the dependencies for this media type"
        )
    filename = Path((file.filename or "").replace("\\", "/")).name[:180]
    extension = Path(filename).suffix.lower()
    if extension not in media["extensions"]:
        raise HTTPException(422, "File extension is not supported for this media type")
    # Multipart spooling is additionally bounded by an ingress limit in deployment.
    content = await file.read(media["max_mb"] * 1024 * 1024 + 1)
    await file.close()
    if len(content) > media["max_mb"] * 1024 * 1024:
        raise HTTPException(413, f"Maximum file size is {media['max_mb']} MB")
    try:
        await run_in_threadpool(validate_content, content, extension, media_type)
    except Exception as exc:
        raise HTTPException(
            422,
            "Invalid file. Use a readable, unencrypted file in the selected format.",
        ) from exc
    claim_mutation(db, case, "uploading")
    path = None
    try:
        artifact = Artifact(
            case_id=case_id,
            role=role,
            media_type=media_type,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            checksum_sha256=sha256_bytes(content),
            storage_path="",
        )
        db.add(artifact)
        db.flush()
        path = storage.write_artifact(
            case_id, artifact.id, "source" + extension, content
        )
        artifact.storage_path = str(path)
        if media_type == "video":
            duration = await run_in_threadpool(probe_duration_seconds, path)
            if not 0 < duration <= settings.max_video_seconds:
                raise ValueError("Video duration outside supported range")
        old = (
            db.query(Artifact)
            .filter(
                Artifact.case_id == case_id,
                Artifact.role == role,
                Artifact.id != artifact.id,
            )
            .all()
        )
        old_paths = [Path(a.storage_path) for a in old]
        for a in old:
            db.delete(a)
        invalidate_report(db, case_id)
        case.status = "ready"
        db.commit()
        for old_path in old_paths:
            try:
                old_path.unlink(missing_ok=True)
            except OSError:
                # The replacement is committed; do not delete the new file on
                # a stale-file cleanup failure. Case expiry will retry cleanup.
                logging.getLogger(__name__).warning(
                    "Old upload cleanup deferred for case %s", case_id
                )
        return ArtifactResponse(
            artifact_id=artifact.id,
            case_id=case_id,
            role=role,
            media_type=media_type,
            filename=filename,
            size_bytes=len(content),
        )
    except Exception as exc:
        db.rollback()
        if path:
            path.unlink(missing_ok=True)
        case.status = "failed"
        db.commit()
        raise HTTPException(
            422,
            "File could not be inspected or stored. Check the format and duration, then retry.",
        ) from exc


@router.post("/{case_id}/analyze", response_model=AnalyzeResponse)
def analyze_case(
    case_id: str,
    background: BackgroundTasks,
    x_case_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    case = require_case(db, case_id, x_case_token)
    artifacts = db.query(Artifact).filter_by(case_id=case_id).all()
    if len(artifacts) != 2 or {a.role for a in artifacts} != {"original", "alleged"}:
        raise HTTPException(422, "Upload one original and one comparison file")
    if len({a.media_type for a in artifacts}) != 1:
        raise HTTPException(422, "Both files must use the same media type")
    if not capabilities()["media"][artifacts[0].media_type]["available"]:
        raise HTTPException(503, "Required media dependencies are unavailable")
    if (
        db.query(Job).filter(Job.status.in_({"queued", "running"})).count()
        >= settings.max_active_jobs
    ):
        raise HTTPException(429, "Analysis capacity is busy. Try again shortly.")
    claim_mutation(db, case, "queued")
    job = Job(case_id=case_id, status="queued", stage="queued", progress=0)
    invalidate_report(db, case_id)
    db.add(job)
    db.commit()
    try:
        if settings.celery_task_always_eager:
            background.add_task(run_case_analysis, case_id=case_id, job_id=job.id)
        else:
            run_case_analysis.delay(case_id=case_id, job_id=job.id)
    except Exception:
        job.status, case.status = "failed", "failed"
        job.error = "Worker unavailable. Retry analysis."
        db.commit()
        raise HTTPException(503, job.error)
    return AnalyzeResponse(job_id=job.id, case_id=case_id, status="queued")


@router.get("/{case_id}/report", response_model=CaseReportResponse)
def get_case_report(
    case_id: str, x_case_token: str | None = Header(None), db: Session = Depends(get_db)
):
    case = require_case(db, case_id, x_case_token)
    report = db.query(CaseReport).filter_by(case_id=case_id).first()
    if not report or case.status != "completed":
        raise HTTPException(
            409, "Report is not ready. Run analysis after your changes."
        )
    return CaseReportResponse(case_id=case_id, report=report.report_json)


@router.get("/{case_id}/report.pdf")
def get_pdf(
    case_id: str, x_case_token: str | None = Header(None), db: Session = Depends(get_db)
):
    get_case_report(case_id, x_case_token, db)
    path = settings.report_root / f"{case_id}.pdf"
    if not path.is_file():
        raise HTTPException(404, "PDF unavailable. Run analysis again.")
    return FileResponse(
        path, filename=f"copycat-{case_id}.pdf", media_type="application/pdf"
    )


@router.get("/{case_id}/preview/{role}")
def image_preview(
    case_id: str,
    role: str,
    x_case_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    get_case_report(case_id, x_case_token, db)
    if role not in {"original", "alleged"}:
        raise HTTPException(404, "Preview not found")
    artifact = (
        db.query(Artifact)
        .filter_by(case_id=case_id, role=role, media_type="image")
        .first()
    )
    if not artifact:
        raise HTTPException(404, "Image preview not found")
    path = (
        settings.report_root
        / case_id
        / role
        / f"{Path(artifact.storage_path).stem}_normalized.png"
    )
    if not path.is_file():
        raise HTTPException(404, "Preview unavailable")
    return FileResponse(path, media_type="image/png")


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: str, x_case_token: str | None = Header(None), db: Session = Depends(get_db)
):
    case = require_case(db, case_id, x_case_token)
    claim_mutation(db, case, "uploading")
    delete_case_data(db, case)
