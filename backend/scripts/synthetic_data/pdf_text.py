"""Read rendered PDFs back as text, the way the RAG ingestion will see them."""

from pathlib import Path

import pymupdf

PageTexts = dict[str, dict[str, list[str]]]
"""uhid -> report file -> whitespace-normalised text of each page (page 1 first)."""


def extract_pages(pdf_path: Path) -> list[str]:
    with pymupdf.open(pdf_path) as document:  # type: ignore[no-untyped-call]
        return [" ".join(page.get_text().split()) for page in document]
