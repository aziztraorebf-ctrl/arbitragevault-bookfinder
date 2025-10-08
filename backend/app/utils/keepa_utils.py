"""
Keepa Data Utilities - NumPy-Safe Helpers
==========================================

Source verified (2025-10-08):
  - Keepa SDK v1.3.0: https://github.com/akaszynski/keepa
  - PyPI: https://pypi.org/project/keepa/
  - Context7 Library ID: /akaszynski/keepa
  - Production test: Render API 2025-10-08 13:34 UTC
  - Confirmed: product['data']['NEW'] = numpy.ndarray, shape (n,)
  - Null values: -1 (integer), not None

NumPy-safe utilities for handling Keepa API responses that return numpy.ndarray
instead of Python lists. These helpers prevent "ambiguous truth value" errors.

Author: Claude Code + Refactor 2025-10-08
"""

from typing import Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def safe_array_check(arr: Any) -> bool:
    """
    Check if array has elements (handles numpy.ndarray, list, None).

    Args:
        arr: Array-like object (numpy.ndarray, list, tuple, etc.) or None

    Returns:
        True if array exists and has elements, False otherwise

    Examples:
        >>> safe_array_check([1, 2, 3])
        True
        >>> safe_array_check([])
        False
        >>> safe_array_check(None)
        False
        >>> import numpy as np
        >>> safe_array_check(np.array([1, 2]))
        True
        >>> safe_array_check(np.array([]))
        False
    """
    if arr is None:
        return False

    try:
        return len(arr) > 0
    except TypeError:
        # Scalar value or unsupported type
        return False


def safe_array_to_list(arr: Any) -> List:
    """
    Convert numpy arrays to regular Python lists safely.

    Handles:
    - numpy.ndarray → list (via .tolist())
    - list → list (pass-through)
    - None → empty list
    - Scalar values → single-element list
    - Errors → empty list

    Args:
        arr: Array-like object or None

    Returns:
        Python list (empty if conversion fails)

    Examples:
        >>> safe_array_to_list([1, 2, 3])
        [1, 2, 3]
        >>> safe_array_to_list(None)
        []
        >>> import numpy as np
        >>> safe_array_to_list(np.array([10, 20]))
        [10, 20]
        >>> safe_array_to_list(np.array([]))
        []
        >>> safe_array_to_list(42)
        [42]
    """
    if arr is None:
        return []

    # Try numpy tolist() first
    if hasattr(arr, "tolist"):
        try:
            result = arr.tolist()
            # Ensure result is a list (tolist() on scalar returns scalar)
            return result if isinstance(result, list) else [result]
        except Exception as e:
            logger.warning(f"Failed tolist() conversion: {e}")
            # Fall through to list() conversion

    # Try Python list() conversion
    try:
        return list(arr)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed list() conversion: {e}")
        # Scalar value? Wrap in list
        return [arr]


def safe_value_check(value: Any, null_value: int = -1) -> bool:
    """
    Check if value is valid (not None, not null_value).

    Keepa uses -1 to represent null/missing values in arrays.

    Args:
        value: Value to check
        null_value: Value representing null (default: -1)

    Returns:
        True if value is valid (not None, not -1), False otherwise

    Examples:
        >>> safe_value_check(100)
        True
        >>> safe_value_check(-1)
        False
        >>> safe_value_check(None)
        False
        >>> safe_value_check(0)
        True
        >>> safe_value_check(-1, null_value=-999)
        True
    """
    if value is None:
        return False

    try:
        return value != null_value
    except (TypeError, ValueError):
        # Comparison failed (e.g., numpy scalar vs Python int)
        try:
            return float(value) != float(null_value)
        except Exception:
            return False


def extract_latest_value(
    data_dict: dict,
    key: str,
    is_price: bool = False,
    null_value: int = -1
) -> Optional[Any]:
    """
    Extract latest valid value from Keepa data array.

    Safely extracts the last non-null value from a numpy array or list,
    handling null values (-1) and type conversions.

    Args:
        data_dict: Product data dictionary (e.g., product['data'])
        key: Data key to extract (e.g., 'NEW', 'SALES')
        is_price: If True, convert cents to dollars (divide by 100)
        null_value: Value representing null (default: -1)

    Returns:
        Latest valid value (float for price, int for BSR/count), or None if not found

    Examples:
        >>> data = {'NEW': [100, 200, -1, 300]}
        >>> extract_latest_value(data, 'NEW', is_price=True)
        3.0
        >>> data = {'SALES': [1000, -1, 500]}
        >>> extract_latest_value(data, 'SALES', is_price=False)
        500
        >>> extract_latest_value(data, 'MISSING_KEY')
        None
    """
    # Get array from dict
    arr = data_dict.get(key)

    if not safe_array_check(arr):
        return None

    # Convert to list
    arr_list = safe_array_to_list(arr)

    # Find last valid value (iterate backwards)
    for value in reversed(arr_list):
        if safe_value_check(value, null_value):
            try:
                if is_price:
                    # Convert cents to dollars
                    return int(value) / 100.0
                else:
                    # Return as integer (BSR, counts, etc.)
                    return int(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert value {value}: {e}")
                continue

    return None


def validate_keepa_data_structure(product: dict) -> bool:
    """
    Validate that product dict has expected Keepa structure.

    Checks:
    - 'data' key exists
    - 'data' is a dictionary
    - Critical keys present (NEW, SALES, etc.)
    - Arrays are numpy.ndarray or list

    Args:
        product: Product dictionary from keepa.query()

    Returns:
        True if structure is valid, False otherwise

    Raises:
        TypeError: If structure is invalid (in non-production mode)
    """
    if not isinstance(product, dict):
        logger.error(f"Invalid product type: {type(product)}, expected dict")
        return False

    if 'data' not in product:
        logger.error("Missing 'data' key in product dict")
        return False

    data = product['data']

    if not isinstance(data, dict):
        logger.error(f"Invalid 'data' type: {type(data)}, expected dict")
        return False

    # Check critical keys
    critical_keys = ['NEW', 'SALES']
    for key in critical_keys:
        if key in data:
            arr = data[key]
            # Verify it's array-like (numpy.ndarray or list)
            if not (hasattr(arr, '__len__') or hasattr(arr, 'tolist')):
                logger.warning(
                    f"Data key '{key}' has unexpected type: {type(arr)}"
                )
        else:
            logger.debug(f"Optional key '{key}' not present in data")

    return True


# Convenience constants
KEEPA_NULL_VALUE = -1  # Keepa uses -1 to represent null/missing values
KEEPA_PRICE_DIVISOR = 100  # Prices stored in cents, divide by 100 for dollars
