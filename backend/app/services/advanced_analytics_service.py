"""
Advanced Analytics Service for Phase 8.0
Implements velocity intelligence, price stability, ROI calculation, competition analysis.

REFACTORED: Removed detect_dead_inventory and hardcoded BSR thresholds.
Velocity risk is now calculated using real Keepa salesDrops data via SalesVelocityService.
See analytics.py:_calculate_slow_velocity_risk() for the new implementation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
import statistics

from sqlalchemy.orm import Session

from app.models.analytics import ASINHistory, DecisionOutcome


class AdvancedAnalyticsService:
    """Service for advanced product analytics calculations."""

    # REMOVED: CATEGORY_DEAD_INVENTORY_THRESHOLDS - was based on arbitrary BSR values
    # Now using real Keepa salesDrops data via SalesVelocityService

    STORAGE_COSTS_MONTHLY = {
        'standard': Decimal('0.87'),
        'oversized': Decimal('1.24'),
    }

    @staticmethod
    def calculate_velocity_intelligence(
        bsr: Optional[int],
        bsr_history: List[Dict[str, Any]],
        category: str = 'books'
    ) -> Dict[str, Any]:
        """
        Calculate advanced velocity score based on BSR trends over multiple periods.

        Args:
            bsr: Current BSR value
            bsr_history: List of historical BSR readings with timestamps
            category: Product category for benchmarking

        Returns:
            Dict with velocity_score, trend analysis, seasonal factors
        """
        if not bsr or bsr <= 0:
            return {
                'velocity_score': 0,
                'trend_7d': None,
                'trend_30d': None,
                'trend_90d': None,
                'risk_level': 'NO_DATA'
            }

        now = datetime.now(timezone.utc)
        velocity_score = 100

        bsr_values_7d = []
        bsr_values_30d = []
        bsr_values_90d = []

        for record in bsr_history:
            record_time = record.get('timestamp')
            if isinstance(record_time, str):
                record_time = datetime.fromisoformat(record_time.replace('Z', '+00:00'))

            record_bsr = record.get('bsr')
            if not record_bsr:
                continue

            days_ago = (now - record_time).days

            if 0 <= days_ago <= 7:
                bsr_values_7d.append(record_bsr)
            if 0 <= days_ago <= 30:
                bsr_values_30d.append(record_bsr)
            if 0 <= days_ago <= 90:
                bsr_values_90d.append(record_bsr)

        trend_7d = trend_30d = trend_90d = None

        if len(bsr_values_7d) >= 2:
            trend_7d = (bsr_values_7d[0] - bsr_values_7d[-1])
            if trend_7d < -50:
                velocity_score += 20
            elif trend_7d > 100:
                velocity_score -= 15

        if len(bsr_values_30d) >= 3:
            trend_30d = (bsr_values_30d[0] - bsr_values_30d[-1])
            if trend_30d < -100:
                velocity_score += 15
            elif trend_30d > 200:
                velocity_score -= 10

        if len(bsr_values_90d) >= 4:
            trend_90d = (bsr_values_90d[0] - bsr_values_90d[-1])
            if trend_90d < -200:
                velocity_score += 10

        velocity_score = max(0, min(100, velocity_score))

        return {
            'velocity_score': velocity_score,
            'trend_7d': trend_7d,
            'trend_30d': trend_30d,
            'trend_90d': trend_90d,
            'bsr_current': bsr,
            'risk_level': 'HIGH' if velocity_score < 30 else 'MEDIUM' if velocity_score < 60 else 'LOW'
        }

    @staticmethod
    def calculate_price_stability_score(
        price_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate price stability score based on price variance over time.
        Lower variance = more stable = higher score.
        """
        if not price_history or len(price_history) < 2:
            return {
                'stability_score': 50,
                'coefficient_variation': None,
                'price_volatility': 'UNKNOWN',
                'avg_price': None
            }

        prices = [float(p.get('price')) for p in price_history if p.get('price')]

        if len(prices) < 2:
            return {
                'stability_score': 50,
                'coefficient_variation': None,
                'price_volatility': 'INSUFFICIENT_DATA',
                'avg_price': prices[0] if prices else None
            }

        avg_price = statistics.mean(prices)
        if avg_price == 0:
            cv = 0
        else:
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
            cv = (std_dev / avg_price) * 100

        stability_score = 100 - min(100, cv * 5)

        volatility = 'LOW' if cv < 10 else 'MEDIUM' if cv < 25 else 'HIGH'

        return {
            'stability_score': max(0, stability_score),
            'coefficient_variation': round(cv, 2),
            'price_volatility': volatility,
            'avg_price': round(avg_price, 2),
            'std_deviation': round(statistics.stdev(prices), 2) if len(prices) > 1 else 0
        }

    @staticmethod
    def calculate_roi_net(
        estimated_buy_price: Decimal,
        estimated_sell_price: Decimal,
        referral_fee_percent: Decimal = Decimal('15'),
        fba_fee: Decimal = Decimal('2.50'),
        prep_fee: Optional[Decimal] = None,
        return_rate_percent: Decimal = Decimal('2'),
        storage_cost_monthly: Decimal = Decimal('0.87'),
        sale_cycle_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate net ROI including all fees and costs.

        Args:
            estimated_buy_price: Cost to acquire product
            estimated_sell_price: Expected selling price
            referral_fee_percent: Amazon referral fee percentage
            fba_fee: FBA fulfillment fee per unit
            prep_fee: Prep cost per unit
            return_rate_percent: Expected return rate percentage
            storage_cost_monthly: Monthly storage cost
            sale_cycle_days: Expected days to sell
        """
        buy = Decimal(str(estimated_buy_price))
        sell = Decimal(str(estimated_sell_price))

        referral = (sell * referral_fee_percent) / Decimal('100')
        returns_cost = (sell * return_rate_percent) / Decimal('100')

        fba = Decimal(str(fba_fee))
        prep = prep_fee or Decimal('0')

        storage_months = Decimal(sale_cycle_days) / Decimal('30')
        storage = Decimal(str(storage_cost_monthly)) * storage_months

        gross_profit = sell - buy
        total_fees = referral + fba + prep + storage + returns_cost

        net_profit = gross_profit - total_fees

        roi_percent = (net_profit / buy * Decimal('100')) if buy > 0 else Decimal('0')

        return {
            'net_profit': float(net_profit),
            'roi_percentage': float(roi_percent),
            'gross_profit': float(gross_profit),
            'referral_fee': float(referral),
            'fba_fee': float(fba),
            'prep_fee': float(prep),
            'storage_cost': float(storage),
            'return_losses': float(returns_cost),
            'total_fees': float(total_fees),
            'breakeven_required_days': int((total_fees / (sell - buy) * 30).to_integral_value()) if sell > buy else None
        }

    @staticmethod
    def calculate_competition_score(
        seller_count: Optional[int],
        fba_seller_count: Optional[int],
        amazon_on_listing: Optional[bool] = False
    ) -> Dict[str, Any]:
        """
        Calculate competition level based on seller count and FBA presence.
        """
        if seller_count is None:
            return {
                'competition_score': 50,
                'competition_level': 'UNKNOWN',
                'seller_count': None,
                'fba_ratio': None,
                'amazon_risk': 'UNKNOWN'
            }

        competition_score = 100

        if seller_count > 50:
            competition_score -= min(40, seller_count // 10)
        elif seller_count <= 3:
            competition_score += 20

        if fba_seller_count and seller_count and seller_count > 0:
            fba_ratio = fba_seller_count / seller_count
            if fba_ratio > 0.7:
                competition_score -= 15
        else:
            fba_ratio = None

        if amazon_on_listing:
            competition_score -= 25

        competition_score = max(0, min(100, competition_score))

        level = 'LOW' if competition_score >= 70 else 'MEDIUM' if competition_score >= 40 else 'HIGH'

        return {
            'competition_score': competition_score,
            'competition_level': level,
            'seller_count': seller_count,
            'fba_ratio': fba_ratio,
            'amazon_risk': 'CRITICAL' if amazon_on_listing else 'NONE'
        }

    # REMOVED: detect_dead_inventory method
    # This method used arbitrary BSR thresholds (50K, 30K, 100K) that didn't reflect
    # real sales velocity. Based on actual Keepa salesDrops data:
    # - BSR 200K = 15+ sales/month (NOT dead inventory)
    # - BSR 350K = 7+ sales/month (still sells regularly)
    # - Only 0-4 sales/month is truly "DEAD"
    #
    # Velocity risk is now calculated using SalesVelocityService with real Keepa data.
    # See analytics.py:_calculate_slow_velocity_risk()
