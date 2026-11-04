"""The slice of the RAG pipeline the API layer depends on.

Typing against this Protocol (rather than ``RagPipeline``) keeps the web layer
importable without ML libraries and lets tests substitute a fake.
"""

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Protocol

from app.rag.types import IngestResult, RagAnswer, RagEvent, Turn


class RagPort(Protocol):
    def ingest_pdf(
        self,
        *,
        patient_id: str,
        report_id: str,
        report_name: str,
        category: str,
        pdf_path: Path,
    ) -> IngestResult: ...

    def delete_report(self, *, patient_id: str, report_id: str) -> None: ...

    def delete_patient(self, *, patient_id: str) -> None: ...

    def answer(self, *, patient_id: str, question: str, history: Sequence[Turn]) -> RagAnswer: ...

    def answer_stream(
        self, *, patient_id: str, question: str, history: Sequence[Turn]
    ) -> Iterator[RagEvent]: ...

    def warmup(self) -> None: ...
