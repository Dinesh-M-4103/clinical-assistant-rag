import asyncio
from collections.abc import AsyncGenerator

from app.api.sse import sse_response
from app.services.chat import SseMessage, SseMessages


class _Probe:
    def __init__(self) -> None:
        self.closed = False

    def endless(self) -> SseMessages:
        try:
            while True:
                yield SseMessage("token", '{"text": "x"}')
        finally:
            self.closed = True


def test_client_disconnect_closes_the_pipeline_generator() -> None:
    probe = _Probe()

    async def consume_one_then_disconnect() -> None:
        stream = sse_response(probe.endless()).body_iterator
        assert isinstance(stream, AsyncGenerator)
        first = await anext(stream)
        assert (first.event, first.data) == ("token", '{"text": "x"}')
        await stream.aclose()

    asyncio.run(consume_one_then_disconnect())

    assert probe.closed
