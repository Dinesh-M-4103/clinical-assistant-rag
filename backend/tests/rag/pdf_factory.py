"""Builds small clinical-looking PDFs with reportlab so tests never need binary fixtures."""

from collections.abc import Sequence
from pathlib import Path

import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

Row = Sequence[str]


class Page:
    """Declarative page: a heading, prose paragraphs and an optional ruled table."""

    def __init__(
        self,
        *,
        heading: str | None = None,
        paragraphs: Sequence[str] = (),
        table: Sequence[Row] = (),
    ) -> None:
        self.heading = heading
        self.paragraphs = paragraphs
        self.table = table


def build_pdf(
    path: Path,
    pages: Sequence[Page],
    *,
    header: str | None = "City Hospital - Department of Pathology",
) -> Path:
    """Write ``pages`` to ``path``; ``header`` and a page number repeat on every page."""
    styles = getSampleStyleSheet()

    def decorate(canvas, doc) -> None:  # type: ignore[no-untyped-def]
        canvas.setFont("Helvetica", 9)
        if header:
            canvas.drawString(40, A4[1] - 30, header)
        canvas.drawString(40, 25, f"Page {doc.page}")

    story: list = []  # type: ignore[type-arg]
    for index, page in enumerate(pages):
        if index:
            story.append(PageBreak())
        if page.heading:
            story.append(Paragraph(page.heading, styles["Heading2"]))
        for paragraph in page.paragraphs:
            story.append(Paragraph(paragraph, styles["BodyText"]))
            story.append(Spacer(1, 6))
        if page.table:
            table = Table(list(page.table))
            table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
            story.append(table)
    SimpleDocTemplate(str(path), pagesize=A4).build(
        story, onFirstPage=decorate, onLaterPages=decorate
    )
    return path


def build_blank_pdf(path: Path) -> Path:
    """A valid PDF whose single page has no text layer, like a scanned report."""
    document = pymupdf.open()  # type: ignore[no-untyped-call]
    document.new_page()
    document.save(path)  # type: ignore[no-untyped-call]
    return path
