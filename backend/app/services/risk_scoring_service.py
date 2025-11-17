"""
Risk Scoring Service for Phase 8.0
5-component risk assessment algorithm.
"""
from typing import Dict, Any, Optional
from decimal import Decimal

from app.services.advanced_analytics_service import AdvancedAnalyticsService


class RiskScoringService:
    """Service for comprehensive risk assessment."""

    RISK_WEIGHTS = {
        'dead_inventory': 0.35,
        'competition': 0.25,
        'amazon_presence': 0.20,
        'price_stability': 0.10,
        'category': 0.10
    }

    CATEGORY_RISK_FACTORS = {
        'textbooks': 45,
        'fiction': 35,
        'nonfiction': 40,
        'technical': 30,
        'general': 50,
    }

    @staticmethod
    def calculate_risk_score(
        bsr: Optional[int],
        category: str,
        seller_count: Optional[int],
        amazon_on_listing: Optional[bool],
        price_stability_data: Dict[str, Any],
        dead_inventory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive 5-component risk score.

        Components:
        1. Dead Inventory Risk (35% weight) - BSR thresholds
        2. Competition Risk (25% weight) - Seller count, FBA presence
        3. Amazon Presence Risk (20% weight) - Amazon owns listing
        4. Price Stability Risk (10% weight) - Price volatility
        5. Category Risk (10% weight) - Category-specific factors

        Args:
            bsr: Current best seller rank
            category: Product category
            seller_count: Number of sellers
            amazon_on_listing: Whether Amazon is selling
            price_stability_data: From calculate_price_stability_score
            dead_inventory_data: From detect_dead_inventory

        Returns:
            Dict with risk_score, risk_level, and component breakdown
        """
        risk_components = {}

        risk_components['dead_inventory'] = _calculate_dead_inventory_risk(dead_inventory_data)
        risk_components['competition'] = _calculate_competition_risk(seller_count)
        risk_components['amazon_presence'] = _calculate_amazon_risk(amazon_on_listing)
        risk_components['price_stability'] = _calculate_price_stability_risk(price_stability_data)
        risk_components['category'] = _calculate_category_risk(category)

        total_risk = (
            risk_components['dead_inventory'] * RiskScoringService.RISK_WEIGHTS['dead_inventory'] +
            risk_components['competition'] * RiskScoringService.RISK_WEIGHTS['competition'] +
            risk_components['amazon_presence'] * RiskScoringService.RISK_WEIGHTS['amazon_presence'] +
            risk_components['price_stability'] * RiskScoringService.RISK_WEIGHTS['price_stability'] +
            risk_components['category'] * RiskScoringService.RISK_WEIGHTS['category']
        )

        risk_level = _get_risk_level(total_risk)

        return {
            'total_risk_score': round(total_risk, 2),
            'risk_level': risk_level,
            'components': {
                'dead_inventory': {
                    'score': round(risk_components['dead_inventory'], 2),
                    'weighted': round(
                        risk_components['dead_inventory'] * RiskScoringService.RISK_WEIGHTS['dead_inventory'],
                        2
                    ),
                    'weight': RiskScoringService.RISK_WEIGHTS['dead_inventory']
                },
                'competition': {
                    'score': round(risk_components['competition'], 2),
                    'weighted': round(
                        risk_components['competition'] * RiskScoringService.RISK_WEIGHTS['competition'],
                        2
                    ),
                    'weight': RiskScoringService.RISK_WEIGHTS['competition']
                },
                'amazon_presence': {
                    'score': round(risk_components['amazon_presence'], 2),
                    'weighted': round(
                        risk_components['amazon_presence'] * RiskScoringService.RISK_WEIGHTS['amazon_presence'],
                        2
                    ),
                    'weight': RiskScoringService.RISK_WEIGHTS['amazon_presence']
                },
                'price_stability': {
                    'score': round(risk_components['price_stability'], 2),
                    'weighted': round(
                        risk_components['price_stability'] * RiskScoringService.RISK_WEIGHTS['price_stability'],
                        2
                    ),
                    'weight': RiskScoringService.RISK_WEIGHTS['price_stability']
                },
                'category': {
                    'score': round(risk_components['category'], 2),
                    'weighted': round(
                        risk_components['category'] * RiskScoringService.RISK_WEIGHTS['category'],
                        2
                    ),
                    'weight': RiskScoringService.RISK_WEIGHTS['category']
                }
            }
        }

    @staticmethod
    def get_risk_recommendations(risk_score: float, risk_level: str) -> str:
        """Get actionable recommendations based on risk level."""
        if risk_level == 'CRITICAL':
            return 'HIGH RISK: Consider alternative products. Monitor for price drops and sales velocity.'
        elif risk_level == 'HIGH':
            return 'Watch this product carefully. Ensure sufficient inventory buffer for storage costs.'
        elif risk_level == 'MEDIUM':
            return 'Moderate risk acceptable. Recommend monitoring price and BSR trends.'
        else:
            return 'Low risk profile. Product suitable for arbitrage.'


def _calculate_dead_inventory_risk(dead_inventory_data: Dict[str, Any]) -> float:
    """Component 1: Dead Inventory Risk (0-100)"""
    if dead_inventory_data.get('is_dead_risk'):
        return min(100, 50 + dead_inventory_data.get('risk_score', 0))
    return max(0, dead_inventory_data.get('risk_score', 0))


def _calculate_competition_risk(seller_count: Optional[int]) -> float:
    """Component 2: Competition Risk (0-100)"""
    if seller_count is None:
        return 50

    if seller_count <= 2:
        return 10
    elif seller_count <= 5:
        return 25
    elif seller_count <= 15:
        return 45
    elif seller_count <= 30:
        return 65
    else:
        return min(100, 80 + (seller_count - 30) // 20)


def _calculate_amazon_risk(amazon_on_listing: Optional[bool]) -> float:
    """Component 3: Amazon Presence Risk (0-100)"""
    return 95 if amazon_on_listing else 5


def _calculate_price_stability_risk(price_stability_data: Dict[str, Any]) -> float:
    """Component 4: Price Stability Risk (0-100)"""
    stability_score = price_stability_data.get('stability_score', 50)
    return 100 - stability_score


def _calculate_category_risk(category: str) -> float:
    """Component 5: Category Risk (0-100)"""
    base_risk = RiskScoringService.CATEGORY_RISK_FACTORS.get(category, 50)
    return base_risk


def _get_risk_level(risk_score: float) -> str:
    """Map risk score to risk level."""
    if risk_score >= 75:
        return 'CRITICAL'
    elif risk_score >= 55:
        return 'HIGH'
    elif risk_score >= 35:
        return 'MEDIUM'
    else:
        return 'LOW'
