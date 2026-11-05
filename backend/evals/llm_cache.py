"""A disk-backed LLM wrapper so re-running the answer evaluation costs no API quota.

Entries are keyed by a hash of the model name and the full prompt (system text, user text
and temperature), so changing retrieval or prompts automatically invalidates only the
answers that actually changed. A hard cap on live calls guards the free-tier key.
"""

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

from app.rag.errors import LLMUnavailableError
from app.rag.llm import LLMClient, LLMDelta, LLMResult
from app.rag.types import Prompt


def cache_key(model: str, prompt: Prompt) -> str:
    payload = json.dumps([model, prompt.system, prompt.user, prompt.temperature])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CachedLLM:
    """Serves repeated prompts from ``path``; calls ``inner`` only for new ones."""

    def __init__(self, inner: LLMClient, path: Path, *, max_live_calls: int) -> None:
        self._inner = inner
        self._path = path
        self._max_live_calls = max_live_calls
        self._entries = _load(path)
        self.live_calls = 0
        self.cache_hits = 0

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    def generate(self, prompt: Prompt) -> LLMResult:
        key = cache_key(self.model_name, prompt)
        if key in self._entries:
            self.cache_hits += 1
            return LLMResult(self._entries[key], usage=None)
        if self.live_calls >= self._max_live_calls:
            raise LLMUnavailableError(
                f"Live LLM call budget of {self._max_live_calls} reached; "
                "re-run to continue from the cache."
            )
        self.live_calls += 1
        result = self._inner.generate(prompt)
        self._entries[key] = result.text
        _save(self._path, self._entries)
        return result

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]:
        result = self.generate(prompt)
        yield LLMDelta(result.text, result.usage)


def _load(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _save(path: Path, entries: dict[str, str]) -> None:
    """Write after every live call so a crash or quota error never loses paid-for answers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    temporary.replace(path)
