from datetime import UTC, datetime
from pathlib import Path
import shutil
from app.core.config import get_settings
from app.db.models import Case, SimilarityMetric
from app.services.access import expires_at


def delete_case_data(db, case):
    s = get_settings()
    for root in (s.storage_root, s.report_root):
        target = (root / case.id).resolve()
        if target.parent != root.resolve():
            raise ValueError("Unsafe storage path")
        if target.exists():
            shutil.rmtree(target)
    (s.report_root / f"{case.id}.pdf").unlink(missing_ok=True)
    db.query(SimilarityMetric).filter_by(case_id=case.id).delete()
    db.delete(case)
    db.commit()


def cleanup_expired(db):
    count = 0
    for case in db.query(Case).all():
        # Workers own running files. Expired cases are already inaccessible.
        if case.status not in {"queued", "running", "uploading"} and expires_at(case) <= datetime.now(UTC):
            delete_case_data(db, case)
            count += 1
    return count
