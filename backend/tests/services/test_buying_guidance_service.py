"""
Unit tests for Buying Guidance Service.

TDD: These tests are written FIRST before implementation.
Tests the transformation of intrinsic value data into user-friendly buying guidance.
"""
import pytest
from dataclasses import asdict
from typing import Dict, Any

# Import will fail until service is implemented - expected for TDD
from app.services.buying_guidance_service import (
    BuyingGuidance,
    BuyingGuidanceService,
    calculate_max_buy_price,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def high_confidence_intrinsic() -> Dict[str, Any]:
    """
    Intrinsic value result with HIGH confidence.
    Simulates a textbook with stable pricing.
    """
    return {
        'low': 45.00,
        'median': 52.00,
        'high': 58.00,
        'confidence': 'HIGH',
        'volatility': 0.12,
        'data_points': 85,
        'window_days': 90,
        'reason': 'High confidence: 85 data points with 12.0% volatility'
    }


@pytest.fixture
def medium_confidence_intrinsic() -> Dict[str, Any]:
    """
    Intrinsic value result with MEDIUM confidence.
    """
    return {
        'low': 30.00,
        'median': 35.00,
        'high': 42.00,
        'confidence': 'MEDIUM',
        'volatility': 0.25,
        'data_points': 22,
        'window_days': 90,
        'reason': 'Medium confidence: data points (22) < 30'
    }


@pytest.fixture
def low_confidence_intrinsic() -> Dict[str, Any]:
    """
    Intrinsic value result with LOW confidence.
    """
    return {
        'low': 20.00,
        'median': 25.00,
        'high': 32.00,
        'confidence': 'LOW',
        'volatility': 0.40,
        'data_points': 12,
        'window_days': 90,
        'reason': 'Low confidence: volatility (40.0%) >= 35%'
    }


@pytest.fixture
def insufficient_data_intrinsic() -> Dict[str, Any]:
    """
    Intrinsic value result with INSUFFICIENT_DATA.
    """
    return {
        'low': None,
        'median': None,
        'high': None,
        'confidence': 'INSUFFICIENT_DATA',
        'volatility': 0.0,
        'data_points': 3,
        'window_days': 90,
        'reason': 'Insufficient data points: 3 < 10 required'
    }


@pytest.fixture
def velocity_data_fast() -> Dict[str, Any]:
    """
    Velocity data for a fast-selling product.
    """
    return {
        'monthly_sales': 75,
        'velocity_tier': 'HIGH',
        'current_bsr': 25000
    }


@pytest.fixture
def velocity_data_slow() -> Dict[str, Any]:
    """
    Velocity data for a slow-selling product.
    """
    return {
        'monthly_sales': 8,
        'velocity_tier': 'LOW',
        'current_bsr': 850000
    }


@pytest.fixture
def guidance_service() -> BuyingGuidanceService:
    """
    Create a BuyingGuidanceService instance.
    """
    return BuyingGuidanceService()


# =============================================================================
# TEST: calculate_max_buy_price
# =============================================================================

class TestCalculateMaxBuyPrice:
    """Test max buy price calculation formula."""

    def test_max_buy_price_with_50_percent_roi_target(self):
        """
        Formula: max_buy = sell_price * (1 - fee_pct) / (1 + target_roi)
        Example: $52 sell, 22% fees, 50% ROI target
        max_buy = 52 * (1 - 0.22) / (1 + 0.50) = 52 * 0.78 / 1.50 = 27.04
        """
        result = calculate_max_buy_price(
            sell_price=52.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Expected: 52 * 0.78 / 1.50 = 27.04
        assert result == pytest.approx(27.04, rel=0.01)

    def test_max_buy_price_with_100_percent_roi_target(self):
        """
        100% ROI target should halve the net after fees.
        Example: $100 sell, 15% fees, 100% ROI
        max_buy = 100 * 0.85 / 2.00 = 42.50
        """
        result = calculate_max_buy_price(
            sell_price=100.00,
            fee_pct=0.15,
            target_roi=1.00
        )

        assert result == pytest.approx(42.50, rel=0.01)

    def test_max_buy_price_with_zero_roi(self):
        """
        0% ROI means break-even: max_buy = sell * (1 - fees)
        """
        result = calculate_max_buy_price(
            sell_price=50.00,
            fee_pct=0.20,
            target_roi=0.0
        )

        # Expected: 50 * 0.80 / 1.00 = 40.00
        assert result == pytest.approx(40.00, rel=0.01)

    def test_max_buy_price_with_high_fees(self):
        """
        High fees (35%) should significantly reduce max buy price.
        """
        result = calculate_max_buy_price(
            sell_price=80.00,
            fee_pct=0.35,
            target_roi=0.50
        )

        # Expected: 80 * 0.65 / 1.50 = 34.67
        assert result == pytest.approx(34.67, rel=0.01)

    def test_max_buy_price_returns_zero_for_invalid_inputs(self):
        """
        Invalid inputs should return 0 or handle gracefully.
        """
        # Zero sell price
        assert calculate_max_buy_price(0, 0.22, 0.50) == 0.0

        # Negative sell price
        assert calculate_max_buy_price(-10, 0.22, 0.50) == 0.0

        # Negative ROI (invalid)
        assert calculate_max_buy_price(50, 0.22, -0.50) == 0.0


# =============================================================================
# TEST: BuyingGuidance dataclass
# =============================================================================

class TestBuyingGuidanceDataclass:
    """Test the BuyingGuidance dataclass structure."""

    def test_buying_guidance_has_all_required_fields(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        BuyingGuidance should have all required fields.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Check all required fields exist
        assert hasattr(result, 'max_buy_price')
        assert hasattr(result, 'target_sell_price')
        assert hasattr(result, 'estimated_profit')
        assert hasattr(result, 'estimated_roi_pct')
        assert hasattr(result, 'price_range')
        assert hasattr(result, 'estimated_days_to_sell')
        assert hasattr(result, 'recommendation')
        assert hasattr(result, 'recommendation_reason')
        assert hasattr(result, 'confidence_label')
        assert hasattr(result, 'explanations')

    def test_buying_guidance_is_dataclass(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        BuyingGuidance should be convertible to dict.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Should be convertible to dict
        as_dict = asdict(result)
        assert isinstance(as_dict, dict)
        assert 'max_buy_price' in as_dict


# =============================================================================
# TEST: French confidence labels
# =============================================================================

class TestFrenchConfidenceLabels:
    """Test that confidence labels are in French."""

    def test_high_confidence_returns_fiable(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        HIGH confidence should return 'Fiable'.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.confidence_label == "Fiable"

    def test_medium_confidence_returns_modere(self, guidance_service, medium_confidence_intrinsic, velocity_data_fast):
        """
        MEDIUM confidence should return 'Modere'.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=medium_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.confidence_label == "Modere"

    def test_low_confidence_returns_incertain(self, guidance_service, low_confidence_intrinsic, velocity_data_fast):
        """
        LOW confidence should return 'Incertain'.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=low_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.confidence_label == "Incertain"

    def test_insufficient_data_returns_donnees_insuffisantes(self, guidance_service, insufficient_data_intrinsic, velocity_data_fast):
        """
        INSUFFICIENT_DATA should return 'Donnees insuffisantes'.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=insufficient_data_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.confidence_label == "Donnees insuffisantes"


# =============================================================================
# TEST: Recommendation logic
# =============================================================================

class TestRecommendationLogic:
    """Test BUY/HOLD/SKIP recommendation logic."""

    def test_buy_recommendation_high_roi_high_confidence(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        ROI >= 100% + HIGH confidence should recommend BUY.
        """
        # Source price $20, sell price $52 with 22% fees
        # Net: 52 * 0.78 = 40.56, Profit: 40.56 - 20 = 20.56, ROI: 102.8%
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=20.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "BUY"
        assert result.estimated_roi_pct >= 100.0

    def test_buy_recommendation_50_roi_high_confidence(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        ROI >= 50% + HIGH confidence should recommend BUY.
        """
        # Source price $27, sell price $52 with 22% fees
        # Net: 40.56, Profit: 13.56, ROI: 50.2%
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=27.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "BUY"
        assert result.estimated_roi_pct >= 50.0

    def test_buy_recommendation_50_roi_medium_confidence(self, guidance_service, medium_confidence_intrinsic, velocity_data_fast):
        """
        ROI >= 50% + MEDIUM confidence should recommend BUY.
        """
        # Medium confidence, sell $35, source $15
        # Net: 35 * 0.78 = 27.30, Profit: 12.30, ROI: 82%
        result = guidance_service.calculate_guidance(
            intrinsic_result=medium_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "BUY"

    def test_hold_recommendation_30_to_50_roi(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        ROI 30-50% should recommend HOLD.
        """
        # Source price $31, sell price $52 with 22% fees
        # Net: 40.56, Profit: 9.56, ROI: 30.8%
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=31.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "HOLD"
        assert 30.0 <= result.estimated_roi_pct < 50.0

    def test_skip_recommendation_low_roi(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        ROI < 30% should recommend SKIP.
        """
        # Source price $35, sell price $52 with 22% fees
        # Net: 40.56, Profit: 5.56, ROI: 15.9%
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=35.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "SKIP"
        assert result.estimated_roi_pct < 30.0

    def test_skip_recommendation_insufficient_data(self, guidance_service, insufficient_data_intrinsic, velocity_data_fast):
        """
        INSUFFICIENT_DATA should always recommend SKIP.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=insufficient_data_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=10.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "SKIP"
        assert "insuffisantes" in result.recommendation_reason.lower() or "donnees" in result.recommendation_reason.lower()

    def test_skip_recommendation_negative_roi(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Negative ROI should recommend SKIP.
        """
        # Source price $50 > net sell price $40.56 = loss
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=50.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation == "SKIP"
        assert result.estimated_roi_pct < 0


# =============================================================================
# TEST: Price range formatting
# =============================================================================

class TestPriceRangeFormatting:
    """Test price range string formatting."""

    def test_price_range_format_with_valid_corridor(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Price range should be formatted as '$XX - $YY'.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Expected: "$45 - $58"
        assert result.price_range == "$45 - $58"

    def test_price_range_handles_none_values(self, guidance_service, insufficient_data_intrinsic, velocity_data_fast):
        """
        When corridor has None values, price_range should handle gracefully.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=insufficient_data_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Should be "N/A" or similar
        assert result.price_range in ("N/A", "Non disponible", "-")


# =============================================================================
# TEST: Days to sell estimation
# =============================================================================

class TestDaysToSellEstimation:
    """Test estimated days to sell calculation."""

    def test_fast_selling_product_low_days(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Fast-selling product (75 sales/month) should have low days to sell.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # 75 sales/month = ~2.5 sales/day = ~0.4 days per sale
        # Expected: 1-5 days
        assert result.estimated_days_to_sell <= 5

    def test_slow_selling_product_high_days(self, guidance_service, high_confidence_intrinsic, velocity_data_slow):
        """
        Slow-selling product (8 sales/month) should have higher days to sell.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_slow,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # 8 sales/month = ~0.27 sales/day = ~4 days per sale
        # Expected: 3-7 days
        assert result.estimated_days_to_sell >= 3

    def test_zero_sales_returns_max_days(self, guidance_service, high_confidence_intrinsic):
        """
        Zero monthly sales should return a high/max days estimate.
        """
        velocity_data = {
            'monthly_sales': 0,
            'velocity_tier': 'DEAD',
            'current_bsr': 2000000
        }

        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Should be a high number (30+ days or 90 days or 999)
        assert result.estimated_days_to_sell >= 30


# =============================================================================
# TEST: Explanations for tooltips
# =============================================================================

class TestExplanationsForTooltips:
    """Test that explanations dict contains all required fields."""

    def test_explanations_contains_max_buy_price(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Explanations should include max_buy_price explanation.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert 'max_buy_price' in result.explanations
        assert "50%" in result.explanations['max_buy_price'] or "ROI" in result.explanations['max_buy_price']

    def test_explanations_contains_target_sell_price(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Explanations should include target_sell_price explanation.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert 'target_sell_price' in result.explanations
        assert "median" in result.explanations['target_sell_price'].lower() or "90" in result.explanations['target_sell_price']

    def test_explanations_contains_price_range(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Explanations should include price_range explanation.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert 'price_range' in result.explanations

    def test_explanations_contains_days_to_sell(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Explanations should include estimated_days_to_sell explanation.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert 'estimated_days_to_sell' in result.explanations

    def test_explanations_in_french(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Explanations should be in French (no emojis).
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Check for French words in explanations
        all_text = " ".join(result.explanations.values())

        # Should contain French words like "Prix", "apres", "frais", etc.
        french_indicators = ["prix", "apres", "frais", "median", "vente", "jour"]
        has_french = any(word in all_text.lower() for word in french_indicators)
        assert has_french, f"Explanations should be in French: {all_text}"


# =============================================================================
# TEST: Edge cases and robustness
# =============================================================================

class TestEdgeCasesAndRobustness:
    """Test edge cases and error handling."""

    def test_handles_zero_fee_percentage(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Zero fees should work correctly.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.0,
            target_roi=0.50
        )

        # With 0% fees, max_buy = 52 / 1.50 = 34.67
        assert result.max_buy_price == pytest.approx(34.67, rel=0.01)

    def test_handles_high_fee_percentage(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        High fees (40%) should still work.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.40,
            target_roi=0.50
        )

        # With 40% fees, max_buy = 52 * 0.60 / 1.50 = 20.80
        assert result.max_buy_price == pytest.approx(20.80, rel=0.01)

    def test_handles_missing_velocity_data_fields(self, guidance_service, high_confidence_intrinsic):
        """
        Missing velocity data fields should not crash.
        """
        incomplete_velocity = {}  # Empty dict

        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=incomplete_velocity,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Should return valid result with default days estimate
        assert result.estimated_days_to_sell > 0

    def test_recommendation_reason_is_not_empty(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Recommendation reason should never be empty.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=15.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.recommendation_reason
        assert len(result.recommendation_reason) > 10

    def test_profit_calculation_accuracy(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Estimated profit should be calculated correctly.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=20.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Net from $52 with 22% fees = 52 * 0.78 = 40.56
        # Profit = 40.56 - 20 = 20.56
        assert result.estimated_profit == pytest.approx(20.56, rel=0.01)

    def test_roi_calculation_accuracy(self, guidance_service, high_confidence_intrinsic, velocity_data_fast):
        """
        Estimated ROI should be calculated correctly.
        """
        result = guidance_service.calculate_guidance(
            intrinsic_result=high_confidence_intrinsic,
            velocity_data=velocity_data_fast,
            source_price=20.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Profit = 20.56, ROI = (20.56 / 20) * 100 = 102.8%
        assert result.estimated_roi_pct == pytest.approx(102.8, rel=0.01)


# =============================================================================
# TEST: Integration with intrinsic value service output
# =============================================================================

class TestIntegrationWithIntrinsicValue:
    """Test integration with real intrinsic value service output format."""

    def test_works_with_standard_intrinsic_output(self, guidance_service, velocity_data_fast):
        """
        Should work with standard output from calculate_intrinsic_value_corridor.
        """
        # Simulate real output from intrinsic_value_service
        intrinsic_output = {
            'low': 28.50,
            'median': 34.99,
            'high': 42.00,
            'confidence': 'HIGH',
            'volatility': 0.1523,
            'data_points': 67,
            'window_days': 90,
            'reason': 'High confidence: 67 data points with 15.2% volatility'
        }

        result = guidance_service.calculate_guidance(
            intrinsic_result=intrinsic_output,
            velocity_data=velocity_data_fast,
            source_price=18.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        # Verify reasonable outputs
        assert result.target_sell_price == 34.99
        assert result.price_range == "$29 - $42" or result.price_range == "$28 - $42"
        assert result.confidence_label == "Fiable"
        assert result.recommendation in ("BUY", "HOLD", "SKIP")

    def test_target_sell_price_uses_median(self, guidance_service, velocity_data_fast):
        """
        target_sell_price should always be the median from intrinsic corridor.
        """
        intrinsic = {
            'low': 10.00,
            'median': 15.55,
            'high': 20.00,
            'confidence': 'MEDIUM',
            'volatility': 0.25,
            'data_points': 25,
            'window_days': 90,
            'reason': 'Medium confidence'
        }

        result = guidance_service.calculate_guidance(
            intrinsic_result=intrinsic,
            velocity_data=velocity_data_fast,
            source_price=5.00,
            fee_pct=0.22,
            target_roi=0.50
        )

        assert result.target_sell_price == 15.55
