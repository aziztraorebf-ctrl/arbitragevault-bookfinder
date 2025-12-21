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
    BuyOpportunity,
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


def calculate_profit_with_buy_price(sell_price: float, buy_price: float) -> float:
    """Calculate profit given explicit buy and sell prices.

    Args:
        sell_price: Expected selling price on Amazon
        buy_price: Actual buy cost from seller

    Returns:
        Net profit after all fees
    """
    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]
    extra_weight = max(0, FBA_FEES["avg_book_weight"] - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])
    total_fees = referral + closing + fulfillment + FBA_FEES["prep_fee"] + FBA_FEES["inbound_shipping"]
    return sell_price - buy_price - total_fees


def calculate_roi(sell_price: float, buy_price: float) -> float:
    """Calculate ROI percentage.

    Args:
        sell_price: Expected selling price
        buy_price: Buy cost

    Returns:
        ROI as percentage
    """
    profit = calculate_profit_with_buy_price(sell_price, buy_price)
    if buy_price <= 0:
        return 0.0
    return (profit / buy_price) * 100


# Keepa condition codes mapping
CONDITION_MAP = {
    0: "Unknown",
    1: "New",
    2: "Used - Like New",
    3: "Used - Very Good",
    4: "Used - Good",
    5: "Used - Acceptable",
    6: "Refurbished",
    7: "Collectible - Like New",
    8: "Collectible - Very Good",
    9: "Collectible - Good",
    10: "Collectible - Acceptable",
}


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
            sell_price = current_data.get("price")
            if sell_price:
                profit = Decimal(str(round(calculate_profit(float(sell_price)), 2)))
                if request.saved_price:
                    saved_profit = calculate_profit(float(request.saved_price))
                    if saved_profit > 0:
                        profit_change = round(
                            ((float(profit) - saved_profit) / saved_profit) * 100, 1
                        )

            # Parse buy opportunities from seller offers
            # Pass both New and Used sell prices for correct profit calculation
            used_sell_price = current_data.get("used_price")
            buy_opportunities = self._parse_buy_opportunities(
                product_data,
                float(sell_price) if sell_price else None,
                float(used_sell_price) if used_sell_price else None
            )

            logger.info(
                f"[VERIFY] Completed for {request.asin}: status={status.value}, "
                f"buy_opportunities={len(buy_opportunities)}"
            )

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
                buy_opportunities=buy_opportunities,
                sell_price=sell_price,
                used_sell_price=used_sell_price,
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
            Dict with price, used_price, bsr, fba_count, amazon_selling
        """
        stats = product_data.get("stats", {})
        current = stats.get("current", [])

        # Keepa current array indices:
        # 0 = Amazon price, 1 = New price, 2 = Used price, 3 = Sales Rank, 11 = FBA seller count
        amazon_price = current[0] if len(current) > 0 else None
        new_price = current[1] if len(current) > 1 else None
        used_price = current[2] if len(current) > 2 else None
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
            "used_price": Decimal(str(used_price / 100)) if used_price and used_price > 0 else None,
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

    def _parse_buy_opportunities(
        self,
        product_data: dict,
        new_sell_price: Optional[float],
        used_sell_price: Optional[float]
    ) -> List[BuyOpportunity]:
        """Parse buy opportunities from Keepa product offers.

        IMPORTANT: Uses correct sell price based on condition:
        - New offers (condition=1) -> Compare to new_sell_price
        - Used offers (condition=2-5) -> Compare to used_sell_price

        Args:
            product_data: Raw Keepa product response with offers
            new_sell_price: Current New sell price for New offers
            used_sell_price: Current Used sell price for Used offers

        Returns:
            List of BuyOpportunity objects sorted by profit (descending)
        """
        if not new_sell_price and not used_sell_price:
            logger.warning("[VERIFY] No sell prices available, cannot calculate opportunities")
            return []

        offers = product_data.get("offers", [])
        live_offers_order = product_data.get("liveOffersOrder", [])

        if not offers or not live_offers_order:
            logger.info("[VERIFY] No offers data available")
            return []

        logger.info(
            f"[VERIFY] Parsing {len(live_offers_order)} live offers "
            f"from {len(offers)} total offers"
        )
        logger.info(f"[VERIFY] Sell prices - New: ${new_sell_price}, Used: ${used_sell_price}")

        buy_opportunities = []

        for offer_index in live_offers_order[:20]:  # Limit to first 20 live offers
            if offer_index >= len(offers):
                continue

            offer = offers[offer_index]

            # Skip Amazon as seller (cannot resell Amazon products)
            is_amazon = offer.get("isAmazon", False)
            if is_amazon:
                continue

            # Extract offer details
            seller_id = offer.get("sellerId", "Unknown")
            condition_code = offer.get("condition", 0)
            condition_str = CONDITION_MAP.get(condition_code, f"Unknown ({condition_code})")
            is_fba = offer.get("isFBA", False)
            is_prime = offer.get("isPrime", False)

            # Determine if New or Used offer
            is_new = condition_code == 1

            # Select appropriate sell price based on condition
            # New (1) -> use new_sell_price
            # Used (2-5) -> use used_sell_price
            if is_new:
                sell_price = new_sell_price
            else:
                sell_price = used_sell_price

            # Skip if no sell price for this condition type
            if not sell_price or sell_price <= 0:
                continue

            # Get current price from offerCSV (format: [time, price, shipping, time, price, shipping, ...])
            # Each entry is a triplet: timestamp (Keepa minutes), price (cents), shipping (cents)
            offer_csv = offer.get("offerCSV", [])
            if not offer_csv or len(offer_csv) < 3:
                continue

            # Last triplet: [-3]=time, [-2]=price, [-1]=shipping
            current_price_cents = offer_csv[-2]
            if not current_price_cents or current_price_cents <= 0:
                continue

            item_price = current_price_cents / 100.0

            # Shipping cost is the last element of the triplet (in cents)
            shipping_cents = offer_csv[-1] if len(offer_csv) >= 1 else 0
            shipping = (shipping_cents / 100.0) if shipping_cents and shipping_cents > 0 else 0.0

            # Total buy cost
            total_cost = item_price + shipping

            # Calculate profit and ROI using CORRECT sell price for condition
            profit = calculate_profit_with_buy_price(sell_price, total_cost)
            roi = calculate_roi(sell_price, total_cost)

            # Only include profitable opportunities
            if profit <= 0:
                continue

            opportunity = BuyOpportunity(
                seller_id=seller_id[:20],  # Truncate long seller IDs
                condition=condition_str,
                condition_code=condition_code,
                is_new=is_new,
                price=Decimal(str(round(item_price, 2))),
                shipping=Decimal(str(round(shipping, 2))),
                total_cost=Decimal(str(round(total_cost, 2))),
                sell_price=Decimal(str(round(sell_price, 2))),
                profit=Decimal(str(round(profit, 2))),
                roi_percent=round(roi, 1),
                is_fba=is_fba,
                is_prime=is_prime
            )

            buy_opportunities.append(opportunity)

        # Sort by profit descending (best deals first)
        buy_opportunities.sort(key=lambda x: float(x.profit), reverse=True)

        # Limit to top 10 opportunities
        buy_opportunities = buy_opportunities[:10]

        new_count = sum(1 for o in buy_opportunities if o.is_new)
        used_count = len(buy_opportunities) - new_count
        logger.info(
            f"[VERIFY] Found {len(buy_opportunities)} profitable opportunities "
            f"(New: {new_count}, Used: {used_count})"
        )

        return buy_opportunities
