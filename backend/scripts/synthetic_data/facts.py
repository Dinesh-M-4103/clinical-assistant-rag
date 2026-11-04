"""Locate ground-truth facts in rendered PDFs, so page numbers are measured, never typed."""

from collections.abc import Sequence

from synthetic_data.model import Fact


class FactNotFoundError(ValueError):
    """A needle declared in the cohort data does not appear in the rendered report."""


def locate_fact(fact: Fact, page_texts: Sequence[str]) -> tuple[int, ...]:
    """1-based pages on which any needle of ``fact`` appears (case-sensitive, exact text)."""
    needle_pages = [
        {number for number, text in enumerate(page_texts, start=1) if needle in text}
        for needle in fact.needles
    ]
    for needle, pages in zip(fact.needles, needle_pages, strict=True):
        if not pages:
            raise FactNotFoundError(f"{fact.report}: needle not found in PDF text: {needle!r}")
    if fact.spans_page_break and any(
        a & b for index, a in enumerate(needle_pages) for b in needle_pages[index + 1 :]
    ):
        raise FactNotFoundError(
            f"{fact.report}: needles expected on different pages: {fact.needles}"
        )
    return tuple(sorted(set().union(*needle_pages)))
