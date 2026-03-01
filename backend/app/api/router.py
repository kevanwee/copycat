from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.cases import router as cases_router
from app.api.routes.jobs import router as jobs_router

api_router = APIRouter()
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])