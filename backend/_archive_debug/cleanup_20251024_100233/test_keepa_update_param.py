"""
Test script to validate Keepa update=1 parameter fix.
Compares old cache vs new live data for ASIN 0593655036.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.keepa_service import KeepaService
from datetime import datetime

async def test_keepa_live_refresh():
    """Test ASIN 0593655036 with update=1 (live refresh)"""

    # Get API key from environment
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        try:
            import keyring
            api_key = keyring.get_password("memex", "KEEPA_API_KEY")
        except:
            pass

    if not api_key:
        print("ERROR: KEEPA_API_KEY not found")
        return

    # Create service instance
    service = KeepaService(api_key=api_key)

    try:
        print("=" * 60)
        print("KEEPA update=1 VALIDATION TEST")
        print("=" * 60)
        print(f"ASIN: 0593655036 (The Anxious Generation)")
        print(f"Expected: Live data from Amazon (2025)")
        print(f"Old behavior: Cache from 2015")
        print("=" * 60)

        # Force refresh (bypass cache)
        product_data = await service.get_product_data(
            identifier="0593655036",
            domain=1,  # US
            force_refresh=True  # Skip cache
        )

        if not product_data:
            print("ERROR: No product data returned")
            return

        # Extract timestamps (Keepa format)
        keepa_epoch = 971222400
        last_update_keepa = product_data.get("lastUpdate", -1)
        last_price_change_keepa = product_data.get("lastPriceChange", -1)

        # Convert to readable dates
        def keepa_to_date(keepa_time):
            if keepa_time == -1:
                return "N/A"
            unix_ts = keepa_epoch + (keepa_time * 60)
            dt = datetime.fromtimestamp(unix_ts)
            age_days = (datetime.now() - dt).days
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_days} days old)"

        last_update_str = keepa_to_date(last_update_keepa)
        last_price_change_str = keepa_to_date(last_price_change_keepa)

        # Extract prices (CSV arrays)
        csv_data = product_data.get("csv", [])

        def get_last_price(array_idx, array_name):
            if array_idx < len(csv_data):
                price_array = csv_data[array_idx]
                if price_array and len(price_array) >= 2:
                    last_price = price_array[-1]
                    last_timestamp = price_array[-2]

                    if last_price != -1:
                        price_usd = last_price / 100.0
                        timestamp_str = keepa_to_date(last_timestamp)
                        return f"${price_usd:.2f} (timestamp: {timestamp_str})"
            return "N/A"

        amazon_price = get_last_price(0, "AMAZON")
        new_price = get_last_price(1, "NEW")
        fba_price = get_last_price(7, "FBA")
        buybox_price = get_last_price(12, "BUY_BOX")

        # Display results
        print("\nTIMESTAMP ANALYSIS:")
        print(f"  lastUpdate:       {last_update_str}")
        print(f"  lastPriceChange:  {last_price_change_str}")

        print("\nPRICE DATA EXTRACTED:")
        print(f"  Amazon Price:  {amazon_price}")
        print(f"  NEW Price:     {new_price}")
        print(f"  FBA Price:     {fba_price}")
        print(f"  BuyBox Price:  {buybox_price}")

        # Validation
        print("\n" + "=" * 60)
        print("VALIDATION:")

        # Check if lastPriceChange is recent (< 30 days = success)
        if last_price_change_keepa != -1:
            unix_ts = keepa_epoch + (last_price_change_keepa * 60)
            age_days = (datetime.now() - datetime.fromtimestamp(unix_ts)).days

            if age_days < 30:
                print("  [PASS] lastPriceChange is RECENT (< 30 days)")
            else:
                print(f"  [FAIL] lastPriceChange is OLD ({age_days} days)")

        # Check if prices are realistic (> $10)
        prices_to_check = [
            ("Amazon", amazon_price),
            ("NEW", new_price),
            ("BuyBox", buybox_price)
        ]

        realistic_prices = 0
        for name, price_str in prices_to_check:
            if "$" in price_str:
                price_val = float(price_str.split("$")[1].split(" ")[0])
                if price_val > 10.0:
                    realistic_prices += 1
                    print(f"  [PASS] {name} price is realistic (${price_val:.2f})")
                else:
                    print(f"  [FAIL] {name} price too low (${price_val:.2f})")

        if realistic_prices > 0:
            print(f"\n  SUCCESS: {realistic_prices}/3 prices are realistic")
        else:
            print("\n  FAILURE: All prices are obsolete cache data")

        print("=" * 60)

    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_keepa_live_refresh())
