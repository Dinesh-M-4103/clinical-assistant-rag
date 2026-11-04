"""Turns the model's inline ``[C#]`` markers into verified citations.

Models occasionally cite sources that were never provided or write markers in
odd shapes (``[C1, C2]``, ``[c1]``). Everything the user sees is therefore
re-derived from the retrieved set: unknown markers are dropped and the rest are
normalised to ``[C1][C2]``.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.rag.types import Candidate, CandidateTraceDTO, CitationDTO

_MARKER_GROUP = re.compile(
    r"(?P<before>[ \t]?)\[\s*(?P<ids>C\d+(?:\s*[,;]\s*C\d+)*)\s*\](?P<after>[ \t]?)",
    re.IGNORECASE,
)
_ID = re.compile(r"C\d+", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedAnswer:
    """The answer with only valid, normalised markers, and the ids it cites in order."""

    text: str
    cited_ids: tuple[str, ...]


def citation_id(position: int) -> str:
    """Id of the candidate at 0-based ``position``: ``C1``, ``C2``, ..."""
    return f"C{position + 1}"


def parse_citations(answer: str, valid_ids: Sequence[str]) -> ParsedAnswer:
    """Keep markers that point at retrieved chunks, discard and tidy the rest."""
    valid = set(valid_ids)
    cited: list[str] = []

    def replace(match: re.Match[str]) -> str:
        ids = list(dict.fromkeys(i.upper() for i in _ID.findall(match.group("ids"))))
        kept = [i for i in ids if i in valid]
        cited.extend(i for i in kept if i not in cited)
        before, after = match.group("before"), match.group("after")
        if kept:
            return f"{before}{''.join(f'[{i}]' for i in kept)}{after}"
        return before if before and after else ""

    return ParsedAnswer(_MARKER_GROUP.sub(replace, answer), tuple(cited))


def to_citations(
    candidates: Sequence[Candidate], cited_ids: Sequence[str] = ()
) -> list[CitationDTO]:
    """One citation per retrieved candidate; ``cited`` marks the ones the answer used."""
    return [
        CitationDTO(
            id=citation_id(position),
            report_id=candidate.chunk.report_id,
            report_name=candidate.chunk.report_name,
            category=candidate.chunk.category,
            page=candidate.chunk.page,
            section=candidate.chunk.section,
            text=candidate.chunk.text,
            score=candidate.score,
            cited=citation_id(position) in cited_ids,
        )
        for position, candidate in enumerate(candidates)
    ]


def to_trace_candidates(candidates: Sequence[Candidate]) -> list[CandidateTraceDTO]:
    """Per-stage ranking evidence, keyed by the same ids as :func:`to_citations`."""
    return [
        CandidateTraceDTO(
            id=citation_id(position),
            dense_rank=candidate.dense_rank,
            bm25_rank=candidate.bm25_rank,
            fused_score=candidate.fused_score,
            rerank_score=candidate.rerank_score,
        )
        for position, candidate in enumerate(candidates)
    ]
