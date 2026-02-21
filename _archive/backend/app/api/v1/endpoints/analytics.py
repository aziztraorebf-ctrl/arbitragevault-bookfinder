"""
Analytics API endpoints for Phase 8.0
Advanced analytics, risk scoring, and recommendations.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.schemas.analytics import (
    AnalyticsRequestSchema,
    RiskScoreResponseSchema,
    RecommendationResponseSchema,
    ProductDecisionSchema
)
from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.risk_scoring_service import RiskScoringService
from app.services.recommendation_engine_service import RecommendationEngineService
from app.services.sales_velocity_service import SalesVelocityService

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Initialize velocity service
_velocity_service = SalesVelocityService()


def _calculate_slow_velocity_risk(
    sales_drops_30: int | None,
    bsr: int | None,
    category: str = 'books'
) -> dict:
    """
    Calculate slow velocity risk using real Keepa salesDrops data.

    This replaces the old hardcoded BSR thresholds with actual sales data.
    Based on real data analysis:
    - BSR 200K can have 15+ sales/month (NOT dead inventory)
    - BSR 350K can have 7+ sales/month (still sells regularly)
    - Only 0-4 sales/month is truly "DEAD"
    """
    if sales_drops_30 is not None:
        # Use REAL Keepa data
        monthly_sales = _velocity_service.estimate_monthly_sales(
            sales_drops_30, bsr or 0, category
        )
        velocity_tier = _velocity_service.classify_velocity_tier(monthly_sales)
        tier_info = _velocity_service.get_tier_description(velocity_tier)
        data_source = 'KEEPA_REAL'
    elif bsr is not None:
        # Fallback: estimate from BSR only (less accurate)
        # Use conservative estimates based on our real data analysis
        if bsr < 50000:
            monthly_sales = 50  # HIGH tier
        elif bsr < 150000:
            monthly_sales = 25  # MEDIUM tier
        elif bsr < 350000:
            monthly_sales = 10  # LOW tier
        elif bsr < 500000:
            monthly_sales = 4   # borderline DEAD
        else:
            monthly_sales = 1   # DEAD
        velocity_tier = _velocity_service.classify_velocity_tier(monthly_sales)
        tier_info = _velocity_service.get_tier_description(velocity_tier)
        data_source = 'ESTIMATED_FROM_BSR'
    else:
        # No data available
        monthly_sales = 0
        velocity_tier = 'UNKNOWN'
        tier_info = {'label': 'Unknown', 'description': 'No data available'}
        data_source = 'NO_DATA'

    # Convert velocity tier to risk score (inverse relationship)
    tier_to_risk = {
        'PREMIUM': 5,   # Very low risk
        'HIGH': 15,     # Low risk
        'MEDIUM': 35,   # Moderate risk
        'LOW': 60,      # Higher risk
        'DEAD': 90,     # Very high risk
        'UNKNOWN': 50   # Default moderate
    }
    risk_score = tier_to_risk.get(velocity_tier, 50)

    return {
        'velocity_tier': velocity_tier,
        'monthly_sales_estimate': monthly_sales,
        'risk_score': risk_score,
        'tier_description': tier_info.get('description', ''),
        'data_source': data_source
    }


@router.post("/calculate-analytics", response_model=dict)
async def calculate_product_analytics(
    request: AnalyticsRequestSchema,
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Calculate comprehensive analytics for a product.
    Includes velocity intelligence, price stability, ROI, and competition analysis.
    """
    try:
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=request.bsr,
            bsr_history=request.bsr_history or [],
            category=request.category or 'books'
        )

        price_stability_data = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=request.price_history or []
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=request.estimated_buy_price,
            estimated_sell_price=request.estimated_sell_price,
            referral_fee_percent=request.referral_fee_percent or 15,
            fba_fee=request.fba_fee or 2.50,
            prep_fee=request.prep_fee,
            return_rate_percent=request.return_rate_percent or 2,
            storage_cost_monthly=request.storage_cost_monthly or 0.87,
            sale_cycle_days=request.estimated_sale_cycle_days or 30
        )

        competition_data = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=request.seller_count,
            fba_seller_count=request.fba_seller_count,
            amazon_on_listing=request.amazon_on_listing
        )

        # Use real Keepa salesDrops data instead of hardcoded BSR thresholds
        slow_velocity_data = _calculate_slow_velocity_risk(
            sales_drops_30=request.sales_drops_30,
            bsr=request.bsr,
            category=request.category or 'books'
        )

        return {
            'asin': request.asin,
            'title': request.title,
            'velocity': velocity_data,
            'price_stability': price_stability_data,
            'roi': roi_data,
            'competition': competition_data,
            'slow_velocity_risk': slow_velocity_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation error: {str(e)}")


@router.post("/calculate-risk-score", response_model=RiskScoreResponseSchema)
async def calculate_risk_score(
    request: AnalyticsRequestSchema,
    db: AsyncSession = Depends(get_db_session)
) -> RiskScoreResponseSchema:
    """
    Calculate comprehensive 5-component risk score for a product.

    Risk components (weighted):
    - Dead Inventory (35%): BSR thresholds by category
    - Competition (25%): Seller count and FBA presence
    - Amazon Presence (20%): Whether Amazon is selling
    - Price Stability (10%): Price volatility
    - Category (10%): Category-specific risk factors
    """
    try:
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=request.bsr,
            bsr_history=request.bsr_history or [],
            category=request.category or 'books'
        )

        price_stability_data = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=request.price_history or []
        )

        # Use real Keepa salesDrops data instead of hardcoded BSR thresholds
        slow_velocity_data = _calculate_slow_velocity_risk(
            sales_drops_30=request.sales_drops_30,
            bsr=request.bsr,
            category=request.category or 'books'
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            slow_velocity_data=slow_velocity_data
        )

        recommendations = RiskScoringService.get_risk_recommendations(
            risk_data['total_risk_score'],
            risk_data['risk_level']
        )

        return RiskScoreResponseSchema(
            asin=request.asin,
            risk_score=risk_data['total_risk_score'],
            risk_level=risk_data['risk_level'],
            components=risk_data['components'],
            recommendations=recommendations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk calculation error: {str(e)}")


@router.post("/generate-recommendation", response_model=RecommendationResponseSchema)
async def generate_recommendation(
    request: AnalyticsRequestSchema,
    db: AsyncSession = Depends(get_db_session)
) -> RecommendationResponseSchema:
    """
    Generate final product recommendation (5-tier system).

    Tiers: STRONG_BUY, BUY, CONSIDER, WATCH, SKIP, AVOID

    Considers:
    - ROI >= 30%
    - Velocity score >= 70
    - Risk score < 50
    - Breakeven within 45 days
    - Amazon not present
    - Price stability good
    """
    try:
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=request.bsr,
            bsr_history=request.bsr_history or [],
            category=request.category or 'books'
        )

        price_stability_data = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=request.price_history or []
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=request.estimated_buy_price,
            estimated_sell_price=request.estimated_sell_price,
            referral_fee_percent=request.referral_fee_percent or 15,
            fba_fee=request.fba_fee or 2.50,
            prep_fee=request.prep_fee,
            return_rate_percent=request.return_rate_percent or 2,
            storage_cost_monthly=request.storage_cost_monthly or 0.87,
            sale_cycle_days=request.estimated_sale_cycle_days or 30
        )

        # Use real Keepa salesDrops data instead of hardcoded BSR thresholds
        slow_velocity_data = _calculate_slow_velocity_risk(
            sales_drops_30=request.sales_drops_30,
            bsr=request.bsr,
            category=request.category or 'books'
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            slow_velocity_data=slow_velocity_data
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin=request.asin,
            title=request.title or 'Unknown',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=risk_data['total_risk_score'],
            price_stability_score=price_stability_data['stability_score'],
            amazon_on_listing=request.amazon_on_listing or False,
            amazon_has_buybox=request.amazon_has_buybox or False,
            estimated_sell_price=float(request.estimated_sell_price),
            estimated_buy_price=float(request.estimated_buy_price),
            seller_count=request.seller_count,
            breakeven_days=roi_data.get('breakeven_required_days')
        )

        return RecommendationResponseSchema(**recommendation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation error: {str(e)}")


@router.post("/product-decision", response_model=ProductDecisionSchema)
async def get_product_decision(
    request: AnalyticsRequestSchema,
    db: AsyncSession = Depends(get_db_session)
) -> ProductDecisionSchema:
    """
    Get comprehensive product decision card with all analytics.

    Returns complete decision package including:
    - Velocity intelligence and trends
    - Price stability analysis
    - ROI net calculation
    - Risk score (5 components)
    - Final recommendation (5-tier)
    """
    try:
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=request.bsr,
            bsr_history=request.bsr_history or [],
            category=request.category or 'books'
        )

        price_stability_data = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=request.price_history or []
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=request.estimated_buy_price,
            estimated_sell_price=request.estimated_sell_price,
            referral_fee_percent=request.referral_fee_percent or 15,
            fba_fee=request.fba_fee or 2.50,
            prep_fee=request.prep_fee,
            return_rate_percent=request.return_rate_percent or 2,
            storage_cost_monthly=request.storage_cost_monthly or 0.87,
            sale_cycle_days=request.estimated_sale_cycle_days or 30
        )

        competition_data = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=request.seller_count,
            fba_seller_count=request.fba_seller_count,
            amazon_on_listing=request.amazon_on_listing
        )

        # Use real Keepa salesDrops data instead of hardcoded BSR thresholds
        slow_velocity_data = _calculate_slow_velocity_risk(
            sales_drops_30=request.sales_drops_30,
            bsr=request.bsr,
            category=request.category or 'books'
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            slow_velocity_data=slow_velocity_data
        )

        recommendations = RiskScoringService.get_risk_recommendations(
            risk_data['total_risk_score'],
            risk_data['risk_level']
        )

        risk_response = RiskScoreResponseSchema(
            asin=request.asin,
            risk_score=risk_data['total_risk_score'],
            risk_level=risk_data['risk_level'],
            components=risk_data['components'],
            recommendations=recommendations
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin=request.asin,
            title=request.title or 'Unknown',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=risk_data['total_risk_score'],
            price_stability_score=price_stability_data['stability_score'],
            amazon_on_listing=request.amazon_on_listing or False,
            amazon_has_buybox=request.amazon_has_buybox or False,
            estimated_sell_price=float(request.estimated_sell_price),
            estimated_buy_price=float(request.estimated_buy_price),
            seller_count=request.seller_count,
            breakeven_days=roi_data.get('breakeven_required_days')
        )

        return ProductDecisionSchema(
            asin=request.asin,
            title=request.title or 'Unknown',
            velocity=velocity_data,
            price_stability=price_stability_data,
            roi=roi_data,
            competition=competition_data,
            risk=risk_response,
            recommendation=recommendation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision card generation error: {str(e)}")
