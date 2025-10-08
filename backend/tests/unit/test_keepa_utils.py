"""
Unit Tests for Keepa Utilities - NumPy-Safe Helpers
====================================================

Tests numpy-safe helper functions for handling Keepa API responses.

Source verified (2025-10-08):
  - Keepa SDK v1.3.0: https://github.com/akaszynski/keepa
  - Documentation: docs/keepa_structure_verified.md
"""

import pytest
import numpy as np
from decimal import Decimal

from app.utils.keepa_utils import (
    safe_array_check,
    safe_array_to_list,
    safe_value_check,
    extract_latest_value,
    validate_keepa_data_structure,
    KEEPA_NULL_VALUE,
    KEEPA_PRICE_DIVISOR
)


class TestSafeArrayCheck:
    """Test safe_array_check() function."""

    def test_with_list(self):
        """Test with Python list."""
        assert safe_array_check([1, 2, 3]) is True
        assert safe_array_check([]) is False

    def test_with_none(self):
        """Test with None value."""
        assert safe_array_check(None) is False

    def test_with_numpy_array(self):
        """Test with numpy arrays."""
        assert safe_array_check(np.array([1, 2])) is True
        assert safe_array_check(np.array([])) is False

    def test_with_tuple(self):
        """Test with tuple."""
        assert safe_array_check((1, 2, 3)) is True
        assert safe_array_check(()) is False

    def test_with_scalar(self):
        """Test with scalar values."""
        assert safe_array_check(42) is False
        assert safe_array_check("string") is False


class TestSafeArrayToList:
    """Test safe_array_to_list() function."""

    def test_with_list(self):
        """Test with Python list (pass-through)."""
        assert safe_array_to_list([1, 2, 3]) == [1, 2, 3]
        assert safe_array_to_list([]) == []

    def test_with_none(self):
        """Test with None returns empty list."""
        assert safe_array_to_list(None) == []

    def test_with_numpy_array(self):
        """Test with numpy array conversion."""
        result = safe_array_to_list(np.array([10, 20, 30]))
        assert result == [10, 20, 30]
        assert isinstance(result, list)

    def test_with_empty_numpy(self):
        """Test with empty numpy array."""
        result = safe_array_to_list(np.array([]))
        assert result == []

    def test_with_scalar(self):
        """Test with scalar wraps in list."""
        assert safe_array_to_list(42) == [42]
        assert safe_array_to_list("hello") == ["hello"]

    def test_with_tuple(self):
        """Test with tuple converts to list."""
        assert safe_array_to_list((1, 2, 3)) == [1, 2, 3]


class TestSafeValueCheck:
    """Test safe_value_check() function."""

    def test_valid_values(self):
        """Test with valid (non-null) values."""
        assert safe_value_check(100) is True
        assert safe_value_check(0) is True
        assert safe_value_check(1.5) is True

    def test_null_value_default(self):
        """Test with default null value (-1)."""
        assert safe_value_check(-1) is False
        assert safe_value_check(KEEPA_NULL_VALUE) is False

    def test_custom_null_value(self):
        """Test with custom null value."""
        assert safe_value_check(-1, null_value=-999) is True
        assert safe_value_check(-999, null_value=-999) is False

    def test_none_value(self):
        """Test with None returns False."""
        assert safe_value_check(None) is False

    def test_numpy_scalar(self):
        """Test with numpy scalar types."""
        assert safe_value_check(np.int64(100)) is True
        assert safe_value_check(np.int64(-1)) is False


class TestExtractLatestValue:
    """Test extract_latest_value() function."""

    def test_extract_price(self):
        """Test price extraction (cents to dollars)."""
        data = {'NEW': [100, 200, -1, 300]}
        result = extract_latest_value(data, 'NEW', is_price=True)
        assert result == 3.0  # 300 cents = $3.00

    def test_extract_bsr(self):
        """Test BSR extraction (integer)."""
        data = {'SALES': [1000, -1, 500]}
        result = extract_latest_value(data, 'SALES', is_price=False)
        assert result == 500

    def test_missing_key(self):
        """Test with missing key returns None."""
        data = {'NEW': [100, 200]}
        result = extract_latest_value(data, 'MISSING_KEY')
        assert result is None

    def test_empty_array(self):
        """Test with empty array returns None."""
        data = {'NEW': []}
        result = extract_latest_value(data, 'NEW')
        assert result is None

    def test_all_null_values(self):
        """Test with all -1 values returns None."""
        data = {'NEW': [-1, -1, -1]}
        result = extract_latest_value(data, 'NEW')
        assert result is None

    def test_with_numpy_array(self):
        """Test with numpy array."""
        data = {'NEW': np.array([100, 200, 300])}
        result = extract_latest_value(data, 'NEW', is_price=True)
        assert result == 3.0

    def test_price_conversion(self):
        """Test price conversion from cents."""
        data = {'NEW': [2299]}  # $22.99
        result = extract_latest_value(data, 'NEW', is_price=True)
        assert result == 22.99


class TestValidateKeepaDataStructure:
    """Test validate_keepa_data_structure() function."""

    def test_valid_structure(self):
        """Test with valid product structure."""
        product = {
            'asin': 'B0CHWRXH8B',
            'data': {
                'NEW': np.array([100, 200]),
                'SALES': np.array([1000, 500])
            }
        }
        assert validate_keepa_data_structure(product) is True

    def test_missing_data_key(self):
        """Test with missing 'data' key."""
        product = {'asin': 'B0CHWRXH8B'}
        assert validate_keepa_data_structure(product) is False

    def test_invalid_data_type(self):
        """Test with invalid 'data' type."""
        product = {'data': "not a dict"}
        assert validate_keepa_data_structure(product) is False

    def test_invalid_product_type(self):
        """Test with non-dict product."""
        assert validate_keepa_data_structure("not a dict") is False
        assert validate_keepa_data_structure(None) is False

    def test_with_python_lists(self):
        """Test with Python lists instead of numpy."""
        product = {
            'asin': 'TEST',
            'data': {
                'NEW': [100, 200],
                'SALES': [1000, 500]
            }
        }
        assert validate_keepa_data_structure(product) is True


class TestConstants:
    """Test module constants."""

    def test_null_value_constant(self):
        """Test KEEPA_NULL_VALUE constant."""
        assert KEEPA_NULL_VALUE == -1

    def test_price_divisor_constant(self):
        """Test KEEPA_PRICE_DIVISOR constant."""
        assert KEEPA_PRICE_DIVISOR == 100
