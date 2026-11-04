import pytest

from app.rag.ingestion.sections import Heading, detect_heading
from app.rag.ingestion.sentences import split_sentences


@pytest.mark.parametrize(
    ("line", "section"),
    [
        ("Diagnosis", "Diagnosis"),
        ("DIAGNOSIS:", "Diagnosis"),
        ("Final Diagnosis", "Diagnosis"),
        ("Current Medications", "Medications"),
        ("Medications on Discharge", "Medications"),
        ("2. Allergies", "Allergies"),
        ("**Impression**", "Impression"),
        ("Laboratory Results", "Laboratory Results"),
        ("History of Presenting Illness", "History of Present Illness"),
        ("Reason for Visit", "Chief Complaint"),
        ("Follow-up", "Follow-up"),
        ("Plan", "Plan"),
    ],
)
def test_headings_are_detected_and_mapped_to_a_canonical_section(line: str, section: str) -> None:
    heading = detect_heading(line)

    assert heading == Heading(section=section, body="")


def test_inline_heading_keeps_the_text_after_the_colon() -> None:
    assert detect_heading("Allergies: No known drug allergies") == Heading(
        "Allergies", "No known drug allergies"
    )


@pytest.mark.parametrize(
    "line",
    [
        "Plan to continue metformin",
        "The diagnosis was confirmed by biopsy.",
        "Metformin 500 mg twice daily",
        "Patient reports allergies to dust",
    ],
)
def test_ordinary_sentences_are_not_headings(line: str) -> None:
    assert detect_heading(line) is None


def test_sentences_split_at_real_boundaries() -> None:
    text = "HbA1c was 7.8 % on 12 Mar. Glucose was 130 mg/dL. Plan: review in 3 months!"

    assert split_sentences(text) == [
        "HbA1c was 7.8 % on 12 Mar.",
        "Glucose was 130 mg/dL.",
        "Plan: review in 3 months!",
    ]


def test_abbreviations_initials_and_decimals_do_not_split_sentences() -> None:
    text = "Seen by Dr. A. Kapoor for Tab. Metformin b.i.d. Creatinine was 1.9 mg/dL. Stable."

    assert split_sentences(text) == [
        "Seen by Dr. A. Kapoor for Tab. Metformin b.i.d. Creatinine was 1.9 mg/dL.",
        "Stable.",
    ]


def test_empty_text_has_no_sentences() -> None:
    assert split_sentences("   ") == []
