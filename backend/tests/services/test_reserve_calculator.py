"""
Unit tests for Reserve Calculator Service.

TDD: These tests are written FIRST before implementation.
Tests the income smoothing reserve calculation for the Textbook Pivot.
"""
import pytest
from dataclasses import dataclass
from typing import Dict, List

# Import will fail until service is implemented - expected for TDD
from app.services.reserve_calculator_service import (
    ReserveRecommendation,
    calculate_smoothing_reserve,
    project_annual_income,
    get_capital_growth_projection,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def typical_textbook_scenario() -> Dict:
    """
    Typical textbook arbitrage scenario:
    - Peak months (Aug-Oct): ~$4500/month
    - Trough months (May-Jul): ~$800/month
    - Target income: $2000/month
    """
    return {
        "target_monthly_income": 2000.0,
        "avg_peak_monthly": 4500.0,
        "avg_trough_monthly": 800.0,
        "trough_months": 5,
        "safety_margin": 0.15,
    }


@pytest.fixture
def monthly_projections_seasonal() -> Dict[int, float]:
    """
    Monthly projections with strong seasonality.
    Peak: Aug-Oct (back to school)
    Trough: May-Jul (summer)
    """
    return {
        1: 2500.0,   # January - moderate
        2: 2200.0,   # February - moderate
        3: 1800.0,   # March - slowing
        4: 1200.0,   # April - low
        5: 800.0,    # May - trough
        6: 600.0,    # June - trough
        7: 700.0,    # July - trough
        8: 5000.0,   # August - PEAK (back to school)
        9: 4500.0,   # September - PEAK
        10: 4000.0,  # October - PEAK
        11: 3000.0,  # November - moderate
        12: 2800.0,  # December - moderate (holiday)
    }


@pytest.fixture
def zero_trough_scenario() -> Dict:
    """
    Edge case: zero income during trough months.
    """
    return {
        "target_monthly_income": 2000.0,
        "avg_peak_monthly": 5000.0,
        "avg_trough_monthly": 0.0,
        "trough_months": 5,
        "safety_margin": 0.15,
    }


# =============================================================================
# TEST: calculate_smoothing_reserve
# =============================================================================

class TestCalculateSmoothingReserve:
    """Test reserve calculation for income smoothing."""

    def test_calculate_reserve_for_target_income(self, typical_textbook_scenario):
        """
        Test reserve calculation with typical textbook scenario.

        Given:
        - Target income: $2000/month
        - Peak income: $4500/month
        - Trough income: $800/month
        - Trough months: 5
        - Safety margin: 15%

        Expected:
        - Monthly gap = $2000 - $800 = $1200
        - Base reserve = $1200 * 5 = $6000
        - With margin = $6000 * 1.15 = $6900
        - Monthly contribution = ($4500 - $2000) * 0.25 = $625
        - Months to build = $6900 / $625 = 11.04 -> 12 months
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=typical_textbook_scenario["target_monthly_income"],
            avg_peak_monthly=typical_textbook_scenario["avg_peak_monthly"],
            avg_trough_monthly=typical_textbook_scenario["avg_trough_monthly"],
            trough_months=typical_textbook_scenario["trough_months"],
            safety_margin=typical_textbook_scenario["safety_margin"],
        )

        # Verify return type
        assert isinstance(result, ReserveRecommendation)

        # Verify structure
        assert hasattr(result, 'recommended_reserve')
        assert hasattr(result, 'monthly_contribution')
        assert hasattr(result, 'months_to_build')
        assert hasattr(result, 'coverage_months')
        assert hasattr(result, 'target_monthly_income')
        assert hasattr(result, 'safety_margin_pct')

        # Verify calculations
        # Monthly gap = $2000 - $800 = $1200
        # Base reserve = $1200 * 5 = $6000
        # With margin = $6000 * 1.15 = $6900
        assert result.recommended_reserve == pytest.approx(6900.0, rel=0.01)

        # Monthly contribution = ($4500 - $2000) * 0.25 = $625
        assert result.monthly_contribution == pytest.approx(625.0, rel=0.01)

        # Months to build = ceiling($6900 / $625) = ceiling(11.04) = 12
        assert result.months_to_build == 12

        # Coverage months should match input
        assert result.coverage_months == 5

        # Target income should match input
        assert result.target_monthly_income == 2000.0

        # Safety margin percentage should match input
        assert result.safety_margin_pct == pytest.approx(0.15, rel=0.01)

    def test_zero_trough_income_handled(self, zero_trough_scenario):
        """
        Test handling of zero trough income.

        Given:
        - Target income: $2000/month
        - Trough income: $0/month
        - This means full gap = target income
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=zero_trough_scenario["target_monthly_income"],
            avg_peak_monthly=zero_trough_scenario["avg_peak_monthly"],
            avg_trough_monthly=zero_trough_scenario["avg_trough_monthly"],
            trough_months=zero_trough_scenario["trough_months"],
            safety_margin=zero_trough_scenario["safety_margin"],
        )

        # Monthly gap = $2000 - $0 = $2000
        # Base reserve = $2000 * 5 = $10000
        # With margin = $10000 * 1.15 = $11500
        assert result.recommended_reserve == pytest.approx(11500.0, rel=0.01)

        # Monthly contribution = ($5000 - $2000) * 0.25 = $750
        assert result.monthly_contribution == pytest.approx(750.0, rel=0.01)

        # Months to build = ceiling($11500 / $750) = ceiling(15.33) = 16
        assert result.months_to_build == 16

    def test_no_reserve_needed_when_trough_exceeds_target(self):
        """
        No reserve needed when trough income exceeds target.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=1000.0,
            avg_peak_monthly=3000.0,
            avg_trough_monthly=1500.0,  # Trough > target
            trough_months=5,
            safety_margin=0.15,
        )

        # Monthly gap = max(0, $1000 - $1500) = $0
        # No reserve needed
        assert result.recommended_reserve == 0.0
        assert result.monthly_contribution >= 0.0
        assert result.months_to_build == 0

    def test_different_safety_margins(self):
        """
        Test different safety margin values.
        """
        base_params = {
            "target_monthly_income": 2000.0,
            "avg_peak_monthly": 4000.0,
            "avg_trough_monthly": 1000.0,
            "trough_months": 5,
        }

        result_10pct = calculate_smoothing_reserve(**base_params, safety_margin=0.10)
        result_20pct = calculate_smoothing_reserve(**base_params, safety_margin=0.20)
        result_30pct = calculate_smoothing_reserve(**base_params, safety_margin=0.30)

        # Higher margin = higher reserve
        assert result_10pct.recommended_reserve < result_20pct.recommended_reserve
        assert result_20pct.recommended_reserve < result_30pct.recommended_reserve

        # Base reserve = ($2000 - $1000) * 5 = $5000
        assert result_10pct.recommended_reserve == pytest.approx(5500.0, rel=0.01)
        assert result_20pct.recommended_reserve == pytest.approx(6000.0, rel=0.01)
        assert result_30pct.recommended_reserve == pytest.approx(6500.0, rel=0.01)

    def test_zero_safety_margin(self):
        """
        Test with zero safety margin.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=2000.0,
            avg_peak_monthly=4000.0,
            avg_trough_monthly=1000.0,
            trough_months=5,
            safety_margin=0.0,
        )

        # Base reserve = ($2000 - $1000) * 5 = $5000
        # No margin = $5000
        assert result.recommended_reserve == pytest.approx(5000.0, rel=0.01)
        assert result.safety_margin_pct == 0.0

    def test_different_trough_months(self):
        """
        Test different trough month durations.
        """
        base_params = {
            "target_monthly_income": 2000.0,
            "avg_peak_monthly": 4000.0,
            "avg_trough_monthly": 1000.0,
            "safety_margin": 0.15,
        }

        result_3mo = calculate_smoothing_reserve(**base_params, trough_months=3)
        result_5mo = calculate_smoothing_reserve(**base_params, trough_months=5)
        result_6mo = calculate_smoothing_reserve(**base_params, trough_months=6)

        # More trough months = higher reserve needed
        assert result_3mo.recommended_reserve < result_5mo.recommended_reserve
        assert result_5mo.recommended_reserve < result_6mo.recommended_reserve

        # Verify coverage months
        assert result_3mo.coverage_months == 3
        assert result_5mo.coverage_months == 5
        assert result_6mo.coverage_months == 6


class TestCalculateSmoothingReserveEdgeCases:
    """Test edge cases for reserve calculation."""

    def test_equal_peak_and_trough(self):
        """
        When peak equals trough, no surplus to contribute.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=2000.0,
            avg_peak_monthly=2000.0,  # Equal to trough
            avg_trough_monthly=2000.0,
            trough_months=5,
            safety_margin=0.15,
        )

        # Gap = $2000 - $2000 = $0
        assert result.recommended_reserve == 0.0

        # No surplus = contribution = ($2000 - $2000) * 0.25 = $0
        assert result.monthly_contribution == 0.0

    def test_peak_below_target(self):
        """
        When even peak is below target, contribution is zero.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=5000.0,
            avg_peak_monthly=3000.0,  # Below target
            avg_trough_monthly=1000.0,
            trough_months=5,
            safety_margin=0.15,
        )

        # Gap = $5000 - $1000 = $4000
        # Reserve needed = $4000 * 5 * 1.15 = $23000
        assert result.recommended_reserve > 0

        # Contribution = max(0, ($3000 - $5000)) * 0.25 = $0
        # No surplus during peak
        assert result.monthly_contribution == 0.0

        # If contribution is 0, months_to_build should be infinity or special value
        # We'll use -1 to indicate "cannot build from surplus alone"
        assert result.months_to_build == -1

    def test_very_small_values(self):
        """
        Test with very small monetary values.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=10.0,
            avg_peak_monthly=20.0,
            avg_trough_monthly=5.0,
            trough_months=3,
            safety_margin=0.15,
        )

        # Gap = $10 - $5 = $5
        # Reserve = $5 * 3 * 1.15 = $17.25
        assert result.recommended_reserve == pytest.approx(17.25, rel=0.01)

    def test_large_values(self):
        """
        Test with large monetary values.
        """
        result = calculate_smoothing_reserve(
            target_monthly_income=50000.0,
            avg_peak_monthly=100000.0,
            avg_trough_monthly=20000.0,
            trough_months=5,
            safety_margin=0.15,
        )

        # Gap = $50000 - $20000 = $30000
        # Reserve = $30000 * 5 * 1.15 = $172500
        assert result.recommended_reserve == pytest.approx(172500.0, rel=0.01)

        # Contribution = ($100000 - $50000) * 0.25 = $12500
        assert result.monthly_contribution == pytest.approx(12500.0, rel=0.01)


# =============================================================================
# TEST: project_annual_income
# =============================================================================

class TestProjectAnnualIncome:
    """Test annual income projection with seasonality."""

    def test_project_annual_income_with_seasonality(self, monthly_projections_seasonal):
        """
        Test annual projection with strong seasonality.
        """
        result = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=25,
        )

        # Verify structure
        assert 'annual_gross' in result
        assert 'annual_net' in result
        assert 'peak_months' in result
        assert 'trough_months' in result
        assert 'avg_peak' in result
        assert 'avg_trough' in result
        assert 'reserve_contribution' in result
        assert 'smoothed_monthly' in result

        # Verify annual gross
        expected_gross = sum(monthly_projections_seasonal.values())
        assert result['annual_gross'] == pytest.approx(expected_gross, rel=0.01)

        # Peak months should be August, September, October, November (top 4)
        assert 8 in result['peak_months']
        assert 9 in result['peak_months']
        assert 10 in result['peak_months']

        # Trough months should include June (lowest)
        assert 6 in result['trough_months']

        # Avg peak should be around $4125 (Aug, Sep, Oct, Nov average)
        assert result['avg_peak'] > 3000.0

        # Avg trough should be around $820 (5 lowest)
        assert result['avg_trough'] < 1500.0

    def test_reserve_contribution_calculation(self, monthly_projections_seasonal):
        """
        Test reserve contribution from peak months.
        """
        result_25pct = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=25,
        )
        result_50pct = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=50,
        )

        # Higher reserve percentage = higher contribution
        assert result_50pct['reserve_contribution'] > result_25pct['reserve_contribution']

        # Reserve contribution should be peak_profits * reserve_pct
        # Peak profits = sum of top 4 months
        peak_total = 5000.0 + 4500.0 + 4000.0 + 3000.0  # $16500
        expected_25pct = peak_total * 0.25  # $4125
        assert result_25pct['reserve_contribution'] == pytest.approx(expected_25pct, rel=0.05)

    def test_smoothed_monthly_calculation(self, monthly_projections_seasonal):
        """
        Test smoothed monthly income value.
        """
        result = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=25,
        )

        # Smoothed monthly = annual_net / 12
        expected_smoothed = result['annual_net'] / 12
        assert result['smoothed_monthly'] == pytest.approx(expected_smoothed, rel=0.01)

    def test_empty_projections(self):
        """
        Test handling of empty projections.
        """
        result = project_annual_income(
            monthly_projections={},
            reserve_percentage=25,
        )

        assert result['annual_gross'] == 0.0
        assert result['annual_net'] == 0.0
        assert result['peak_months'] == []
        assert result['trough_months'] == []

    def test_partial_year_projections(self):
        """
        Test with fewer than 12 months.
        """
        partial_projections = {
            1: 2000.0,
            2: 2500.0,
            3: 1800.0,
        }

        result = project_annual_income(
            monthly_projections=partial_projections,
            reserve_percentage=25,
        )

        expected_gross = 2000.0 + 2500.0 + 1800.0
        assert result['annual_gross'] == pytest.approx(expected_gross, rel=0.01)

    def test_uniform_projections(self):
        """
        Test with uniform monthly projections (no seasonality).
        """
        uniform = {i: 2000.0 for i in range(1, 13)}

        result = project_annual_income(
            monthly_projections=uniform,
            reserve_percentage=25,
        )

        # All months are "peak" and "trough"
        assert result['annual_gross'] == 24000.0
        assert result['avg_peak'] == result['avg_trough']

    def test_zero_reserve_percentage(self, monthly_projections_seasonal):
        """
        Test with zero reserve percentage.
        """
        result = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=0,
        )

        # No reserve contribution
        assert result['reserve_contribution'] == 0.0
        assert result['annual_net'] == result['annual_gross']


# =============================================================================
# TEST: get_capital_growth_projection
# =============================================================================

class TestCapitalGrowthProjection:
    """Test capital growth projection over time."""

    def test_basic_capital_growth(self):
        """
        Test basic capital growth with default parameters.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=12,
        )

        # Should return list of 12 monthly projections
        assert len(result) == 12

        # Each month should have required fields
        for month_data in result:
            assert 'month' in month_data
            assert 'starting_capital' in month_data
            assert 'gross_profit' in month_data
            assert 'net_profit' in month_data
            assert 'reinvested' in month_data
            assert 'pocket' in month_data
            assert 'ending_capital' in month_data

        # First month
        month_1 = result[0]
        assert month_1['month'] == 1
        assert month_1['starting_capital'] == 1000.0

        # Gross profit = $1000 * 50% = $500
        assert month_1['gross_profit'] == pytest.approx(500.0, rel=0.01)

        # Net profit = $500 * 90% = $450 (10% for fees/costs)
        assert month_1['net_profit'] == pytest.approx(450.0, rel=0.01)

        # Reinvested = $450 * 75% = $337.50
        assert month_1['reinvested'] == pytest.approx(337.50, rel=0.01)

        # Pocket = $450 * 25% = $112.50
        assert month_1['pocket'] == pytest.approx(112.50, rel=0.01)

        # Ending capital = $1000 + $337.50 = $1337.50
        assert month_1['ending_capital'] == pytest.approx(1337.50, rel=0.01)

    def test_compound_growth_over_12_months(self):
        """
        Test compound growth compounds correctly over time.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=12,
        )

        # Capital should grow each month
        for i in range(1, len(result)):
            assert result[i]['starting_capital'] > result[i-1]['starting_capital']
            assert result[i]['ending_capital'] > result[i-1]['ending_capital']

        # Month 2 starting capital should equal Month 1 ending capital
        assert result[1]['starting_capital'] == pytest.approx(
            result[0]['ending_capital'], rel=0.01
        )

        # Final capital should be significantly higher than initial
        final_capital = result[-1]['ending_capital']
        assert final_capital > 1000.0 * 5  # Should at least 5x with 50% ROI

    def test_zero_reinvestment_rate(self):
        """
        Test with zero reinvestment (all profit pocketed).
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=0,
            months=6,
        )

        # Capital should stay constant
        for month_data in result:
            assert month_data['starting_capital'] == 1000.0
            assert month_data['ending_capital'] == 1000.0
            assert month_data['reinvested'] == 0.0
            assert month_data['pocket'] == month_data['net_profit']

    def test_full_reinvestment_rate(self):
        """
        Test with 100% reinvestment (no profit pocketed).
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=100,
            months=6,
        )

        for month_data in result:
            assert month_data['pocket'] == 0.0
            assert month_data['reinvested'] == month_data['net_profit']

        # Growth should be maximum
        assert result[-1]['ending_capital'] > 5000.0  # Strong growth

    def test_different_roi_percentages(self):
        """
        Test different ROI percentages.
        """
        result_25 = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=25,
            reinvestment_rate=75,
            months=12,
        )
        result_50 = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=12,
        )
        result_75 = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=75,
            reinvestment_rate=75,
            months=12,
        )

        # Higher ROI = higher final capital
        assert result_25[-1]['ending_capital'] < result_50[-1]['ending_capital']
        assert result_50[-1]['ending_capital'] < result_75[-1]['ending_capital']

    def test_single_month_projection(self):
        """
        Test projection for single month.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=1,
        )

        assert len(result) == 1
        assert result[0]['month'] == 1

    def test_zero_months_returns_empty(self):
        """
        Test zero months returns empty list.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=0,
        )

        assert result == []

    def test_zero_initial_capital(self):
        """
        Test with zero initial capital.
        """
        result = get_capital_growth_projection(
            initial_capital=0.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=6,
        )

        # All values should be zero
        for month_data in result:
            assert month_data['starting_capital'] == 0.0
            assert month_data['gross_profit'] == 0.0
            assert month_data['ending_capital'] == 0.0

    def test_large_initial_capital(self):
        """
        Test with large initial capital.
        """
        result = get_capital_growth_projection(
            initial_capital=100000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=6,
        )

        # First month gross profit = $100000 * 50% = $50000
        assert result[0]['gross_profit'] == pytest.approx(50000.0, rel=0.01)

    def test_cumulative_pocket_money(self):
        """
        Test that pocket money accumulates correctly.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=12,
        )

        total_pocket = sum(m['pocket'] for m in result)

        # Should have meaningful pocket money over 12 months
        assert total_pocket > 1000.0  # More than initial capital


class TestCapitalGrowthProjectionEdgeCases:
    """Test edge cases for capital growth projection."""

    def test_negative_roi_handled(self):
        """
        Test handling of negative ROI (losing money).
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=-10,  # Losing 10% per month
            reinvestment_rate=75,
            months=6,
        )

        # Capital should decrease
        assert result[-1]['ending_capital'] < 1000.0

    def test_very_high_roi(self):
        """
        Test with very high ROI percentage.
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=200,  # 200% ROI
            reinvestment_rate=75,
            months=6,
        )

        # Should grow very fast
        assert result[-1]['ending_capital'] > 50000.0

    def test_net_profit_formula(self):
        """
        Verify net profit is 90% of gross profit (10% for fees).
        """
        result = get_capital_growth_projection(
            initial_capital=1000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=1,
        )

        gross = result[0]['gross_profit']
        net = result[0]['net_profit']

        # Net should be 90% of gross
        assert net == pytest.approx(gross * 0.90, rel=0.01)


# =============================================================================
# TEST: Integration scenarios
# =============================================================================

class TestReserveCalculatorIntegration:
    """Test integration between reserve calculator functions."""

    def test_reserve_matches_projection(
        self, monthly_projections_seasonal
    ):
        """
        Reserve calculation should align with annual projection.
        """
        # Get annual projection
        annual = project_annual_income(
            monthly_projections=monthly_projections_seasonal,
            reserve_percentage=25,
        )

        # Calculate reserve based on projection
        reserve = calculate_smoothing_reserve(
            target_monthly_income=annual['smoothed_monthly'],
            avg_peak_monthly=annual['avg_peak'],
            avg_trough_monthly=annual['avg_trough'],
            trough_months=5,
            safety_margin=0.15,
        )

        # Reserve should cover the gap during trough months
        assert reserve.recommended_reserve >= 0

        # If trough is below target, reserve should be positive
        if annual['avg_trough'] < annual['smoothed_monthly']:
            assert reserve.recommended_reserve > 0

    def test_growth_projection_informs_reserve_timeline(self):
        """
        Capital growth affects time to build reserve.
        """
        # Get growth projection
        growth = get_capital_growth_projection(
            initial_capital=5000.0,
            monthly_roi_pct=50,
            reinvestment_rate=75,
            months=12,
        )

        # Total pocket money over 12 months
        total_pocket = sum(m['pocket'] for m in growth)

        # Calculate reserve needed
        reserve = calculate_smoothing_reserve(
            target_monthly_income=2000.0,
            avg_peak_monthly=4500.0,
            avg_trough_monthly=800.0,
            trough_months=5,
            safety_margin=0.15,
        )

        # Pocket money should eventually cover reserve
        # (This is a business validation, not just math)
        assert total_pocket > 0
        assert reserve.recommended_reserve > 0
