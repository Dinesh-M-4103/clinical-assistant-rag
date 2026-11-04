"""Text embeddings: a small Protocol plus the sentence-transformers implementation."""

from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from app.rag.model_cache import load_cached_first

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
"""Prefix the BGE authors recommend for short search queries (not for documents)."""
EMBED_BATCH_SIZE = 32


class Embedder(Protocol):
    """Maps text to unit-length vectors and counts tokens the way the model sees them."""

    @property
    def model_name(self) -> str: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...

    def count_tokens(self, text: str) -> int: ...


class SentenceTransformerEmbedder:
    """Local embedding model, loaded on first use so app start-up stays fast."""

    def __init__(self, model_name: str, cache_dir: Path | None = None) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir

    @property
    def model_name(self) -> str:
        return self._model_name

    @cached_property
    def _model(self) -> "SentenceTransformer":
        # Imported here: torch takes seconds to import and tests/CLIs may never need it.
        from sentence_transformers import SentenceTransformer

        return load_cached_first(SentenceTransformer, self._model_name, self._cache_dir)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._encode(list(texts))

    def embed_query(self, text: str) -> list[float]:
        prefix = BGE_QUERY_INSTRUCTION if "bge" in self._model_name.lower() else ""
        return self._encode([prefix + text])[0]

    def count_tokens(self, text: str) -> int:
        """Token count under the embedding model's own tokenizer (no network, no tiktoken)."""
        return len(self._model.tokenizer.encode(text, add_special_tokens=False))

    def _encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors]
