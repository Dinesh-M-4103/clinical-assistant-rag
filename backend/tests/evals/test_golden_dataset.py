import json
import re
from pathlib import Path

from app.rag.types import Turn
from evals.dataset import load_golden, load_manifest
from evals.paths import GOLDEN_PATH, MANIFEST_PATH, PDF_ROOT


def test_parses_questions_with_and_without_history(tmp_path: Path) -> None:
    rows = [
        {
            "id": "a1",
            "patient_id": "P1",
            "question": "Latest HbA1c?",
            "type": "temporal",
            "answerable": True,
            "expected_reports": ["lab.pdf"],
            "expected_pages": [1, 2],
            "must_include": ["7\\.2"],
            "must_not_include": [],
        },
        {
            "id": "a2",
            "patient_id": "P1",
            "question": "And before that?",
            "type": "followup",
            "answerable": True,
            "expected_reports": ["lab.pdf"],
            "expected_pages": [1],
            "must_include": [],
            "must_not_include": [],
            "history": [{"role": "user", "content": "Latest HbA1c?"}],
        },
    ]
    path = tmp_path / "golden.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n\n", encoding="utf-8")

    first, second = load_golden(path)

    assert first.expected_sources == {("lab.pdf", 1), ("lab.pdf", 2)}
    assert first.history == ()
    assert second.history == (Turn("user", "Latest HbA1c?"),)


def test_golden_set_agrees_with_the_synthetic_corpus() -> None:
    reports_of = {p.uhid: {r.file for r in p.reports} for p in load_manifest(MANIFEST_PATH)}
    questions = load_golden(GOLDEN_PATH)

    assert len({q.id for q in questions}) == len(questions)
    for question in questions:
        assert question.patient_id in reports_of
        assert set(question.expected_reports) <= reports_of[question.patient_id], question.id
        for pattern in (*question.must_include, *question.must_not_include):
            re.compile(pattern)


def test_every_manifest_report_has_a_pdf() -> None:
    for patient in load_manifest(MANIFEST_PATH):
        for report in patient.reports:
            assert (PDF_ROOT / patient.uhid / report.file).is_file()
