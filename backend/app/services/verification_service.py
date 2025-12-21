"""Verification Service for pre-purchase product verification.

Phase 8: Implements verification workflow comparing saved analysis data
against current Keepa API data to detect changes before purchase.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import logging

from app.schemas.verification import (
    VerificationStatus,
    VerificationChange,
    VerificationRequest,
    VerificationResponse,
    VerificationThresholds,
)
from app.services.keepa_service import KeepaService
from app.core.logging import get_logger

logger = get_logger(__name__)


# FBA Fee structure for Books (from PDF guide)
FBA_FEES = {
    "referral_percent": 0.15,
    "closing_fee": 1.80,
    "fba_base": 3.22,
    "fba_per_lb": 0.75,
    "avg_book_weight": 1.5,
    "prep_fee": 0.50,
    "inbound_shipping": 0.40,
}


def calculate_profit(sell_price: float, buy_cost_factor: float = 0.50) -> float:
    """Calculate realistic profit for a book.

    Args:
        sell_price: Expected selling price
        buy_cost_factor: Buy cost as fraction of sell price (default 50%)

    Returns:
        Net profit after all fees
    """
    buy_cost = sell_price * buy_cost_factor
    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]
    extra_weight = max(0, FBA_FEES["avg_book_weight"] - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])
    total_fees = referral + closing + fulfillment + FBA_FEES["prep_fee"] + FBA_FEES["inbound_shipping"]
    return sell_price - buy_cost - total_fees


class VerificationService:
    """Service for verifying product status before purchase.

    Compares saved analysis data against current Keepa API data to detect:
    - Price changes (significant increase/decrease)
    - BSR changes (rank degradation)
    - Competition changes (more FBA sellers)
    - Amazon selling status (critical - avoid if Amazon enters)
    """

    def __init__(
        self,
        keepa_service: KeepaService,
        thresholds: Optional[VerificationThresholds] = None
    ):
        """Initialize verification service.

        Args:
            keepa_service: KeepaService instance for API calls
            thresholds: Custom thresholds (uses defaults if None)
        """
        self.keepa = keepa_service
        self.thresholds = thresholds or VerificationThresholds()

    async def verify_product(self, request: VerificationRequest) -> VerificationResponse:
        """Verify a product's current status against saved analysis.

        Args:
            request: VerificationRequest with ASIN and saved values

        Returns:
            VerificationResponse with status, changes, and current data
        """
        logger.info(f"[VERIFY] Starting verification for {request.asin}")

        try:
            # Get current data from Keepa (force refresh for real-time data)
            product_data = await self.keepa.get_product_data(
                identifier=request.asin,
                domain=1,  # US
                force_refresh=True
            )

            if not product_data:
                logger.warning(f"[VERIFY] No data returned for {request.asin}")
                return VerificationResponse(
                    asin=request.asin,
                    status=VerificationStatus.AVOID,
                    message="Product not found in Keepa database",
                    verified_at=datetime.now(timezone.utc)
                )

            # Extract current values
            current_data = self._extract_current_data(product_data)

            # Check for Amazon selling (critical condition)
            if current_data.get("amazon_selling", False):
                logger.warning(f"[VERIFY] AVOID - Amazon is selling {request.asin}")
                return VerificationResponse(
                    asin=request.asin,
                    status=VerificationStatus.AVOID,
                    message="AVOID: Amazon is now selling this product",
                    amazon_selling=True,
                    current_price=current_data.get("price"),
                    current_bsr=current_data.get("bsr"),
                    current_fba_count=current_data.get("fba_count"),
                    verified_at=datetime.now(timezone.utc)
                )

            # Detect changes
            changes = self._detect_changes(request, current_data)

            # Determine overall status
            status, message = self._determine_status(changes, current_data)

            # Calculate profit impact
            profit = None
            profit_change = None
            if current_data.get("price"):
                profit = Decimal(str(round(calculate_profit(float(current_data["price"])), 2)))
                if request.saved_price:
                    saved_profit = calculate_profit(float(request.saved_price))
                    if saved_profit > 0:
                        profit_change = round(
                            ((float(profit) - saved_profit) / saved_profit) * 100, 1
                        )

            logger.info(f"[VERIFY] Completed for {request.asin}: status={status.value}")

            return VerificationResponse(
                asin=request.asin,
                status=status,
                message=message,
                current_price=current_data.get("price"),
                current_bsr=current_data.get("bsr"),
                current_fba_count=current_data.get("fba_count"),
                amazon_selling=current_data.get("amazon_selling", False),
                changes=changes,
                estimated_profit=profit,
                profit_change_percent=profit_change,
                verified_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"[VERIFY] Error verifying {request.asin}: {e}")
            return VerificationResponse(
                asin=request.asin,
                status=VerificationStatus.AVOID,
                message=f"Verification failed: {str(e)}",
                verified_at=datetime.now(timezone.utc)
            )

    def _extract_current_data(self, product_data: dict) -> dict:
        """Extract relevant current values from Keepa product data.

        Args:
            product_data: Raw Keepa product response

        Returns:
            Dict with price, bsr, fba_count, amazon_selling
        """
        stats = product_data.get("stats", {})
        current = stats.get("current", [])

        # Keepa current array indices:
        # 0 = Amazon price, 1 = New price, 3 = Sales Rank, 11 = FBA seller count
        amazon_price = current[0] if len(current) > 0 else None
        new_price = current[1] if len(current) > 1 else None
        bsr = current[3] if len(current) > 3 else None
        fba_count = current[11] if len(current) > 11 else None

        # Amazon selling detection: availabilityAmazon >= 0 OR amazon_price > 0
        availability_amazon = product_data.get("availabilityAmazon", -1)
        amazon_selling = (
            (availability_amazon is not None and availability_amazon >= 0) or
            (amazon_price is not None and amazon_price > 0)
        )

        return {
            "price": Decimal(str(new_price / 100)) if new_price and new_price > 0 else None,
            "bsr": bsr if bsr and bsr > 0 else None,
            "fba_count": fba_count if fba_count is not None else 0,
            "amazon_selling": amazon_selling
        }

    def _detect_changes(
        self,
        request: VerificationRequest,
        current: dict
    ) -> List[VerificationChange]:
        """Detect significant changes between saved and current data.

        Args:
            request: VerificationRequest with saved values
            current: Current data extracted from Keepa

        Returns:
            List of VerificationChange objects
        """
        changes = []

        # Price change detection
        if request.saved_price and current.get("price"):
            saved = float(request.saved_price)
            curr = float(current["price"])
            if saved > 0:
                pct_change = abs((curr - saved) / saved) * 100
                if pct_change >= self.thresholds.price_change_critical:
                    direction = "increased" if curr > saved else "decreased"
                    changes.append(VerificationChange(
                        field="price",
                        saved_value=saved,
                        current_value=curr,
                        severity="critical",
                        message=f"Price {direction} by {pct_change:.1f}% (${saved:.2f} -> ${curr:.2f})"
                    ))
                elif pct_change >= self.thresholds.price_change_warning:
                    direction = "increased" if curr > saved else "decreased"
                    changes.append(VerificationChange(
                        field="price",
                        saved_value=saved,
                        current_value=curr,
                        severity="warning",
                        message=f"Price {direction} by {pct_change:.1f}% (${saved:.2f} -> ${curr:.2f})"
                    ))

        # BSR change detection
        if request.saved_bsr and current.get("bsr"):
            saved = request.saved_bsr
            curr = current["bsr"]
            pct_change = abs((curr - saved) / saved) * 100
            if pct_change >= self.thresholds.bsr_change_critical:
                direction = "worsened" if curr > saved else "improved"
                changes.append(VerificationChange(
                    field="bsr",
                    saved_value=saved,
                    current_value=curr,
                    severity="critical",
                    message=f"BSR {direction} by {pct_change:.1f}% (#{saved:,} -> #{curr:,})"
                ))
            elif pct_change >= self.thresholds.bsr_change_warning:
                direction = "worsened" if curr > saved else "improved"
                changes.append(VerificationChange(
                    field="bsr",
                    saved_value=saved,
                    current_value=curr,
                    severity="warning",
                    message=f"BSR {direction} by {pct_change:.1f}% (#{saved:,} -> #{curr:,})"
                ))

        # FBA seller count change
        if request.saved_fba_count is not None and current.get("fba_count") is not None:
            saved = request.saved_fba_count
            curr = current["fba_count"]
            increase = curr - saved
            if increase >= self.thresholds.fba_count_critical:
                changes.append(VerificationChange(
                    field="fba_count",
                    saved_value=saved,
                    current_value=curr,
                    severity="critical",
                    message=f"FBA sellers increased by {increase} ({saved} -> {curr})"
                ))
            elif increase >= self.thresholds.fba_count_warning:
                changes.append(VerificationChange(
                    field="fba_count",
                    saved_value=saved,
                    current_value=curr,
                    severity="warning",
                    message=f"FBA sellers increased by {increase} ({saved} -> {curr})"
                ))

        return changes

    def _determine_status(
        self,
        changes: List[VerificationChange],
        current: dict
    ) -> tuple:
        """Determine overall verification status based on changes.

        Args:
            changes: List of detected changes
            current: Current data dict

        Returns:
            Tuple of (VerificationStatus, message string)
        """
        critical_changes = [c for c in changes if c.severity == "critical"]
        warning_changes = [c for c in changes if c.severity == "warning"]

        if critical_changes:
            fields = ", ".join(c.field for c in critical_changes)
            return (
                VerificationStatus.AVOID,
                f"Critical changes detected in: {fields}. Review before buying."
            )
        elif warning_changes:
            fields = ", ".join(c.field for c in warning_changes)
            return (
                VerificationStatus.CHANGED,
                f"Moderate changes detected in: {fields}. Verify profit still acceptable."
            )
        else:
            return (
                VerificationStatus.OK,
                "Product conditions unchanged. Safe to proceed with purchase."
            )
