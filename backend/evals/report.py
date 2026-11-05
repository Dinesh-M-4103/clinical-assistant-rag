"""Markdown tables for the evaluation results."""

from collections.abc import Mapping, Sequence

from evals.answer_eval import AnswerSummary
from evals.retrieval_eval import GateOutcome, RetrievalSummary


def ablation_table(by_mode: Mapping[str, RetrievalSummary]) -> str:
    header = (
        "| Mode | Questions | hit@1 | hit@3 | hit@5 | MRR@5 | recall@1 | recall@3 | recall@5 "
        "| Mean latency (ms) |"
    )
    rows = [
        f"| {mode} | {s.questions} | {s.hit_at[1]:.3f} | {s.hit_at[3]:.3f} | {s.hit_at[5]:.3f} "
        f"| {s.mrr:.3f} | {s.recall_at[1]:.3f} | {s.recall_at[3]:.3f} | {s.recall_at[5]:.3f} "
        f"| {s.latency_ms:.0f} |"
        for mode, s in by_mode.items()
    ]
    return _table(header, rows)


def type_table(by_type: Mapping[str, Mapping[str, RetrievalSummary]]) -> str:
    """One row per question type, each mode shown as ``hit@1 / hit@5``."""
    modes = list(next(iter(by_type.values()))) if by_type else []
    header = "| Question type | n | " + " | ".join(f"{m} (hit@1 / hit@5)" for m in modes) + " |"
    rows = [
        f"| {question_type} | {next(iter(per_mode.values())).questions} | "
        + " | ".join(f"{per_mode[m].hit_at[1]:.2f} / {per_mode[m].hit_at[5]:.2f}" for m in modes)
        + " |"
        for question_type, per_mode in by_type.items()
    ]
    return _table(header, rows)


def gate_table(outcomes: Sequence[GateOutcome]) -> str:
    """One row per threshold: correct refusals against wrongful refusals."""
    header = "| Gate threshold | Unanswerable refused | Answerable wrongly refused |"
    rows = [
        f"| {o.threshold:g} | {o.refused_unanswerable} / {o.unanswerable} "
        f"| {o.refused_answerable} / {o.answerable} |"
        for o in outcomes
    ]
    return _table(header, rows)


def answer_lines(summary: AnswerSummary) -> str:
    return "\n".join(
        [
            _rate(
                "Answerable questions passing must_include / must_not_include",
                summary.answerable_passed,
                summary.answerable_total,
            ),
            _rate(
                "Unanswerable questions handled correctly (refusal, nothing forbidden)",
                summary.unanswerable_correct,
                summary.unanswerable_total,
            ),
            _rate(
                "Injection questions resisted (no forbidden text in the answer)",
                summary.injection_resisted,
                summary.injection_total,
            ),
            _rate(
                "Cited chunks that sit on an expected (report, page)",
                summary.cited_supported,
                summary.cited_total,
            ),
            f"- Answerable questions that cite nothing: {summary.answers_without_citation}",
            _rate("Cross-patient leaks", summary.leaks, summary.questions),
        ]
    )


def answer_type_table(rates: Mapping[str, tuple[int, int]]) -> str:
    rows = [f"| {t} | {passed} / {total} |" for t, (passed, total) in rates.items()]
    return _table("| Question type | Passed |", rows)


def _rate(label: str, count: int, total: int) -> str:
    share = f"{count / total:.3f}" if total else "n/a"
    return f"- {label}: {count} / {total} ({share})"


def _table(header: str, rows: Sequence[str]) -> str:
    columns = header.count("|") - 1
    separator = "|" + "---|" * columns
    return "\n".join([header, separator, *rows])
