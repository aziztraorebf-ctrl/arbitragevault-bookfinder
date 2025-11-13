"""Check Keepa account status and limitations"""
import requests
import os

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")

# Test 1: Check tokens status
print("="*80)
print("KEEPA ACCOUNT INFO")
print("="*80)

response = requests.get(
    "https://api.keepa.com/token",
    params={"key": KEEPA_API_KEY}
)

print(f"\nStatus: {response.status_code}")
print(f"Response:\n{response.json()}")

# Test 2: Try with only=offers,history to verify update parameter
print("\n" + "="*80)
print("TEST: Minimal request with update=0")
print("="*80)

response2 = requests.get(
    "https://api.keepa.com/product",
    params={
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": "0735211299",
        "update": 0,
        "only": "offers"
    },
    timeout=30
)

data2 = response2.json()
product2 = data2.get("products", [{}])[0]
last_update2 = product2.get("lastUpdate")

print(f"lastUpdate with only=offers: {last_update2}")

if last_update2:
    from datetime import datetime
    KEEPA_EPOCH = 971222400
    dt = datetime.fromtimestamp(KEEPA_EPOCH + (last_update2 * 60))
    age_days = (datetime.now() - dt).days
    print(f"Date: {dt}")
    print(f"Age: {age_days} days")
