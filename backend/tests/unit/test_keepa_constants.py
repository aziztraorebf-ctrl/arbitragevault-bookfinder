"""
Unit tests for Keepa constants - ensures all required constants are exported.
"""
import pytest


class TestKeepaConstants:
    """Test suite for keepa_constants module."""

    def test_keepa_csv_type_enum_exists(self):
        """Verify KeepaCSVType enum is importable from services."""
        from app.services.keepa_constants import KeepaCSVType

        assert KeepaCSVType.AMAZON == 0
        assert KeepaCSVType.NEW == 1
        assert KeepaCSVType.USED == 2
        assert KeepaCSVType.SALES == 3
        assert KeepaCSVType.NEW_FBA == 10

    def test_keepa_time_constants_exist(self):
        """Verify time conversion constants are available."""
        from app.services.keepa_constants import (
            KEEPA_TIME_OFFSET_MINUTES,
            KEEPA_NULL_VALUE,
            KEEPA_PRICE_DIVISOR
        )

        assert KEEPA_TIME_OFFSET_MINUTES == 21564000
        assert KEEPA_NULL_VALUE == -1
        assert KEEPA_PRICE_DIVISOR == 100

    def test_condition_codes_exist(self):
        """Verify condition codes are defined."""
        from app.services.keepa_constants import (
            KEEPA_CONDITION_CODES,
            DEFAULT_CONDITIONS,
            ALL_CONDITION_KEYS
        )

        assert 1 in KEEPA_CONDITION_CODES
        assert KEEPA_CONDITION_CODES[1][0] == 'new'
        assert 'new' in DEFAULT_CONDITIONS
        assert 'acceptable' in ALL_CONDITION_KEYS

    def test_all_exports_defined(self):
        """Verify __all__ includes all required exports."""
        from app.services import keepa_constants

        expected_exports = [
            'KeepaCSVType',
            'KEEPA_CONDITION_CODES',
            'DEFAULT_CONDITIONS',
            'ALL_CONDITION_KEYS',
            'KEEPA_TIME_OFFSET_MINUTES',
            'KEEPA_NULL_VALUE',
            'KEEPA_PRICE_DIVISOR'
        ]

        for export in expected_exports:
            assert hasattr(keepa_constants, export), f"Missing export: {export}"
