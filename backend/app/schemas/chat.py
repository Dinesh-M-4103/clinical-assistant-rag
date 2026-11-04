"""Chat request/response models, including the payloads of each SSE event."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Intent = Literal["question", "greeting", "off_topic"]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: Annotated[str, Field(max_length=8000)]


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: Annotated[str, Field(min_length=1, max_length=2000)]
    history: Annotated[
        list[ChatTurn],
        Field(
            max_length=100, description="Previous turns, oldest first; only the last 10 are used."
        ),
    ] = []


class Citation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="C1..Cn, scoped to this response.")
    report_id: str
    report_name: str
    category: str
    page: int
    section: str | None
    text: str
    score: float
    cited: bool = Field(description="True when the answer references this chunk.")


class TraceCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dense_rank: int | None
    bm25_rank: int | None
    fused_score: float
    rerank_score: float | None


class TraceModels(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    llm: str
    embedding: str
    reranker: str


class TokenUsage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prompt: int
    completion: int


class Trace(BaseModel):
    """How an answer was produced; powers the UI's explanation drawer."""

    model_config = ConfigDict(from_attributes=True)

    intent: Intent
    rewritten_query: str | None
    insufficient_evidence: bool
    candidates: list[TraceCandidate]
    timings_ms: dict[str, int]
    models: TraceModels
    tokens: TokenUsage | None


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    citations: list[Citation]
    trace: Trace


class StreamMeta(BaseModel):
    """Payload of the SSE ``meta`` event."""

    model_config = ConfigDict(from_attributes=True)

    intent: Intent
    rewritten_query: str | None


class StreamToken(BaseModel):
    """Payload of the SSE ``token`` event."""

    model_config = ConfigDict(from_attributes=True)

    text: str
