"""Self-checks proving the golden set agrees with the text actually extracted from the PDFs."""

import re
from collections.abc import Sequence

from synthetic_data.golden import BuiltQuestion
from synthetic_data.model import PatientSpec
from synthetic_data.pdf_text import PageTexts


def _patient_text(texts: PageTexts, uhid: str) -> str:
    return " ".join(page for pages in texts[uhid].values() for page in pages)


def _matches(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def check_golden(
    built: Sequence[BuiltQuestion], cohort: Sequence[PatientSpec], texts: PageTexts
) -> list[str]:
    """Return human-readable problems; an empty list means the golden set is consistent."""
    own = {patient.uhid: _patient_text(texts, patient.uhid) for patient in cohort}
    problems: list[str] = []
    ids = [item.record.id for item in built]
    if len(set(ids)) != len(ids):
        problems.append("duplicate golden ids")

    for item in built:
        record = item.record
        others = " ".join(text for uhid, text in own.items() if uhid != record.patient_id)
        prefix = f"{record.id} ({record.patient_id}, {record.type})"

        if record.answerable == (not record.expected_pages):
            problems.append(f"{prefix}: answerable flag disagrees with expected pages")
        if record.answerable:
            problems += [
                f"{prefix}: must_include {pattern!r} not found on expected pages"
                for pattern in record.must_include
                if not _matches(pattern, item.evidence)
            ]
        if record.type == "injection":
            if not any(_matches(p, own[record.patient_id]) for p in record.must_not_include):
                problems.append(f"{prefix}: no injected text found in the patient's records")
            continue
        for pattern in record.must_not_include:
            if _matches(pattern, own[record.patient_id]):
                problems.append(f"{prefix}: must_not_include {pattern!r} occurs in own records")
            if record.type in ("cross_patient", "unanswerable") and not _matches(pattern, others):
                problems.append(f"{prefix}: must_not_include {pattern!r} leaks nothing real")
    return problems
