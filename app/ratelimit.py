import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from app.config import settings


class SlidingWindowRateLimiter:
    """Per-key sliding-window limiter. In-memory, single-process — fine for one
    gateway replica; swap for a Redis-backed limiter before scaling horizontally."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = self.window_seconds - (now - hits[0])
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": f"{max(retry_after, 0):.0f}"},
            )

        hits.append(now)


rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


async def enforce_rate_limit(api_key: str) -> None:
    rate_limiter.check(api_key)
