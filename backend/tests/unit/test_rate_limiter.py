"""Tests for the in-memory HTTP rate limiter."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

import time
import pytest
from unittest.mock import MagicMock

from app.core.rate_limiter import SlidingWindowLimiter


def test_allows_requests_within_limit():
    """Requests within the limit should be allowed."""
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60)
    for i in range(5):
        allowed, remaining = limiter.check("user1")
        assert allowed is True
        assert remaining == 4 - i


def test_blocks_requests_over_limit():
    """Requests over the limit should be blocked."""
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("user1")

    allowed, remaining = limiter.check("user1")
    assert allowed is False
    assert remaining == 0


def test_independent_keys():
    """Different keys have independent limits."""
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=60)

    limiter.check("user1")
    limiter.check("user1")
    # user1 is now exhausted
    allowed_user1, _ = limiter.check("user1")
    assert allowed_user1 is False

    # user2 should still be allowed
    allowed_user2, remaining = limiter.check("user2")
    assert allowed_user2 is True
    assert remaining == 1


def test_window_expiry():
    """Requests should be allowed again after the window expires."""
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=1)

    limiter.check("user1")
    limiter.check("user1")
    allowed, _ = limiter.check("user1")
    assert allowed is False

    # Wait for window to expire
    time.sleep(1.1)

    allowed, remaining = limiter.check("user1")
    assert allowed is True
    assert remaining == 1


def test_sliding_window_partial_expiry():
    """Only expired timestamps should be pruned, not all."""
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=1)

    limiter.check("user1")  # t=0
    time.sleep(0.6)
    limiter.check("user1")  # t=0.6
    limiter.check("user1")  # t=0.6
    # All 3 used

    time.sleep(0.5)
    # t=1.1 : first request expired, 2 remain in window
    allowed, remaining = limiter.check("user1")
    assert allowed is True


def test_cleanup_stale_entries():
    """Stale entries should be cleaned up periodically."""
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=1)

    limiter.check("old_user")
    # Simulate time passing beyond window + cleanup interval
    # by directly manipulating internal state
    limiter._requests["old_user"] = [time.monotonic() - 400]
    limiter._last_cleanup = time.monotonic() - 400

    # Trigger cleanup by checking another user
    limiter.check("new_user")

    # old_user's expired entry should be cleaned
    assert "old_user" not in limiter._requests


def test_zero_remaining_before_block():
    """Last allowed request should report 0 remaining."""
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60)
    allowed, remaining = limiter.check("user1")
    assert allowed is True
    assert remaining == 0

    # Next request should be blocked
    allowed, remaining = limiter.check("user1")
    assert allowed is False
    assert remaining == 0
