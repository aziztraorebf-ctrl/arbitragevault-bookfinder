"""
Keepa API Response Parser v2.0 - Production-ready with enhanced BSR extraction
================================================================================
Refactored version with proper BSR extraction pattern following official Keepa documentation.

Author: Claude Opus 4.1 + Context7 Validation
Date: October 2025
Last Modified: 2025-10-08 03:05 UTC - Force cache invalidation
"""

from datetime import datetime, timedelta
from decimal import Decimal
import decimal
from typing import Dict, List, Optional, Any, Tuple
import logging
from enum import IntEnum

from app.models.keepa_models import ProductStatus
from app.core.calculations import VelocityData
from app.utils.keepa_utils import (
    safe_array_check,
    safe_array_to_list,
    safe_value_check,
    extract_latest_value,
    KEEPA_NULL_VALUE,
    KEEPA_PRICE_DIVISOR
)


# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KeepaCSVType(IntEnum):
    """
    Official Keepa CSV Type indices from Java API.
    Source: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
    """
    AMAZON = 0              # Amazon price
    NEW = 1                 # Marketplace New price (includes Amazon)
    USED = 2                # Used price
    SALES = 3               # Sales Rank (BSR) - INTEGER not price!
    LISTPRICE = 4           # List price
    COLLECTIBLE = 5         # Collectible price
    REFURBISHED = 6         # Refurbished price
    NEW_FBM_SHIPPING = 7    # FBM with shipping
    LIGHTNING_DEAL = 8      # Lightning deal price
    WAREHOUSE = 9           # Amazon Warehouse
    NEW_FBA = 10            # FBA price (3rd party only)
    COUNT_NEW = 11          # New offer count
    COUNT_USED = 12         # Used offer count
    COUNT_REFURBISHED = 13  # Refurbished count
    COUNT_COLLECTIBLE = 14  # Collectible count
    RATING = 15             # Product rating (0-50, e.g., 45 = 4.5 stars)
    COUNT_REVIEWS = 16      # Review count
    BUY_BOX_SHIPPING = 18   # Buy Box price with shipping


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
                    except:
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
        from app.utils.keepa_utils import keepa_to_datetime
        result = keepa_to_datetime(keepa_time)
        return result if result is not None else datetime.now()

    @staticmethod
    def _datetime_to_keepa(dt: datetime) -> int:
        """
        Convert Python datetime to Keepa timestamp.

        Inverse of _keepa_to_datetime().
        """
        from app.utils.keepa_utils import datetime_to_keepa
        return datetime_to_keepa(dt)


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
        from app.utils.keepa_utils import keepa_to_datetime

        asin = raw_data.get("asin", "unknown")

        # ═══════════════════════════════════════════════════════
        # PRIORITY 1: lastPriceChange (RECOMMENDED)
        # ═══════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════
        # PRIORITY 2: Last timestamp in CSV arrays
        # ═══════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════
        # PRIORITY 3: lastUpdate (LAST RESORT)
        # ═══════════════════════════════════════════════════════
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


class KeepaBSRExtractor:
    """
    Business logic layer for BSR extraction and validation.
    Implements fallback strategies and data quality checks.
    """

    @staticmethod
    def extract_current_bsr(raw_data: Dict[str, Any]) -> Tuple[Optional[int], str]:
        """
        Extract current BSR with multiple fallback strategies.

        Priority order (UPDATED based on real Keepa API structure):
        1. salesRanks[categoryId][1] (current BSR value) - source: 'salesRanks'
        2. stats.current[3] (legacy format support) - source: 'current'
        3. Last point from csv[3] history (if recent) - source: 'csv_recent'
        4. stats.avg30[3] (30-day average as fallback) - source: 'avg30'

        Args:
            raw_data: Raw Keepa API response

        Returns:
            Tuple of (BSR value or None, data source identifier)
        """
        asin = raw_data.get("asin", "unknown")

        # Extract stats early for use in fallback strategies
        stats = raw_data.get("stats", {})

        # Strategy 1: NEW - salesRanks format (current Keepa API structure)
        # Format: {"categoryId": [timestamp, bsr_value]}
        sales_ranks = raw_data.get("salesRanks", {})
        sales_rank_reference = raw_data.get("salesRankReference")

        # Try main category first (only if valid reference)
        if sales_rank_reference and sales_rank_reference != -1 and str(sales_rank_reference) in sales_ranks:
            rank_data = sales_ranks[str(sales_rank_reference)]
            if isinstance(rank_data, list) and len(rank_data) >= 2:
                # salesRanks format: [timestamp1, bsr1, timestamp2, bsr2, ...]
                # Last element is the most recent BSR
                bsr = rank_data[-1]  # FIX: Read LAST element (current BSR), not second
                if bsr and bsr != -1:
                    logger.info(f"ASIN {asin}: BSR {bsr} from salesRanks[{sales_rank_reference}]")
                    return int(bsr), "salesRanks"

        # Fallback to any available category
        if sales_ranks:
            for category_id, rank_data in sales_ranks.items():
                if isinstance(rank_data, list) and len(rank_data) >= 2:
                    bsr = rank_data[-1]  # FIX: Read LAST element (current BSR)
                    if bsr and bsr != -1:
                        logger.info(f"ASIN {asin}: BSR {bsr} from salesRanks[{category_id}]")
                        return int(bsr), "salesRanks"

        # Strategy 2: Legacy - current[3] (older Keepa API format)
        # Keep for backward compatibility
        current = raw_data.get("current")
        if not current:  # Fallback ancien format
            current = stats.get("current", [])

        if current and len(current) > KeepaCSVType.SALES:
            bsr = current[KeepaCSVType.SALES]
            if bsr and bsr != -1:
                logger.info(f"ASIN {asin}: BSR {bsr} from current[3] (legacy)")
                return int(bsr), "current"

        # Strategy 3: Fallback to last historical point if recent
        csv_data = raw_data.get("csv", [])
        if csv_data and len(csv_data) > KeepaCSVType.SALES:
            sales_data = csv_data[KeepaCSVType.SALES]
            if sales_data and len(sales_data) >= 2:
                # Check last data point (must be within 24 hours)
                last_timestamp = sales_data[-2] if len(sales_data) >= 2 else None
                last_value = sales_data[-1] if len(sales_data) >= 1 else None

                if last_timestamp and last_value and last_value != -1:
                    last_date = KeepaRawParser._keepa_to_datetime(last_timestamp)
                    age_hours = (datetime.now() - last_date).total_seconds() / 3600

                    # Only accept recent data (within last 24h)
                    if age_hours <= 24:
                        logger.info(f"ASIN {asin}: BSR {last_value} from csv[3] history ({age_hours:.1f}h old)")
                        return int(last_value), "csv_recent"
                    else:
                        logger.debug(f"ASIN {asin}: Historical BSR too old ({age_hours:.1f}h)")

        # Strategy 4: Use 30-day average if available (legacy support)
        avg30 = stats.get("avg30", [])
        if avg30 and len(avg30) > KeepaCSVType.SALES:
            avg_bsr = avg30[KeepaCSVType.SALES]
            if avg_bsr and avg_bsr != -1:
                logger.warning(f"ASIN {asin}: Using 30-day avg BSR {avg_bsr} as fallback")
                return int(avg_bsr), "avg30"

        logger.warning(f"ASIN {asin}: No BSR data available from any source")
        return None, "none"

    @staticmethod
    def validate_bsr_quality(bsr: Optional[int], category: str = "unknown", source: str = "current") -> Dict[str, Any]:
        """
        Validate BSR value and assess data quality.

        Args:
            bsr: BSR value to validate
            category: Product category for context
            source: Data source identifier (salesRanks, current, csv_recent, avg30, none)

        Returns:
            Quality assessment with confidence score (adjusted by source quality)
        """
        if bsr is None or source == "none":
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": "No BSR data available"
            }

        # BSR range validation by category
        category_ranges = {
            "books": (1, 5_000_000),
            "electronics": (1, 1_000_000),
            "toys": (1, 2_000_000),
            "default": (1, 10_000_000)
        }

        min_bsr, max_bsr = category_ranges.get(category.lower(), category_ranges["default"])

        if not (min_bsr <= bsr <= max_bsr):
            return {
                "valid": False,
                "confidence": 0.3,
                "reason": f"BSR {bsr} outside expected range for {category}"
            }

        # Calculate base confidence based on BSR value
        if bsr < 10_000:
            base_confidence = 1.0  # Top sellers have reliable BSR
        elif bsr < 100_000:
            base_confidence = 0.9
        elif bsr < 1_000_000:
            base_confidence = 0.7
        else:
            base_confidence = 0.5  # Lower confidence for high BSR

        # Apply penalty for fallback data sources
        source_multipliers = {
            "salesRanks": 1.0,  # Primary source, no penalty
            "current": 1.0,     # Also current data, no penalty
            "csv_recent": 0.9,  # Recent historical data, slight penalty
            "avg30": 0.8,       # 30-day average, significant penalty
        }

        source_multiplier = source_multipliers.get(source, 0.7)  # Default penalty for unknown sources
        final_confidence = base_confidence * source_multiplier

        return {
            "valid": True,
            "confidence": final_confidence,
            "reason": f"BSR within expected range (source: {source})"
        }


def parse_keepa_product(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Keepa product parsing.
    Orchestrates parsing with enhanced BSR extraction and logging.

    Args:
        raw_data: Raw Keepa API response for a single product

    Returns:
        Structured product data with current_bsr properly extracted
    """
    asin = raw_data.get("asin", "unknown")
    logger.info(f"=== Parsing Keepa product: {asin} ===")

    try:
        # Basic product info
        product_data = {
            "asin": asin,
            "title": raw_data.get("title", ""),
            "category": _extract_category(raw_data),
            "brand": raw_data.get("brand", ""),
            "manufacturer": raw_data.get("manufacturer", ""),
            "status": ProductStatus.ACTIVE.value,
            "domain": raw_data.get("domainId", 1)
        }

        # Package dimensions (for FBA fees)
        package_data = raw_data.get("packageDimensions", {})
        if package_data:
            product_data.update({
                "package_height": _safe_decimal(package_data.get("height")),
                "package_length": _safe_decimal(package_data.get("length")),
                "package_width": _safe_decimal(package_data.get("width")),
                "package_weight": _safe_decimal(package_data.get("weight"))
            })

        # Extract current values using refactored parser
        parser = KeepaRawParser()
        current_values = parser.extract_current_values(raw_data)

        # Map to expected field names
        product_data.update({
            "current_amazon_price": current_values.get("amazon_price"),
            "current_fbm_price": current_values.get("new_price"),
            "current_used_price": current_values.get("used_price"),
            "current_fba_price": current_values.get("fba_price"),
            "current_buybox_price": current_values.get("buybox_price"),
            "offers_count": current_values.get("new_count"),
        })

        # Extract BSR with enhanced logic (returns tuple: (bsr, source))
        extractor = KeepaBSRExtractor()
        current_bsr, bsr_source = extractor.extract_current_bsr(raw_data)
        product_data["current_bsr"] = current_bsr

        # Validate BSR quality (adjusted by data source)
        bsr_validation = extractor.validate_bsr_quality(current_bsr, product_data["category"], bsr_source)
        product_data["bsr_confidence"] = bsr_validation["confidence"]

        if current_bsr:
            logger.info(f"[OK] ASIN {asin}: BSR={current_bsr}, confidence={bsr_validation['confidence']:.2f}")
        else:
            logger.warning(f"[WARNING] ASIN {asin}: No BSR available - {bsr_validation['reason']}")

        # Determine best current price
        product_data["current_price"] = _determine_best_current_price(product_data)

        # Extract historical data
        history_data = parser.extract_history_arrays(raw_data)
        product_data.update(history_data)

        # Store raw data for debugging
        product_data["raw_data"] = raw_data
        product_data["parsing_timestamp"] = datetime.now().isoformat()
        product_data["keepa_product_code"] = raw_data.get("productCode")

        # Extract data freshness timestamp with multi-level fallback strategy
        timestamp_extractor = KeepaTimestampExtractor()
        freshness_timestamp = timestamp_extractor.extract_data_freshness_timestamp(raw_data)

        if freshness_timestamp:
            product_data["last_updated_at"] = freshness_timestamp.isoformat()
        else:
            product_data["last_updated_at"] = None

        logger.info(f"[OK] Successfully parsed {asin}: price=${product_data.get('current_price')}, BSR={current_bsr}")
        return product_data

    except Exception as e:
        logger.error(f"[ERROR] Failed to parse Keepa product {asin}: {e}", exc_info=True)
        return {
            "asin": asin,
            "error": f"Parsing failed: {str(e)}",
            "raw_data": raw_data,
            "status": ProductStatus.UNRESOLVED.value
        }


def _extract_category(raw_data: Dict[str, Any]) -> str:
    """Extract product category from Keepa data."""
    category_fields = [
        raw_data.get("category"),
        raw_data.get("categoryTree", [{}])[-1].get("name") if raw_data.get("categoryTree") else None,
        raw_data.get("productGroup"),
        raw_data.get("binding")
    ]

    for field in category_fields:
        if field and isinstance(field, str):
            return field.lower().strip()

    return "unknown"


def _determine_target_sell_price(data: Dict[str, Any]) -> Optional[Decimal]:
    """
    Determine sell price for USED arbitrage (BuyBox competition target).

    Strategy: USED-to-USED arbitrage (buy from FBA sellers, resell via FBA at BuyBox).
    Priority: BuyBox USED > FBA avg > NEW fallback
    Excludes: current_amazon_price (too high NEW), current_used_price (defective items)

    Returns:
        Decimal price if valid, None otherwise
    """
    price_priority = [
        "current_buybox_price",  # [OK] Target for BuyBox competition (USED)
        "current_fba_price",     # [OK] FBA average if BuyBox missing
        "current_new_price",     # [WARNING] Fallback only
    ]

    for price_field in price_priority:
        price = data.get(price_field)
        if price is not None:
            try:
                price_val = float(price) if price else 0
                if price_val > 0:
                    return Decimal(str(price))
            except (ValueError, TypeError, decimal.InvalidOperation):
                continue

    return None


def _determine_buy_cost_used(data: Dict[str, Any]) -> Optional[Decimal]:
    """
    Determine purchase cost from FBA USED sellers.

    Strategy: Buy USED books from third-party FBA sellers.
    Priority: FBA USED > NEW fallback
    Excludes: current_used_price (too low, defective items)

    Returns:
        Decimal cost if valid, None otherwise
    """
    price_priority = [
        "current_fba_price",    # [OK] FBA USED sellers (primary source)
        "lowest_offer_new",     # [WARNING] Fallback if USED unavailable
    ]

    for price_field in price_priority:
        price = data.get(price_field)
        if price is not None:
            try:
                price_val = float(price) if price else 0
                if price_val > 0:
                    return Decimal(str(price))
            except (ValueError, TypeError, decimal.InvalidOperation):
                continue

    return None


def _auto_select_strategy(parsed: Dict[str, Any]) -> str:
    """
    Auto-select strategy based on price + BSR business rules.

    Rules:
    - Textbook: price ≥$40, BSR ≤250k (high margin, slow rotation OK)
    - Velocity: price ≥$25, BSR <250k (modest margin, fast rotation)
    - Balanced: fallback for products outside textbook/velocity criteria

    Args:
        parsed: Parsed Keepa product data with current_buybox_price and current_bsr

    Returns:
        Strategy name: "textbook", "velocity", or "balanced"
    """
    # Extract price (prefer BuyBox, fallback to any available)
    price_raw = parsed.get("current_buybox_price") or parsed.get("current_price") or 0
    try:
        price = float(price_raw) if price_raw else 0
    except (ValueError, TypeError):
        price = 0

    # Extract BSR
    bsr = parsed.get("current_bsr") or 999999

    # Business rules
    if price >= 40 and bsr <= 250000:
        return "textbook"
    elif price >= 25 and bsr < 250000:
        return "velocity"
    else:
        return "balanced"


def _determine_best_current_price(data: Dict[str, Any]) -> Optional[Decimal]:
    """
    DEPRECATED: Use _determine_target_sell_price() instead.
    Kept for backward compatibility during transition.

    Determine the best current price from available options.
    Priority: Amazon > FBA > New > Buy Box > Used
    """
    price_priority = [
        "current_amazon_price",
        "current_fba_price",
        "current_fbm_price",
        "current_buybox_price",
        "current_used_price"
    ]

    for price_field in price_priority:
        price = data.get(price_field)
        if price is not None:
            try:
                # Handle Decimal, float, numpy scalars, etc.
                price_val = float(price) if price else 0
                if price_val > 0:
                    return price
            except (ValueError, TypeError, decimal.InvalidOperation):
                continue

    return None


def _safe_decimal(value: Any) -> Optional[Decimal]:
    """Safely convert value to Decimal."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


# ==================== UNIFIED PARSER FOR PHASE 1 ====================


def parse_keepa_product_unified(raw_keepa: Dict[str, Any]) -> Dict[str, Any]:
    """
    UNIFIED parser - Extracts ALL data from Keepa response.
    Used by ALL endpoints: Analyse Manuelle + Mes Niches + AutoSourcing

    Extracts:
    - Current prices (Amazon, New, Used, FBA)
    - BSR (Sales Rank)
    - Offers detailed with conditions
    - History data
    - Metadata

    Returns: Complete structured dict ready for analysis
    """
    asin = raw_keepa.get('asin', 'unknown')
    parsed = {
        'asin': asin,
        'title': raw_keepa.get('title'),
        'errors': []
    }

    # Step 1: Extract BSR using our enhanced extractor
    # IMPORTANT: Use KeepaBSRExtractor.extract_current_bsr() which handles salesRanks format
    parsed['current_bsr'] = KeepaBSRExtractor.extract_current_bsr(raw_keepa)

    # Step 1b: Extract current prices
    # Try modern format first (directly in product object)
    stats = raw_keepa.get('stats', {})
    current_array = stats.get('current', [])

    # Modern format: prices directly in product
    if raw_keepa and ('buyBoxPrice' in raw_keepa or 'newPriceIsMAP' in raw_keepa):
        # Extract from modern format
        parsed['current_amazon_price'] = raw_keepa.get('amazonPrice')
        parsed['current_new_price'] = raw_keepa.get('newPrice')
        parsed['current_used_price'] = raw_keepa.get('usedPrice')
        parsed['current_list_price'] = raw_keepa.get('listPrice')
        parsed['current_fba_price'] = raw_keepa.get('fbaPrice')
        parsed['current_buybox_price'] = raw_keepa.get('buyBoxPrice')

        logger.debug(
            f"ASIN {asin}: Modern format - "
            f"New=${parsed['current_new_price']}, "
            f"Used=${parsed['current_used_price']}, "
            f"BSR={parsed['current_bsr']}"
        )
    # Legacy format: stats.current array
    elif current_array and len(current_array) > 0:
        # Using KeepaCSVType indices
        parsed['current_amazon_price'] = _extract_price(current_array, 0)
        parsed['current_new_price'] = _extract_price(current_array, 1)
        parsed['current_used_price'] = _extract_price(current_array, 2)
        # BSR already extracted above
        parsed['current_list_price'] = _extract_price(current_array, 4)
        parsed['current_fba_price'] = _extract_price(current_array, 10)
        parsed['current_buybox_price'] = _extract_price(current_array, 18) if len(current_array) > 18 else None

        logger.debug(
            f"ASIN {asin}: Legacy format - "
            f"Amazon=${parsed['current_amazon_price']}, "
            f"New=${parsed['current_new_price']}, "
            f"BSR={parsed['current_bsr']}"
        )
    else:
        parsed['errors'].append("No pricing data found (neither modern nor legacy format)")
        logger.warning(f"ASIN {asin}: No pricing data available")

    # Step 2: Extract offers with conditions (GAME CHANGER!)
    offers = raw_keepa.get('offers', [])
    if offers:
        offers_by_condition = _group_offers_by_condition(offers)
        parsed['offers_by_condition'] = offers_by_condition
        logger.debug(f"ASIN {asin}: Grouped {len(offers)} offers by condition")
    else:
        parsed['offers_by_condition'] = {}
        logger.debug(f"ASIN {asin}: No offers found")

    # Step 3: Extract price history from csv arrays
    csv = raw_keepa.get('csv', [])
    if csv and len(csv) > 10:
        # Raw arrays for compatibility
        parsed['history_new'] = csv[1] if len(csv) > 1 else None
        parsed['history_used'] = csv[2] if len(csv) > 2 else None
        parsed['history_fba'] = csv[10] if len(csv) > 10 else None

        # NEW: Extract structured history for advanced scoring
        # BSR history from csv[3] (SALES rank)
        bsr_csv = csv[3] if len(csv) > 3 else []
        if bsr_csv and isinstance(bsr_csv, list) and len(bsr_csv) > 0:
            parsed['bsr_history'] = _parse_csv_to_timeseries(bsr_csv, is_price=False)
            logger.debug(f"ASIN {asin}: Extracted {len(parsed['bsr_history'])} BSR data points")
        else:
            parsed['bsr_history'] = []
            logger.debug(f"ASIN {asin}: No BSR history available")

        # Price history from csv[1] (NEW price)
        price_csv = csv[1] if len(csv) > 1 else []
        if price_csv and isinstance(price_csv, list) and len(price_csv) > 0:
            parsed['price_history'] = _parse_csv_to_timeseries(price_csv, is_price=True)
            logger.debug(f"ASIN {asin}: Extracted {len(parsed['price_history'])} price data points")
        else:
            parsed['price_history'] = []
            logger.debug(f"ASIN {asin}: No price history available")

        logger.debug(f"ASIN {asin}: Extracted history arrays")
    else:
        # No CSV data available
        parsed['bsr_history'] = []
        parsed['price_history'] = []
        logger.warning(f"ASIN {asin}: No CSV data available for history extraction")

    # Step 4: Extract metadata
    parsed['category_tree'] = raw_keepa.get('categoryTree', [])
    parsed['rating'] = _extract_rating(current_array) if current_array and len(current_array) > 15 else None
    parsed['review_count'] = _extract_integer(current_array, 16) if current_array and len(current_array) > 16 else None

    logger.info(f"[OK] ASIN {asin}: Unified parse complete - offers_by_condition: {list(parsed['offers_by_condition'].keys())}")

    return parsed


def _parse_csv_to_timeseries(csv_array: List[int], is_price: bool = True) -> List[Tuple[int, float]]:
    """
    Parse Keepa CSV array to timeseries [(timestamp_minutes, value), ...].

    Args:
        csv_array: Keepa CSV array format [timestamp1, value1, timestamp2, value2, ...]
        is_price: If True, divide value by 100 (prices in cents). If False, keep as-is (BSR).

    Returns:
        List of (timestamp_minutes, value) tuples
    """
    if not csv_array or not isinstance(csv_array, list):
        return []

    timeseries = []
    try:
        # Keepa CSV format: [timestamp1, value1, timestamp2, value2, ...]
        # Timestamps are in minutes since Keepa epoch (21 Oct 2000 00:00 UTC)
        for i in range(0, len(csv_array) - 1, 2):
            timestamp = csv_array[i]
            value = csv_array[i + 1]

            # Skip invalid values
            if value is None or value == KEEPA_NULL_VALUE or value == -1:
                continue

            # Convert price from cents to dollars if needed
            if is_price:
                value_converted = float(value) / KEEPA_PRICE_DIVISOR
            else:
                value_converted = float(value)

            timeseries.append((timestamp, value_converted))

        return timeseries

    except (IndexError, ValueError, TypeError) as e:
        logger.warning(f"Error parsing CSV to timeseries: {e}")
        return []


def _extract_price(array: List, index: int) -> Optional[float]:
    """Extract price from array at index, convert from cents to dollars."""
    if index >= len(array):
        return None

    value = array[index]
    if value is None or value == KEEPA_NULL_VALUE or value == -1:
        return None

    try:
        return float(value) / KEEPA_PRICE_DIVISOR
    except (ValueError, TypeError):
        return None


def _extract_integer(array: List, index: int) -> Optional[int]:
    """Extract integer from array at index."""
    if index >= len(array):
        return None

    value = array[index]
    if value is None or value == KEEPA_NULL_VALUE or value == -1:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _extract_rating(array: List) -> Optional[float]:
    """Extract rating from array index 15 (Keepa stores as 0-50, we convert to 0-5)."""
    if len(array) <= 15:
        return None

    value = array[15]
    if value is None or value == KEEPA_NULL_VALUE or value == -1:
        return None

    try:
        # Keepa stores rating as 0-50 (e.g., 45 = 4.5 stars)
        rating_raw = int(value)
        return rating_raw / 10.0
    except (ValueError, TypeError):
        return None


def _group_offers_by_condition(offers: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Group offers by condition (NEW, VERY_GOOD, GOOD, ACCEPTABLE).
    Extract minimum price per condition.

    Conditions (from Keepa):
    - 1 = NEW
    - 3 = Used - Very Good
    - 4 = Used - Good
    - 5 = Used - Acceptable
    """
    conditions_map = {
        1: ('new', 'New'),
        3: ('very_good', 'Used - Very Good'),
        4: ('good', 'Used - Good'),
        5: ('acceptable', 'Used - Acceptable')
    }

    grouped = {}

    for condition_id, (condition_key, condition_label) in conditions_map.items():
        # Find all offers with this condition
        offers_for_condition = [
            o for o in offers
            if o.get('condition') == condition_id
        ]

        if offers_for_condition:
            # Extract the minimum price offer
            min_offer = _find_minimum_price_offer(offers_for_condition)

            if min_offer:
                # Extract price from offerCSV (latest price is first entry)
                offer_csv = min_offer.get('offerCSV', [])
                min_price_cents = None

                if offer_csv:
                    # offerCSV format: [[timestamp, price_cents, shipping_cents], ...]
                    # Latest is first
                    if isinstance(offer_csv[0], (list, tuple)) and len(offer_csv[0]) >= 2:
                        min_price_cents = offer_csv[0][1]

                if min_price_cents is not None:
                    min_price_dollars = min_price_cents / KEEPA_PRICE_DIVISOR
                else:
                    min_price_dollars = None

                # Count FBA offers
                fba_count = sum(1 for o in offers_for_condition if o.get('isFBA'))

                grouped[condition_key] = {
                    'condition_id': condition_id,
                    'condition_label': condition_label,
                    'minimum_price': min_price_dollars,
                    'minimum_price_cents': min_price_cents,
                    'seller_count': len(offers_for_condition),
                    'fba_count': fba_count,
                    'sample_offer': {
                        'seller_id': min_offer.get('sellerId'),
                        'is_fba': min_offer.get('isFBA'),
                        'is_prime': min_offer.get('isPrime'),
                        'is_amazon': min_offer.get('isAmazon'),
                        'shipping_cents': min_price_cents if offer_csv and isinstance(offer_csv[0], (list, tuple)) and len(offer_csv[0]) > 2 else 0
                    }
                }

    return grouped


def _find_minimum_price_offer(offers: List[Dict]) -> Optional[Dict]:
    """Find offer with minimum price from a list of offers."""
    if not offers:
        return None

    def get_price(offer):
        """Extract latest price from offer."""
        offer_csv = offer.get('offerCSV', [])
        if offer_csv and isinstance(offer_csv[0], (list, tuple)) and len(offer_csv[0]) >= 2:
            return offer_csv[0][1]
        return float('inf')  # Invalid offers get highest price

    return min(offers, key=get_price)


# Backward compatibility exports
__all__ = [
    'parse_keepa_product',
    'parse_keepa_product_unified',
    'KeepaRawParser',
    'KeepaBSRExtractor',
    'KeepaCSVType'
]