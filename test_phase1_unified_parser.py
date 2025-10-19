#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 1 VALIDATION TEST - Unified Parser with Real MCP Keepa Data
This test validates parse_keepa_product_unified() with real data from MCP Keepa
"""

import sys
import json
import os

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, './backend')

from app.services.keepa_parser_v2 import parse_keepa_product_unified

# Real MCP Keepa response data for ASIN 0593655036
keepa_response = {
    "asin": "0593655036",
    "title": "The Anxious Generation: How the Great Rewiring of Childhood Is Causing an Epidemic of Mental Illness",
    "stats": {
        "current": [1698, 1400, 971, 66, 3000, None, None, None, None, None, 1888, None, None, None, None, 45, 1200, None]
    },
    "offers": [
        {"condition": 1, "sellerId": "ATVPDKIKX0DER", "isFBA": True, "isPrime": True, "isAmazon": True, "offerCSV": [[7596600, 1698, 0]]},
        {"condition": 5, "sellerId": "A263RIO308P3G8", "isFBA": False, "isPrime": False, "isAmazon": False, "offerCSV": [[7783248, 994, 449]]},
        {"condition": 4, "sellerId": "A1F5ORSGF7UA9M", "isFBA": False, "isPrime": False, "isAmazon": False, "offerCSV": [[7783248, 1515, 0]]},
        {"condition": 3, "sellerId": "A1AEW18JPFPJWB", "isFBA": False, "isPrime": False, "isAmazon": False, "offerCSV": [[7783248, 1060, 499]]},
    ]
}

print("=" * 80)
print("PHASE 1 UNIFIED PARSER VALIDATION TEST")
print("=" * 80)
print()

try:
    # Parse the data
    print("🔍 Parsing MCP Keepa data for ASIN 0593655036...")
    result = parse_keepa_product_unified(keepa_response)

    print("✅ Parser executed successfully!")
    print()

    # Validate current prices
    print("📊 VALIDATION RESULTS:")
    print("-" * 80)
    print()

    print("1. CURRENT PRICES EXTRACTION:")
    print(f"   Amazon Price:     ${result['current_amazon_price']}")
    print(f"   New Price:        ${result['current_new_price']}")
    print(f"   Used Price:       ${result['current_used_price']}")
    print(f"   FBA Price:        ${result['current_fba_price']}")
    print(f"   BSR (Sales Rank): {result['current_bsr']}")
    print()

    # Validate offers by condition
    print("2. OFFERS BY CONDITION:")
    offers = result['offers_by_condition']

    if not offers:
        print("   ❌ ERROR: No offers grouped by condition!")
    else:
        for cond_key, cond_data in sorted(offers.items()):
            print(f"   {cond_key.upper().replace('_', ' ')}:")
            print(f"     - Minimum Price:  ${cond_data['minimum_price']}")
            print(f"     - Seller Count:   {cond_data['seller_count']}")
            print(f"     - FBA Available:  {cond_data['fba_count']} offers")
    print()

    # Run validation checks
    print("3. VALIDATION CHECKS:")
    print("-" * 80)
    checks_passed = 0
    checks_total = 0

    # Check 1: BSR is 66, not -1
    checks_total += 1
    if result['current_bsr'] == 66:
        print("   ✅ Check 1: BSR correctly extracted (66)")
        checks_passed += 1
    else:
        print(f"   ❌ Check 1: BSR incorrect - got {result['current_bsr']}, expected 66")

    # Check 2: Offers grouped by 4 conditions
    checks_total += 1
    if len(offers) == 4:
        print(f"   ✅ Check 2: All 4 conditions present ({list(offers.keys())})")
        checks_passed += 1
    else:
        print(f"   ❌ Check 2: Expected 4 conditions, got {len(offers)}: {list(offers.keys())}")

    # Check 3: Good condition price < New condition price
    checks_total += 1
    if offers.get('good') and offers.get('new'):
        good_price = offers['good']['minimum_price']
        new_price = offers['new']['minimum_price']
        if good_price < new_price:
            print(f"   ✅ Check 3: Good (${good_price}) < New (${new_price})")
            checks_passed += 1
        else:
            print(f"   ❌ Check 3: Good (${good_price}) NOT < New (${new_price})")
    else:
        print("   ⚠️  Check 3: Skipped (missing good or new condition)")

    # Check 4: FBA price ($18.88) matches expected value
    checks_total += 1
    if result['current_fba_price'] == 18.88:
        print(f"   ✅ Check 4: FBA price correct (${result['current_fba_price']})")
        checks_passed += 1
    else:
        print(f"   ❌ Check 4: FBA price incorrect - got ${result['current_fba_price']}, expected $18.88")

    # Check 5: No null values for valid data
    checks_total += 1
    null_values = [k for k, v in result.items() if v is None and k not in ['current_list_price', 'history_new', 'history_used', 'history_fba']]
    if not null_values:
        print("   ✅ Check 5: No unexpected null values")
        checks_passed += 1
    else:
        print(f"   ⚠️  Check 5: Found null values: {null_values}")

    print()
    print("=" * 80)
    print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 80)

    if checks_passed == checks_total:
        print("✅ PHASE 1 VALIDATION: PASSED - Parser is working correctly!")
        sys.exit(0)
    else:
        print("⚠️  PHASE 1 VALIDATION: PARTIAL - Some checks need attention")
        sys.exit(1)

except Exception as e:
    print(f"❌ PARSER ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
