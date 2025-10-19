"""
Pricing Service for unified product analysis.
Handles USED vs NEW pricing breakdown and calculations.

Phase 2 (UNIFIED): calculate_pricing_metrics_unified() for ROI per condition
- Replaces old pricing_breakdown approach with condition-based metrics
- Calculates ROI for each condition (new, very_good, good, acceptable)
- Identifies recommended condition based on ROI
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Constants from keepa_parser_v2.py
KEEPA_PRICE_DIVISOR = 100  # Keepa stores prices in cents


# ============================================================================
# PHASE 2: UNIFIED PRICING METRICS - Calculate ROI per condition
# ============================================================================

def calculate_pricing_metrics_unified(
    parsed_data: Dict[str, Any],
    source_price: float,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    UNIFIED pricing metrics calculation - Used by ALL endpoints.

    Calculates ROI for EACH condition (new, very_good, good, acceptable)
    from parsed unified Keepa data.

    Args:
        parsed_data: Output from parse_keepa_product_unified()
                    Must contain 'offers_by_condition' key
        source_price: Acquisition/source price (in dollars)
        config: Configuration dict with:
               - amazon_fee_pct: Amazon fees percentage (default 0.15)
               - shipping_cost: Shipping cost in dollars (default 3.0)

    Returns:
        Dict[condition_key] -> {
            'market_price': float,           # Minimum available price for condition
            'roi_pct': float,                # Return on investment percentage
            'roi_value': float,              # Profit in dollars
            'profit_margin': float,          # Profit margin after fees
            'seller_count': int,             # Number of sellers for condition
            'fba_count': int,                # Number of FBA sellers
            'is_recommended': bool,          # True if best ROI
            'net_revenue': float,            # Revenue after fees
            'amazon_fees': float,            # Amazon fee amount
        }

    Example:
        metrics = calculate_pricing_metrics_unified(
            parsed_data={'offers_by_condition': {...}},
            source_price=2.50,
            config={'amazon_fee_pct': 0.15, 'shipping_cost': 3.0}
        )
        # Returns: {'good': {..., 'is_recommended': True}, 'new': {...}, ...}
    """
    offers_by_condition = parsed_data.get('offers_by_condition', {})

    if not offers_by_condition:
        logger.warning("[UNIFIED_PRICING] No offers by condition found")
        return {}

    # Get config values with defaults
    amazon_fee_pct = config.get('amazon_fee_pct', 0.15)
    shipping_cost = config.get('shipping_cost', 3.0)

    # Calculate ROI for each condition
    results = {}
    for condition_key, condition_data in offers_by_condition.items():
        # Extract minimum price (stored in cents, convert to dollars)
        min_price_cents = condition_data.get('minimum_price_cents')

        # If minimum_price_cents not present, try 'minimum_price' (might be dollars already)
        if min_price_cents is None:
            min_price_dollars = condition_data.get('minimum_price')
            if min_price_dollars is None:
                continue
        else:
            min_price_dollars = min_price_cents / KEEPA_PRICE_DIVISOR

        # Calculate ROI for this condition
        roi_data = _calculate_roi_for_condition(
            market_price=min_price_dollars,
            source_price=source_price,
            amazon_fee_pct=amazon_fee_pct,
            shipping_cost=shipping_cost
        )

        # Add condition-specific metadata
        results[condition_key] = {
            'market_price': min_price_dollars,
            'seller_count': condition_data.get('seller_count', 0),
            'fba_count': condition_data.get('fba_count', 0),
            'condition_label': condition_data.get('condition_label'),
            **roi_data  # Unpack roi_pct, roi_value, etc.
        }

    # Determine recommended condition (best ROI)
    if results:
        best_condition_key = max(
            results.keys(),
            key=lambda x: results[x].get('roi_pct', -999)
        )

        for condition_key in results:
            results[condition_key]['is_recommended'] = (
                condition_key == best_condition_key
            )

        logger.info(
            f"[UNIFIED_PRICING] Recommended: {best_condition_key} "
            f"(ROI: {results[best_condition_key]['roi_pct']*100:.1f}%)"
        )
    else:
        logger.warning("[UNIFIED_PRICING] No conditions with valid prices")

    return results


def _calculate_roi_for_condition(
    market_price: float,
    source_price: float,
    amazon_fee_pct: float = 0.15,
    shipping_cost: float = 3.0
) -> Dict[str, Any]:
    """
    Calculate ROI metrics for a single condition/price point.

    Formula:
        amazon_fees = market_price * amazon_fee_pct
        net_revenue = market_price - amazon_fees - shipping_cost
        roi_value = net_revenue - source_price
        roi_pct = (roi_value / source_price) * 100

    Args:
        market_price: Selling price in dollars
        source_price: Acquisition cost in dollars
        amazon_fee_pct: Fee percentage (0.15 = 15%)
        shipping_cost: Shipping cost in dollars

    Returns:
        Dict with ROI metrics:
        - roi_pct: Percentage return (can be negative)
        - roi_value: Dollar profit (can be negative)
        - profit_margin: Margin on selling price
        - net_revenue: Revenue after all costs
        - amazon_fees: Fee amount
    """
    if source_price <= 0:
        logger.warning("[ROI_CALC] Invalid source_price")
        return {
            'roi_pct': 0,
            'roi_value': 0,
            'profit_margin': 0,
            'net_revenue': market_price,
            'amazon_fees': market_price * amazon_fee_pct
        }

    # Calculate fees and net revenue
    amazon_fees = market_price * amazon_fee_pct
    net_revenue = market_price - amazon_fees - shipping_cost

    # Calculate ROI
    roi_value = net_revenue - source_price
    roi_pct = (roi_value / source_price)  # As decimal (multiply by 100 for percentage)

    # Calculate profit margin
    profit_margin = (roi_value / market_price) if market_price > 0 else 0

    return {
        'roi_pct': roi_pct,
        'roi_value': roi_value,
        'profit_margin': profit_margin,
        'net_revenue': net_revenue,
        'amazon_fees': amazon_fees
    }


def compute_pricing_breakdown(
    parsed_data: Dict[str, Any],
    amazon_check: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute comprehensive pricing breakdown for USED vs NEW books.

    Args:
        parsed_data: Parsed Keepa product data containing prices
        amazon_check: Amazon presence check results

    Returns:
        Dict with pricing breakdown including:
        - used_price: Current USED price from Keepa
        - new_price: Current NEW price from Keepa
        - market_sell_price: Best available selling price (USED or NEW)
        - pricing_source: Which price was selected ("USED" or "NEW")
        - has_used_offers: Boolean indicating USED availability
        - has_new_offers: Boolean indicating NEW availability
    """

    # Extract prices from parsed data
    used_price = parsed_data.get("current_used_price")
    new_price = parsed_data.get("current_new_price")

    # Log pricing data for debugging
    logger.info(f"[PRICING] Raw prices - USED: {used_price}, NEW: {new_price}")

    # Determine availability
    has_used_offers = used_price is not None and used_price > 0
    has_new_offers = new_price is not None and new_price > 0

    # Determine market sell price (prefer USED for better margins)
    if has_used_offers:
        market_sell_price = used_price
        pricing_source = "USED"
        logger.info(f"[PRICING] Using USED price: ${used_price:.2f}")
    elif has_new_offers:
        market_sell_price = new_price
        pricing_source = "NEW"
        logger.info(f"[PRICING] Using NEW price: ${new_price:.2f}")
    else:
        # No prices available
        market_sell_price = None
        pricing_source = None
        logger.warning("[PRICING] No prices available (USED or NEW)")

    # Build pricing breakdown
    pricing_breakdown = {
        "used_price": used_price,
        "new_price": new_price,
        "market_sell_price": market_sell_price,
        "pricing_source": pricing_source,
        "has_used_offers": has_used_offers,
        "has_new_offers": has_new_offers
    }

    # Add Amazon-specific pricing info if available
    if amazon_check.get("has_buybox"):
        pricing_breakdown["amazon_buybox_price"] = amazon_check.get("buybox_price")
        pricing_breakdown["amazon_listing_active"] = amazon_check.get("listing_active", False)

    return pricing_breakdown


def calculate_roi_metrics(
    pricing_breakdown: Dict[str, Any],
    source_price: float,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate ROI metrics based on pricing breakdown and source price.

    Args:
        pricing_breakdown: Pricing breakdown from compute_pricing_breakdown()
        source_price: The acquisition/source price of the book
        config: Configuration with fees and multipliers

    Returns:
        Dict with ROI metrics including:
        - current_roi_pct: Percentage ROI
        - current_roi_value: Dollar value ROI
        - profit_margin: Profit margin after fees
        - meets_roi_threshold: Boolean if ROI meets minimum
    """

    market_sell_price = pricing_breakdown.get("market_sell_price")

    if not market_sell_price or not source_price:
        return {
            "current_roi_pct": None,
            "current_roi_value": None,
            "profit_margin": None,
            "meets_roi_threshold": False
        }

    # Get fee configuration
    amazon_fee_pct = config.get("amazon_fee_pct", 0.15)  # 15% default
    shipping_cost = config.get("shipping_cost", 3.0)  # $3 default
    min_roi_threshold = config.get("min_roi_threshold", 0.30)  # 30% default

    # Calculate net revenue after Amazon fees
    amazon_fees = market_sell_price * amazon_fee_pct
    net_revenue = market_sell_price - amazon_fees - shipping_cost

    # Calculate ROI
    roi_value = net_revenue - source_price
    roi_pct = (roi_value / source_price) if source_price > 0 else 0

    # Calculate profit margin
    profit_margin = (roi_value / market_sell_price) if market_sell_price > 0 else 0

    # Check if meets threshold
    meets_threshold = roi_pct >= min_roi_threshold

    logger.info(
        f"[ROI] Sell: ${market_sell_price:.2f}, "
        f"Source: ${source_price:.2f}, "
        f"ROI: {roi_pct*100:.1f}%, "
        f"Meets threshold: {meets_threshold}"
    )

    return {
        "current_roi_pct": roi_pct,
        "current_roi_value": roi_value,
        "profit_margin": profit_margin,
        "meets_roi_threshold": meets_threshold,
        "net_revenue": net_revenue,
        "amazon_fees": amazon_fees,
        "shipping_cost": shipping_cost
    }


def calculate_velocity_score(
    parsed_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate velocity score based on sales rank history.

    Args:
        parsed_data: Parsed Keepa data with sales history
        config: Optional configuration for velocity thresholds

    Returns:
        Dict with velocity metrics including:
        - velocity_score: Numeric score (0-100)
        - velocity_category: "fast", "medium", or "slow"
        - avg_daily_sales: Estimated daily sales
    """

    # Get BSR for velocity calculation
    current_bsr = parsed_data.get("current_bsr")

    if not current_bsr or current_bsr <= 0:
        return {
            "velocity_score": 0,
            "velocity_category": "unknown",
            "avg_daily_sales": None
        }

    # Default thresholds (can be overridden by config)
    if not config:
        config = {}

    fast_threshold = config.get("velocity_fast_bsr", 100000)  # BSR < 100k = fast
    medium_threshold = config.get("velocity_medium_bsr", 500000)  # BSR < 500k = medium

    # Calculate velocity score (inverse of BSR, scaled 0-100)
    if current_bsr <= fast_threshold:
        velocity_score = 100 - (current_bsr / fast_threshold * 30)  # 70-100 score
        velocity_category = "fast"
        # Rough estimate: top 100k books sell 1-10 copies/day
        avg_daily_sales = 10 - (current_bsr / fast_threshold * 9)
    elif current_bsr <= medium_threshold:
        velocity_score = 70 - ((current_bsr - fast_threshold) / (medium_threshold - fast_threshold) * 40)  # 30-70 score
        velocity_category = "medium"
        # Rough estimate: 100k-500k books sell 0.1-1 copies/day
        avg_daily_sales = 1 - ((current_bsr - fast_threshold) / (medium_threshold - fast_threshold) * 0.9)
    else:
        velocity_score = 30 - min(30, (current_bsr - medium_threshold) / 1000000 * 30)  # 0-30 score
        velocity_category = "slow"
        # Rough estimate: 500k+ books sell < 0.1 copies/day
        avg_daily_sales = 0.1 * (500000 / current_bsr) if current_bsr > 0 else 0

    logger.info(
        f"[VELOCITY] BSR: {current_bsr}, "
        f"Score: {velocity_score:.1f}, "
        f"Category: {velocity_category}, "
        f"Est. daily sales: {avg_daily_sales:.2f}"
    )

    return {
        "velocity_score": round(velocity_score, 1),
        "velocity_category": velocity_category,
        "avg_daily_sales": round(avg_daily_sales, 2) if avg_daily_sales else None,
        "current_bsr": current_bsr
    }


def format_price_display(price: Optional[float]) -> str:
    """
    Format price for display with proper handling of None values.

    Args:
        price: Price value or None

    Returns:
        Formatted price string or "N/A"
    """
    if price is None or price <= 0:
        return "N/A"
    return f"${price:.2f}"