"""Plain data shapes shared across the RAG package.

The ``*DTO`` classes and the events mirror the JSON in ``docs/api-contract.md``
one-to-one, so the API layer only has to map them onto its response models.
"""

from dataclasses import dataclass
from typing import Literal

Role = Literal["user", "assistant"]
Intent = Literal["question", "greeting", "off_topic"]


@dataclass(frozen=True)
class Turn:
    """One message of the conversation so far."""

    role: Role
    content: str


@dataclass(frozen=True)
class Chunk:
    """A retrievable passage of one report page."""

    chunk_id: str
    report_id: str
    report_name: str
    category: str
    page: int
    section: str | None
    text: str

    @property
    def contextual_text(self) -> str:
        """Text prefixed with report name and section, as the embedder and reranker read it.

        A bare table row ("Metformin | 500 mg") says nothing about which report or
        section it belongs to; the header lets "the discharge diagnosis" or "medications"
        match it. Stored and displayed text stays verbatim.
        """
        header = " - ".join(part for part in (self.report_name, self.section) if part)
        return f"{header}\n{self.text}"


@dataclass(frozen=True)
class Candidate:
    """A chunk plus the evidence of how each retrieval stage ranked it."""

    chunk: Chunk
    dense_rank: int | None
    bm25_rank: int | None
    fused_score: float
    rerank_score: float | None

    @property
    def score(self) -> float:
        """Best available relevance signal, shown to the user as the citation score."""
        return self.fused_score if self.rerank_score is None else self.rerank_score


@dataclass(frozen=True)
class Prompt:
    """Text sent to the language model."""

    system: str
    user: str
    temperature: float = 0.1


@dataclass(frozen=True)
class IngestResult:
    page_count: int
    chunk_count: int


@dataclass(frozen=True)
class CitationDTO:
    id: str
    report_id: str
    report_name: str
    category: str
    page: int
    section: str | None
    text: str
    score: float
    cited: bool


@dataclass(frozen=True)
class CandidateTraceDTO:
    id: str
    dense_rank: int | None
    bm25_rank: int | None
    fused_score: float
    rerank_score: float | None


@dataclass(frozen=True)
class TokenUsage:
    prompt: int
    completion: int


@dataclass(frozen=True)
class TraceDTO:
    intent: Intent
    rewritten_query: str | None
    insufficient_evidence: bool
    candidates: list[CandidateTraceDTO]
    timings_ms: dict[str, int]
    models: dict[str, str]
    tokens: TokenUsage | None


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    citations: list[CitationDTO]
    trace: TraceDTO


@dataclass(frozen=True)
class MetaEvent:
    intent: Intent
    rewritten_query: str | None


@dataclass(frozen=True)
class CitationsEvent:
    citations: list[CitationDTO]


@dataclass(frozen=True)
class TokenEvent:
    text: str


@dataclass(frozen=True)
class DoneEvent(RagAnswer):
    """Authoritative final answer; replaces everything streamed before it."""


@dataclass(frozen=True)
class ErrorEvent:
    code: str
    message: str


RagEvent = MetaEvent | CitationsEvent | TokenEvent | DoneEvent | ErrorEvent
