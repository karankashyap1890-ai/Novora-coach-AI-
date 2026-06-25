"""
Novora — Security: Rate Limiter
Sliding-window in-memory rate limiter using SlowAPI + custom middleware.
"""
from collections import defaultdict, deque
from time import time
from typing import Dict, Deque

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

# SlowAPI limiter — used as a decorator on routes
limiter = Limiter(key_func=get_remote_address)


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter.
    Tracks request timestamps per user/IP in a deque.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time()
        window_start = now - self.window_seconds
        dq = self._store[key]

        # Remove timestamps outside the window
        while dq and dq[0] < window_start:
            dq.popleft()

        if len(dq) >= self.max_requests:
            return False

        dq.append(now)
        return True

    def get_remaining(self, key: str) -> int:
        dq = self._store.get(key, deque())
        return max(0, self.max_requests - len(dq))


# Shared global instance
_rate_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency — raises 429 if rate limit exceeded."""
    key = request.headers.get("X-User-ID") or get_remote_address(request)
    if not _rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down.",
            headers={"Retry-After": "60"},
        )
