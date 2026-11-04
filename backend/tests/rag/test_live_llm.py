"""Calls the real Gemini API (RUN_LIVE=1); the key comes from the environment or backend/.env."""

import os
from pathlib import Path
from typing import cast

import pytest

from app.rag.config import GeminiBackend
from app.rag.llm import GeminiClient
from app.rag.types import Prompt

pytestmark = pytest.mark.live

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _setting(name: str) -> str | None:
    if value := os.environ.get(name):
        return value
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name and value.strip():
                return value.strip()
    return None


@pytest.fixture(scope="module")
def client() -> GeminiClient:
    api_key = _setting("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY is not configured")
    backend = cast(GeminiBackend, _setting("GEMINI_BACKEND") or "studio")
    return GeminiClient(
        model=_setting("GEMINI_MODEL") or "gemini-3.5-flash-lite", api_key=api_key, backend=backend
    )


def test_generate_returns_text_and_usage(client: GeminiClient) -> None:
    result = client.generate(Prompt(system="Answer in one word.", user="Capital of France?"))

    assert "paris" in result.text.lower()
    assert result.usage is not None and result.usage.prompt > 0


def test_stream_yields_incremental_text_and_usage(client: GeminiClient) -> None:
    deltas = list(
        client.stream(
            Prompt(system="Be brief.", user="List three primary colours, comma separated.")
        )
    )

    assert "".join(d.text for d in deltas).strip()
    assert deltas[-1].usage is not None
