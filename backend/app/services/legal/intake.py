"""User assessments are never inferred from similarity."""

from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: Literal["yes", "no", "unknown"] = "unknown"
    basis: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def require_basis(self):
        self.basis = self.basis.strip()
        if self.answer != "unknown" and not self.basis:
            raise ValueError(
                "An explanation or evidence reference is required for yes/no answers"
            )
        return self


class FairUseFactors(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: str = Field(default="", max_length=4000)
    nature: str = Field(default="", max_length=4000)
    amount: str = Field(default="", max_length=4000)
    market: str = Field(default="", max_length=4000)
    context: Literal["other", "news", "criticism_review"] = "other"
    acknowledgment: Literal["unknown", "sufficient", "impossible", "absent"] = "unknown"
    acknowledgment_basis: str = Field(default="", max_length=4000)


class LegalIntake(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="Untitled comparison", max_length=160)
    work_category: Literal[
        "unknown", "literary", "dramatic", "musical", "artistic", "film", "other"
    ] = "unknown"
    claim_route: Literal["direct", "authorisation", "secondary", "unknown"] = "direct"
    conduct_date: date | None = None
    assessments: dict[str, Assessment] = Field(default_factory=dict, max_length=30)
    fair_use_factors: FairUseFactors = Field(default_factory=FairUseFactors)

    @model_validator(mode="after")
    def validate_questions(self):
        from app.services.legal.rulepack_loader import load_rulepack

        allowed = {q["id"] for q in load_rulepack("sg_v2")["questions"]}
        if set(self.assessments) - allowed:
            raise ValueError("Unrecognised assessment question")
        return self
