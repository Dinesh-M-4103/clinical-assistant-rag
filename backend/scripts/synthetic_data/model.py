"""Declarative model of the synthetic cohort.

Reports are described as data (blocks), never as drawing code, so the same structures feed the
PDF renderer, the manifest and the golden evaluation set and cannot drift apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal, TypeAlias

Category = Literal["lab", "imaging", "discharge", "prescription", "consultation"]
Gender = Literal["male", "female"]
QuestionType = Literal[
    "factoid",
    "numeric",
    "temporal",
    "table",
    "negation",
    "multi_chunk",
    "abbreviation",
    "followup",
    "cross_patient",
    "unanswerable",
    "injection",
]

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


# ---------------------------------------------------------------- document blocks


@dataclass(frozen=True)
class Heading:
    text: str


@dataclass(frozen=True)
class Para:
    """Paragraph; ``**bold**`` spans are supported."""

    text: str


@dataclass(frozen=True)
class Bullets:
    items: tuple[str, ...]


@dataclass(frozen=True)
class Grid:
    """Label/value pairs laid out in ``columns`` side-by-side columns (vitals, specimen data)."""

    cells: tuple[tuple[str, str], ...]
    columns: int = 3


@dataclass(frozen=True)
class DataTable:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    widths: tuple[float, ...] = ()


@dataclass(frozen=True)
class LabResult:
    """One analyte; the reference range text and the H/L flag are derived from the bounds."""

    test: str
    value: float | str
    unit: str = ""
    low: float | None = None
    high: float | None = None
    decimals: int = 1
    ref_text: str = ""

    @property
    def shown(self) -> str:
        if isinstance(self.value, str):
            return self.value
        return f"{self.value:.{self.decimals}f}"

    @property
    def reference(self) -> str:
        if self.ref_text:
            return self.ref_text
        low = None if self.low is None else f"{self.low:.{self.decimals}f}"
        high = None if self.high is None else f"{self.high:.{self.decimals}f}"
        if low and high:
            return f"{low} - {high}"
        if high:
            return f"< {high}"
        if low:
            return f">= {low}"
        return ""

    @property
    def flag(self) -> Literal["H", "L", ""]:
        if isinstance(self.value, str):
            return ""
        if self.low is not None and self.value < self.low:
            return "L"
        if self.high is not None:
            above = self.value > self.high if self.low is not None else self.value >= self.high
            return "H" if above else ""
        return ""

    @property
    def needle(self) -> str:
        """Text as it appears in the extracted PDF row (cells joined by single spaces)."""
        return " ".join(part for part in (self.test, self.shown, self.unit) if part)


@dataclass(frozen=True)
class LabTable:
    """Lab panel; plain strings are panel sub-headings, results are rows."""

    rows: tuple[str | LabResult, ...]


@dataclass(frozen=True)
class TwoColumns:
    left: tuple[Block, ...]
    right: tuple[Block, ...]


@dataclass(frozen=True)
class Callout:
    text: str


@dataclass(frozen=True)
class NewPage:
    pass


Block: TypeAlias = (
    Heading | Para | Bullets | Grid | DataTable | LabTable | TwoColumns | Callout | NewPage
)


# ---------------------------------------------------------------- cohort


@dataclass(frozen=True)
class ReportSpec:
    file: str
    name: str
    category: Category
    notes: str
    day: date
    title: str
    department: str
    author: str
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class Fact:
    """A ground-truth statement located in one report by the text ``needles`` it renders as.

    Pages are never typed by hand: the generator searches the rendered PDF for each needle.
    ``spans_page_break`` asserts that the needles land on different pages.
    """

    report: str
    needles: tuple[str, ...]
    spans_page_break: bool = False


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class QuestionSpec:
    type: QuestionType
    question: str
    facts: tuple[str, ...] = ()
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()
    answerable: bool = True
    history: tuple[Turn, ...] = ()


@dataclass(frozen=True)
class PatientSpec:
    uhid: str
    name: str
    age: int
    gender: Gender
    summary: str
    reports: tuple[ReportSpec, ...]
    facts: dict[str, Fact]
    questions: tuple[QuestionSpec, ...]


# ---------------------------------------------------------------- formatting helpers


def fmt_date(day: date) -> str:
    """Date as printed on every report, e.g. ``06 Apr 2026``."""
    return f"{day.day:02d} {MONTHS[day.month - 1][:3]} {day.year}"


def gestation(lmp: date, on: date) -> str:
    """Gestational age in completed weeks and days, e.g. ``28w2d``."""
    weeks, days = divmod((on - lmp).days, 7)
    return f"{weeks}w{days}d"


def due_date(lmp: date) -> date:
    """Naegele's rule: 280 days from the last menstrual period."""
    return lmp + timedelta(days=280)


# ---------------------------------------------------------------- answer-pattern helpers


def number_re(*values: str) -> str:
    """Regex matching any of the numbers as a standalone token (``1500`` also matches ``1,500``)."""
    alternatives = "|".join(re.sub(r"^(\d+)(\d{3})$", r"\1,?\2", re.escape(v)) for v in values)
    return rf"(?<![\d.,])(?:{alternatives})(?![\d]|\.\d)"


def dose_re(amount: str, unit: str = "mg") -> str:
    """Regex for a dose such as ``5 mg`` that does not match inside ``2.5 mg``."""
    return rf"{number_re(amount)}\s*{unit}\b"


def date_re(day: date) -> str:
    """Regex accepting the common spellings of a date (ISO, 6 April 2026, April 6, 06/04/2026)."""
    month = MONTHS[day.month - 1]
    d = rf"0?{day.day}(?:st|nd|rd|th)?"
    return (
        rf"(?:{day.isoformat()}"
        rf"|{d}[\s-]+(?:of\s+)?{month[:3]}[a-z]*\.?,?[\s-]+{day.year}"
        rf"|{month[:3]}[a-z]*\.?\s+{d},?\s+{day.year}"
        rf"|0?{day.day}/0?{day.month}/{day.year})"
    )


REFUSAL_RE = (
    r"(?:not (?:found|mentioned|documented|available|stated|recorded|provided|specified|reported"
    r"|listed|contain|include)"
    r"|no (?:\w+ ){0,2}(?:information|record|mention|data|documentation|result|evidence|value"
    r"|figure|level)"
    r"|cannot|can't|unable|don't|do not|does not|doesn't|insufficient)"
)
"""Loose pattern for 'the records do not say', shared by every unanswerable question."""

NEGATIVE_START_RE = r"^\s*yes\b"
"""Used as ``must_not_include`` on negation questions: the answer must not open with 'Yes'."""

NO_RE = r"\b(?:no|not|none|without|denies|negative|absent|never)\b"
