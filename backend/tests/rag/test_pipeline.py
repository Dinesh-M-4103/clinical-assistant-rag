from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from app.rag import prompts
from app.rag.config import RagSettings
from app.rag.errors import EmbeddingModelMismatchError, LLMUnavailableError, NoExtractableTextError
from app.rag.pipeline import RagPipeline
from app.rag.types import (
    CitationsEvent,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
    Prompt,
    TokenEvent,
    Turn,
)

from .fakes import (
    FailingVectorStore,
    FakeEmbedder,
    InMemoryVectorStore,
    OverlapReranker,
    ScriptedLLM,
)
from .pdf_factory import Page, build_blank_pdf, build_pdf

GATE = 0.3


class RoutingLLM(ScriptedLLM):
    """Answers rewrite prompts and answer prompts differently, like the real model would."""

    def __init__(self, answer: str, rewrite: str) -> None:
        super().__init__(answer)
        self.rewrite = rewrite

    def generate(self, prompt: Prompt):  # type: ignore[no-untyped-def]
        result = super().generate(prompt)
        if prompt.system == prompts.REWRITE_SYSTEM:
            return type(result)(self.rewrite, result.usage)
        return result


def make_pipeline(
    tmp_path: Path,
    llm: ScriptedLLM | None = None,
    store: InMemoryVectorStore | None = None,
    **overrides: Any,
) -> tuple[RagPipeline, ScriptedLLM, InMemoryVectorStore]:
    settings = replace(
        RagSettings(chroma_dir=tmp_path / "chroma", min_rerank_score=GATE), **overrides
    )
    llm = llm or ScriptedLLM("Metformin 500 mg twice daily [C1].")
    store = store or InMemoryVectorStore()
    pipeline = RagPipeline(
        settings, embedder=FakeEmbedder(), store=store, reranker=OverlapReranker(), llm=llm
    )
    return pipeline, llm, store


def ingest(
    pipeline: RagPipeline,
    tmp_path: Path,
    *,
    patient: str = "p1",
    report: str = "r1",
    pages: list[Page] | None = None,
) -> None:
    pages = pages or [
        Page(heading="Medications", paragraphs=["Metformin 500 mg twice daily for diabetes."])
    ]
    pdf = build_pdf(tmp_path / f"{patient}-{report}.pdf", pages, header=None)
    pipeline.ingest_pdf(
        patient_id=patient,
        report_id=report,
        report_name=f"Report {report}",
        category="prescription",
        pdf_path=pdf,
    )


# --- ingestion ---------------------------------------------------------------------------


def test_ingest_reports_pages_and_chunks_and_stores_report_metadata(tmp_path: Path) -> None:
    pipeline, _, store = make_pipeline(tmp_path)
    pdf = build_pdf(
        tmp_path / "multi.pdf",
        [
            Page(heading="Medications", paragraphs=["Metformin 500 mg twice daily."]),
            Page(heading="Plan", paragraphs=["Review in three months."]),
        ],
        header=None,
    )

    result = pipeline.ingest_pdf(
        patient_id="p1", report_id="r1", report_name="Rx", category="prescription", pdf_path=pdf
    )

    chunks = store.all_chunks("p1")
    assert (result.page_count, result.chunk_count) == (2, len(chunks))
    assert [(c.page, c.section) for c in chunks] == [(1, "Medications"), (2, "Plan")]
    assert {c.report_id for c in chunks} == {"r1"}
    assert chunks[0].chunk_id == "r1:0"


def test_reingesting_a_report_replaces_its_chunks(tmp_path: Path) -> None:
    pipeline, _, store = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path)
    ingest(pipeline, tmp_path, pages=[Page(paragraphs=["Insulin glargine 20 units nightly."])])

    texts = " ".join(c.text for c in store.all_chunks("p1"))
    assert "Insulin" in texts
    assert "Metformin" not in texts


def test_a_pdf_without_text_is_rejected(tmp_path: Path) -> None:
    blank = build_blank_pdf(tmp_path / "scan.pdf")
    pipeline, _, _ = make_pipeline(tmp_path)

    with pytest.raises(NoExtractableTextError):
        pipeline.ingest_pdf(
            patient_id="p1", report_id="r1", report_name="Scan", category="other", pdf_path=blank
        )


def test_deleting_a_report_or_patient_removes_it_from_keyword_and_vector_search(
    tmp_path: Path,
) -> None:
    pipeline, _, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path, report="r1")
    ingest(pipeline, tmp_path, report="r2", pages=[Page(paragraphs=["Warfarin 5 mg at night."])])
    assert pipeline.retrieve("p1", "warfarin")

    pipeline.delete_report(patient_id="p1", report_id="r2")
    assert all("Warfarin" not in c.chunk.text for c in pipeline.retrieve("p1", "warfarin"))

    pipeline.delete_patient(patient_id="p1")
    assert pipeline.retrieve("p1", "metformin") == []


# --- answering -----------------------------------------------------------------------------


def test_a_grounded_answer_flags_the_citations_the_model_used(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path)

    answer = pipeline.answer(patient_id="p1", question="metformin dose", history=[])

    assert answer.answer == "Metformin 500 mg twice daily [C1]."
    assert [(c.id, c.cited) for c in answer.citations] == [("C1", True)]
    assert answer.citations[0].report_name == "Report r1"
    assert answer.citations[0].page == 1
    assert answer.trace.intent == "question"
    assert not answer.trace.insufficient_evidence
    assert [c.id for c in answer.trace.candidates] == ["C1"]
    assert answer.trace.tokens is not None
    assert answer.trace.models == {
        "llm": "fake-llm",
        "embedding": "fake-embedder",
        "reranker": "fake-reranker",
    }
    assert set(answer.trace.timings_ms) == {"rewrite", "retrieval", "rerank", "generation", "total"}
    assert len(llm.prompts) == 1
    assert 'id="C1"' in llm.prompts[0].user


def test_citations_to_unknown_sources_are_removed_from_the_answer(tmp_path: Path) -> None:
    llm = ScriptedLLM("Dose is 500 mg [C1][C4].")
    pipeline, _, _ = make_pipeline(tmp_path, llm)
    ingest(pipeline, tmp_path)

    answer = pipeline.answer(patient_id="p1", question="metformin dose", history=[])

    assert answer.answer == "Dose is 500 mg [C1]."


def test_retrieved_but_unused_chunks_are_returned_uncited(tmp_path: Path) -> None:
    llm = ScriptedLLM("Answer without any marker.")
    pipeline, _, _ = make_pipeline(tmp_path, llm)
    ingest(pipeline, tmp_path)

    answer = pipeline.answer(patient_id="p1", question="metformin dose", history=[])

    assert [c.cited for c in answer.citations] == [False]


def test_small_talk_is_answered_without_retrieval_or_the_llm(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)

    answer = pipeline.answer(patient_id="p1", question="Hello!", history=[])

    assert answer.answer == prompts.GREETING_REPLY
    assert answer.trace.intent == "greeting"
    assert answer.citations == []
    assert llm.prompts == []


def test_relevance_gate_refuses_without_calling_the_llm(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path)

    answer = pipeline.answer(patient_id="p1", question="blood group of the patient", history=[])

    assert answer.answer == prompts.INSUFFICIENT_EVIDENCE_REPLY
    assert answer.trace.insufficient_evidence
    assert answer.citations == []
    assert answer.trace.candidates == []
    assert llm.prompts == []


def test_a_patient_without_any_reports_gets_the_not_found_answer(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)

    answer = pipeline.answer(patient_id="empty", question="metformin dose", history=[])

    assert answer.trace.insufficient_evidence
    assert llm.prompts == []


def test_one_patient_never_sees_another_patients_records(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path, patient="p1", report="r1")
    ingest(
        pipeline,
        tmp_path,
        patient="p2",
        report="r2",
        pages=[Page(paragraphs=["Insulin glargine 20 units nightly for diabetes."])],
    )

    answer = pipeline.answer(
        patient_id="p2", question="What metformin dose for diabetes?", history=[]
    )

    retrieved = [c.chunk for c in pipeline.retrieve("p2", "metformin dose diabetes")]
    assert retrieved
    assert {c.report_id for c in retrieved} == {"r2"}
    assert all("Metformin" not in c.text for c in retrieved)
    assert all("Metformin" not in c.text for c in answer.citations)
    assert all("Metformin" not in p.user for p in llm.prompts)


def test_history_is_trimmed_and_the_follow_up_is_rewritten_for_retrieval(tmp_path: Path) -> None:
    llm = RoutingLLM(answer="Dose [C1].", rewrite="metformin dose")
    pipeline, _, _ = make_pipeline(tmp_path, llm, history_turns=2)
    ingest(pipeline, tmp_path)
    history = [
        Turn("user", "OLDEST turn"),
        Turn("assistant", "Previous answer about metformin"),
        Turn("user", "Which drug was that?"),
    ]

    answer = pipeline.answer(patient_id="p1", question="and its dose?", history=history)

    assert answer.trace.rewritten_query == "metformin dose"
    assert answer.citations
    answer_prompt = llm.prompts[-1].user
    assert "OLDEST turn" not in answer_prompt
    assert "Which drug was that?" in answer_prompt
    assert answer_prompt.rstrip().endswith("Question: and its dose?")


def test_rewrite_failure_falls_back_to_the_original_question(tmp_path: Path) -> None:
    class FlakyLLM(ScriptedLLM):
        def generate(self, prompt: Prompt):  # type: ignore[no-untyped-def]
            if prompt.system == prompts.REWRITE_SYSTEM:
                raise LLMUnavailableError("rewrite down")
            return super().generate(prompt)

    pipeline, _, _ = make_pipeline(tmp_path, FlakyLLM("Dose [C1]."))
    ingest(pipeline, tmp_path)

    answer = pipeline.answer(
        patient_id="p1", question="metformin dose", history=[Turn("user", "hi there doc")]
    )

    assert answer.trace.rewritten_query == "metformin dose"
    assert answer.citations


def test_llm_failure_propagates_from_answer(tmp_path: Path) -> None:
    pipeline, _, _ = make_pipeline(tmp_path, ScriptedLLM(fail_with=LLMUnavailableError("down")))
    ingest(pipeline, tmp_path)

    with pytest.raises(LLMUnavailableError):
        pipeline.answer(patient_id="p1", question="metformin dose", history=[])


# --- retrieval modes --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "dense", "bm25", "reranked"),
    [
        ("dense", True, False, False),
        ("bm25", False, True, False),
        ("hybrid", True, True, False),
        ("hybrid_rerank", True, True, True),
    ],
)
def test_retrieval_mode_selects_which_stages_contribute(
    tmp_path: Path, mode: str, dense: bool, bm25: bool, reranked: bool
) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path, retrieval_mode=mode)
    ingest(pipeline, tmp_path)

    candidates = pipeline.retrieve("p1", "metformin dose")

    assert candidates
    first = candidates[0]
    assert (first.dense_rank is not None) is dense
    assert (first.bm25_rank is not None) is bm25
    assert (first.rerank_score is not None) is reranked
    assert llm.prompts == []


def test_rerank_reorders_candidates_by_cross_encoder_score(tmp_path: Path) -> None:
    pipeline, _, _ = make_pipeline(tmp_path, rerank_top_n=2)
    ingest(
        pipeline,
        tmp_path,
        pages=[
            Page(paragraphs=["Aspirin 75 mg daily."]),
            Page(paragraphs=["Atorvastatin 40 mg at night."]),
            Page(paragraphs=["Atorvastatin and aspirin were reviewed."]),
        ],
    )

    candidates = pipeline.retrieve("p1", "atorvastatin aspirin")

    scores = [c.rerank_score or 0.0 for c in candidates]
    assert len(candidates) == 2
    assert scores == sorted(scores, reverse=True)
    assert candidates[0].chunk.page == 3


def test_candidates_report_ranks_from_both_retrievers_and_the_fused_score(tmp_path: Path) -> None:
    pipeline, _, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path)

    best = pipeline.retrieve("p1", "metformin dose")[0]

    assert best.dense_rank == 1
    assert best.bm25_rank == 1
    assert best.fused_score == pytest.approx(2 / 61)


# --- streaming ----------------------------------------------------------------------------------


def test_stream_emits_meta_citations_tokens_then_the_authoritative_done(tmp_path: Path) -> None:
    pipeline, _, _ = make_pipeline(tmp_path)
    ingest(pipeline, tmp_path)

    events = list(pipeline.answer_stream(patient_id="p1", question="metformin dose", history=[]))

    meta, citations, *tokens, done = events
    assert isinstance(meta, MetaEvent) and meta.intent == "question"
    assert isinstance(citations, CitationsEvent) and [c.cited for c in citations.citations] == [
        False
    ]
    assert tokens and all(isinstance(t, TokenEvent) for t in tokens)
    assert isinstance(done, DoneEvent)
    assert "".join(t.text for t in tokens if isinstance(t, TokenEvent)).strip() == done.answer
    assert [c.cited for c in done.citations] == [True]
    assert done.trace.tokens is not None


def test_stream_of_small_talk_still_sends_a_token_and_done(tmp_path: Path) -> None:
    pipeline, llm, _ = make_pipeline(tmp_path)

    events = list(pipeline.answer_stream(patient_id="p1", question="thanks!", history=[]))

    assert [type(e) for e in events] == [MetaEvent, CitationsEvent, TokenEvent, DoneEvent]
    assert events[2] == TokenEvent(prompts.THANKS_REPLY)
    assert llm.prompts == []


def test_stream_turns_an_llm_failure_into_a_terminal_error_event(tmp_path: Path) -> None:
    pipeline, _, _ = make_pipeline(tmp_path, ScriptedLLM(fail_with=LLMUnavailableError("down")))
    ingest(pipeline, tmp_path)

    events = list(pipeline.answer_stream(patient_id="p1", question="metformin dose", history=[]))

    assert isinstance(events[-1], ErrorEvent)
    assert events[-1].code == "llm_unavailable"
    assert not any(isinstance(e, DoneEvent) for e in events)


def test_stream_reports_unexpected_failures_without_leaking_details(tmp_path: Path) -> None:
    pipeline = make_pipeline(
        tmp_path, store=FailingVectorStore(RuntimeError("secret internal detail"))
    )[0]

    events = list(pipeline.answer_stream(patient_id="p1", question="metformin dose", history=[]))

    assert events == [ErrorEvent("internal_error", "Something went wrong while answering.")]


def test_stream_surfaces_an_embedding_model_mismatch_as_an_error_event(tmp_path: Path) -> None:
    failing = FailingVectorStore(EmbeddingModelMismatchError("built with another model"))
    pipeline = make_pipeline(tmp_path, store=failing)[0]

    events = list(pipeline.answer_stream(patient_id="p1", question="metformin dose", history=[]))

    assert events == [ErrorEvent("embedding_model_mismatch", "built with another model")]
