"""
Test script to validate that force_refresh bypasses cache and uses update=0 for live data.
This test uses the actual keepa_service.py with our new logging.
"""
import asyncio
import sys
import os
import logging

# Setup logging to see our new log messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.keepa_service import KeepaService
from datetime import datetime

async def test_force_refresh_with_logs():
    """Test force_refresh behavior with our new logging"""

    # Get API key
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

    # Create service with logging enabled
    service = KeepaService(api_key=api_key)

    # Test ASINs (using different products to avoid cross-contamination)
    test_cases = [
        ("0593655036", "The Anxious Generation (book)"),
        ("B0D5FDDQLD", "iPhone 16 Pro (Oct 2024)"),
        ("B0CHX2F5HT", "Apple AirPods Pro 2nd Gen USB-C")
    ]

    print("=" * 80)
    print("FORCE REFRESH TEST WITH IMPROVED LOGGING")
    print("=" * 80)
    print("This test validates:")
    print("1. force_refresh=True bypasses cache")
    print("2. update=0 is used for live data")
    print("3. Logs clearly show data source")
    print("=" * 80)

    for asin, product_name in test_cases:
        print(f"\n{'='*80}")
        print(f"TESTING: {asin} ({product_name})")
        print("=" * 80)

        try:
            # TEST 1: Normal call (may use cache)
            print("\n[TEST 1] Normal call (force_refresh=False)")
            print("-" * 40)

            data1 = await service.get_product_data(
                identifier=asin,
                domain=1,
                force_refresh=False
            )

            if data1:
                # Extract price for comparison
                csv_data = data1.get("csv", [])
                buybox_price1 = "N/A"
                if len(csv_data) > 12 and csv_data[12] and len(csv_data[12]) >= 2:
                    price = csv_data[12][-1]
                    if price != -1:
                        buybox_price1 = f"${price / 100.0:.2f}"

                print(f"  BuyBox Price: {buybox_price1}")
            else:
                print(f"  No data returned")

            # WAIT 2 seconds
            print("\n[WAITING] 2 seconds before force refresh...")
            await asyncio.sleep(2)

            # TEST 2: Force refresh (must bypass cache, use update=0)
            print("\n[TEST 2] Force refresh call (force_refresh=True)")
            print("-" * 40)

            data2 = await service.get_product_data(
                identifier=asin,
                domain=1,
                force_refresh=True  # ← THIS SHOULD TRIGGER update=0
            )

            if data2:
                # Extract price for comparison
                csv_data = data2.get("csv", [])
                buybox_price2 = "N/A"
                if len(csv_data) > 12 and csv_data[12] and len(csv_data[12]) >= 2:
                    price = csv_data[12][-1]
                    if price != -1:
                        buybox_price2 = f"${price / 100.0:.2f}"

                print(f"  BuyBox Price: {buybox_price2}")

                # Check if data changed
                if buybox_price1 != buybox_price2:
                    print(f"  [DIFFERENT] Prices changed: {buybox_price1} → {buybox_price2}")
                else:
                    print(f"  [SAME] Price unchanged: {buybox_price2}")
            else:
                print(f"  No data returned")

            # TEST 3: Normal call again (should use cache from Test 2)
            print("\n[TEST 3] Normal call again (should use cached data from Test 2)")
            print("-" * 40)

            data3 = await service.get_product_data(
                identifier=asin,
                domain=1,
                force_refresh=False
            )

            if data3:
                csv_data = data3.get("csv", [])
                buybox_price3 = "N/A"
                if len(csv_data) > 12 and csv_data[12] and len(csv_data[12]) >= 2:
                    price = csv_data[12][-1]
                    if price != -1:
                        buybox_price3 = f"${price / 100.0:.2f}"

                print(f"  BuyBox Price: {buybox_price3}")

                # Should match Test 2 (same cache)
                if buybox_price2 == buybox_price3:
                    print(f"  [PASS] Using cached data from Test 2")
                else:
                    print(f"  [WARNING] Price changed unexpectedly")

        except Exception as e:
            print(f"  [ERROR] {e}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nEXPECTED LOGS:")
    print("  Test 1: [CACHE MISS] or [CACHE HIT]")
    print("  Test 2: [FORCE REFRESH] + [KEEPA API] with update=0")
    print("  Test 3: [CACHE HIT]")
    print("\nCheck the logs above to verify correct behavior!")
    print("=" * 80)

    await service.close()

if __name__ == "__main__":
    asyncio.run(test_force_refresh_with_logs())