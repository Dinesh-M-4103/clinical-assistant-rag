"""Cross-cutting behaviour: health, error envelope, request ids, CORS, OpenAPI."""

from collections.abc import Iterator

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.fakes import FakePipeline
from tests.helpers import ALLOWED_ORIGIN, UHID


def test_health_reports_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "llm_configured": False,
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "version": "0.1.0",
    }


def test_health_reflects_a_configured_key(settings: Settings, pipeline: FakePipeline) -> None:
    configured = Settings(
        _env_file=None,
        storage_dir=settings.storage_dir,
        gemini_api_key="AQ.dummy",
        skip_warmup=True,
    )
    with TestClient(create_app(configured, lambda _: pipeline)) as client:
        body = client.get("/api/v1/health").json()

    assert body["llm_configured"] is True
    assert "AQ.dummy" not in str(body)


def test_warmup_runs_unless_skipped(settings: Settings) -> None:
    warmed, skipped = FakePipeline(), FakePipeline()
    warming = Settings(_env_file=None, storage_dir=settings.storage_dir, skip_warmup=False)

    with TestClient(create_app(warming, lambda _: warmed)):
        pass
    with TestClient(create_app(settings, lambda _: skipped)):
        pass

    assert (warmed.warmed_up, skipped.warmed_up) == (True, False)


@pytest.mark.parametrize(
    ("method", "path", "status", "code"),
    [
        ("GET", "/api/v1/nothing-here", 404, "not_found"),
        ("PUT", "/api/v1/patients", 405, "method_not_allowed"),
        ("POST", "/api/v1/patients", 422, "validation_error"),
    ],
)
def test_every_error_uses_the_envelope(
    client: TestClient, method: str, path: str, status: int, code: str
) -> None:
    response = client.request(method, path)

    assert response.status_code == status
    body = response.json()
    assert list(body) == ["error"]
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)


def test_validation_error_does_not_echo_input(client: TestClient) -> None:
    secret = "do-not-echo-me"

    response = client.post("/api/v1/patients", json={"uhid": "ok1", "name": secret, "age": "old"})

    assert secret not in response.text


@pytest.fixture
def crashing_client(settings: Settings, pipeline: FakePipeline) -> Iterator[TestClient]:
    app = create_app(settings, lambda _: pipeline)
    router = APIRouter()

    @router.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret D:\\clinical-assistant\\backend\\storage\\app.db")

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_unhandled_exception_returns_generic_500_with_cors(crashing_client: TestClient) -> None:
    response = crashing_client.get("/boom", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An unexpected error occurred."}
    }
    assert "secret" not in response.text
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["x-request-id"]


def test_request_id_is_generated_and_echoed(client: TestClient) -> None:
    generated = client.get("/api/v1/health").headers["x-request-id"]
    echoed = client.get("/api/v1/health", headers={"X-Request-ID": "trace-123"}).headers[
        "x-request-id"
    ]
    sanitised = client.get("/api/v1/health", headers={"X-Request-ID": "bad id\t!"}).headers[
        "x-request-id"
    ]

    assert len(generated) == 32
    assert echoed == "trace-123"
    assert sanitised != "bad id\t!"


def test_cors_allows_listed_origin(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


def test_cors_ignores_unlisted_origin(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_for_json_post(client: TestClient) -> None:
    response = client.options(
        f"/api/v1/patients/{UHID}/chat",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "POST" in response.headers["access-control-allow-methods"]


def test_wildcard_origin_is_refused_at_configuration_time() -> None:
    with pytest.raises(ValueError, match="never '\\*'"):
        Settings(_env_file=None, cors_origins=["*"])


def test_cors_origins_parse_from_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test, http://b.test")

    assert Settings(_env_file=None).cors_origins == ["http://a.test", "http://b.test"]


def test_openapi_documents_error_envelope_and_sse(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()

    assert spec["info"]["title"] == "Clinical Assistant API"
    assert {tag["name"] for tag in spec["tags"]} == {"health", "patients", "reports", "chat"}
    stream = spec["paths"]["/api/v1/patients/{uhid}/chat/stream"]["post"]
    assert "text/event-stream" in stream["responses"]["200"]["content"]
    create = spec["paths"]["/api/v1/patients"]["post"]["responses"]
    assert create["409"]["content"]["application/json"]["schema"]["$ref"].endswith("ErrorEnvelope")
