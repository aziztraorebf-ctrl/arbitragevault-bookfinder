"""
Test Script: Validate Amazon Exclusion Filter

This test verifies that products where Amazon sells are properly excluded.

USAGE:
    cd backend
    python scripts/test_amazon_filter.py
"""

import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import httpx

# Load .env
env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key, value)

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"

# Test ASINs: products we know Amazon sells
TEST_ASINS = [
    "B0D5HVSW5T",  # Little Corner: Coloring Book - Amazon sells (current[0] = 999)
    "B0DJQVYV99",  # Should be Amazon-free based on previous analysis
    "B0CJL7J1CK",  # Another test
]


async def check_amazon_status(asins: list) -> dict:
    """Check Amazon availability for ASINs via Keepa API."""
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": ",".join(asins),
        "stats": 1,
        "history": 0
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/product", params=params)
        if response.status_code != 200:
            return {"error": response.text}

        data = response.json()
        results = {}

        for product in data.get("products", []):
            asin = product.get("asin")
            stats = product.get("stats", {})
            current = stats.get("current", [])

            # current[0] = Amazon price (in cents)
            amazon_price = current[0] if len(current) > 0 else None
            # current[11] = FBA seller count
            fba_count = current[11] if len(current) > 11 else None
            # availabilityAmazon: -1 = no, >= 0 = yes
            availability_amazon = product.get("availabilityAmazon")
            # buyBoxIsAmazon
            buybox_amazon = stats.get("buyBoxIsAmazon")

            results[asin] = {
                "amazon_price_cents": amazon_price,
                "amazon_price_dollars": f"${amazon_price/100:.2f}" if amazon_price and amazon_price > 0 else "N/A",
                "fba_seller_count": fba_count,
                "availabilityAmazon": availability_amazon,
                "buyBoxIsAmazon": buybox_amazon,
                "should_exclude": (
                    (amazon_price is not None and amazon_price > 0) or
                    (availability_amazon is not None and availability_amazon >= 0)
                )
            }

        return results


async def test_filter_logic():
    """Test the filter logic that should exclude Amazon."""
    print("\n" + "="*70)
    print("TEST: Amazon Exclusion Filter Validation")
    print("="*70)

    results = await check_amazon_status(TEST_ASINS)

    print("\n>>> ANALYSIS OF EACH ASIN <<<\n")

    excluded_count = 0
    passed_count = 0

    for asin, data in results.items():
        if "error" in data:
            print(f"{asin}: ERROR - {data['error']}")
            continue

        print(f"ASIN: {asin}")
        print(f"  - Amazon Price: {data['amazon_price_dollars']}")
        print(f"  - FBA Sellers: {data['fba_seller_count']}")
        print(f"  - availabilityAmazon: {data['availabilityAmazon']}")
        print(f"  - buyBoxIsAmazon: {data['buyBoxIsAmazon']}")

        # Our current filter logic: exclude if current[0] > 0
        current_filter_excludes = data['amazon_price_cents'] and data['amazon_price_cents'] > 0

        # What the filter SHOULD do based on business logic
        should_exclude = data['should_exclude']

        if current_filter_excludes:
            print(f"  => CURRENT FILTER: Would EXCLUDE (amazon_price > 0)")
            excluded_count += 1
        else:
            print(f"  => CURRENT FILTER: Would PASS (amazon_price <= 0 or null)")
            passed_count += 1

        if should_exclude:
            print(f"  => CORRECT BEHAVIOR: Should be EXCLUDED")
        else:
            print(f"  => CORRECT BEHAVIOR: Should PASS")

        if current_filter_excludes != should_exclude:
            print(f"  *** MISMATCH! Filter behavior differs from expected ***")

        print()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total ASINs tested: {len(results)}")
    print(f"Would be EXCLUDED by current filter: {excluded_count}")
    print(f"Would PASS current filter: {passed_count}")

    # The key insight
    print("\n>>> KEY INSIGHT <<<")
    print("If products with Amazon selling are appearing as EXCELLENT,")
    print("the post-filtering might not be executing properly.")
    print("\nPossible causes:")
    print("1. Post-filter function returning early due to error")
    print("2. Products cached BEFORE filter was fixed")
    print("3. Filter logic has edge case bug")


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    asyncio.run(test_filter_logic())
