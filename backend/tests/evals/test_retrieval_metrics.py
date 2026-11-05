import pytest

from evals.metrics import first_hit_rank, hit_at, mean, recall_at, score_question

EXPECTED = frozenset({("lab.pdf", 1), ("rx.pdf", 1)})
RANKED = [("note.pdf", 1), ("lab.pdf", 2), ("lab.pdf", 1), ("rx.pdf", 1)]


def test_first_hit_rank_is_one_based() -> None:
    assert first_hit_rank(RANKED, EXPECTED) == 3


def test_first_hit_rank_is_none_without_a_hit() -> None:
    assert first_hit_rank([("note.pdf", 1)], EXPECTED) is None


def test_page_must_match_not_just_report() -> None:
    assert not hit_at([("lab.pdf", 2)], EXPECTED, k=5)


def test_hit_at_respects_the_cutoff() -> None:
    assert not hit_at(RANKED, EXPECTED, k=2)
    assert hit_at(RANKED, EXPECTED, k=3)


def test_recall_counts_each_expected_report_once() -> None:
    assert recall_at(RANKED, EXPECTED, k=3) == 0.5
    assert recall_at(RANKED, EXPECTED, k=4) == 1.0


def test_recall_ignores_extra_hits_in_the_same_report() -> None:
    ranked = [("lab.pdf", 1), ("lab.pdf", 1)]
    assert recall_at(ranked, frozenset({("lab.pdf", 1)}), k=2) == 1.0


def test_recall_without_expectations_is_zero() -> None:
    assert recall_at(RANKED, frozenset(), k=5) == 0.0


def test_score_question_bundles_all_cutoffs() -> None:
    scores = score_question(RANKED, EXPECTED)

    assert scores.hits_at == {1: False, 3: True, 5: True}
    assert scores.reciprocal_rank == pytest.approx(1 / 3)
    assert scores.recall_at == {1: 0.0, 3: 0.5, 5: 1.0}


def test_a_miss_scores_zero_everywhere() -> None:
    scores = score_question([("note.pdf", 1)], EXPECTED)

    assert scores.reciprocal_rank == 0.0
    assert not any(scores.hits_at.values())


def test_mean_of_nothing_is_zero() -> None:
    assert mean([]) == 0.0
    assert mean([1.0, 0.0]) == 0.5
