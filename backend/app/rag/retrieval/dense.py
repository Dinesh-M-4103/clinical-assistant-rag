"""Dense (semantic) retrieval over one patient's vector collection."""

from app.rag.embeddings import Embedder
from app.rag.types import Chunk
from app.rag.vectorstore import VectorStore


class DenseRetriever:
    """Finds chunks whose meaning is closest to the query, even without shared words."""

    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def search(self, patient_id: str, query: str, k: int) -> list[Chunk]:
        """Best chunk first; rank is the position in the returned list."""
        return self._store.search(patient_id, self._embedder.embed_query(query), k)
