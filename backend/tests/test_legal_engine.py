from __future__ import annotations

from app.services.legal.engine import compute_risk_band, evaluate_rulepack
from app.services.legal.rulepack_loader import load_rulepack



def test_legal_engine_subsistence_yes() -> None:
    rulepack = load_rulepack("sg_v1")
    facts = {
        "work_category_supported": True,
        "originality_evidence": True,
        "fixation_evidence": True,
        "sg_connection": True,
        "term_active": True,
        "ownership_asserted": True,
        "acts_covered": True,
        "authorization_present": False,
        "access_evidence": True,
        "similarity_score": 0.82,
        "qualitative_importance_flag": True,
        "fair_use_indicator": False,
    }

    nodes, answers = evaluate_rulepack(rulepack, facts)
    assert any(n.node_id == "subsistence_overall" and n.answer == "yes" for n in nodes)

    risk = compute_risk_band(answers, similarity_score=0.82)
    assert risk == "HIGH"


def test_legal_engine_fair_use_downgrades_risk() -> None:
    rulepack = load_rulepack("sg_v1")
    facts = {
        "work_category_supported": True,
        "originality_evidence": True,
        "fixation_evidence": True,
        "sg_connection": True,
        "term_active": True,
        "ownership_asserted": True,
        "acts_covered": True,
        "authorization_present": False,
        "access_evidence": True,
        "similarity_score": 0.82,
        "qualitative_importance_flag": True,
        "fair_use_indicator": True,
    }

    _, answers = evaluate_rulepack(rulepack, facts)
    risk = compute_risk_band(answers, similarity_score=0.82)
    assert risk == "MEDIUM"