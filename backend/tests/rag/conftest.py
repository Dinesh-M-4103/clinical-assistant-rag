"""Opt-in gates for the expensive RAG tests.

* ``slow``: loads the real embedding and reranker models (run with ``-m slow`` or RUN_SLOW=1).
* ``live``: calls the real Gemini API (run with RUN_LIVE=1).
"""

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_slow = os.environ.get("RUN_SLOW") == "1" or "slow" in (config.getoption("-m") or "")
    run_live = os.environ.get("RUN_LIVE") == "1"
    for item in items:
        if item.get_closest_marker("slow") and not run_slow:
            item.add_marker(pytest.mark.skip(reason="loads real models; use -m slow"))
        if item.get_closest_marker("live") and not run_live:
            item.add_marker(pytest.mark.skip(reason="calls the real LLM; set RUN_LIVE=1"))
