"""Derive the golden evaluation set from the cohort's own fact and question declarations."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from synthetic_data.facts import locate_fact
from synthetic_data.model import PatientSpec, QuestionSpec
from synthetic_data.pdf_text import PageTexts


@dataclass(frozen=True)
class GoldenRecord:
    id: str
    patient_id: str
    question: str
    type: str
    answerable: bool
    expected_reports: list[str]
    expected_pages: list[int]
    must_include: list[str]
    must_not_include: list[str]
    history: list[dict[str, str]]

    def to_json(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        if not self.history:
            del data["history"]
        return data


@dataclass(frozen=True)
class BuiltQuestion:
    """A golden record plus the PDF text of the pages it points at (used to self-check it)."""

    record: GoldenRecord
    evidence: str


def _build_one(
    number: int, patient: PatientSpec, spec: QuestionSpec, texts: PageTexts
) -> BuiltQuestion:
    pages_by_report: dict[str, set[int]] = {}
    for key in spec.facts:
        fact = patient.facts[key]
        report_pages = texts[patient.uhid][fact.report]
        pages_by_report.setdefault(fact.report, set()).update(locate_fact(fact, report_pages))

    report_order = [report.file for report in patient.reports]
    reports = sorted(pages_by_report, key=report_order.index)
    evidence = " ".join(
        texts[patient.uhid][file][page - 1]
        for file in reports
        for page in sorted(pages_by_report[file])
    )
    record = GoldenRecord(
        id=f"g{number:02d}",
        patient_id=patient.uhid,
        question=spec.question,
        type=spec.type,
        answerable=spec.answerable,
        expected_reports=reports,
        expected_pages=sorted(set().union(*pages_by_report.values())),
        must_include=list(spec.must_include),
        must_not_include=list(spec.must_not_include),
        history=[{"role": turn.role, "content": turn.content} for turn in spec.history],
    )
    return BuiltQuestion(record, evidence)


def build_golden(cohort: Sequence[PatientSpec], texts: PageTexts) -> list[BuiltQuestion]:
    specs = [(patient, spec) for patient in cohort for spec in patient.questions]
    return [
        _build_one(number, patient, spec, texts)
        for number, (patient, spec) in enumerate(specs, start=1)
    ]
