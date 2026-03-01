from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.db.models import Artifact, Case
from app.services.legal.engine import LegalNodeResult


def _deterministic_report_id(
    case_id: str,
    scoring_version: str,
    rule_pack_version: str,
    artifact_checksums: list[str],
) -> str:
    payload = {
        "case_id": case_id,
        "scoring_version": scoring_version,
        "rule_pack_version": rule_pack_version,
        "artifact_checksums": sorted(artifact_checksums),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:24]


def build_report_payload(
    case: Case,
    artifacts: list[Artifact],
    media_type: str,
    similarity: dict[str, Any],
    legal_nodes: list[LegalNodeResult],
    risk_band: str,
    rulepack: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    report_id = _deterministic_report_id(
        case_id=case.id,
        scoring_version=settings.scoring_version,
        rule_pack_version=rulepack.get("rule_pack_id", settings.rule_pack_version),
        artifact_checksums=[artifact.checksum_sha256 for artifact in artifacts],
    )

    legal_flow = [
        {
            "node_id": n.node_id,
            "phase": n.phase,
            "prompt": n.prompt,
            "answer": n.answer,
            "confidence": n.confidence,
            "evidence_refs": n.evidence_refs,
            "legal_refs": n.legal_refs,
        }
        for n in legal_nodes
    ]

    report = {
        "report_id": report_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "case_id": case.id,
        "jurisdiction": case.jurisdiction,
        "media_type": media_type,
        "headline_overlap_percentage": round(similarity["headline_score"] * 100.0, 2),
        "headline_score": round(similarity["headline_score"], 6),
        "component_scores": similarity["component_scores"],
        "evidence": similarity.get("evidence", {}),
        "legal_flow": legal_flow,
        "risk_band": risk_band,
        "scoring_version": settings.scoring_version,
        "rule_pack_version": rulepack.get("rule_pack_id", settings.rule_pack_version),
        "citations": rulepack.get("citations", {}),
        "disclaimers": [
            "This report is a legal triage aid and not legal advice.",
            "Outputs are deterministic under fixed versions and parameters.",
            f"Source files are retained for {settings.retention_hours} hours by default.",
        ],
    }
    return report