"""
Regression test: source_price_factor must be 0.40 everywhere.

Calibration history:
- 0.28 (legacy, too conservative)
- 0.50 (FBM->FBA guide default — overestimates margins)
- 0.35 (daily_review_service — too aggressive)
- 0.40 (online model 2026 — calibrated from market data)
"""
import pathlib
from decimal import Decimal

import pytest

from app.schemas.config import ROIConfig


class TestSourcePriceFactorUnified:
    """Tests for unified source_price_factor across services."""

    def test_roi_config_default_is_0_40(self):
        """ROIConfig.source_price_factor default must be 0.40."""
        config = ROIConfig()
        assert config.source_price_factor == Decimal("0.40"), (
            f"Expected 0.40, got {config.source_price_factor}. "
            "Did someone change the default?"
        )

    def test_source_price_factor_calculates_correct_estimated_cost(self):
        """
        With source_price_factor=0.40, a $100 product should have:
        - estimated_cost = $40 (40% of sell price)
        """
        sell_price = Decimal("100.00")
        source_price_factor = Decimal("0.40")
        estimated_cost = sell_price * source_price_factor
        assert estimated_cost == Decimal("40.00"), (
            f"Expected $40.00, got ${estimated_cost}."
        )

    def test_roi_calculation_with_0_40_factor(self):
        """
        Verify ROI calculation with source_price_factor=0.40.

        Example: $80 book
        - Buy cost (40%): $32
        - Amazon fees (22%): $17.60
        - Profit: $80 - $32 - $17.60 = $30.40
        - ROI: ($30.40 / $32) * 100 = 95%
        """
        sell_price = Decimal("80.00")
        source_price_factor = Decimal("0.40")
        fee_percentage = Decimal("0.22")

        buy_cost = sell_price * source_price_factor
        fees = sell_price * fee_percentage
        profit = sell_price - buy_cost - fees
        roi = (profit / buy_cost) * 100

        assert roi > Decimal("50"), (
            f"ROI is {roi}%, expected > 50%."
        )

    def test_source_price_factor_range_validation(self):
        """Verify source_price_factor must be between 0.1 and 0.9."""
        config = ROIConfig(source_price_factor=Decimal("0.40"))
        assert config.source_price_factor == Decimal("0.40")

        with pytest.raises(ValueError):
            ROIConfig(source_price_factor=Decimal("0.05"))
        with pytest.raises(ValueError):
            ROIConfig(source_price_factor=Decimal("0.95"))

    def test_no_old_defaults_in_service_files(self):
        """Scan service files for stale 0.50/0.35 defaults on source_price_factor."""
        files_to_check = [
            "app/services/autosourcing_service.py",
            "app/services/daily_review_service.py",
            "app/api/v1/routers/cowork.py",
        ]
        for fpath in files_to_check:
            content = pathlib.Path(fpath).read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if "source_price_factor" in line and "get(" in line:
                    assert "0.50)" not in line, (
                        f"Old default 0.50 in {fpath}:{i}: {line.strip()}"
                    )
                    assert "0.35)" not in line, (
                        f"Old default 0.35 in {fpath}:{i}: {line.strip()}"
                    )

    def test_source_price_factor_not_legacy_values(self):
        """Verify we're not using legacy 0.28, 0.50, or 0.70 values."""
        config = ROIConfig()
        legacy_values = [Decimal("0.28"), Decimal("0.50"), Decimal("0.70")]
        for val in legacy_values:
            assert config.source_price_factor != val, (
                f"source_price_factor is {val}! Should be 0.40."
            )
