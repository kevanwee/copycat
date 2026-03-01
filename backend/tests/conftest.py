from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_env() -> None:
    os.environ.setdefault("COPYCAT_DATABASE_URL", "sqlite:///./data/test_copycat.db")
    os.environ.setdefault("COPYCAT_STORAGE_ROOT", "./data/test_uploads")
    os.environ.setdefault("COPYCAT_REPORT_ROOT", "./data/test_reports")
    os.environ.setdefault("COPYCAT_CELERY_TASK_ALWAYS_EAGER", "true")

    Path("./data/test_uploads").mkdir(parents=True, exist_ok=True)
    Path("./data/test_reports").mkdir(parents=True, exist_ok=True)
    yield

    try:
        from app.db.session import engine

        engine.dispose()
    except Exception:
        pass

    shutil.rmtree("./data/test_uploads", ignore_errors=True)
    shutil.rmtree("./data/test_reports", ignore_errors=True)
    Path("./data/test_copycat.db").unlink(missing_ok=True)


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client