"""Cross-encoder re-ranking: reads query and passage together for a sharper relevance score."""

import math
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from app.rag.model_cache import load_cached_first

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

MAX_PASSAGE_TOKENS = 512


class Reranker(Protocol):
    @property
    def model_name(self) -> str: ...

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        """Relevance of each passage to the query, as a probability-like value in [0, 1]."""
        ...


class CrossEncoderReranker:
    """Local cross-encoder, loaded on first use."""

    def __init__(self, model_name: str, cache_dir: Path | None = None) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir

    @property
    def model_name(self) -> str:
        return self._model_name

    @cached_property
    def _model(self) -> "CrossEncoder":
        # Imported here: torch takes seconds to import and tests/CLIs may never need it.
        from sentence_transformers import CrossEncoder

        model: CrossEncoder = load_cached_first(
            CrossEncoder, self._model_name, self._cache_dir, max_length=MAX_PASSAGE_TOKENS
        )
        return model

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        """Sigmoid of the raw logits, so scores are comparable and thresholdable."""
        if not passages:
            return []
        logits = self._model.predict([(query, passage) for passage in passages])
        return [_sigmoid(float(logit)) for logit in logits]


def _sigmoid(value: float) -> float:
    """Numerically stable logistic function (no overflow for large negative logits)."""
    return 0.5 * (1.0 + math.tanh(value / 2.0))
