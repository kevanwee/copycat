from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Artifact, CaseReport
from app.db.session import SessionLocal



def cleanup_expired() -> dict[str, int]:
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(hours=settings.retention_hours)

    db: Session = SessionLocal()
    deleted_artifacts = 0
    deleted_reports = 0

    try:
        artifacts = db.query(Artifact).filter(Artifact.created_at < cutoff).all()
        for artifact in artifacts:
            try:
                Path(artifact.storage_path).unlink(missing_ok=True)
            except Exception:
                pass
            db.delete(artifact)
            deleted_artifacts += 1

        reports = db.query(CaseReport).filter(CaseReport.generated_at < cutoff).all()
        for report in reports:
            pdf_path = settings.report_root / f"{report.case_id}.pdf"
            pdf_path.unlink(missing_ok=True)
            db.delete(report)
            deleted_reports += 1

        db.commit()
    finally:
        db.close()

    return {"deleted_artifacts": deleted_artifacts, "deleted_reports": deleted_reports}


if __name__ == "__main__":
    result = cleanup_expired()
    print(result)