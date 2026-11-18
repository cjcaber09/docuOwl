import time
from collections import defaultdict, deque
from collections.abc import Callable


class RateLimiter:
    """Allows at most `max_attempts` per `window_seconds` for each key (an IP address or an email).

    Kept in memory, which is correct while only one backend runs (spec section 13).
    """

    def __init__(self, max_attempts: int, window_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self._clock()
        attempts = self._attempts[key]
        # Forget attempts that are older than the window.
        while attempts and now - attempts[0] >= self.window_seconds:
            attempts.popleft()
        if len(attempts) >= self.max_attempts:
            return False
        attempts.append(now)
        return True

    def reset(self) -> None:
        self._attempts.clear()


login_by_ip = RateLimiter(max_attempts=20, window_seconds=15 * 60)
login_by_email = RateLimiter(max_attempts=10, window_seconds=15 * 60)
signup_by_ip = RateLimiter(max_attempts=10, window_seconds=60 * 60)


def reset_all_limiters() -> None:
    for limiter in (login_by_ip, login_by_email, signup_by_ip):
        limiter.reset()
