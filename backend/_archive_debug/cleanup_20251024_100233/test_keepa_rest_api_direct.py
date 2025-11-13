"""
Test Keepa REST API directly (bypass Python library).
This will prove if update parameter works at API level.
"""
import asyncio
import os
import httpx
from datetime import datetime

async def test_rest_api_direct():
    """Call Keepa REST API directly with update=0"""

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

    keepa_epoch = 971222400
    base_url = "https://api.keepa.com"
    test_asin = "0593655036"

    def keepa_to_str(keepa_time):
        if keepa_time == -1 or keepa_time is None:
            return "N/A", 99999
        unix_ts = keepa_epoch + (keepa_time * 60)
        dt = datetime.fromtimestamp(unix_ts)
        age_days = (datetime.now() - dt).days
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}", age_days

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 70)
        print("KEEPA REST API DIRECT TEST")
        print("=" * 70)
        print(f"ASIN: {test_asin}")
        print("Testing both update=0 and update=1 to see which works")
        print("=" * 70)

        # TEST 1: update=0 (librairie dit: live data)
        print("\n[TEST 1] Calling REST API with update=0...")
        params1 = {
            "key": api_key,
            "domain": 1,  # US
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20,
            "update": 0  # FORCE LIVE DATA (selon librairie)
        }

        response1 = await client.get(f"{base_url}/product", params=params1)
        print(f"  HTTP Status: {response1.status_code}")

        if response1.status_code == 200:
            data1 = response1.json()
            products1 = data1.get("products", [])

            if products1:
                product1 = products1[0]
                lpc1 = product1.get("lastPriceChange", -1)
                lpc1_str, lpc1_age = keepa_to_str(lpc1)
                print(f"  lastPriceChange: {lpc1_str} ({lpc1_age} days old)")

                # Extract BuyBox
                csv1 = product1.get("csv", [])
                buybox1 = "N/A"
                if len(csv1) > 12 and csv1[12] and len(csv1[12]) >= 2:
                    price = csv1[12][-1]
                    if price != -1:
                        buybox1 = f"${price / 100.0:.2f}"
                print(f"  BuyBox Price: {buybox1}")
        else:
            print(f"  ERROR: {response1.text}")

        # WAIT 5 seconds
        print("\n[WAITING] 5 seconds...")
        await asyncio.sleep(5)

        # TEST 2: update=1 (REST API docs disent peut-être: live data)
        print("\n[TEST 2] Calling REST API with update=1...")
        params2 = {
            "key": api_key,
            "domain": 1,
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20,
            "update": 1  # Alternative value
        }

        response2 = await client.get(f"{base_url}/product", params=params2)
        print(f"  HTTP Status: {response2.status_code}")

        if response2.status_code == 200:
            data2 = response2.json()
            products2 = data2.get("products", [])

            if products2:
                product2 = products2[0]
                lpc2 = product2.get("lastPriceChange", -1)
                lpc2_str, lpc2_age = keepa_to_str(lpc2)
                print(f"  lastPriceChange: {lpc2_str} ({lpc2_age} days old)")

                # Extract BuyBox
                csv2 = product2.get("csv", [])
                buybox2 = "N/A"
                if len(csv2) > 12 and csv2[12] and len(csv2[12]) >= 2:
                    price = csv2[12][-1]
                    if price != -1:
                        buybox2 = f"${price / 100.0:.2f}"
                print(f"  BuyBox Price: {buybox2}")
        else:
            print(f"  ERROR: {response2.text}")

        # TEST 3: No update parameter (cache)
        print("\n[TEST 3] Calling REST API with NO update parameter (cache)...")
        params3 = {
            "key": api_key,
            "domain": 1,
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20
            # NO update parameter
        }

        response3 = await client.get(f"{base_url}/product", params=params3)
        print(f"  HTTP Status: {response3.status_code}")

        if response3.status_code == 200:
            data3 = response3.json()
            products3 = data3.get("products", [])

            if products3:
                product3 = products3[0]
                lpc3 = product3.get("lastPriceChange", -1)
                lpc3_str, lpc3_age = keepa_to_str(lpc3)
                print(f"  lastPriceChange: {lpc3_str} ({lpc3_age} days old)")

                # Extract BuyBox
                csv3 = product3.get("csv", [])
                buybox3 = "N/A"
                if len(csv3) > 12 and csv3[12] and len(csv3[12]) >= 2:
                    price = csv3[12][-1]
                    if price != -1:
                        buybox3 = f"${price / 100.0:.2f}"
                print(f"  BuyBox Price: {buybox3}")
        else:
            print(f"  ERROR: {response3.text}")

        print("\n" + "=" * 70)
        print("CONCLUSION:")
        print("=" * 70)
        print("If all 3 tests show identical old data (2015),")
        print("then either:")
        print("  1. This ASIN genuinely has no fresh Amazon data")
        print("  2. Keepa API plan doesn't support live updates")
        print("  3. update parameter requires different approach")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_rest_api_direct())
