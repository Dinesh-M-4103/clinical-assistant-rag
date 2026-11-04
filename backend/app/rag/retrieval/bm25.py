"""Keyword retrieval with BM25, tuned for clinical vocabulary.

Dense embeddings blur exact tokens such as ``HbA1c``, ``B12`` or ``500mg``;
BM25 matches them precisely, which is why the two are combined.
"""

import re
from threading import Lock

from rank_bm25 import BM25Plus

from app.rag.types import Chunk
from app.rag.vectorstore import VectorStore

_TOKEN = re.compile(r"\d+(?:\.\d+)?[a-z]*|[a-z][a-z0-9]*")
"""Alphanumeric runs stay whole (``hba1c``, ``b12``, ``5mg``) and decimals keep their point
(``13.2``); hyphens and slashes split, so a range such as ``12.0-15.5`` yields both bounds."""
_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from", "has", "have",
        "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "were", "what",
        "when", "which", "who", "with",
    }
)  # fmt: skip


def tokenize(text: str) -> list[str]:
    """Lower-case, medical-friendly tokens with common English stop words removed."""
    return [token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS]


class _PatientIndex:
    """BM25+ over one patient's chunks.

    Plain BM25 gives a term that appears in half the chunks (or in a one-chunk
    corpus) a zero or negative weight, which silently loses matches for the small
    collections typical of one patient. BM25+ keeps every weight positive; since it
    also adds a constant for chunks without the term, only chunks that really
    contain a query token are eligible.
    """

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.tokens = [set(tokenize(chunk.text)) for chunk in chunks]
        self.bm25 = BM25Plus([tokenize(chunk.text) for chunk in chunks])

    def top(self, query: str, k: int) -> list[Chunk]:
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        matching = [i for i, tokens in enumerate(self.tokens) if tokens.intersection(query_tokens)]
        ranked = sorted(matching, key=lambda i: scores[i], reverse=True)
        return [self.chunks[i] for i in ranked[:k]]


class Bm25Retriever:
    """Builds one BM25 index per patient from the stored chunks and caches it.

    The cache must be dropped with :meth:`invalidate` whenever a patient's
    chunks change (ingest or delete); the pipeline does this.
    """

    def __init__(self, store: VectorStore) -> None:
        self._store = store
        self._indexes: dict[str, _PatientIndex] = {}
        self._lock = Lock()

    def search(self, patient_id: str, query: str, k: int) -> list[Chunk]:
        """Best chunk first; chunks sharing no query token are never returned."""
        index = self._index(patient_id)
        return index.top(query, k) if index else []

    def invalidate(self, patient_id: str) -> None:
        with self._lock:
            self._indexes.pop(patient_id, None)

    def _index(self, patient_id: str) -> _PatientIndex | None:
        with self._lock:
            if patient_id not in self._indexes:
                chunks = self._store.all_chunks(patient_id)
                if not chunks:
                    return None
                self._indexes[patient_id] = _PatientIndex(chunks)
            return self._indexes[patient_id]
