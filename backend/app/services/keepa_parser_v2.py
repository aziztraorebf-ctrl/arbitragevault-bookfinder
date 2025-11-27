"""
Keepa API Response Parser v2.0 - Production-ready with enhanced BSR extraction
================================================================================
Refactored version with proper BSR extraction pattern following official Keepa documentation.

Author: Claude Opus 4.1 + Context7 Validation
Date: October 2025
Last Modified: 2025-11-27 - SRP refactor: split into modules
"""

from datetime import datetime
from decimal import Decimal
import decimal
from typing import Dict, List, Optional, Any, Tuple
import logging

from app.models.keepa_models import ProductStatus
from app.core.calculations import VelocityData
from app.utils.keepa_utils import (
    KEEPA_NULL_VALUE,
    KEEPA_PRICE_DIVISOR
)

# Import from new split modules
from app.services.keepa_constants import KeepaCSVType, KEEPA_CONDITION_CODES
from app.services.keepa_extractors import (
    KeepaRawParser,
    KeepaTimestampExtractor,
    KeepaBSRExtractor
)


# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    - Textbook: price >=40, BSR <=250k (high margin, slow rotation OK)
    - Velocity: price >=25, BSR <250k (modest margin, fast rotation)
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
    grouped = {}

    for condition_id, (condition_key, condition_label) in KEEPA_CONDITION_CODES.items():
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


# =============================================================================
# VELOCITY DATA HELPERS (migrated from keepa_parser.py)
# =============================================================================

def create_velocity_data_from_keepa(parsed_product: Dict[str, Any]) -> VelocityData:
    """
    Create VelocityData object from parsed Keepa product data.

    Args:
        parsed_product: Product data from parse_keepa_product()

    Returns:
        VelocityData object for velocity calculations
    """
    return VelocityData(
        current_bsr=parsed_product.get("current_bsr"),
        bsr_history=parsed_product.get("bsr_history", []),
        price_history=parsed_product.get("price_history", []),
        buybox_history=[],
        offers_history=[],
        category=parsed_product.get("category", "books")
    )


# Backward compatibility exports
__all__ = [
    'parse_keepa_product',
    'parse_keepa_product_unified',
    'KeepaRawParser',
    'KeepaBSRExtractor',
    'KeepaTimestampExtractor',
    'KeepaCSVType',
    'KEEPA_CONDITION_CODES',
    'create_velocity_data_from_keepa'
]
