"""Pytest configuration: env overrides and shared TestClient fixture."""

import os
import tempfile

# Must be set before any app module is imported so pydantic-settings picks them up.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["APP_DB_PATH"] = _tmp_db.name
os.environ["APP_OTEL_ENDPOINT"] = ""  # disable remote export during tests

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Context manager triggers lifespan → setup() creates the experiments table.
    with TestClient(app) as c:
        yield c
