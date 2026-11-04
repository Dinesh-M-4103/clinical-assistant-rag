"""reportlab renderer: turns a ReportSpec into a hospital-style PDF.

Every page carries a running header and the mandatory synthetic-data footer. Output is
byte-deterministic (``invariant=1`` pins dates and document ids).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from synthetic_data.model import (
    Block,
    Bullets,
    Callout,
    DataTable,
    Grid,
    Heading,
    LabResult,
    LabTable,
    NewPage,
    Para,
    PatientSpec,
    ReportSpec,
    TwoColumns,
    fmt_date,
)

HOSPITAL = "Northbridge General Hospital (fictional)"
ADDRESS = "100 Example Avenue, Northbridge - fictional address, telephone 000 0000"
FOOTER_BANNER = "SYNTHETIC DATA — FOR DEMONSTRATION ONLY"

NAVY = colors.HexColor("#1f3a5f")
TEAL = colors.HexColor("#2a7f8e")
LINE = colors.HexColor("#b8c2cc")
ZEBRA = colors.HexColor("#f2f5f8")
PANEL = colors.HexColor("#dde8f0")
ALERT = colors.HexColor("#b3261e")
LOW = colors.HexColor("#1a5fb4")
GREY = colors.HexColor("#5b6670")

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X
FOOTER_H = 20 * mm
FIRST_TOP = 36 * mm
LATER_TOP = 22 * mm
HEADING_MIN_SPACE = 45


def _style(name: str, **kw: Any) -> ParagraphStyle:
    base: dict[str, Any] = {"fontName": "Helvetica", "fontSize": 9, "leading": 12.5}
    return ParagraphStyle(name, **{**base, **kw})


BODY = _style("body", spaceAfter=4)
BULLET = _style("bullet", leftIndent=12, bulletIndent=2, spaceAfter=1.5)
HEADING = _style(
    "heading",
    fontName="Helvetica-Bold",
    fontSize=10.5,
    textColor=NAVY,
    spaceBefore=9,
    spaceAfter=4,
)
CELL = _style("cell", fontSize=8.5, leading=11)
CELL_BOLD = _style("cell_bold", parent=CELL, fontName="Helvetica-Bold")
CELL_HEAD = _style("cell_head", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
CELL_LABEL = _style("cell_label", parent=CELL, textColor=GREY, fontSize=7.5, leading=9)
TITLE = _style("title", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=NAVY)
SUBTITLE = _style("subtitle", fontSize=9, textColor=GREY, spaceAfter=6)
CENTER_GREY = _style("end", alignment=TA_CENTER, textColor=GREY, fontSize=8, spaceBefore=8)


def _markup(text: str) -> str:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def _scaled(weights: Sequence[float], width: float, count: int) -> list[float]:
    weights = weights or (1.0,) * count
    total = sum(weights)
    return [width * w / total for w in weights]


def _table(
    rows: list[list[Any]], widths: list[float], extra: Sequence[tuple[Any, ...]] = ()
) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                *extra,
            ]
        )
    )
    return table


def _data_table(block: DataTable, width: float) -> list[Flowable]:
    rows: list[list[Any]] = [[Paragraph(_markup(h), CELL_HEAD) for h in block.header]]
    rows += [[Paragraph(_markup(c), CELL) for c in row] for row in block.rows]
    return [_table(rows, _scaled(block.widths, width, len(block.header))), Spacer(1, 6)]


def _flag_cell(result: LabResult) -> Paragraph:
    color = ALERT if result.flag == "H" else LOW
    return Paragraph(f'<font color="{color.hexval()}"><b>{result.flag}</b></font>', CELL)


def _lab_table(block: LabTable, width: float) -> list[Flowable]:
    header = ("Test", "Result", "Unit", "Reference range", "Flag")
    rows: list[list[Any]] = [[Paragraph(h, CELL_HEAD) for h in header]]
    extra: list[tuple[Any, ...]] = []
    for item in block.rows:
        index = len(rows)
        if isinstance(item, str):
            rows.append([Paragraph(_markup(item), CELL_BOLD), "", "", "", ""])
            extra += [
                ("SPAN", (0, index), (-1, index)),
                ("BACKGROUND", (0, index), (-1, index), PANEL),
            ]
            continue
        result_style = CELL_BOLD if item.flag else CELL
        rows.append(
            [
                Paragraph(_markup(item.test), CELL),
                Paragraph(_markup(item.shown), result_style),
                Paragraph(_markup(item.unit), CELL),
                Paragraph(_markup(item.reference), CELL),
                _flag_cell(item) if item.flag else "",
            ]
        )
    widths = _scaled((0.36, 0.14, 0.17, 0.23, 0.10), width, 5)
    return [_table(rows, widths, extra), Spacer(1, 6)]


def _grid(block: Grid, width: float) -> list[Flowable]:
    cols = block.columns
    cells = list(block.cells)
    cells += [("", "")] * (-len(cells) % cols)
    rows = []
    for start in range(0, len(cells), cols):
        rows.append(
            [
                [Paragraph(label.upper(), CELL_LABEL), Paragraph(_markup(value), CELL_BOLD)]
                for label, value in cells[start : start + cols]
            ]
        )
    table = Table(rows, colWidths=[width / cols] * cols)
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("BACKGROUND", (0, 0), (-1, -1), ZEBRA),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [table, Spacer(1, 6)]


def _callout(block: Callout, width: float) -> list[Flowable]:
    table = Table([[Paragraph(_markup(block.text), BODY)]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff4d6")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#e0a100")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0a100")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [table, Spacer(1, 6)]


def _two_columns(block: TwoColumns, width: float) -> list[Flowable]:
    gap = 8 * mm
    half = (width - gap) / 2
    cell = [_blocks(block.left, half), _blocks(block.right, half)]
    table = Table([cell], colWidths=[half + gap / 2, half + gap / 2])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), gap / 2),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ("LINEAFTER", (0, 0), (0, 0), 0.4, LINE),
                ("LEFTPADDING", (1, 0), (1, 0), gap / 2),
            ]
        )
    )
    return [table, Spacer(1, 4)]


def _block(block: Block, width: float) -> list[Flowable]:
    match block:
        case Heading(text):
            return [CondPageBreak(HEADING_MIN_SPACE), Paragraph(_markup(text), HEADING)]
        case Para(text):
            return [Paragraph(_markup(text), BODY)]
        case Bullets(items):
            return [Paragraph(_markup(item), BULLET, bulletText="•") for item in items]
        case Grid():
            return _grid(block, width)
        case DataTable():
            return _data_table(block, width)
        case LabTable():
            return _lab_table(block, width)
        case TwoColumns():
            return _two_columns(block, width)
        case Callout():
            return _callout(block, width)
        case NewPage():
            return [PageBreak()]
    raise TypeError(f"unsupported block: {block!r}")


def _blocks(blocks: Sequence[Block], width: float) -> list[Flowable]:
    return [flowable for block in blocks for flowable in _block(block, width)]


def _banner(patient: PatientSpec, report: ReportSpec, ref: str) -> list[Flowable]:
    cells = (
        ("Patient", patient.name),
        ("UHID", patient.uhid),
        ("Age / sex", f"{patient.age} years / {patient.gender.capitalize()}"),
        ("Report date", fmt_date(report.day)),
        ("Reference no.", ref),
        ("Department", report.department),
    )
    return _grid(Grid(cells, columns=3), CONTENT_W)


class _ReportCanvas(Canvas):  # type: ignore[misc]
    """Canvas that stamps the footer after the page count is known ("Page 2 of 4")."""

    def __init__(self, footer_left: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._footer_left = footer_left
        self._saved_pages: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total: int) -> None:
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(MARGIN_X, 15 * mm, PAGE_W - MARGIN_X, 15 * mm)
        self.setFillColor(ALERT)
        self.setFont("Helvetica-Bold", 8)
        self.drawCentredString(PAGE_W / 2, 11 * mm, FOOTER_BANNER)
        self.setFillColor(GREY)
        self.setFont("Helvetica", 7.5)
        self.drawString(MARGIN_X, 7 * mm, self._footer_left)
        self.drawRightString(PAGE_W - MARGIN_X, 7 * mm, f"Page {self._pageNumber} of {total}")


def _draw_letterhead(canvas: Canvas, _doc: Any) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 26 * mm, PAGE_W, 26 * mm, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H - 28 * mm, PAGE_W, 2 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 17)
    canvas.drawString(MARGIN_X, PAGE_H - 14 * mm, HOSPITAL)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN_X, PAGE_H - 20 * mm, ADDRESS)
    canvas.restoreState()


def _running_header(patient: PatientSpec, report: ReportSpec) -> Any:
    def draw(canvas: Canvas, _doc: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN_X, PAGE_H - 12 * mm, HOSPITAL)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            PAGE_W - MARGIN_X,
            PAGE_H - 12 * mm,
            f"{report.title} | {patient.name} | UHID {patient.uhid}",
        )
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(0.8)
        canvas.line(MARGIN_X, PAGE_H - 15 * mm, PAGE_W - MARGIN_X, PAGE_H - 15 * mm)
        canvas.restoreState()

    return draw


def _frame(top: float, name: str) -> Frame:
    return Frame(
        MARGIN_X,
        FOOTER_H,
        CONTENT_W,
        PAGE_H - FOOTER_H - top,
        id=name,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )


def render_report(patient: PatientSpec, report: ReportSpec, ref: str, out_path: Path) -> None:
    """Write ``report`` as a PDF at ``out_path``."""
    footer_left = f"{HOSPITAL}  |  {patient.name}  |  UHID {patient.uhid}  |  Ref {ref}"
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=A4,
        title=f"{report.title} - {patient.name}",
        author=HOSPITAL,
        subject="Synthetic demonstration record - not real patient data",
        creator="clinical-assistant synthetic data generator",
        invariant=1,
    )
    doc.addPageTemplates(
        [
            PageTemplate(
                "first",
                [_frame(FIRST_TOP, "first")],
                onPage=_draw_letterhead,
                autoNextPageTemplate="later",
            ),
            PageTemplate(
                "later", [_frame(LATER_TOP, "later")], onPage=_running_header(patient, report)
            ),
        ]
    )
    story: list[Flowable] = [
        Paragraph(_markup(report.title), TITLE),
        Paragraph(_markup(report.department), SUBTITLE),
        *_banner(patient, report, ref),
        *_blocks(report.blocks, CONTENT_W),
        KeepTogether(
            [
                Spacer(1, 8),
                Paragraph(
                    _markup(
                        f"Electronically signed: **{report.author}** on {fmt_date(report.day)}"
                    ),
                    BODY,
                ),
                Paragraph("*** End of report ***", CENTER_GREY),
            ]
        ),
    ]
    doc.build(story, canvasmaker=lambda *a, **kw: _ReportCanvas(footer_left, *a, **kw))
