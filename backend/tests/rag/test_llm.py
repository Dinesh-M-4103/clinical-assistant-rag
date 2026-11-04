from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from google import genai
from google.genai import errors

from app.rag.errors import LLMUnavailableError
from app.rag.llm import GeminiClient
from app.rag.ratelimit import RateLimiter
from app.rag.types import Prompt, TokenUsage

PROMPT = Prompt(system="Be brief.", user="What is the dose?")


def response(text: str | None, prompt_tokens: int = 12, completion_tokens: int = 3) -> Any:
    usage = SimpleNamespace(
        prompt_token_count=prompt_tokens,
        candidates_token_count=completion_tokens,
        thoughts_token_count=None,
    )
    return SimpleNamespace(text=text, usage_metadata=usage)


def api_error(code: int, *details: dict[str, Any], message: str | None = None) -> errors.APIError:
    error_class = errors.ServerError if code >= 500 else errors.ClientError
    body = {"message": message or f"status {code}", "status": "ERR", "details": list(details)}
    return error_class(code, {"error": body})


def retry_info(delay: str) -> dict[str, Any]:
    return {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}


def quota_failure(quota_id: str) -> dict[str, Any]:
    return {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [{"quotaId": quota_id}],
    }


class FakeModels:
    """Plays back one scripted outcome per call: a response, an iterator, or an exception."""

    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    def _next(self) -> Any:
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def generate_content(self, **_: Any) -> Any:
        return self._next()

    def generate_content_stream(self, **_: Any) -> Iterator[Any]:
        return cast(Iterator[Any], self._next())


def make_client(
    outcomes: list[Any], sleeps: list[float] | None = None, **options: Any
) -> tuple[GeminiClient, FakeModels]:
    models = FakeModels(outcomes)
    record: Callable[[float], None] = (sleeps if sleeps is not None else []).append
    sdk = cast(genai.Client, SimpleNamespace(models=models))
    client = GeminiClient(
        model="gemini-test-flash", api_key="k", sleep=record, client=sdk, **options
    )
    return client, models


def test_a_missing_api_key_is_reported_as_llm_unavailable() -> None:
    client = GeminiClient(model="m", api_key=None)

    with pytest.raises(LLMUnavailableError, match="not configured"):
        client.generate(PROMPT)


# --- generate ---------------------------------------------------------------------------


def test_generate_returns_text_and_token_usage() -> None:
    client, _ = make_client([response("500 mg twice daily", 40, 7)])

    result = client.generate(PROMPT)

    assert result.text == "500 mg twice daily"
    assert result.usage == TokenUsage(prompt=40, completion=7)


def test_transient_errors_are_retried_with_exponential_backoff() -> None:
    sleeps: list[float] = []
    client, models = make_client(
        [api_error(429), api_error(503), response("ok")], sleeps, base_delay_seconds=1.0
    )

    assert client.generate(PROMPT).text == "ok"
    assert models.calls == 3
    assert 0.75 <= sleeps[0] <= 1.25
    assert 1.5 <= sleeps[1] <= 2.5


def test_network_failures_are_retried_too() -> None:
    client, models = make_client([httpx.ConnectError("boom"), response("ok")])

    assert client.generate(PROMPT).text == "ok"
    assert models.calls == 2


def test_client_errors_fail_immediately_without_retrying() -> None:
    client, models = make_client([api_error(400), response("never")])

    with pytest.raises(LLMUnavailableError, match="400"):
        client.generate(PROMPT)
    assert models.calls == 1


def test_retries_stop_after_max_attempts() -> None:
    client, models = make_client([api_error(503)] * 5, max_attempts=3)

    with pytest.raises(LLMUnavailableError, match="503"):
        client.generate(PROMPT)
    assert models.calls == 3


def test_an_empty_response_is_an_error() -> None:
    client, _ = make_client([response(None)])

    with pytest.raises(LLMUnavailableError, match="empty"):
        client.generate(PROMPT)


# --- stream -----------------------------------------------------------------------------


def test_stream_yields_text_deltas_then_usage() -> None:
    chunks = iter([response("500 mg ", 20, 1), response("twice daily", 20, 4)])
    client, _ = make_client([chunks])

    deltas = list(client.stream(PROMPT))

    assert [d.text for d in deltas] == ["500 mg ", "twice daily", ""]
    assert deltas[-1].usage == TokenUsage(prompt=20, completion=4)


def test_stream_retries_when_the_failure_happens_before_any_text() -> None:
    client, models = make_client([api_error(503), iter([response("ok")])])

    assert "".join(d.text for d in client.stream(PROMPT)) == "ok"
    assert models.calls == 2


def test_stream_never_retries_after_text_was_sent() -> None:
    def broken() -> Iterator[Any]:
        yield response("partial ")
        raise api_error(503)

    client, models = make_client([broken(), iter([response("full answer")])])
    received: list[str] = []

    with pytest.raises(LLMUnavailableError):
        for delta in client.stream(PROMPT):
            received.append(delta.text)

    assert received == ["partial "]
    assert models.calls == 1


# --- rate limits and quota ----------------------------------------------------------------


def test_a_429_waits_for_the_delay_the_server_asked_for() -> None:
    sleeps: list[float] = []
    client, models = make_client([api_error(429, retry_info("34s")), response("ok")], sleeps)

    assert client.generate(PROMPT).text == "ok"
    assert sleeps == [34.0]
    assert models.calls == 2


def test_a_429_reads_the_delay_from_the_message_when_there_is_no_retry_info() -> None:
    sleeps: list[float] = []
    rate_limited = api_error(429, message="Please retry in 12.5s.")
    client, _ = make_client([rate_limited, response("ok")], sleeps)

    client.generate(PROMPT)

    assert sleeps == [12.5]


def test_a_429_asking_for_a_very_long_wait_fails_instead_of_blocking_the_request() -> None:
    client, models = make_client([api_error(429, retry_info("900s")), response("never")])

    with pytest.raises(LLMUnavailableError, match="rate limited"):
        client.generate(PROMPT)
    assert models.calls == 1


def test_an_exhausted_daily_quota_is_never_retried() -> None:
    daily = api_error(429, quota_failure("GenerateRequestsPerDayPerProjectPerModel-FreeTier"))
    client, models = make_client([daily, response("never")])

    with pytest.raises(LLMUnavailableError, match="daily request quota"):
        client.generate(PROMPT)
    assert models.calls == 1


def test_a_per_minute_quota_is_retried() -> None:
    per_minute = api_error(
        429, quota_failure("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"), retry_info("3s")
    )
    client, models = make_client([per_minute, response("ok")])

    assert client.generate(PROMPT).text == "ok"
    assert models.calls == 2


def test_a_streamed_daily_quota_error_is_reported_without_retrying() -> None:
    daily = api_error(429, quota_failure("GenerateRequestsPerDayPerProjectPerModel-FreeTier"))
    client, models = make_client([daily, iter([response("never")])])

    with pytest.raises(LLMUnavailableError, match="daily request quota"):
        list(client.stream(PROMPT))
    assert models.calls == 1


def test_every_attempt_waits_for_the_rate_limiter() -> None:
    now = [0.0]

    def advance(seconds: float) -> None:
        now[0] += seconds

    limiter = RateLimiter(2, clock=lambda: now[0], sleep=advance)
    client, models = make_client([response("a"), response("b"), response("c")], limiter=limiter)

    for _ in range(3):
        client.generate(PROMPT)

    assert models.calls == 3
    assert now[0] == 60.0
