import copy
import pytest
from pydantic import ValidationError
from app.services.legal.engine import all_answers, evaluate_rulepack, assess_outcome
from app.services.legal.intake import LegalIntake
from app.services.legal.rulepack_loader import load_rulepack

PACK = load_rulepack("sg_v2")


def complete_intake():
    answers = {q["id"]: {"answer": "yes" if q["id"] in PACK["core_requirements"] else "no", "basis": "Recorded evidence, exhibit 1"} for q in PACK["questions"]}
    return dict(work_category="literary", conduct_date="2026-09-01", assessments=answers)


def outcome(intake):
    _, answers = evaluate_rulepack(PACK, intake)
    return assess_outcome(PACK, intake, answers)


def test_unknown_defaults_and_no_mutation():
    facts = {}
    nodes, answers = evaluate_rulepack(PACK, facts)
    assert set(answers.values()) == {"unknown"}
    assert facts == {}
    assert not any(hasattr(n, "confidence") for n in nodes)


@pytest.mark.parametrize("limb", PACK["core_requirements"])
def test_each_required_limb_controls_outcome(limb):
    facts = complete_intake()
    assert outcome(facts)["status"] == "supported"
    facts["assessments"][limb]["answer"] = "unknown"
    assert outcome(facts)["status"] == "incomplete"
    facts["assessments"][limb]["answer"] = "no"
    assert outcome(facts)["status"] == "not_established"


def test_independent_creation_requires_review():
    facts = complete_intake()
    facts["assessments"]["independent_creation"]["answer"] = "yes"
    assert outcome(facts)["status"] == "review_required"


def test_fair_use_is_not_a_checkbox_discount():
    facts = complete_intake()
    facts["assessments"]["fair_use"]["answer"] = "yes"
    assert outcome(facts)["status"] == "incomplete"
    facts["fair_use_factors"] = {k: "Factor evidence" for k in ("purpose", "nature", "amount", "market")}
    assert outcome(facts)["status"] == "review_required"
    facts["fair_use_factors"].update(context="criticism_review", acknowledgment="impossible", acknowledgment_basis="Cannot locate author")
    assert outcome(facts)["status"] == "incomplete"
    facts["fair_use_factors"]["context"] = "news"
    assert outcome(facts)["status"] == "review_required"


@pytest.mark.parametrize("change", [{"work_category": "unknown"}, {"claim_route": "secondary"}, {"claim_route": "authorisation"}, {"conduct_date": "2019-01-01"}, {"conduct_date": "2024-01-01"}, {"conduct_date": "2027-01-01"}])
def test_scope_gates(change):
    assert outcome(dict(complete_intake(), **change))["status"] == "scope_review"


def test_strict_assessments():
    for facts in [{"similarity_score": 1}, {"assessments": {"invented": {}}}, {"assessments": {"substantial_part": {"answer": "yes"}}}]:
        with pytest.raises(ValidationError):
            LegalIntake.model_validate(facts)
    assert all_answers(["unknown", "no"]) == "no"
