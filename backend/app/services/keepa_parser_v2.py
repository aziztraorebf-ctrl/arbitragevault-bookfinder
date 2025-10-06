"""
Keepa API Response Parser v2.0 - Production-ready with enhanced BSR extraction
================================================================================
Refactored version with proper BSR extraction pattern following official Keepa documentation.

Author: Claude Opus 4.1 + Context7 Validation
Date: October 2025
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import logging
from enum import IntEnum

from app.models.keepa_models import ProductStatus
from app.core.calculations import VelocityData


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
        Extract current values from stats.current[] array.

        Args:
            raw_data: Raw Keepa API response

        Returns:
            Dictionary with current values (prices, BSR, counts)
        """
        current_values = {}

        # Primary source: stats.current[] array
        stats = raw_data.get("stats", {})
        current_array = stats.get("current", [])

        if not current_array or not isinstance(current_array, list):
            logger.warning(f"ASIN {raw_data.get('asin', 'unknown')}: stats.current[] not available")
            return current_values

        # Extract values using official indices
        extractors = [
            (KeepaCSVType.AMAZON, "amazon_price", True),           # Convert to price
            (KeepaCSVType.NEW, "new_price", True),                 # Convert to price
            (KeepaCSVType.USED, "used_price", True),               # Convert to price
            (KeepaCSVType.SALES, "bsr", False),                    # Keep as integer
            (KeepaCSVType.LISTPRICE, "list_price", True),          # Convert to price
            (KeepaCSVType.NEW_FBA, "fba_price", True),             # Convert to price
            (KeepaCSVType.BUY_BOX_SHIPPING, "buybox_price", True), # Convert to price
            (KeepaCSVType.COUNT_NEW, "new_count", False),          # Keep as integer
            (KeepaCSVType.COUNT_USED, "used_count", False),        # Keep as integer
            (KeepaCSVType.RATING, "rating", False),                # Keep as integer (0-50)
            (KeepaCSVType.COUNT_REVIEWS, "review_count", False),   # Keep as integer
        ]

        for idx, key, is_price in extractors:
            if len(current_array) > idx:
                value = current_array[idx]
                if value is not None and value != -1:
                    if is_price:
                        current_values[key] = KeepaRawParser._convert_price(value)
                    else:
                        current_values[key] = int(value)
                    logger.debug(f"Extracted {key}: {current_values[key]}")

        return current_values

    @staticmethod
    def extract_history_arrays(raw_data: Dict[str, Any], days_back: int = 90) -> Dict[str, List[Tuple]]:
        """
        Extract historical data from csv[][] arrays.

        Args:
            raw_data: Raw Keepa API response
            days_back: Number of days of history to extract

        Returns:
            Dictionary with history arrays (bsr_history, price_history, etc.)
        """
        history_data = {}
        csv_data = raw_data.get("csv", [])

        if not csv_data or not isinstance(csv_data, list):
            logger.warning(f"ASIN {raw_data.get('asin', 'unknown')}: csv[] data not available")
            return history_data

        # Calculate cutoff timestamp
        cutoff_date = datetime.now() - timedelta(days=days_back)
        keepa_cutoff = KeepaRawParser._datetime_to_keepa(cutoff_date)

        # Extract BSR history from csv[3]
        if len(csv_data) > KeepaCSVType.SALES and csv_data[KeepaCSVType.SALES]:
            bsr_history = KeepaRawParser._parse_time_series(
                csv_data[KeepaCSVType.SALES],
                keepa_cutoff,
                convert_price=False
            )
            history_data["bsr_history"] = bsr_history
            logger.debug(f"Extracted {len(bsr_history)} BSR data points")

        # Extract price history from csv[0] (Amazon price)
        if len(csv_data) > KeepaCSVType.AMAZON and csv_data[KeepaCSVType.AMAZON]:
            price_history = KeepaRawParser._parse_time_series(
                csv_data[KeepaCSVType.AMAZON],
                keepa_cutoff,
                convert_price=True
            )
            history_data["price_history"] = price_history
            logger.debug(f"Extracted {len(price_history)} price data points")

        # Extract Buy Box history from csv[18]
        if len(csv_data) > KeepaCSVType.BUY_BOX_SHIPPING and csv_data[KeepaCSVType.BUY_BOX_SHIPPING]:
            buybox_history = KeepaRawParser._parse_time_series(
                csv_data[KeepaCSVType.BUY_BOX_SHIPPING],
                keepa_cutoff,
                convert_price=True
            )
            history_data["buybox_history"] = buybox_history

        # Extract offer count history from csv[11]
        if len(csv_data) > KeepaCSVType.COUNT_NEW and csv_data[KeepaCSVType.COUNT_NEW]:
            offers_history = KeepaRawParser._parse_time_series(
                csv_data[KeepaCSVType.COUNT_NEW],
                keepa_cutoff,
                convert_price=False
            )
            history_data["offers_history"] = offers_history

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

        # Strategy 1: Primary source - stats.current[3]
        stats = raw_data.get("stats", {})
        current = stats.get("current", [])

        if current and len(current) > KeepaCSVType.SALES:
            bsr = current[KeepaCSVType.SALES]
            if bsr and bsr != -1:
                logger.info(f"ASIN {asin}: BSR {bsr} from stats.current[3]")
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


def _determine_best_current_price(data: Dict[str, Any]) -> Optional[Decimal]:
    """
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
        if price and price > 0:
            return price

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