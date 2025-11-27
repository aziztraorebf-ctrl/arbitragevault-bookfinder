"""
ROI Calculation Functions
=========================
Core ROI and profitability calculations for arbitrage analysis.

Separated from calculations.py for SRP compliance.
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional, Any

from .fees_config import calculate_profit_metrics, calculate_total_fees


def calculate_purchase_cost_from_strategy(
    sell_price: Decimal,
    strategy: str,
    config: Dict[str, Any]
) -> Decimal:
    """
    Calculate maximum purchase cost from strategy ROI target using inverse ROI formula.

    This function guarantees the exact ROI percentage defined in the strategy configuration
    by working backwards from the target ROI to calculate the maximum purchase price.

    Formula: buy_cost = (sell_price - fees - buffer) / (1 + roi_target/100)

    Args:
        sell_price: Target selling price (from Keepa current price)
        strategy: Strategy name ('aggressive', 'balanced', 'conservative')
        config: Business configuration containing strategy definitions

    Returns:
        Calculated purchase cost that guarantees target ROI

    Example:
        sell_price = $100, strategy = 'balanced' (roi_min: 25%)
        fees = $6.90, buffer = $5.00
        buy_cost = ($100 - $6.90 - $5.00) / (1 + 0.25) = $70.48
        Actual ROI = ($100 - $6.90 - $70.48 - $5.00) / $70.48 * 100 = 25%
    """
    # 1. Calculate all Amazon fees (referral, FBA, closing, etc.)
    fees_result = calculate_total_fees(sell_price, Decimal("1.0"), "books")
    total_fees = fees_result["total_fees"]

    # 2. Calculate 5% buffer amount
    buffer_amount = sell_price * Decimal("0.05")

    # 3. Get ROI target from strategy configuration
    strategies = config.get("strategies", {})
    strategy_config = strategies.get(strategy.lower(), {})
    roi_target = Decimal(str(strategy_config.get("roi_min", 30)))  # Default 30% if not found

    # 4. Apply inverse ROI formula
    # roi = (sell_price - fees - buy_cost - buffer) / buy_cost * 100
    # Solving for buy_cost: buy_cost = (sell_price - fees - buffer) / (1 + roi/100)
    numerator = sell_price - total_fees - buffer_amount
    denominator = Decimal("1") + (roi_target / Decimal("100"))
    purchase_cost = numerator / denominator

    # 5. Validation and fallback
    # If calculation produces invalid result, fallback to 50% of sell price
    if purchase_cost <= 0 or purchase_cost >= sell_price:
        purchase_cost = sell_price * Decimal("0.50")

    return purchase_cost


def calculate_max_buy_price(
    sell_price: Decimal,
    target_roi_pct: float = 35.0,
    category: str = "books",
    config: Optional[Dict[str, Any]] = None
) -> Decimal:
    """
    Calculate maximum buy price to achieve target ROI percentage.

    Used for Phase 2.5A hybrid solution - recommends max purchase price
    for user to find profitable arbitrage opportunities.

    Formula: max_buy = (sell_price - fees) / (1 + target_roi/100)

    Args:
        sell_price: Target selling price (from Keepa current market price)
        target_roi_pct: Desired ROI percentage (default 35%)
        category: Product category for fee calculation
        config: Optional business config

    Returns:
        Maximum buy price (Decimal) that achieves target ROI
        Returns 0 if calculation invalid (fees > sell price)

    Example:
        sell_price = $28.00, target_roi = 35%, fees = $6.90
        max_buy = (28.00 - 6.90) / 1.35 = $15.63

        If user buys at $15.63 and sells at $28.00:
        ROI = (28 - 6.90 - 15.63) / 15.63 x 100 = 35%
    """
    # Calculate Amazon fees (referral + FBA + closing)
    fees_result = calculate_total_fees(sell_price, Decimal("1.0"), category)
    total_fees = fees_result["total_fees"]

    # Check if fees exceed sell price (invalid scenario)
    if total_fees >= sell_price:
        return Decimal("0.00")

    # Apply inverse ROI formula
    # roi = (sell - fees - buy) / buy x 100
    # Solving for buy: buy = (sell - fees) / (1 + roi/100)
    numerator = sell_price - total_fees
    denominator = Decimal("1") + (Decimal(str(target_roi_pct)) / Decimal("100"))
    max_buy = numerator / denominator

    # Validation: max_buy must be positive and less than sell price
    if max_buy <= 0 or max_buy >= sell_price:
        return Decimal("0.00")

    return max_buy


def calculate_roi_metrics(
    current_price: Decimal,
    estimated_buy_cost: Decimal,
    product_weight_lbs: Decimal = Decimal("1.0"),
    category: str = "books",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate ROI and profitability metrics.

    Uses current market price as target sell price and estimates
    profit potential at given buy cost.

    Args:
        current_price: Current market price (potential sell price)
        estimated_buy_cost: Cost to acquire the item
        product_weight_lbs: Weight for FBA fee calculation
        category: Product category for fee lookup

    Returns:
        Complete ROI analysis
    """
    try:
        metrics = calculate_profit_metrics(
            sell_price=current_price,
            buy_cost=estimated_buy_cost,
            weight_lbs=product_weight_lbs,
            category=category,
            config=config
        )

        # Add additional ROI-specific fields
        metrics.update({
            "calculation_type": "roi_analysis",
            "timestamp": datetime.now().isoformat(),
            "confidence_level": _assess_roi_confidence(current_price, estimated_buy_cost)
        })

        return metrics

    except Exception as e:
        return {
            "error": f"ROI calculation failed: {str(e)}",
            "calculation_type": "roi_analysis",
            "timestamp": datetime.now().isoformat()
        }


def _assess_roi_confidence(current_price: Decimal, estimated_buy_cost: Decimal) -> str:
    """Assess confidence level in ROI calculation."""
    if current_price <= 0 or estimated_buy_cost <= 0:
        return "low"

    price_ratio = float(current_price / estimated_buy_cost)

    if price_ratio >= 3.0:      # 3x+ markup
        return "high"
    elif price_ratio >= 1.5:    # 1.5x+ markup
        return "medium"
    else:                       # < 1.5x markup
        return "low"


__all__ = [
    'calculate_purchase_cost_from_strategy',
    'calculate_max_buy_price',
    'calculate_roi_metrics',
]
