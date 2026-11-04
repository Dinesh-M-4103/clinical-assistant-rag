"""Bridges the synchronous RAG event generator to an SSE HTTP response."""

from collections.abc import AsyncIterator
from contextlib import suppress

from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.concurrency import iterate_in_threadpool

from app.services.chat import SseMessages

_STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def sse_response(messages: SseMessages) -> EventSourceResponse:
    return EventSourceResponse(_relay(messages), headers=_STREAM_HEADERS)


async def _relay(messages: SseMessages) -> AsyncIterator[ServerSentEvent]:
    """Pull blocking pipeline output on worker threads so the event loop stays free.

    When the client disconnects this coroutine is cancelled; the ``finally``
    closes the generator so the pipeline can release the LLM stream.
    """
    try:
        async for message in iterate_in_threadpool(messages):
            yield ServerSentEvent(data=message.data, event=message.event)
    finally:
        # A worker may still be inside next(); close() then raises and the
        # generator is reclaimed as soon as that call returns.
        with suppress(ValueError):
            messages.close()
