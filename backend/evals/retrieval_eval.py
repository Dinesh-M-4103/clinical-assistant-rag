"""Run the golden questions through each retrieval mode and aggregate the metrics.

Retrieval needs no language model, so this stage costs nothing in API quota. Follow-up
questions are searched with their literal text: rewriting them into standalone queries is
an LLM step that only the answer evaluation exercises.
"""

import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from app.rag.config import RetrievalMode
from app.rag.pipeline import RagPipeline
from evals.dataset import GoldenQuestion
from evals.ingest import file_name_of, owner_of
from evals.metrics import CUTOFFS, RetrievalScores, Source, mean, score_question

FOLLOWUP = "followup"


@dataclass(frozen=True)
class RetrievalRecord:
    """One question under one retrieval mode."""

    question_id: str
    question_type: str
    mode: RetrievalMode
    ranked: tuple[Source, ...]
    latency_ms: float
    best_rerank_score: float | None
    """Top cross-encoder score (``hybrid_rerank`` only); what the relevance gate looks at."""
    leaked: bool
    scores: RetrievalScores | None
    """``None`` for questions without expected sources (the records cannot answer them)."""


@dataclass(frozen=True)
class RetrievalSummary:
    """Mean metrics over a group of scored questions."""

    questions: int
    hit_at: dict[int, float]
    mrr: float
    recall_at: dict[int, float]
    latency_ms: float


def evaluate_retrieval(
    pipelines: Mapping[RetrievalMode, RagPipeline],
    questions: Sequence[GoldenQuestion],
    clock: Callable[[], float] = time.perf_counter,
) -> list[RetrievalRecord]:
    """Retrieve for every question in every mode (the pipelines share one vector store)."""
    records: list[RetrievalRecord] = []
    for mode, pipeline in pipelines.items():
        for question in questions:
            started = clock()
            candidates = pipeline.retrieve(question.patient_id, question.question)
            latency_ms = (clock() - started) * 1000
            ranked = tuple((file_name_of(c.chunk.report_id), c.chunk.page) for c in candidates)
            expected = question.expected_sources
            records.append(
                RetrievalRecord(
                    question_id=question.id,
                    question_type=question.type,
                    mode=mode,
                    ranked=ranked,
                    latency_ms=latency_ms,
                    best_rerank_score=max(
                        (c.rerank_score for c in candidates if c.rerank_score is not None),
                        default=None,
                    ),
                    leaked=any(
                        owner_of(c.chunk.report_id) != question.patient_id for c in candidates
                    ),
                    scores=score_question(ranked, expected) if expected else None,
                )
            )
    return records


def summarise(records: Sequence[RetrievalRecord]) -> RetrievalSummary:
    scored = [r for r in records if r.scores is not None]
    scores = [r.scores for r in scored if r.scores is not None]
    return RetrievalSummary(
        questions=len(scored),
        hit_at={k: mean([float(s.hits_at[k]) for s in scores]) for k in CUTOFFS},
        mrr=mean([s.reciprocal_rank for s in scores]),
        recall_at={k: mean([s.recall_at[k] for s in scores]) for k in CUTOFFS},
        latency_ms=mean([r.latency_ms for r in scored]),
    )


def summarise_by_mode(records: Sequence[RetrievalRecord]) -> dict[str, RetrievalSummary]:
    return {mode: summarise([r for r in records if r.mode == mode]) for mode in _modes(records)}


def summarise_by_type(
    records: Sequence[RetrievalRecord],
) -> dict[str, dict[str, RetrievalSummary]]:
    """``{question type: {mode: summary}}``, skipping types with no scored question."""
    grouped: dict[str, list[RetrievalRecord]] = defaultdict(list)
    for record in records:
        if record.scores is not None:
            grouped[record.question_type].append(record)
    return {
        question_type: {
            mode: summarise([r for r in rows if r.mode == mode]) for mode in _modes(rows)
        }
        for question_type, rows in sorted(grouped.items())
    }


@dataclass(frozen=True)
class GateOutcome:
    """What the relevance gate would do at one threshold (``hybrid_rerank`` scores only)."""

    threshold: float
    refused_unanswerable: int
    unanswerable: int
    refused_answerable: int
    answerable: int


GATE_SWEEP = (0.00001, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05)


def summarise_gate(
    records: Sequence[RetrievalRecord],
    questions: Sequence[GoldenQuestion],
    thresholds: Sequence[float],
) -> list[GateOutcome]:
    """Replay the gate at each threshold using the recorded best rerank scores.

    Follow-ups are left out: searched without rewriting, their scores say nothing about the gate.
    """
    answerable = {q.id: q.answerable for q in questions if q.type != FOLLOWUP}
    scores = {
        r.question_id: r.best_rerank_score
        for r in records
        if r.mode == "hybrid_rerank" and r.question_id in answerable
    }
    outcomes = []
    for threshold in thresholds:
        refused = {i for i, score in scores.items() if score is None or score < threshold}
        outcomes.append(
            GateOutcome(
                threshold=threshold,
                refused_unanswerable=sum(not answerable[i] for i in refused),
                unanswerable=sum(not answerable[i] for i in scores),
                refused_answerable=sum(answerable[i] for i in refused),
                answerable=sum(answerable[i] for i in scores),
            )
        )
    return outcomes


def _modes(records: Sequence[RetrievalRecord]) -> list[RetrievalMode]:
    return list(dict.fromkeys(r.mode for r in records))
