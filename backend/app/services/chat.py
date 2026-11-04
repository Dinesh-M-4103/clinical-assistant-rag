"""Chat use-cases: maps RAG results and events onto API schemas and SSE messages."""

from collections.abc import Generator
from dataclasses import dataclass

import structlog
from pydantic import BaseModel, TypeAdapter

from app.core.errors import INTERNAL_ERROR_MESSAGE, LlmUnavailableError
from app.rag import errors as rag_errors
from app.rag.types import (
    CitationsEvent,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
    RagEvent,
    TokenEvent,
    Turn,
)
from app.schemas.chat import ChatRequest, ChatResponse, Citation, StreamMeta, StreamToken
from app.schemas.errors import ErrorBody
from app.services.patients import PatientService
from app.services.ports import RagPort

logger = structlog.get_logger(__name__)

MAX_HISTORY_TURNS = 10
_CITATIONS = TypeAdapter(list[Citation])


@dataclass(frozen=True)
class SseMessage:
    """One server-sent event, already serialised; transport-agnostic."""

    event: str
    data: str


SseMessages = Generator[SseMessage, None, None]


class ChatService:
    def __init__(self, pipeline: RagPort, patients: PatientService) -> None:
        self._pipeline = pipeline
        self._patients = patients

    def answer(self, uhid: str, request: ChatRequest) -> ChatResponse:
        self._patients.get(uhid)
        try:
            result = self._pipeline.answer(
                patient_id=uhid, question=request.question, history=_to_turns(request)
            )
        except rag_errors.LLMUnavailableError as exc:
            raise LlmUnavailableError() from exc
        return ChatResponse.model_validate(result)

    def stream(self, uhid: str, request: ChatRequest) -> SseMessages:
        """Check the patient eagerly (so a 404 is a real HTTP status), then stream."""
        self._patients.get(uhid)
        return self._stream_events(uhid, request)

    def _stream_events(self, uhid: str, request: ChatRequest) -> SseMessages:
        try:
            for event in self._pipeline.answer_stream(
                patient_id=uhid, question=request.question, history=_to_turns(request)
            ):
                yield _to_message(event)
                if isinstance(event, DoneEvent | ErrorEvent):
                    return
        except rag_errors.RagError as exc:
            logger.warning("rag_stream_failed", code=exc.code, error=str(exc))
            yield _error_message(exc.code, str(exc))
        except Exception:
            logger.exception("chat_stream_failed")
            yield _error_message("internal_error", INTERNAL_ERROR_MESSAGE)


def _to_turns(request: ChatRequest) -> list[Turn]:
    recent = request.history[-MAX_HISTORY_TURNS:]
    return [Turn(role=turn.role, content=turn.content) for turn in recent]


def _to_message(event: RagEvent) -> SseMessage:
    match event:
        case MetaEvent():
            return _message("meta", StreamMeta.model_validate(event))
        case CitationsEvent():
            citations = _CITATIONS.validate_python(event.citations, from_attributes=True)
            return SseMessage("citations", _CITATIONS.dump_json(citations).decode())
        case TokenEvent():
            return _message("token", StreamToken.model_validate(event))
        case DoneEvent():
            return _message("done", ChatResponse.model_validate(event))
        case ErrorEvent():
            return _error_message(event.code, event.message)


def _message(name: str, payload: BaseModel) -> SseMessage:
    return SseMessage(name, payload.model_dump_json())


def _error_message(code: str, message: str) -> SseMessage:
    return _message("error", ErrorBody(code=code, message=message))
