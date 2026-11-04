"""Loading Hugging Face models without needless network round-trips."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

_M = TypeVar("_M")


def load_cached_first(
    factory: Callable[..., _M], model_name: str, cache_dir: Path | None, **options: Any
) -> _M:
    """Build a model from the local cache, downloading it only when it is not there yet.

    By default every load asks the Hub whether a newer revision exists, which adds
    about twenty seconds to each start-up on a slow connection even though the files
    are already on disk. The models are pinned by name, so the cached copy is enough.
    """
    cache = str(cache_dir) if cache_dir else None
    try:
        return factory(model_name, cache_folder=cache, local_files_only=True, **options)
    except OSError:
        return factory(model_name, cache_folder=cache, **options)
