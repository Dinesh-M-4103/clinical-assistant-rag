"""Sentence-, section- and table-aware chunking.

Retrieval quality depends on chunks that read as complete thoughts, so the
chunker packs whole sentences up to a token budget, never crosses a page or a
section boundary, keeps table rows together, and repeats a little trailing text
(overlap) so an answer that straddles two chunks is still found.

Pipeline per page:  lines -> blocks (paragraph / table) -> units -> chunks.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.rag.ingestion.layout import CELL_SEPARATOR
from app.rag.ingestion.pdf_loader import PageText
from app.rag.ingestion.sections import detect_heading
from app.rag.ingestion.sentences import split_sentences

MAX_TABLE_TITLE_WORDS = 6
WRAPPED_LINE_MIN_CHARS = 60
"""A line this long that does not end a sentence is assumed to wrap onto the next line."""
_LIST_ITEM = re.compile(r"^(?:[-*\u2022\u2013\u00b7]|\d{1,2}[.)])\s+")
_SENTENCE_END = (".", "!", "?", ":")


class TokenCounter(Protocol):
    def count_tokens(self, text: str) -> int: ...


@dataclass(frozen=True)
class RawChunk:
    """Chunk text with its position; the pipeline adds report identity."""

    page: int
    section: str | None
    text: str


@dataclass(frozen=True)
class _Unit:
    """Smallest piece the packer places: a sentence or a table row."""

    text: str
    tokens: int
    starts_line: bool


@dataclass(frozen=True)
class _Block:
    units: tuple[_Unit, ...]
    section: str | None
    keep_together: bool

    @property
    def tokens(self) -> int:
        return sum(unit.tokens for unit in self.units)


def chunk_pages(
    pages: Sequence[PageText],
    counter: TokenCounter,
    *,
    max_tokens: int,
    overlap_tokens: int,
) -> list[RawChunk]:
    """Split pages into chunks of at most ``max_tokens`` tokens.

    A sentence is only cut when it alone exceeds ``max_tokens``. The section in
    force at the end of a page carries over to the next page.
    """
    chunks: list[RawChunk] = []
    section: str | None = None
    for page in pages:
        blocks, section = _page_blocks(page.lines, section, counter)
        packer = _Packer(page.number, max_tokens, overlap_tokens, counter)
        for block in blocks:
            packer.add_block(block)
        chunks.extend(packer.finish())
    return chunks


def _page_blocks(
    lines: Sequence[str], section: str | None, counter: TokenCounter
) -> tuple[list[_Block], str | None]:
    blocks: list[_Block] = []
    paragraph: list[str] = []
    table: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            sentences = split_sentences(" ".join(paragraph))
            units = tuple(
                _Unit(text, counter.count_tokens(text), starts_line=index == 0)
                for index, text in enumerate(sentences)
            )
            blocks.append(_Block(units, section, keep_together=False))
            paragraph.clear()

    def flush_table() -> None:
        if table:
            units = tuple(_Unit(row, counter.count_tokens(row), True) for row in table)
            blocks.append(_Block(units, section, keep_together=True))
            table.clear()

    previous = ""
    for line in lines:
        heading = detect_heading(line)
        if heading:
            flush_paragraph()
            flush_table()
            section = heading.section
        if line.count(CELL_SEPARATOR) >= 2:
            if not table and (title := _table_title(paragraph)):
                section = title
            flush_paragraph()
            table.append(line)
        else:
            flush_table()
            if heading or not _continues(previous, line):
                flush_paragraph()
            paragraph.append(line)
            if heading and not heading.body:
                flush_paragraph()
        previous = line
    flush_paragraph()
    flush_table()
    return blocks, section


def _table_title(paragraph: Sequence[str]) -> str | None:
    """A lone short line right above a table names it ("Lipid Profile"), so it opens a section."""
    if len(paragraph) != 1:
        return None
    title = paragraph[0]
    is_caption = len(title.split()) <= MAX_TABLE_TITLE_WORDS and not title.endswith(_SENTENCE_END)
    return title if is_caption else None


def _continues(previous: str, line: str) -> bool:
    """Whether ``line`` continues the sentence ``previous`` ended mid-way (a wrapped line)."""
    if not previous or _LIST_ITEM.match(line) or previous.endswith(_SENTENCE_END):
        return False
    return line[0].islower() or len(previous) >= WRAPPED_LINE_MIN_CHARS


class _Packer:
    """Fills chunks for one page, flushing whenever the next unit would overflow."""

    def __init__(self, page: int, max_tokens: int, overlap_tokens: int, counter: TokenCounter):
        self._page = page
        self._max = max_tokens
        self._overlap = overlap_tokens
        self._counter = counter
        self._section: str | None = None
        self._units: list[_Unit] = []
        self._chunks: list[RawChunk] = []

    def add_block(self, block: _Block) -> None:
        if block.section != self._section:
            self._flush(carry_overlap=False)
            self._section = block.section
        if block.keep_together and block.tokens <= self._max:
            if self._tokens() + block.tokens > self._max:
                self._flush(carry_overlap=False)
            self._units.extend(block.units)
            return
        for unit in block.units:
            for piece in self._fit(unit):
                self._add_unit(piece)

    def finish(self) -> list[RawChunk]:
        self._flush(carry_overlap=False)
        return self._chunks

    def _add_unit(self, unit: _Unit) -> None:
        if self._units and self._tokens() + unit.tokens > self._max:
            self._flush(carry_overlap=True)
            if self._tokens() + unit.tokens > self._max:
                self._units = []
        self._units.append(unit)

    def _fit(self, unit: _Unit) -> list[_Unit]:
        """Return ``unit`` itself, or word-wise pieces when it alone exceeds the budget."""
        if unit.tokens <= self._max:
            return [unit]
        pieces: list[_Unit] = []
        words: list[str] = []
        used = 0
        for word in unit.text.split():
            cost = self._counter.count_tokens(word)
            if words and used + cost > self._max:
                pieces.append(
                    _Unit(" ".join(words), used, starts_line=not pieces and unit.starts_line)
                )
                words, used = [], 0
            words.append(word)
            used += cost
        pieces.append(_Unit(" ".join(words), used, starts_line=not pieces and unit.starts_line))
        return pieces

    def _flush(self, *, carry_overlap: bool) -> None:
        if not self._units:
            return
        self._chunks.append(RawChunk(self._page, self._section, _join(self._units)))
        self._units = self._trailing_overlap() if carry_overlap else []

    def _trailing_overlap(self) -> list[_Unit]:
        kept: list[_Unit] = []
        used = 0
        for unit in reversed(self._units[1:]):
            if used + unit.tokens > self._overlap:
                break
            kept.insert(0, unit)
            used += unit.tokens
        return kept

    def _tokens(self) -> int:
        return sum(unit.tokens for unit in self._units)


def _join(units: Sequence[_Unit]) -> str:
    text = units[0].text
    for unit in units[1:]:
        text += ("\n" if unit.starts_line else " ") + unit.text
    return text
