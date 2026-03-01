from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


class LocalStorage:
    def __init__(self) -> None:
        self.settings = get_settings()

    def case_dir(self, case_id: str) -> Path:
        path = self.settings.storage_root / case_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_artifact(self, case_id: str, artifact_id: str, filename: str, data: bytes) -> Path:
        safe_name = filename.replace("..", "_").replace("/", "_").replace("\\", "_")
        path = self.case_dir(case_id) / f"{artifact_id}_{safe_name}"
        path.write_bytes(data)
        return path

    def read_bytes(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()