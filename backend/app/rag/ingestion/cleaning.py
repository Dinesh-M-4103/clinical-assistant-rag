"""Text clean-up that makes PDF output safe to chunk and search.

Hyphenated line breaks, stray unicode and repeating page furniture (running
headers, footers, page numbers) would otherwise pollute chunks and rankings.
"""

import math
import re
import unicodedata

from app.rag.ingestion.sections import detect_heading

EDGE_LINES = 2
"""How many lines at the top and bottom of a page count as header or footer."""

_REPLACEMENTS = str.maketrans(
    {
        "\N{NO-BREAK SPACE}": " ",
        "\N{THIN SPACE}": " ",
        "\N{ZERO WIDTH SPACE}": "",
        "\N{SOFT HYPHEN}": "",
        "\N{LATIN SMALL LIGATURE FI}": "fi",
        "\N{LATIN SMALL LIGATURE FL}": "fl",
        "\N{RIGHT SINGLE QUOTATION MARK}": "'",
    }
)
_HYPHEN_LINE_BREAK = re.compile(r"(?<=[a-z])-\n(?=[a-z])")
_SPACES = re.compile(r"[ \t]+")
_PAGE_NUMBER = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$|^-\s*\d+\s*-$", re.IGNORECASE)


def normalise_text(raw: str) -> list[str]:
    """Return the cleaned, non-empty lines of one page.

    Joins words broken by a hyphen at a line end (``hemo-`` / ``globin``) and
    leaves genuine hyphens (``follow-up``, ``12.0-15.5``) alone.
    """
    text = unicodedata.normalize("NFC", raw).translate(_REPLACEMENTS)
    text = _HYPHEN_LINE_BREAK.sub("", text)
    lines = (_SPACES.sub(" ", line).strip() for line in text.splitlines())
    return [line for line in lines if line]


def strip_page_furniture(pages: list[list[str]]) -> list[list[str]]:
    """Remove page numbers and running headers/footers, keeping the first copy.

    A header that repeats on at least half of the pages is dropped from every
    page after the one where it first appears: it often carries the report date
    or laboratory name, so one copy is worth keeping for retrieval. Section headings
    ("Impression" at the top of every page) are body text and are never removed.
    """
    needed = max(2, math.ceil(len(pages) / 2))
    edge_counts: dict[str, int] = {}
    for lines in pages:
        for key in {_furniture_key(line) for line in _edge_lines(lines)}:
            edge_counts[key] = edge_counts.get(key, 0) + 1

    seen: set[str] = set()
    cleaned: list[list[str]] = []
    for lines in pages:
        edge_positions = _edge_positions(lines)
        kept: list[str] = []
        for position, line in enumerate(lines):
            if position in edge_positions and not detect_heading(line):
                if _PAGE_NUMBER.match(line):
                    continue
                key = _furniture_key(line)
                if edge_counts[key] >= needed:
                    if key in seen:
                        continue
                    seen.add(key)
            kept.append(line)
        cleaned.append(kept)
    return cleaned


def _edge_positions(lines: list[str]) -> set[int]:
    """Indices of the header and footer zones; a short page keeps its middle line(s) as body."""
    edge = min(EDGE_LINES, (len(lines) - 1) // 2)
    return set(range(edge)) | set(range(len(lines) - edge, len(lines)))


def _edge_lines(lines: list[str]) -> list[str]:
    return [lines[position] for position in sorted(_edge_positions(lines))]


def _furniture_key(line: str) -> str:
    """Normalise digits so "Page 1" and "Page 2" count as the same furniture."""
    return re.sub(r"\d+", "#", line.lower())
