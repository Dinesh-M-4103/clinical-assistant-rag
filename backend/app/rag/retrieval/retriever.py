"""Orchestrates retrieval according to ``RagSettings.retrieval_mode``.

Modes exist so evaluations can ablate each stage: ``dense`` and ``bm25`` use one
ranking, ``hybrid`` fuses both with RRF, and ``hybrid_rerank`` (the default)
re-scores the fused pool with a cross-encoder.
"""

from dataclasses import dataclass, replace

from app.rag.config import RagSettings
from app.rag.retrieval.bm25 import Bm25Retriever
from app.rag.retrieval.dense import DenseRetriever
from app.rag.retrieval.fusion import reciprocal_rank_fusion
from app.rag.retrieval.reranker import Reranker
from app.rag.timing import elapsed_ms, now
from app.rag.types import Candidate, Chunk

_USES_DENSE = frozenset({"dense", "hybrid", "hybrid_rerank"})
_USES_BM25 = frozenset({"bm25", "hybrid", "hybrid_rerank"})


@dataclass(frozen=True)
class RetrievalResult:
    """Final candidates, best first, with the time spent in each stage."""

    candidates: list[Candidate]
    retrieval_ms: int
    rerank_ms: int


class HybridRetriever:
    def __init__(
        self,
        settings: RagSettings,
        dense: DenseRetriever,
        bm25: Bm25Retriever,
        reranker: Reranker,
    ) -> None:
        self._settings = settings
        self._dense = dense
        self._bm25 = bm25
        self._reranker = reranker

    def retrieve(self, patient_id: str, query: str) -> RetrievalResult:
        settings = self._settings
        started = now()
        dense_hits = (
            self._dense.search(patient_id, query, settings.dense_k)
            if settings.retrieval_mode in _USES_DENSE
            else []
        )
        bm25_hits = (
            self._bm25.search(patient_id, query, settings.bm25_k)
            if settings.retrieval_mode in _USES_BM25
            else []
        )
        candidates = _fuse(dense_hits, bm25_hits)
        retrieval_ms = elapsed_ms(started)

        rerank_ms = 0
        if settings.retrieval_mode == "hybrid_rerank":
            started = now()
            candidates = self._rerank(query, candidates)
            rerank_ms = elapsed_ms(started)
        return RetrievalResult(candidates[: settings.rerank_top_n], retrieval_ms, rerank_ms)

    def invalidate(self, patient_id: str) -> None:
        """Forget cached keyword indexes after the patient's chunks changed."""
        self._bm25.invalidate(patient_id)

    def _rerank(self, query: str, candidates: list[Candidate]) -> list[Candidate]:
        scores = self._reranker.score(query, [c.chunk.contextual_text for c in candidates])
        scored = [replace(c, rerank_score=s) for c, s in zip(candidates, scores, strict=True)]
        return sorted(scored, key=lambda c: c.rerank_score or 0.0, reverse=True)


def _fuse(dense_hits: list[Chunk], bm25_hits: list[Chunk]) -> list[Candidate]:
    dense_rank = {chunk.chunk_id: rank for rank, chunk in enumerate(dense_hits, start=1)}
    bm25_rank = {chunk.chunk_id: rank for rank, chunk in enumerate(bm25_hits, start=1)}
    chunks = {chunk.chunk_id: chunk for chunk in [*dense_hits, *bm25_hits]}
    fused = reciprocal_rank_fusion([list(dense_rank), list(bm25_rank)])
    return [
        Candidate(chunks[chunk_id], dense_rank.get(chunk_id), bm25_rank.get(chunk_id), score, None)
        for chunk_id, score in fused
    ]
