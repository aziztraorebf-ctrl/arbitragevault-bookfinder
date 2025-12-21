"""
Test Script: Keepa API Offers/Sellers Data
==========================================

Phase 9: Test script to verify we can retrieve seller offers for buy opportunities.

Goal: When user clicks "Verify", show available sellers with their prices
so user can make an informed purchase decision.

Usage:
    cd backend
    KEEPA_API_KEY="your_key" python scripts/test_keepa_offers.py

Expected output:
    - List of sellers with prices
    - Seller condition (New, Used, etc.)
    - Whether seller is FBA
    - Calculated profit for each offer
"""

import asyncio
import os
import sys
import json
from decimal import Decimal
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.keepa_service import KeepaService
from app.core.config import settings


# FBA Fee structure for Books
FBA_FEES = {
    "referral_percent": 0.15,
    "closing_fee": 1.80,
    "fba_base": 3.22,
    "fba_per_lb": 0.75,
    "avg_book_weight": 1.5,
    "prep_fee": 0.50,
    "inbound_shipping": 0.40,
}


def calculate_profit(sell_price: float, buy_price: float) -> float:
    """Calculate profit given sell and buy prices."""
    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]
    extra_weight = max(0, FBA_FEES["avg_book_weight"] - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])
    total_fees = referral + closing + fulfillment + FBA_FEES["prep_fee"] + FBA_FEES["inbound_shipping"]
    return sell_price - buy_price - total_fees


def calculate_roi(sell_price: float, buy_price: float) -> float:
    """Calculate ROI percentage."""
    profit = calculate_profit(sell_price, buy_price)
    if buy_price <= 0:
        return 0.0
    return (profit / buy_price) * 100


# Keepa condition codes
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


async def test_keepa_offers():
    """Test retrieving seller offers from Keepa API."""

    print("=" * 60)
    print("KEEPA API OFFERS TEST")
    print("=" * 60)

    # Test ASIN - from the screenshot
    test_asin = "0061801313"  # Pretty Little Liars Box Set

    # Alternative test ASINs
    alternative_asins = [
        "1454857935",  # From Keepa docs
        "0316769177",  # The Lovely Bones
    ]

    print(f"\nTest ASIN: {test_asin}")
    print(f"API Key configured: {bool(settings.KEEPA_API_KEY)}")

    if not settings.KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        return

    # Initialize service
    keepa = KeepaService(api_key=settings.KEEPA_API_KEY)

    try:
        # Check token balance first
        balance = await keepa.check_api_balance()
        print(f"Token balance: {balance}")

        if balance < 10:
            print("WARNING: Low token balance, test may fail")

        print("\n" + "-" * 60)
        print("TEST 1: Get product with offers=20")
        print("-" * 60)

        # Call Keepa API with offers parameter
        # We need to modify the request to include offers
        endpoint = "/product"
        params = {
            "domain": 1,  # US
            "asin": test_asin,
            "offers": 20,  # Request up to 20 seller offers
            "history": 1,  # Need history for stats.current prices
            "stats": 1,    # Get current stats (prices, BSR)
            "rating": 0,
            "stock": 0,
        }

        print(f"Request params: {params}")

        response = await keepa._make_request(endpoint, params)

        if not response:
            print("ERROR: No response from Keepa API")
            return

        # Check tokens consumed
        tokens_consumed = response.get("tokensConsumed", 0)
        print(f"Tokens consumed: {tokens_consumed}")

        products = response.get("products", [])
        if not products:
            print("ERROR: No products in response")
            return

        product = products[0]

        # Basic product info
        print(f"\nProduct: {product.get('title', 'N/A')[:60]}...")
        print(f"ASIN: {product.get('asin', 'N/A')}")

        # Get current sell price (New price)
        stats = product.get("stats", {})
        current = stats.get("current", [])

        # Debug: show current array
        print(f"\nDEBUG stats.current (first 15 values):")
        for i, val in enumerate(current[:15]):
            print(f"  [{i}] = {val}")

        # Index 1 = New price (in cents)
        new_price_cents = current[1] if len(current) > 1 else None
        sell_price = new_price_cents / 100 if new_price_cents and new_price_cents > 0 else None

        # Index 3 = BSR
        bsr = current[3] if len(current) > 3 else None

        # If New price not available, try to get from live offers (Buy Box)
        if not sell_price:
            # Check if there's a buyBoxPrice in stats
            buy_box = stats.get("buyBoxPrice", None)
            if buy_box and buy_box > 0:
                sell_price = buy_box / 100
                print(f"Using buyBoxPrice as sell price")

        # Also check the csv array for current NEW price
        csv = product.get("csv", [])
        if csv and len(csv) > 1:
            new_csv = csv[1] if len(csv) > 1 else []
            if new_csv and len(new_csv) >= 2:
                # Last value in csv is current price
                last_new_price = new_csv[-1] if new_csv[-1] and new_csv[-1] > 0 else None
                if last_new_price and not sell_price:
                    sell_price = last_new_price / 100
                    print(f"Using csv[1] last value as sell price")

        print(f"\nCurrent sell price (New): ${sell_price:.2f}" if sell_price else "\nSell price: N/A")
        print(f"BSR: #{bsr:,}" if bsr else "BSR: N/A")

        print("\n" + "-" * 60)
        print("TEST 2: Parse seller offers")
        print("-" * 60)

        offers = product.get("offers", [])
        live_offers_order = product.get("liveOffersOrder", [])

        print(f"Total offers in response: {len(offers)}")
        print(f"Live offers count: {len(live_offers_order)}")

        if not offers:
            print("No offers found - trying with different approach...")
            # Some products may not have offers data
            return

        # Parse live offers
        print("\n" + "=" * 60)
        print("LIVE SELLER OFFERS (Buy Opportunities)")
        print("=" * 60)

        buy_opportunities = []

        for idx, offer_index in enumerate(live_offers_order[:10]):  # Limit to 10
            if offer_index >= len(offers):
                continue

            offer = offers[offer_index]

            # Extract offer data
            seller_id = offer.get("sellerId", "Unknown")
            condition = offer.get("condition", 0)
            condition_str = CONDITION_MAP.get(condition, f"Unknown ({condition})")
            is_fba = offer.get("isFBA", False)
            is_prime = offer.get("isPrime", False)
            is_amazon = offer.get("isAmazon", False)

            # Get current price from offerCSV (last value)
            offer_csv = offer.get("offerCSV", [])
            if offer_csv and len(offer_csv) >= 2:
                # offerCSV format: [time1, price1, time2, price2, ...]
                # Last price is at index -1
                current_offer_price_cents = offer_csv[-1]
                offer_price = current_offer_price_cents / 100 if current_offer_price_cents > 0 else None
            else:
                offer_price = None

            # Shipping cost
            shipping_cents = offer.get("shipping", 0)
            shipping = shipping_cents / 100 if shipping_cents else 0

            # Total buy cost
            total_buy_cost = (offer_price + shipping) if offer_price else None

            # Calculate profit if we have both prices
            profit = None
            roi = None
            if sell_price and total_buy_cost:
                profit = calculate_profit(sell_price, total_buy_cost)
                roi = calculate_roi(sell_price, total_buy_cost)

            offer_data = {
                "seller_id": seller_id,
                "condition": condition_str,
                "is_fba": is_fba,
                "is_prime": is_prime,
                "is_amazon": is_amazon,
                "price": offer_price,
                "shipping": shipping,
                "total_cost": total_buy_cost,
                "profit": profit,
                "roi": roi,
            }

            # Skip Amazon as seller (we want third-party sellers)
            if is_amazon:
                print(f"\n[{idx+1}] AMAZON (skipped - cannot buy from Amazon to resell)")
                continue

            # Skip if no price
            if not offer_price:
                print(f"\n[{idx+1}] Seller {seller_id[:10]}... - No price available")
                continue

            buy_opportunities.append(offer_data)

            print(f"\n[{idx+1}] Seller: {seller_id[:15]}...")
            print(f"    Condition: {condition_str}")
            print(f"    Price: ${offer_price:.2f}" if offer_price else "    Price: N/A")
            print(f"    Shipping: ${shipping:.2f}")
            print(f"    Total Buy Cost: ${total_buy_cost:.2f}" if total_buy_cost else "    Total: N/A")
            print(f"    FBA: {'Yes' if is_fba else 'No'} | Prime: {'Yes' if is_prime else 'No'}")
            if profit is not None:
                profit_color = "PROFIT" if profit > 0 else "LOSS"
                print(f"    {profit_color}: ${profit:.2f} (ROI: {roi:.1f}%)")

        print("\n" + "=" * 60)
        print("SUMMARY: BUY OPPORTUNITIES")
        print("=" * 60)

        # Filter profitable opportunities (handle None values)
        profitable = [o for o in buy_opportunities if (o.get("profit") or 0) > 0]
        profitable.sort(key=lambda x: x.get("profit", 0), reverse=True)

        print(f"\nSell Price on Amazon: ${sell_price:.2f}" if sell_price else "Sell Price: N/A")
        print(f"Total offers found: {len(buy_opportunities)}")
        print(f"Profitable offers: {len(profitable)}")

        if profitable:
            print("\nTop 3 Best Buy Opportunities:")
            for i, opp in enumerate(profitable[:3]):
                print(f"  {i+1}. ${opp['total_cost']:.2f} ({opp['condition']}) -> Profit: ${opp['profit']:.2f} ({opp['roi']:.1f}% ROI)")
        else:
            print("\nNo profitable opportunities found at current prices.")

        print("\n" + "-" * 60)
        print("TEST 3: Raw offer structure (for debugging)")
        print("-" * 60)

        if offers:
            # Show first offer structure
            first_offer = offers[0]
            print("\nFirst offer keys:")
            for key in first_offer.keys():
                value = first_offer[key]
                if isinstance(value, list) and len(value) > 5:
                    print(f"  {key}: [{type(value[0]).__name__}...] (len={len(value)})")
                else:
                    print(f"  {key}: {value}")

        # Final token balance
        final_balance = await keepa.check_api_balance()
        print(f"\nFinal token balance: {final_balance}")
        print(f"Tokens used in test: {balance - final_balance}")

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await keepa.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_keepa_offers())
