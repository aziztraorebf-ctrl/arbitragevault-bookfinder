"""
Debug script to examine Keepa product data structure
and find where salesDrops data is stored.
"""

import asyncio
import os
import sys
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY required")
        sys.exit(1)

    client = httpx.AsyncClient(timeout=60.0)

    try:
        # Fetch a few products with full stats
        url = "https://api.keepa.com/product"
        params = {
            "key": api_key,
            "domain": 1,
            "asin": "0134685997,0321125215,0596007124",  # Sample textbook ASINs
            "stats": 90,
            "offers": 0,
        }

        print("Fetching sample products to examine data structure...")
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        products = data.get("products", [])
        print(f"\nFound {len(products)} products\n")

        for p in products:
            print("=" * 60)
            print(f"ASIN: {p.get('asin')}")
            print(f"Title: {(p.get('title') or '')[:50]}")

            stats = p.get("stats", {})

            # Check all possible locations for sales data
            print("\n--- stats keys ---")
            for key in sorted(stats.keys()):
                value = stats[key]
                if "sale" in key.lower() or "drop" in key.lower() or "buy" in key.lower():
                    print(f"  {key}: {value}")

            # Check current array
            current = stats.get("current", [])
            print(f"\n--- stats.current (length={len(current)}) ---")

            # Known indices from Keepa documentation
            indices_of_interest = {
                0: "AMAZON",
                1: "NEW",
                2: "USED",
                3: "SALES (BSR)",
                4: "LISTPRICE",
                10: "NEW_FBM_SHIPPING",
                11: "LIGHTNING_DEAL",
                18: "SALES_RANK_DROPS_current",
                19: "BUY_BOX_SELLER",
                20: "USED_VERY_GOOD",
                21: "USED_GOOD",
                22: "USED_ACCEPTABLE",
                31: "COLLECTIBLE",
            }

            for idx in range(min(40, len(current))):
                val = current[idx] if idx < len(current) else None
                label = indices_of_interest.get(idx, "")
                if val is not None and val != -1:
                    print(f"  [{idx}] {label}: {val}")

            # Check for salesDrops at top level
            print("\n--- Top level sales-related keys ---")
            for key in p.keys():
                if "sale" in key.lower() or "drop" in key.lower():
                    print(f"  {key}: {p[key]}")

            # Check avg30/avg90 which might have sales data
            print("\n--- avg30 (sample) ---")
            avg30 = stats.get("avg30", [])
            if avg30:
                for idx in range(min(20, len(avg30))):
                    val = avg30[idx] if idx < len(avg30) else None
                    if val is not None and val != -1:
                        print(f"  [{idx}]: {val}")

            print("\n")

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
