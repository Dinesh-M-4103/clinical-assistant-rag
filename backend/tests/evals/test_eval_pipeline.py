"""The evaluation stages end to end, over two tiny patients and fake models (no network)."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.rag.config import RagSettings
from app.rag.pipeline import RagPipeline
from evals import report
from evals.answer_eval import evaluate_answers, pass_rate_by_type, summarise_answers
from evals.dataset import GoldenQuestion, ManifestPatient, ManifestReport
from evals.ingest import ingest_corpus
from evals.retrieval_eval import (
    evaluate_retrieval,
    summarise_by_mode,
    summarise_by_type,
    summarise_gate,
)
from tests.rag.fakes import FakeEmbedder, InMemoryVectorStore, OverlapReranker, ScriptedLLM
from tests.rag.pdf_factory import Page, build_pdf

REFUSAL = "not found"


def make_question(
    question_id: str,
    patient_id: str,
    question: str,
    *,
    question_type: str = "temporal",
    report_file: str | None = "rx.pdf",
    must_include: tuple[str, ...] = (),
    must_not_include: tuple[str, ...] = (),
) -> GoldenQuestion:
    return GoldenQuestion(
        id=question_id,
        patient_id=patient_id,
        question=question,
        type=question_type,
        answerable=report_file is not None,
        expected_reports=(report_file,) if report_file else (),
        expected_pages=(1,) if report_file else (),
        must_include=must_include,
        must_not_include=must_not_include,
    )


QUESTIONS = [
    make_question(
        "q1", "P1", "What dose of metformin is prescribed?", must_include=(r"\b500 mg\b",)
    ),
    make_question(
        "q2",
        "P2",
        "What dose of metformin is prescribed?",
        question_type="cross_patient",
        must_not_include=(r"\b500 mg\b",),
    ),
    make_question(
        "q3",
        "P1",
        "zzyzx plugh?",
        question_type="unanswerable",
        report_file=None,
        must_include=(REFUSAL,),
    ),
]


@pytest.fixture
def pipelines(tmp_path: Path) -> dict[str, RagPipeline]:
    patients = []
    for uhid, dose in (("P1", "500 mg twice daily"), ("P2", "1000 mg once daily")):
        directory = tmp_path / "pdfs" / uhid
        directory.mkdir(parents=True)
        page = Page(heading="Medications", paragraphs=[f"Metformin {dose} after meals."])
        build_pdf(directory / "rx.pdf", [page])
        patients.append(ManifestPatient(uhid, (ManifestReport("rx.pdf", "Prescription", "other"),)))

    store = InMemoryVectorStore()
    settings = RagSettings(chroma_dir=tmp_path / "chroma", min_rerank_score=0.05)
    llm = ScriptedLLM("Metformin 500 mg twice daily [C1].")
    built = {
        mode: RagPipeline(
            replace(settings, retrieval_mode=mode),
            embedder=FakeEmbedder(),
            store=store,
            reranker=OverlapReranker(),
            llm=llm,
        )
        for mode in ("dense", "hybrid_rerank")
    }
    ingest_corpus(built["dense"], patients, tmp_path / "pdfs")
    return built


def test_retrieval_is_scored_per_mode_and_per_type(pipelines: dict[str, RagPipeline]) -> None:
    records = evaluate_retrieval(pipelines, QUESTIONS)  # type: ignore[arg-type]

    by_mode = summarise_by_mode(records)
    by_type = summarise_by_type(records)

    assert set(by_mode) == {"dense", "hybrid_rerank"}
    assert by_mode["hybrid_rerank"].questions == 2
    assert by_mode["hybrid_rerank"].hit_at[1] == 1.0
    assert set(by_type) == {"temporal", "cross_patient"}
    assert not any(record.leaked for record in records)
    assert "| hybrid_rerank | 2 |" in report.ablation_table(by_mode)


def test_gate_replay_counts_correct_and_wrongful_refusals(
    pipelines: dict[str, RagPipeline],
) -> None:
    records = evaluate_retrieval(pipelines, QUESTIONS)  # type: ignore[arg-type]

    strict, lenient = summarise_gate(records, QUESTIONS, [0.5, 0.0])

    assert (strict.refused_unanswerable, strict.unanswerable) == (1, 1)
    assert strict.answerable == 2
    assert lenient.refused_unanswerable == 0
    assert lenient.refused_answerable == 0


def test_answers_are_checked_and_aggregated(pipelines: dict[str, RagPipeline]) -> None:
    verdicts = evaluate_answers(pipelines["hybrid_rerank"], QUESTIONS)
    summary = summarise_answers(verdicts)

    assert [v.passed for v in verdicts] == [True, False, True]
    assert verdicts[2].refused_by_gate
    assert (summary.answerable_passed, summary.answerable_total) == (1, 2)
    assert (summary.unanswerable_correct, summary.unanswerable_total) == (1, 1)
    assert (summary.cited_supported, summary.cited_total) == (2, 2)
    assert summary.leaks == 1
    assert pass_rate_by_type(verdicts)["cross_patient"] == (0, 1)
    assert "Cross-patient leaks: 1 / 3" in report.answer_lines(summary)
