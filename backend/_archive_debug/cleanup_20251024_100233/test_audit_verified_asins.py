"""
Test Keepa API with 3 verified recent ASINs
Created: 2025-10-14
Purpose: Phase 1 of audit - confirm API returns fresh data for active products
"""

import requests
import os
from datetime import datetime

# Keepa API configuration
KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"
KEEPA_EPOCH = 971222400  # 21 Oct 2000 00:00:00 GMT

# 3 verified recent Amazon USA bestsellers
TEST_ASINS = [
    "B0CHWRXH8B",  # Apple AirPods Pro 2nd Gen USB-C (verified active 2024)
    "0593655036",  # All the Light We Cannot See (consistent bestseller)
    "1250301696"   # The 48 Laws of Power (perennial bestseller)
]

def keepa_timestamp_to_datetime(keepa_minutes: int) -> datetime:
    """Convert Keepa timestamp to datetime."""
    timestamp_seconds = KEEPA_EPOCH + (keepa_minutes * 60)
    return datetime.fromtimestamp(timestamp_seconds)

def test_keepa_with_update_zero():
    """Test Keepa API with update=0 (force live scraping)."""

    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not found in environment")
        return

    print("="*80)
    print("KEEPA AUDIT - Phase 1: Testing API with update=0")
    print("="*80)
    print(f"Using Keepa epoch: {KEEPA_EPOCH}")
    print(f"Testing {len(TEST_ASINS)} verified ASINs")
    print()

    for idx, asin in enumerate(TEST_ASINS, 1):
        print(f"\n--- Test {idx}/{len(TEST_ASINS)}: ASIN {asin} ---")

        params = {
            "key": KEEPA_API_KEY,
            "domain": 1,  # .com
            "asin": asin,
            "stats": 180,
            "history": 1,
            "offers": 20,
            "update": 0  # Force live data
        }

        try:
            print(f"[REQUEST] Calling Keepa API with update=0...")
            response = requests.get(
                f"{KEEPA_BASE_URL}/product",
                params=params,
                timeout=30  # Increased timeout for live scraping
            )

            print(f"[RESPONSE] Status: {response.status_code}")

            if response.status_code != 200:
                print(f"ERROR: API returned {response.status_code}")
                print(f"Response: {response.text[:500]}")
                continue

            data = response.json()

            # Check tokens remaining
            tokens_left = data.get("tokensLeft", "unknown")
            print(f"[TOKENS] Tokens left: {tokens_left}")

            # Get product data
            products = data.get("products", [])
            if not products:
                print("ERROR: No products in response")
                continue

            product = products[0]

            # Extract key timestamps
            last_update = product.get("lastUpdate")
            last_price_change = product.get("lastPriceChange")

            print(f"\n[TIMESTAMPS]")
            print(f"  lastUpdate (raw): {last_update}")
            print(f"  lastPriceChange (raw): {last_price_change}")

            if last_update:
                last_update_dt = keepa_timestamp_to_datetime(last_update)
                age_hours = (datetime.now() - last_update_dt).total_seconds() / 3600
                print(f"  lastUpdate (datetime): {last_update_dt}")
                print(f"  Data age: {age_hours:.1f} hours ({age_hours/24:.1f} days)")

            if last_price_change:
                last_price_change_dt = keepa_timestamp_to_datetime(last_price_change)
                price_age_days = (datetime.now() - last_price_change_dt).days
                print(f"  lastPriceChange (datetime): {last_price_change_dt}")
                print(f"  Price change age: {price_age_days} days")

            # Extract current prices
            csv_amazon = product.get("csv", [[]])
            if csv_amazon and len(csv_amazon) > 0 and len(csv_amazon[0]) >= 2:
                latest_price_cents = csv_amazon[0][-1]
                if latest_price_cents and latest_price_cents != -1:
                    print(f"\n[PRICE] Latest Amazon price: ${latest_price_cents/100:.2f}")

            # Data freshness verdict
            print(f"\n[VERDICT]")
            if last_update:
                if age_hours < 24:
                    print(f"  FRESH DATA (< 24h)")
                elif age_hours < 168:  # 7 days
                    print(f"  ACCEPTABLE DATA (< 7 days)")
                else:
                    print(f"  OLD DATA (> 7 days)")

            print(f"\n" + "-"*80)

        except requests.Timeout:
            print(f"ERROR: Request timeout (update=0 takes longer)")
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_keepa_with_update_zero()
