"""End-to-end smoke tests with the real embedding and reranker models (``-m slow``).

They prove the wiring that fakes cannot: tokenizer-based chunk sizing, normalised
BGE vectors, Chroma persistence, cross-encoder scores and the calibrated relevance gate.
The language model is still a scripted fake; ``test_live_llm.py`` covers Gemini.
"""

from pathlib import Path

import pytest

from app.rag.config import RagSettings
from app.rag.embeddings import SentenceTransformerEmbedder
from app.rag.pipeline import RagPipeline

from .fakes import ScriptedLLM
from .pdf_factory import Page, build_pdf

pytestmark = pytest.mark.slow

HF_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "huggingface"


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory: pytest.TempPathFactory) -> RagPipeline:
    root = tmp_path_factory.mktemp("real-models")
    settings = RagSettings(chroma_dir=root / "chroma", hf_cache_dir=HF_CACHE)
    rag = RagPipeline(settings, llm=ScriptedLLM("HbA1c was 7.8 % [C1]."))
    lab = build_pdf(
        root / "lab.pdf",
        [
            Page(
                heading="Laboratory Results",
                paragraphs=["Fasting sample collected on 14 Jan 2026."],
                table=[
                    ["Test", "Result", "Unit", "Reference"],
                    ["HbA1c", "7.8", "%", "4.0 - 5.6"],
                    ["Serum creatinine", "1.9", "mg/dL", "0.7 - 1.3"],
                ],
            ),
            Page(
                heading="Impression",
                paragraphs=["Glycaemic control is suboptimal and renal function is reduced."],
            ),
        ],
    )
    rx = build_pdf(
        root / "rx.pdf",
        [Page(heading="Medications", paragraphs=["Metformin 500 mg twice daily after meals."])],
    )
    rag.ingest_pdf(
        patient_id="MG1", report_id="lab", report_name="Lab Jan 2026", category="lab", pdf_path=lab
    )
    rag.ingest_pdf(
        patient_id="MG1", report_id="rx", report_name="Prescription", category="prescription",
        pdf_path=rx,
    )  # fmt: skip
    other = build_pdf(
        root / "other.pdf", [Page(paragraphs=["Warfarin 5 mg for atrial fibrillation."])]
    )
    rag.ingest_pdf(
        patient_id="MG2", report_id="o1", report_name="Cardiology", category="other", pdf_path=other
    )
    return rag


def test_embedder_returns_normalised_384_dimensional_vectors_and_counts_tokens() -> None:
    embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5", HF_CACHE)

    vector = embedder.embed_query("latest HbA1c")

    assert len(vector) == 384
    assert sum(v * v for v in vector) == pytest.approx(1.0, abs=1e-3)
    assert 3 <= embedder.count_tokens("HbA1c was 7.8 % on 12 Mar 2025.") <= 20


def test_hybrid_retrieval_puts_the_answering_chunk_first(pipeline: RagPipeline) -> None:
    best = pipeline.retrieve("MG1", "What is the latest HbA1c?")[0]

    assert best.chunk.report_name == "Lab Jan 2026"
    assert "HbA1c | 7.8 | % | 4.0 - 5.6" in best.chunk.text
    assert best.dense_rank is not None
    assert best.bm25_rank is not None
    assert best.rerank_score is not None and best.rerank_score > 0.1


def test_medication_question_finds_the_prescription(pipeline: RagPipeline) -> None:
    best = pipeline.retrieve("MG1", "What medications is the patient taking?")[0]

    assert best.chunk.report_name == "Prescription"


def test_an_unanswerable_question_is_refused_by_the_calibrated_gate(pipeline: RagPipeline) -> None:
    answer = pipeline.answer(patient_id="MG1", question="What did the brain MRI show?", history=[])

    assert answer.trace.insufficient_evidence
    assert answer.citations == []


def test_a_grounded_question_reaches_the_llm_with_numbered_excerpts(pipeline: RagPipeline) -> None:
    answer = pipeline.answer(patient_id="MG1", question="What is the latest HbA1c?", history=[])

    assert not answer.trace.insufficient_evidence
    assert answer.citations[0].cited
    assert answer.citations[0].score > 0.1
    assert answer.trace.timings_ms["rerank"] >= 0


def test_patients_are_isolated_with_real_vectors(pipeline: RagPipeline) -> None:
    candidates = pipeline.retrieve("MG2", "What is the latest HbA1c and metformin dose?")

    assert all(c.chunk.report_id == "o1" for c in candidates)
