"""
Test de validation de la conversion Keepa Time
===============================================

Source: Keepa Support Email (October 15, 2025)

Official validation:
keepa_time = 7777548 → Oct 15 2025 03:48:00 GMT+0200 → Oct 15 2025 01:48:00 UTC

Author: Claude Code + Keepa Support Specification
Last Updated: 2025-10-15
"""

import pytest
from datetime import datetime
from app.utils.keepa_utils import keepa_to_datetime, datetime_to_keepa
from app.utils.keepa_constants import KEEPA_TIME_OFFSET_MINUTES


def test_keepa_time_conversion_official_example():
    """
    Test avec l'exemple exact du support Keepa.

    Valeur officielle confirmée par Keepa Support:
    keepa_time = 7777548 → Oct 15 2025 03:48:00 GMT+0200
                        → Oct 15 2025 01:48:00 UTC

    CRITICAL: This test MUST pass. If it fails, the conversion formula is wrong.
    """
    keepa_time = 7777548
    result = keepa_to_datetime(keepa_time)

    assert result is not None, "Conversion should not return None"

    # Validate exact date/time (UTC)
    assert result.year == 2025, f"❌ Expected year 2025, got {result.year}"
    assert result.month == 10, f"❌ Expected month 10, got {result.month}"
    assert result.day == 15, f"❌ Expected day 15, got {result.day}"
    assert result.hour == 1, f"❌ Expected hour 1 (UTC), got {result.hour}"
    assert result.minute == 48, f"❌ Expected minute 48, got {result.minute}"

    print(f"✅ Conversion correcte: keepa_time={keepa_time} → {result.isoformat()}")


def test_keepa_time_conversion_formula():
    """
    Test que la formule officielle est correctement implémentée.

    Formula: unix_seconds = (keepa_time + 21564000) * 60
    """
    keepa_time = 7777548

    # Calculate manually
    expected_unix_seconds = (keepa_time + KEEPA_TIME_OFFSET_MINUTES) * 60
    expected_dt = datetime.utcfromtimestamp(expected_unix_seconds)

    # Use our function
    result_dt = keepa_to_datetime(keepa_time)

    assert result_dt == expected_dt, (
        f"Formula mismatch:\n"
        f"  Expected: {expected_dt.isoformat()}\n"
        f"  Got:      {result_dt.isoformat()}"
    )


def test_keepa_time_null_values():
    """Test que les valeurs null sont gérées correctement."""
    # Keepa uses -1 for null
    assert keepa_to_datetime(-1) is None, "keepa_time=-1 should return None"
    assert keepa_to_datetime(None) is None, "keepa_time=None should return None"


def test_keepa_time_roundtrip():
    """
    Test conversion bidirectionnelle (roundtrip).

    datetime → keepa_time → datetime should preserve the value.
    """
    original_dt = datetime(2025, 10, 15, 1, 48, 0)

    # Convert to keepa time
    keepa_time = datetime_to_keepa(original_dt)

    # Convert back to datetime
    result_dt = keepa_to_datetime(keepa_time)

    # Should match original (with 1-minute tolerance due to integer division)
    diff_seconds = abs((result_dt - original_dt).total_seconds())
    assert diff_seconds < 60, (
        f"Roundtrip error: {diff_seconds}s\n"
        f"  Original:  {original_dt.isoformat()}\n"
        f"  Keepa:     {keepa_time}\n"
        f"  Result:    {result_dt.isoformat()}"
    )


def test_keepa_epoch_regression_detection():
    """
    Test de régression pour détecter retour à l'ancien epoch.

    CRITICAL: This test prevents regression to the old (incorrect) epoch.

    Old epoch (971222400) gave dates in 2015 (WRONG).
    New formula (offset 21564000) gives dates in 2025 (CORRECT).

    If this test fails, someone re-introduced the legacy epoch bug!
    """
    keepa_time = 7777548
    result = keepa_to_datetime(keepa_time)

    # MUST be in 2025, NOT 2015
    assert result.year >= 2025, (
        f"⚠️ REGRESSION DETECTED: Using old epoch!\n"
        f"  Expected year ≥ 2025, got {result.year}\n"
        f"  This means the legacy epoch (971222400) is being used.\n"
        f"  Fix: Use offset 21564000 instead."
    )

    # If we get 2015, it's definitely the old epoch
    if result.year == 2015:
        pytest.fail(
            "❌ CRITICAL REGRESSION: Using legacy epoch (971222400)!\n"
            "This gives dates in 2015 instead of 2025.\n"
            "MUST use official offset: (keepa_time + 21564000) * 60"
        )

    print(f"✅ No regression detected: year={result.year} (expected ≥ 2025)")


def test_keepa_time_recent_dates():
    """
    Test avec des dates récentes pour vérifier cohérence.

    Les timestamps Keepa doivent donner des dates proches de maintenant.
    """
    # Timestamp approximate pour "maintenant" (Oct 2025)
    # Calculation: roughly 7777548 = Oct 15 2025
    # So dates within ±30 days should be around 7776000 to 7779000

    test_cases = [
        (7776000, "Early October 2025"),
        (7777548, "Mid October 2025"),
        (7779000, "Late October 2025"),
    ]

    for keepa_time, description in test_cases:
        result = keepa_to_datetime(keepa_time)

        assert result is not None, f"Failed to convert {keepa_time}"
        assert result.year == 2025, f"{description}: wrong year {result.year}"
        assert result.month == 10, f"{description}: wrong month {result.month}"

        print(f"✅ {description}: {result.isoformat()}")


def test_keepa_time_zero_and_edge_cases():
    """Test edge cases."""
    # Zero gives the Keepa epoch start date
    # Formula: (0 + 21564000) * 60 = 1293840000 seconds = Jan 1, 2011 00:00:00 UTC
    result_zero = keepa_to_datetime(0)
    assert result_zero is not None
    assert result_zero.year == 2011, f"keepa_time=0 should give year 2011 (Keepa epoch), got {result_zero.year}"
    assert result_zero.month == 1, f"keepa_time=0 should give month 1, got {result_zero.month}"
    assert result_zero.day == 1, f"keepa_time=0 should give day 1, got {result_zero.day}"

    # Very large value should give future date
    # keepa_time=10000000 -> (10000000 + 21564000) * 60 = 1893840000 seconds = ~2030
    result_large = keepa_to_datetime(10000000)
    assert result_large is not None
    assert result_large.year > 2025, f"Large keepa_time should be in future, got {result_large.year}"


def test_keepa_constants_consistency():
    """
    Verify that constants are correctly defined.
    """
    from app.utils.keepa_constants import (
        KEEPA_TIME_OFFSET_MINUTES,
        KEEPA_EPOCH_LEGACY,
        KEEPA_NULL_VALUE
    )

    # Official offset
    assert KEEPA_TIME_OFFSET_MINUTES == 21564000, (
        f"❌ CRITICAL: Wrong offset value!\n"
        f"  Expected: 21564000 (official Keepa spec)\n"
        f"  Got:      {KEEPA_TIME_OFFSET_MINUTES}"
    )

    # Legacy epoch (should exist but not be used)
    assert KEEPA_EPOCH_LEGACY == 971222400, "Legacy epoch constant wrong"

    # Null value
    assert KEEPA_NULL_VALUE == -1, "Null value constant wrong"

    print("✅ All constants correctly defined")


if __name__ == "__main__":
    """Run tests with verbose output."""
    print("=" * 70)
    print("Keepa Time Conversion Validation Tests")
    print("=" * 70)
    print()

    pytest.main([__file__, "-v", "--tb=short"])
