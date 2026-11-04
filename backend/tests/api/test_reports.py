from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.rag.errors import InvalidPdfError, NoExtractableTextError
from app.services.storage import ReportFileStore
from tests.fakes import FakePipeline
from tests.helpers import UHID, make_pdf, upload_pdf

MIB = 1024 * 1024
OTHER_UHID = "MG25002"


def stored_files(settings: Settings) -> list[Path]:
    return [path for path in settings.reports_dir.rglob("*") if path.is_file()]


@pytest.fixture
def other_patient(client: TestClient) -> None:
    payload = {"uhid": OTHER_UHID, "name": "Ravi Rao", "age": 61, "gender": "male"}
    assert client.post("/api/v1/patients", json=payload).status_code == 201


def test_upload_returns_report_and_ingests(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    pdf = make_pdf()

    response = upload_pdf(client, content=pdf, notes="  fasting sample ")

    assert response.status_code == 201
    body = response.json()
    assert body["uhid"] == UHID
    assert body["name"] == "CBC Report"
    assert body["category"] == "lab"
    assert body["notes"] == "fasting sample"
    assert body["original_filename"] == "cbc.pdf"
    assert (body["page_count"], body["chunk_count"]) == (3, 7)
    assert body["size_bytes"] == len(pdf)
    assert body["file_url"] == f"/api/v1/patients/{UHID}/reports/{body['report_id']}/file"
    assert body["uploaded_at"].endswith("Z")

    [call] = pipeline.ingested
    assert call["patient_id"] == UHID
    assert call["report_id"] == body["report_id"]
    assert call["category"] == "lab"
    assert call["file_existed"] is True
    assert call["pdf_path"] == settings.reports_dir / UHID / f"{body['report_id']}.pdf"


def test_upload_sanitises_filename(client: TestClient, patient: dict[str, object]) -> None:
    response = upload_pdf(client, filename="..\\..\\etc/pass wd<script>.pdf")

    assert response.json()["original_filename"] == "pass wd_script.pdf"


def test_upload_to_unknown_patient_is_404_and_stores_nothing(
    client: TestClient, settings: Settings
) -> None:
    response = upload_pdf(client, uhid="NOPE1")

    assert response.status_code == 404
    assert not settings.reports_dir.exists() or stored_files(settings) == []


def test_non_pdf_with_pdf_extension_is_rejected(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    response = upload_pdf(client, content=b"MZ\x90\x00 not a pdf at all", filename="evil.pdf")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"
    assert pipeline.ingested == []
    assert stored_files(settings) == []


def test_empty_file_is_rejected(client: TestClient, patient: dict[str, object]) -> None:
    assert upload_pdf(client, content=b"").status_code == 415


def test_upload_over_limit_is_rejected_while_streaming(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    """1.5 MiB passes the declared-length guard but exceeds the 1 MiB file cap."""
    oversized = b"%PDF-" + b"0" * (3 * MIB // 2)

    response = upload_pdf(client, content=oversized)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
    assert pipeline.ingested == []
    assert stored_files(settings) == []
    assert list(settings.reports_dir.rglob("*.part")) == []


def test_upload_far_over_limit_is_rejected_before_parsing(
    client: TestClient, pipeline: FakePipeline, patient: dict[str, object]
) -> None:
    response = upload_pdf(client, content=b"%PDF-" + b"0" * (4 * MIB))

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
    assert pipeline.ingested == []


def test_pdf_without_text_is_rejected_and_fully_rolled_back(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    pipeline.ingest_error = NoExtractableTextError("scanned")

    response = upload_pdf(client)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "no_extractable_text"
    assert stored_files(settings) == []
    assert pipeline.deleted_reports == [(UHID, pipeline.ingested[0]["report_id"])]
    assert client.get(f"/api/v1/patients/{UHID}/reports").json() == []


def test_corrupt_pdf_is_a_bad_request(
    client: TestClient, pipeline: FakePipeline, patient: dict[str, object]
) -> None:
    pipeline.ingest_error = InvalidPdfError("encrypted")

    response = upload_pdf(client)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_pdf"


def test_failed_file_cleanup_does_not_mask_the_original_error(
    client: TestClient,
    pipeline: FakePipeline,
    patient: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline.ingest_error = InvalidPdfError("truncated")

    def locked(*_: object) -> None:
        raise PermissionError("file is in use")

    monkeypatch.setattr(ReportFileStore, "delete", locked)

    response = upload_pdf(client)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_pdf"


def test_unexpected_ingestion_failure_is_rolled_back_without_leaking(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    pipeline.ingest_error = RuntimeError("secret path D:\\clinical\\chroma exploded")

    response = upload_pdf(client)

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An unexpected error occurred."}
    }
    assert stored_files(settings) == []
    assert len(pipeline.deleted_reports) == 1
    assert client.get(f"/api/v1/patients/{UHID}/reports").json() == []


@pytest.mark.parametrize(
    ("form", "field"),
    [
        ({"name": "", "category": "lab"}, "name"),
        ({"name": "CBC", "category": "xray"}, "category"),
        ({"category": "lab"}, "name"),
    ],
)
def test_invalid_upload_form_is_422(
    client: TestClient, patient: dict[str, object], form: dict[str, str], field: str
) -> None:
    files = {"file": ("a.pdf", make_pdf(), "application/pdf")}

    response = client.post(f"/api/v1/patients/{UHID}/reports", data=form, files=files)

    assert response.status_code == 422
    assert field in response.json()["error"]["message"]


def test_upload_without_file_is_422(client: TestClient, patient: dict[str, object]) -> None:
    response = client.post(
        f"/api/v1/patients/{UHID}/reports", data={"name": "CBC", "category": "lab"}
    )

    assert response.status_code == 422


def test_list_reports_newest_first(client: TestClient, patient: dict[str, object]) -> None:
    first = upload_pdf(client, name="First").json()["report_id"]
    second = upload_pdf(client, name="Second").json()["report_id"]

    listed = [r["report_id"] for r in client.get(f"/api/v1/patients/{UHID}/reports").json()]

    assert listed == [second, first]


def test_list_reports_of_unknown_patient_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/patients/NOPE1/reports").status_code == 404


def test_download_serves_inline_pdf(client: TestClient, patient: dict[str, object]) -> None:
    pdf = make_pdf()
    report = upload_pdf(client, content=pdf, filename="my report.pdf").json()

    response = client.get(report["file_url"])

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content == pdf


def test_download_unknown_report_is_404(client: TestClient, patient: dict[str, object]) -> None:
    response = client.get(
        f"/api/v1/patients/{UHID}/reports/00000000-0000-4000-8000-000000000000/file"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_download_when_file_vanished_is_404(
    client: TestClient, settings: Settings, patient: dict[str, object]
) -> None:
    report = upload_pdf(client).json()
    for path in stored_files(settings):
        path.unlink()

    assert client.get(report["file_url"]).status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/patients/..%2F..%2Fetc/reports",
        "/api/v1/patients/MG25001/reports/..%2F..%2Fapp.db/file",
        "/api/v1/patients/MG25001/reports/../../../../etc/passwd/file",
        "/api/v1/patients/MG25001/reports/%2e%2e%5c%2e%2e%5csecret/file",
        "/api/v1/patients/MG25001/reports/not-a-uuid/file",
        "/api/v1/patients/%2e%2e/reports/00000000-0000-4000-8000-000000000000/file",
    ],
)
def test_path_traversal_attempts_never_reach_the_filesystem(
    client: TestClient, patient: dict[str, object], path: str
) -> None:
    response = client.get(path)

    assert response.status_code in {404, 422}
    assert response.json()["error"]["code"] in {"not_found", "validation_error"}


def test_report_of_another_patient_is_not_reachable(
    client: TestClient,
    pipeline: FakePipeline,
    patient: dict[str, object],
    other_patient: None,
) -> None:
    report = upload_pdf(client).json()
    stolen = f"/api/v1/patients/{OTHER_UHID}/reports/{report['report_id']}"

    assert client.get(f"{stolen}/file").status_code == 404
    assert client.delete(stolen).status_code == 404
    assert client.get(f"/api/v1/patients/{OTHER_UHID}/reports").json() == []
    assert pipeline.deleted_reports == []
    assert client.get(report["file_url"]).status_code == 200


def test_delete_report_removes_row_file_and_vectors(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    report = upload_pdf(client).json()

    response = client.delete(f"/api/v1/patients/{UHID}/reports/{report['report_id']}")

    assert response.status_code == 204
    assert pipeline.deleted_reports == [(UHID, report["report_id"])]
    assert stored_files(settings) == []
    assert client.get(report["file_url"]).status_code == 404
    assert client.get(f"/api/v1/patients/{UHID}").json()["report_count"] == 0


def test_delete_report_keeps_everything_when_vector_deletion_fails(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    report = upload_pdf(client).json()
    pipeline.delete_error = RuntimeError("chroma down")

    response = client.delete(f"/api/v1/patients/{UHID}/reports/{report['report_id']}")

    assert response.status_code == 500
    assert len(stored_files(settings)) == 1
    assert client.get(report["file_url"]).status_code == 200


def test_delete_unknown_report_is_404(client: TestClient, patient: dict[str, object]) -> None:
    response = client.delete(
        f"/api/v1/patients/{UHID}/reports/00000000-0000-4000-8000-000000000000"
    )

    assert response.status_code == 404
