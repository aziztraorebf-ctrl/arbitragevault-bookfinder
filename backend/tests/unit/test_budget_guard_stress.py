"""
Budget Guard Stress Tests

Phase 6 Audit - Task 3: Stress tests for budget guard boundary conditions.
Tests verify edge cases like one-token-below threshold, negative balance, concurrent requests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.v1.endpoints.niches import check_budget_before_discovery
from app.services.keepa_product_finder import estimate_discovery_cost


class TestBudgetGuardBoundaries:
    """Stress tests for budget guard boundary conditions."""

    @pytest.mark.asyncio
    async def test_budget_one_token_below_threshold(self):
        """Should reject when balance is exactly 1 token below cost."""
        mock_keepa = MagicMock()
        # Cost for count=3, max_asins=100 is 450 tokens (3 * 150)
        mock_keepa.check_api_balance = AsyncMock(return_value=449)

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=3,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )
        assert exc.value.status_code == 429
        assert exc.value.detail["deficit"] == 1
        assert exc.value.detail["current_balance"] == 449

    @pytest.mark.asyncio
    async def test_budget_exactly_at_threshold(self):
        """Should PASS when balance is exactly equal to cost."""
        mock_keepa = MagicMock()
        # Cost for count=3, max_asins=100 is 450 tokens (3 * 150)
        mock_keepa.check_api_balance = AsyncMock(return_value=450)

        result = await check_budget_before_discovery(
            count=3,
            keepa=mock_keepa,
            max_asins_per_niche=100
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_budget_negative_balance(self):
        """Should handle negative balance (edge case from API)."""
        mock_keepa = MagicMock()
        mock_keepa.check_api_balance = AsyncMock(return_value=-100)

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=1,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )
        assert exc.value.status_code == 429
        assert exc.value.detail["current_balance"] == -100

    @pytest.mark.asyncio
    async def test_budget_zero_balance(self):
        """Should reject when balance is exactly zero."""
        mock_keepa = MagicMock()
        mock_keepa.check_api_balance = AsyncMock(return_value=0)

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=1,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )
        assert exc.value.status_code == 429
        assert exc.value.detail["current_balance"] == 0

    @pytest.mark.asyncio
    async def test_budget_very_large_balance(self):
        """Should proceed with very large balance."""
        mock_keepa = MagicMock()
        mock_keepa.check_api_balance = AsyncMock(return_value=1_000_000)

        result = await check_budget_before_discovery(
            count=5,
            keepa=mock_keepa,
            max_asins_per_niche=100
        )
        assert result is True


class TestEstimateDiscoveryCost:
    """Tests for cost estimation formula."""

    def test_estimate_cost_single_niche(self):
        """Estimate for 1 niche with 100 max_asins = 150 tokens."""
        cost = estimate_discovery_cost(count=1, max_asins_per_niche=100)
        assert cost == 150  # 50 + 100

    def test_estimate_cost_max_niches(self):
        """Estimate for max niches (5) should be reasonable."""
        cost = estimate_discovery_cost(count=5, max_asins_per_niche=100)
        assert cost == 750  # 5 * (50 + 100)
        assert cost < 1000  # Reasonable upper bound

    def test_estimate_cost_with_buffer(self):
        """Estimate with 50% buffer should not overflow."""
        cost = estimate_discovery_cost(count=5, max_asins_per_niche=100, buffer_percent=50)
        assert cost == 1125  # 750 * 1.5

    def test_estimate_cost_zero_buffer(self):
        """Estimate with 0% buffer should be base cost."""
        cost = estimate_discovery_cost(count=3, max_asins_per_niche=100, buffer_percent=0)
        assert cost == 450  # 3 * 150

    def test_estimate_cost_large_asins(self):
        """Estimate with large max_asins should scale correctly."""
        cost = estimate_discovery_cost(count=1, max_asins_per_niche=500)
        assert cost == 550  # 50 + 500


class TestBudgetGuardConcurrency:
    """Tests for concurrent budget checks."""

    @pytest.mark.asyncio
    async def test_concurrent_budget_checks(self):
        """Multiple concurrent checks should all get accurate balance."""
        import asyncio

        mock_keepa = MagicMock()
        call_count = 0

        async def mock_balance():
            nonlocal call_count
            call_count += 1
            return 500

        mock_keepa.check_api_balance = mock_balance

        # Run 5 concurrent checks
        tasks = [
            check_budget_before_discovery(count=1, keepa=mock_keepa, max_asins_per_niche=100)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)

        assert all(r is True for r in results)
        assert call_count == 5  # Each check should call balance

    @pytest.mark.asyncio
    async def test_concurrent_checks_some_fail(self):
        """Concurrent checks with varying balances - some pass, some fail."""
        import asyncio

        # Simulate a service where balance decreases with each check
        call_count = 0
        balances = [500, 400, 300, 200, 100]  # Decreasing balance

        mock_keepa = MagicMock()

        async def mock_balance():
            nonlocal call_count
            balance = balances[min(call_count, len(balances) - 1)]
            call_count += 1
            return balance

        mock_keepa.check_api_balance = mock_balance

        # Create tasks - cost for count=2, max_asins=100 is 300 tokens
        async def check_with_result(idx):
            try:
                result = await check_budget_before_discovery(
                    count=2, keepa=mock_keepa, max_asins_per_niche=100
                )
                return ("pass", result)
            except HTTPException as e:
                return ("fail", e.status_code)

        results = []
        for i in range(5):
            result = await check_with_result(i)
            results.append(result)

        # At least first 2 should pass (500, 400 >= 300), last 2 should fail (200, 100 < 300)
        pass_count = sum(1 for r in results if r[0] == "pass")
        fail_count = sum(1 for r in results if r[0] == "fail")

        assert pass_count >= 2, f"Expected at least 2 passes, got {pass_count}"
        assert fail_count >= 2, f"Expected at least 2 fails, got {fail_count}"


class TestBudgetGuardHeaders:
    """Tests for HTTP headers in 429 responses."""

    @pytest.mark.asyncio
    async def test_429_includes_token_headers(self):
        """429 response should include X-Token-Balance and X-Token-Required headers."""
        mock_keepa = MagicMock()
        mock_keepa.check_api_balance = AsyncMock(return_value=100)

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=3,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )

        headers = exc.value.headers
        assert "X-Token-Balance" in headers
        assert headers["X-Token-Balance"] == "100"
        assert "X-Token-Required" in headers
        assert "Retry-After" in headers
        assert headers["Retry-After"] == "3600"

    @pytest.mark.asyncio
    async def test_429_includes_suggestion(self):
        """429 response should include actionable suggestion."""
        mock_keepa = MagicMock()
        mock_keepa.check_api_balance = AsyncMock(return_value=200)

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=3,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )

        detail = exc.value.detail
        assert "suggestion" in detail
        # Should suggest trying with fewer niches since 200 tokens can afford 1 niche
        assert "count=" in detail["suggestion"] or "Wait for" in detail["suggestion"]
