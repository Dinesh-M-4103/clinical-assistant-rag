"""Reads a PDF into clean, page-wise text with PyMuPDF."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf

from app.rag.errors import InvalidPdfError, NoExtractableTextError
from app.rag.ingestion.cleaning import normalise_text, strip_page_furniture
from app.rag.ingestion.layout import TextBlock, TextLine, lines_to_rows, reading_order

_TEXT_BLOCK = 0


@dataclass(frozen=True)
class PageText:
    """Cleaned text of one page; ``number`` is 1-based like the PDF viewer's."""

    number: int
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ParsedPdf:
    page_count: int
    pages: tuple[PageText, ...]


def load_pdf(path: Path) -> ParsedPdf:
    """Extract text page by page, in reading order, without headers and footers.

    Raises:
        InvalidPdfError: the file is corrupt or password protected.
        NoExtractableTextError: no page has a text layer (e.g. a scan).
    """
    try:
        # Opened from memory: PyMuPDF keeps a file handle alive after a failed open, which on
        # Windows would stop the caller from deleting the rejected upload.
        with pymupdf.open(stream=path.read_bytes(), filetype="pdf") as document:  # type: ignore[no-untyped-call]
            if document.needs_pass:
                raise InvalidPdfError("The PDF is password protected.")
            raw_pages = [_page_lines(page) for page in document]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as error:
        raise InvalidPdfError("The file is not a readable PDF.") from error

    cleaned = strip_page_furniture(raw_pages)
    pages = tuple(
        PageText(number=index, lines=tuple(lines))
        for index, lines in enumerate(cleaned, start=1)
        if lines
    )
    if not pages:
        raise NoExtractableTextError("The PDF has no extractable text.")
    return ParsedPdf(page_count=len(raw_pages), pages=pages)


def _page_lines(page: pymupdf.Page) -> list[str]:
    blocks = _text_blocks(page)
    ordered = reading_order(blocks, page.rect.width)
    lines = [line for block in ordered for line in block.lines]
    return normalise_text("\n".join(lines_to_rows(lines)))


def _text_blocks(page: pymupdf.Page) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for raw in page.get_text("dict")["blocks"]:  # type: ignore[no-untyped-call]
        if raw["type"] != _TEXT_BLOCK:
            continue
        lines = tuple(_text_line(line) for line in raw["lines"])
        non_empty = tuple(line for line in lines if line.text.strip())
        if non_empty:
            x0, y0, x1, y1 = raw["bbox"]
            blocks.append(TextBlock(x0, y0, x1, y1, non_empty))
    return blocks


def _text_line(line: dict[str, Any]) -> TextLine:
    x0, y0, x1, y1 = line["bbox"]
    return TextLine(x0, y0, x1, y1, "".join(span["text"] for span in line["spans"]))
