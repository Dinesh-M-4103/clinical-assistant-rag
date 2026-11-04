import math

import pytest

from app.rag.retrieval.bm25 import Bm25Retriever, tokenize
from app.rag.retrieval.fusion import reciprocal_rank_fusion
from app.rag.retrieval.relevance import has_sufficient_evidence
from app.rag.retrieval.reranker import _sigmoid
from app.rag.types import Candidate

from .fakes import FakeEmbedder, InMemoryVectorStore, make_chunk

# --- reciprocal rank fusion ------------------------------------------------------


def test_rrf_sums_reciprocal_ranks_across_lists() -> None:
    fused = dict(reciprocal_rank_fusion([["a", "b", "c"], ["b", "a"]], k=60))

    assert fused["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["c"] == pytest.approx(1 / 63)


def test_rrf_orders_by_score_and_rewards_agreement_between_lists() -> None:
    fused = reciprocal_rank_fusion([["x", "shared"], ["y", "shared"]])

    assert fused[0][0] == "shared"
    assert len(fused) == 3


def test_rrf_default_k_is_sixty_and_ties_keep_first_seen_order() -> None:
    fused = reciprocal_rank_fusion([["first"], ["second"]])

    assert fused == [("first", 1 / 61), ("second", 1 / 61)]


def test_rrf_of_nothing_is_empty() -> None:
    assert reciprocal_rank_fusion([[], []]) == []


# --- BM25 tokenizer ------------------------------------------------------------------


def test_tokenizer_keeps_lab_and_drug_tokens_whole() -> None:
    tokens = tokenize("HbA1c 7.8% on Metformin 500mg; vitamin B12 low, eGFR 38 mL/min")

    assert {"hba1c", "7.8", "500mg", "b12", "egfr", "38", "ml", "min"} <= set(tokens)


def test_tokenizer_splits_ranges_and_drops_stop_words() -> None:
    assert tokenize("Reference 12.0-15.5 of the range") == ["reference", "12.0", "15.5", "range"]


# --- BM25 retriever --------------------------------------------------------------------


def bm25_store() -> InMemoryVectorStore:
    store = InMemoryVectorStore()
    chunks = [
        make_chunk("r1:0", "HbA1c 7.8 % fasting glucose 130 mg/dL", section="Laboratory Results"),
        make_chunk("r1:1", "Metformin 500mg twice daily after meals"),
        make_chunk("r1:2", "Vitamin B12 level was low at 150 pg/mL"),
    ]
    store.add_chunks("p1", chunks, FakeEmbedder().embed_documents([c.text for c in chunks]))
    return store


def test_bm25_finds_exact_clinical_tokens() -> None:
    retriever = Bm25Retriever(bm25_store())

    assert retriever.search("p1", "what is the hba1c", 5)[0].chunk_id == "r1:0"
    assert retriever.search("p1", "metformin 500mg", 5)[0].chunk_id == "r1:1"
    assert [c.chunk_id for c in retriever.search("p1", "B12", 5)] == ["r1:2"]


def test_bm25_returns_nothing_when_no_query_token_matches() -> None:
    assert Bm25Retriever(bm25_store()).search("p1", "tuberculosis", 5) == []


def test_bm25_for_a_patient_without_chunks_is_empty() -> None:
    assert Bm25Retriever(bm25_store()).search("unknown", "hba1c", 5) == []


def test_bm25_index_is_cached_until_invalidated() -> None:
    store = bm25_store()
    retriever = Bm25Retriever(store)
    assert retriever.search("p1", "warfarin", 5) == []

    new_chunk = make_chunk("r2:0", "Warfarin 5mg at night", report_id="r2")
    store.add_chunks("p1", [new_chunk], FakeEmbedder().embed_documents([new_chunk.text]))
    assert retriever.search("p1", "warfarin", 5) == []

    retriever.invalidate("p1")
    assert [c.chunk_id for c in retriever.search("p1", "warfarin", 5)] == ["r2:0"]


# --- reranker maths and relevance gate ---------------------------------------------------


def test_sigmoid_is_stable_for_extreme_logits() -> None:
    assert _sigmoid(0.0) == 0.5
    assert _sigmoid(-1000.0) == 0.0
    assert _sigmoid(1000.0) == 1.0
    assert math.isclose(_sigmoid(2.0), 1 / (1 + math.exp(-2.0)))


def candidate(rerank_score: float | None) -> Candidate:
    return Candidate(make_chunk(), None, None, 0.03, rerank_score)


def test_gate_refuses_when_the_best_rerank_score_is_below_the_threshold() -> None:
    assert not has_sufficient_evidence([candidate(0.0005), candidate(0.0002)], 0.001)


def test_gate_passes_when_any_candidate_reaches_the_threshold() -> None:
    assert has_sufficient_evidence([candidate(0.0002), candidate(0.4)], 0.001)


def test_gate_refuses_when_nothing_was_retrieved() -> None:
    assert not has_sufficient_evidence([], 0.001)


def test_gate_cannot_judge_candidates_that_were_never_reranked() -> None:
    assert has_sufficient_evidence([candidate(None)], 0.5)
