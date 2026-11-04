"""Per-patient mutual exclusion for operations that write a vector collection."""

import threading
from collections.abc import Iterator
from contextlib import contextmanager


class PatientLocks:
    """Serialises ingestion and deletion per patient while patients run in parallel.

    Chroma collections are not safe for concurrent writers, and an upload spans
    several steps (embed, write vectors, commit row) that must not interleave
    with a delete of the same patient.
    """

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    @contextmanager
    def hold(self, uhid: str) -> Iterator[None]:
        with self._guard:
            lock = self._locks.setdefault(uhid, threading.Lock())
        with lock:
            yield
