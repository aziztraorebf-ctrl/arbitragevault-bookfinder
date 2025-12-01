"""
Tests for Niche Discovery Budget Guard - Phase 6 TDD

Tests the dynamic cost estimation and budget checking for niche discovery
to prevent token consumption without results.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.keepa_product_finder import KeepaProductFinderService


class TestNicheBudgetEstimation:
    """Tests for dynamic cost estimation."""

    def test_estimate_niche_discovery_cost_single_niche(self):
        """Cost estimation for 1 niche should be ~150 tokens (50 bestsellers + 100 filtering)."""
        # Formula: bestsellers (50) + filtering (100 ASINs * 1 token)
        from app.services.keepa_product_finder import estimate_discovery_cost

        estimated = estimate_discovery_cost(count=1, max_asins_per_niche=100)

        assert estimated == 150  # 50 + 100

    def test_estimate_niche_discovery_cost_three_niches(self):
        """Cost estimation for 3 niches should be ~450 tokens."""
        from app.services.keepa_product_finder import estimate_discovery_cost

        estimated = estimate_discovery_cost(count=3, max_asins_per_niche=100)

        assert estimated == 450  # 3 * (50 + 100)

    def test_estimate_niche_discovery_cost_with_buffer(self):
        """Cost estimation should include safety buffer."""
        from app.services.keepa_product_finder import estimate_discovery_cost

        # With 20% buffer
        estimated = estimate_discovery_cost(count=3, max_asins_per_niche=100, buffer_percent=20)

        assert estimated == 540  # 450 * 1.2


class TestBudgetGuardRejectsInsufficientTokens:
    """Tests for budget guard rejection when tokens insufficient."""

    @pytest.mark.asyncio
    async def test_discover_rejects_if_budget_insufficient(self):
        """Discovery should fail fast with 429 if balance < estimated cost."""
        from app.api.v1.endpoints.niches import check_budget_before_discovery

        # Mock keepa with low balance
        mock_keepa = AsyncMock()
        mock_keepa.check_api_balance.return_value = 100  # Only 100 tokens

        # Trying to discover 3 niches (needs ~450 tokens)
        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=3,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )

        assert exc.value.status_code == 429
        assert "insufficient" in exc.value.detail["message"].lower()
        assert exc.value.detail["estimated_cost"] == 450
        assert exc.value.detail["current_balance"] == 100
        assert exc.value.detail["deficit"] == 350

    @pytest.mark.asyncio
    async def test_discover_proceeds_if_budget_sufficient(self):
        """Discovery should proceed if balance >= estimated cost."""
        from app.api.v1.endpoints.niches import check_budget_before_discovery

        # Mock keepa with sufficient balance
        mock_keepa = AsyncMock()
        mock_keepa.check_api_balance.return_value = 500  # Enough for 3 niches

        # Should NOT raise - returns True to proceed
        result = await check_budget_before_discovery(
            count=3,
            keepa=mock_keepa,
            max_asins_per_niche=100
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_budget_response_includes_suggestion(self):
        """429 response should include actionable suggestion."""
        from app.api.v1.endpoints.niches import check_budget_before_discovery

        mock_keepa = AsyncMock()
        mock_keepa.check_api_balance.return_value = 200  # Enough for 1 niche only

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=3,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )

        assert "suggestion" in exc.value.detail
        assert "count=1" in exc.value.detail["suggestion"]


class TestBudgetGuardEdgeCases:
    """Edge cases for budget guard."""

    @pytest.mark.asyncio
    async def test_budget_exact_match_proceeds(self):
        """Discovery should proceed if balance == estimated cost (exact match)."""
        from app.api.v1.endpoints.niches import check_budget_before_discovery

        mock_keepa = AsyncMock()
        mock_keepa.check_api_balance.return_value = 450  # Exact match for 3 niches

        result = await check_budget_before_discovery(
            count=3,
            keepa=mock_keepa,
            max_asins_per_niche=100
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_budget_check_with_zero_balance(self):
        """Should reject immediately with zero balance."""
        from app.api.v1.endpoints.niches import check_budget_before_discovery

        mock_keepa = AsyncMock()
        mock_keepa.check_api_balance.return_value = 0

        with pytest.raises(HTTPException) as exc:
            await check_budget_before_discovery(
                count=1,
                keepa=mock_keepa,
                max_asins_per_niche=100
            )

        assert exc.value.status_code == 429
        assert exc.value.detail["current_balance"] == 0

    def test_estimate_with_zero_niches_returns_zero(self):
        """Edge case: 0 niches should cost 0 tokens."""
        from app.services.keepa_product_finder import estimate_discovery_cost

        estimated = estimate_discovery_cost(count=0, max_asins_per_niche=100)

        assert estimated == 0


class TestFBASellerFilter:
    """Tests for FBA seller count competition filter (Phase 6)."""

    def test_filter_asins_by_criteria_signature_includes_max_fba_sellers(self):
        """Verify _filter_asins_by_criteria accepts max_fba_sellers parameter."""
        import inspect
        from app.services.keepa_product_finder import KeepaProductFinderService

        sig = inspect.signature(KeepaProductFinderService._filter_asins_by_criteria)
        params = list(sig.parameters.keys())

        assert "max_fba_sellers" in params

    def test_discover_products_signature_includes_max_fba_sellers(self):
        """Verify discover_products accepts max_fba_sellers parameter."""
        import inspect
        from app.services.keepa_product_finder import KeepaProductFinderService

        sig = inspect.signature(KeepaProductFinderService.discover_products)
        params = list(sig.parameters.keys())

        assert "max_fba_sellers" in params

    def test_discover_with_scoring_signature_includes_max_fba_sellers(self):
        """Verify discover_with_scoring accepts max_fba_sellers parameter."""
        import inspect
        from app.services.keepa_product_finder import KeepaProductFinderService

        sig = inspect.signature(KeepaProductFinderService.discover_with_scoring)
        params = list(sig.parameters.keys())

        assert "max_fba_sellers" in params

    def test_niche_templates_have_max_fba_sellers(self):
        """All niche templates should define max_fba_sellers."""
        from app.services.niche_templates import CURATED_NICHES

        for template in CURATED_NICHES:
            assert "max_fba_sellers" in template, f"Template {template['id']} missing max_fba_sellers"
            assert isinstance(template["max_fba_sellers"], int), f"Template {template['id']} max_fba_sellers should be int"
            assert template["max_fba_sellers"] > 0, f"Template {template['id']} max_fba_sellers should be > 0"

    def test_strategy_configs_have_max_fba_sellers(self):
        """Strategy configs should define max_fba_sellers thresholds."""
        from app.services.niche_templates import STRATEGY_CONFIGS

        assert "smart_velocity" in STRATEGY_CONFIGS
        assert "textbooks" in STRATEGY_CONFIGS

        # Smart Velocity should allow up to 5 FBA sellers
        assert STRATEGY_CONFIGS["smart_velocity"]["max_fba_sellers"] == 5

        # Textbooks should be more restrictive (3 FBA sellers)
        assert STRATEGY_CONFIGS["textbooks"]["max_fba_sellers"] == 3
