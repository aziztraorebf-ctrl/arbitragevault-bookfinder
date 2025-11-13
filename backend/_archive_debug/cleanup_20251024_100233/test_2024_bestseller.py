"""Test avec un bestseller 2024 vérifié actif"""
import requests
import os
from datetime import datetime

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_EPOCH = 971222400

# Atomic Habits by James Clear - #1 bestseller 2024, sorti en 2018
# Devrait avoir des données récentes vu l'activité
TEST_ASIN = "0735211299"

def keepa_ts_to_dt(keepa_min):
    return datetime.fromtimestamp(KEEPA_EPOCH + (keepa_min * 60))

params = {
    "key": KEEPA_API_KEY,
    "domain": 1,
    "asin": TEST_ASIN,
    "stats": 180,
    "history": 1,
    "offers": 20,
    "update": 0
}

print(f"Testing ASIN {TEST_ASIN} (Atomic Habits - #1 bestseller 2024)")
print("Calling Keepa API with update=0...")

response = requests.get("https://api.keepa.com/product", params=params, timeout=30)
data = response.json()

product = data["products"][0]
last_update = product.get("lastUpdate")
tokens_left = data.get("tokensLeft")

if last_update:
    dt = keepa_ts_to_dt(last_update)
    age_days = (datetime.now() - dt).days
    print(f"\nlastUpdate: {dt}")
    print(f"Age: {age_days} days")
    print(f"Tokens left: {tokens_left}")
    
    if age_days > 365:
        print(f"\nCRITICAL: Data is {age_days} days old despite update=0!")
    else:
        print(f"\nOK: Data is fresh (< 1 year)")
