"""In-memory stand-in for ``RagPipeline`` so API tests never load ML models."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from app.rag.types import (
    CandidateTraceDTO,
    CitationDTO,
    CitationsEvent,
    DoneEvent,
    IngestResult,
    MetaEvent,
    RagAnswer,
    RagEvent,
    TokenEvent,
    TokenUsage,
    TraceDTO,
    Turn,
)


def sample_answer() -> RagAnswer:
    """A realistic answer: two retrieved chunks, one of which was cited."""
    return RagAnswer(
        answer="HbA1c was 7.8% on 2025-03-02 [C1].",
        citations=[
            CitationDTO(
                id="C1",
                report_id="11111111-1111-4111-8111-111111111111",
                report_name="Diabetes Panel",
                category="lab",
                page=2,
                section="Laboratory Results",
                text="HbA1c 7.8 %",
                score=0.91,
                cited=True,
            ),
            CitationDTO(
                id="C2",
                report_id="11111111-1111-4111-8111-111111111111",
                report_name="Diabetes Panel",
                category="lab",
                page=1,
                section=None,
                text="Fasting glucose 142 mg/dL",
                score=0.42,
                cited=False,
            ),
        ],
        trace=TraceDTO(
            intent="question",
            rewritten_query="latest HbA1c value",
            insufficient_evidence=False,
            candidates=[
                CandidateTraceDTO("C1", 1, 3, 0.031, 0.91),
                CandidateTraceDTO("C2", 2, None, 0.016, 0.42),
            ],
            timings_ms={"rewrite": 210, "retrieval": 35, "rerank": 120, "generation": 900},
            models={"llm": "fake-llm", "embedding": "fake-embed", "reranker": "fake-rerank"},
            tokens=TokenUsage(prompt=1200, completion=180),
        ),
    )


@dataclass
class FakePipeline:
    """Records every call and fails on demand; satisfies ``RagPort`` structurally."""

    page_count: int = 3
    chunk_count: int = 7
    result: RagAnswer = field(default_factory=sample_answer)
    ingest_error: Exception | None = None
    delete_error: Exception | None = None
    answer_error: Exception | None = None
    stream_error: Exception | None = None
    stream_events: list[RagEvent] | None = None

    ingested: list[dict[str, object]] = field(default_factory=list)
    deleted_reports: list[tuple[str, str]] = field(default_factory=list)
    deleted_patients: list[str] = field(default_factory=list)
    questions: list[tuple[str, str, list[Turn]]] = field(default_factory=list)
    warmed_up: bool = False

    def ingest_pdf(
        self,
        *,
        patient_id: str,
        report_id: str,
        report_name: str,
        category: str,
        pdf_path: Path,
    ) -> IngestResult:
        self.ingested.append(
            {
                "patient_id": patient_id,
                "report_id": report_id,
                "report_name": report_name,
                "category": category,
                "pdf_path": pdf_path,
                "file_existed": pdf_path.is_file(),
            }
        )
        if self.ingest_error is not None:
            raise self.ingest_error
        return IngestResult(page_count=self.page_count, chunk_count=self.chunk_count)

    def delete_report(self, *, patient_id: str, report_id: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted_reports.append((patient_id, report_id))

    def delete_patient(self, *, patient_id: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted_patients.append(patient_id)

    def answer(self, *, patient_id: str, question: str, history: Sequence[Turn]) -> RagAnswer:
        self.questions.append((patient_id, question, list(history)))
        if self.answer_error is not None:
            raise self.answer_error
        return self.result

    def answer_stream(
        self, *, patient_id: str, question: str, history: Sequence[Turn]
    ) -> Iterator[RagEvent]:
        self.questions.append((patient_id, question, list(history)))
        if self.stream_events is not None:
            yield from self.stream_events
            return
        yield MetaEvent(intent="question", rewritten_query="latest HbA1c value")
        if self.stream_error is not None:
            raise self.stream_error
        yield CitationsEvent(
            citations=[replace(citation, cited=False) for citation in self.result.citations]
        )
        for word in self.result.answer.split(" "):
            yield TokenEvent(text=f"{word} ")
        yield DoneEvent(
            answer=self.result.answer, citations=self.result.citations, trace=self.result.trace
        )

    def warmup(self) -> None:
        self.warmed_up = True
