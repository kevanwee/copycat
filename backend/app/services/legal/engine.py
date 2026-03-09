from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LegalNodeResult:
    node_id: str
    phase: str
    answer: str
    confidence: float
    evidence_refs: list[str]
    legal_refs: list[str]
    prompt: str


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"yes", "true", "1"}:
            return True
        if lowered in {"no", "false", "0"}:
            return False
    return None


def _score_gte(facts: dict[str, Any], fact: str, threshold: float) -> bool | None:
    raw = facts.get(fact)
    if raw is None:
        return None
    try:
        return float(raw) >= float(threshold)
    except Exception:
        return None


def _evaluate_expression(expr: dict[str, Any], facts: dict[str, Any], node_answers: dict[str, str]) -> bool | None:
    if not isinstance(expr, dict):
        return None

    expr_type = expr.get("type")

    if expr_type == "fact_bool":
        return _as_bool(facts.get(expr.get("fact")))
    if expr_type == "fact_false":
        val = _as_bool(facts.get(expr.get("fact")))
        return None if val is None else (not val)
    if expr_type == "all_true":
        facts_list = expr.get("facts") or []
        if not isinstance(facts_list, list):
            return None
        vals = [_as_bool(facts.get(f)) for f in facts_list]
        if any(v is None for v in vals):
            return None
        return all(vals)
    if expr_type == "any_true":
        facts_list = expr.get("facts") or []
        if not isinstance(facts_list, list):
            return None
        vals = [_as_bool(facts.get(f)) for f in facts_list]
        if all(v is None for v in vals):
            return None
        return any(v for v in vals if v is not None)
    if expr_type == "score_gte":
        return _score_gte(facts, expr.get("fact", ""), float(expr.get("threshold", 0.0)))
    if expr_type == "all_nodes_true":
        nodes = expr.get("nodes") or []
        if not isinstance(nodes, list):
            return None
        vals = [node_answers.get(n) for n in nodes]
        if any(v is None for v in vals):
            return None
        if any(v == "unknown" for v in vals):
            return None
        return all(v == "yes" for v in vals)

    return None


def evaluate_rulepack(rulepack: dict[str, Any], facts: dict[str, Any]) -> tuple[list[LegalNodeResult], dict[str, str]]:
    node_results: list[LegalNodeResult] = []
    node_answers: dict[str, str] = {}

    nodes = rulepack.get("nodes") or []
    if not isinstance(nodes, list):
        nodes = []

    for node in nodes:
        if not isinstance(node, dict):
            continue

        derive = node.get("derive") or {}
        if not isinstance(derive, dict):
            derive = {}
        for key, expr in derive.items():
            if key not in facts:
                facts[key] = _evaluate_expression(expr, facts, node_answers)

        required_facts = node.get("required_facts") or []
        if not isinstance(required_facts, list):
            required_facts = []

        required_nodes = node.get("required_nodes") or []
        if not isinstance(required_nodes, list):
            required_nodes = []

        known_required_facts = [facts.get(key) is not None for key in required_facts]
        known_required_nodes = [node_answers.get(key) is not None for key in required_nodes]

        denominator = max(1, len(required_facts) + len(required_nodes))
        evidence_ratio = (sum(known_required_facts) + sum(known_required_nodes)) / denominator

        bool_result = _evaluate_expression(node.get("eval", {}), facts, node_answers)
        if bool_result is True:
            answer = "yes"
            answer_certainty = 1.0
        elif bool_result is False:
            answer = "no"
            answer_certainty = 1.0
        else:
            answer = "unknown"
            answer_certainty = 0.0

        # Blend evidence coverage (60%) and answer determinism (40%).
        # Prevents a node with all facts present but an unknown answer from
        # falsely reporting 100% confidence.
        confidence = round((evidence_ratio * 0.6) + (answer_certainty * 0.4), 6)

        evidence_refs = [f"fact:{f}" for f in required_facts if facts.get(f) is not None]
        evidence_refs.extend([f"node:{n}" for n in required_nodes if node_answers.get(n) is not None])

        result = LegalNodeResult(
            node_id=node["id"],
            phase=node["phase"],
            answer=answer,
            confidence=confidence,
            evidence_refs=evidence_refs,
            legal_refs=node.get("legal_refs", []),
            prompt=node.get("prompt", ""),
        )
        node_results.append(result)
        node_answers[node["id"]] = answer

    return node_results, node_answers


def compute_risk_band(node_answers: dict[str, str], similarity_score: float) -> str:
    if node_answers.get("subsistence_overall") == "no":
        return "LOW"

    base = "LOW"
    if similarity_score >= 0.75:
        base = "HIGH"
    elif similarity_score >= 0.40:
        base = "MEDIUM"

    infringement_core = all(
        node_answers.get(key) == "yes"
        for key in [
            "infringement_ownership_standing",
            "infringement_acts_covered",
            "infringement_no_authorization",
            "copying_objective_similarity",
            "substantial_taking_quality",
        ]
    )

    if infringement_core:
        base = "HIGH"

    if node_answers.get("exceptions_fair_use_signal") == "yes":
        if base == "HIGH":
            return "MEDIUM"
        if base == "MEDIUM":
            return "LOW"

    return base