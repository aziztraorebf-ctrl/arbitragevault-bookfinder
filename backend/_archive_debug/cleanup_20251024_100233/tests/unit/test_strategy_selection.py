"""
Unit tests for strategy selection logic (Textbook vs Velocity vs Balanced).
Tests _auto_select_strategy() function from keepa_parser_v2.
"""

import pytest
from decimal import Decimal

from app.services.keepa_parser_v2 import (
    _auto_select_strategy,
    _determine_target_sell_price,
    _determine_buy_cost_used
)


class TestAutoSelectStrategy:
    """Test automatic strategy selection based on price + BSR rules."""

    def test_textbook_strategy_high_price_good_bsr(self):
        """Textbook: price ≥$40, BSR ≤250k → textbook."""
        parsed = {
            "current_buybox_price": Decimal("45.00"),
            "current_bsr": 100000
        }
        assert _auto_select_strategy(parsed) == "textbook"

    def test_textbook_strategy_exact_threshold(self):
        """Textbook: price=$40, BSR=250k → textbook."""
        parsed = {
            "current_buybox_price": Decimal("40.00"),
            "current_bsr": 250000
        }
        assert _auto_select_strategy(parsed) == "textbook"

    def test_velocity_strategy_modest_price_fast_bsr(self):
        """Velocity: price ≥$25, BSR <250k → velocity."""
        parsed = {
            "current_buybox_price": Decimal("30.00"),
            "current_bsr": 50000
        }
        assert _auto_select_strategy(parsed) == "velocity"

    def test_velocity_strategy_exact_threshold(self):
        """Velocity: price=$25, BSR=249999 → velocity."""
        parsed = {
            "current_buybox_price": Decimal("25.00"),
            "current_bsr": 249999
        }
        assert _auto_select_strategy(parsed) == "velocity"

    def test_balanced_strategy_low_price(self):
        """Balanced: price < $25 → balanced."""
        parsed = {
            "current_buybox_price": Decimal("15.00"),
            "current_bsr": 50000
        }
        assert _auto_select_strategy(parsed) == "balanced"

    def test_balanced_strategy_poor_bsr(self):
        """Balanced: BSR > 250k → balanced."""
        parsed = {
            "current_buybox_price": Decimal("45.00"),
            "current_bsr": 300000
        }
        assert _auto_select_strategy(parsed) == "balanced"

    def test_balanced_strategy_textbook_price_but_poor_bsr(self):
        """Balanced: price=$50 but BSR=300k → balanced (fails BSR rule)."""
        parsed = {
            "current_buybox_price": Decimal("50.00"),
            "current_bsr": 300000
        }
        assert _auto_select_strategy(parsed) == "balanced"

    def test_balanced_strategy_missing_price(self):
        """Balanced: missing price → balanced."""
        parsed = {
            "current_bsr": 50000
        }
        assert _auto_select_strategy(parsed) == "balanced"

    def test_balanced_strategy_missing_bsr(self):
        """Balanced: missing BSR → balanced (assumes BSR=999999)."""
        parsed = {
            "current_buybox_price": Decimal("45.00")
        }
        assert _auto_select_strategy(parsed) == "balanced"

    def test_fallback_to_current_price(self):
        """Strategy selection uses current_price if current_buybox_price missing."""
        parsed = {
            "current_price": Decimal("45.00"),
            "current_bsr": 100000
        }
        assert _auto_select_strategy(parsed) == "textbook"


class TestDetermineTargetSellPrice:
    """Test sell price extraction for USED arbitrage (BuyBox target)."""

    def test_buybox_price_priority(self):
        """Priority 1: current_buybox_price."""
        data = {
            "current_buybox_price": Decimal("28.50"),
            "current_fba_price": Decimal("30.00"),
            "current_new_price": Decimal("35.00")
        }
        assert _determine_target_sell_price(data) == Decimal("28.50")

    def test_fba_price_fallback(self):
        """Priority 2: current_fba_price if BuyBox missing."""
        data = {
            "current_fba_price": Decimal("30.00"),
            "current_new_price": Decimal("35.00")
        }
        assert _determine_target_sell_price(data) == Decimal("30.00")

    def test_new_price_fallback(self):
        """Priority 3: current_new_price if BuyBox and FBA missing."""
        data = {
            "current_new_price": Decimal("35.00")
        }
        assert _determine_target_sell_price(data) == Decimal("35.00")

    def test_no_valid_price(self):
        """Returns None if all prices missing."""
        data = {}
        assert _determine_target_sell_price(data) is None

    def test_ignores_zero_price(self):
        """Ignores zero prices, falls back to next available."""
        data = {
            "current_buybox_price": 0,
            "current_fba_price": Decimal("30.00")
        }
        assert _determine_target_sell_price(data) == Decimal("30.00")

    def test_excludes_amazon_price(self):
        """Does NOT use current_amazon_price (NEW price, too high for USED arbitrage)."""
        data = {
            "current_amazon_price": Decimal("80.00"),  # Should be ignored
            "current_new_price": Decimal("35.00")
        }
        assert _determine_target_sell_price(data) == Decimal("35.00")

    def test_excludes_used_price(self):
        """Does NOT use current_used_price (defective items, too low)."""
        data = {
            "current_used_price": Decimal("0.55"),  # Should be ignored
            "current_new_price": Decimal("35.00")
        }
        assert _determine_target_sell_price(data) == Decimal("35.00")


class TestDetermineBuyCostUsed:
    """Test purchase cost extraction from FBA USED sellers."""

    def test_fba_price_primary_source(self):
        """Priority 1: current_fba_price (FBA USED sellers)."""
        data = {
            "current_fba_price": Decimal("18.50"),
            "lowest_offer_new": Decimal("25.00")
        }
        assert _determine_buy_cost_used(data) == Decimal("18.50")

    def test_new_price_fallback(self):
        """Priority 2: lowest_offer_new if FBA missing."""
        data = {
            "lowest_offer_new": Decimal("25.00")
        }
        assert _determine_buy_cost_used(data) == Decimal("25.00")

    def test_no_valid_cost(self):
        """Returns None if all sources missing."""
        data = {}
        assert _determine_buy_cost_used(data) is None

    def test_ignores_zero_cost(self):
        """Ignores zero costs, falls back to next available."""
        data = {
            "current_fba_price": 0,
            "lowest_offer_new": Decimal("25.00")
        }
        assert _determine_buy_cost_used(data) == Decimal("25.00")

    def test_excludes_used_price(self):
        """Does NOT use current_used_price (too low, defective items)."""
        data = {
            "current_used_price": Decimal("0.55"),  # Should be ignored
            "current_fba_price": Decimal("18.50")
        }
        assert _determine_buy_cost_used(data) == Decimal("18.50")


class TestPriceValidationLogic:
    """Test validation: buy_cost must be < sell_price for valid arbitrage."""

    def test_valid_arbitrage_opportunity(self):
        """Valid: buy=$18, sell=$28 → profitable."""
        data = {
            "current_buybox_price": Decimal("28.00"),
            "current_fba_price": Decimal("18.00")
        }
        sell_price = _determine_target_sell_price(data)
        buy_cost = _determine_buy_cost_used(data)

        assert sell_price is not None
        assert buy_cost is not None
        assert buy_cost < sell_price  # Valid arbitrage

    def test_invalid_arbitrage_buy_exceeds_sell(self):
        """Invalid: buy=$30, sell=$28 → no profit."""
        data = {
            "current_buybox_price": Decimal("28.00"),
            "current_fba_price": Decimal("30.00")
        }
        sell_price = _determine_target_sell_price(data)
        buy_cost = _determine_buy_cost_used(data)

        assert sell_price is not None
        assert buy_cost is not None
        assert buy_cost >= sell_price  # Invalid arbitrage (should trigger fallback)

    def test_edge_case_equal_prices(self):
        """Edge case: buy=sell → no margin."""
        data = {
            "current_buybox_price": Decimal("28.00"),
            "current_fba_price": Decimal("28.00")
        }
        sell_price = _determine_target_sell_price(data)
        buy_cost = _determine_buy_cost_used(data)

        assert sell_price == buy_cost  # No margin (should trigger fallback)
