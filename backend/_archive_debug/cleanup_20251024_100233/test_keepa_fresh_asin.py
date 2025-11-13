"""
Test Keepa update=1 with a FRESH, popular ASIN (2024 bestseller).
This will confirm if update=1 works correctly when Amazon has current data.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.keepa_service import KeepaService
from datetime import datetime

async def test_fresh_asin():
    """Test with popular 2024 bestseller"""

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

    # Test ASINs (popular 2024 books that MUST have fresh data)
    test_asins = [
        ("B0C3HXC65T", "Fourth Wing (2024 bestseller)"),
        ("B0C9WHNXJN", "Holly (Stephen King 2024)"),
        ("B0BYL5QWTT", "The Woman in Me (Britney Spears 2024)")
    ]

    try:
        keepa_epoch = 971222400

        def keepa_to_date(keepa_time):
            if keepa_time == -1:
                return "N/A", 99999
            unix_ts = keepa_epoch + (keepa_time * 60)
            dt = datetime.fromtimestamp(unix_ts)
            age_days = (datetime.now() - dt).days
            return f"{dt.strftime('%Y-%m-%d %H:%M')}", age_days

        for asin, title in test_asins:
            print("\n" + "=" * 70)
            print(f"ASIN: {asin}")
            print(f"Title: {title}")
            print("=" * 70)

            product_data = await service.get_product_data(
                identifier=asin,
                domain=1,
                force_refresh=True
            )

            if not product_data:
                print("  [SKIP] No data returned")
                continue

            last_price_change_keepa = product_data.get("lastPriceChange", -1)
            last_price_change_str, age_days = keepa_to_date(last_price_change_keepa)

            # Extract BuyBox price + timestamp
            csv_data = product_data.get("csv", [])
            buybox_price = "N/A"
            buybox_timestamp = "N/A"
            buybox_age = 99999

            if len(csv_data) > 12:
                buybox_array = csv_data[12]
                if buybox_array and len(buybox_array) >= 2:
                    price = buybox_array[-1]
                    timestamp = buybox_array[-2]

                    if price != -1:
                        buybox_price = f"${price / 100.0:.2f}"
                        buybox_timestamp, buybox_age = keepa_to_date(timestamp)

            print(f"  lastPriceChange: {last_price_change_str} ({age_days} days old)")
            print(f"  BuyBox Price: {buybox_price} (timestamp: {buybox_timestamp}, {buybox_age} days old)")

            # Validation
            if age_days < 30:
                print(f"  [PASS] Recent data (< 30 days)")
            else:
                print(f"  [FAIL] Old data ({age_days} days)")

            if buybox_age < 7:
                print(f"  [EXCELLENT] BuyBox very fresh (< 7 days)")
            elif buybox_age < 30:
                print(f"  [GOOD] BuyBox recent (< 30 days)")
            else:
                print(f"  [WARNING] BuyBox old ({buybox_age} days)")

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_fresh_asin())
