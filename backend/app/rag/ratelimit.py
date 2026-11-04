"""Client-side request throttling, so a free-tier API quota is never burnt by bursts."""

import threading
import time
from collections import deque
from collections.abc import Callable

WINDOW_SECONDS = 60.0


class RateLimiter:
    """Sliding-window limiter: at most ``max_requests`` acquisitions in any 60 seconds.

    Thread-safe. The wait happens outside the lock so one sleeping caller never
    blocks others from checking the window.
    """

    def __init__(
        self,
        max_requests: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        self._max_requests = max_requests
        self._clock = clock
        self._sleep = sleep
        self._starts: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a request may start, then record it."""
        while (wait := self._try_acquire()) > 0:
            self._sleep(wait)

    def _try_acquire(self) -> float:
        """Record the request and return 0, or return how long to wait before trying again."""
        with self._lock:
            now = self._clock()
            while self._starts and now - self._starts[0] >= WINDOW_SECONDS:
                self._starts.popleft()
            if len(self._starts) < self._max_requests:
                self._starts.append(now)
                return 0.0
            return self._starts[0] + WINDOW_SECONDS - now
