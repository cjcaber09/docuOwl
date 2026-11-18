from app.auth.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_blocks():
    limiter = RateLimiter(max_attempts=3, window_seconds=60, clock=FakeClock())

    assert [limiter.allow("1.2.3.4") for _ in range(4)] == [True, True, True, False]


def test_attempts_expire_after_the_window():
    clock = FakeClock()
    limiter = RateLimiter(max_attempts=1, window_seconds=60, clock=clock)
    limiter.allow("1.2.3.4")

    clock.now += 61

    assert limiter.allow("1.2.3.4") is True


def test_each_key_is_counted_separately():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, clock=FakeClock())
    limiter.allow("1.2.3.4")

    assert limiter.allow("5.6.7.8") is True
