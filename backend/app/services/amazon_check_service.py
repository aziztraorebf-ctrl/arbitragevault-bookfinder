"""Amazon Check Service - Phase 2.5A Step 1.

Detects Amazon presence on product listings:
- amazon_on_listing: Amazon has any offer on the product
- amazon_buybox: Amazon currently owns the Buy Box

Uses raw Keepa product data (offers array with isAmazon field).

BUILD_TAG: PHASE_2_5A_STEP_1
"""

from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


def check_amazon_presence(keepa_data: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """Check if Amazon is present on listing or owns Buy Box.

    Args:
        keepa_data: Raw Keepa product dict from keepa.query() or get_product_data()

    Returns:
        Dict with:
        - amazon_on_listing (bool): Amazon has any offer on the product
        - amazon_buybox (bool): Amazon currently owns the Buy Box

    Note:
        - Requires offers data (query with offers=20)
        - Uses offers[].isAmazon field (official Keepa API field)
        - Returns False for both if offers data unavailable
    """
    result = {"amazon_on_listing": False, "amazon_buybox": False}

    # Handle None input gracefully
    if keepa_data is None:
        logger.warning("check_amazon_presence called with None keepa_data")
        return result

    try:
        # Method 0: Check availabilityAmazon field (most reliable, always present)
        # From Keepa docs: availabilityAmazon >= 0 means Amazon has stock
        # Values: -1 = not available, 0+ = available (value indicates delay code)
        availability_amazon = keepa_data.get("availabilityAmazon")
        if availability_amazon is not None and availability_amazon >= 0:
            result["amazon_on_listing"] = True
            logger.debug(
                "Amazon detected via availabilityAmazon",
                asin=keepa_data.get("asin"),
                availability_amazon=availability_amazon,
            )

        # Check if offers data exists for more detailed analysis
        offers = keepa_data.get("offers")
        if not offers or not isinstance(offers, list):
            logger.debug(
                "No offers data in Keepa response, using availabilityAmazon only",
                has_offers=bool(offers),
                asin=keepa_data.get("asin"),
                amazon_detected=result["amazon_on_listing"],
            )
            return result

        # Method 1: Check offers[].isAmazon for confirmation
        # This confirms availabilityAmazon and can detect Amazon even if availabilityAmazon is missing
        for offer in offers:
            if isinstance(offer, dict) and offer.get("isAmazon") is True:
                if not result["amazon_on_listing"]:
                    result["amazon_on_listing"] = True
                    logger.debug(
                        "Amazon detected via offers[].isAmazon",
                        asin=keepa_data.get("asin"),
                        seller_id=offer.get("sellerId"),
                    )
                break

        # Check if Amazon owns Buy Box (amazon_buybox)
        # Method 1: Check buyBoxSellerIdHistory for most recent entry
        buybox_history = keepa_data.get("buyBoxSellerIdHistory")
        if buybox_history and isinstance(buybox_history, list) and len(buybox_history) >= 2:
            # buyBoxSellerIdHistory format: [time, sellerId, time, sellerId, ...]
            # Most recent entry is at index -1 (last sellerId)
            most_recent_seller_id = buybox_history[-1]

            # Find this seller in offers to check if it's Amazon
            for offer in offers:
                if (
                    isinstance(offer, dict)
                    and offer.get("sellerId") == most_recent_seller_id
                    and offer.get("isAmazon") is True
                ):
                    result["amazon_buybox"] = True
                    logger.debug(
                        "Amazon owns Buy Box",
                        asin=keepa_data.get("asin"),
                        seller_id=most_recent_seller_id,
                    )
                    break

        # Method 2: Fallback to liveOffersOrder (current active offers order)
        if not result["amazon_buybox"]:
            live_offers_order = keepa_data.get("liveOffersOrder")
            if live_offers_order and isinstance(live_offers_order, list) and len(live_offers_order) > 0:
                # First offer in liveOffersOrder is typically the Buy Box winner
                first_offer_index = live_offers_order[0]
                if 0 <= first_offer_index < len(offers):
                    first_offer = offers[first_offer_index]
                    if isinstance(first_offer, dict) and first_offer.get("isAmazon") is True:
                        result["amazon_buybox"] = True
                        logger.debug(
                            "Amazon owns Buy Box (via liveOffersOrder)",
                            asin=keepa_data.get("asin"),
                            seller_id=first_offer.get("sellerId"),
                        )

        logger.info(
            "Amazon presence check complete",
            asin=keepa_data.get("asin"),
            amazon_on_listing=result["amazon_on_listing"],
            amazon_buybox=result["amazon_buybox"],
        )

        return result

    except Exception as e:
        logger.error(
            "Error checking Amazon presence",
            error=str(e),
            asin=keepa_data.get("asin"),
            exc_info=True,
        )
        # Return False for both on error (safe default)
        return {"amazon_on_listing": False, "amazon_buybox": False}
