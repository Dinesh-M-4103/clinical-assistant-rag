"""The RAG pipeline: the one class the API layer talks to.

Reading order of this file is the story of a question:

    route (small talk?) -> rewrite follow-up -> retrieve -> relevance gate
        -> grounded prompt -> LLM -> verify citations -> answer + trace
"""

import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from app.rag import prompts
from app.rag.citations import citation_id, parse_citations, to_citations, to_trace_candidates
from app.rag.config import RagSettings
from app.rag.embeddings import Embedder, SentenceTransformerEmbedder
from app.rag.errors import NoExtractableTextError, RagError
from app.rag.ingestion.chunker import chunk_pages
from app.rag.ingestion.pdf_loader import load_pdf
from app.rag.llm import GeminiClient, LLMClient
from app.rag.query import QueryRewriter, route
from app.rag.ratelimit import RateLimiter
from app.rag.retrieval.bm25 import Bm25Retriever
from app.rag.retrieval.dense import DenseRetriever
from app.rag.retrieval.relevance import has_sufficient_evidence
from app.rag.retrieval.reranker import CrossEncoderReranker, Reranker
from app.rag.retrieval.retriever import HybridRetriever
from app.rag.timing import elapsed_ms, now
from app.rag.types import (
    Candidate,
    Chunk,
    CitationsEvent,
    DoneEvent,
    ErrorEvent,
    IngestResult,
    Intent,
    MetaEvent,
    Prompt,
    RagAnswer,
    RagEvent,
    TokenEvent,
    TokenUsage,
    TraceDTO,
    Turn,
)
from app.rag.vectorstore import ChromaVectorStore, VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Plan:
    """Everything decided before generation: either a canned reply or a prompt for the LLM."""

    intent: Intent
    started: float
    rewritten_query: str | None = None
    candidates: tuple[Candidate, ...] = ()
    insufficient_evidence: bool = False
    reply: str | None = None
    prompt: Prompt | None = None
    timings_ms: Mapping[str, int] = field(default_factory=dict)


class RagPipeline:
    """Ingest PDFs per patient and answer grounded questions about them.

    Collaborators are built lazily from ``settings``; tests (and the evals) may
    inject their own implementations of the small Protocols.
    """

    def __init__(
        self,
        settings: RagSettings,
        *,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
        reranker: Reranker | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._embedder = embedder or SentenceTransformerEmbedder(
            settings.embedding_model, settings.hf_cache_dir
        )
        self._store = store or ChromaVectorStore(settings.chroma_dir, self._embedder.model_name)
        self._reranker = reranker or CrossEncoderReranker(
            settings.reranker_model, settings.hf_cache_dir
        )
        self._llm = llm or GeminiClient(
            model=settings.llm_model,
            api_key=settings.gemini_api_key,
            backend=settings.gemini_backend,
            limiter=RateLimiter(settings.gemini_max_rpm),
        )
        self._retriever = HybridRetriever(
            settings,
            DenseRetriever(self._embedder, self._store),
            Bm25Retriever(self._store),
            self._reranker,
        )
        self._rewriter = QueryRewriter(self._llm)

    # --- Ingestion -------------------------------------------------------------

    def ingest_pdf(
        self, *, patient_id: str, report_id: str, report_name: str, category: str, pdf_path: Path
    ) -> IngestResult:
        """Parse, chunk, embed and store one report. Re-ingesting a report replaces it.

        Raises:
            InvalidPdfError: the file cannot be opened as a PDF.
            NoExtractableTextError: the PDF has no text layer.
        """
        parsed = load_pdf(pdf_path)
        raw_chunks = chunk_pages(
            parsed.pages,
            self._embedder,
            max_tokens=self._settings.chunk_tokens,
            overlap_tokens=self._settings.chunk_overlap_tokens,
        )
        if not raw_chunks:
            raise NoExtractableTextError("The PDF has no extractable text.")
        chunks = [
            Chunk(
                chunk_id=f"{report_id}:{index}",
                report_id=report_id,
                report_name=report_name,
                category=category,
                page=raw.page,
                section=raw.section,
                text=raw.text,
            )
            for index, raw in enumerate(raw_chunks)
        ]
        embeddings = self._embedder.embed_documents([c.contextual_text for c in chunks])
        self._store.delete_report(patient_id, report_id)
        self._store.add_chunks(patient_id, chunks, embeddings)
        self._retriever.invalidate(patient_id)
        return IngestResult(page_count=parsed.page_count, chunk_count=len(chunks))

    def delete_report(self, *, patient_id: str, report_id: str) -> None:
        self._store.delete_report(patient_id, report_id)
        self._retriever.invalidate(patient_id)

    def delete_patient(self, *, patient_id: str) -> None:
        self._store.delete_patient(patient_id)
        self._retriever.invalidate(patient_id)

    def warmup(self) -> None:
        """Load the local models now so the first question is not slow."""
        self._embedder.embed_query("warmup")
        self._reranker.score("warmup", ["warmup"])

    # --- Retrieval only (used by evals) ---------------------------------------

    def retrieve(self, patient_id: str, query: str) -> list[Candidate]:
        """Run retrieval alone, without routing, rewriting or the LLM."""
        return self._retriever.retrieve(patient_id, query).candidates

    # --- Answering -------------------------------------------------------------

    def answer(self, *, patient_id: str, question: str, history: Sequence[Turn] = ()) -> RagAnswer:
        plan = self._plan(patient_id, question, history)
        if plan.prompt is None:
            return self._finish(plan, plan.reply or "", usage=None, generation_ms=0)
        started = now()
        result = self._llm.generate(plan.prompt)
        return self._finish(plan, result.text, result.usage, elapsed_ms(started))

    def answer_stream(
        self, *, patient_id: str, question: str, history: Sequence[Turn] = ()
    ) -> Iterator[RagEvent]:
        """Yield meta, citations, tokens, then done - or a terminal error event.

        Failures become an :class:`ErrorEvent` because an HTTP error status can
        no longer be sent once the stream has started.
        """
        try:
            plan = self._plan(patient_id, question, history)
            yield MetaEvent(plan.intent, plan.rewritten_query)
            yield CitationsEvent(to_citations(plan.candidates))
            if plan.prompt is None:
                reply = plan.reply or ""
                yield TokenEvent(reply)
                yield _to_done(self._finish(plan, reply, usage=None, generation_ms=0))
                return
            started = now()
            parts: list[str] = []
            usage: TokenUsage | None = None
            for delta in self._llm.stream(plan.prompt):
                usage = delta.usage or usage
                if delta.text:
                    parts.append(delta.text)
                    yield TokenEvent(delta.text)
            yield _to_done(self._finish(plan, "".join(parts), usage, elapsed_ms(started)))
        except RagError as error:
            yield ErrorEvent(error.code, str(error))
        except Exception:
            logger.exception("Unexpected failure while streaming an answer")
            yield ErrorEvent("internal_error", "Something went wrong while answering.")

    def _plan(self, patient_id: str, question: str, history: Sequence[Turn]) -> _Plan:
        """Decide how to answer: canned reply, insufficient evidence, or an LLM prompt."""
        started = now()
        history = history[max(len(history) - self._settings.history_turns, 0) :]
        routed = route(question)
        if routed:
            return _Plan(routed.intent, started, reply=routed.reply)

        step = now()
        rewritten = self._rewriter.rewrite(question, history)
        timings = {"rewrite": elapsed_ms(step) if history else 0}
        retrieval = self._retriever.retrieve(patient_id, rewritten)
        timings |= {"retrieval": retrieval.retrieval_ms, "rerank": retrieval.rerank_ms}

        rewritten_query = rewritten if history else None
        if not has_sufficient_evidence(retrieval.candidates, self._settings.min_rerank_score):
            return _Plan(
                "question",
                started,
                rewritten_query=rewritten_query,
                insufficient_evidence=True,
                reply=prompts.INSUFFICIENT_EVIDENCE_REPLY,
                timings_ms=timings,
            )
        return _Plan(
            "question",
            started,
            rewritten_query=rewritten_query,
            candidates=tuple(retrieval.candidates),
            prompt=prompts.build_answer_prompt(question, history, retrieval.candidates),
            timings_ms=timings,
        )

    def _finish(
        self, plan: _Plan, raw_answer: str, usage: TokenUsage | None, generation_ms: int
    ) -> RagAnswer:
        """Verify citations against the retrieved set and attach the trace."""
        valid_ids = [citation_id(position) for position in range(len(plan.candidates))]
        parsed = parse_citations(raw_answer.strip(), valid_ids)
        timings = {"rewrite": 0, "retrieval": 0, "rerank": 0, **plan.timings_ms}
        timings |= {"generation": generation_ms, "total": elapsed_ms(plan.started)}
        trace = TraceDTO(
            intent=plan.intent,
            rewritten_query=plan.rewritten_query,
            insufficient_evidence=plan.insufficient_evidence,
            candidates=to_trace_candidates(plan.candidates),
            timings_ms=timings,
            models={
                "llm": self._llm.model_name,
                "embedding": self._embedder.model_name,
                "reranker": self._reranker.model_name,
            },
            tokens=usage,
        )
        return RagAnswer(parsed.text, to_citations(plan.candidates, parsed.cited_ids), trace)


def _to_done(answer: RagAnswer) -> DoneEvent:
    return DoneEvent(answer.answer, answer.citations, answer.trace)
