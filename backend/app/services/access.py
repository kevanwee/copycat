import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from app.core.config import get_settings
from app.db.models import Case


def expires_at(case):
    return case.created_at.replace(tzinfo=UTC) + timedelta(hours=get_settings().retention_hours)


def require_case(db, case_id: str, token: str | None):
    case = db.get(Case, case_id)
    digest = hashlib.sha256((token or "").encode()).hexdigest()
    expected = (case.metadata_json or {}).get("access_hash", "") if case else ""
    if not expected or not secrets.compare_digest(digest, expected):
        raise HTTPException(404, "Case not found or access key incorrect")
    if datetime.now(UTC) >= expires_at(case):
        raise HTTPException(410, "This case has expired. Create a new comparison.")
    return case
