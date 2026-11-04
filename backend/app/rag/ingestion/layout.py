"""Reading order for the text blocks of one PDF page.

PDF text comes out in drawing order, which is not reading order: a two-column
report would interleave its columns line by line. This module restores the order
and re-assembles table rows, whose cells PyMuPDF reports as separate lines.
"""

import itertools
from dataclasses import dataclass

COLUMN_MIN_WIDTH = 0.3
"""A block narrower than this share of the page is a table cell or label, not a column."""
COLUMN_MARGIN = 0.05
"""How far, as a share of the page width, a column may reach across the page middle."""

CELL_SEPARATOR = " | "
CELL_GAP_RATIO = 0.5
"""A horizontal gap wider than this share of the line height separates two table cells."""
SAME_ROW_OVERLAP = 0.5
"""Two lines sit on one visual row when they overlap vertically by at least this share."""


@dataclass(frozen=True)
class TextLine:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


@dataclass(frozen=True)
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    lines: tuple[TextLine, ...]

    @property
    def width(self) -> float:
        return self.x1 - self.x0


def reading_order(blocks: list[TextBlock], page_width: float) -> list[TextBlock]:
    """Order blocks top-to-bottom, reading a two-column band left column first.

    A band is a run of column blocks (wide enough, and sitting entirely in one
    half of the page) between two blocks of any other kind, such as a full-width
    paragraph or a table. Inside a band holding both columns, the whole left
    column is emitted before the right one; everything else keeps top-to-bottom order.
    """
    ordered: list[TextBlock] = []
    band: list[TextBlock] = []

    for block in sorted(blocks, key=lambda b: (b.y0, b.x0)):
        if _column_side(block, page_width) is not None:
            band.append(block)
            continue
        ordered.extend(_order_band(band, page_width))
        band.clear()
        ordered.append(block)
    ordered.extend(_order_band(band, page_width))
    return ordered


def _column_side(block: TextBlock, page_width: float) -> str | None:
    """``"left"`` or ``"right"`` for a column block, ``None`` for anything else."""
    if block.width <= COLUMN_MIN_WIDTH * page_width:
        return None
    middle, margin = page_width / 2, COLUMN_MARGIN * page_width
    if block.x1 <= middle + margin:
        return "left"
    if block.x0 >= middle - margin:
        return "right"
    return None


def _order_band(band: list[TextBlock], page_width: float) -> list[TextBlock]:
    left = [b for b in band if _column_side(b, page_width) == "left"]
    right = [b for b in band if _column_side(b, page_width) == "right"]
    return left + right if left and right else list(band)


def lines_to_rows(lines: list[TextLine]) -> list[str]:
    """Join consecutive lines on the same visual row, marking table cell boundaries.

    ``Hemoglobin`` ``13.2`` ``g/dL`` drawn side by side become
    ``Hemoglobin | 13.2 | g/dL`` so the chunker can keep the row intact.
    """
    rows: list[list[TextLine]] = []
    for line in lines:
        if rows and _same_row(rows[-1][-1], line):
            rows[-1].append(line)
        else:
            rows.append([line])
    return [_join_row(sorted(row, key=lambda item: item.x0)) for row in rows]


def _same_row(previous: TextLine, line: TextLine) -> bool:
    overlap = min(previous.y1, line.y1) - max(previous.y0, line.y0)
    shorter = min(previous.y1 - previous.y0, line.y1 - line.y0)
    return shorter > 0 and overlap / shorter >= SAME_ROW_OVERLAP and line.x0 >= previous.x0


def _join_row(row: list[TextLine]) -> str:
    text = row[0].text
    for previous, line in itertools.pairwise(row):
        gap = line.x0 - previous.x1
        height = max(line.y1 - line.y0, 1.0)
        separator = CELL_SEPARATOR if gap > CELL_GAP_RATIO * height else " "
        text += separator + line.text
    return text
