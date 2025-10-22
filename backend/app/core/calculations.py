"""
Core calculation engine for ROI, velocity, and business metrics.
"""

import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .fees_config import calculate_profit_metrics, get_fee_config, calculate_total_fees


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
        ROI = (28 - 6.90 - 15.63) / 15.63 × 100 = 35%
    """
    # Calculate Amazon fees (referral + FBA + closing)
    fees_result = calculate_total_fees(sell_price, Decimal("1.0"), category)
    total_fees = fees_result["total_fees"]

    # Check if fees exceed sell price (invalid scenario)
    if total_fees >= sell_price:
        return Decimal("0.00")

    # Apply inverse ROI formula
    # roi = (sell - fees - buy) / buy × 100
    # Solving for buy: buy = (sell - fees) / (1 + roi/100)
    numerator = sell_price - total_fees
    denominator = Decimal("1") + (Decimal(str(target_roi_pct)) / Decimal("100"))
    max_buy = numerator / denominator

    # Validation: max_buy must be positive and less than sell price
    if max_buy <= 0 or max_buy >= sell_price:
        return Decimal("0.00")

    return max_buy


@dataclass
class VelocityData:
    """Input data for velocity calculations."""
    current_bsr: Optional[int]
    bsr_history: List[Tuple[datetime, int]]  # (timestamp, bsr) pairs
    price_history: List[Tuple[datetime, float]]  # (timestamp, price) pairs  
    buybox_history: List[Tuple[datetime, bool]]  # (timestamp, has_buybox) pairs
    offers_history: List[Tuple[datetime, int]]   # (timestamp, offer_count) pairs
    category: str = "books"


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


def calculate_velocity_score(velocity_data: VelocityData, window_days: int = 30, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate velocity score (0-100) based on sales rank patterns and market activity.
    
    Higher scores indicate faster-moving products with better sales velocity.
    
    Args:
        velocity_data: Historical data for velocity analysis
        window_days: Analysis window in days
        
    Returns:
        Velocity analysis with score and component breakdown
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=window_days)
        
        # Filter data to window
        recent_bsr = [item for item in velocity_data.bsr_history if item[0] >= cutoff_date]
        recent_prices = [item for item in velocity_data.price_history if item[0] >= cutoff_date] 
        recent_buybox = [item for item in velocity_data.buybox_history if item[0] >= cutoff_date]
        recent_offers = [item for item in velocity_data.offers_history if item[0] >= cutoff_date]
        
        # Component 1: BSR Percentile Trend (0-30 points)
        rank_percentile_30d = _calculate_rank_percentile(recent_bsr, velocity_data.category, config)
        rank_percentile_score = min(rank_percentile_30d * 0.3, 30)
        
        # Component 2: BSR Improvement Frequency (0-25 points) 
        rank_drops_30d = _count_rank_improvements(recent_bsr)
        rank_improvement_score = min(rank_drops_30d * 2.5, 25)  # Max 10 improvements = 25 pts
        
        # Component 3: Buybox Availability (0-25 points)
        buybox_uptime_30d = _calculate_buybox_uptime(recent_buybox)
        buybox_score = buybox_uptime_30d * 0.25
        
        # Component 4: Price Stability (0-20 points)
        offers_volatility = _calculate_offers_volatility(recent_offers, recent_prices)
        stability_score = max(20 - (offers_volatility * 2), 0)  # Lower volatility = higher score
        
        # Calculate final velocity score
        velocity_score = rank_percentile_score + rank_improvement_score + buybox_score + stability_score
        velocity_score = min(max(velocity_score, 0), 100)  # Clamp to 0-100
        
        return {
            "velocity_score": round(float(velocity_score), 2),
            "rank_percentile_30d": round(rank_percentile_30d, 2),
            "rank_drops_30d": rank_drops_30d, 
            "buybox_uptime_30d": round(buybox_uptime_30d, 2),
            "offers_volatility": round(offers_volatility, 2),
            
            # Component scores (for debugging)
            "component_scores": {
                "rank_percentile_score": round(rank_percentile_score, 2),
                "rank_improvement_score": round(rank_improvement_score, 2), 
                "buybox_score": round(buybox_score, 2),
                "stability_score": round(stability_score, 2)
            },
            
            # Metadata
            "calculation_type": "velocity_analysis",
            "window_days": window_days,
            "data_points": {
                "bsr_points": len(recent_bsr),
                "price_points": len(recent_prices),
                "buybox_points": len(recent_buybox),
                "offers_points": len(recent_offers)
            },
            "timestamp": datetime.now().isoformat(),
            "velocity_tier": _get_velocity_tier(velocity_score, config)
        }
        
    except Exception as e:
        return {
            "error": f"Velocity calculation failed: {str(e)}",
            "velocity_score": 0,
            "calculation_type": "velocity_analysis",
            "timestamp": datetime.now().isoformat()
        }


def _calculate_rank_percentile(bsr_history: List[Tuple[datetime, int]], category: str, config: Optional[Dict[str, Any]] = None) -> float:
    """Calculate BSR percentile compared to category average."""
    if not bsr_history:
        return 0.0
        
    # Extract BSR values
    bsr_values = [item[1] for item in bsr_history if item[1] is not None]
    if not bsr_values:
        return 0.0
    
    avg_bsr = statistics.mean(bsr_values)
    
    # Get benchmarks from config or use defaults
    if config and "velocity" in config and "benchmarks" in config["velocity"]:
        benchmarks = config["velocity"]["benchmarks"]
    else:
        # Default benchmarks
        benchmarks = {
            "books": 100000,      # Books category median
            "media": 50000,       # Media category median  
            "default": 150000     # Conservative default
        }
    
    category_key = category.lower()
    benchmark = benchmarks.get(category_key, benchmarks.get("default", 150000))
    
    # Calculate percentile (lower BSR = higher percentile)
    if avg_bsr <= benchmark * 0.1:  # Top 10%
        return 90.0
    elif avg_bsr <= benchmark * 0.25:  # Top 25%
        return 75.0
    elif avg_bsr <= benchmark * 0.5:   # Top 50%
        return 50.0
    elif avg_bsr <= benchmark:         # Above median
        return 25.0
    else:                             # Below median
        return 10.0


def _count_rank_improvements(bsr_history: List[Tuple[datetime, int]]) -> int:
    """Count number of BSR improvements (rank decreases)."""
    if len(bsr_history) < 2:
        return 0
        
    # Sort by timestamp
    sorted_history = sorted(bsr_history, key=lambda x: x[0])
    
    improvements = 0
    for i in range(1, len(sorted_history)):
        current_rank = sorted_history[i][1]
        previous_rank = sorted_history[i-1][1]
        
        if current_rank is not None and previous_rank is not None:
            if current_rank < previous_rank:  # Lower number = better rank
                improvements += 1
    
    return improvements


def _calculate_buybox_uptime(buybox_history: List[Tuple[datetime, bool]]) -> float:
    """Calculate percentage of time buybox was available."""
    if not buybox_history:
        return 0.0
    
    buybox_available_count = sum(1 for item in buybox_history if item[1])
    total_points = len(buybox_history)
    
    return (buybox_available_count / total_points) * 100.0


def _calculate_offers_volatility(
    offers_history: List[Tuple[datetime, int]], 
    price_history: List[Tuple[datetime, float]]
) -> float:
    """Calculate market volatility based on offer count and price changes."""
    volatility_score = 0.0
    
    # Offers volatility (frequent changes in number of sellers)
    if len(offers_history) >= 2:
        offer_counts = [item[1] for item in offers_history if item[1] is not None]
        if offer_counts:
            offer_volatility = statistics.stdev(offer_counts) if len(offer_counts) > 1 else 0
            volatility_score += min(offer_volatility, 10)  # Cap at 10
    
    # Price volatility
    if len(price_history) >= 2:
        prices = [item[1] for item in price_history if item[1] is not None]
        if prices:
            price_volatility = statistics.stdev(prices) / statistics.mean(prices) * 100
            volatility_score += min(price_volatility, 10)  # Cap at 10
    
    return volatility_score


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


def _get_velocity_tier(velocity_score: float, config: Optional[Dict[str, Any]] = None) -> str:
    """Categorize velocity score into tiers using config thresholds."""
    
    # Get thresholds from config or use defaults
    if config and "velocity" in config:
        velocity_config = config["velocity"]
        fast = velocity_config.get("fast_threshold", 80.0)
        medium = velocity_config.get("medium_threshold", 60.0)
        slow = velocity_config.get("slow_threshold", 40.0)
    else:
        fast = 80.0
        medium = 60.0
        slow = 40.0
    
    if velocity_score >= fast:
        return "fast"
    elif velocity_score >= medium:
        return "medium"
    elif velocity_score >= slow:
        return "slow"
    else:
        return "very_slow"


def create_combined_analysis(
    current_price: Decimal,
    estimated_buy_cost: Decimal,
    velocity_data: VelocityData,
    product_weight_lbs: Decimal = Decimal("1.0")
) -> Dict[str, Any]:
    """
    Create comprehensive analysis combining ROI and velocity metrics.
    
    This is the main function for full product analysis.
    """
    # Calculate ROI metrics
    roi_metrics = calculate_roi_metrics(
        current_price=current_price,
        estimated_buy_cost=estimated_buy_cost,
        product_weight_lbs=product_weight_lbs,
        category=velocity_data.category
    )
    
    # Calculate velocity metrics
    velocity_metrics = calculate_velocity_score(velocity_data)
    
    # Create combined analysis
    analysis = {
        "analysis_type": "combined_roi_velocity",
        "timestamp": datetime.now().isoformat(),
        
        # ROI Analysis
        "roi_analysis": roi_metrics,
        
        # Velocity Analysis  
        "velocity_analysis": velocity_metrics,
        
        # Combined Scoring (with config)
        "combined_score": _calculate_combined_score(roi_metrics, velocity_metrics, config),
        "recommendation": _generate_recommendation(roi_metrics, velocity_metrics, config)
    }
    
    return analysis


def _calculate_combined_score(roi_metrics: Dict, velocity_metrics: Dict, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate weighted combined score from ROI and velocity."""
    try:
        roi_score = min(max(float(roi_metrics.get("roi_percentage", 0)), 0), 100)
        velocity_score = float(velocity_metrics.get("velocity_score", 0))
        
        # Get weights from config or use defaults
        if config and "combined_score" in config:
            roi_weight = config["combined_score"].get("roi_weight", 0.6)
            velocity_weight = config["combined_score"].get("velocity_weight", 0.4)
        else:
            roi_weight = 0.6
            velocity_weight = 0.4
        
        # Weighted average with config weights
        combined_score = (roi_score * roi_weight) + (velocity_score * velocity_weight)
        
        return {
            "combined_score": round(combined_score, 2),
            "roi_weight": roi_weight,
            "velocity_weight": velocity_weight,
            "roi_contribution": round(roi_score * roi_weight, 2),
            "velocity_contribution": round(velocity_score * velocity_weight, 2)
        }
    except:
        return {"combined_score": 0, "error": "Score calculation failed"}


def _generate_recommendation(roi_metrics: Dict, velocity_metrics: Dict, config: Optional[Dict[str, Any]] = None) -> str:
    """Generate business recommendation based on combined analysis."""
    try:
        roi_pct = float(roi_metrics.get("roi_percentage", 0))
        velocity_score = float(velocity_metrics.get("velocity_score", 0))
        is_profitable = roi_metrics.get("is_profitable", False)
        
        if not is_profitable:
            return "PASS - Not profitable"
        
        # Use config recommendation rules if available
        if config and "recommendation_rules" in config:
            rules = config["recommendation_rules"]
            
            for rule in rules:
                min_roi = rule.get("min_roi", 0)
                min_velocity = rule.get("min_velocity", 0)
                
                if roi_pct >= min_roi and velocity_score >= min_velocity:
                    label = rule.get("label", "UNKNOWN")
                    description = rule.get("description", "")
                    return f"{label} - {description}" if description else label
            
            return "PASS - Below configured thresholds"
        else:
            # Default fallback rules
            if roi_pct >= 30 and velocity_score >= 70:
                return "STRONG BUY - High profit, fast moving"
            elif roi_pct >= 20 and velocity_score >= 50:
                return "BUY - Good opportunity"  
            elif roi_pct >= 15 or velocity_score >= 60:
                return "CONSIDER - Monitor for better entry"
            else:
                return "PASS - Low profit/slow moving"
            
    except:
        return "UNKNOWN - Analysis incomplete"


# ============================================================================
# ADVANCED SCORING FUNCTIONS (v1.5.0) - SIMPLE FORMULAS + CONFIG-DRIVEN
# ============================================================================

def compute_advanced_velocity_score(bsr_history: List[Tuple[datetime, int]], config: Dict[str, Any]) -> Tuple[float, int, str, str]:
    """
    Calculate simplified velocity score (0-100) based on BSR trend.

    Args:
        bsr_history: List of (datetime, bsr) pairs
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure bsr_history is a list
    if not isinstance(bsr_history, list):
        return (0.5, 50, "unknown", "Invalid data type for bsr_history")

    try:
        velocity_config = config.get("advanced_scoring", {}).get("velocity", {})
        min_points = velocity_config.get("min_data_points", 10)
        fallback_score = velocity_config.get("fallback_score", 50)

        # Filter valid BSR data
        valid_bsr = [(dt, bsr) for dt, bsr in bsr_history if bsr and bsr > 0]
        
        if len(valid_bsr) < min_points:
            return (0.5, fallback_score, "unknown", f"Insufficient data: {len(valid_bsr)} points")
        
        # Simple BSR trend calculation
        bsr_values = [bsr for _, bsr in valid_bsr]
        recent_avg = statistics.mean(bsr_values[-7:]) if len(bsr_values) >= 7 else statistics.mean(bsr_values)
        older_avg = statistics.mean(bsr_values[:7]) if len(bsr_values) >= 14 else statistics.mean(bsr_values)
        
        if older_avg > 0:
            # Improvement = lower BSR is better
            improvement = (older_avg - recent_avg) / older_avg
            velocity_raw = 0.5 + (improvement * 0.5)  # Scale to 0-1
            velocity_raw = max(0.0, min(1.0, velocity_raw))  # Clamp
        else:
            velocity_raw = 0.5
        
        # Convert to 0-100
        velocity_normalized = int(velocity_raw * 100)
        
        # Determine level
        level = _get_score_level(velocity_normalized, velocity_config)
        
        notes = f"{len(valid_bsr)} BSR data points, {improvement:.2%} trend" if 'improvement' in locals() else f"{len(valid_bsr)} BSR data points"
        
        return (velocity_raw, velocity_normalized, level, notes)
        
    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_advanced_stability_score(price_history: List[Tuple[datetime, float]], config: Dict[str, Any]) -> Tuple[float, int, str, str]:
    """
    Calculate price stability score (0-100) based on coefficient of variation.

    Args:
        price_history: List of (datetime, price) pairs
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure price_history is a list
    if not isinstance(price_history, list):
        return (0.5, 50, "unknown", "Invalid data type for price_history")

    try:
        stability_config = config.get("advanced_scoring", {}).get("stability", {})
        min_points = stability_config.get("min_price_points", 10)
        fallback_score = stability_config.get("fallback_score", 50)
        
        # Filter valid price data
        valid_prices = [price for _, price in price_history if price and price > 0]
        
        if len(valid_prices) < min_points:
            return (0.5, fallback_score, "unknown", f"Insufficient price data: {len(valid_prices)} points")
        
        if len(set(valid_prices)) == 1:
            # Constant price = perfect stability
            return (1.0, 100, "excellent", f"Constant price: ${valid_prices[0]:.2f}")
        
        # Simple coefficient of variation
        mean_price = statistics.mean(valid_prices)
        std_price = statistics.stdev(valid_prices)
        cv = std_price / mean_price if mean_price > 0 else 0
        
        # Stability = 1 - CV (clamped to 0-1)
        stability_raw = 1 - min(cv, 1.0)
        stability_raw = max(0.0, stability_raw)
        
        # Convert to 0-100
        stability_normalized = int(stability_raw * 100)
        
        # Determine level  
        level = _get_score_level(stability_normalized, stability_config)
        
        notes = f"CV: {cv:.3f}, price range: ${min(valid_prices):.2f}-${max(valid_prices):.2f}"
        
        return (stability_raw, stability_normalized, level, notes)
        
    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_advanced_confidence_score(
    price_history: List[Tuple[datetime, float]],
    bsr_data: List[Tuple[datetime, int]],
    data_age_days: int,
    config: Dict[str, Any]
) -> Tuple[float, int, str, str]:
    """
    Calculate data confidence score (0-100) based on freshness, completeness, and BSR availability.

    Args:
        price_history: List of (datetime, price) pairs
        bsr_data: List of (datetime, bsr) pairs
        data_age_days: Age of most recent data in days
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure price_history and bsr_data are lists
    if not isinstance(price_history, list):
        return (0.5, 50, "unknown", "Invalid data type for price_history")
    if not isinstance(bsr_data, list):
        return (0.5, 50, "unknown", "Invalid data type for bsr_data")

    try:
        confidence_config = config.get("advanced_scoring", {}).get("confidence", {})
        freshness_threshold = confidence_config.get("data_freshness_days", 7)
        weights = confidence_config.get("weights", {"freshness": 0.3, "completeness": 0.4, "bsr_availability": 0.3})
        
        # Component 1: Data Freshness
        if data_age_days <= freshness_threshold:
            freshness_score = 1.0
        else:
            # Linear decay after threshold
            freshness_score = max(0, 1 - (data_age_days - freshness_threshold) / 30)
        
        # Component 2: Price Data Completeness
        # Assume 90-day window for completeness calculation
        window_days = 90
        expected_points = window_days
        actual_points = len([p for _, p in price_history if p and p > 0])
        completeness_score = min(actual_points / expected_points, 1.0) if expected_points > 0 else 0
        
        # Component 3: BSR Availability
        has_recent_bsr = bool(bsr_data and any(bsr for _, bsr in bsr_data if bsr and bsr > 0))
        bsr_availability_score = 1.0 if has_recent_bsr else 0.3  # Partial credit if missing
        
        # Weighted average
        confidence_raw = (
            freshness_score * weights.get("freshness", 0.3) +
            completeness_score * weights.get("completeness", 0.4) +
            bsr_availability_score * weights.get("bsr_availability", 0.3)
        )
        
        # Convert to 0-100
        confidence_normalized = int(confidence_raw * 100)
        
        # Determine level
        level = _get_confidence_level(confidence_normalized, confidence_config)
        
        notes = f"Fresh: {freshness_score:.2f}, Complete: {completeness_score:.2f}, BSR: {bsr_availability_score:.2f}"
        
        return (confidence_raw, confidence_normalized, level, notes)
        
    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_overall_rating(roi: float, velocity: int, stability: int, confidence: int, config: Dict[str, Any]) -> str:
    """
    Determine overall rating using gating rules from config.
    
    Args:
        roi: ROI percentage 
        velocity: Velocity score (0-100)
        stability: Stability score (0-100)
        confidence: Confidence score (0-100)
        config: Configuration from business_rules.json
        
    Returns:
        Overall rating string (EXCELLENT/GOOD/FAIR/PASS)
    """
    try:
        gating_rules = config.get("overall_rating", {}).get("gating_rules", {})
        
        # Check each rating level from highest to lowest
        for rating in ["EXCELLENT", "GOOD", "FAIR"]:
            rules = gating_rules.get(rating, {})
            
            roi_min = rules.get("roi_min", 0)
            velocity_min = rules.get("velocity_min", 0)
            stability_min = rules.get("stability_min", 0)
            confidence_min = rules.get("confidence_min", 0)
            
            if (roi >= roi_min and velocity >= velocity_min and 
                stability >= stability_min and confidence >= confidence_min):
                return rating
        
        return "PASS"  # Falls below all thresholds
        
    except Exception as e:
        return "ERROR"


def generate_readable_summary(roi: float, rating: str, scores: Dict[str, int], config: Dict[str, Any]) -> str:
    """
    Generate readable summary using templates from config.
    
    Args:
        roi: ROI percentage
        rating: Overall rating (EXCELLENT/GOOD/FAIR/PASS)
        scores: Dict with velocity, stability, confidence scores
        config: Configuration from business_rules.json
        
    Returns:
        Formatted summary string
    """
    try:
        templates = config.get("summary_templates", {})
        level_flags = config.get("level_flags", {})
        
        if rating not in templates:
            return f"Rating: {rating}, ROI: {roi}%" # Fallback
        
        template = templates[rating]
        
        # Get levels for each score
        velocity_level = _get_level_from_flags(scores.get("velocity", 0), level_flags.get("velocity", {}))
        stability_level = _get_level_from_flags(scores.get("stability", 0), level_flags.get("stability", {}))
        confidence_level = _get_level_from_flags(scores.get("confidence", 0), level_flags.get("confidence", {}))
        
        # Handle PASS case with primary_issue
        if rating == "PASS":
            primary_issue = _determine_primary_issue(roi, scores, config)
            return template.format(roi=roi, primary_issue=primary_issue)
        
        # Standard template formatting
        return template.format(
            roi=roi,
            velocity_level=velocity_level,
            stability_level=stability_level,
            confidence_level=confidence_level
        )
        
    except Exception as e:
        return f"Summary generation failed: {roi}% ROI"


def _get_score_level(score: int, score_config: Dict[str, Any]) -> str:
    """Get level name for score using thresholds."""
    excellent = score_config.get("excellent_threshold", 80)
    good = score_config.get("good_threshold", 60)
    fair = score_config.get("fair_threshold", 40)
    
    if score >= excellent:
        return "excellent"
    elif score >= good:
        return "good"
    elif score >= fair:
        return "fair"
    else:
        return "poor"


def _get_confidence_level(score: int, confidence_config: Dict[str, Any]) -> str:
    """Get confidence level name for score."""
    high = confidence_config.get("high_threshold", 85)
    good = confidence_config.get("good_threshold", 70)
    fair = confidence_config.get("fair_threshold", 50)
    
    if score >= high:
        return "high"
    elif score >= good:
        return "good"
    elif score >= fair:
        return "fair"
    else:
        return "low"


def _get_level_from_flags(score: int, flags: Dict[str, int]) -> str:
    """Get level name from score using level_flags config."""
    # Sort levels by threshold descending
    sorted_levels = sorted(flags.items(), key=lambda x: x[1], reverse=True)
    
    for level, threshold in sorted_levels:
        if score >= threshold:
            return level
    
    return "unknown"


def _determine_primary_issue(roi: float, scores: Dict[str, int], config: Dict[str, Any]) -> str:
    """Determine primary issue for PASS rating."""
    try:
        gating_rules = config.get("overall_rating", {}).get("gating_rules", {})
        fair_rules = gating_rules.get("FAIR", {})
        
        roi_min = fair_rules.get("roi_min", 15.0)
        velocity_min = fair_rules.get("velocity_min", 30)
        stability_min = fair_rules.get("stability_min", 30)
        confidence_min = fair_rules.get("confidence_min", 40)
        
        # Calculate gaps
        gaps = {}
        if roi < roi_min:
            gaps["low_roi"] = roi_min - roi
        if scores.get("velocity", 0) < velocity_min:
            gaps["slow_velocity"] = velocity_min - scores.get("velocity", 0)
        if scores.get("stability", 0) < stability_min:
            gaps["volatile_pricing"] = stability_min - scores.get("stability", 0)
        if scores.get("confidence", 0) < confidence_min:
            gaps["low_confidence"] = confidence_min - scores.get("confidence", 0)
        
        # Return biggest gap
        if gaps:
            primary_issue = max(gaps.items(), key=lambda x: x[1])[0]
            return primary_issue.replace("_", " ")
        
        return "multiple factors"
        
    except Exception:
        return "insufficient metrics"