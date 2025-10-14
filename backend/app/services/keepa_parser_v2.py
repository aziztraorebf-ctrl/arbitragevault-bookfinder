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
        Extract current values from product['data'] arrays using keepa library format.

        The keepa Python library transforms API responses into structured data:
        - product['data']['NEW'] = array of New prices (latest = current)
        - product['data']['SALES'] = array of BSR values (latest = current)
        - product['data']['AMAZON'] = array of Amazon prices
        - etc.

        Args:
            raw_data: Keepa product dict from keepa.Keepa().query()

        Returns:
            Dictionary with current values (prices, BSR, counts)
        """
        current_values = {}
        asin = raw_data.get('asin', 'unknown')

        # Get 'data' section (created by keepa lib)
        data = raw_data.get('data', {})

        if not data:
            logger.warning(f"ASIN {asin}: 'data' section not available")
            return current_values

        # Helper to extract latest value from array (numpy or list)
        # Source verified: Keepa SDK v1.3.0 - numpy arrays with -1 for null
        def get_latest(key: str, is_price: bool = False) -> Optional[Any]:
            """
            Extract latest valid value from Keepa data array using numpy-safe helpers.

            Uses extract_latest_value() to avoid "ambiguous truth value" errors.
            """
            return extract_latest_value(data, key, is_price=is_price, null_value=KEEPA_NULL_VALUE)

        # Extract current values from data arrays
        extractors = [
            ('AMAZON', 'amazon_price', True),      # Amazon price
            ('NEW', 'new_price', True),            # New price
            ('USED', 'used_price', True),          # Used price
            ('SALES', 'bsr', False),               # BSR (Sales Rank) - INTEGER!
            ('LISTPRICE', 'list_price', True),     # List price
            ('NEW_FBA', 'fba_price', True),        # FBA price
            ('BUY_BOX_SHIPPING', 'buybox_price', True),  # Buy Box price
            ('COUNT_NEW', 'new_count', False),     # New offer count
            ('COUNT_USED', 'used_count', False),   # Used offer count
            ('RATING', 'rating', False),           # Rating (0-50)
            ('COUNT_REVIEWS', 'review_count', False),  # Review count
        ]

        for data_key, output_key, is_price in extractors:
            value = get_latest(data_key, is_price)
            if value is not None:
                current_values[output_key] = value
                logger.debug(f"ASIN {asin}: {output_key} = {value}")

        logger.info(f"✅ ASIN {asin}: Extracted {len(current_values)} current values from keepa lib format")

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
            logger.warning(f"ASIN {asin}: 'data' section not available")
            return history_data

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Helper to extract time series from keepa lib format
        def extract_series(value_key: str, time_key: str, is_price: bool = False) -> List[Tuple]:
            values = data.get(value_key)
            times = data.get(time_key)

            # ✅ Handle numpy arrays - check existence with 'is None', not 'not'
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

        logger.info(f"✅ ASIN {asin}: Extracted {len(history_data)} history series from keepa lib format")

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
    def _convert_price(keepa_price: int) -> Decimal:
        """Convert Keepa price (in cents) to Decimal dollars."""
        return Decimal(keepa_price) / Decimal(100)

    @staticmethod
    def _keepa_to_datetime(keepa_time: int) -> datetime:
        """Convert Keepa timestamp to Python datetime."""
        unix_ms = (keepa_time + 21564000) * 60000
        return datetime.fromtimestamp(unix_ms / 1000)

    @staticmethod
    def _datetime_to_keepa(dt: datetime) -> int:
        """Convert Python datetime to Keepa timestamp."""
        unix_ms = int(dt.timestamp() * 1000)
        return (unix_ms // 60000) - 21564000


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
        keepa_epoch = 971222400  # Keepa epoch: 21 Oct 2000 00:00:00 GMT

        # ═══════════════════════════════════════════════════════
        # PRIORITY 1: lastPriceChange (RECOMMENDED)
        # ═══════════════════════════════════════════════════════
        last_price_change = raw_data.get("lastPriceChange", -1)

        if last_price_change != -1:
            unix_timestamp = keepa_epoch + (last_price_change * 60)
            timestamp = datetime.fromtimestamp(unix_timestamp)

            # Verify timestamp is reasonable (< 30 days)
            age_days = (datetime.now() - timestamp).days
            if age_days < 30:
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
                            unix_timestamp = keepa_epoch + (last_timestamp_keepa * 60)
                            timestamp = datetime.fromtimestamp(unix_timestamp)

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
            unix_timestamp = keepa_epoch + (last_update * 60)
            timestamp = datetime.fromtimestamp(unix_timestamp)
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
    def extract_current_bsr(raw_data: Dict[str, Any]) -> Optional[int]:
        """
        Extract current BSR with multiple fallback strategies.

        Priority order:
        1. stats.current[3] (official current value)
        2. Last point from csv[3] history (if recent)
        3. stats.avg30[3] (30-day average as fallback)

        Args:
            raw_data: Raw Keepa API response

        Returns:
            Current BSR value or None if not available
        """
        asin = raw_data.get("asin", "unknown")

        # Strategy 1: Primary source - current[3]
        # ✅ Compatibilité Keepa nouvelle et ancienne structure
        current = raw_data.get("current")
        if not current:  # Fallback ancien format
            stats = raw_data.get("stats", {})
            current = stats.get("current", [])

        if current and len(current) > KeepaCSVType.SALES:
            bsr = current[KeepaCSVType.SALES]
            if bsr and bsr != -1:
                logger.info(f"ASIN {asin}: BSR {bsr} from current[3]")
                return int(bsr)

        # Strategy 2: Fallback to last historical point if recent
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

                    if age_hours <= 24:
                        logger.info(f"ASIN {asin}: BSR {last_value} from csv[3] history ({age_hours:.1f}h old)")
                        return int(last_value)
                    else:
                        logger.debug(f"ASIN {asin}: Historical BSR too old ({age_hours:.1f}h)")

        # Strategy 3: Use 30-day average if available
        avg30 = stats.get("avg30", [])
        if avg30 and len(avg30) > KeepaCSVType.SALES:
            avg_bsr = avg30[KeepaCSVType.SALES]
            if avg_bsr and avg_bsr != -1:
                logger.warning(f"ASIN {asin}: Using 30-day avg BSR {avg_bsr} as fallback")
                return int(avg_bsr)

        logger.warning(f"ASIN {asin}: No BSR data available from any source")
        return None

    @staticmethod
    def validate_bsr_quality(bsr: Optional[int], category: str = "unknown") -> Dict[str, Any]:
        """
        Validate BSR value and assess data quality.

        Args:
            bsr: BSR value to validate
            category: Product category for context

        Returns:
            Quality assessment with confidence score
        """
        if bsr is None:
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

        # Calculate confidence based on BSR value
        if bsr < 10_000:
            confidence = 1.0  # Top sellers have reliable BSR
        elif bsr < 100_000:
            confidence = 0.9
        elif bsr < 1_000_000:
            confidence = 0.7
        else:
            confidence = 0.5  # Lower confidence for high BSR

        return {
            "valid": True,
            "confidence": confidence,
            "reason": "BSR within expected range"
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

        # Extract BSR with enhanced logic
        extractor = KeepaBSRExtractor()
        current_bsr = extractor.extract_current_bsr(raw_data)
        product_data["current_bsr"] = current_bsr

        # Validate BSR quality
        bsr_validation = extractor.validate_bsr_quality(current_bsr, product_data["category"])
        product_data["bsr_confidence"] = bsr_validation["confidence"]

        if current_bsr:
            logger.info(f"✅ ASIN {asin}: BSR={current_bsr}, confidence={bsr_validation['confidence']:.2f}")
        else:
            logger.warning(f"⚠️ ASIN {asin}: No BSR available - {bsr_validation['reason']}")

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

        logger.info(f"✅ Successfully parsed {asin}: price=${product_data.get('current_price')}, BSR={current_bsr}")
        return product_data

    except Exception as e:
        logger.error(f"❌ Failed to parse Keepa product {asin}: {e}", exc_info=True)
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
        "current_buybox_price",  # ✅ Target for BuyBox competition (USED)
        "current_fba_price",     # ✅ FBA average if BuyBox missing
        "current_new_price",     # ⚠️ Fallback only
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
        "current_fba_price",    # ✅ FBA USED sellers (primary source)
        "lowest_offer_new",     # ⚠️ Fallback if USED unavailable
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


# Backward compatibility exports
__all__ = [
    'parse_keepa_product',
    'KeepaRawParser',
    'KeepaBSRExtractor',
    'KeepaCSVType'
]