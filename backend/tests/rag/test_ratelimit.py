import threading

import pytest

from app.rag.ratelimit import RateLimiter


class FakeClock:
    """A clock that only moves when somebody sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class WouldBlockError(Exception):
    pass


def make_limiter(max_requests: int) -> tuple[RateLimiter, FakeClock]:
    clock = FakeClock()
    return RateLimiter(max_requests, clock=lambda: clock.now, sleep=clock.sleep), clock


def test_requests_under_the_limit_do_not_wait() -> None:
    limiter, clock = make_limiter(3)

    for _ in range(3):
        limiter.acquire()

    assert clock.sleeps == []


def test_the_request_over_the_limit_waits_until_the_oldest_leaves_the_window() -> None:
    limiter, clock = make_limiter(2)
    limiter.acquire()
    clock.now = 10.0
    limiter.acquire()

    limiter.acquire()

    assert clock.sleeps == [50.0]
    assert clock.now == 60.0


def test_the_window_slides_instead_of_resetting() -> None:
    limiter, clock = make_limiter(2)
    limiter.acquire()
    clock.now = 30.0
    limiter.acquire()
    clock.now = 60.0

    limiter.acquire()
    limiter.acquire()

    assert clock.sleeps == [30.0]


def test_a_burst_of_requests_never_exceeds_the_limit_in_any_window() -> None:
    limiter, clock = make_limiter(8)
    starts: list[float] = []

    for _ in range(40):
        limiter.acquire()
        starts.append(clock.now)

    for start in starts:
        assert sum(1 for other in starts if start <= other < start + 60.0) <= 8


def test_concurrent_callers_never_exceed_the_limit() -> None:
    def refuse_to_wait(_: float) -> None:
        raise WouldBlockError

    limiter = RateLimiter(5, clock=lambda: 0.0, sleep=refuse_to_wait)
    outcomes: list[bool] = []

    def worker() -> None:
        try:
            limiter.acquire()
            outcomes.append(True)
        except WouldBlockError:
            outcomes.append(False)

    threads = [threading.Thread(target=worker) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert outcomes.count(True) == 5


def test_a_limit_below_one_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RateLimiter(0)
