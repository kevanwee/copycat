from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    jurisdiction: str = Field(default="SG")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseResponse(BaseModel):
    case_id: str
    jurisdiction: str
    status: str
    created_at: datetime


class ArtifactResponse(BaseModel):
    artifact_id: str
    case_id: str
    role: Literal["original", "alleged"]
    media_type: Literal["text", "video"]
    filename: str
    size_bytes: int


class AnalyzeResponse(BaseModel):
    job_id: str
    case_id: str
    status: str


class JobResponse(BaseModel):
    job_id: str
    case_id: str
    status: str
    progress: float
    stage: str
    error: str | None = None
    updated_at: datetime


class CaseReportResponse(BaseModel):
    case_id: str
    report: dict[str, Any]