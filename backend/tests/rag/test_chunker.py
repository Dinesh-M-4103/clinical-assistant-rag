from collections.abc import Sequence

from app.rag.ingestion.chunker import RawChunk, chunk_pages
from app.rag.ingestion.pdf_loader import PageText

from .fakes import FakeEmbedder

COUNTER = FakeEmbedder()


def chunk(
    pages: Sequence[Sequence[str]], *, max_tokens: int = 30, overlap_tokens: int = 8
) -> list[RawChunk]:
    page_texts = [PageText(number, tuple(lines)) for number, lines in enumerate(pages, start=1)]
    return chunk_pages(page_texts, COUNTER, max_tokens=max_tokens, overlap_tokens=overlap_tokens)


def sentence(index: int, words: int = 6) -> str:
    return " ".join(f"S{index}x{n}" for n in range(words - 1)) + f" end{index}."


def test_chunks_never_exceed_the_token_budget_and_split_on_sentence_boundaries() -> None:
    paragraph = " ".join(sentence(i) for i in range(12))

    chunks = chunk([[paragraph]])

    assert len(chunks) > 1
    for item in chunks:
        assert COUNTER.count_tokens(item.text) <= 30
        assert item.text.endswith(".")
        assert item.text.startswith("S")


def test_consecutive_chunks_share_trailing_sentences_as_overlap() -> None:
    paragraph = " ".join(sentence(i) for i in range(10))

    first, second = chunk([[paragraph]])[:2]

    last_sentence_of_first = first.text.split(". ")[-1]
    assert last_sentence_of_first.rstrip(".") in second.text
    assert COUNTER.count_tokens(second.text) <= 30


def test_a_sentence_longer_than_the_budget_is_split_by_words() -> None:
    long_sentence = " ".join(f"word{n}" for n in range(75)) + "."

    chunks = chunk([[long_sentence]])

    assert len(chunks) == 3
    assert all(COUNTER.count_tokens(c.text) <= 30 for c in chunks)
    assert " ".join(c.text for c in chunks).split() == long_sentence.split()


def test_abbreviations_do_not_end_a_sentence() -> None:
    chunks = chunk([["Seen by Dr. Rao on Tab. Metformin review. Next visit in May."]])

    assert len(chunks) == 1
    assert "Dr. Rao" in chunks[0].text


def test_table_rows_stay_together_in_one_chunk() -> None:
    table = ["Test | Result | Unit", "HbA1c | 7.8 | %", "Glucose | 130 | mg/dL"]
    prose = " ".join(sentence(i) for i in range(3))

    chunks = chunk([[prose, *table]], max_tokens=30)

    holder = [c for c in chunks if "HbA1c" in c.text]
    assert len(holder) == 1
    assert all(row in holder[0].text for row in table)
    assert "\n".join(table) in holder[0].text


def test_an_oversized_table_is_split_between_rows_never_inside_one() -> None:
    rows = [f"Analyte{n} | {n}.5 | mg/dL | 1 - 9" for n in range(12)]

    chunks = chunk([rows], max_tokens=30, overlap_tokens=0)

    assert len(chunks) > 1
    seen = [line for c in chunks for line in c.text.split("\n")]
    assert seen == rows


def test_a_lone_title_above_a_table_becomes_its_section() -> None:
    lines = ["Lipid Profile", "Test | Result | Unit", "LDL | 112 | mg/dL"]

    chunks = chunk([lines])

    assert chunks[0].section == "Lipid Profile"
    assert chunks[0].text.startswith("Lipid Profile\nTest")


def test_chunks_carry_page_number_and_section() -> None:
    pages = [
        ["Diagnosis: Type 2 diabetes mellitus.", "Medications", "Metformin 500 mg twice daily."],
        ["Continue the same dose until review.", "Plan", "Repeat HbA1c in three months."],
    ]

    chunks = chunk(pages)

    assert [(c.page, c.section) for c in chunks] == [
        (1, "Diagnosis"),
        (1, "Medications"),
        (2, "Medications"),
        (2, "Plan"),
    ]


def test_a_new_section_always_starts_a_new_chunk() -> None:
    chunks = chunk([["Allergies", "No known allergies.", "Plan", "Review in May."]])

    assert [c.section for c in chunks] == ["Allergies", "Plan"]
    assert "Plan" not in chunks[0].text


def test_wrapped_lines_are_joined_but_short_independent_lines_are_not() -> None:
    wrapped_first = (
        "The patient reports a persistent cough that has lasted for about three weeks and"
    )
    chunks = chunk([[wrapped_first, "worsens at night.", "Name: Asha", "Age: 54"]], max_tokens=100)

    assert chunks[0].text == f"{wrapped_first} worsens at night.\nName: Asha\nAge: 54"


def test_pages_without_text_produce_no_chunks() -> None:
    assert chunk([]) == []
