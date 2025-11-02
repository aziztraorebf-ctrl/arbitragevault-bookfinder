"""
Keepa API Throttling System
Prevents token exhaustion by implementing token bucket algorithm
Phase 3 Day 10 - Protection contre épuisement tokens
"""
import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class KeepaThrottle:
    """
    Token bucket implementation for Keepa API rate limiting.

    Prevents API token exhaustion by:
    - Limiting requests to 20/minute (Keepa plan limit)
    - Managing burst capacity conservatively
    - Auto-pausing when tokens are low
    - Thread-safe for concurrent requests
    """

    def __init__(self,
                 tokens_per_minute: int = 20,
                 burst_capacity: int = 100,  # Conservative to avoid negative balance
                 warning_threshold: int = 50,
                 critical_threshold: int = 20):
        """
        Initialize throttle with conservative defaults.

        Args:
            tokens_per_minute: Rate limit (20 for current Keepa plan)
            burst_capacity: Max tokens to accumulate (100 = 5 min buffer)
            warning_threshold: Warn when below this level
            critical_threshold: Force wait when below this level
        """
        self.rate = tokens_per_minute / 60.0  # tokens per second
        self.capacity = burst_capacity
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.tokens = float(burst_capacity)
        self.last_refill = time.monotonic()  # Use monotonic to avoid clock issues
        self._lock = asyncio.Lock()  # Thread-safe for concurrent requests
        self.total_requests = 0
        self.total_wait_time = 0.0

    async def acquire(self, cost: int = 1) -> bool:
        """
        Acquire tokens for API request, wait if necessary.

        Args:
            cost: Number of tokens needed (usually 1 per request)

        Returns:
            True when tokens acquired successfully
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill

            # Progressive refill based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )
            self.last_refill = now

            # Log warning if tokens are low (only log once per 10 tokens drop)
            if self.tokens < self.warning_threshold and int(self.tokens) % 10 == 0:
                logger.warning(
                    f"⚠️ Keepa tokens low: {self.tokens:.0f} remaining "
                    f"(threshold: {self.warning_threshold})"
                )

            # Critical level - force longer wait
            if self.tokens < self.critical_threshold:
                logger.error(
                    f"🔴 Keepa tokens CRITICAL: {self.tokens:.0f} remaining. "
                    f"Forcing 30s cooldown."
                )
                await asyncio.sleep(30)  # Force cooldown
                # Recalculate after cooldown
                elapsed = 30
                self.tokens = min(
                    self.capacity,
                    self.tokens + (elapsed * self.rate)
                )

            # Calculate wait time if insufficient tokens
            if self.tokens < cost:
                wait_time = (cost - self.tokens) / self.rate
                logger.info(
                    f"📊 Throttling: waiting {wait_time:.1f}s for {cost} tokens "
                    f"(current: {self.tokens:.1f})"
                )
                self.total_wait_time += wait_time
                await asyncio.sleep(wait_time)

                # Recalculate tokens after wait
                now = time.monotonic()
                elapsed = wait_time
                self.tokens = min(
                    self.capacity,
                    self.tokens + (elapsed * self.rate)
                )
                self.last_refill = now

            # Consume tokens
            self.tokens -= cost
            self.total_requests += 1

            # Log every 10 requests
            if self.total_requests % 10 == 0:
                logger.debug(
                    f"📈 Throttle stats: {self.total_requests} requests, "
                    f"{self.total_wait_time:.1f}s total wait, "
                    f"{self.tokens:.0f} tokens available"
                )

            return True

    @property
    def available_tokens(self) -> int:
        """Get available tokens without consuming them."""
        return int(self.tokens)

    @property
    def is_healthy(self) -> bool:
        """Check if we have sufficient tokens."""
        return self.tokens > self.warning_threshold

    def reset_stats(self):
        """Reset statistics counters."""
        self.total_requests = 0
        self.total_wait_time = 0.0
        logger.info("📊 Throttle statistics reset")

    async def wait_for_tokens(self, required: int = 50):
        """
        Wait until we have a specific number of tokens available.
        Useful before starting batch operations.
        """
        while self.available_tokens < required:
            wait_time = (required - self.tokens) / self.rate
            logger.info(
                f"⏳ Waiting {wait_time:.1f}s to accumulate {required} tokens"
            )
            await asyncio.sleep(wait_time)

            # Refill tokens
            now = time.monotonic()
            elapsed = wait_time
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.rate)
            )
            self.last_refill = now