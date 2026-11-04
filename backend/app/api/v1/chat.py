from typing import Any

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from app.api.deps import ChatServiceDep, UhidPath
from app.api.sse import sse_response
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.errors import error_responses

router = APIRouter(prefix="/patients/{uhid}/chat", tags=["chat"])

_SSE_DOCS: dict[int | str, dict[str, Any]] = {
    200: {
        "description": (
            "Server-sent events in order: `meta`, `citations`, many `token`, then `done` "
            "(the authoritative ChatResponse) or a terminal `error`."
        ),
        "content": {"text/event-stream": {"schema": {"type": "string"}}},
    }
}


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question about the patient's records",
    responses=error_responses(404, 422, 502),
)
def chat(uhid: UhidPath, request: ChatRequest, service: ChatServiceDep) -> ChatResponse:
    return service.answer(uhid, request)


@router.post(
    "/stream",
    response_class=EventSourceResponse,
    summary="Ask a question and stream the answer as server-sent events",
    responses={**_SSE_DOCS, **error_responses(404, 422)},
)
def chat_stream(
    uhid: UhidPath, request: ChatRequest, service: ChatServiceDep
) -> EventSourceResponse:
    return sse_response(service.stream(uhid, request))
