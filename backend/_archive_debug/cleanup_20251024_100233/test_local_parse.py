"""Test local parsing to verify current_bsr is extracted."""
import json
from app.services.keepa_parser import parse_keepa_product

# Load our saved Keepa response
with open('keepa_full_response_airpods.json', 'r') as f:
    raw_keepa = json.load(f)

print("🔍 Test Local Parsing")
print("="*60)

# Parse
parsed = parse_keepa_product(raw_keepa)

# Check fields
print(f"\nASIN: {parsed.get('asin')}")
print(f"Titre: {parsed.get('title', 'N/A')[:50]}...")
print(f"current_price: {parsed.get('current_price')}")
print(f"current_bsr: {parsed.get('current_bsr')}")

# Check if fields are in the dict
print(f"\n📋 Clés dans parsed_data (top 20):")
keys = list(parsed.keys())[:20]
for key in keys:
    if 'current' in key or 'bsr' in key.lower():
        print(f"  ✅ {key}: {parsed[key]}")

if 'current_bsr' in parsed:
    print(f"\n✅ current_bsr présent dans parsed_data: {parsed['current_bsr']}")
else:
    print(f"\n❌ current_bsr MANQUANT dans parsed_data")
