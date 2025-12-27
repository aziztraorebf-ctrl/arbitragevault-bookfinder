"""
Test Script: Product Finder FINAL - Root Category + Arbitrage Filters

CONCLUSION du test precedent:
- rootCategory doit etre une CATEGORIE RACINE (283155 = Books)
- Les sous-categories (10777 = Law) ne fonctionnent PAS avec /query

Ce test valide l'hypothese finale avec les filtres d'arbitrage.

USAGE:
    cd backend
    python scripts/test_product_finder_final.py
"""

import asyncio
import os
import sys
import json
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


async def query_product_finder(selection: dict, domain: int = 1) -> dict:
    """Execute Product Finder query."""
    query_params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "selection": json.dumps(selection)
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/query", params=query_params)

        if response.status_code != 200:
            return {"success": False, "error": response.text[:200], "asins": [], "total": 0}

        data = response.json()
        return {
            "success": True,
            "asins": data.get("asinList", []),
            "total": data.get("totalResults", 0),
            "tokens": data.get("tokensConsumed", 0)
        }


async def get_product_details(asins: list, limit: int = 5) -> list:
    """Get details for ASINs."""
    if not asins:
        return []

    test_asins = asins[:limit]
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": ",".join(test_asins),
        "stats": 1,
        "history": 0
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/product", params=params)
        if response.status_code != 200:
            return []

        data = response.json()
        products = data.get("products", [])

        results = []
        for p in products:
            current = p.get("stats", {}).get("current", [])
            # Extract key metrics
            amazon_price = current[0] if len(current) > 0 else None
            new_price = current[1] if len(current) > 1 else None
            bsr = current[3] if len(current) > 3 else None
            fba_count = current[11] if len(current) > 11 else None

            results.append({
                "asin": p.get("asin"),
                "title": p.get("title", "?")[:60],
                "amazon_price": amazon_price,
                "new_price": new_price,
                "bsr": bsr,
                "fba_sellers": fba_count
            })
        return results


async def run_arbitrage_tests():
    """Test with arbitrage-focused filters on ROOT category."""

    print("\n" + "#"*70)
    print("# PRODUCT FINDER - ARBITRAGE FILTERS TEST")
    print("# Using ROOT category 283155 (Books) instead of subcategories")
    print("#"*70)

    tests = [
        # Test 1: Books + BSR 30K-250K + Price $40-180 + FBA<=3 + No Amazon
        {
            "name": "1. Full arbitrage filters (strict)",
            "selection": {
                "rootCategory": 283155,  # Books (ROOT)
                "perPage": 50,
                "current_SALES_gte": 30000,
                "current_SALES_lte": 250000,
                "current_NEW_gte": 4000,  # $40
                "current_NEW_lte": 18000,  # $180
                "offerCountFBA_lte": 3,
                "current_AMAZON_lte": -1  # Exclude Amazon
            }
        },
        # Test 2: Relax price range
        {
            "name": "2. Relaxed price ($20-300)",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "current_SALES_gte": 30000,
                "current_SALES_lte": 250000,
                "current_NEW_gte": 2000,  # $20
                "current_NEW_lte": 30000,  # $300
                "offerCountFBA_lte": 3,
                "current_AMAZON_lte": -1
            }
        },
        # Test 3: Relax BSR
        {
            "name": "3. Relaxed BSR (10K-500K)",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "current_SALES_gte": 10000,
                "current_SALES_lte": 500000,
                "current_NEW_gte": 2000,
                "current_NEW_lte": 30000,
                "offerCountFBA_lte": 3,
                "current_AMAZON_lte": -1
            }
        },
        # Test 4: Relax FBA count
        {
            "name": "4. Relaxed FBA (<=5)",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "current_SALES_gte": 10000,
                "current_SALES_lte": 500000,
                "current_NEW_gte": 2000,
                "current_NEW_lte": 30000,
                "offerCountFBA_lte": 5,
                "current_AMAZON_lte": -1
            }
        },
        # Test 5: Remove Amazon exclusion
        {
            "name": "5. Allow Amazon seller",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "current_SALES_gte": 10000,
                "current_SALES_lte": 500000,
                "current_NEW_gte": 2000,
                "current_NEW_lte": 30000,
                "offerCountFBA_lte": 5
                # NO current_AMAZON_lte
            }
        },
        # Test 6: Minimum viable - just BSR + price
        {
            "name": "6. Minimum viable (BSR + price only)",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "current_SALES_gte": 10000,
                "current_SALES_lte": 200000,
                "current_NEW_gte": 2000,
                "current_NEW_lte": 15000
            }
        },
        # Test 7: Only FBA filter (low competition focus)
        {
            "name": "7. Low competition focus (FBA<=3 only)",
            "selection": {
                "rootCategory": 283155,
                "perPage": 50,
                "offerCountFBA_lte": 3,
                "current_AMAZON_lte": -1
            }
        }
    ]

    results = []
    total_tokens = 0

    for test in tests:
        print(f"\n{'='*70}")
        print(f"TEST: {test['name']}")
        print(f"Selection: {json.dumps(test['selection'], indent=2)}")

        result = await query_product_finder(test['selection'])
        total_tokens += result.get('tokens', 0)

        print(f"\nResult: {result['total']} products found")
        print(f"Tokens used: {result.get('tokens', 0)} (total: {total_tokens})")

        # Get sample products for successful queries
        if result['success'] and result['asins']:
            print(f"\nSample products (first 5):")
            details = await get_product_details(result['asins'], 5)
            for d in details:
                amazon_status = "AMAZON" if d['amazon_price'] and d['amazon_price'] > 0 else "no-amz"
                price_str = f"${d['new_price']/100:.0f}" if d['new_price'] else "N/A"
                fba_str = f"FBA={d['fba_sellers']}" if d['fba_sellers'] is not None else "FBA=?"
                print(f"  - {d['asin']}: BSR={d['bsr']}, {price_str}, {fba_str}, {amazon_status}")
                print(f"    {d['title']}...")

        results.append({
            "test": test['name'],
            "selection": test['selection'],
            "total": result['total'],
            "sample_count": len(result.get('asins', []))
        })

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY - ARBITRAGE FILTERS ON ROOT CATEGORY")
    print("="*70)
    print(f"\n{'Test':<50} | {'Found':>10}")
    print("-"*70)
    for r in results:
        print(f"{r['test']:<50} | {r['total']:>10}")

    print(f"\n{'='*70}")
    print(f"Total tokens consumed: {total_tokens}")
    print("="*70)

    # Analysis
    print("\n>>> ANALYSIS <<<")
    successful = [r for r in results if r['total'] > 0]
    if successful:
        print(f"FOUND {len(successful)}/{len(results)} working filter combinations!")
        print("\nRecommended approach:")
        # Find most restrictive that works
        for s in successful:
            if s['total'] > 0 and s['total'] < 100000:
                print(f"  -> {s['test']}: {s['total']} products")
    else:
        print("NO PRODUCTS FOUND - need to investigate further")

    return results


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    results = asyncio.run(run_arbitrage_tests())

    # Save
    output_file = backend_dir / "scripts" / "product_finder_final_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
