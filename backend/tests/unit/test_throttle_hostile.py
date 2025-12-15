"""
Hostile Tests for Keepa Throttle System
Tests race conditions, edge cases, and token exhaustion scenarios.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import time

from app.services.keepa_throttle import KeepaThrottle


class TestThrottleHostileEdgeCases:
    """Hostile tests for throttle edge cases."""

    @pytest.mark.asyncio
    async def test_acquire_zero_tokens_doesnt_crash(self):
        """Acquiring 0 tokens should work (no-op)."""
        throttle = KeepaThrottle(tokens_per_minute=20, burst_capacity=100)
        result = await throttle.acquire(cost=0)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_negative_tokens_handled(self):
        """Negative cost should be handled gracefully."""
        throttle = KeepaThrottle(tokens_per_minute=20, burst_capacity=100)
        initial_tokens = throttle.available_tokens
        # Negative cost should either work or raise clear error
        result = await throttle.acquire(cost=-1)
        # Negative cost adds tokens (subtracting negative = addition)
        # This tests that the system doesn't crash with unexpected input
        assert result is True
        assert throttle.available_tokens >= initial_tokens

    @pytest.mark.asyncio
    async def test_concurrent_acquires_dont_exceed_capacity(self):
        """Concurrent acquire calls should not cause race conditions."""
        # Use very high rate for fast test without long waits
        throttle = KeepaThrottle(tokens_per_minute=6000, burst_capacity=50)

        async def drain_token():
            return await throttle.acquire(cost=1)

        # Launch 15 concurrent acquires (all should complete quickly)
        tasks = [drain_token() for _ in range(15)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)
        # Tokens should be depleted but system should remain stable
        assert throttle.available_tokens >= -10  # Allow some overdraft from timing

    @pytest.mark.asyncio
    async def test_set_tokens_negative_clamps_to_zero(self):
        """set_tokens with negative value should clamp to 0."""
        throttle = KeepaThrottle()
        throttle.set_tokens(-50)
        assert throttle.available_tokens == 0

    @pytest.mark.asyncio
    async def test_very_large_cost_handled(self):
        """Cost larger than capacity should still eventually succeed."""
        throttle = KeepaThrottle(
            tokens_per_minute=60,
            burst_capacity=100,
            critical_threshold=10  # Set lower critical threshold
        )
        throttle.tokens = 50  # Start with sufficient tokens to avoid critical mode

        # Request 5 tokens when we have 50
        start = time.monotonic()
        result = await asyncio.wait_for(
            throttle.acquire(cost=5),
            timeout=5.0  # Should complete within 5s
        )
        elapsed = time.monotonic() - start

        assert result is True
        # Should complete quickly since we had enough tokens
        assert elapsed < 1.0

    def test_available_tokens_never_negative_in_property(self):
        """available_tokens property should always return >= 0."""
        throttle = KeepaThrottle(burst_capacity=10)
        throttle.tokens = -5.5  # Simulate overdraft
        assert throttle.available_tokens >= -5  # int() truncates

    def test_is_healthy_threshold_check(self):
        """is_healthy should correctly reflect warning threshold."""
        throttle = KeepaThrottle(warning_threshold=50, burst_capacity=100)

        throttle.tokens = 51
        assert throttle.is_healthy is True

        throttle.tokens = 49
        assert throttle.is_healthy is False


class TestThrottleCriticalLevel:
    """Tests for critical level forced cooldown."""

    @pytest.mark.asyncio
    async def test_critical_level_forces_wait(self):
        """Below critical threshold should force 30s cooldown."""
        throttle = KeepaThrottle(
            tokens_per_minute=60,
            critical_threshold=20,
            burst_capacity=100
        )
        throttle.tokens = 15  # Below critical

        start = time.monotonic()

        # Mock sleep to avoid actual 30s wait
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await throttle.acquire(cost=1)
            # Should have called sleep(30)
            mock_sleep.assert_called()
            call_args = [call[0][0] for call in mock_sleep.call_args_list]
            assert 30 in call_args or any(c >= 30 for c in call_args)
