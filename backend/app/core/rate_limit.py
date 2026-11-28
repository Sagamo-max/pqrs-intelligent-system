from collections import defaultdict, deque
import os
from threading import Lock
import time

from fastapi import HTTPException, Request, status


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class SlidingWindowRateLimiter:
    """Thread-safe in-memory IP rate limiter for public endpoints."""

    def __init__(self, default_max_requests: int = 15, default_window_seconds: int = 60):
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _limits(self) -> tuple[int, int]:
        max_requests = int(
            os.getenv("PUBLIC_PQRS_RATE_LIMIT_MAX", str(self.default_max_requests))
        )
        window_seconds = int(
            os.getenv(
                "PUBLIC_PQRS_RATE_LIMIT_WINDOW_SECONDS",
                str(self.default_window_seconds),
            )
        )
        return max_requests, window_seconds

    def check(self, key: str) -> None:
        max_requests, window_seconds = self._limits()
        if max_requests <= 0 or window_seconds <= 0:
            return

        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiadas solicitudes de radicación. Intente nuevamente más tarde.",
                )
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


public_pqrs_rate_limiter = SlidingWindowRateLimiter()


def enforce_public_pqrs_rate_limit(request: Request) -> None:
    public_pqrs_rate_limiter.check(_get_client_ip(request))
