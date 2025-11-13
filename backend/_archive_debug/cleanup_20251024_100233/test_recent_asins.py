"""
Test recent ASINs with update=0 to validate live data refresh.
Tests 3 ASINs provided by user: 055327757X, 1640951083, 1736495232
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.services.keepa_service import KeepaService

async def test_recent_asins():
    """Test recent ASINs with both update=None and update=0"""

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

    # Test ASINs from user
    test_asins = [
        "055327757X",
        "1640951083",
        "1736495232"
    ]

    keepa_epoch = 971222400

    def keepa_to_date(keepa_time):
        """Convert Keepa time to readable date"""
        if keepa_time == -1 or keepa_time is None:
            return None, None, 99999
        unix_ts = keepa_epoch + (keepa_time * 60)
        dt = datetime.fromtimestamp(unix_ts)
        age_days = (datetime.now() - dt).days
        return dt, dt.strftime('%Y-%m-%d %H:%M:%S'), age_days

    def extract_prices(product):
        """Extract all available prices from CSV arrays"""
        csv_data = product.get("csv", [])
        prices = {}

        # Index mapping (from Keepa docs)
        price_types = {
            0: "AMAZON",
            1: "NEW",
            2: "USED",
            3: "SALES_RANK",
            7: "NEW_FBA",
            12: "BUY_BOX"
        }

        for idx, name in price_types.items():
            if idx < len(csv_data) and csv_data[idx]:
                price_array = csv_data[idx]
                if price_array and len(price_array) >= 2:
                    last_price = price_array[-1]
                    last_timestamp = price_array[-2]

                    if last_price != -1:
                        dt, dt_str, age_days = keepa_to_date(last_timestamp)

                        if name == "SALES_RANK":
                            prices[name] = {
                                "value": last_price,
                                "timestamp": dt_str,
                                "age_days": age_days
                            }
                        else:
                            prices[name] = {
                                "value": f"${last_price / 100.0:.2f}",
                                "timestamp": dt_str,
                                "age_days": age_days
                            }

        return prices

    try:
        for asin in test_asins:
            print("\n" + "=" * 80)
            print(f"TESTING ASIN: {asin}")
            print("=" * 80)

            # TEST 1: Normal call (update=None, uses cache)
            print("\n[TEST 1] Normal call (force_refresh=False, update=None)")
            print("-" * 80)

            try:
                data1 = await service.get_product_data(
                    identifier=asin,
                    domain=1,
                    force_refresh=False
                )

                if data1:
                    title = data1.get("title", "N/A")
                    print(f"  Title: {title[:80]}...")

                    # Extract metadata
                    last_update = data1.get("lastUpdate", -1)
                    last_price_change = data1.get("lastPriceChange", -1)

                    _, lu_str, lu_age = keepa_to_date(last_update)
                    _, lpc_str, lpc_age = keepa_to_date(last_price_change)

                    print(f"\n  Metadata:")
                    print(f"    lastUpdate:       {lu_str} ({lu_age} days old)")
                    print(f"    lastPriceChange:  {lpc_str} ({lpc_age} days old)")

                    # Extract prices
                    prices1 = extract_prices(data1)
                    print(f"\n  Prices extracted:")
                    for price_type, info in prices1.items():
                        print(f"    {price_type:15} {info['value']:12} (timestamp: {info['timestamp']}, {info['age_days']} days old)")

                    if not prices1:
                        print("    [WARNING] No prices found in CSV arrays")

                else:
                    print("  [ERROR] No data returned")

            except Exception as e:
                print(f"  [ERROR] {e}")

            # WAIT 5 seconds
            print("\n[WAITING] 5 seconds before force refresh...")
            await asyncio.sleep(5)

            # TEST 2: Force refresh (update=0, live data)
            print("\n[TEST 2] Force refresh (force_refresh=True, update=0)")
            print("-" * 80)

            try:
                data2 = await service.get_product_data(
                    identifier=asin,
                    domain=1,
                    force_refresh=True  # This should trigger update=0
                )

                if data2:
                    title = data2.get("title", "N/A")
                    print(f"  Title: {title[:80]}...")

                    # Extract metadata
                    last_update = data2.get("lastUpdate", -1)
                    last_price_change = data2.get("lastPriceChange", -1)

                    _, lu_str, lu_age = keepa_to_date(last_update)
                    _, lpc_str, lpc_age = keepa_to_date(last_price_change)

                    print(f"\n  Metadata:")
                    print(f"    lastUpdate:       {lu_str} ({lu_age} days old)")
                    print(f"    lastPriceChange:  {lpc_str} ({lpc_age} days old)")

                    # Extract prices
                    prices2 = extract_prices(data2)
                    print(f"\n  Prices extracted:")
                    for price_type, info in prices2.items():
                        print(f"    {price_type:15} {info['value']:12} (timestamp: {info['timestamp']}, {info['age_days']} days old)")

                    if not prices2:
                        print("    [WARNING] No prices found in CSV arrays")

                    # COMPARISON
                    print("\n  [COMPARISON] Test 1 vs Test 2:")
                    if prices1 and prices2:
                        for price_type in prices1.keys():
                            if price_type in prices2:
                                val1 = prices1[price_type]['value']
                                val2 = prices2[price_type]['value']
                                age1 = prices1[price_type]['age_days']
                                age2 = prices2[price_type]['age_days']

                                if val1 != val2:
                                    print(f"    {price_type}: CHANGED {val1} -> {val2}")
                                elif age1 != age2:
                                    print(f"    {price_type}: Same value, timestamp changed ({age1}d -> {age2}d)")
                                else:
                                    print(f"    {price_type}: No change ({val2}, {age2}d old)")

                    # Check if data got fresher
                    if lpc_age < lu_age:
                        if lpc_age < 7:
                            print(f"\n  ✅ [SUCCESS] Data is VERY FRESH (< 7 days)")
                        elif lpc_age < 30:
                            print(f"\n  ✅ [SUCCESS] Data is RECENT (< 30 days)")
                        else:
                            print(f"\n  ⚠️ [WARNING] Data is OLD ({lpc_age} days)")
                    else:
                        if lu_age < 7:
                            print(f"\n  ✅ [ACCEPTABLE] Using lastUpdate, data < 7 days")
                        else:
                            print(f"\n  ❌ [FAIL] Data is OLD ({lu_age} days)")

                else:
                    print("  [ERROR] No data returned")

            except Exception as e:
                print(f"  [ERROR] {e}")

        print("\n" + "=" * 80)
        print("FINAL ANALYSIS")
        print("=" * 80)
        print("Check above results to determine:")
        print("1. Are timestamps recent (< 30 days)?")
        print("2. Do prices look realistic for 2024/2025?")
        print("3. Did force_refresh (update=0) improve data freshness?")
        print("=" * 80)

    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_recent_asins())
