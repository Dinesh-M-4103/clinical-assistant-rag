"""Build one RAG pipeline per retrieval mode over a single throw-away vector store."""

import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

from chromadb.errors import InternalError

from app.core.config import Settings
from app.rag.config import RagSettings, RetrievalMode
from app.rag.embeddings import SentenceTransformerEmbedder
from app.rag.errors import LLMUnavailableError
from app.rag.llm import LLMClient, LLMDelta, LLMResult
from app.rag.pipeline import RagPipeline
from app.rag.retrieval.reranker import CrossEncoderReranker
from app.rag.types import Prompt
from app.rag.vectorstore import ChromaVectorStore
from evals.dataset import ManifestPatient
from evals.ingest import ingest_corpus
from evals.paths import HF_CACHE_DIR, PDF_ROOT

BUILD_ATTEMPTS = 4


class OfflineLLM:
    """Stands in for the language model in retrieval-only runs, which must never call it."""

    model_name = "offline"

    def generate(self, prompt: Prompt) -> LLMResult:
        raise LLMUnavailableError("This evaluation run is retrieval-only; no LLM is available.")

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]:
        raise LLMUnavailableError("This evaluation run is retrieval-only; no LLM is available.")


def app_rag_settings() -> RagSettings:
    """The settings the real app would use (``backend/.env`` included)."""
    return replace(Settings().rag_settings(), hf_cache_dir=HF_CACHE_DIR)


@contextmanager
def ingested_pipelines(
    settings: RagSettings,
    modes: Sequence[RetrievalMode],
    patients: list[ManifestPatient],
    llm: LLMClient | None = None,
) -> Iterator[dict[RetrievalMode, RagPipeline]]:
    """Ingest the corpus once into a temporary Chroma directory and yield a pipeline per mode.

    The embedder, reranker and store are shared, so the modes differ only in how they
    rank, which is exactly what an ablation should vary.
    """
    with tempfile.TemporaryDirectory(prefix="clinical-evals-", ignore_cleanup_errors=True) as root:
        embedder = SentenceTransformerEmbedder(settings.embedding_model, settings.hf_cache_dir)
        reranker = CrossEncoderReranker(settings.reranker_model, settings.hf_cache_dir)
        for attempt in range(1, BUILD_ATTEMPTS + 1):
            chroma_dir = Path(root) / f"chroma-{attempt}"
            store = ChromaVectorStore(chroma_dir, embedder.model_name)
            pipelines = {
                mode: RagPipeline(
                    replace(settings, chroma_dir=chroma_dir, retrieval_mode=mode),
                    embedder=embedder,
                    store=store,
                    reranker=reranker,
                    llm=llm or OfflineLLM(),
                )
                for mode in modes
            }
            ingest_corpus(next(iter(pipelines.values())), patients, PDF_ROOT)
            try:
                _assert_searchable(store, embedder, [p.uhid for p in patients])
            except InternalError:
                if attempt == BUILD_ATTEMPTS:
                    raise
                continue
            yield pipelines
            return


def _assert_searchable(
    store: ChromaVectorStore, embedder: SentenceTransformerEmbedder, patient_ids: list[str]
) -> None:
    """Query every collection once, raising ``InternalError`` if Chroma cannot read one.

    On Windows, Chroma 1.5 occasionally leaves a freshly bulk-ingested collection
    unreadable ("Nothing found on disk") for good. Detecting it up front lets the caller
    rebuild the throw-away store instead of failing halfway through an evaluation.
    """
    probe = embedder.embed_query("probe")
    for patient_id in patient_ids:
        store.search(patient_id, probe, 1)
