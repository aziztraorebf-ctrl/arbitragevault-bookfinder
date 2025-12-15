"""
Unit Tests for Strategic View Calculations
Tests scoring algorithms for velocity, competition, volatility, etc.
"""
import pytest
from app.api.v1.routers.strategic_views import (
    calculate_velocity_score,
    calculate_competition_level,
    calculate_price_volatility,
    calculate_demand_consistency,
    calculate_data_confidence
)


class TestVelocityScoreCalculation:
    """Tests for velocity score calculation."""

    def test_velocity_bsr_1_returns_max_score(self):
        """BSR=1 (best seller) should return ~1.0."""
        score = calculate_velocity_score(sales_rank=1)
        assert score >= 0.99

    def test_velocity_bsr_1m_returns_zero(self):
        """BSR=1,000,000 should return 0.0."""
        score = calculate_velocity_score(sales_rank=1_000_000)
        assert score == 0.0

    def test_velocity_bsr_zero_returns_zero(self):
        """BSR=0 (invalid) should return 0.0."""
        score = calculate_velocity_score(sales_rank=0)
        assert score == 0.0

    def test_velocity_negative_bsr_returns_zero(self):
        """Negative BSR should return 0.0."""
        score = calculate_velocity_score(sales_rank=-100)
        assert score == 0.0

    def test_velocity_with_sales_drops_increases_score(self):
        """Adding high sales drops should boost velocity score for poor BSR."""
        base_score = calculate_velocity_score(sales_rank=800_000)
        boosted_score = calculate_velocity_score(sales_rank=800_000, sales_drops=80)
        assert boosted_score > base_score

    def test_velocity_score_in_valid_range(self):
        """Score should always be between 0.0 and 1.0."""
        for bsr in [1, 100, 10000, 500000, 1000000, 5000000]:
            score = calculate_velocity_score(sales_rank=bsr)
            assert 0.0 <= score <= 1.0


class TestCompetitionLevel:
    """Tests for competition level calculation."""

    def test_amazon_buybox_is_high_competition(self):
        """Amazon holding Buy Box = HIGH competition."""
        level = calculate_competition_level(num_sellers=1, buy_box_amazon=True)
        assert level == "HIGH"

    def test_many_sellers_is_high_competition(self):
        """>10 sellers = HIGH competition."""
        level = calculate_competition_level(num_sellers=15, buy_box_amazon=False)
        assert level == "HIGH"

    def test_medium_sellers_is_medium(self):
        """5-10 sellers = MEDIUM competition."""
        level = calculate_competition_level(num_sellers=7, buy_box_amazon=False)
        assert level == "MEDIUM"

    def test_few_sellers_is_low(self):
        """<5 sellers = LOW competition."""
        level = calculate_competition_level(num_sellers=3, buy_box_amazon=False)
        assert level == "LOW"

    def test_zero_sellers_is_low(self):
        """0 sellers = LOW competition."""
        level = calculate_competition_level(num_sellers=0, buy_box_amazon=False)
        assert level == "LOW"


class TestPriceVolatility:
    """Tests for price volatility calculation."""

    def test_same_price_is_zero_volatility(self):
        """Current == Average = 0 volatility."""
        vol = calculate_price_volatility(current_price=20.0, avg_price=20.0)
        assert vol == 0.0

    def test_zero_current_price_returns_zero(self):
        """Zero price should return 0."""
        vol = calculate_price_volatility(current_price=0, avg_price=20.0)
        assert vol == 0.0

    def test_no_average_returns_default(self):
        """No average price = default moderate volatility."""
        vol = calculate_price_volatility(current_price=20.0, avg_price=0)
        assert vol == 0.3

    def test_high_deviation_caps_at_one(self):
        """Volatility should cap at 1.0."""
        vol = calculate_price_volatility(current_price=100.0, avg_price=10.0)
        assert vol == 1.0


class TestDemandConsistency:
    """Tests for demand consistency calculation."""

    def test_top_bsr_has_high_consistency(self):
        """Top 10% BSR should have high consistency."""
        score = calculate_demand_consistency(sales_rank=5000, category="books")
        assert score >= 0.90

    def test_zero_bsr_returns_default(self):
        """Zero BSR should return default 0.5."""
        score = calculate_demand_consistency(sales_rank=0)
        assert score == 0.5

    def test_poor_bsr_has_low_consistency(self):
        """Very high BSR should have low consistency."""
        score = calculate_demand_consistency(sales_rank=500000, category="books")
        assert score < 0.5


class TestDataConfidence:
    """Tests for data confidence calculation."""

    def test_all_data_present_high_confidence(self):
        """All data fields present = high confidence."""
        score = calculate_data_confidence(
            has_bsr=True, has_price=True, has_title=True, source="keepa_api"
        )
        assert score >= 0.8

    def test_missing_fields_reduce_confidence(self):
        """Missing fields should reduce confidence."""
        full = calculate_data_confidence(True, True, True, "keepa_api")
        partial = calculate_data_confidence(True, False, True, "keepa_api")
        assert partial < full

    def test_cached_source_slightly_lower(self):
        """Cached source should be slightly lower confidence."""
        live = calculate_data_confidence(True, True, True, "keepa_api")
        cached = calculate_data_confidence(True, True, True, "cached")
        assert cached < live
