from collections.abc import Iterator
from pathlib import Path

import pytest

from app.rag.errors import LLMUnavailableError
from app.rag.llm import LLMDelta, LLMResult
from app.rag.types import Prompt
from evals.llm_cache import CachedLLM, cache_key


class CountingLLM:
    model_name = "fake-model"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: Prompt) -> LLMResult:
        self.calls += 1
        return LLMResult(f"answer to {prompt.user}", usage=None)

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]:
        yield LLMDelta(self.generate(prompt).text)


def test_repeated_prompt_is_served_from_disk_by_a_new_instance(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    prompt = Prompt("system", "question")
    first_inner = CountingLLM()
    CachedLLM(first_inner, path, max_live_calls=5).generate(prompt)

    second_inner = CountingLLM()
    second = CachedLLM(second_inner, path, max_live_calls=5)
    result = second.generate(prompt)

    assert result.text == "answer to question"
    assert (first_inner.calls, second_inner.calls) == (1, 0)
    assert second.cache_hits == 1
    assert second.live_calls == 0


def test_key_depends_on_model_prompt_and_temperature() -> None:
    base = cache_key("m", Prompt("s", "u"))

    assert cache_key("other", Prompt("s", "u")) != base
    assert cache_key("m", Prompt("s", "different")) != base
    assert cache_key("m", Prompt("s", "u", temperature=0.9)) != base
    assert cache_key("m", Prompt("s", "u")) == base


def test_live_call_budget_stops_further_calls(tmp_path: Path) -> None:
    inner = CountingLLM()
    llm = CachedLLM(inner, tmp_path / "cache.json", max_live_calls=1)
    llm.generate(Prompt("s", "one"))

    with pytest.raises(LLMUnavailableError, match="budget"):
        llm.generate(Prompt("s", "two"))
    assert inner.calls == 1


def test_cached_prompts_do_not_consume_the_budget(tmp_path: Path) -> None:
    llm = CachedLLM(CountingLLM(), tmp_path / "cache.json", max_live_calls=1)
    prompt = Prompt("s", "one")

    llm.generate(prompt)
    llm.generate(prompt)

    assert llm.live_calls == 1


def test_stream_yields_the_cached_answer(tmp_path: Path) -> None:
    llm = CachedLLM(CountingLLM(), tmp_path / "cache.json", max_live_calls=1)

    assert [d.text for d in llm.stream(Prompt("s", "q"))] == ["answer to q"]
