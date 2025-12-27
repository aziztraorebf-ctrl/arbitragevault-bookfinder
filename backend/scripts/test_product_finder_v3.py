"""
Test Script: Keepa Product Finder v3 - Using query endpoint correctly

Based on analysis:
- MCP Keepa get_bestsellers works -> API is functional
- Our /query calls return 0 results
- Need to test the correct Product Finder endpoint format

USAGE:
    cd backend
    python scripts/test_product_finder_v3.py
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


async def test_query_endpoint(selection: dict, domain: int = 1, endpoint: str = "query") -> dict:
    """Test different endpoint configurations."""

    # Method 1: selection as JSON string in query param (current approach)
    query_params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "selection": json.dumps(selection)
    }

    print(f"\n{'='*60}")
    print(f"Testing endpoint: /{endpoint}")
    print(f"Selection: {json.dumps(selection, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test GET with selection param
        response = await client.get(f"{KEEPA_BASE_URL}/{endpoint}", params=query_params)

        print(f"\nGET /{endpoint}?selection=... -> HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            asins = data.get("asinList", [])
            total = data.get("totalResults", 0)
            tokens = data.get("tokensConsumed", 0)
            print(f"  Results: {total} total, {len(asins)} returned")
            print(f"  Tokens: {tokens}")
            return {"success": True, "total": total, "asins": asins, "tokens": tokens}
        else:
            print(f"  Error: {response.text[:300]}")
            return {"success": False, "error": response.text[:200], "total": 0, "asins": []}


async def test_search_endpoint(term: str, domain: int = 1) -> dict:
    """Test the search endpoint (which we know works via MCP)."""

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "term": term
    }

    print(f"\n{'='*60}")
    print(f"Testing /search endpoint with term: '{term}'")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/search", params=params)

        print(f"GET /search?term={term} -> HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            asins = data.get("asinList", [])
            total = data.get("totalResults", len(asins))
            tokens = data.get("tokensConsumed", 0)
            print(f"  Results: {total} total, {len(asins)} returned")
            print(f"  Tokens: {tokens}")

            # Show first 3 ASINs
            if asins:
                print(f"  First 3: {asins[:3]}")

            return {"success": True, "total": total, "asins": asins, "tokens": tokens}
        else:
            print(f"  Error: {response.text[:300]}")
            return {"success": False, "error": response.text[:200], "total": 0, "asins": []}


async def test_bestsellers_endpoint(category: int, domain: int = 1) -> dict:
    """Test the bestsellers endpoint (which we know works via MCP)."""

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "category": category
    }

    print(f"\n{'='*60}")
    print(f"Testing /bestsellers endpoint for category: {category}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/bestsellers", params=params)

        print(f"GET /bestsellers?category={category} -> HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            # Bestsellers has different response structure
            bs_list = data.get("bestSellersList", {})
            asins = bs_list.get("asinList", [])
            tokens = data.get("tokensConsumed", 0)
            print(f"  Results: {len(asins)} ASINs")
            print(f"  Tokens: {tokens}")

            # Show first 3 ASINs
            if asins:
                print(f"  First 3: {asins[:3]}")

            return {"success": True, "total": len(asins), "asins": asins, "tokens": tokens}
        else:
            print(f"  Error: {response.text[:300]}")
            return {"success": False, "error": response.text[:200], "total": 0, "asins": []}


async def main():
    """Run comprehensive endpoint tests."""

    print("\n" + "#"*70)
    print("# KEEPA API ENDPOINT COMPARISON TEST")
    print("# Comparing different endpoints to find working solution")
    print("#"*70)

    results = {}
    total_tokens = 0

    # Test 1: Bestsellers (known to work)
    r1 = await test_bestsellers_endpoint(category=10777, domain=1)  # Law
    results["bestsellers_law"] = r1
    total_tokens += r1.get("tokens", 0)

    # Test 2: Search endpoint
    r2 = await test_search_endpoint(term="law textbook", domain=1)
    results["search_law"] = r2
    total_tokens += r2.get("tokens", 0)

    # Test 3: Query endpoint - minimal selection
    r3 = await test_query_endpoint(
        selection={"rootCategory": 10777, "perPage": 50},
        domain=1
    )
    results["query_minimal"] = r3
    total_tokens += r3.get("tokens", 0)

    # Test 4: Query endpoint - Books root category (283155)
    r4 = await test_query_endpoint(
        selection={"rootCategory": 283155, "perPage": 50},
        domain=1
    )
    results["query_books_root"] = r4
    total_tokens += r4.get("tokens", 0)

    # Test 5: Query endpoint - with salesRankRange format (from Python lib docs)
    r5 = await test_query_endpoint(
        selection={
            "rootCategory": 283155,
            "perPage": 50,
            "salesRankRange": [10000, 100000]  # Different format?
        },
        domain=1
    )
    results["query_salesrank_format"] = r5
    total_tokens += r5.get("tokens", 0)

    # Test 6: Query endpoint - with current_SALES (our format)
    r6 = await test_query_endpoint(
        selection={
            "rootCategory": 283155,
            "perPage": 50,
            "current_SALES_gte": 10000,
            "current_SALES_lte": 100000
        },
        domain=1
    )
    results["query_current_sales"] = r6
    total_tokens += r6.get("tokens", 0)

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for name, result in results.items():
        status = "OK" if result["success"] and result["total"] > 0 else "FAIL"
        print(f"  {name:<30}: {status} - {result['total']} results")

    print(f"\nTotal tokens consumed: {total_tokens}")

    # Conclusion
    print("\n" + "-"*70)
    working = [k for k, v in results.items() if v["success"] and v["total"] > 0]
    failing = [k for k, v in results.items() if not v["success"] or v["total"] == 0]

    if working:
        print(f"WORKING endpoints: {working}")
    if failing:
        print(f"FAILING endpoints: {failing}")

    print("-"*70)

    return results


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    results = asyncio.run(main())

    # Save results
    output_file = backend_dir / "scripts" / "endpoint_comparison_results.json"
    with open(output_file, "w") as f:
        # Clean for JSON
        clean = {}
        for k, v in results.items():
            clean[k] = {kk: vv for kk, vv in v.items() if kk != "asins"}
            clean[k]["asin_count"] = len(v.get("asins", []))
        json.dump(clean, f, indent=2)
    print(f"\nResults saved to: {output_file}")
