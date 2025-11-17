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

router = APIRouter(prefix="/analytics", tags=["analytics"])


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

        dead_inventory_data = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count
        )

        return {
            'asin': request.asin,
            'title': request.title,
            'velocity': velocity_data,
            'price_stability': price_stability_data,
            'roi': roi_data,
            'competition': competition_data,
            'dead_inventory_risk': dead_inventory_data
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

        dead_inventory_data = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            dead_inventory_data=dead_inventory_data
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

        dead_inventory_data = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            dead_inventory_data=dead_inventory_data
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

        dead_inventory_data = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=request.bsr,
            category=request.category or 'books',
            seller_count=request.seller_count,
            amazon_on_listing=request.amazon_on_listing,
            price_stability_data=price_stability_data,
            dead_inventory_data=dead_inventory_data
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
