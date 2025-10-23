#!/usr/bin/env python
"""Test local du parser pour vérifier extraction historique."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.keepa_parser_v2 import parse_keepa_product_unified

# Test avec données simulées Keepa
fake_keepa_data = {
    "asin": "TEST123",
    "csv": [
        None,  # csv[0] - not used
        [100, 1000, 200, 1200, 300, 1400],  # csv[1] - NEW price (timestamps, cents)
        None,  # csv[2] - USED price
        [100, 50000, 200, 45000, 300, 40000],  # csv[3] - SALES rank (BSR)
        None, None, None, None, None, None,
        [50, 500, 150, 600]  # csv[10] - FBA price
    ],
    "stats": {
        "current": [
            0,  # [0] last update
            1400,  # [1] NEW price in cents
            None,  # [2] USED price
            40000,  # [3] BSR
            None, None, None, None, None, None,
            600  # [10] FBA price
        ]
    }
}

print("Test parsing Keepa data avec historique CSV")
print("=" * 60)

result = parse_keepa_product_unified(fake_keepa_data, "TEST123")

print(f"\nASIN: {result.get('asin')}")
print(f"Current BSR: {result.get('current_bsr')}")
print(f"Current Price: ${result.get('current_price', 0):.2f}")

print(f"\n[HISTORIQUE BSR]")
bsr_history = result.get('bsr_history', [])
print(f"  Points de données: {len(bsr_history)}")
if bsr_history:
    print(f"  Premiers points: {bsr_history[:3]}")
else:
    print("  VIDE - PROBLEME!")

print(f"\n[HISTORIQUE PRIX]")
price_history = result.get('price_history', [])
print(f"  Points de données: {len(price_history)}")
if price_history:
    print(f"  Premiers points: {price_history[:3]}")
else:
    print("  VIDE - PROBLEME!")

# Vérification
if bsr_history and price_history:
    print("\n✅ SUCCESS - Les tableaux d'historique sont peuplés")
    sys.exit(0)
else:
    print("\n❌ FAIL - Les tableaux d'historique sont vides")
    sys.exit(1)
