#!/usr/bin/env python3
"""Debug script to understand Keepa history structure"""

import json
import requests
from datetime import datetime, timedelta

KEEPA_API_KEY = "rvd01p0nku3s8bsnbubeda6je1763vv5gc94jrng4eiakghlnv4bm3pmvd0sg7ru"

def debug_keepa_structure(asin: str):
    """Fetch and examine Keepa data structure for history."""

    print(f"\n{'='*60}")
    print(f"Debugging ASIN: {asin}")
    print(f"{'='*60}\n")

    # Fetch from Keepa with history
    params = {
        'key': KEEPA_API_KEY,
        'domain': 1,
        'asin': asin,
        'history': 1,  # Include price history
        'stats': 90,   # Include 90-day stats
        'rating': 1,
        'offers': 20
    }

    response = requests.get('https://api.keepa.com/product', params=params)
    response.raise_for_status()

    keepa_response = response.json()

    if not keepa_response.get('products'):
        print("No product data")
        return

    product = keepa_response['products'][0]

    # Check what keys are present
    print("Top-level keys present:")
    for key in sorted(product.keys()):
        value_type = type(product[key]).__name__
        if isinstance(product[key], (list, dict)):
            size = len(product[key])
            print(f"  - {key}: {value_type} (size={size})")
        else:
            print(f"  - {key}: {value_type}")

    # Check salesRanks structure
    print("\nsalesRanks structure:")
    sales_ranks = product.get('salesRanks', {})
    if sales_ranks:
        for cat_id, data in sales_ranks.items():
            if isinstance(data, list):
                print(f"  Category {cat_id}:")
                print(f"    - Type: {type(data).__name__}")
                print(f"    - Length: {len(data)}")
                if len(data) >= 2:
                    print(f"    - First 2 elements: {data[:2]}")
                    # Check if it's [timestamp, bsr] or [[timestamp, bsr], ...]
                    if isinstance(data[0], list):
                        print(f"    - FORMAT: List of pairs [[timestamp, bsr], ...]")
                        print(f"    - Sample pair: {data[0]}")
                    else:
                        print(f"    - FORMAT: Single pair [timestamp, bsr]")
    else:
        print("  No salesRanks data")

    # Check csv structure (often contains history)
    print("\nCSV structure:")
    csv_data = product.get('csv', [])
    if csv_data:
        print(f"  - Number of CSV arrays: {len(csv_data)}")
        for i, csv_array in enumerate(csv_data):
            if csv_array and isinstance(csv_array, list):
                print(f"  - CSV[{i}]: {len(csv_array)} elements")
                if len(csv_array) >= 4:
                    print(f"    Sample: {csv_array[:4]}")
    else:
        print("  No CSV data")

    # Check stats for BSR drops
    print("\nStats structure:")
    stats = product.get('stats', {})
    if stats:
        for key in ['salesRankDrops30', 'salesRankDrops90', 'salesRankDrops180']:
            if key in stats:
                print(f"  - {key}: {stats[key]}")

        # Check current array
        current = stats.get('current')
        if current and isinstance(current, list):
            print(f"  - current array length: {len(current)}")
            if len(current) > 3:
                print(f"    current[3] (BSR): {current[3]}")

    # Save full structure for analysis
    with open(f'keepa_debug_{asin}.json', 'w') as f:
        json.dump(product, f, indent=2)
    print(f"\nFull data saved to keepa_debug_{asin}.json")


# Test with a few ASINs
test_asins = ['0593655036', '0134685997', '1492056200']

for asin in test_asins:
    debug_keepa_structure(asin)
    print("\n" + "="*60)