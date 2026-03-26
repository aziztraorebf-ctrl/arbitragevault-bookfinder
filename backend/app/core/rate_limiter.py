"""
In-memory HTTP rate limiter using sliding window counters.
No external dependencies (no Redis, no slowapi).

Designed for single-process deployments (Render).
Resets on redeploy, which is acceptable for CoWork agent traffic.
"""
import logging
import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Stale entry cleanup threshold (entries older than this are pruned)
_CLEANUP_INTERVAL_SECONDS = 300


class SlidingWindowLimiter:
    """
    Sliding window counter rate limiter.

    Tracks request counts per key (token hash or IP) within a rolling window.
    Thread-safe for single-process async usage.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> list of timestamps
        self._requests: Dict[str, list] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def _cleanup_stale(self, now: float) -> None:
        """Remove entries older than window + cleanup interval."""
        if now - self._last_cleanup < _CLEANUP_INTERVAL_SECONDS:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds - _CLEANUP_INTERVAL_SECONDS
        stale_keys = [
            k for k, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for k in stale_keys:
            del self._requests[k]

    def check(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for the given key.

        Returns:
            (allowed, remaining) - whether request is allowed and remaining quota
        """
        now = time.monotonic()
        self._cleanup_stale(now)

        # Prune expired timestamps for this key
        window_start = now - self.window_seconds
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]

        current_count = len(self._requests[key])
        remaining = self.max_requests - current_count

        if current_count >= self.max_requests:
            return False, 0

        self._requests[key].append(now)
        return True, remaining - 1


# Global limiter instances (created once, persist across requests)
_read_limiter = SlidingWindowLimiter(max_requests=30, window_seconds=60)
_write_limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60)


def _extract_key(request: Request) -> str:
    """Extract rate limit key from request (Bearer token or IP)."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        # Use first 16 chars of token as key (enough to distinguish clients)
        return f"token:{auth[7:23]}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


async def rate_limit_reads(request: Request) -> None:
    """FastAPI dependency: rate limit GET endpoints (30 req/min)."""
    key = _extract_key(request)
    allowed, remaining = _read_limiter.check(key)
    if not allowed:
        logger.warning(
            "Rate limit exceeded (reads)",
            extra={"key": key, "limit": _read_limiter.max_requests},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 30 requests per minute for read endpoints.",
            headers={"Retry-After": str(_read_limiter.window_seconds)},
        )


async def rate_limit_writes(request: Request) -> None:
    """FastAPI dependency: rate limit POST endpoints (5 req/min)."""
    key = _extract_key(request)
    allowed, remaining = _write_limiter.check(key)
    if not allowed:
        logger.warning(
            "Rate limit exceeded (writes)",
            extra={"key": key, "limit": _write_limiter.max_requests},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 5 requests per minute for write endpoints.",
            headers={"Retry-After": str(_write_limiter.window_seconds)},
        )
