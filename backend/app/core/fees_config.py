"""
Amazon Fee Configuration - Books category defaults and calculation logic.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FeeConfig:
    """Amazon fee configuration for a category."""
    
    category: str
    referral_fee_pct: Decimal  # Percentage (15 = 15%)
    closing_fee: Decimal       # Fixed fee per item
    fba_fee_base: Decimal      # Base FBA fee
    fba_fee_per_lb: Decimal    # Additional fee per pound
    inbound_shipping: Decimal  # Inbound shipping per item
    prep_fee: Decimal          # Prep fee per item
    tax_pct: Decimal          # Tax percentage (0 = no tax)


# Default fee configurations by category
DEFAULT_FEES: Dict[str, FeeConfig] = {
    "books": FeeConfig(
        category="books",
        referral_fee_pct=Decimal("15.0"),     # 15% referral fee for books
        closing_fee=Decimal("1.80"),          # $1.80 closing fee
        fba_fee_base=Decimal("2.50"),         # Base FBA fee
        fba_fee_per_lb=Decimal("0.40"),       # $0.40 per pound additional
        inbound_shipping=Decimal("0.40"),     # $0.40 inbound shipping
        prep_fee=Decimal("0.20"),             # $0.20 prep fee
        tax_pct=Decimal("0.0")                # No tax for simplicity
    ),
    "media": FeeConfig(
        category="media", 
        referral_fee_pct=Decimal("15.0"),
        closing_fee=Decimal("1.80"),
        fba_fee_base=Decimal("2.50"),
        fba_fee_per_lb=Decimal("0.40"), 
        inbound_shipping=Decimal("0.35"),
        prep_fee=Decimal("0.15"),
        tax_pct=Decimal("0.0")
    ),
    "default": FeeConfig(
        category="default",
        referral_fee_pct=Decimal("15.0"),     # Conservative 15%
        closing_fee=Decimal("1.80"),
        fba_fee_base=Decimal("3.00"),         # Higher base for unknown
        fba_fee_per_lb=Decimal("0.50"),
        inbound_shipping=Decimal("0.50"),
        prep_fee=Decimal("0.25"),
        tax_pct=Decimal("0.0")
    )
}


def get_fee_config(category: str = "books") -> FeeConfig:
    """
    Get fee configuration for a category.
    
    Args:
        category: Product category (books, media, etc.)
        
    Returns:
        FeeConfig for the category, defaulting to "books"
    """
    # Normalize category
    category = category.lower().strip()
    
    # Check for books-related categories
    if any(keyword in category for keyword in ["book", "textbook", "manual", "guide"]):
        return DEFAULT_FEES["books"]
    
    # Check for media categories  
    if any(keyword in category for keyword in ["cd", "dvd", "vinyl", "music", "movie"]):
        return DEFAULT_FEES["media"]
    
    # Return specific category or default
    return DEFAULT_FEES.get(category, DEFAULT_FEES["default"])


def calculate_total_fees(
    sell_price: Decimal,
    weight_lbs: Decimal = Decimal("1.0"), 
    category: str = "books"
) -> Dict[str, Decimal]:
    """
    Calculate all Amazon fees for a product.
    
    Args:
        sell_price: Target selling price
        weight_lbs: Product weight in pounds
        category: Product category for fee lookup
        
    Returns:
        Dictionary with fee breakdown and total
    """
    config = get_fee_config(category)
    
    # Calculate individual fees
    referral_fee = sell_price * (config.referral_fee_pct / Decimal("100"))
    closing_fee = config.closing_fee
    fba_fee = config.fba_fee_base + (weight_lbs * config.fba_fee_per_lb)
    inbound_shipping = config.inbound_shipping
    prep_fee = config.prep_fee
    tax_amount = sell_price * (config.tax_pct / Decimal("100"))
    
    total_fees = referral_fee + closing_fee + fba_fee + inbound_shipping + prep_fee + tax_amount
    
    return {
        "referral_fee": referral_fee,
        "closing_fee": closing_fee, 
        "fba_fee": fba_fee,
        "inbound_shipping": inbound_shipping,
        "prep_fee": prep_fee,
        "tax_amount": tax_amount,
        "total_fees": total_fees,
        "category_used": config.category
    }


def calculate_profit_metrics(
    sell_price: Decimal,
    buy_cost: Decimal,
    weight_lbs: Decimal = Decimal("1.0"),
    category: str = "books",
    buffer_pct: Decimal = Decimal("5.0"),
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive profit metrics.
    
    Args:
        sell_price: Target selling price
        buy_cost: Cost to acquire the item
        weight_lbs: Product weight in pounds
        category: Product category
        buffer_pct: Safety buffer percentage
        
    Returns:
        Complete profit analysis dictionary
    """
    # Get config parameters (use defaults if not provided)
    if config:
        buffer_from_config = config.get("fees", {}).get("buffer_pct_default", float(buffer_pct))
        buffer_pct = Decimal(str(buffer_from_config))
        
        target_roi_from_config = config.get("roi", {}).get("target_pct_default", 30.0)
        target_roi = Decimal(str(target_roi_from_config))
    else:
        target_roi = Decimal("30.0")  # Default fallback
    
    # Calculate fees
    fees = calculate_total_fees(sell_price, weight_lbs, category)
    total_fees = fees["total_fees"]
    
    # Apply safety buffer
    buffer_amount = sell_price * (buffer_pct / Decimal("100"))
    
    # Core profit calculations
    net_profit = sell_price - total_fees - buy_cost - buffer_amount
    roi_percentage = (net_profit / buy_cost * Decimal("100")) if buy_cost > 0 else Decimal("0")
    margin_percentage = (net_profit / sell_price * Decimal("100")) if sell_price > 0 else Decimal("0")
    
    # Pricing targets (using config target ROI)
    target_profit_needed = buy_cost * (target_roi / Decimal("100"))
    target_buy_price = sell_price - total_fees - target_profit_needed - buffer_amount
    
    # Breakeven analysis
    breakeven_price = total_fees + buffer_amount  # Buy cost that results in $0 profit
    
    return {
        # Input parameters
        "sell_price": sell_price,
        "buy_cost": buy_cost,
        "weight_lbs": weight_lbs,
        "category": category,
        "buffer_pct": buffer_pct,
        "buffer_amount": buffer_amount,
        
        # Fee breakdown
        "fees": fees,
        
        # Core metrics
        "net_profit": net_profit,
        "roi_percentage": roi_percentage,
        "margin_percentage": margin_percentage,
        
        # Pricing targets
        "target_buy_price": target_buy_price,
        "breakeven_price": breakeven_price,
        
        # Status flags
        "is_profitable": net_profit > 0,
        "meets_target_roi": roi_percentage >= target_roi,
        "profit_tier": _get_profit_tier(roi_percentage, config),
        
        # Config audit trail
        "config_applied": {
            "target_roi_used": float(target_roi),
            "buffer_pct_used": float(buffer_pct),
            "config_source": "provided" if config else "default"
        }
    }


def _get_profit_tier(roi_percentage: Decimal, config: Optional[Dict[str, Any]] = None) -> str:
    """Categorize ROI into tiers using config thresholds."""
    roi_pct = float(roi_percentage)
    
    # Get thresholds from config or use defaults
    if config and "roi" in config:
        roi_config = config["roi"]
        excellent = roi_config.get("excellent_threshold", 50.0)
        good = roi_config.get("good_threshold", 30.0)
        fair = roi_config.get("fair_threshold", 15.0)
    else:
        # Default thresholds
        excellent = 50.0
        good = 30.0
        fair = 15.0
    
    if roi_pct >= excellent:
        return "excellent"
    elif roi_pct >= good:
        return "good"
    elif roi_pct >= fair:
        return "fair" 
    elif roi_pct > 0:
        return "poor"
    else:
        return "loss"