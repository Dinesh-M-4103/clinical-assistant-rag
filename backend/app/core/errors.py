"""Domain exceptions and their translation into the contract's error envelope.

Every failure path (domain, validation, routing, unexpected) answers with
``{"error": {"code": ..., "message": ...}}`` so clients parse one shape only.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base class for errors that are safe to show to API clients."""

    status_code = 500

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BadRequestError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, message: str) -> None:
        super().__init__("not_found", message)


class ConflictError(AppError):
    status_code = 409


class FileTooLargeError(AppError):
    status_code = 413

    def __init__(self, limit_mb: int) -> None:
        super().__init__("file_too_large", f"File exceeds the {limit_mb} MB upload limit.")


class UnsupportedMediaTypeError(AppError):
    status_code = 415

    def __init__(self, message: str) -> None:
        super().__init__("unsupported_media_type", message)


class LlmUnavailableError(AppError):
    status_code = 502

    def __init__(self, message: str = "The language model is currently unavailable.") -> None:
        super().__init__("llm_unavailable", message)


INTERNAL_ERROR_MESSAGE = "An unexpected error occurred."

_HTTP_ERROR_CODES = {
    404: "not_found",
    405: "method_not_allowed",
}


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


def internal_error_response() -> JSONResponse:
    return error_response(500, "internal_error", INTERNAL_ERROR_MESSAGE)


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return error_response(exc.status_code, exc.code, exc.message)


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    problems = [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    ]
    return error_response(422, "validation_error", "; ".join(problems))


async def _handle_http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail))


def register_exception_handlers(app: FastAPI) -> None:
    """Install handlers; unexpected exceptions are handled by the request middleware."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
