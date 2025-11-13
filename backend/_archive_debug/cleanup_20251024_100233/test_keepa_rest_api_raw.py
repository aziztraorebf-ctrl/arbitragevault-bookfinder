"""
Direct REST API test - bypassing Python keepa library completely.
This will reveal if the problem is in the library or the API itself.
"""
import os
import httpx
import json
from datetime import datetime
import asyncio

async def test_rest_api_direct():
    """Test Keepa REST API with raw HTTP requests"""

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

    base_url = "https://api.keepa.com/product"
    keepa_epoch = 971222400

    def keepa_to_date(keepa_time):
        if keepa_time == -1 or keepa_time is None:
            return "N/A", 99999
        unix_ts = keepa_epoch + (keepa_time * 60)
        dt = datetime.fromtimestamp(unix_ts)
        age_days = (datetime.now() - dt).days
        return dt.strftime('%Y-%m-%d %H:%M:%S'), age_days

    # Test with one ASIN
    test_asin = "055327757X"

    print("=" * 80)
    print("KEEPA REST API DIRECT TEST (NO PYTHON LIBRARY)")
    print("=" * 80)
    print(f"ASIN: {test_asin}")
    print(f"Base URL: {base_url}")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:

        # TEST 1: update=0 (should force live data)
        print("\n[TEST 1] Direct HTTP GET with update=0")
        print("-" * 80)

        params_0 = {
            "key": api_key,
            "domain": 1,
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20,
            "update": 0
        }

        # Build full URL for logging
        url_0 = f"{base_url}?"
        url_params = "&".join([f"{k}={v}" for k, v in params_0.items() if k != "key"])
        url_0_display = f"{base_url}?key=***&{url_params}"

        print(f"  URL: {url_0_display}")
        print(f"  Params: {json.dumps({k: v for k, v in params_0.items() if k != 'key'}, indent=2)}")

        try:
            response_0 = await client.get(base_url, params=params_0)
            print(f"\n  HTTP Status: {response_0.status_code}")

            if response_0.status_code == 200:
                data_0 = response_0.json()

                # Log raw response structure
                print(f"  Response keys: {list(data_0.keys())}")

                if "products" in data_0:
                    products = data_0["products"]
                    print(f"  Products count: {len(products)}")

                    if products:
                        product = products[0]

                        # Extract metadata
                        title = product.get("title", "N/A")
                        last_update = product.get("lastUpdate", -1)
                        last_price_change = product.get("lastPriceChange", -1)

                        lu_str, lu_age = keepa_to_date(last_update)
                        lpc_str, lpc_age = keepa_to_date(last_price_change)

                        print(f"\n  Product Data:")
                        print(f"    Title: {title[:60]}")
                        print(f"    lastUpdate:       {lu_str} ({lu_age} days old)")
                        print(f"    lastPriceChange:  {lpc_str} ({lpc_age} days old)")

                        # Extract BuyBox from CSV
                        csv_data = product.get("csv", [])
                        if len(csv_data) > 12 and csv_data[12]:
                            buybox_array = csv_data[12]
                            if buybox_array and len(buybox_array) >= 2:
                                price = buybox_array[-1]
                                timestamp = buybox_array[-2]

                                if price != -1:
                                    bb_str, bb_age = keepa_to_date(timestamp)
                                    print(f"    BuyBox Price:     ${price / 100.0:.2f}")
                                    print(f"    BuyBox Timestamp: {bb_str} ({bb_age} days old)")

                        # Check if data is fresh
                        if lpc_age < 7:
                            print(f"\n  ✅ [SUCCESS] lastPriceChange is FRESH (< 7 days)")
                        elif lpc_age < 30:
                            print(f"\n  ⚠️ [ACCEPTABLE] lastPriceChange is RECENT (< 30 days)")
                        else:
                            print(f"\n  ❌ [FAIL] lastPriceChange is OLD ({lpc_age} days)")

                # Check tokens
                tokens_left = data_0.get("tokensLeft", "unknown")
                refill_rate = data_0.get("refillRate", "unknown")
                print(f"\n  Tokens remaining: {tokens_left}")
                print(f"  Refill rate: {refill_rate} tokens/min")

            else:
                print(f"  Error: {response_0.text}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:150]}")

        # WAIT before second test
        print("\n[WAITING] 10 seconds before update=1 test...")
        await asyncio.sleep(10)

        # TEST 2: update=1 (update if > 1 hour old)
        print("\n[TEST 2] Direct HTTP GET with update=1")
        print("-" * 80)

        params_1 = {
            "key": api_key,
            "domain": 1,
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20,
            "update": 1
        }

        url_params = "&".join([f"{k}={v}" for k, v in params_1.items() if k != "key"])
        url_1_display = f"{base_url}?key=***&{url_params}"

        print(f"  URL: {url_1_display}")

        try:
            response_1 = await client.get(base_url, params=params_1)
            print(f"\n  HTTP Status: {response_1.status_code}")

            if response_1.status_code == 200:
                data_1 = response_1.json()

                if "products" in data_1:
                    products = data_1["products"]

                    if products:
                        product = products[0]

                        last_update = product.get("lastUpdate", -1)
                        last_price_change = product.get("lastPriceChange", -1)

                        lu_str, lu_age = keepa_to_date(last_update)
                        lpc_str, lpc_age = keepa_to_date(last_price_change)

                        print(f"\n  Product Data:")
                        print(f"    lastUpdate:       {lu_str} ({lu_age} days old)")
                        print(f"    lastPriceChange:  {lpc_str} ({lpc_age} days old)")

                        # Extract BuyBox
                        csv_data = product.get("csv", [])
                        if len(csv_data) > 12 and csv_data[12]:
                            buybox_array = csv_data[12]
                            if buybox_array and len(buybox_array) >= 2:
                                price = buybox_array[-1]
                                timestamp = buybox_array[-2]

                                if price != -1:
                                    bb_str, bb_age = keepa_to_date(timestamp)
                                    print(f"    BuyBox Price:     ${price / 100.0:.2f}")
                                    print(f"    BuyBox Timestamp: {bb_str} ({bb_age} days old)")

                        if lpc_age < 7:
                            print(f"\n  ✅ [SUCCESS] lastPriceChange is FRESH (< 7 days)")
                        elif lpc_age < 30:
                            print(f"\n  ⚠️ [ACCEPTABLE] lastPriceChange is RECENT (< 30 days)")
                        else:
                            print(f"\n  ❌ [FAIL] lastPriceChange is OLD ({lpc_age} days)")

                tokens_left = data_1.get("tokensLeft", "unknown")
                print(f"\n  Tokens remaining: {tokens_left}")

            else:
                print(f"  Error: {response_1.text}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:150]}")

        # TEST 3: No update parameter (pure cache)
        print("\n[TEST 3] Direct HTTP GET with NO update parameter")
        print("-" * 80)

        params_none = {
            "key": api_key,
            "domain": 1,
            "asin": test_asin,
            "stats": 180,
            "history": 1,
            "offers": 20
        }

        print(f"  URL: {base_url}?key=***&domain=1&asin={test_asin}&stats=180&history=1&offers=20")

        try:
            response_none = await client.get(base_url, params=params_none)
            print(f"\n  HTTP Status: {response_none.status_code}")

            if response_none.status_code == 200:
                data_none = response_none.json()

                if "products" in data_none:
                    products = data_none["products"]

                    if products:
                        product = products[0]

                        last_price_change = product.get("lastPriceChange", -1)
                        lpc_str, lpc_age = keepa_to_date(last_price_change)

                        print(f"\n  Product Data:")
                        print(f"    lastPriceChange:  {lpc_str} ({lpc_age} days old)")

                        csv_data = product.get("csv", [])
                        if len(csv_data) > 12 and csv_data[12]:
                            buybox_array = csv_data[12]
                            if buybox_array and len(buybox_array) >= 2:
                                price = buybox_array[-1]
                                if price != -1:
                                    print(f"    BuyBox Price:     ${price / 100.0:.2f}")

                tokens_left = data_none.get("tokensLeft", "unknown")
                print(f"\n  Tokens remaining: {tokens_left}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:150]}")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("Compare the 3 tests above:")
    print("1. Did update=0 return fresher data than update=1?")
    print("2. Did update=1 return fresher data than no update?")
    print("3. Are all 3 returning identical old data?")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_rest_api_direct())
