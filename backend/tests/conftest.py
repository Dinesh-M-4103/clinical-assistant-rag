"""Shared fixtures: an app wired to temp storage and a fake pipeline."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.fakes import FakePipeline
from tests.helpers import ALLOWED_ORIGIN, UHID


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Isolated settings: never reads backend/.env or the real storage folder."""
    return Settings(
        _env_file=None,
        storage_dir=tmp_path / "storage",
        max_upload_mb=1,
        cors_origins=[ALLOWED_ORIGIN],
        skip_warmup=True,
    )


@pytest.fixture
def pipeline() -> FakePipeline:
    return FakePipeline()


@pytest.fixture
def client(settings: Settings, pipeline: FakePipeline) -> Iterator[TestClient]:
    app = create_app(settings, lambda _: pipeline)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def patient(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/patients",
        json={"uhid": UHID, "name": "Asha Verma", "age": 54, "gender": "female"},
    )
    assert response.status_code == 201
    created: dict[str, object] = response.json()
    return created
