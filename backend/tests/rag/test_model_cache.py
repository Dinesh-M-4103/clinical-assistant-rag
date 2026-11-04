from pathlib import Path
from typing import Any

from app.rag.model_cache import load_cached_first


class _Recorder:
    """Stands in for a model class; raises ``OSError`` while the model is not cached."""

    def __init__(self, cached: bool) -> None:
        self.cached = cached
        self.calls: list[dict[str, Any]] = []

    def __call__(self, name: str, **options: Any) -> str:
        self.calls.append(options)
        if options.get("local_files_only") and not self.cached:
            raise OSError("not in the cache")
        return name


def test_cached_model_is_loaded_without_going_online(tmp_path: Path) -> None:
    factory = _Recorder(cached=True)

    assert load_cached_first(factory, "org/model", tmp_path, max_length=64) == "org/model"

    assert factory.calls == [
        {"cache_folder": str(tmp_path), "local_files_only": True, "max_length": 64}
    ]


def test_missing_model_is_downloaded_on_first_use(tmp_path: Path) -> None:
    factory = _Recorder(cached=False)

    assert load_cached_first(factory, "org/model", tmp_path) == "org/model"

    assert [call.get("local_files_only", False) for call in factory.calls] == [True, False]


def test_default_cache_location_is_left_to_the_library() -> None:
    factory = _Recorder(cached=True)

    load_cached_first(factory, "org/model", None)

    assert factory.calls[0]["cache_folder"] is None
