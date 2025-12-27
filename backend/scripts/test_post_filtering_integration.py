"""
Test Script: Post-Filtering Integration Test

Validates the Phase 6.2 Product Finder post-filtering strategy:
1. Product Finder /query with BSR/price pre-filters
2. Post-filter via /product for Amazon exclusion + FBA count
3. Compare with previous bestsellers approach

USAGE:
    cd backend
    python scripts/test_post_filtering_integration.py
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import List, Dict

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


async def test_product_finder_with_post_filter(
    category: int,
    bsr_min: int,
    bsr_max: int,
    price_min: float,
    price_max: float,
    max_fba_sellers: int,
    exclude_amazon: bool = True
) -> Dict:
    """
    Test the post-filtering strategy:
    1. Query Product Finder with BSR/price filters
    2. Post-filter results for Amazon/FBA
    """
    result = {
        "strategy": "product_finder_post_filter",
        "category": category,
        "filters": {
            "bsr_min": bsr_min,
            "bsr_max": bsr_max,
            "price_min": price_min,
            "price_max": price_max,
            "max_fba_sellers": max_fba_sellers,
            "exclude_amazon": exclude_amazon
        },
        "pre_filter_count": 0,
        "post_filter_count": 0,
        "tokens_used": 0,
        "sample_products": []
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Product Finder query
        selection = {
            "rootCategory": 283155,  # Books (ROOT)
            "perPage": 50,
            "current_SALES_gte": bsr_min,
            "current_SALES_lte": bsr_max,
            "current_NEW_gte": int(price_min * 100),
            "current_NEW_lte": int(price_max * 100)
        }

        params = {
            "key": KEEPA_API_KEY,
            "domain": 1,
            "selection": json.dumps(selection)
        }

        print(f"\n{'='*60}")
        print(f"Step 1: Product Finder Query")
        print(f"  Selection: BSR {bsr_min}-{bsr_max}, Price ${price_min}-${price_max}")

        response = await client.get(f"{KEEPA_BASE_URL}/query", params=params)

        if response.status_code != 200:
            print(f"  ERROR: {response.text[:200]}")
            return result

        data = response.json()
        asins = data.get("asinList", [])
        total = data.get("totalResults", 0)
        tokens = data.get("tokensConsumed", 0)

        result["pre_filter_count"] = len(asins)
        result["tokens_used"] += tokens

        print(f"  Found: {total} total, {len(asins)} returned")
        print(f"  Tokens: {tokens}")

        if not asins:
            print("  No ASINs found - skipping post-filter")
            return result

        # Step 2: Get product details for post-filtering
        print(f"\nStep 2: Post-Filtering via /product")
        print(f"  Fetching details for {len(asins)} ASINs...")

        product_params = {
            "key": KEEPA_API_KEY,
            "domain": 1,
            "asin": ",".join(asins[:50]),  # Limit to 50
            "stats": 1,
            "history": 0
        }

        response = await client.get(f"{KEEPA_BASE_URL}/product", params=product_params)

        if response.status_code != 200:
            print(f"  ERROR: {response.text[:200]}")
            return result

        data = response.json()
        products = data.get("products", [])
        tokens = data.get("tokensConsumed", 0)
        result["tokens_used"] += tokens

        print(f"  Got details for {len(products)} products")
        print(f"  Tokens: {tokens}")

        # Step 3: Apply post-filters
        print(f"\nStep 3: Applying Post-Filters")
        print(f"  exclude_amazon={exclude_amazon}, max_fba={max_fba_sellers}")

        filtered = []
        amazon_excluded = 0
        fba_excluded = 0

        for p in products:
            asin = p.get("asin")
            current = p.get("stats", {}).get("current", [])

            # Check Amazon seller
            amazon_price = current[0] if len(current) > 0 else None
            if exclude_amazon and amazon_price is not None and amazon_price > 0:
                amazon_excluded += 1
                continue

            # Check FBA count
            fba_count = current[11] if len(current) > 11 else 0
            if fba_count is not None and fba_count > max_fba_sellers:
                fba_excluded += 1
                continue

            # Passed filters
            new_price = current[1] if len(current) > 1 else None
            bsr = current[3] if len(current) > 3 else None

            filtered.append({
                "asin": asin,
                "title": p.get("title", "?")[:60],
                "bsr": bsr,
                "price": f"${new_price/100:.2f}" if new_price else "N/A",
                "fba_sellers": fba_count,
                "amazon_sells": amazon_price is not None and amazon_price > 0
            })

        result["post_filter_count"] = len(filtered)
        result["sample_products"] = filtered[:5]

        print(f"\n  Results:")
        print(f"    - Amazon excluded: {amazon_excluded}")
        print(f"    - FBA excluded: {fba_excluded}")
        print(f"    - PASSED: {len(filtered)}/{len(products)}")

        if filtered:
            print(f"\n  Sample Products:")
            for p in filtered[:5]:
                print(f"    - {p['asin']}: BSR={p['bsr']}, {p['price']}, FBA={p['fba_sellers']}")
                print(f"      {p['title']}...")

    return result


async def main():
    """Run post-filtering integration tests."""

    print("\n" + "#"*70)
    print("# POST-FILTERING INTEGRATION TEST")
    print("# Phase 6.2: Product Finder with Amazon/FBA post-filtering")
    print("#"*70)

    tests = [
        # Test 1: Smart Velocity criteria
        {
            "name": "Smart Velocity (BSR 10K-80K, $20-50, FBA<=5)",
            "category": 3508,  # Python books
            "bsr_min": 10000,
            "bsr_max": 80000,
            "price_min": 20.0,
            "price_max": 50.0,
            "max_fba_sellers": 5
        },
        # Test 2: Textbooks criteria
        {
            "name": "Textbooks (BSR 30K-250K, $40-150, FBA<=3)",
            "category": 10777,  # Law
            "bsr_min": 30000,
            "bsr_max": 250000,
            "price_min": 40.0,
            "price_max": 150.0,
            "max_fba_sellers": 3
        },
        # Test 3: Broader criteria
        {
            "name": "Broad (BSR 10K-200K, $15-100, FBA<=5)",
            "category": 283155,  # Books root
            "bsr_min": 10000,
            "bsr_max": 200000,
            "price_min": 15.0,
            "price_max": 100.0,
            "max_fba_sellers": 5
        }
    ]

    results = []
    total_tokens = 0

    for test in tests:
        print(f"\n\n{'='*70}")
        print(f"TEST: {test['name']}")
        print(f"{'='*70}")

        result = await test_product_finder_with_post_filter(
            category=test["category"],
            bsr_min=test["bsr_min"],
            bsr_max=test["bsr_max"],
            price_min=test["price_min"],
            price_max=test["price_max"],
            max_fba_sellers=test["max_fba_sellers"]
        )

        result["test_name"] = test["name"]
        results.append(result)
        total_tokens += result["tokens_used"]

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n{'Test':<45} | {'Pre':>6} | {'Post':>6} | {'Tokens':>6}")
    print("-"*70)

    for r in results:
        print(f"{r['test_name']:<45} | {r['pre_filter_count']:>6} | {r['post_filter_count']:>6} | {r['tokens_used']:>6}")

    print(f"\n{'='*70}")
    print(f"Total tokens consumed: {total_tokens}")
    print("="*70)

    # Analysis
    print("\n>>> ANALYSIS <<<")
    successful = [r for r in results if r["post_filter_count"] > 0]
    if successful:
        print(f"SUCCESS: {len(successful)}/{len(results)} tests found products!")
        for s in successful:
            print(f"  - {s['test_name']}: {s['post_filter_count']} products passed all filters")
    else:
        print("NO PRODUCTS found with any criteria - investigate further")

    return results


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    results = asyncio.run(main())

    # Save results
    output_file = backend_dir / "scripts" / "post_filtering_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
