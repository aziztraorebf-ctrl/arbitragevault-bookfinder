#!/usr/bin/env python3
"""
Debug pourquoi 63% des ASINs n'ont pas de prix
"""

import json
import requests

KEEPA_API_KEY = "rvd01p0nku3s8bsnbubeda6je1763vv5gc94jrng4eiakghlnv4bm3pmvd0sg7ru"

# ASINs qui ont échoué
FAILED_ASINS = [
    "0134895436",  # Textbook
    "0063340240",  # Business
    "0593579135",  # Business
    "0593723597",  # Business
    "0593713842",  # Fiction
    "0593449274",  # Fiction
    "B0CW1SXHZL",  # Fiction
    "1492056200",  # Technical
]

def debug_asin(asin):
    """Debug un ASIN pour comprendre pourquoi pas de prix."""

    print(f"\n{'='*60}")
    print(f"Debugging: {asin}")
    print(f"{'='*60}")

    # Fetch avec tous les paramètres
    params = {
        'key': KEEPA_API_KEY,
        'domain': 1,
        'asin': asin,
        'stats': 90,
        'history': 1,
        'offers': 50,  # Plus d'offres
        'rating': 1,
        'buybox': 1
    }

    response = requests.get('https://api.keepa.com/product', params=params)
    data = response.json()

    if not data.get('products'):
        print("[ERROR] No product data")
        return

    product = data['products'][0]

    # 1. Check basic info
    title = product.get('title') or 'N/A'
    print(f"Title: {title[:60] if title else 'N/A'}")
    print(f"ASIN: {product.get('asin')}")

    # 2. Check stats.current array
    stats = product.get('stats', {})
    current = stats.get('current')

    if current:
        print(f"\nstats.current array (length={len(current)}):")

        # Key indices for prices
        indices = {
            0: "AMAZON",
            1: "NEW",
            7: "NEW_FBA_LOWEST",
            10: "NEW_FBM_SHIPPING",
            18: "BUY_BOX"
        }

        for idx, name in indices.items():
            if len(current) > idx:
                val = current[idx]
                if val and val != -1:
                    print(f"  [{idx}] {name}: ${val/100:.2f}")
                else:
                    print(f"  [{idx}] {name}: None/Out of stock")

    # 3. Check CSV data
    csv_data = product.get('csv', [])
    if csv_data:
        print(f"\nCSV arrays present: {len(csv_data)}")
        for i, csv_array in enumerate(csv_data[:5]):  # First 5 CSV arrays
            if csv_array and isinstance(csv_array, list) and len(csv_array) > 0:
                # Get last value (most recent)
                last_val = csv_array[-1] if len(csv_array) >= 1 else None
                if last_val and last_val != -1:
                    print(f"  CSV[{i}] last value: ${last_val/100:.2f}")
                else:
                    print(f"  CSV[{i}]: No data or out of stock")

    # 4. Check offers
    offers = product.get('offers')
    if offers:
        print(f"\nOffers data:")
        for i, offer in enumerate(offers[:3]):  # First 3 offers
            print(f"  Offer {i+1}:")
            print(f"    - Condition: {offer.get('condition')}")
            print(f"    - FBA: {offer.get('isFBA')}")
            print(f"    - Price: ${offer.get('offerPrice', 0)/100:.2f}")
            print(f"    - Seller: {offer.get('sellerName', 'N/A')[:30]}")
    else:
        print("\nNo offers available")

    # 5. Check availability
    avail = product.get('availabilityAmazon')
    if avail:
        print(f"\nAmazon availability: {avail}")

    # Save full data
    with open(f'debug_{asin}.json', 'w') as f:
        json.dump(product, f, indent=2)
    print(f"\nFull data saved to debug_{asin}.json")


# Test first few ASINs
for asin in FAILED_ASINS[:3]:
    debug_asin(asin)