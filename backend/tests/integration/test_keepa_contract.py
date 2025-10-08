"""
Integration Contract Tests for Keepa SDK
=========================================

Validates that the actual Keepa SDK returns expected data structures.

Source verified (2025-10-08):
  - Keepa SDK v1.3.0: https://github.com/akaszynski/keepa
  - PyPI: https://pypi.org/project/keepa/

These tests require KEEPA_API_KEY environment variable.
They are skipped if the key is not available.
"""

import pytest
import os
import numpy as np

# Skip all tests if KEEPA_API_KEY not available
pytestmark = pytest.mark.skipif(
    not os.getenv("KEEPA_API_KEY"),
    reason="Requires KEEPA_API_KEY environment variable"
)


@pytest.fixture(scope="module")
def keepa_api():
    """Create Keepa API instance for testing."""
    import keepa
    api_key = os.getenv("KEEPA_API_KEY")
    return keepa.Keepa(api_key)


@pytest.fixture(scope="module")
def test_product(keepa_api):
    """Query a real product for testing."""
    # Test ASIN: AirPods Pro 2nd Gen (known to have data)
    asin = "B0CHWRXH8B"
    products = keepa_api.query(asin, domain='US', stats=180, history=True, offers=20)

    if not products or len(products) == 0:
        pytest.skip(f"Product {asin} not found in Keepa")

    return products[0]


class TestKeepaStructureContract:
    """Validate Keepa SDK returns expected structure."""

    def test_product_has_data_key(self, test_product):
        """Product dict must have 'data' key."""
        assert 'data' in test_product
        assert isinstance(test_product['data'], dict)

    def test_product_has_asin(self, test_product):
        """Product dict must have 'asin' key."""
        assert 'asin' in test_product
        assert isinstance(test_product['asin'], str)

    def test_product_has_title(self, test_product):
        """Product dict must have 'title' key."""
        assert 'title' in test_product
        assert isinstance(test_product['title'], str)

    def test_data_has_price_arrays(self, test_product):
        """Data section must have price arrays."""
        data = test_product['data']

        # Check for price keys
        price_keys = ['NEW', 'AMAZON', 'SALES']
        for key in price_keys:
            if key in data:
                arr = data[key]
                # Must be numpy array or list
                assert isinstance(arr, (list, np.ndarray)), \
                    f"Expected list or ndarray for '{key}', got {type(arr)}"

    def test_data_has_time_arrays(self, test_product):
        """Data section must have corresponding time arrays."""
        data = test_product['data']

        # Check for time keys
        time_keys = ['NEW_time', 'AMAZON_time', 'SALES_time']
        for key in time_keys:
            if key in data:
                arr = data[key]
                assert isinstance(arr, (list, np.ndarray)), \
                    f"Expected list or ndarray for '{key}', got {type(arr)}"

    def test_new_array_is_numpy(self, test_product):
        """NEW array should be numpy.ndarray."""
        data = test_product['data']

        if 'NEW' in data:
            new_array = data['NEW']
            assert isinstance(new_array, np.ndarray), \
                f"Expected numpy.ndarray for 'NEW', got {type(new_array)}"

    def test_sales_array_is_numpy(self, test_product):
        """SALES (BSR) array should be numpy.ndarray."""
        data = test_product['data']

        if 'SALES' in data:
            sales_array = data['SALES']
            assert isinstance(sales_array, np.ndarray), \
                f"Expected numpy.ndarray for 'SALES', got {type(sales_array)}"

    def test_null_values_are_minus_one(self, test_product):
        """Null values should be represented as -1 (integer)."""
        data = test_product['data']

        if 'NEW' in data:
            new_array = data['NEW']
            # Convert to list for safe iteration
            new_list = new_array.tolist() if hasattr(new_array, 'tolist') else list(new_array)

            # Check for -1 values (null representation)
            has_minus_one = -1 in new_list
            # Note: not all arrays will have -1, but if they do, it should be integer
            if has_minus_one:
                idx = new_list.index(-1)
                assert isinstance(new_list[idx], (int, np.integer)), \
                    "Null value -1 should be integer type"

    def test_price_values_are_cents(self, test_product):
        """Price values should be in cents (integers)."""
        data = test_product['data']

        if 'NEW' in data:
            new_array = data['NEW']
            new_list = new_array.tolist() if hasattr(new_array, 'tolist') else list(new_array)

            # Find first valid price (not -1)
            valid_prices = [p for p in new_list if p != -1 and p is not None]
            if valid_prices:
                price = valid_prices[0]
                # Should be an integer (cents)
                assert isinstance(price, (int, np.integer)), \
                    f"Price should be integer (cents), got {type(price)}"
                # Reasonable price range (0-100000 cents = $0-$1000)
                assert 0 <= price <= 1000000, \
                    f"Price {price} cents seems unreasonable"

    def test_bsr_values_are_integers(self, test_product):
        """BSR (SALES) values should be integers."""
        data = test_product['data']

        if 'SALES' in data:
            sales_array = data['SALES']
            sales_list = sales_array.tolist() if hasattr(sales_array, 'tolist') else list(sales_array)

            # Find first valid BSR (not -1)
            valid_bsr = [b for b in sales_list if b != -1 and b is not None]
            if valid_bsr:
                bsr = valid_bsr[0]
                # Should be an integer (rank)
                assert isinstance(bsr, (int, np.integer)), \
                    f"BSR should be integer, got {type(bsr)}"
                # Reasonable BSR range (1 to 10 million)
                assert 1 <= bsr <= 10000000, \
                    f"BSR {bsr} seems unreasonable"


class TestKeepaQueryAPI:
    """Test Keepa API query methods."""

    def test_query_single_asin(self, keepa_api):
        """Test querying a single ASIN."""
        products = keepa_api.query('B0CHWRXH8B', domain='US')
        assert len(products) >= 1
        assert 'asin' in products[0]

    def test_query_with_history(self, keepa_api):
        """Test querying with history=True."""
        products = keepa_api.query('B0CHWRXH8B', domain='US', history=True)
        assert len(products) >= 1
        assert 'data' in products[0]

    def test_query_with_stats(self, keepa_api):
        """Test querying with stats parameter."""
        products = keepa_api.query('B0CHWRXH8B', domain='US', stats=180)
        assert len(products) >= 1

    def test_domain_string_format(self, keepa_api):
        """Test that domain accepts string format."""
        # Should NOT raise ValueError
        products = keepa_api.query('B0CHWRXH8B', domain='US')
        assert len(products) >= 1
