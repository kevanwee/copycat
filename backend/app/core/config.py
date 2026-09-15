from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COPYCAT_", case_sensitive=False)

    app_name: str = "Copycat API"
    environment: str = "dev"

    database_url: str = "sqlite:///./data/copycat.db"
    storage_root: Path = Path("./data/uploads")
    report_root: Path = Path("./data/reports")

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = True

    max_text_mb: int = 10
    max_video_mb: int = 100
    max_video_seconds: int = 300
    max_image_mb: int = 20
    max_text_tokens: int = 20000
    cleanup_interval_seconds: int = 300
    max_active_jobs: int = 2

    allowed_jurisdictions: str = "SG"
    default_jurisdiction: str = "SG"

    retention_hours: int = 24
    scoring_version: str = "v2.0.0"
    rule_pack_version: str = "sg_v2"

    whisper_model_name: str = "base"
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    frontend_base_url: str = "http://localhost:3000"

    @property
    def allowed_jurisdictions_list(self) -> list[str]:
        return [j.strip().upper() for j in self.allowed_jurisdictions.split(",") if j.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    settings.report_root.mkdir(parents=True, exist_ok=True)
    return settings
