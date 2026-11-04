"""Language-model access: a small Protocol plus the Gemini implementation.

Every request passes a client-side rate limiter (free-tier keys allow only a few
requests per minute). Transient failures are retried a bounded number of times,
honouring the server's retry delay; an exhausted daily quota is never retried.
All failures surface as :class:`LLMUnavailableError`, so callers handle one error type.
"""

import random
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

import httpx
from google import genai
from google.genai import errors, types

from app.rag.config import GeminiBackend
from app.rag.errors import LLMUnavailableError
from app.rag.ratelimit import RateLimiter
from app.rag.types import Prompt, TokenUsage

TRANSIENT_STATUS = frozenset({500, 502, 503, 504})
RATE_LIMITED = 429
DEFAULT_MAX_RPM = 8
MAX_SERVER_RETRY_DELAY_SECONDS = 60.0
REQUEST_TIMEOUT_MS = 60_000
MAX_OUTPUT_TOKENS = 2048
_ERROR_DETAIL_LIMIT = 200
_RETRY_IN_MESSAGE = re.compile(r"retry in (\d+(?:\.\d+)?)s", re.IGNORECASE)

_T = TypeVar("_T")


@dataclass(frozen=True)
class LLMResult:
    text: str
    usage: TokenUsage | None


@dataclass(frozen=True)
class LLMDelta:
    """A streamed piece of text; the last delta of a stream carries the token usage."""

    text: str
    usage: TokenUsage | None = None


class LLMClient(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate(self, prompt: Prompt) -> LLMResult: ...

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]: ...


class GeminiClient:
    """Gemini through the ``google-genai`` SDK, created on first use."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        backend: GeminiBackend = "studio",
        limiter: RateLimiter | None = None,
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        client: genai.Client | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._backend = backend
        self._limiter = limiter or RateLimiter(DEFAULT_MAX_RPM)
        self._max_attempts = max_attempts
        self._base_delay = base_delay_seconds
        self._sleep = sleep
        self._client = client

    @property
    def model_name(self) -> str:
        return self._model

    def _sdk(self) -> genai.Client:
        if self._client is None:
            if not self._api_key:
                raise LLMUnavailableError("The language model is not configured (missing API key).")
            self._client = genai.Client(
                api_key=self._api_key,
                vertexai=self._backend == "vertex",
                http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
            )
        return self._client

    def generate(self, prompt: Prompt) -> LLMResult:
        response = self._with_retries(
            lambda: self._sdk().models.generate_content(
                model=self._model, contents=prompt.user, config=self._config(prompt)
            )
        )
        if not response.text:
            raise LLMUnavailableError("The language model returned an empty response.")
        return LLMResult(response.text, _usage(response))

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]:
        """Yield text deltas; retries only before the first delta, so output never repeats."""
        for attempt in range(1, self._max_attempts + 1):
            yielded = False
            usage: TokenUsage | None = None
            try:
                self._limiter.acquire()
                for chunk in self._sdk().models.generate_content_stream(
                    model=self._model, contents=prompt.user, config=self._config(prompt)
                ):
                    usage = _usage(chunk) or usage
                    if chunk.text:
                        yielded = True
                        yield LLMDelta(chunk.text)
            except (errors.APIError, httpx.TransportError) as error:
                delay = None if yielded else self._retry_delay(error, attempt)
                if delay is None:
                    raise _unavailable(error) from error
                self._sleep(delay)
                continue
            if not yielded:
                raise LLMUnavailableError("The language model returned an empty response.")
            yield LLMDelta("", usage)
            return

    def _config(self, prompt: Prompt) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=prompt.system,
            temperature=prompt.temperature,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            thinking_config=_minimal_thinking(self._model),
        )

    def _with_retries(self, call: Callable[[], _T]) -> _T:
        for attempt in range(1, self._max_attempts + 1):
            try:
                self._limiter.acquire()
                return call()
            except (errors.APIError, httpx.TransportError) as error:
                delay = self._retry_delay(error, attempt)
                if delay is None:
                    raise _unavailable(error) from error
                self._sleep(delay)
        raise AssertionError("unreachable: the last attempt either returns or raises")

    def _retry_delay(self, error: Exception, attempt: int) -> float | None:
        """Seconds to wait before the next attempt, or ``None`` when retrying cannot help."""
        if attempt >= self._max_attempts:
            return None
        if isinstance(error, httpx.TransportError):
            return self._backoff(attempt)
        if not isinstance(error, errors.APIError):
            return None
        if error.code == RATE_LIMITED:
            if is_daily_quota(error):
                return None
            server_delay = server_retry_delay(error)
            if server_delay is None:
                return self._backoff(attempt)
            return server_delay if server_delay <= MAX_SERVER_RETRY_DELAY_SECONDS else None
        return self._backoff(attempt) if error.code in TRANSIENT_STATUS else None

    def _backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter, so concurrent clients do not retry in lockstep."""
        return self._base_delay * 2.0 ** (attempt - 1) * random.uniform(0.75, 1.25)


def _minimal_thinking(model: str) -> types.ThinkingConfig | None:
    """Keep hidden reasoning to a minimum on Flash models.

    Answers are grounded extraction, and reasoning only adds seconds before the first
    streamed token. Gemini 2.5 takes a token budget; Gemini 3 rejects it and takes a level.
    """
    if "flash" not in model:
        return None
    if model.startswith("gemini-2.5"):
        return types.ThinkingConfig(thinking_budget=0)
    return types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)


def is_daily_quota(error: errors.APIError) -> bool:
    """Whether a 429 reports the per-day quota, which no amount of waiting will clear soon."""
    return any("perday" in quota_id.lower() for quota_id in _violated_quotas(error))


def server_retry_delay(error: errors.APIError) -> float | None:
    """The delay the server asked for (``RetryInfo`` or "Please retry in 34s"), if any."""
    for detail in _error_details(error):
        delay = detail.get("retryDelay")
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                continue
    match = _RETRY_IN_MESSAGE.search(error.message or "")
    return float(match.group(1)) if match else None


def _error_details(error: errors.APIError) -> list[dict[str, Any]]:
    body = error.details if isinstance(error.details, dict) else {}
    inner = body.get("error", body)
    details = inner.get("details", []) if isinstance(inner, dict) else []
    return [item for item in details if isinstance(item, dict)]


def _violated_quotas(error: errors.APIError) -> list[str]:
    return [
        str(violation.get("quotaId", ""))
        for detail in _error_details(error)
        for violation in detail.get("violations", [])
        if isinstance(violation, dict)
    ]


def _unavailable(error: Exception) -> LLMUnavailableError:
    if isinstance(error, errors.APIError):
        if error.code == RATE_LIMITED:
            if is_daily_quota(error):
                return LLMUnavailableError(
                    "The language model's daily request quota is exhausted; try again tomorrow."
                )
            return LLMUnavailableError(
                "The language model is rate limited right now; please retry in a minute."
            )
        detail = (error.message or "").strip()[:_ERROR_DETAIL_LIMIT]
        return LLMUnavailableError(f"The language model request failed ({error.code}): {detail}")
    return LLMUnavailableError("The language model could not be reached.")


def _usage(response: types.GenerateContentResponse) -> TokenUsage | None:
    metadata = response.usage_metadata
    if metadata is None or metadata.prompt_token_count is None:
        return None
    completion = (metadata.candidates_token_count or 0) + (metadata.thoughts_token_count or 0)
    return TokenUsage(prompt=metadata.prompt_token_count, completion=completion)
