from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def load_rulepack(rule_pack_version: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    version = rule_pack_version or settings.rule_pack_version
    path = Path(__file__).resolve().parents[2] / "rulepacks" / f"{version}.json"
    if not path.exists():
        raise FileNotFoundError(f"Rule pack not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))