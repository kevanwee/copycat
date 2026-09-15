from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.db.models import Case, Job
from app.db.session import SessionLocal
from app.services.pipeline import analyze_case_job


@celery_app.task(name="app.tasks.analyze_case.run_case_analysis")
def run_case_analysis(*, case_id: str, job_id: str) -> dict:
    db = SessionLocal()
    try:
        return analyze_case_job(db, case_id=case_id, job_id=job_id)
    except Exception as exc:
        logging.getLogger(__name__).error("Analysis failed for job %s (%s)", job_id, type(exc).__name__)
        db.rollback()
        message = str(exc) if isinstance(exc, ValueError) else "Analysis could not complete. Check the files and retry; contact the operator if it persists."
        job = db.query(Job).filter(Job.id == job_id).first()
        if job is not None:
            job.status = "failed"
            job.stage = "failed"
            job.error = message[:500]
            db.add(job)

        case = db.query(Case).filter(Case.id == case_id).first()
        if case is not None:
            case.status = "failed"
            db.add(case)

        db.commit()
        return {"error": message[:500], "case_id": case_id, "job_id": job_id}
    finally:
        db.close()
