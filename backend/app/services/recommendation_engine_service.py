"""
Final Recommendation Engine for Phase 8.0
5-tier recommendation system (STRONG_BUY, BUY, CONSIDER, WATCH, SKIP/AVOID)
"""
from typing import Dict, Any, Optional
from enum import Enum


class RecommendationTier(str, Enum):
    """5-tier recommendation system."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    CONSIDER = "CONSIDER"
    WATCH = "WATCH"
    SKIP = "SKIP"
    AVOID = "AVOID"


class RecommendationEngineService:
    """Service for final product recommendation decision."""

    MIN_ROI_THRESHOLD = 30
    GOOD_VELOCITY_THRESHOLD = 70
    ACCEPTABLE_RISK_THRESHOLD = 50
    MAX_SALE_CYCLE_DAYS = 45

    @staticmethod
    def generate_recommendation(
        asin: str,
        title: str,
        roi_net: float,
        velocity_score: float,
        risk_score: float,
        price_stability_score: float,
        amazon_on_listing: bool,
        amazon_has_buybox: bool,
        estimated_sell_price: float,
        estimated_buy_price: float,
        seller_count: Optional[int] = None,
        breakeven_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate final recommendation based on multiple criteria.

        Scoring criteria:
        1. ROI >= 30% (acceptable)
        2. Velocity >= 70 (good sales)
        3. Risk score < 50 (acceptable risk)
        4. Breakeven days <= 45
        5. Amazon not present on listing
        6. Price stability good

        Returns:
            Dict with recommendation tier, confidence, reason, and actions
        """
        criteria = {
            "roi_sufficient": roi_net >= RecommendationEngineService.MIN_ROI_THRESHOLD,
            "velocity_good": velocity_score >= RecommendationEngineService.GOOD_VELOCITY_THRESHOLD,
            "risk_acceptable": risk_score < RecommendationEngineService.ACCEPTABLE_RISK_THRESHOLD,
            "time_to_sell_ok": (breakeven_days or 60) <= RecommendationEngineService.MAX_SALE_CYCLE_DAYS,
            "amazon_not_present": not amazon_on_listing,
            "price_stable": price_stability_score >= 50,
        }

        passed_criteria = sum(1 for v in criteria.values() if v)

        recommendation = _map_criteria_to_recommendation(passed_criteria)

        confidence = _calculate_confidence(
            passed_criteria,
            roi_net,
            velocity_score,
            risk_score
        )

        reason = _generate_reason(
            recommendation,
            criteria,
            roi_net,
            velocity_score,
            risk_score,
            amazon_on_listing,
            amazon_has_buybox
        )

        special_cases = _check_special_cases(
            amazon_on_listing,
            amazon_has_buybox,
            roi_net,
            risk_score,
            velocity_score
        )

        if special_cases['override']:
            recommendation = special_cases['recommendation']
            reason = special_cases['reason']

        profit_per_unit = estimated_sell_price - estimated_buy_price

        return {
            'asin': asin,
            'title': title,
            'recommendation': recommendation.value,
            'confidence_percent': round(confidence, 1),
            'criteria_passed': passed_criteria,
            'criteria_total': len(criteria),
            'reason': reason,
            'roi_net': round(roi_net, 2),
            'velocity_score': round(velocity_score, 2),
            'risk_score': round(risk_score, 2),
            'profit_per_unit': round(profit_per_unit, 2),
            'estimated_time_to_sell_days': breakeven_days,
            'suggested_action': _get_suggested_action(recommendation),
            'next_steps': _get_next_steps(recommendation)
        }

    @staticmethod
    def bulk_recommendation(
        products: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """Generate recommendations for multiple products."""
        recommendations = []
        for product in products:
            rec = RecommendationEngineService.generate_recommendation(**product)
            recommendations.append(rec)
        return recommendations


def _map_criteria_to_recommendation(passed_criteria: int) -> RecommendationTier:
    """Map number of passed criteria to recommendation tier."""
    if passed_criteria >= 6:
        return RecommendationTier.STRONG_BUY
    elif passed_criteria >= 5:
        return RecommendationTier.BUY
    elif passed_criteria >= 4:
        return RecommendationTier.CONSIDER
    elif passed_criteria >= 3:
        return RecommendationTier.WATCH
    else:
        return RecommendationTier.SKIP


def _calculate_confidence(
    passed_criteria: int,
    roi_net: float,
    velocity_score: float,
    risk_score: float
) -> float:
    """Calculate confidence level as percentage."""
    base_confidence = (passed_criteria / 6) * 60

    if roi_net >= 50:
        base_confidence += 15
    elif roi_net >= 30:
        base_confidence += 10

    if velocity_score >= 80:
        base_confidence += 10
    elif velocity_score >= 60:
        base_confidence += 5

    if risk_score < 30:
        base_confidence += 10
    elif risk_score < 50:
        base_confidence += 5

    return min(100, base_confidence)


def _generate_reason(
    recommendation: RecommendationTier,
    criteria: Dict[str, bool],
    roi_net: float,
    velocity_score: float,
    risk_score: float,
    amazon_on_listing: bool,
    amazon_has_buybox: bool
) -> str:
    """Generate human-readable reason for recommendation."""
    if recommendation == RecommendationTier.STRONG_BUY:
        return f"Excellent opportunity: {roi_net:.0f}% ROI, strong velocity ({velocity_score:.0f}), low risk ({risk_score:.0f})"

    elif recommendation == RecommendationTier.BUY:
        return f"Good opportunity: {roi_net:.0f}% ROI with acceptable risk. Monitor velocity trends."

    elif recommendation == RecommendationTier.CONSIDER:
        issues = []
        if not criteria['roi_sufficient']:
            issues.append("ROI below target")
        if not criteria['velocity_good']:
            issues.append("sales velocity concern")
        if not criteria['risk_acceptable']:
            issues.append(f"risk level elevated ({risk_score:.0f})")
        return f"Marginal opportunity. {', '.join(issues)}. Consider alternatives."

    elif recommendation == RecommendationTier.WATCH:
        return f"Not recommended at current pricing. Monitor for price drops and improved velocity."

    else:
        return f"Skip this product. Risk level too high or insufficient ROI."


def _check_special_cases(
    amazon_on_listing: bool,
    amazon_has_buybox: bool,
    roi_net: float,
    risk_score: float,
    velocity_score: float
) -> Dict[str, Any]:
    """Check for special override cases."""
    if amazon_on_listing and amazon_has_buybox:
        return {
            'override': True,
            'recommendation': RecommendationTier.AVOID,
            'reason': 'CRITICAL: Amazon owns Buy Box. Competition risk too high.'
        }

    if roi_net < 15:
        return {
            'override': True,
            'recommendation': RecommendationTier.SKIP,
            'reason': f'ROI too low: {roi_net:.0f}%. Minimum 30% ROI required.'
        }

    if risk_score > 85:
        return {
            'override': True,
            'recommendation': RecommendationTier.SKIP,
            'reason': f'Risk score critical: {risk_score:.0f}%. Product too risky.'
        }

    return {'override': False}


def _get_suggested_action(recommendation: RecommendationTier) -> str:
    """Get suggested action based on recommendation."""
    actions = {
        RecommendationTier.STRONG_BUY: "Buy immediately at current or lower price",
        RecommendationTier.BUY: "Buy at this or better price point",
        RecommendationTier.CONSIDER: "Research further before purchase decision",
        RecommendationTier.WATCH: "Monitor price trends, buy only if price drops 15%+",
        RecommendationTier.SKIP: "Skip, look for better opportunities",
        RecommendationTier.AVOID: "Avoid completely - too risky"
    }
    return actions.get(recommendation, "Review product details manually")


def _get_next_steps(recommendation: RecommendationTier) -> list[str]:
    """Get recommended next steps."""
    if recommendation == RecommendationTier.STRONG_BUY:
        return [
            "Verify current price on Amazon",
            "Check seller ratings and performance metrics",
            "Purchase inventory",
            "Create FBA shipment"
        ]

    elif recommendation == RecommendationTier.BUY:
        return [
            "Verify current price and stock availability",
            "Check seller account health",
            "Plan inventory level",
            "Prepare for FBA submission"
        ]

    elif recommendation == RecommendationTier.CONSIDER:
        return [
            "Deep dive into category trends",
            "Analyze price history over 90 days",
            "Check competitor strategies",
            "Calculate worst-case scenarios"
        ]

    elif recommendation == RecommendationTier.WATCH:
        return [
            "Add to watchlist",
            "Set price alert for 15% drop",
            "Monitor weekly for changes",
            "Revisit in 2-4 weeks"
        ]

    else:
        return [
            "Move to ignored list",
            "Find alternative products in similar category"
        ]
