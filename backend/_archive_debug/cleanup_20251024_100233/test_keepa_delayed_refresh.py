"""
Test Keepa update parameter with delayed verification.
Theory: update=0 triggers async scraping, but data needs time to refresh.
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.services.keepa_service import KeepaService
from datetime import datetime

async def test_delayed_refresh():
    """Test with delay to allow Keepa to complete scraping"""

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

    service = KeepaService(api_key=api_key)

    keepa_epoch = 971222400
    test_asin = "0593655036"

    try:
        print("=" * 70)
        print("KEEPA DELAYED REFRESH TEST")
        print("=" * 70)
        print(f"ASIN: {test_asin}")
        print(f"Strategy: Call with update=0 (trigger scraping), wait, call again")
        print("=" * 70)

        # CALL 1: Trigger scraping with update=0
        print("\n[CALL 1] Requesting live data (update=0)...")
        print("This should trigger Keepa to scrape Amazon...")

        # Modify service call to use update=0 via extra_params
        # (We need to bypass the keepa_service.py wrapper)
        import keepa
        api = keepa.Keepa(api_key)

        # First call with update=0 (force live data)
        products = api.query(
            test_asin,
            domain='US',
            stats=180,
            history=True,
            offers=20,
            update=0,  # FORCE LIVE DATA
            wait=True
        )

        if not products or len(products) == 0:
            print("ERROR: No product returned")
            return

        product1 = products[0]
        last_price_change1 = product1.get("lastPriceChange", -1)

        def keepa_to_str(keepa_time):
            if keepa_time == -1:
                return "N/A", 99999
            unix_ts = keepa_epoch + (keepa_time * 60)
            dt = datetime.fromtimestamp(unix_ts)
            age_days = (datetime.now() - dt).days
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}", age_days

        lpc1_str, lpc1_age = keepa_to_str(last_price_change1)
        print(f"  lastPriceChange: {lpc1_str} ({lpc1_age} days old)")

        # Extract BuyBox price
        csv1 = product1.get("csv", [])
        buybox1 = "N/A"
        if len(csv1) > 12 and csv1[12] and len(csv1[12]) >= 2:
            price = csv1[12][-1]
            if price != -1:
                buybox1 = f"${price / 100.0:.2f}"

        print(f"  BuyBox Price: {buybox1}")

        # WAIT for Keepa to complete scraping
        wait_seconds = 30
        print(f"\n[WAITING] {wait_seconds} seconds for Keepa to complete scraping...")
        for i in range(wait_seconds, 0, -5):
            print(f"  {i} seconds remaining...", end="\r")
            await asyncio.sleep(5)

        print("\n\n[CALL 2] Requesting data again (should be fresh now)...")

        # Second call (cache should be updated now)
        products2 = api.query(
            test_asin,
            domain='US',
            stats=180,
            history=True,
            offers=20,
            update=None,  # Use cache (should be fresh now)
            wait=True
        )

        if not products2 or len(products2) == 0:
            print("ERROR: No product returned")
            return

        product2 = products2[0]
        last_price_change2 = product2.get("lastPriceChange", -1)
        lpc2_str, lpc2_age = keepa_to_str(last_price_change2)

        print(f"  lastPriceChange: {lpc2_str} ({lpc2_age} days old)")

        # Extract BuyBox price
        csv2 = product2.get("csv", [])
        buybox2 = "N/A"
        if len(csv2) > 12 and csv2[12] and len(csv2[12]) >= 2:
            price = csv2[12][-1]
            if price != -1:
                buybox2 = f"${price / 100.0:.2f}"

        print(f"  BuyBox Price: {buybox2}")

        # COMPARISON
        print("\n" + "=" * 70)
        print("COMPARISON:")
        print("=" * 70)
        print(f"  CALL 1 (immediate):  lastPriceChange={lpc1_age} days, BuyBox={buybox1}")
        print(f"  CALL 2 (after wait): lastPriceChange={lpc2_age} days, BuyBox={buybox2}")

        if lpc2_age < lpc1_age:
            print("\n  [SUCCESS] Data was refreshed after waiting!")
        elif lpc1_age == lpc2_age:
            print("\n  [NO CHANGE] Data still the same (Keepa may need more time or update=0 not working)")
        else:
            print("\n  [ERROR] Data got older somehow?")

        print("=" * 70)

    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_delayed_refresh())
