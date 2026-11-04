import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.fakes import FakePipeline
from tests.helpers import UHID, upload_pdf

PATIENT = {"uhid": UHID, "name": "Asha Verma", "age": 54, "gender": "female", "summary": "T2DM"}


def test_create_patient_returns_contract_shape(client: TestClient) -> None:
    response = client.post("/api/v1/patients", json=PATIENT)

    assert response.status_code == 201
    body = response.json()
    assert body.pop("created_at").endswith("Z")
    assert body == PATIENT | {"report_count": 0}


def test_create_patient_trims_text_and_defaults_summary(client: TestClient) -> None:
    payload = {"uhid": "ABC", "name": "  Ravi Rao ", "age": 0, "gender": "male"}

    body = client.post("/api/v1/patients", json=payload).json()

    assert body["name"] == "Ravi Rao"
    assert body["summary"] is None


def test_duplicate_uhid_conflicts(client: TestClient, patient: dict[str, object]) -> None:
    response = client.post("/api/v1/patients", json=PATIENT)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "patient_exists"


@pytest.mark.parametrize(
    "override",
    [
        {"uhid": "ab"},
        {"uhid": "has space"},
        {"uhid": "x" * 33},
        {"uhid": "../etc"},
        {"name": "   "},
        {"age": -1},
        {"age": 131},
        {"gender": "robot"},
    ],
)
def test_invalid_patient_is_rejected_with_envelope(
    client: TestClient, override: dict[str, object]
) -> None:
    response = client.post("/api/v1/patients", json=PATIENT | override)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert next(iter(override)) in error["message"]


def test_list_patients_is_newest_first(client: TestClient) -> None:
    for uhid in ("AAA", "BBB", "CCC"):
        client.post("/api/v1/patients", json=PATIENT | {"uhid": uhid})

    listed = [p["uhid"] for p in client.get("/api/v1/patients").json()]

    assert listed == ["CCC", "BBB", "AAA"]


def test_get_patient_and_report_count(client: TestClient, patient: dict[str, object]) -> None:
    upload_pdf(client)

    body = client.get(f"/api/v1/patients/{UHID}").json()

    assert body["report_count"] == 1


def test_unknown_patient_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/patients/NOPE1")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_patient_cascades_to_reports_files_and_vectors(
    client: TestClient,
    settings: Settings,
    pipeline: FakePipeline,
    patient: dict[str, object],
) -> None:
    report_id = upload_pdf(client).json()["report_id"]
    stored = settings.reports_dir / UHID / f"{report_id}.pdf"
    assert stored.is_file()

    response = client.delete(f"/api/v1/patients/{UHID}")

    assert response.status_code == 204
    assert pipeline.deleted_patients == [UHID]
    assert not stored.parent.exists()
    assert client.get(f"/api/v1/patients/{UHID}").status_code == 404
    assert client.get(f"/api/v1/patients/{UHID}/reports/{report_id}/file").status_code == 404


def test_delete_patient_rolls_back_when_vector_deletion_fails(
    client: TestClient, pipeline: FakePipeline, patient: dict[str, object]
) -> None:
    upload_pdf(client)
    pipeline.delete_error = RuntimeError("chroma down")

    response = client.delete(f"/api/v1/patients/{UHID}")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert client.get(f"/api/v1/patients/{UHID}").json()["report_count"] == 1


def test_delete_unknown_patient_is_404(client: TestClient) -> None:
    assert client.delete("/api/v1/patients/NOPE1").status_code == 404
