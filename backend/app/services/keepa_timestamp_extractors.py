"""
Keepa Timestamp Extractors
===========================
Specialized extractors for data freshness timestamps from Keepa API responses.
Implements multi-level fallback strategy for maximum reliability.

Extracted from keepa_extractors.py for Single Responsibility Principle compliance.
"""

from datetime import datetime
from typing import Any, Dict, Optional
import logging

from app.utils.keepa_utils import keepa_to_datetime


logger = logging.getLogger(__name__)


class KeepaTimestampExtractor:
    """
    Extracts data freshness timestamp from Keepa response.
    Multi-level fallback strategy for maximum reliability.
    """

    @staticmethod
    def extract_data_freshness_timestamp(raw_data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract the most relevant timestamp showing data freshness.

        PRIORITY (most reliable to least reliable):
        1. lastPriceChange: Last detected price change by Keepa
        2. Last timestamp in CSV array BUY_BOX (most important price)
        3. Last timestamp in CSV array NEW (fallback)
        4. lastUpdate (last resort, often outdated)

        Args:
            raw_data: Raw Keepa API response

        Returns:
            datetime object or None if no data available
        """
        asin = raw_data.get("asin", "unknown")

        # PRIORITY 1: lastPriceChange (RECOMMENDED)
        last_price_change = raw_data.get("lastPriceChange", -1)

        if last_price_change != -1:
            timestamp = keepa_to_datetime(last_price_change)

            if timestamp is None:
                logger.warning(f"ASIN {asin}: Failed to convert lastPriceChange={last_price_change}")
            else:
                # Verify timestamp is reasonable (< 365 days = 1 year)
                age_days = (datetime.now() - timestamp).days
                if age_days < 365:
                    logger.info(f"ASIN {asin}: Using lastPriceChange timestamp: {timestamp} ({age_days} days old)")
                    return timestamp
                else:
                    logger.warning(f"ASIN {asin}: lastPriceChange too old ({age_days} days), trying fallback")

        # PRIORITY 2: Last timestamp in CSV arrays
        csv_data = raw_data.get("csv", [])

        if csv_data:
            # Priority: BUY_BOX (index 12) > NEW (index 1) > AMAZON (index 0)
            priority_arrays = [
                (12, "BUY_BOX"),  # Most relevant for arbitrage
                (1, "NEW"),       # Fallback
                (0, "AMAZON")     # Last resort
            ]

            for array_idx, array_name in priority_arrays:
                if array_idx < len(csv_data):
                    price_array = csv_data[array_idx]

                    # Check array exists and has data
                    if price_array and len(price_array) >= 2:
                        # Format: [ts1, price1, ts2, price2, ...]
                        # Last timestamp = second-to-last element
                        last_timestamp_keepa = price_array[-2]
                        last_price = price_array[-1]

                        # Verify valid data (-1 = null in Keepa)
                        if last_timestamp_keepa != -1 and last_price != -1:
                            timestamp = keepa_to_datetime(last_timestamp_keepa)

                            if timestamp:
                                age_days = (datetime.now() - timestamp).days
                                logger.info(
                                    f"ASIN {asin}: Using {array_name} array timestamp: {timestamp} "
                                    f"({age_days} days old, price=${last_price/100:.2f})"
                                )
                                return timestamp

        # PRIORITY 3: lastUpdate (LAST RESORT)
        last_update = raw_data.get("lastUpdate", -1)

        if last_update != -1:
            timestamp = keepa_to_datetime(last_update)

            if timestamp:
                age_days = (datetime.now() - timestamp).days
                logger.warning(
                    f"ASIN {asin}: Fallback to lastUpdate: {timestamp} ({age_days} days old) "
                    f"- May be inaccurate"
                )
                return timestamp

        # No data available
        logger.error(f"ASIN {asin}: No timestamp data available in Keepa response")
        return None


__all__ = ['KeepaTimestampExtractor']
