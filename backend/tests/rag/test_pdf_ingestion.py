from pathlib import Path

import pytest

from app.rag.errors import InvalidPdfError, NoExtractableTextError
from app.rag.ingestion.cleaning import normalise_text, strip_page_furniture
from app.rag.ingestion.layout import TextBlock, TextLine, lines_to_rows, reading_order
from app.rag.ingestion.pdf_loader import load_pdf

from .pdf_factory import Page, build_blank_pdf, build_pdf

PAGE_WIDTH = 600.0


def block(x0: float, y0: float, x1: float, y1: float, text: str) -> TextBlock:
    return TextBlock(x0, y0, x1, y1, (TextLine(x0, y0, x1, y1, text),))


def texts(blocks: list[TextBlock]) -> list[str]:
    return [b.lines[0].text for b in blocks]


# --- cleaning ------------------------------------------------------------------


def test_normalise_joins_hyphenated_line_breaks_but_keeps_real_hyphens() -> None:
    lines = normalise_text("Hemo-\nglobin was low.\nFollow-up in 12.0-\n15.5 weeks\n")

    assert lines == ["Hemoglobin was low.", "Follow-up in 12.0-", "15.5 weeks"]


def test_normalise_collapses_whitespace_and_unicode_noise() -> None:
    raw = (
        "  HbA1c\N{NO-BREAK SPACE}\N{NO-BREAK SPACE} 7.8 %\t\n\n\n  next \N{ZERO WIDTH SPACE}line "
    )

    assert normalise_text(raw) == ["HbA1c 7.8 %", "next line"]


def test_furniture_removes_repeated_headers_after_the_first_page_and_page_numbers() -> None:
    pages = [
        ["City Lab", "Findings page one.", "Page 1"],
        ["City Lab", "Findings page two.", "Page 2"],
        ["City Lab", "Findings page three.", "Page 3"],
    ]

    cleaned = strip_page_furniture(pages)

    assert cleaned == [
        ["City Lab", "Findings page one."],
        ["Findings page two."],
        ["Findings page three."],
    ]


def test_furniture_ignores_digits_when_matching_and_never_touches_body_lines() -> None:
    pages = [
        ["Ref LAB-1 | Page 1 of 2", "HbA1c 7.8", "Plan", "Ref LAB-1 | Page 1 of 2"],
        ["Ref LAB-1 | Page 2 of 2", "HbA1c 7.4", "Plan", "Ref LAB-1 | Page 2 of 2"],
    ]

    cleaned = strip_page_furniture(pages)

    assert cleaned[1] == ["HbA1c 7.4", "Plan"]
    assert cleaned[0][0] == "Ref LAB-1 | Page 1 of 2"


def test_furniture_keeps_everything_on_a_single_page_document() -> None:
    page = ["Header", "Body", "Footer"]

    assert strip_page_furniture([page]) == [page]


# --- layout --------------------------------------------------------------------


def test_two_column_page_reads_the_left_column_before_the_right() -> None:
    blocks = [
        block(40, 100, 290, 120, "left 1"),
        block(310, 100, 560, 120, "right 1"),
        block(40, 130, 290, 150, "left 2"),
        block(310, 130, 560, 150, "right 2"),
    ]

    assert texts(reading_order(blocks, PAGE_WIDTH)) == ["left 1", "left 2", "right 1", "right 2"]


def test_a_full_width_block_separates_column_bands() -> None:
    blocks = [
        block(40, 50, 560, 70, "title"),
        block(40, 100, 290, 120, "left 1"),
        block(310, 100, 560, 120, "right 1"),
        block(40, 200, 560, 220, "full width"),
        block(40, 250, 290, 270, "left 2"),
        block(310, 250, 560, 270, "right 2"),
    ]

    assert texts(reading_order(blocks, PAGE_WIDTH)) == [
        "title",
        "left 1",
        "right 1",
        "full width",
        "left 2",
        "right 2",
    ]


def test_narrow_table_cell_blocks_stay_in_row_order() -> None:
    cells = [
        block(40, 100, 120, 115, "Test"),
        block(300, 100, 380, 115, "Result"),
        block(40, 120, 120, 135, "HbA1c"),
        block(300, 120, 380, 135, "7.8"),
    ]

    assert texts(reading_order(cells, PAGE_WIDTH)) == ["Test", "Result", "HbA1c", "7.8"]


def test_lines_on_one_visual_row_become_cells_separated_by_pipes() -> None:
    lines = [
        TextLine(40, 100, 100, 112, "HbA1c"),
        TextLine(200, 100, 220, 112, "7.8"),
        TextLine(222, 100, 232, 112, "%"),
        TextLine(40, 120, 300, 132, "Next paragraph line"),
    ]

    assert lines_to_rows(lines) == ["HbA1c | 7.8 %", "Next paragraph line"]


# --- loading -------------------------------------------------------------------


def test_load_pdf_extracts_pages_tables_and_drops_running_headers(tmp_path: Path) -> None:
    pdf = build_pdf(
        tmp_path / "lab.pdf",
        [
            Page(
                heading="Laboratory Results",
                paragraphs=["HbA1c was 7.8% on 12 Mar 2025."],
                table=[["Test", "Result", "Unit"], ["HbA1c", "7.8", "%"]],
            ),
            Page(heading="Medications", paragraphs=["Metformin 500 mg twice daily."]),
        ],
    )

    parsed = load_pdf(pdf)

    assert parsed.page_count == 2
    first, second = parsed.pages
    assert first.number == 1
    assert "City Hospital - Department of Pathology" in first.lines
    assert "HbA1c | 7.8 | %" in first.lines
    assert "City Hospital - Department of Pathology" not in second.lines
    assert not any(line.startswith("Page ") for page in parsed.pages for line in page.lines)


def test_load_pdf_rejects_a_pdf_without_a_text_layer(tmp_path: Path) -> None:
    blank = build_blank_pdf(tmp_path / "scan.pdf")

    with pytest.raises(NoExtractableTextError):
        load_pdf(blank)


def test_load_pdf_rejects_a_file_that_is_not_a_pdf(tmp_path: Path) -> None:
    fake = tmp_path / "notes.pdf"
    fake.write_text("this is plain text, not a PDF")

    with pytest.raises(InvalidPdfError):
        load_pdf(fake)


def test_rejected_pdf_leaves_no_file_handle_open(tmp_path: Path) -> None:
    """On Windows an open handle would stop the upload service from deleting the rejected file."""
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 truncated")

    with pytest.raises(InvalidPdfError):
        load_pdf(broken)

    broken.unlink()
    assert not broken.exists()
