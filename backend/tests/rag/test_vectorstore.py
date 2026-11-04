from pathlib import Path

import pytest

from app.rag.errors import EmbeddingModelMismatchError
from app.rag.vectorstore import ChromaVectorStore, collection_name

from .fakes import FakeEmbedder, make_chunk

EMBEDDER = FakeEmbedder()


def store(path: Path, model: str = "model-a") -> ChromaVectorStore:
    return ChromaVectorStore(path, model)


def add(target: ChromaVectorStore, patient: str, *chunks_text: tuple[str, str]) -> None:
    """Add ``(chunk_id, text)`` pairs; the report id is the part of the id before the colon."""
    chunks = [
        make_chunk(chunk_id, text, report_id=chunk_id.split(":")[0])
        for chunk_id, text in chunks_text
    ]
    target.add_chunks(patient, chunks, EMBEDDER.embed_documents([c.text for c in chunks]))


def search(target: ChromaVectorStore, patient: str, query: str, k: int = 5) -> list[str]:
    return [c.chunk_id for c in target.search(patient, EMBEDDER.embed_query(query), k)]


def test_chunks_round_trip_with_all_metadata(tmp_path: Path) -> None:
    target = store(tmp_path)
    chunk = make_chunk("r1:0", "HbA1c 7.8 %", report_name="Lab Jan", page=3, section=None)
    target.add_chunks("MG25001", [chunk], EMBEDDER.embed_documents([chunk.text]))

    assert target.search("MG25001", EMBEDDER.embed_query("hba1c"), 3) == [chunk]
    assert target.all_chunks("MG25001") == [chunk]


def test_search_ranks_the_closest_chunk_first(tmp_path: Path) -> None:
    target = store(tmp_path)
    add(target, "p1", ("r1:0", "metformin tablets twice daily"), ("r1:1", "chest x-ray normal"))

    assert search(target, "p1", "metformin dose")[0] == "r1:0"
    assert search(target, "p1", "x-ray of the chest")[0] == "r1:1"


def test_a_patient_can_never_retrieve_another_patients_chunks(tmp_path: Path) -> None:
    target = store(tmp_path)
    add(target, "p1", ("r1:0", "warfarin 5 mg for atrial fibrillation"))
    add(target, "p2", ("r2:0", "insulin glargine 20 units nightly"))

    assert search(target, "p2", "warfarin atrial fibrillation") == ["r2:0"]
    assert [c.chunk_id for c in target.all_chunks("p1")] == ["r1:0"]
    assert search(target, "nobody", "warfarin") == []


def test_delete_report_removes_only_that_reports_chunks(tmp_path: Path) -> None:
    target = store(tmp_path)
    add(target, "p1", ("r1:0", "alpha"), ("r1:1", "beta"), ("r2:0", "gamma"))

    target.delete_report("p1", "r1")

    assert [c.chunk_id for c in target.all_chunks("p1")] == ["r2:0"]


def test_delete_patient_drops_the_collection_and_is_idempotent(tmp_path: Path) -> None:
    target = store(tmp_path)
    add(target, "p1", ("r1:0", "alpha"))
    add(target, "p2", ("r2:0", "beta"))

    target.delete_patient("p1")
    target.delete_patient("p1")

    assert target.all_chunks("p1") == []
    assert [c.chunk_id for c in target.all_chunks("p2")] == ["r2:0"]


def test_data_survives_reopening_the_store(tmp_path: Path) -> None:
    add(store(tmp_path), "p1", ("r1:0", "alpha"))

    assert [c.chunk_id for c in store(tmp_path).all_chunks("p1")] == ["r1:0"]


def test_opening_a_collection_with_another_embedding_model_raises(tmp_path: Path) -> None:
    add(store(tmp_path, "model-a"), "p1", ("r1:0", "alpha"))
    other = store(tmp_path, "model-b")

    with pytest.raises(EmbeddingModelMismatchError, match="model-a"):
        other.search("p1", EMBEDDER.embed_query("alpha"), 3)
    with pytest.raises(EmbeddingModelMismatchError):
        add(other, "p1", ("r2:0", "beta"))
    assert [c.chunk_id for c in store(tmp_path, "model-a").all_chunks("p1")] == ["r1:0"]


@pytest.mark.parametrize(
    ("uhid", "expected"),
    [("MG25001", "patient_MG25001"), ("ab-", "patient_ab-.x"), ("x_", "patient_x_.x")],
)
def test_collection_names_always_end_alphanumerically(uhid: str, expected: str) -> None:
    assert collection_name(uhid) == expected
