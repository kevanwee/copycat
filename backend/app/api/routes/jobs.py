from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Job
from app.db.schemas import JobResponse
from app.db.session import get_db

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.id,
        case_id=job.case_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        error=job.error,
        updated_at=job.updated_at,
    )