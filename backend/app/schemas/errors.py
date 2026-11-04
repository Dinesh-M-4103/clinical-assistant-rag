"""The error envelope and helpers to document it in OpenAPI."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(description="Stable snake_case identifier clients can branch on.")
    message: str = Field(description="Human-readable explanation.")


class ErrorEnvelope(BaseModel):
    error: ErrorBody


_DESCRIPTIONS = {
    400: "Invalid input or unusable file",
    404: "Resource not found",
    409: "Conflict with existing data",
    413: "Upload exceeds the size limit",
    415: "Unsupported media type",
    422: "Request validation failed",
    502: "Language model unavailable",
}


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """Build the ``responses=`` mapping documenting the envelope for each status."""
    return {
        status: {"model": ErrorEnvelope, "description": _DESCRIPTIONS[status]}
        for status in statuses
    }
