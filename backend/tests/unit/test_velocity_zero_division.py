"""
RED-GREEN Test: Velocity Calculations Zero Division Bug
=======================================================
Tests for ZeroDivisionError in _calculate_offers_volatility.

BUG: Line 211 in velocity_calculations.py
    price_volatility = statistics.stdev(prices) / statistics.mean(prices) * 100
    When mean(prices) == 0, this causes ZeroDivisionError.
"""

import pytest
from datetime import datetime, timedelta

from app.core.velocity_calculations import (
    _calculate_offers_volatility,
    calculate_velocity_score,
    VelocityData
)


class TestZeroDivisionBug:
    """RED tests - These expose the bug."""

    def test_zero_prices_should_not_crash(self):
        """When all prices are 0.0, should return 0 volatility, not crash."""
        now = datetime.now()
        # Price history with all zeros
        price_history = [
            (now - timedelta(hours=2), 0.0),
            (now - timedelta(hours=1), 0.0),
            (now, 0.0)
        ]
        offers_history = []

        # This should NOT raise ZeroDivisionError
        result = _calculate_offers_volatility(offers_history, price_history)

        # Should return 0 volatility for zero prices
        assert result == 0.0

    def test_single_zero_price_with_others(self):
        """Mix of zero and non-zero prices should work."""
        now = datetime.now()
        price_history = [
            (now - timedelta(hours=2), 0.0),
            (now - timedelta(hours=1), 10.0),
            (now, 20.0)
        ]
        offers_history = []

        result = _calculate_offers_volatility(offers_history, price_history)

        # Should calculate volatility based on mean of [0.0, 10.0, 20.0] = 10.0
        assert result >= 0  # Should not crash

    def test_empty_price_history(self):
        """Empty price history should return 0."""
        result = _calculate_offers_volatility([], [])
        assert result == 0.0

    def test_single_price_point(self):
        """Single price point should return 0 (no stdev possible)."""
        now = datetime.now()
        price_history = [(now, 10.0)]
        result = _calculate_offers_volatility([], price_history)
        assert result == 0.0


class TestVelocityScoreWithEdgeCases:
    """Integration tests with VelocityData edge cases."""

    def test_velocity_score_with_zero_prices(self):
        """Full velocity calculation with zero prices should not crash."""
        now = datetime.now()

        velocity_data = VelocityData(
            current_bsr=1000,
            bsr_history=[(now - timedelta(days=1), 1200), (now, 1000)],
            price_history=[(now - timedelta(days=1), 0.0), (now, 0.0)],
            buybox_history=[(now, True)],
            offers_history=[(now, 5)],
            category="books"
        )

        # Should not crash
        result = calculate_velocity_score(velocity_data)

        assert "velocity_score" in result
        assert result["velocity_score"] >= 0
        assert result["velocity_score"] <= 100

    def test_velocity_score_with_all_none_values(self):
        """Velocity calculation with None values should handle gracefully."""
        now = datetime.now()

        velocity_data = VelocityData(
            current_bsr=None,
            bsr_history=[],
            price_history=[(now, None), (now - timedelta(hours=1), None)],
            buybox_history=[],
            offers_history=[],
            category="books"
        )

        # Should not crash
        result = calculate_velocity_score(velocity_data)

        assert "velocity_score" in result
        # Score should be 0 or minimal with no valid data
        assert result["velocity_score"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
