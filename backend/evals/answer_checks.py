"""Deterministic answer checks: regexes and citation pages, never an LLM judge."""

import re
from dataclasses import dataclass

from app.rag.types import RagAnswer
from evals.dataset import GoldenQuestion
from evals.ingest import file_name_of, owner_of
from evals.metrics import Source


@dataclass(frozen=True)
class AnswerVerdict:
    """Everything the evaluation records about one answer."""

    question_id: str
    question_type: str
    answerable: bool
    answer: str
    missing: tuple[str, ...]
    """``must_include`` patterns the answer does not match."""
    forbidden: tuple[str, ...]
    """``must_not_include`` patterns the answer does match."""
    refused_by_gate: bool
    cited: tuple[Source, ...]
    cited_supported: int
    """How many of ``cited`` are expected (report, page) sources."""
    foreign_citation: bool
    """A retrieved chunk came from another patient's report."""

    @property
    def passed(self) -> bool:
        return not self.missing and not self.forbidden

    @property
    def leaked(self) -> bool:
        """Cross-patient leak: foreign evidence retrieved, or another patient's value stated."""
        return self.foreign_citation or (
            self.question_type == "cross_patient" and bool(self.forbidden)
        )


def check_answer(question: GoldenQuestion, answer: RagAnswer) -> AnswerVerdict:
    cited = tuple((file_name_of(c.report_id), c.page) for c in answer.citations if c.cited)
    expected = question.expected_sources
    return AnswerVerdict(
        question_id=question.id,
        question_type=question.type,
        answerable=question.answerable,
        answer=answer.answer,
        missing=tuple(p for p in question.must_include if not _matches(p, answer.answer)),
        forbidden=tuple(p for p in question.must_not_include if _matches(p, answer.answer)),
        refused_by_gate=answer.trace.insufficient_evidence,
        cited=cited,
        cited_supported=sum(source in expected for source in cited),
        foreign_citation=any(
            owner_of(c.report_id) != question.patient_id for c in answer.citations
        ),
    )


def _matches(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None
