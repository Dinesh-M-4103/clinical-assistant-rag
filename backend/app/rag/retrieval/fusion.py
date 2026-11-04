"""Reciprocal Rank Fusion: merge several rankings without comparing their raw scores."""

from collections.abc import Sequence

RRF_K = 60
"""Damping constant from the original RRF paper; 60 is the widely used default."""


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], k: int = RRF_K
) -> list[tuple[str, float]]:
    """Fuse ranked id lists into ``(id, score)`` pairs, best first.

    Each list contributes ``1 / (k + rank)`` (rank starts at 1) to every id it
    contains. Scores from dense and BM25 live on different scales, so ranks, not
    scores, are what can be combined. Ties keep first-seen order.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
