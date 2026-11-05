"""Generate answers for the golden questions and aggregate the deterministic checks."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from app.rag.pipeline import RagPipeline
from evals.answer_checks import AnswerVerdict, check_answer
from evals.dataset import GoldenQuestion

INJECTION = "injection"


@dataclass(frozen=True)
class AnswerSummary:
    """Headline answer-quality numbers; every rate is ``count / total`` so none is rounded away."""

    answerable_passed: int
    answerable_total: int
    unanswerable_correct: int
    unanswerable_total: int
    injection_resisted: int
    injection_total: int
    leaks: int
    questions: int
    cited_supported: int
    cited_total: int
    answers_without_citation: int
    """Answerable questions whose answer cites no chunk at all."""


def evaluate_answers(
    pipeline: RagPipeline, questions: Sequence[GoldenQuestion]
) -> list[AnswerVerdict]:
    """Ask every question (with its conversation history) and check each answer."""
    return [
        check_answer(
            question,
            pipeline.answer(
                patient_id=question.patient_id, question=question.question, history=question.history
            ),
        )
        for question in questions
    ]


def summarise_answers(verdicts: Sequence[AnswerVerdict]) -> AnswerSummary:
    answerable = [v for v in verdicts if v.answerable]
    unanswerable = [v for v in verdicts if not v.answerable]
    injections = [v for v in verdicts if v.question_type == INJECTION]
    return AnswerSummary(
        answerable_passed=sum(v.passed for v in answerable),
        answerable_total=len(answerable),
        unanswerable_correct=sum(v.passed for v in unanswerable),
        unanswerable_total=len(unanswerable),
        injection_resisted=sum(not v.forbidden for v in injections),
        injection_total=len(injections),
        leaks=sum(v.leaked for v in verdicts),
        questions=len(verdicts),
        cited_supported=sum(v.cited_supported for v in answerable),
        cited_total=sum(len(v.cited) for v in answerable),
        answers_without_citation=sum(not v.cited for v in answerable),
    )


def pass_rate_by_type(verdicts: Sequence[AnswerVerdict]) -> dict[str, tuple[int, int]]:
    """``{question type: (passed, total)}`` over every question, refusals included."""
    grouped: dict[str, list[AnswerVerdict]] = defaultdict(list)
    for verdict in verdicts:
        grouped[verdict.question_type].append(verdict)
    return {t: (sum(v.passed for v in rows), len(rows)) for t, rows in sorted(grouped.items())}
