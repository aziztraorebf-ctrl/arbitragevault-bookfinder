"""
Test Script: Keepa Product Finder - Progressive Relaxation

Ce script teste des filtres progressivement relaxes pour trouver
le "sweet spot" entre competition et disponibilite.

USAGE:
    cd backend
    python scripts/test_product_finder_relaxed.py
"""

import asyncio
import os
import sys
import json
from typing import Optional
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
    """Execute Product Finder query with selection object."""
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


async def get_product_details(asins: list, limit: int = 3) -> list:
    """Get details for first N ASINs."""
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
            results.append({
                "asin": p.get("asin"),
                "title": p.get("title", "?")[:50],
                "amazon_price": current[0] if len(current) > 0 else None,
                "new_price": current[1] if len(current) > 1 else None,
                "bsr": current[3] if len(current) > 3 else None,
                "fba_sellers": current[11] if len(current) > 11 else None
            })
        return results


async def run_progressive_tests():
    """Test avec filtres progressivement relaxes."""

    print("\n" + "#"*70)
    print("# PROGRESSIVE RELAXATION TESTS")
    print("# Finding the sweet spot between competition and availability")
    print("#"*70)

    tests = [
        # Test A: Remove Amazon exclusion only
        {
            "name": "A: Remove Amazon exclusion (keep other filters)",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50,
                "current_SALES_gte": 30000,
                "current_SALES_lte": 250000,
                "current_NEW_gte": 4000,
                "current_NEW_lte": 18000,
                "offerCountFBA_lte": 3
                # NO current_AMAZON_lte
            }
        },
        # Test B: Remove FBA limit only
        {
            "name": "B: Remove FBA limit (keep Amazon exclusion)",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50,
                "current_SALES_gte": 30000,
                "current_SALES_lte": 250000,
                "current_NEW_gte": 4000,
                "current_NEW_lte": 18000,
                "current_AMAZON_lte": -1
                # NO offerCountFBA_lte
            }
        },
        # Test C: Expand BSR range significantly
        {
            "name": "C: Expand BSR (1K-500K), keep FBA<=5",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50,
                "current_SALES_gte": 1000,
                "current_SALES_lte": 500000,
                "current_NEW_gte": 4000,
                "current_NEW_lte": 18000,
                "offerCountFBA_lte": 5,
                "current_AMAZON_lte": -1
            }
        },
        # Test D: Expand price range
        {
            "name": "D: Expand price ($20-300), BSR 1K-500K, FBA<=5",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50,
                "current_SALES_gte": 1000,
                "current_SALES_lte": 500000,
                "current_NEW_gte": 2000,  # $20
                "current_NEW_lte": 30000,  # $300
                "offerCountFBA_lte": 5,
                "current_AMAZON_lte": -1
            }
        },
        # Test E: Very relaxed - only FBA filter + no Amazon
        {
            "name": "E: Very relaxed - only FBA<=10, no Amazon, any BSR/price",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50,
                "offerCountFBA_lte": 10,
                "current_AMAZON_lte": -1
            }
        },
        # Test F: Only category (baseline)
        {
            "name": "F: BASELINE - only category, no other filters",
            "selection": {
                "rootCategory": 10777,
                "perPage": 50
            }
        },
        # Test G: Smart Velocity template (different category)
        {
            "name": "G: Python Books (cat 3508), BSR 10K-80K, FBA<=5",
            "selection": {
                "rootCategory": 3508,  # Python/Programming
                "perPage": 50,
                "current_SALES_gte": 10000,
                "current_SALES_lte": 80000,
                "current_NEW_gte": 2000,  # $20
                "current_NEW_lte": 5000,  # $50
                "offerCountFBA_lte": 5,
                "current_AMAZON_lte": -1
            }
        },
        # Test H: Books general with low competition
        {
            "name": "H: General Books (283155), FBA<=3, no Amazon",
            "selection": {
                "rootCategory": 283155,  # Books
                "perPage": 50,
                "current_SALES_gte": 50000,
                "current_SALES_lte": 200000,
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

        if result['success'] and result['asins']:
            print(f"\nFirst 3 products:")
            details = await get_product_details(result['asins'], 3)
            for d in details:
                amazon_status = "AMAZON" if d['amazon_price'] and d['amazon_price'] > 0 else "no-amz"
                price_str = f"${d['new_price']/100:.0f}" if d['new_price'] else "N/A"
                print(f"  - {d['asin']}: BSR={d['bsr']}, Price={price_str}, FBA={d['fba_sellers']}, {amazon_status}")
                print(f"    {d['title']}...")

        results.append({
            "test": test['name'],
            "selection": test['selection'],
            "total": result['total'],
            "sample_count": len(result.get('asins', []))
        })

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n{'Test':<55} | {'Found':>8}")
    print("-"*70)
    for r in results:
        print(f"{r['test']:<55} | {r['total']:>8}")

    print(f"\n{'='*70}")
    print(f"Total tokens consumed: {total_tokens}")
    print("="*70)

    # Find sweet spot
    successful = [r for r in results if r['total'] > 0]
    if successful:
        print("\n>>> SWEET SPOT IDENTIFIED <<<")
        for s in successful:
            if "FBA" in s['test'] or "Amazon" in s['test'].lower():
                print(f"  - {s['test']}: {s['total']} products")
    else:
        print("\n>>> NO PRODUCTS FOUND with any filter combination <<<")
        print("The market may be too competitive or filters need different approach")

    return results


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    results = asyncio.run(run_progressive_tests())

    # Save
    output_file = backend_dir / "scripts" / "product_finder_relaxed_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
