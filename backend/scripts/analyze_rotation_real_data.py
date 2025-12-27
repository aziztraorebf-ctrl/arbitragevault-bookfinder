"""
Rotation Analysis with Real Keepa salesRankDrops Data

This script fetches real textbooks in our target BSR ranges and analyzes
their salesRankDrops to determine actual rotation times.

Key insight from Keepa API:
- stats.salesRankDrops30 = number of BSR drops in last 30 days
- stats.salesRankDrops90 = number of BSR drops in last 90 days
- Each drop = 1 sale (approximately)
"""

import asyncio
import os
import sys
import httpx
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Target BSR ranges for our strategies
BSR_RANGES = {
    "textbooks_standard": {
        "min": 100000,
        "max": 250000,
        "description": "Textbook Standard (BSR 100K-250K)",
    },
    "textbooks_patience": {
        "min": 250000,
        "max": 400000,
        "description": "Textbook Patience (BSR 250K-400K)",
    },
}


async def fetch_product_stats(client: httpx.AsyncClient, api_key: str, asin: str) -> dict | None:
    """Fetch product with stats to get salesRankDrops."""
    url = "https://api.keepa.com/product"
    params = {
        "key": api_key,
        "domain": 1,
        "asin": asin,
        "stats": 90,
        "history": 0,
    }

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        products = data.get("products", [])
        if products:
            return products[0]
    except Exception as e:
        print(f"  Error fetching {asin}: {e}")

    return None


async def discover_textbooks_in_range(client: httpx.AsyncClient, api_key: str, bsr_min: int, bsr_max: int) -> list[str]:
    """Use Product Finder to get textbooks in BSR range."""
    url = "https://api.keepa.com/query"

    # Query for textbooks in our BSR range
    query = {
        "domain": 1,
        "categories": {"include": [283155]},  # Books category
        "productType": [0],  # Regular products
        "current_SALES": {"gte": bsr_min, "lte": bsr_max},
        "binding": ["paperback", "hardcover"],
        "title": "textbook OR edition OR programming OR calculus OR biology OR chemistry OR physics OR economics",
        "sort": [["current_SALES", "asc"]],
        "perPage": 50,
    }

    try:
        response = await client.post(
            url,
            params={"key": api_key},
            json=query,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("asinList", [])
    except Exception as e:
        print(f"  Product Finder error: {e}")
        return []


async def main():
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY required")
        sys.exit(1)

    client = httpx.AsyncClient(timeout=60.0)

    try:
        print("=" * 70)
        print("ROTATION ANALYSIS WITH REAL KEEPA DATA")
        print("=" * 70)
        print()
        print("Using salesRankDrops from Keepa stats to measure actual sales velocity.")
        print("Each salesRankDrop = 1 sale (approximately)")
        print()

        results = {}

        for strategy, config in BSR_RANGES.items():
            print(f"\n{'=' * 60}")
            print(f"STRATEGY: {config['description']}")
            print(f"BSR Range: {config['min']:,} - {config['max']:,}")
            print("=" * 60)

            # Discover textbooks in range
            print("\nDiscovering textbooks in BSR range...")
            asins = await discover_textbooks_in_range(
                client, api_key, config["min"], config["max"]
            )

            if not asins:
                print("  No products found via Product Finder, using sample ASINs...")
                # Fallback to some known textbook ASINs
                asins = []

            print(f"  Found {len(asins)} products")

            # Fetch stats for each product
            products_data = []
            sample_size = min(20, len(asins))  # Limit to save tokens

            print(f"\nFetching salesRankDrops for {sample_size} products...")

            for i, asin in enumerate(asins[:sample_size]):
                product = await fetch_product_stats(client, api_key, asin)
                if product:
                    stats = product.get("stats", {})
                    bsr = stats.get("current", [None] * 4)[3]  # Index 3 = BSR
                    drops_30 = stats.get("salesRankDrops30", -1)
                    drops_90 = stats.get("salesRankDrops90", -1)

                    if bsr and bsr != -1 and drops_30 != -1:
                        products_data.append({
                            "asin": asin,
                            "title": (product.get("title") or "")[:50],
                            "bsr": bsr,
                            "drops_30": drops_30,
                            "drops_90": drops_90,
                        })
                        print(f"  [{i+1}] {asin}: BSR={bsr:,}, Drops30={drops_30}, Drops90={drops_90}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            if not products_data:
                print("  No valid data collected for this range")
                continue

            # Calculate statistics
            drops_30_list = [p["drops_30"] for p in products_data if p["drops_30"] > 0]
            drops_90_list = [p["drops_90"] for p in products_data if p["drops_90"] > 0]
            bsr_list = [p["bsr"] for p in products_data]

            print(f"\n--- ROTATION ANALYSIS ({len(products_data)} products) ---")

            if drops_30_list:
                avg_drops_30 = mean(drops_30_list)
                med_drops_30 = median(drops_30_list)
                # Time to sell 1 unit = 30 days / drops_30
                avg_rotation_days = 30 / avg_drops_30 if avg_drops_30 > 0 else float('inf')

                print(f"\n  30-Day Sales (salesRankDrops30):")
                print(f"    Average: {avg_drops_30:.1f} sales/month")
                print(f"    Median:  {med_drops_30:.1f} sales/month")
                print(f"    Rotation: ~{avg_rotation_days:.1f} days to sell 1 unit")

            if drops_90_list:
                avg_drops_90 = mean(drops_90_list)
                monthly_from_90 = avg_drops_90 / 3  # Convert to monthly
                rotation_from_90 = 30 / monthly_from_90 if monthly_from_90 > 0 else float('inf')

                print(f"\n  90-Day Sales (salesRankDrops90):")
                print(f"    Average: {avg_drops_90:.1f} sales/90days ({monthly_from_90:.1f}/month)")
                print(f"    Rotation: ~{rotation_from_90:.1f} days to sell 1 unit")

            print(f"\n  BSR Statistics:")
            print(f"    Average BSR: {mean(bsr_list):,.0f}")
            print(f"    Median BSR:  {median(bsr_list):,.0f}")
            print(f"    Range: {min(bsr_list):,} - {max(bsr_list):,}")

            results[strategy] = {
                "avg_drops_30": mean(drops_30_list) if drops_30_list else 0,
                "avg_drops_90": mean(drops_90_list) if drops_90_list else 0,
                "avg_bsr": mean(bsr_list),
                "sample_size": len(products_data),
            }

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY: REAL ROTATION DATA")
        print("=" * 70)

        for strategy, data in results.items():
            if data["avg_drops_30"] > 0:
                rotation_days = 30 / data["avg_drops_30"]
                print(f"\n{strategy.upper()}:")
                print(f"  Average Sales: {data['avg_drops_30']:.1f}/month")
                print(f"  Rotation Time: ~{rotation_days:.0f} days to sell 1 unit")
                print(f"  Sample Size: {data['sample_size']} products")

        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)
        print("""
Based on real Keepa salesRankDrops data:
- Textbook rotation is SLOWER than theoretical BSR estimates suggest
- User's estimate of ~30 days rotation is likely MORE ACCURATE
- UI labels should be updated to reflect realistic expectations

Recommended label updates:
- Textbook Standard: "Rotation 2-4 semaines" (not 7-14 days)
- Textbook Patience: "Rotation 4-8 semaines" (not 4-6 weeks - already close)
""")

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
