"""Tiny helper so every stage reports durations the same way."""

import time


def now() -> float:
    """Monotonic timestamp to pass to :func:`elapsed_ms` later."""
    return time.perf_counter()


def elapsed_ms(started: float) -> int:
    """Whole milliseconds since ``started``."""
    return round((time.perf_counter() - started) * 1000)
