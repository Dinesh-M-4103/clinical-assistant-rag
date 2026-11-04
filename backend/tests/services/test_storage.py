from io import BytesIO
from pathlib import Path

import pytest

from app.core.errors import FileTooLargeError, UnsupportedMediaTypeError
from app.services.storage import ReportFileStore

UHID = "MG25001"
REPORT_ID = "3f2b8c1e-5d4a-4e6f-9a7b-1c2d3e4f5a6b"
MIB = 1024 * 1024


@pytest.fixture
def store(tmp_path: Path) -> ReportFileStore:
    return ReportFileStore(tmp_path / "reports", max_upload_mb=1)


def test_save_streams_pdf_to_server_generated_path(store: ReportFileStore) -> None:
    size = store.save(BytesIO(b"%PDF-1.7 body"), UHID, REPORT_ID)

    path = store.path_for(UHID, REPORT_ID)
    assert size == 13
    assert path.read_bytes() == b"%PDF-1.7 body"
    assert path.name == f"{REPORT_ID}.pdf"
    assert path.parent.name == UHID


def test_save_accepts_a_file_exactly_at_the_limit(store: ReportFileStore) -> None:
    assert store.save(BytesIO(b"%PDF-" + b"0" * (MIB - 5)), UHID, REPORT_ID) == MIB


@pytest.mark.parametrize("content", [b"", b"%PD", b"<html>%PDF-</html>", b"PK\x03\x04"])
def test_save_rejects_content_without_pdf_magic(store: ReportFileStore, content: bytes) -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        store.save(BytesIO(content), UHID, REPORT_ID)

    assert not store.path_for(UHID, REPORT_ID).exists()


def test_save_enforces_the_cap_and_leaves_no_partial_file(
    store: ReportFileStore, tmp_path: Path
) -> None:
    with pytest.raises(FileTooLargeError):
        store.save(BytesIO(b"%PDF-" + b"0" * MIB), UHID, REPORT_ID)

    assert list((tmp_path / "reports").rglob("*.*")) == []


def test_delete_is_idempotent(store: ReportFileStore) -> None:
    store.save(BytesIO(b"%PDF-x"), UHID, REPORT_ID)

    store.delete(UHID, REPORT_ID)
    store.delete(UHID, REPORT_ID)

    assert not store.path_for(UHID, REPORT_ID).exists()


def test_delete_patient_removes_their_directory_only(store: ReportFileStore) -> None:
    other = "MG25002"
    store.save(BytesIO(b"%PDF-x"), UHID, REPORT_ID)
    store.save(BytesIO(b"%PDF-y"), other, REPORT_ID)

    store.delete_patient(UHID)

    assert not store.path_for(UHID, REPORT_ID).parent.exists()
    assert store.path_for(other, REPORT_ID).is_file()


@pytest.mark.parametrize(
    ("uhid", "report_id"),
    [
        ("../escape", REPORT_ID),
        ("a/b", REPORT_ID),
        ("..", REPORT_ID),
        (UHID, "../../evil"),
        (UHID, "not-a-uuid"),
        (UHID, f"{REPORT_ID}/../x"),
    ],
)
def test_unvalidated_identifiers_never_become_paths(
    store: ReportFileStore, uhid: str, report_id: str
) -> None:
    with pytest.raises(ValueError, match="unvalidated"):
        store.path_for(uhid, report_id)


def test_delete_patient_refuses_invalid_uhid(store: ReportFileStore) -> None:
    with pytest.raises(ValueError, match="invalid UHID"):
        store.delete_patient("../..")
