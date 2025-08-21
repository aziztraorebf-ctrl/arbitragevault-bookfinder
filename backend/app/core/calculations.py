"""
Core calculation engine for ROI, velocity, and business metrics.
"""

import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .fees_config import calculate_profit_metrics, get_fee_config


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