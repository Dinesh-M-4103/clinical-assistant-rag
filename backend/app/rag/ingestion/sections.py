"""Detects clinical section headings such as ``Diagnosis:`` or ``LABORATORY RESULTS``.

Chunks carry the section they sit in, so a citation can say "Medications, page 2"
and the chunker keeps different sections in different chunks.
"""

import re
from dataclasses import dataclass

_SECTIONS: dict[str, tuple[str, ...]] = {
    "Chief Complaint": (r"chief complaints?", r"presenting complaints?", r"reason for \w+"),
    "History of Present Illness": (r"history of present(?:ing)? illness", r"hpi"),
    "Past Medical History": (r"past (?:medical )?history", r"medical history", r"pmh"),
    "Allergies": (r"(?:drug |known )?allerg(?:y|ies)",),
    "Medications": (
        r"(?:current |discharge |home )?medications?(?: on discharge)?",
        r"drug history",
        r"prescription",
    ),
    "Vitals": (r"vitals?", r"vital signs"),
    "Examination": (r"(?:physical |clinical |general |on )?examination",),
    "Diagnosis": (r"(?:final |provisional |discharge |primary |working )?diagnos[ie]s",),
    "Laboratory Results": (
        r"lab(?:oratory)? (?:results?|investigations?|findings)",
        r"investigations?",
        r"test results?",
    ),
    "Findings": (r"findings?", r"observations?"),
    "Impression": (r"impression", r"conclusion", r"opinion"),
    "Interpretation": (r"interpretation", r"comments?"),
    "Procedure": (r"procedures?(?: performed)?", r"operative notes?"),
    "Hospital Course": (r"hospital course", r"clinical course", r"course in hospital"),
    "Plan": (r"(?:treatment |management )?plan", r"assessment (?:and|&) plan"),
    "Advice": (r"advice", r"recommendations?", r"instructions", r"discharge advice"),
    "Follow-up": (r"follow[- ]?up", r"review"),
    "Clinical History": (r"clinical (?:history|indication|information)", r"indication", r"history"),
    "Technique": (r"technique", r"protocol"),
    "Comparison": (r"comparison",),
}

_LEADING_MARKUP = re.compile(r"^\s*(?:\d+[.)]\s*)?[*#\s]*")
_HEADING_PATTERNS = [
    (
        name,
        re.compile(rf"(?:{'|'.join(aliases)})\s*(?P<colon>:)?[\s*]*(?P<rest>.*)", re.IGNORECASE),
    )
    for name, aliases in _SECTIONS.items()
]


@dataclass(frozen=True)
class Heading:
    """A detected section opener; ``body`` is any text after ``Heading:`` on the same line."""

    section: str
    body: str


def detect_heading(line: str) -> Heading | None:
    """Return the heading ``line`` opens, or ``None`` for ordinary text.

    A heading is either a line holding only the heading words, or ``Heading: text``.
    Requiring the colon for the inline form keeps ordinary sentences such as
    "Plan to continue metformin" from being mistaken for a heading.
    """
    text = _LEADING_MARKUP.sub("", line)
    for name, pattern in _HEADING_PATTERNS:
        match = pattern.fullmatch(text)
        if match and (match.group("colon") or not match.group("rest")):
            return Heading(section=name, body=match.group("rest").strip())
    return None
