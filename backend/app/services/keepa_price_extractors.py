"""
Keepa Price & Data Extractors
==============================
Handles extraction of current values, historical data, and price-related information
from raw Keepa API responses.

Extracted from keepa_extractors.py for Single Responsibility Principle compliance.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.services.keepa_constants import KeepaCSVType
from app.utils.keepa_utils import (
    extract_latest_value,
    keepa_to_datetime,
    datetime_to_keepa,
    KEEPA_NULL_VALUE,
    KEEPA_PRICE_DIVISOR
)


logger = logging.getLogger(__name__)


class KeepaRawParser:
    """
    Low-level parser for Keepa API raw responses.
    Handles data extraction without business logic.
    """

    @staticmethod
    def extract_current_values(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract current values from product['stats']['current'] array (OFFICIAL Keepa pattern).

        CRITICAL FIX (Oct 15, 2025): Changed from product['data'] to product['stats']['current']
        - product['data']['NEW'] = HISTORICAL array (for charts) [ERROR] WRONG for current prices
        - product['stats']['current'][1] = CURRENT snapshot value [OK] CORRECT

        Keepa stats.current[] indices (official Keepa API structure):
          0: AMAZON - Amazon price
          1: NEW - Marketplace New price (3rd party + Amazon)
          2: USED - Used price
          3: SALES - Sales Rank (BSR) - NOT a price!
          4: LISTPRICE - List price
          10: NEW_FBA - FBA price (3rd party only)
          18: BUY_BOX_SHIPPING - Buy Box price with shipping

        Reference: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java

        Args:
            raw_data: Keepa product dict from keepa.Keepa().query()

        Returns:
            Dictionary with current values (prices, BSR, counts)
        """
        current_values = {}
        asin = raw_data.get('asin', 'unknown')

        # Get 'stats.current' array (official Keepa pattern)
        stats = raw_data.get('stats', {})
        current_array = stats.get('current', [])

        if not current_array:
            logger.warning(f"ASIN {asin}: 'stats.current' array not available")
            return current_values

        # Helper to safely extract value from current array
        def get_current(index: int, is_price: bool = False) -> Optional[Any]:
            """Extract value from stats.current[index] with null checking."""
            if index >= len(current_array):
                return None

            value = current_array[index]

            # -1 = null value in Keepa
            if value is None or value == KEEPA_NULL_VALUE:
                return None

            # Convert price from cents to Decimal
            if is_price:
                return Decimal(value) / Decimal(KEEPA_PRICE_DIVISOR)

            return value

        # Extract current values using official indices
        extractors = [
            (0, 'amazon_price', True),      # Amazon price
            (1, 'new_price', True),         # New price (3rd party + Amazon)
            (2, 'used_price', True),        # Used price
            (3, 'bsr', False),              # BSR (Sales Rank) - INTEGER!
            (4, 'list_price', True),        # List price
            (10, 'fba_price', True),        # FBA price (3rd party only)
            (18, 'buybox_price', True),     # Buy Box price with shipping
        ]

        for index, output_key, is_price in extractors:
            value = get_current(index, is_price)
            if value is not None:
                current_values[output_key] = value
                logger.debug(f"ASIN {asin}: {output_key} = {value}")

        # Extract offer counts - try data section first, then stats.current fallback
        data = raw_data.get('data', {})
        if data:
            # Get latest offer counts from data arrays (these are not in stats.current)
            new_count = extract_latest_value(data, 'COUNT_NEW', is_price=False, null_value=KEEPA_NULL_VALUE)
            used_count = extract_latest_value(data, 'COUNT_USED', is_price=False, null_value=KEEPA_NULL_VALUE)

            if new_count is not None:
                current_values['new_count'] = new_count
            if used_count is not None:
                current_values['used_count'] = used_count
        else:
            # Fallback: Extract from stats.current array (indices 11, 12)
            logger.debug(f"ASIN {asin}: 'data' section not available, using stats.current fallback for offer counts")
            new_count = get_current(11, is_price=False)  # Index 11: New count
            used_count = get_current(12, is_price=False)  # Index 12: Used count

            if new_count is not None:
                current_values['new_count'] = new_count
            if used_count is not None:
                current_values['used_count'] = used_count

        logger.info(f"[OK] ASIN {asin}: Extracted {len(current_values)} current values from stats.current array")

        return current_values

    @staticmethod
    def extract_history_arrays(raw_data: Dict[str, Any], days_back: int = 90) -> Dict[str, List[Tuple]]:
        """
        Extract historical data from product['data'] arrays using keepa library format.

        The keepa library provides:
        - product['data']['SALES'] = BSR values array
        - product['data']['SALES_time'] = corresponding datetime objects
        - product['data']['NEW'] = New price values array
        - product['data']['NEW_time'] = corresponding datetime objects

        Args:
            raw_data: Keepa product dict from keepa.Keepa().query()
            days_back: Number of days of history to extract

        Returns:
            Dictionary with history arrays (bsr_history, price_history, etc.)
        """
        history_data = {}
        asin = raw_data.get('asin', 'unknown')

        # Get 'data' section (created by keepa lib)
        data = raw_data.get('data', {})

        if not data:
            logger.warning(f"ASIN {asin}: 'data' section not available, trying csv fallback")
            # Fallback: Extract from raw csv arrays
            return KeepaRawParser._extract_history_from_csv(raw_data, days_back)

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Helper to extract time series from keepa lib format
        def extract_series(value_key: str, time_key: str, is_price: bool = False) -> List[Tuple]:
            values = data.get(value_key)
            times = data.get(time_key)

            # [OK] Handle numpy arrays - check existence with 'is None', not 'not'
            if values is None or times is None:
                return []

            # Convert to list if numpy array
            try:
                values_list = values.tolist() if hasattr(values, 'tolist') else list(values)
                times_list = times.tolist() if hasattr(times, 'tolist') else list(times)
            except (TypeError, AttributeError):
                return []

            if len(values_list) == 0 or len(times_list) == 0 or len(values_list) != len(times_list):
                return []

            series = []
            for i in range(len(values_list)):
                value = values_list[i]
                time = times_list[i]

                # Skip null/invalid values
                if value is None or value == -1:
                    continue

                # Apply time filter
                if isinstance(time, datetime) and time < cutoff_date:
                    continue

                # Convert price if needed
                if is_price:
                    value = float(KeepaRawParser._convert_price(value))
                else:
                    value = int(value)

                # Ensure time is datetime
                if not isinstance(time, datetime):
                    try:
                        time = datetime.fromisoformat(str(time))
                    except (ValueError, TypeError):
                        continue

                series.append((time, value))

            return series

        # Extract BSR history (SALES)
        bsr_history = extract_series('SALES', 'SALES_time', is_price=False)
        if bsr_history:
            history_data['bsr_history'] = bsr_history
            logger.debug(f"ASIN {asin}: Extracted {len(bsr_history)} BSR data points")

        # Extract price history (NEW)
        price_history = extract_series('NEW', 'NEW_time', is_price=True)
        if price_history:
            history_data['price_history'] = price_history
            logger.debug(f"ASIN {asin}: Extracted {len(price_history)} price data points")

        # Extract Amazon price history
        amazon_history = extract_series('AMAZON', 'AMAZON_time', is_price=True)
        if amazon_history:
            history_data['amazon_history'] = amazon_history

        # Extract Buy Box history
        buybox_history = extract_series('BUY_BOX_SHIPPING', 'BUY_BOX_SHIPPING_time', is_price=True)
        if buybox_history:
            history_data['buybox_history'] = buybox_history

        # Extract offer count history
        offers_history = extract_series('COUNT_NEW', 'COUNT_NEW_time', is_price=False)
        if offers_history:
            history_data['offers_history'] = offers_history

        logger.info(f"[OK] ASIN {asin}: Extracted {len(history_data)} history series from keepa lib format")

        return history_data

    @staticmethod
    def _parse_time_series(data: List, cutoff: int, convert_price: bool = False) -> List[Tuple]:
        """
        Parse Keepa time series data format: [timestamp, value, timestamp, value, ...]
        """
        result = []

        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                timestamp_keepa = data[i]
                value = data[i + 1]

                if timestamp_keepa and timestamp_keepa >= cutoff and value != -1:
                    try:
                        dt = KeepaRawParser._keepa_to_datetime(timestamp_keepa)
                        if convert_price:
                            value = float(KeepaRawParser._convert_price(value))
                        else:
                            value = int(value)
                        result.append((dt, value))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid data point: {e}")
                        continue

        return result

    @staticmethod
    def _extract_history_from_csv(raw_data: Dict[str, Any], days_back: int = 90) -> Dict[str, List[Tuple]]:
        """
        Extract history from raw csv arrays (fallback when keepa SDK 'data' section not available).

        CSV array structure:
        - csv[0]: Amazon prices
        - csv[1]: New prices
        - csv[2]: Used prices
        - csv[3]: BSR (Sales Rank)

        Args:
            raw_data: Raw Keepa response with csv arrays
            days_back: Number of days of history to extract

        Returns:
            Dictionary with history arrays
        """
        history_data = {}
        asin = raw_data.get('asin', 'unknown')
        csv = raw_data.get('csv', [])

        if not csv or len(csv) < 4:
            logger.warning(f"ASIN {asin}: csv arrays not available or incomplete")
            return history_data

        # Calculate cutoff timestamp
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_keepa = KeepaRawParser._datetime_to_keepa(cutoff_date)

        # Extract price history (csv[0] = Amazon, csv[1] = NEW)
        if len(csv[0]) > 0:
            price_history = KeepaRawParser._parse_time_series(csv[0], cutoff_keepa, convert_price=True)
            if price_history:
                history_data['price_history'] = price_history
                logger.debug(f"ASIN {asin}: Extracted {len(price_history)} price data points from csv[0]")

        # Extract BSR history (csv[3] = SALES)
        if len(csv) > 3 and len(csv[3]) > 0:
            bsr_history = KeepaRawParser._parse_time_series(csv[3], cutoff_keepa, convert_price=False)
            if bsr_history:
                history_data['bsr_history'] = bsr_history
                logger.debug(f"ASIN {asin}: Extracted {len(bsr_history)} BSR data points from csv[3]")

        logger.info(f"[OK] ASIN {asin}: Extracted {len(history_data)} history series from csv arrays")

        return history_data

    @staticmethod
    def _convert_price(keepa_price: int) -> Decimal:
        """Convert Keepa price (in cents) to Decimal dollars."""
        return Decimal(keepa_price) / Decimal(100)

    @staticmethod
    def _keepa_to_datetime(keepa_time: int) -> datetime:
        """
        Convert Keepa timestamp to Python datetime.

        Official formula from Keepa Support (Oct 15, 2025):
        unix_seconds = (keepa_time + 21564000) * 60

        IMPORTANT: Uses SECONDS, not milliseconds!
        """
        result = keepa_to_datetime(keepa_time)
        return result if result is not None else datetime.now()

    @staticmethod
    def _datetime_to_keepa(dt: datetime) -> int:
        """
        Convert Python datetime to Keepa timestamp.

        Inverse of _keepa_to_datetime().
        """
        return datetime_to_keepa(dt)


__all__ = ['KeepaRawParser']
