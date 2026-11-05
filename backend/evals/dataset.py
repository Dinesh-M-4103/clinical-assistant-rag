"""Golden questions and the synthetic corpus manifest, loaded into typed records."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.types import Turn


@dataclass(frozen=True)
class GoldenQuestion:
    """One evaluation question with its ground truth.

    ``expected_pages`` are 1-based and apply to every file in ``expected_reports``;
    both are empty for questions the records cannot answer.
    """

    id: str
    patient_id: str
    question: str
    type: str
    answerable: bool
    expected_reports: tuple[str, ...]
    expected_pages: tuple[int, ...]
    must_include: tuple[str, ...]
    must_not_include: tuple[str, ...]
    history: tuple[Turn, ...] = ()

    @property
    def expected_sources(self) -> frozenset[tuple[str, int]]:
        """Every (report file, page) pair that counts as supporting evidence."""
        return frozenset(
            (report, page) for report in self.expected_reports for page in self.expected_pages
        )


@dataclass(frozen=True)
class ManifestReport:
    file: str
    name: str
    category: str


@dataclass(frozen=True)
class ManifestPatient:
    uhid: str
    reports: tuple[ManifestReport, ...]


def load_golden(path: Path) -> list[GoldenQuestion]:
    """Read one JSON object per line; blank lines are ignored."""
    with path.open(encoding="utf-8") as lines:
        return [_parse_question(json.loads(line)) for line in lines if line.strip()]


def load_manifest(path: Path) -> list[ManifestPatient]:
    """Read the patients and report files the synthetic generator produced."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ManifestPatient(
            uhid=patient["uhid"],
            reports=tuple(
                ManifestReport(report["file"], report["name"], report["category"])
                for report in patient["reports"]
            ),
        )
        for patient in data["patients"]
    ]


def _parse_question(row: dict[str, Any]) -> GoldenQuestion:
    history = row.get("history") or []
    return GoldenQuestion(
        id=str(row["id"]),
        patient_id=str(row["patient_id"]),
        question=str(row["question"]),
        type=str(row["type"]),
        answerable=bool(row["answerable"]),
        expected_reports=_strings(row["expected_reports"]),
        expected_pages=tuple(int(page) for page in row["expected_pages"]),
        must_include=_strings(row["must_include"]),
        must_not_include=_strings(row["must_not_include"]),
        history=tuple(Turn(turn["role"], turn["content"]) for turn in history),
    )


def _strings(values: list[Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in values)
