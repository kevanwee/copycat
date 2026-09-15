"""Three-valued evidence triage. Scores never establish legal requirements."""
from dataclasses import dataclass, field
from typing import Any
from app.services.legal.intake import Assessment, LegalIntake


@dataclass(slots=True)
class LegalNodeResult:
    node_id: str
    phase: str
    answer: str
    prompt: str
    explanation: str
    evidence_needed: str
    basis: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    legal_refs: list[str] = field(default_factory=list)


def all_answers(answers: list[str]) -> str:
    if "no" in answers:
        return "no"
    return "yes" if answers and all(a == "yes" for a in answers) else "unknown"


def evaluate_rulepack(rulepack: dict[str, Any], facts: dict[str, Any]) -> tuple[list[LegalNodeResult], dict[str, str]]:
    intake = LegalIntake.model_validate(facts)
    nodes, answers = [], {}
    for q in rulepack["questions"]:
        assessment = intake.assessments.get(q["id"], Assessment())
        answer, explanation = assessment.answer, q["explanation"]
        if q["id"] == "fair_use" and answer == "yes":
            f = intake.fair_use_factors
            complete = all(getattr(f, k).strip() for k in ("purpose", "nature", "amount", "market"))
            ack_ok = f.context == "other" or (bool(f.acknowledgment_basis.strip()) and (
                f.acknowledgment == "sufficient" or (f.context == "news" and f.acknowledgment == "impossible")))
            if not complete or not ack_ok:
                answer = "unknown"
                explanation += " Complete all four factors and any required acknowledgment basis before relying on the supplied conclusion."
        answers[q["id"]] = answer
        nodes.append(LegalNodeResult(
            node_id=q["id"], phase=q["phase"], answer=answer, prompt=q["prompt"],
            explanation=explanation, evidence_needed=q["evidence_needed"], basis=assessment.basis,
            evidence_refs=[f"intake.assessments.{q['id']}"] if assessment.basis else [], legal_refs=q["legal_refs"]))
    return nodes, answers


def assess_outcome(rulepack: dict, intake: dict, answers: dict[str, str]) -> dict:
    facts = LegalIntake.model_validate(intake)
    scope = []
    if facts.work_category not in rulepack["supported_categories"]:
        scope.append("Identify the protected work category; other categories need a separate rights analysis.")
    if facts.claim_route != "direct":
        scope.append("Authorisation and secondary infringement require separate review of conduct, control and statutory conditions.")
    if facts.conduct_date is None:
        scope.append("Supply the alleged conduct date to check which law applies.")
    elif facts.conduct_date.isoformat() < "2021-11-21" or facts.conduct_date.isoformat() > rulepack["reviewed_on"]:
        scope.append("The conduct date falls outside the reviewed legal period; check the law at that date.")
    if facts.work_category == "film":
        scope.append("Film copyright only: assess soundtrack, script, music, artistic works and performance rights separately.")
    core = rulepack["core_requirements"]
    missing = [k for k in core if answers[k] == "unknown"]
    contrary = [k for k in core if answers[k] == "no"]
    exceptions = [k for k in ("fair_use", "other_exception") if answers[k] != "no"]
    if any(not s.startswith("Film copyright only") for s in scope):
        status, title = "scope_review", "Scope needs review"
    elif contrary:
        status, title = "not_established", "Required limbs not established"
    elif answers["independent_creation"] == "yes" or any(answers[k] == "yes" for k in exceptions):
        status, title = "review_required", "Competing evidence or exception needs review"
    elif missing or exceptions or answers["independent_creation"] == "unknown":
        status, title = "incomplete", "More evidence needed"
    else:
        status, title = "supported", "Prima facie limbs supported by supplied assessments"
    return dict(status=status, title=title,
        summary="This evaluates your recorded assessments, not an independent finding of infringement. Technical similarity does not decide copying, substantiality or fair use.",
        missing_requirements=missing, contrary_requirements=contrary, exception_review=exceptions, scope_notes=scope,
        answered_questions=sum(v != "unknown" for v in answers.values()), total_questions=len(answers))
