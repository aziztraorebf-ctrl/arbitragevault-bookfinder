"""
Textbook Analysis API Endpoint - ArbitrageVault Textbook Pivot
==============================================================
POST /api/v1/textbook/analyze

Provides comprehensive textbook analysis including:
- Intrinsic value calculation (price corridor with confidence)
- Seasonal pattern detection (COLLEGE_FALL, COLLEGE_SPRING, etc.)
- Evergreen classification (identifies year-round demand books)
- BUY/SKIP recommendations based on combined analysis

Author: Claude Opus 4.5
Date: January 2026
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.keepa_parser_v2 import parse_keepa_product_unified
from app.services.keepa_constants import ALL_CONDITION_KEYS
from app.services.intrinsic_value_service import get_sell_price_for_strategy
from app.services.seasonal_detector_service import (
    detect_seasonal_pattern,
    get_days_until_peak,
    get_optimal_buy_window,
)
from app.services.evergreen_identifier_service import (
    identify_evergreen,
    EvergreenClassification,
)
from app.services.buying_guidance_service import BuyingGuidanceService


router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class TextbookAnalysisRequest(BaseModel):
    """Request schema for textbook analysis."""
    asin: str = Field(..., min_length=10, max_length=10, description="Amazon ASIN (exactly 10 characters)")
    source_price: Optional[float] = Field(None, ge=0, description="Source/buy price for ROI calculation")


class IntrinsicValueCorridor(BaseModel):
    """Price corridor from intrinsic value calculation."""
    low: Optional[float] = Field(None, description="P25 percentile price")
    median: Optional[float] = Field(None, description="P50 percentile price")
    high: Optional[float] = Field(None, description="P75 percentile price")
    volatility: float = Field(0.0, description="Price volatility coefficient")
    data_points: int = Field(0, description="Number of data points used")
    window_days: int = Field(90, description="Analysis window in days")


class IntrinsicValueResult(BaseModel):
    """Intrinsic value analysis result."""
    sell_price: Optional[float] = Field(None, description="Recommended sell price")
    source: str = Field(..., description="Price source: intrinsic_median, current_price_fallback, no_price_available")
    confidence: str = Field(..., description="Confidence level: HIGH, MEDIUM, LOW, INSUFFICIENT_DATA")
    corridor: IntrinsicValueCorridor = Field(..., description="Price corridor details")
    warning: Optional[str] = Field(None, description="Warning message if fallback used")


class SeasonalPatternResult(BaseModel):
    """Seasonal pattern detection result."""
    pattern_type: str = Field(..., description="Pattern type: COLLEGE_FALL, COLLEGE_SPRING, HIGH_SCHOOL, EVERGREEN, STABLE, IRREGULAR, INSUFFICIENT_DATA")
    peak_months: List[int] = Field(default_factory=list, description="Peak demand months (1-12)")
    trough_months: List[int] = Field(default_factory=list, description="Low demand months (1-12)")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Pattern detection confidence")
    days_until_peak: Optional[int] = Field(None, description="Days until next peak month")
    buy_window: Optional[Dict[str, Any]] = Field(None, description="Optimal buy window recommendation")


class EvergreenResult(BaseModel):
    """Evergreen classification result."""
    is_evergreen: bool = Field(..., description="Whether book is evergreen")
    evergreen_type: str = Field(..., description="Type: PROFESSIONAL_CERTIFICATION, CLASSIC, REFERENCE, SKILL_BASED, SEASONAL")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Classification confidence")
    reasons: List[str] = Field(default_factory=list, description="Reasons for classification")
    recommended_stock_level: int = Field(0, ge=0, description="Recommended inventory level")


class ROIMetrics(BaseModel):
    """ROI calculation metrics."""
    roi_percentage: float = Field(..., description="Return on investment percentage")
    profit: float = Field(..., description="Profit per unit")
    buy_cost: float = Field(..., description="Source/buy price")
    sell_price: float = Field(..., description="Expected sell price")


class RecommendationResult(BaseModel):
    """Buy/skip recommendation result."""
    action: str = Field(..., description="Recommendation: STRONG_BUY, BUY, HOLD, SKIP")
    reasons: List[str] = Field(default_factory=list, description="Reasons for recommendation")


class BuyingGuidanceSchema(BaseModel):
    """User-friendly buying guidance with French labels and tooltips."""
    max_buy_price: float = Field(..., description="Maximum price to pay for target ROI")
    target_sell_price: float = Field(..., description="Expected selling price (intrinsic median)")
    estimated_profit: float = Field(..., description="Net profit after fees")
    estimated_roi_pct: float = Field(..., description="Return on investment percentage")
    price_range: str = Field(..., description="Price corridor as formatted string ($XX - $YY)")
    estimated_days_to_sell: int = Field(..., description="Estimated days to sell based on velocity")
    recommendation: str = Field(..., description="BUY, HOLD, or SKIP recommendation")
    recommendation_reason: str = Field(..., description="French explanation for recommendation")
    confidence_label: str = Field(..., description="French confidence label (Fiable, Modere, etc.)")
    explanations: Dict[str, str] = Field(default_factory=dict, description="Tooltip explanations for each field")


class TextbookAnalysisResponse(BaseModel):
    """Complete textbook analysis response."""
    asin: str = Field(..., description="Amazon ASIN")
    title: Optional[str] = Field(None, description="Product title")
    intrinsic_value: IntrinsicValueResult = Field(..., description="Intrinsic value analysis")
    seasonal_pattern: SeasonalPatternResult = Field(..., description="Seasonal pattern detection")
    evergreen_classification: EvergreenResult = Field(..., description="Evergreen classification")
    recommendation: RecommendationResult = Field(..., description="Buy/skip recommendation")
    roi_metrics: Optional[ROIMetrics] = Field(None, description="ROI metrics (if source_price provided)")
    buying_guidance: BuyingGuidanceSchema = Field(..., description="User-friendly buying guidance with explanations")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


# =============================================================================
# RECOMMENDATION LOGIC
# =============================================================================

# ROI thresholds for recommendations
ROI_STRONG_BUY_THRESHOLD = 50.0  # >50% ROI = STRONG_BUY
ROI_BUY_THRESHOLD = 30.0         # >30% ROI = BUY
ROI_HOLD_THRESHOLD = 15.0        # >15% ROI = HOLD


def _generate_recommendation(
    intrinsic_result: Dict[str, Any],
    seasonal_pattern: Any,
    evergreen_result: EvergreenClassification,
    roi_metrics: Optional[ROIMetrics]
) -> RecommendationResult:
    """
    Generate BUY/SKIP recommendation based on all analysis components.

    Priority rules:
    1. INSUFFICIENT_DATA confidence = SKIP
    2. Evergreen + High confidence = BUY NOW (anytime is good)
    3. ROI > 50% = STRONG_BUY
    4. ROI > 30% = BUY
    5. ROI > 15% = HOLD
    6. Otherwise = SKIP
    """
    reasons: List[str] = []

    # Rule 1: Check for insufficient data
    confidence = intrinsic_result.get("corridor", {}).get("confidence", "INSUFFICIENT_DATA")
    if confidence == "INSUFFICIENT_DATA":
        reasons.append("Insufficient historical data for reliable analysis")
        return RecommendationResult(action="SKIP", reasons=reasons)

    # Rule 2: High-confidence evergreen books are always good
    if evergreen_result.is_evergreen and evergreen_result.confidence >= 0.7:
        reasons.append(f"High-confidence evergreen ({evergreen_result.evergreen_type})")

        # If we also have ROI metrics, check if it's a strong buy
        if roi_metrics and roi_metrics.roi_percentage > ROI_STRONG_BUY_THRESHOLD:
            reasons.append(f"Excellent ROI: {roi_metrics.roi_percentage:.1f}%")
            return RecommendationResult(action="STRONG_BUY", reasons=reasons)

        reasons.append("Year-round demand - buy anytime")
        return RecommendationResult(action="BUY", reasons=reasons)

    # Rule 3-6: ROI-based recommendations (if source_price provided)
    if roi_metrics:
        roi = roi_metrics.roi_percentage

        if roi > ROI_STRONG_BUY_THRESHOLD:
            reasons.append(f"ROI {roi:.1f}% exceeds {ROI_STRONG_BUY_THRESHOLD}% threshold")
            if confidence in ["HIGH", "MEDIUM"]:
                reasons.append(f"Price confidence: {confidence}")
            return RecommendationResult(action="STRONG_BUY", reasons=reasons)

        elif roi > ROI_BUY_THRESHOLD:
            reasons.append(f"ROI {roi:.1f}% exceeds {ROI_BUY_THRESHOLD}% threshold")

            # Add seasonal timing info if relevant
            if seasonal_pattern.pattern_type in ["COLLEGE_FALL", "COLLEGE_SPRING", "HIGH_SCHOOL"]:
                buy_window = get_optimal_buy_window(seasonal_pattern)
                reasons.append(buy_window.get("recommendation", "Check seasonal timing"))

            return RecommendationResult(action="BUY", reasons=reasons)

        elif roi > ROI_HOLD_THRESHOLD:
            reasons.append(f"ROI {roi:.1f}% is marginal (hold threshold: {ROI_HOLD_THRESHOLD}%)")
            reasons.append("Consider waiting for better price or alternative")
            return RecommendationResult(action="HOLD", reasons=reasons)

        else:
            reasons.append(f"ROI {roi:.1f}% below minimum threshold")
            return RecommendationResult(action="SKIP", reasons=reasons)

    # No source_price provided - base recommendation on confidence only
    if confidence == "HIGH":
        reasons.append("High-confidence price data available")
        reasons.append("Provide source_price for ROI calculation")
        return RecommendationResult(action="HOLD", reasons=reasons)

    elif confidence == "MEDIUM":
        reasons.append("Medium-confidence price data")
        reasons.append("Consider more research before buying")
        return RecommendationResult(action="HOLD", reasons=reasons)

    else:
        reasons.append("Low confidence in price data")
        return RecommendationResult(action="SKIP", reasons=reasons)


# =============================================================================
# API ENDPOINT
# =============================================================================

@router.post("/analyze", response_model=TextbookAnalysisResponse)
async def analyze_textbook(
    request: TextbookAnalysisRequest,
    condition_filter: Optional[List[str]] = Query(
        default=None,
        description="Filter offers by condition: new, very_good, good, acceptable. Default: include all."
    ),
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> TextbookAnalysisResponse:
    """
    Analyze a textbook for arbitrage opportunity.

    Returns comprehensive analysis including:
    - Intrinsic value corridor with confidence level
    - Seasonal pattern detection (college vs high school timing)
    - Evergreen classification (year-round vs seasonal demand)
    - BUY/SKIP recommendation with reasoning
    - ROI metrics (if source_price provided)
    """
    asin = request.asin.upper()
    logger.info(f"[TEXTBOOK] Starting analysis for ASIN: {asin}")

    # Validate condition_filter if provided (Gap #2 from Senior Review)
    if condition_filter is not None:
        # Treat empty list as None (include all conditions)
        if len(condition_filter) == 0:
            condition_filter = None
        else:
            # Validate each condition
            invalid_conditions = [c for c in condition_filter if c not in ALL_CONDITION_KEYS]
            if invalid_conditions:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_CONDITION_FILTER",
                        "message": f"Invalid conditions: {invalid_conditions}. Valid conditions: {ALL_CONDITION_KEYS}"
                    }
                )

    try:
        # Step 1: Fetch Keepa data
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(asin, force_refresh=False)

            if keepa_data is None:
                logger.warning(f"[TEXTBOOK] Product not found: {asin}")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "PRODUCT_NOT_FOUND",
                        "message": f"Product {asin} not found in Keepa database"
                    }
                )

        # Step 2: Parse Keepa data using unified parser
        parsed_data = parse_keepa_product_unified(keepa_data, condition_filter=condition_filter)

        # Step 3: Calculate intrinsic value corridor
        intrinsic_result = get_sell_price_for_strategy(
            parsed_data=parsed_data,
            strategy="textbook"  # Uses 365-day window for textbooks
        )

        # Step 4: Detect seasonal pattern
        price_history = parsed_data.get("price_history", [])
        seasonal_pattern = detect_seasonal_pattern(price_history)
        days_to_peak = get_days_until_peak(seasonal_pattern)
        buy_window = get_optimal_buy_window(seasonal_pattern)

        # Step 5: Identify evergreen classification
        evergreen_input = {
            "title": parsed_data.get("title", ""),
            "category": keepa_data.get("category", ""),
            "bsr": parsed_data.get("current_bsr"),
            "price_volatility": intrinsic_result.get("corridor", {}).get("volatility", 0),
            "sales_per_month": parsed_data.get("sales_per_month", 0),
        }
        evergreen_result = identify_evergreen(evergreen_input)

        # Step 6: Calculate ROI metrics (if source_price provided)
        roi_metrics = None
        if request.source_price is not None and intrinsic_result.get("sell_price"):
            sell_price = intrinsic_result["sell_price"]
            profit = sell_price - request.source_price
            roi_pct = (profit / request.source_price * 100) if request.source_price > 0 else 0

            roi_metrics = ROIMetrics(
                roi_percentage=round(roi_pct, 2),
                profit=round(profit, 2),
                buy_cost=request.source_price,
                sell_price=sell_price
            )

        # Step 7: Generate recommendation
        recommendation = _generate_recommendation(
            intrinsic_result=intrinsic_result,
            seasonal_pattern=seasonal_pattern,
            evergreen_result=evergreen_result,
            roi_metrics=roi_metrics
        )

        # Step 8: Calculate buying guidance
        corridor = intrinsic_result.get("corridor", {})
        buying_guidance_service = BuyingGuidanceService()

        # Prepare velocity data for days-to-sell estimation
        velocity_data = {
            'monthly_sales': parsed_data.get('sales_per_month', 0),
            'velocity_tier': 'unknown',
        }

        # Use source_price or default for guidance calculation
        effective_source_price = request.source_price if request.source_price is not None else 8.0

        guidance_result = buying_guidance_service.calculate_guidance(
            intrinsic_result=corridor,
            velocity_data=velocity_data,
            source_price=effective_source_price,
        )

        # Convert dataclass to schema
        buying_guidance = BuyingGuidanceSchema(
            max_buy_price=guidance_result.max_buy_price,
            target_sell_price=guidance_result.target_sell_price,
            estimated_profit=guidance_result.estimated_profit,
            estimated_roi_pct=guidance_result.estimated_roi_pct,
            price_range=guidance_result.price_range,
            estimated_days_to_sell=guidance_result.estimated_days_to_sell,
            recommendation=guidance_result.recommendation,
            recommendation_reason=guidance_result.recommendation_reason,
            confidence_label=guidance_result.confidence_label,
            explanations=guidance_result.explanations,
        )

        # Build response

        response = TextbookAnalysisResponse(
            asin=asin,
            title=parsed_data.get("title"),
            intrinsic_value=IntrinsicValueResult(
                sell_price=intrinsic_result.get("sell_price"),
                source=intrinsic_result.get("source", "unknown"),
                confidence=corridor.get("confidence", "INSUFFICIENT_DATA"),
                corridor=IntrinsicValueCorridor(
                    low=corridor.get("low"),
                    median=corridor.get("median"),
                    high=corridor.get("high"),
                    volatility=corridor.get("volatility", 0),
                    data_points=corridor.get("data_points", 0),
                    window_days=corridor.get("window_days", 90)
                ),
                warning=intrinsic_result.get("warning")
            ),
            seasonal_pattern=SeasonalPatternResult(
                pattern_type=seasonal_pattern.pattern_type,
                peak_months=seasonal_pattern.peak_months,
                trough_months=seasonal_pattern.trough_months,
                confidence=seasonal_pattern.confidence,
                days_until_peak=days_to_peak,
                buy_window=buy_window
            ),
            evergreen_classification=EvergreenResult(
                is_evergreen=evergreen_result.is_evergreen,
                evergreen_type=evergreen_result.evergreen_type,
                confidence=evergreen_result.confidence,
                reasons=evergreen_result.reasons,
                recommended_stock_level=evergreen_result.recommended_stock_level
            ),
            recommendation=recommendation,
            roi_metrics=roi_metrics,
            buying_guidance=buying_guidance,
            analyzed_at=datetime.now()
        )

        logger.info(
            f"[TEXTBOOK] Analysis complete for {asin}: "
            f"recommendation={recommendation.action}, "
            f"confidence={corridor.get('confidence')}, "
            f"evergreen={evergreen_result.is_evergreen}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEXTBOOK] Analysis failed for {asin}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_FAILED",
                "message": f"Failed to analyze textbook: {str(e)}"
            }
        )
