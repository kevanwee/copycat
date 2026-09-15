from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import Base, engine, SessionLocal
from app.db.models import Case, Job
from app.services.retention import cleanup_expired

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Local background jobs do not survive a process restart. Make retry possible.
    if settings.celery_task_always_eager:
        with SessionLocal() as db:
            db.query(Job).filter(Job.status.in_(["queued", "running"])).update({"status": "failed", "stage": "failed", "error": "Service restarted. Retry analysis."})
            db.query(Case).filter(Case.status.in_(["queued", "running", "uploading"])).update({"status": "failed"})
            db.commit()

    def cleanup():
        with SessionLocal() as db:
            cleanup_expired(db)

    async def cleanup_loop():
        while True:
            try:
                await asyncio.to_thread(cleanup)
            except Exception:
                logging.getLogger(__name__).error("Case retention cleanup failed; operator action required")
            await asyncio.sleep(settings.cleanup_interval_seconds)

    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[url.strip() for url in settings.frontend_base_url.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def privacy_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
