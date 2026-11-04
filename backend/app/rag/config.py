"""Runtime configuration for the RAG package.

A plain frozen dataclass on purpose: the API layer builds it from its own
settings object, which keeps this package free of web-framework dependencies.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RetrievalMode = Literal["dense", "bm25", "hybrid", "hybrid_rerank"]
GeminiBackend = Literal["studio", "vertex"]

DEFAULT_MIN_RERANK_SCORE = 0.001
"""Relevance gate for ``cross-encoder/ms-marco-MiniLM-L-6-v2`` (sigmoid-normalised scores).

Calibrated by probing the six synthetic patients (26 reports) with the best rerank score of
23 answerable and 35 unanswerable questions (blood group, MRI, COVID vaccine, "how do I bake
a cake", ...). Unrelated passages sit at the model's noise floor (0.0001 - 0.0003); answerable
questions scored between 0.0012 and 0.999 with one outlier at 0.0003. At 0.001, 33 of the 35
unanswerable questions are refused without an LLM call, and the two that pass (a real
"tuberculosis" mention at 0.17, "blood group" next to a blood-group section at 0.017) are left
to the prompt's "not found" rule. The threshold is deliberately low: a false refusal hides
information from the clinician, whereas a weak citation is visible and harmless.
Re-calibrate whenever the reranker model changes.
"""


@dataclass(frozen=True)
class RagSettings:
    """Everything the pipeline needs; defaults mirror ``docs/api-contract.md``."""

    chroma_dir: Path
    hf_cache_dir: Path | None = None
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "gemini-3.5-flash-lite"
    gemini_api_key: str | None = None
    gemini_backend: GeminiBackend = "studio"
    gemini_max_rpm: int = 8
    chunk_tokens: int = 300
    chunk_overlap_tokens: int = 50
    dense_k: int = 20
    bm25_k: int = 20
    rerank_top_n: int = 5
    min_rerank_score: float = DEFAULT_MIN_RERANK_SCORE
    history_turns: int = 6
    retrieval_mode: RetrievalMode = "hybrid_rerank"
