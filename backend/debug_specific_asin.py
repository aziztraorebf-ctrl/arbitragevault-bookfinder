"""Debug specific ASIN B07FZ8S74R (Kindle Oasis) that has salesRanks but no BSR parsed"""
import requests
import json

KEEPA_API_KEY = "rvd01p0nku3s8bsnbubeda6je1763vv5gc94jrng4eiakghlnv4bm3pmvd0sg7ru"
ASIN = "B07FZ8S74R"  # Kindle Oasis

url = "https://api.keepa.com/product"
params = {
    "key": KEEPA_API_KEY,
    "domain": 1,
    "asin": ASIN,
    "history": 0,
    "stats": 90
}

response = requests.get(url, params=params, timeout=30)
data = response.json()

if data.get("products"):
    product = data["products"][0]

    print(f"ASIN: {ASIN}")
    print(f"salesRankReference: {product.get('salesRankReference')}")
    print(f"salesRanks keys: {list(product.get('salesRanks', {}).keys())}")

    if product.get('salesRanks'):
        print("\nDetailed salesRanks:")
        for category_id, rank_data in product['salesRanks'].items():
            print(f"  Category {category_id}: {rank_data}")
            if isinstance(rank_data, list) and len(rank_data) >= 2:
                print(f"    -> BSR value: {rank_data[1]}")

    # Save for analysis
    with open("debug_kindle_oasis.json", "w") as f:
        json.dump(product, f, indent=2)

    print("\n✅ Full product data saved to debug_kindle_oasis.json")