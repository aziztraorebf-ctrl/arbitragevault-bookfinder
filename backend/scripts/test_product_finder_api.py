"""
Test Script: Keepa Product Finder API Hypothesis Validation

Ce script teste l'API Product Finder pour valider l'hypothese que:
1. L'API peut pre-filtrer par nombre de FBA sellers
2. L'API peut exclure Amazon comme vendeur
3. Les resultats sont des produits "actionables" pour l'arbitrage

USAGE:
    cd backend
    python scripts/test_product_finder_api.py

REQUIRES:
    - KEEPA_API_KEY dans .env ou variable d'environnement
    - httpx (pip install httpx)

NOTE: Ce script est ISOLE - ne modifie aucun fichier du projet.
"""

import asyncio
import os
import sys
import json
from typing import Optional
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Load .env if exists
env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key, value)

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"


async def test_product_finder(
    domain: int = 1,
    root_category: int = 10777,  # Law
    bsr_min: int = 30000,
    bsr_max: int = 250000,
    price_min_cents: int = 4000,  # $40
    price_max_cents: int = 18000,  # $180
    max_fba_sellers: int = 3,
    exclude_amazon: bool = True,
    title_keywords: Optional[str] = "law textbook"
) -> dict:
    """
    Test Keepa Product Finder API directly.

    IMPORTANT: Product Finder uses GET with 'selection' param as JSON string!
    Doc: https://keepa.com/#!discuss/t/product-finder/150

    Returns dict with:
        - success: bool
        - asins: list of ASINs found
        - error: error message if failed
        - raw_response: full API response
    """
    if not KEEPA_API_KEY:
        return {"success": False, "error": "KEEPA_API_KEY not set", "asins": []}

    # Build selection object (this becomes JSON string in query param)
    selection = {
        "rootCategory": root_category,
        "perPage": 50,
    }

    # BSR range filter (current_SALES = BSR in Keepa API)
    if bsr_min is not None:
        selection["current_SALES_gte"] = bsr_min
    if bsr_max is not None:
        selection["current_SALES_lte"] = bsr_max

    # Price filter (NEW price = 3rd party sellers, in cents)
    if price_min_cents:
        selection["current_NEW_gte"] = price_min_cents
    if price_max_cents:
        selection["current_NEW_lte"] = price_max_cents

    # FBA seller count filter
    if max_fba_sellers is not None:
        selection["offerCountFBA_lte"] = max_fba_sellers

    # Exclude Amazon as seller
    # current_AMAZON_lte = -1 means "Amazon price must be <= -1" = no Amazon offer
    if exclude_amazon:
        selection["current_AMAZON_lte"] = -1

    # Title search
    if title_keywords:
        selection["title"] = title_keywords

    print("\n" + "="*60)
    print("KEEPA PRODUCT FINDER API TEST")
    print("="*60)
    print(f"\nEndpoint: {KEEPA_BASE_URL}/query")
    print(f"\nSelection Object:")
    for k, v in selection.items():
        print(f"  {k}: {v}")

    # Convert selection to JSON string for query param
    selection_json = json.dumps(selection)
    print(f"\nSelection JSON: {selection_json}")

    query_params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "selection": selection_json
    }

    print(f"\nQuery Params:")
    print(f"  domain: {domain}")
    print(f"  key: {'*' * 8}...{KEEPA_API_KEY[-4:]}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{KEEPA_BASE_URL}/query",
                params=query_params
            )

            print(f"\nHTTP Status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text[:500]
                print(f"Error Response: {error_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "asins": [],
                    "raw_response": error_text
                }

            data = response.json()

            # Check token balance
            tokens_left = data.get("tokensLeft", "unknown")
            tokens_consumed = data.get("tokensConsumed", "unknown")
            print(f"\nTokens consumed: {tokens_consumed}")
            print(f"Tokens remaining: {tokens_left}")

            # Extract ASINs
            asins = data.get("asinList", [])
            total_results = data.get("totalResults", 0)

            print(f"\nResults: {len(asins)} ASINs returned (total matching: {total_results})")

            return {
                "success": True,
                "asins": asins,
                "total_results": total_results,
                "tokens_consumed": tokens_consumed,
                "tokens_left": tokens_left,
                "raw_response": data
            }

        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout", "asins": []}
        except Exception as e:
            return {"success": False, "error": str(e), "asins": []}


async def get_product_details(asins: list, domain: int = 1) -> list:
    """
    Get product details for ASINs to verify they meet our criteria.
    """
    if not asins or not KEEPA_API_KEY:
        return []

    # Limit to first 5 for testing
    test_asins = asins[:5]

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "asin": ",".join(test_asins),
        "stats": 1,
        "history": 0
    }

    print(f"\n" + "-"*60)
    print(f"Fetching details for {len(test_asins)} ASINs...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{KEEPA_BASE_URL}/product",
                params=params
            )

            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                return []

            data = response.json()
            products = data.get("products", [])

            results = []
            for p in products:
                asin = p.get("asin", "?")
                title = p.get("title", "Unknown")[:60]
                stats = p.get("stats", {})
                current = stats.get("current", [])

                # Extract metrics
                # current[0] = AMAZON price
                # current[1] = NEW price (3rd party)
                # current[3] = BSR
                # current[11] = COUNT_NEW (FBA offers)
                amazon_price = current[0] if len(current) > 0 else None
                new_price = current[1] if len(current) > 1 else None
                bsr = current[3] if len(current) > 3 else None
                fba_count = current[11] if len(current) > 11 else None

                product_info = {
                    "asin": asin,
                    "title": title,
                    "amazon_price": f"${amazon_price/100:.2f}" if amazon_price and amazon_price > 0 else "N/A",
                    "new_price": f"${new_price/100:.2f}" if new_price and new_price > 0 else "N/A",
                    "bsr": bsr,
                    "fba_sellers": fba_count
                }
                results.append(product_info)

                # Print summary
                amazon_status = "AMAZON SELLING" if amazon_price and amazon_price > 0 else "No Amazon"
                print(f"\n  {asin}:")
                print(f"    Title: {title}...")
                print(f"    Price: {product_info['new_price']} | BSR: {bsr} | FBA Sellers: {fba_count}")
                print(f"    Amazon: {amazon_status}")

            return results

        except Exception as e:
            print(f"Error fetching details: {e}")
            return []


async def run_full_test():
    """Run complete hypothesis test."""

    print("\n" + "#"*60)
    print("# HYPOTHESIS TEST: Product Finder API for Low-Competition")
    print("#"*60)
    print("""
HYPOTHESIS:
  Using /query (Product Finder) endpoint with:
  - offerCountFBA_lte=3 (max 3 FBA sellers)
  - current_AMAZON_lte=-1 (exclude Amazon as seller)
  - title="law textbook" (keyword search)

  Should return products suitable for book arbitrage.
    """)

    # Test 1: Product Finder with all filters
    print("\n>>> TEST 1: Product Finder with ALL filters")
    result1 = await test_product_finder(
        root_category=10777,  # Law
        bsr_min=30000,
        bsr_max=250000,
        price_min_cents=4000,
        price_max_cents=18000,
        max_fba_sellers=3,
        exclude_amazon=True,
        title_keywords="law textbook"
    )

    if result1["success"] and result1["asins"]:
        print(f"\n>>> SUCCESS: Found {len(result1['asins'])} products!")
        await get_product_details(result1["asins"])
    else:
        print(f"\n>>> RESULT: {result1.get('error', 'No products found')}")

    # Test 2: Without title keywords (broader search)
    print("\n\n>>> TEST 2: Product Finder WITHOUT title keywords")
    result2 = await test_product_finder(
        root_category=10777,
        bsr_min=30000,
        bsr_max=250000,
        price_min_cents=4000,
        price_max_cents=18000,
        max_fba_sellers=3,
        exclude_amazon=True,
        title_keywords=None  # No keyword filter
    )

    if result2["success"] and result2["asins"]:
        print(f"\n>>> SUCCESS: Found {len(result2['asins'])} products!")
        await get_product_details(result2["asins"])
    else:
        print(f"\n>>> RESULT: {result2.get('error', 'No products found')}")

    # Test 3: Relaxed FBA filter (max 5)
    print("\n\n>>> TEST 3: Relaxed FBA filter (max 5 sellers)")
    result3 = await test_product_finder(
        root_category=10777,
        bsr_min=30000,
        bsr_max=250000,
        price_min_cents=4000,
        price_max_cents=18000,
        max_fba_sellers=5,  # More relaxed
        exclude_amazon=True,
        title_keywords="law"
    )

    if result3["success"] and result3["asins"]:
        print(f"\n>>> SUCCESS: Found {len(result3['asins'])} products!")
        await get_product_details(result3["asins"])
    else:
        print(f"\n>>> RESULT: {result3.get('error', 'No products found')}")

    # Summary
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Test 1 (all filters + keywords): {len(result1.get('asins', []))} products")
    print(f"Test 2 (no keywords):            {len(result2.get('asins', []))} products")
    print(f"Test 3 (relaxed FBA):            {len(result3.get('asins', []))} products")

    total_found = sum([
        len(result1.get('asins', [])),
        len(result2.get('asins', [])),
        len(result3.get('asins', []))
    ])

    print("\n" + "-"*60)
    if total_found > 0:
        print("HYPOTHESIS VALIDATED: Product Finder API returns low-competition products")
        print("RECOMMENDATION: Proceed with Phase 6.2 implementation")
    else:
        print("HYPOTHESIS NOT VALIDATED: Need to investigate API parameters")
        print("RECOMMENDATION: Check Keepa API documentation for correct filter syntax")
    print("-"*60)

    return {
        "test1": result1,
        "test2": result2,
        "test3": result3,
        "total_found": total_found
    }


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not found in environment or .env file")
        print("Set it with: export KEEPA_API_KEY=your_key")
        sys.exit(1)

    print(f"Using API key: {'*' * 20}...{KEEPA_API_KEY[-4:]}")

    results = asyncio.run(run_full_test())

    # Save results for analysis
    output_file = backend_dir / "scripts" / "product_finder_test_results.json"
    with open(output_file, "w") as f:
        # Remove raw_response for cleaner output
        clean_results = {}
        for k, v in results.items():
            if isinstance(v, dict):
                clean_results[k] = {kk: vv for kk, vv in v.items() if kk != "raw_response"}
            else:
                clean_results[k] = v
        json.dump(clean_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
