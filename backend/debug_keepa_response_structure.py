"""
Debug: Examiner structure réponse Keepa pour comprendre pourquoi BSR = null.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

ASIN = "0593655036"  # Anxious Generation (best-seller confirmé)
BASE_URL = "https://arbitragevault-backend-v2.onrender.com"

print(f"🔍 Debugging Keepa Response Structure for ASIN {ASIN}\n")

response = requests.get(
    f"{BASE_URL}/api/v1/keepa/{ASIN}/metrics",
    timeout=30
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()

    print("\n📦 Response Structure:")
    print(f"   Keys: {list(data.keys())}")

    print("\n📊 keepa_metadata:")
    keepa_metadata = data.get("keepa_metadata", {})
    print(f"   Keys: {list(keepa_metadata.keys())}")
    print(f"   current_bsr: {keepa_metadata.get('current_bsr')}")
    print(f"   avg_90_bsr: {keepa_metadata.get('avg_90_bsr')}")
    print(f"   amazon_price: {keepa_metadata.get('amazon_price')}")

    print("\n🔎 raw_keepa_data (first 500 chars):")
    raw_data = keepa_metadata.get("raw_keepa_data", {})
    raw_str = json.dumps(raw_data, indent=2)[:500]
    print(raw_str)

    # Export complet
    with open("last_api_result.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("\n✅ Full response exported to: last_api_result.json")
else:
    print(f"❌ Error: {response.text}")
