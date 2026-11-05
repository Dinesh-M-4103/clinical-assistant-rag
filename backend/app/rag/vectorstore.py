"""Vector storage: a small Protocol plus the ChromaDB implementation.

Patient isolation is structural: every patient owns a separate collection, so a
query can only ever see that patient's chunks - there is no filter to forget.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from chromadb.errors import NotFoundError

from app.rag.errors import EmbeddingModelMismatchError
from app.rag.types import Chunk

_MODEL_KEY = "embedding_model"
_COLLECTION_PREFIX = "patient_"


class VectorStore(Protocol):
    """Per-patient chunk storage with dense search."""

    def add_chunks(
        self, patient_id: str, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]
    ) -> None: ...

    def search(self, patient_id: str, embedding: Sequence[float], k: int) -> list[Chunk]:
        """Nearest chunks first; empty when the patient has no collection."""
        ...

    def all_chunks(self, patient_id: str) -> list[Chunk]: ...

    def delete_report(self, patient_id: str, report_id: str) -> None: ...

    def delete_patient(self, patient_id: str) -> None: ...


def collection_name(patient_id: str) -> str:
    """``patient_<uhid>``; Chroma names must end alphanumerically, UHIDs may end in ``-``/``_``.

    The ``.x`` suffix is unambiguous because a UHID can never contain a dot.
    """
    name = f"{_COLLECTION_PREFIX}{patient_id}"
    return name if name[-1].isalnum() else f"{name}.x"


class ChromaVectorStore:
    """Persistent Chroma store; embeddings are always supplied, never computed by Chroma."""

    def __init__(self, path: Path, embedding_model: str) -> None:
        self._client = chromadb.PersistentClient(
            path=str(path), settings=Settings(anonymized_telemetry=False)
        )
        self._embedding_model = embedding_model

    def add_chunks(
        self, patient_id: str, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]
    ) -> None:
        if not chunks:
            return
        collection = self._client.get_or_create_collection(
            collection_name(patient_id),
            metadata={_MODEL_KEY: self._embedding_model, "hnsw:space": "cosine"},
            embedding_function=None,
        )
        self._check_model(collection)
        collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=[list(vector) for vector in embeddings],  # type: ignore[arg-type]
            documents=[chunk.text for chunk in chunks],
            metadatas=[_to_metadata(chunk) for chunk in chunks],
        )

    def search(self, patient_id: str, embedding: Sequence[float], k: int) -> list[Chunk]:
        collection = self._existing(patient_id)
        if collection is None or collection.count() == 0:
            return []
        result = collection.query(
            query_embeddings=[list(embedding)],  # type: ignore[arg-type]
            n_results=min(k, collection.count()),
            include=["documents", "metadatas"],
        )
        return _to_chunks(
            result["ids"][0],
            (result["documents"] or [[]])[0],
            (result["metadatas"] or [[]])[0],
        )

    def all_chunks(self, patient_id: str) -> list[Chunk]:
        collection = self._existing(patient_id)
        if collection is None:
            return []
        result = collection.get(include=["documents", "metadatas"])
        return _to_chunks(result["ids"], result["documents"] or [], result["metadatas"] or [])

    def delete_report(self, patient_id: str, report_id: str) -> None:
        """Remove one report's chunks; a no-op when there are none.

        Ids are looked up first and deleted explicitly. Calling ``delete(where=...)`` that
        matches nothing - which every first ingest of a report does - intermittently left
        the collection's HNSW index unreadable ("Nothing found on disk") in Chroma 1.5.
        """
        collection = self._existing(patient_id)
        if collection is None:
            return
        ids = collection.get(where={"report_id": report_id}, include=[])["ids"]
        if ids:
            collection.delete(ids=ids)

    def delete_patient(self, patient_id: str) -> None:
        if self._existing(patient_id) is not None:
            self._client.delete_collection(collection_name(patient_id))

    def _existing(self, patient_id: str) -> Collection | None:
        try:
            collection = self._client.get_collection(
                collection_name(patient_id), embedding_function=None
            )
        except NotFoundError:
            return None
        self._check_model(collection)
        return collection

    def _check_model(self, collection: Collection) -> None:
        stored = (collection.metadata or {}).get(_MODEL_KEY)
        if stored != self._embedding_model:
            raise EmbeddingModelMismatchError(
                f"Collection '{collection.name}' was built with embedding model "
                f"'{stored}', but '{self._embedding_model}' is configured. "
                "Re-ingest the patient's reports or restore the original model."
            )


def _to_metadata(chunk: Chunk) -> dict[str, str | int]:
    return {
        "report_id": chunk.report_id,
        "report_name": chunk.report_name,
        "category": chunk.category,
        "page": chunk.page,
        "section": chunk.section or "",
    }


def _to_chunks(
    ids: Sequence[str], texts: Sequence[str], metadatas: Sequence[Mapping[str, object]]
) -> list[Chunk]:
    return [
        Chunk(
            chunk_id=chunk_id,
            report_id=str(meta["report_id"]),
            report_name=str(meta["report_name"]),
            category=str(meta["category"]),
            page=cast(int, meta["page"]),
            section=str(meta["section"]) or None,
            text=text,
        )
        for chunk_id, text, meta in zip(ids, texts, metadatas, strict=True)
    ]
