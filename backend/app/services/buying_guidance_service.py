"""
Buying Guidance Service - User-Friendly Buying Recommendations

This service transforms intrinsic value corridor data into clear, actionable
buying guidance with French labels and tooltips explanations.

Author: Claude Opus 4.5
Date: January 2026
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional

from app.core.fees_config import calculate_total_fees

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Default target ROI
DEFAULT_TARGET_ROI = 0.50  # 50%

# French confidence labels mapping
CONFIDENCE_LABELS_FR = {
    'HIGH': 'Fiable',
    'MEDIUM': 'Modere',
    'LOW': 'Incertain',
    'INSUFFICIENT_DATA': 'Donnees insuffisantes'
}

# ROI thresholds for recommendations
ROI_THRESHOLD_BUY = 50.0  # >= 50% ROI = BUY
ROI_THRESHOLD_HOLD = 30.0  # >= 30% ROI = HOLD, below = SKIP

# Days estimation constants
DEFAULT_MAX_DAYS = 90  # Max days to sell estimate
DAYS_PER_MONTH = 30


def calculate_fee_percentage(
    sell_price: float,
    weight_lbs: float = 1.0,
    category: str = "books"
) -> float:
    """
    Calculate the actual fee percentage for a given sell price using canonical fees.

    This replaces the hardcoded 22% approximation with real fee calculation.

    Args:
        sell_price: Expected selling price.
        weight_lbs: Product weight in pounds (default 1.0 for books).
        category: Product category for fee lookup.

    Returns:
        Fee percentage as decimal (e.g., 0.22 for 22%).
    """
    if sell_price <= 0:
        return 0.0

    fees = calculate_total_fees(
        Decimal(str(sell_price)),
        Decimal(str(weight_lbs)),
        category
    )
    total_fees = float(fees["total_fees"])
    return total_fees / sell_price


# =============================================================================
# DATACLASS
# =============================================================================

@dataclass
class BuyingGuidance:
    """
    User-friendly buying guidance with all metrics and explanations.
    """
    max_buy_price: float
    target_sell_price: float
    estimated_profit: float
    estimated_roi_pct: float
    price_range: str
    estimated_days_to_sell: int
    recommendation: str  # "BUY", "HOLD", "SKIP"
    recommendation_reason: str
    confidence_label: str  # French labels
    explanations: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_max_buy_price(
    sell_price: float,
    fee_pct: float,
    target_roi: float
) -> float:
    """
    Calculate the maximum price to pay for a target ROI.

    Formula: max_buy = sell_price * (1 - fee_pct) / (1 + target_roi)

    Args:
        sell_price: Expected selling price.
        fee_pct: Fee percentage as decimal (e.g., 0.22 for 22%).
        target_roi: Target ROI as decimal (e.g., 0.50 for 50%).

    Returns:
        Maximum buy price to achieve target ROI, or 0.0 if invalid inputs.
    """
    # Validate inputs
    if sell_price <= 0:
        return 0.0
    if target_roi < 0:
        return 0.0
    if fee_pct < 0 or fee_pct >= 1:
        fee_pct = max(0, min(fee_pct, 0.99))

    try:
        net_after_fees = sell_price * (1 - fee_pct)
        max_buy = net_after_fees / (1 + target_roi)
        return round(max_buy, 2)
    except (ZeroDivisionError, ValueError):
        return 0.0


# =============================================================================
# SERVICE CLASS
# =============================================================================

class BuyingGuidanceService:
    """
    Service for generating user-friendly buying guidance from intrinsic value data.
    """

    def __init__(
        self,
        default_target_roi: float = DEFAULT_TARGET_ROI,
        default_fee_pct: Optional[float] = None
    ):
        """
        Initialize the service with default parameters.

        Args:
            default_target_roi: Default target ROI (0.50 = 50%).
            default_fee_pct: Default fee percentage. If None, calculated dynamically
                            using canonical fee calculation from fees_config.
        """
        self.default_target_roi = default_target_roi
        self.default_fee_pct = default_fee_pct

    def calculate_guidance(
        self,
        intrinsic_result: Dict[str, Any],
        velocity_data: Dict[str, Any],
        source_price: float,
        fee_pct: Optional[float] = None,
        target_roi: Optional[float] = None
    ) -> BuyingGuidance:
        """
        Calculate comprehensive buying guidance from intrinsic value data.

        Args:
            intrinsic_result: Output from calculate_intrinsic_value_corridor().
            velocity_data: Velocity data with monthly_sales, velocity_tier, etc.
            source_price: The price at which the book can be sourced.
            fee_pct: Fee percentage. If None, calculated dynamically from sell price.
            target_roi: Target ROI (defaults to self.default_target_roi).

        Returns:
            BuyingGuidance dataclass with all calculated metrics.
        """
        target_roi = target_roi if target_roi is not None else self.default_target_roi

        # Extract intrinsic values
        confidence = intrinsic_result.get('confidence', 'INSUFFICIENT_DATA')
        median_price = intrinsic_result.get('median')
        low_price = intrinsic_result.get('low')
        high_price = intrinsic_result.get('high')

        # Handle insufficient data case
        if confidence == 'INSUFFICIENT_DATA' or median_price is None:
            return self._create_insufficient_data_guidance(
                source_price=source_price,
                intrinsic_result=intrinsic_result
            )

        # Determine fee percentage: use provided, instance default, or calculate dynamically
        if fee_pct is not None:
            effective_fee_pct = fee_pct
        elif self.default_fee_pct is not None:
            effective_fee_pct = self.default_fee_pct
        else:
            # Calculate dynamically using canonical fees
            effective_fee_pct = calculate_fee_percentage(median_price)

        # Calculate max buy price
        max_buy = calculate_max_buy_price(
            sell_price=median_price,
            fee_pct=effective_fee_pct,
            target_roi=target_roi
        )

        # Calculate profit and ROI
        net_sell = median_price * (1 - effective_fee_pct)
        estimated_profit = round(net_sell - source_price, 2)
        estimated_roi_pct = round((estimated_profit / source_price) * 100, 1) if source_price > 0 else 0.0

        # Format price range
        price_range = self._format_price_range(low_price, high_price)

        # Estimate days to sell
        estimated_days = self._estimate_days_to_sell(velocity_data)

        # Get French confidence label
        confidence_label = CONFIDENCE_LABELS_FR.get(confidence, 'Donnees insuffisantes')

        # Determine recommendation
        recommendation, reason = self._determine_recommendation(
            roi_pct=estimated_roi_pct,
            confidence=confidence,
            confidence_label=confidence_label
        )

        # Build explanations
        explanations = self._build_explanations(target_roi, effective_fee_pct)

        return BuyingGuidance(
            max_buy_price=max_buy,
            target_sell_price=median_price,
            estimated_profit=estimated_profit,
            estimated_roi_pct=estimated_roi_pct,
            price_range=price_range,
            estimated_days_to_sell=estimated_days,
            recommendation=recommendation,
            recommendation_reason=reason,
            confidence_label=confidence_label,
            explanations=explanations
        )

    def _create_insufficient_data_guidance(
        self,
        source_price: float,
        intrinsic_result: Dict[str, Any]
    ) -> BuyingGuidance:
        """
        Create guidance for insufficient data case.
        """
        # Use a default fee percentage for explanations when we have no price to calculate from
        # Typical books fee ~20% at mid-range prices
        display_fee_pct = self.default_fee_pct if self.default_fee_pct is not None else 0.20
        return BuyingGuidance(
            max_buy_price=0.0,
            target_sell_price=0.0,
            estimated_profit=0.0,
            estimated_roi_pct=0.0,
            price_range="N/A",
            estimated_days_to_sell=DEFAULT_MAX_DAYS,
            recommendation="SKIP",
            recommendation_reason="Donnees insuffisantes pour calculer une recommandation fiable. "
                                 "Historique de prix trop limite.",
            confidence_label=CONFIDENCE_LABELS_FR['INSUFFICIENT_DATA'],
            explanations=self._build_explanations(self.default_target_roi, display_fee_pct)
        )

    def _format_price_range(
        self,
        low_price: Optional[float],
        high_price: Optional[float]
    ) -> str:
        """
        Format price range as '$XX - $YY'.
        """
        if low_price is None or high_price is None:
            return "N/A"

        # Round to integers for cleaner display
        low_int = int(round(low_price))
        high_int = int(round(high_price))

        return f"${low_int} - ${high_int}"

    def _estimate_days_to_sell(self, velocity_data: Dict[str, Any]) -> int:
        """
        Estimate days to sell based on velocity data.

        Formula: days = 30 / monthly_sales (capped at DEFAULT_MAX_DAYS)
        """
        monthly_sales = velocity_data.get('monthly_sales', 0)

        if monthly_sales <= 0:
            return DEFAULT_MAX_DAYS

        # Days per sale = 30 / monthly_sales
        days_per_sale = DAYS_PER_MONTH / monthly_sales

        # Round and cap
        estimated_days = int(round(days_per_sale))
        return max(1, min(estimated_days, DEFAULT_MAX_DAYS))

    def _determine_recommendation(
        self,
        roi_pct: float,
        confidence: str,
        confidence_label: str
    ) -> tuple:
        """
        Determine BUY/HOLD/SKIP recommendation based on ROI and confidence.

        Logic:
            - ROI >= 100% + HIGH confidence -> BUY
            - ROI >= 50% + HIGH/MEDIUM confidence -> BUY
            - ROI >= 30% -> HOLD
            - ROI < 30% or INSUFFICIENT_DATA -> SKIP
        """
        # Negative ROI = automatic SKIP
        if roi_pct < 0:
            return "SKIP", f"ROI negatif ({roi_pct:.1f}%). Cette opportunite genere une perte."

        # INSUFFICIENT_DATA = automatic SKIP (handled earlier but double-check)
        if confidence == 'INSUFFICIENT_DATA':
            return "SKIP", "Donnees insuffisantes pour une recommandation fiable."

        # High ROI (>= 100%) with HIGH confidence = strong BUY
        if roi_pct >= 100.0 and confidence == 'HIGH':
            return "BUY", f"Excellente opportunite: ROI de {roi_pct:.1f}% avec confiance {confidence_label}."

        # ROI >= 50% with HIGH or MEDIUM confidence = BUY
        if roi_pct >= ROI_THRESHOLD_BUY and confidence in ('HIGH', 'MEDIUM'):
            return "BUY", f"Bonne opportunite: ROI de {roi_pct:.1f}% avec confiance {confidence_label}."

        # ROI >= 50% with LOW confidence = HOLD (need more certainty)
        if roi_pct >= ROI_THRESHOLD_BUY and confidence == 'LOW':
            return "HOLD", f"ROI interessant ({roi_pct:.1f}%) mais confiance {confidence_label}. Verifier manuellement."

        # ROI 30-50% = HOLD
        if roi_pct >= ROI_THRESHOLD_HOLD:
            return "HOLD", f"ROI modere ({roi_pct:.1f}%). A considerer si les ventes sont rapides."

        # ROI < 30% = SKIP
        return "SKIP", f"ROI insuffisant ({roi_pct:.1f}%). Marge trop faible pour couvrir les risques."

    def _build_explanations(self, target_roi: float, fee_pct: float) -> Dict[str, str]:
        """
        Build explanations dictionary for tooltips.
        All explanations are in French without emojis.
        """
        target_roi_pct = int(target_roi * 100)
        fee_pct_display = int(fee_pct * 100)

        return {
            'max_buy_price': f"Prix maximum a payer pour garantir {target_roi_pct}% de ROI apres frais Amazon.",
            'target_sell_price': "Prix median des 90 derniers jours. Plus fiable qu'un prix ponctuel.",
            'estimated_profit': f"Profit net apres deduction des frais ({fee_pct_display}%).",
            'estimated_roi_pct': "Retour sur investissement: (profit / cout d'achat) x 100.",
            'price_range': "Fourchette de prix P25-P75 sur les 90 derniers jours.",
            'estimated_days_to_sell': "Estimation du delai de vente basee sur la velocite historique.",
            'recommendation': "Recommandation basee sur le ROI et la fiabilite des donnees.",
            'confidence_label': "Niveau de fiabilite des donnees historiques (nombre de points + volatilite)."
        }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    'BuyingGuidance',
    'BuyingGuidanceService',
    'calculate_fee_percentage',
    'calculate_max_buy_price',
]
