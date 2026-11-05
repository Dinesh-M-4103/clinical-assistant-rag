from app.rag.types import CitationDTO, RagAnswer, TraceDTO
from evals.answer_checks import check_answer
from evals.dataset import GoldenQuestion

DOSE = r"\b500\s*mg\b"
OLD_DOSE = r"\b1000\s*mg\b"


def make_question(
    *,
    question_type: str = "temporal",
    answerable: bool = True,
    must_include: tuple[str, ...] = (DOSE,),
    must_not_include: tuple[str, ...] = (OLD_DOSE,),
) -> GoldenQuestion:
    return GoldenQuestion(
        id="q1",
        patient_id="P1",
        question="What dose of metformin?",
        type=question_type,
        answerable=answerable,
        expected_reports=("rx.pdf",) if answerable else (),
        expected_pages=(1,) if answerable else (),
        must_include=must_include,
        must_not_include=must_not_include,
    )


def make_citation(report_id: str, page: int, *, cited: bool = True) -> CitationDTO:
    return CitationDTO("C1", report_id, "Report", "lab", page, None, "text", 0.9, cited)


def make_answer(
    text: str, *citations: CitationDTO, insufficient_evidence: bool = False
) -> RagAnswer:
    trace = TraceDTO("question", None, insufficient_evidence, [], {}, {}, None)
    return RagAnswer(text, list(citations), trace)


def test_correct_cited_answer_passes() -> None:
    answer = make_answer("Metformin 500 MG twice daily [C1].", make_citation("P1/rx.pdf", 1))

    verdict = check_answer(make_question(), answer)

    assert verdict.passed
    assert verdict.cited == (("rx.pdf", 1),)
    assert verdict.cited_supported == 1
    assert not verdict.leaked


def test_missing_required_text_fails() -> None:
    verdict = check_answer(make_question(), make_answer("Metformin was prescribed."))

    assert not verdict.passed
    assert verdict.missing == (DOSE,)


def test_forbidden_text_fails() -> None:
    verdict = check_answer(make_question(), make_answer("500 mg, previously 1000 mg."))

    assert not verdict.passed
    assert verdict.forbidden == (OLD_DOSE,)


def test_citation_on_the_wrong_page_is_unsupported() -> None:
    answer = make_answer("500 mg [C1].", make_citation("P1/rx.pdf", 2))

    verdict = check_answer(make_question(), answer)

    assert verdict.cited == (("rx.pdf", 2),)
    assert verdict.cited_supported == 0


def test_retrieved_but_uncited_chunks_are_not_counted_as_cited() -> None:
    answer = make_answer("500 mg.", make_citation("P1/rx.pdf", 1, cited=False))

    assert check_answer(make_question(), answer).cited == ()


def test_chunk_from_another_patient_is_a_leak() -> None:
    answer = make_answer("500 mg [C1].", make_citation("P2/rx.pdf", 1, cited=False))

    assert check_answer(make_question(), answer).leaked


def test_stating_another_patients_value_leaks_only_in_cross_patient_questions() -> None:
    answer = make_answer("500 mg, or 1000 mg.")

    assert not check_answer(make_question(), answer).leaked
    assert check_answer(make_question(question_type="cross_patient"), answer).leaked


def test_unanswerable_question_passes_when_the_answer_refuses() -> None:
    question = make_question(answerable=False, must_include=("not found",), must_not_include=())
    answer = make_answer("This is not found in the records.", insufficient_evidence=True)

    verdict = check_answer(question, answer)

    assert verdict.passed
    assert verdict.refused_by_gate
