"""Request-id propagation, access logging and the last-resort 500 handler.

Written as a pure ASGI middleware (not ``BaseHTTPMiddleware``) so streaming
responses such as SSE are passed through untouched.
"""

import re
import time
import uuid

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response, internal_error_response

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

logger = structlog.get_logger("app.access")


class RequestContextMiddleware:
    """Binds a request id to the log context, logs each request and hides crashes.

    Sitting inside the CORS middleware, it lets a 500 envelope still carry CORS
    headers, so browsers show the API error instead of an opaque network failure.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = Headers(scope=scope).get(REQUEST_ID_HEADER, "")
        request_id = supplied if _SAFE_REQUEST_ID.match(supplied) else uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        status = 500
        response_started = False
        started_at = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception("unhandled_error", path=scope["path"])
            if response_started:
                raise
            await internal_error_response()(scope, receive, send_with_request_id)
        finally:
            logger.info(
                "request",
                method=scope["method"],
                path=scope["path"],
                status=status,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 1),
            )


class BodySizeLimitMiddleware:
    """Rejects requests whose declared body exceeds the cap, before any parsing.

    Starlette spools multipart uploads to disk before handlers run, so without
    this an oversized upload would be fully received first. Chunked requests
    carry no length and are still capped while streaming to storage.
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            declared = Headers(scope=scope).get("content-length", "")
            if declared.isdigit() and int(declared) > self.max_body_bytes:
                limit_mb = self.max_body_bytes // (1024 * 1024)
                response = error_response(
                    413, "file_too_large", f"Request exceeds the {limit_mb} MB limit."
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
