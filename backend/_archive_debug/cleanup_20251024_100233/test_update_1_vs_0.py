"""
Test to compare update=1 vs update=0 with the same ASINs.
This will determine which parameter value actually forces live data refresh.
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

async def test_update_values():
    """Compare update=1 vs update=0 behavior"""

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

    # Import keepa directly to bypass our service layer
    import keepa

    # Test ASINs
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

    def extract_key_data(product):
        """Extract key fields for comparison"""
        if not product:
            return None

        last_update = product.get("lastUpdate", -1)
        last_price_change = product.get("lastPriceChange", -1)

        _, lu_str, lu_age = keepa_to_date(last_update)
        _, lpc_str, lpc_age = keepa_to_date(last_price_change)

        # Extract BuyBox price
        csv_data = product.get("csv", [])
        buybox_price = "N/A"
        buybox_timestamp = "N/A"
        buybox_age = 99999

        if len(csv_data) > 12 and csv_data[12] and len(csv_data[12]) >= 2:
            price = csv_data[12][-1]
            timestamp = csv_data[12][-2]

            if price != -1:
                buybox_price = f"${price / 100.0:.2f}"
                _, buybox_timestamp, buybox_age = keepa_to_date(timestamp)

        return {
            "title": product.get("title", "N/A")[:60],
            "lastUpdate": lu_str,
            "lastUpdate_age": lu_age,
            "lastPriceChange": lpc_str,
            "lastPriceChange_age": lpc_age,
            "buybox_price": buybox_price,
            "buybox_timestamp": buybox_timestamp,
            "buybox_age": buybox_age
        }

    # Create Keepa API instance
    api = keepa.Keepa(api_key)

    print("=" * 80)
    print("KEEPA UPDATE PARAMETER COMPARISON TEST")
    print("=" * 80)
    print("Testing update=1 vs update=0 with same ASINs")
    print("Goal: Determine which value forces live data refresh")
    print("=" * 80)

    for asin in test_asins:
        print(f"\n{'=' * 80}")
        print(f"TESTING ASIN: {asin}")
        print("=" * 80)

        # TEST 1: update=1
        print("\n[TEST A] Calling Keepa with update=1")
        print("-" * 80)

        try:
            products_1 = api.query(
                asin,
                domain='US',
                stats=180,
                history=True,
                offers=20,
                update=1  # Update if data > 1 hour old
            )

            if products_1 and len(products_1) > 0:
                data_1 = extract_key_data(products_1[0])

                print(f"  Title: {data_1['title']}")
                print(f"  lastUpdate:       {data_1['lastUpdate']} ({data_1['lastUpdate_age']} days old)")
                print(f"  lastPriceChange:  {data_1['lastPriceChange']} ({data_1['lastPriceChange_age']} days old)")
                print(f"  BuyBox Price:     {data_1['buybox_price']} (timestamp: {data_1['buybox_timestamp']}, {data_1['buybox_age']} days old)")
            else:
                print("  [ERROR] No data returned")
                data_1 = None

        except Exception as e:
            print(f"  [ERROR] {str(e)[:100]}")
            data_1 = None

        # WAIT 5 seconds
        print("\n[WAITING] 5 seconds before update=0 test...")
        await asyncio.sleep(5)

        # TEST 2: update=0
        print("\n[TEST B] Calling Keepa with update=0")
        print("-" * 80)

        try:
            products_0 = api.query(
                asin,
                domain='US',
                stats=180,
                history=True,
                offers=20,
                update=0  # Force live data (according to docs)
            )

            if products_0 and len(products_0) > 0:
                data_0 = extract_key_data(products_0[0])

                print(f"  Title: {data_0['title']}")
                print(f"  lastUpdate:       {data_0['lastUpdate']} ({data_0['lastUpdate_age']} days old)")
                print(f"  lastPriceChange:  {data_0['lastPriceChange']} ({data_0['lastPriceChange_age']} days old)")
                print(f"  BuyBox Price:     {data_0['buybox_price']} (timestamp: {data_0['buybox_timestamp']}, {data_0['buybox_age']} days old)")
            else:
                print("  [ERROR] No data returned")
                data_0 = None

        except Exception as e:
            print(f"  [ERROR] {str(e)[:100]}")
            data_0 = None

        # COMPARISON
        print("\n" + "-" * 80)
        print("[COMPARISON] update=1 vs update=0")
        print("-" * 80)

        if data_1 and data_0:
            # Compare lastPriceChange ages
            if data_0['lastPriceChange_age'] < data_1['lastPriceChange_age']:
                print(f"  lastPriceChange: update=0 is FRESHER ({data_0['lastPriceChange_age']}d vs {data_1['lastPriceChange_age']}d)")
            elif data_0['lastPriceChange_age'] > data_1['lastPriceChange_age']:
                print(f"  lastPriceChange: update=1 is FRESHER ({data_1['lastPriceChange_age']}d vs {data_0['lastPriceChange_age']}d)")
            else:
                print(f"  lastPriceChange: IDENTICAL ({data_1['lastPriceChange_age']} days old)")

            # Compare BuyBox prices
            if data_1['buybox_price'] != data_0['buybox_price']:
                print(f"  BuyBox Price: DIFFERENT (update=1: {data_1['buybox_price']}, update=0: {data_0['buybox_price']})")
            else:
                print(f"  BuyBox Price: IDENTICAL ({data_1['buybox_price']})")

            # Compare BuyBox timestamps
            if data_0['buybox_age'] < data_1['buybox_age']:
                print(f"  BuyBox Timestamp: update=0 is FRESHER ({data_0['buybox_age']}d vs {data_1['buybox_age']}d)")
            elif data_0['buybox_age'] > data_1['buybox_age']:
                print(f"  BuyBox Timestamp: update=1 is FRESHER ({data_1['buybox_age']}d vs {data_0['buybox_age']}d)")
            else:
                print(f"  BuyBox Timestamp: IDENTICAL ({data_1['buybox_age']} days old)")

            # Overall verdict
            if data_0['lastPriceChange_age'] < 30 or data_0['buybox_age'] < 30:
                print(f"\n  [SUCCESS] update=0 returned FRESH data (< 30 days)")
            elif data_1['lastPriceChange_age'] < 30 or data_1['buybox_age'] < 30:
                print(f"\n  [SUCCESS] update=1 returned FRESH data (< 30 days)")
            else:
                print(f"\n  [FAIL] Both update=1 and update=0 returned OLD data (> 30 days)")

        elif data_1 and not data_0:
            print("  update=1 succeeded, update=0 failed")
        elif data_0 and not data_1:
            print("  update=0 succeeded, update=1 failed")
        else:
            print("  Both tests failed")

    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    print("Review the comparisons above to determine:")
    print("1. Does update=1 return fresher data than update=0?")
    print("2. Does update=0 return fresher data than update=1?")
    print("3. Are both returning the same old data?")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_update_values())
