"""
Tests for slow velocity risk calculation - Phase 8 Refactor

This replaces the old detect_dead_inventory tests.
The new system uses real Keepa salesDrops data instead of arbitrary BSR thresholds.

Based on real data analysis:
- BSR 200K = 15+ sales/month (NOT dead inventory)
- BSR 350K = 7+ sales/month (still sells regularly)
- Only 0-4 sales/month is truly "DEAD"
"""
import pytest
from app.api.v1.endpoints.analytics import _calculate_slow_velocity_risk


class TestSlowVelocityRiskWithRealData:
    """Test _calculate_slow_velocity_risk with Keepa salesDrops data."""

    def test_high_sales_drops_low_risk(self):
        """50+ sales drops with low BSR = HIGH tier = very low risk.

        Note: SalesVelocityService applies BSR-based adjustments to the
        final estimate. A book with 60 salesDrops and BSR 20K will get
        HIGH tier (50-99 sales/month range).
        """
        result = _calculate_slow_velocity_risk(
            sales_drops_30=60,
            bsr=20000,
            category='books'
        )
        assert result['velocity_tier'] in ['PREMIUM', 'HIGH']
        assert result['monthly_sales_estimate'] >= 50
        assert result['risk_score'] <= 20
        assert result['data_source'] == 'KEEPA_REAL'

    def test_medium_sales_drops_moderate_risk(self):
        """20-30 sales drops = MEDIUM tier = moderate risk."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=25,
            bsr=100000,
            category='books'
        )
        assert result['velocity_tier'] in ['MEDIUM', 'HIGH']
        assert result['monthly_sales_estimate'] >= 20
        assert result['risk_score'] <= 40
        assert result['data_source'] == 'KEEPA_REAL'

    def test_low_sales_drops_higher_risk(self):
        """5-10 sales drops = LOW tier = higher risk."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=8,
            bsr=200000,
            category='books'
        )
        assert result['velocity_tier'] in ['LOW', 'MEDIUM']
        assert result['risk_score'] >= 35
        assert result['data_source'] == 'KEEPA_REAL'

    def test_zero_sales_drops_dead(self):
        """0 sales drops = DEAD tier = very high risk."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=0,
            bsr=500000,
            category='books'
        )
        assert result['velocity_tier'] == 'DEAD'
        assert result['monthly_sales_estimate'] == 0
        assert result['risk_score'] >= 80
        assert result['data_source'] == 'KEEPA_REAL'


class TestSlowVelocityRiskWithBSRFallback:
    """Test fallback estimation when salesDrops not available."""

    def test_low_bsr_estimated_as_fast(self):
        """BSR < 50K without salesDrops should estimate HIGH velocity."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=None,
            bsr=30000,
            category='books'
        )
        assert result['velocity_tier'] == 'HIGH'
        assert result['monthly_sales_estimate'] == 50
        assert result['data_source'] == 'ESTIMATED_FROM_BSR'

    def test_medium_bsr_estimated_as_medium(self):
        """BSR 50K-150K without salesDrops should estimate MEDIUM velocity."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=None,
            bsr=100000,
            category='books'
        )
        assert result['velocity_tier'] == 'MEDIUM'
        assert result['monthly_sales_estimate'] == 25
        assert result['data_source'] == 'ESTIMATED_FROM_BSR'

    def test_high_bsr_estimated_as_low(self):
        """BSR 150K-350K without salesDrops should estimate LOW velocity."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=None,
            bsr=250000,
            category='books'
        )
        assert result['velocity_tier'] == 'LOW'
        assert result['monthly_sales_estimate'] == 10
        assert result['data_source'] == 'ESTIMATED_FROM_BSR'

    def test_very_high_bsr_estimated_as_dead(self):
        """BSR > 500K without salesDrops should estimate DEAD velocity."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=None,
            bsr=600000,
            category='books'
        )
        assert result['velocity_tier'] == 'DEAD'
        assert result['monthly_sales_estimate'] == 1
        assert result['data_source'] == 'ESTIMATED_FROM_BSR'


class TestSlowVelocityRiskEdgeCases:
    """Test edge cases and hostile inputs."""

    def test_no_data_returns_unknown(self):
        """No BSR and no salesDrops should return UNKNOWN."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=None,
            bsr=None,
            category='books'
        )
        assert result['velocity_tier'] == 'UNKNOWN'
        assert result['monthly_sales_estimate'] == 0
        assert result['data_source'] == 'NO_DATA'
        assert result['risk_score'] == 50  # Default moderate

    def test_unknown_category_no_crash(self):
        """Unknown category should not crash."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=20,
            bsr=100000,
            category='weird_unknown_category'
        )
        assert result['velocity_tier'] in ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'DEAD']
        assert result['data_source'] == 'KEEPA_REAL'

    def test_salesdrops_overrides_bsr_estimation(self):
        """Real salesDrops should override BSR-based estimation.

        A product with low BSR (looks fast) but low salesDrops (actually slow)
        should be rated based on the real data.
        """
        # Low BSR (looks fast) but only 2 sales (actually very slow)
        result = _calculate_slow_velocity_risk(
            sales_drops_30=2,
            bsr=30000,  # Low BSR would normally mean HIGH velocity
            category='books'
        )
        # Real data shows DEAD, not the HIGH that BSR would suggest
        assert result['velocity_tier'] == 'DEAD'
        assert result['risk_score'] >= 80
        assert result['data_source'] == 'KEEPA_REAL'


class TestSlowVelocityRiskMapping:
    """Test velocity tier to risk score mapping."""

    def test_premium_tier_risk_score(self):
        """PREMIUM tier should have risk_score = 5."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=150,
            bsr=5000,
            category='books'
        )
        assert result['velocity_tier'] == 'PREMIUM'
        assert result['risk_score'] == 5

    def test_high_tier_risk_score(self):
        """HIGH tier should have risk_score = 15."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=60,
            bsr=20000,
            category='books'
        )
        assert result['velocity_tier'] == 'HIGH'
        assert result['risk_score'] == 15

    def test_medium_tier_risk_score(self):
        """MEDIUM tier should have risk_score = 35."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=30,
            bsr=80000,
            category='books'
        )
        assert result['velocity_tier'] == 'MEDIUM'
        assert result['risk_score'] == 35

    def test_low_tier_risk_score(self):
        """LOW tier should have risk_score = 60."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=10,
            bsr=150000,
            category='books'
        )
        assert result['velocity_tier'] == 'LOW'
        assert result['risk_score'] == 60

    def test_dead_tier_risk_score(self):
        """DEAD tier should have risk_score = 90."""
        result = _calculate_slow_velocity_risk(
            sales_drops_30=2,
            bsr=400000,
            category='books'
        )
        assert result['velocity_tier'] == 'DEAD'
        assert result['risk_score'] == 90
