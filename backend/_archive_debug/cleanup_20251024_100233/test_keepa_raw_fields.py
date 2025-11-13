"""Test script to inspect raw Keepa product dict structure.

This script fetches a single product from Keepa and prints the raw response
to identify where sellerId and buyBoxSellerId fields are located.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.keepa_service import KeepaService


async def inspect_raw_keepa_fields():
    """Fetch raw Keepa data and inspect field structure."""
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ KEEPA_API_KEY not set")
        return

    keepa_service = KeepaService(api_key=api_key)

    print("Fetching raw Keepa data for ASIN: 0593655036")
    print("=" * 80)

    async with keepa_service:
        # Get raw product data (not parsed analysis)
        product = await keepa_service.get_product_data("0593655036", force_refresh=True)

        if not product:
            print("[ERROR] Product not found")
            return

        print("\n[SUCCESS] Product fetched successfully")
        print("\n[INFO] Top-level keys in raw Keepa response:")
        print("-" * 80)
        for key in sorted(product.keys()):
            value = product[key]
            value_type = type(value).__name__
            value_preview = str(value)[:100] if value else "None"
            print(f"  * {key:30s} ({value_type:15s}): {value_preview}")

        # Look for seller-related fields
        print("\n\n[INFO] Searching for seller-related fields...")
        print("-" * 80)
        seller_keywords = ["seller", "buybox", "offer", "merchant", "vendor"]
        for key in product.keys():
            if any(keyword in key.lower() for keyword in seller_keywords):
                print(f"  [FOUND] {key}")
                print(f"    Type: {type(product[key])}")
                print(f"    Value: {product[key]}")
                print()

        # Check for Amazon seller ID specifically
        amazon_seller_id = "ATVPDKIKX0DER"
        print(f"\n[INFO] Searching for Amazon seller ID: {amazon_seller_id}")
        print("-" * 80)

        def search_nested(obj, path=""):
            """Recursively search for Amazon seller ID in nested structures."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if v == amazon_seller_id:
                        print(f"  [MATCH] Found at: {path}.{k}")
                    search_nested(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if item == amazon_seller_id:
                        print(f"  [MATCH] Found at: {path}[{i}]")
                    search_nested(item, f"{path}[{i}]")
            elif obj == amazon_seller_id:
                print(f"  [MATCH] Found at: {path}")

        search_nested(product, "product")

        # Save raw response for inspection
        output_file = "keepa_raw_structure.json"
        with open(output_file, "w") as f:
            json.dump(product, f, indent=2, default=str)
        print(f"\n[SAVE] Raw response saved to: {output_file}")
        print(f"   File size: {os.path.getsize(output_file)} bytes")


if __name__ == "__main__":
    asyncio.run(inspect_raw_keepa_fields())
