"""Retrieval metrics: pure functions over ranked (report file, page) sources.

A retrieved chunk is a *hit* when its (report file, page) pair is one of the question's
expected sources. All ranks are 1-based and cut at ``top_k`` results.
"""

from collections.abc import Sequence
from dataclasses import dataclass

Source = tuple[str, int]
CUTOFFS = (1, 3, 5)


@dataclass(frozen=True)
class RetrievalScores:
    """How one question fared in one retrieval mode."""

    hits_at: dict[int, bool]
    reciprocal_rank: float
    recall_at: dict[int, float]


def first_hit_rank(ranked: Sequence[Source], expected: frozenset[Source]) -> int | None:
    """1-based rank of the first expected source, or ``None`` when none was retrieved."""
    return next((rank for rank, source in enumerate(ranked, 1) if source in expected), None)


def hit_at(ranked: Sequence[Source], expected: frozenset[Source], k: int) -> bool:
    rank = first_hit_rank(ranked, expected)
    return rank is not None and rank <= k


def recall_at(ranked: Sequence[Source], expected: frozenset[Source], k: int) -> float:
    """Share of expected *reports* that have at least one hit chunk in the top ``k``.

    Counted per report rather than per page: a question spanning three reports needs
    evidence from each of them, whichever of the expected pages it came from.
    """
    reports = {report for report, _ in expected}
    if not reports:
        return 0.0
    found = {report for report, page in ranked[:k] if (report, page) in expected}
    return len(found) / len(reports)


def score_question(ranked: Sequence[Source], expected: frozenset[Source]) -> RetrievalScores:
    rank = first_hit_rank(ranked, expected)
    return RetrievalScores(
        hits_at={k: hit_at(ranked, expected, k) for k in CUTOFFS},
        reciprocal_rank=0.0 if rank is None else 1.0 / rank,
        recall_at={k: recall_at(ranked, expected, k) for k in CUTOFFS},
    )


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
