"""Relevance gate: decide whether retrieval found anything worth answering from."""

from collections.abc import Sequence

from app.rag.types import Candidate


def has_sufficient_evidence(candidates: Sequence[Candidate], min_rerank_score: float) -> bool:
    """True when the best candidate clears the cross-encoder threshold.

    Without this gate the model would be handed the "least bad" chunks for a
    question the records cannot answer and tempted to improvise. Candidates that
    were never re-scored (the dense/BM25/hybrid ablation modes) carry no
    calibrated score, so for them any non-empty result passes.
    """
    if not candidates:
        return False
    scores = [c.rerank_score for c in candidates if c.rerank_score is not None]
    return max(scores) >= min_rerank_score if scores else True
