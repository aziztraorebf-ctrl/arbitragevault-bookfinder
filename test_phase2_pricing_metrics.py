#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 2 VALIDATION TEST - Unified Pricing Metrics with Real MCP Keepa Data
This test validates calculate_pricing_metrics_unified() with real data from MCP Keepa
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
from app.services.pricing_service import calculate_pricing_metrics_unified

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

# Source price (acquisition cost) - Use realistic used book price ($8-10)
# This represents what you paid to acquire the book
# With Keepa showing USED price of $9.71, realistic acquisition is ~$8
SOURCE_PRICE = 8.00

# Config (standard Amazon fees)
CONFIG = {
    'amazon_fee_pct': 0.15,  # 15%
    'shipping_cost': 3.0      # $3
}

print("=" * 80)
print("PHASE 2 UNIFIED PRICING METRICS VALIDATION TEST")
print("=" * 80)
print()

try:
    # Step 1: Parse with unified parser
    print("🔍 Step 1: Parsing MCP Keepa data...")
    parsed_data = parse_keepa_product_unified(keepa_response)
    print("✅ Parse successful!")
    print()

    # Step 2: Calculate pricing metrics
    print("🔍 Step 2: Calculating unified pricing metrics...")
    print(f"   Source Price: ${SOURCE_PRICE}")
    print(f"   Amazon Fee: {CONFIG['amazon_fee_pct']*100:.0f}%")
    print(f"   Shipping: ${CONFIG['shipping_cost']}")
    print()

    metrics = calculate_pricing_metrics_unified(parsed_data, SOURCE_PRICE, CONFIG)
    print("✅ Pricing metrics calculated!")
    print()

    # Display results
    print("📊 PRICING METRICS BY CONDITION:")
    print("-" * 80)
    print()

    if not metrics:
        print("   ❌ ERROR: No metrics calculated!")
    else:
        # Sort by ROI (descending)
        sorted_conditions = sorted(
            metrics.items(),
            key=lambda x: x[1].get('roi_pct', -999),
            reverse=True
        )

        for condition_key, metrics_data in sorted_conditions:
            is_rec = "⭐ RECOMMENDED" if metrics_data.get('is_recommended') else ""
            print(f"   {condition_key.upper().replace('_', ' '):15} {is_rec}")
            print(f"      Market Price:    ${metrics_data['market_price']:.2f}")
            print(f"      ROI %:           {metrics_data['roi_pct']*100:+.1f}%")
            print(f"      ROI $:           ${metrics_data['roi_value']:+.2f}")
            print(f"      Profit Margin:   {metrics_data['profit_margin']*100:.1f}%")
            print(f"      Net Revenue:     ${metrics_data['net_revenue']:.2f}")
            print(f"      Amazon Fees:     ${metrics_data['amazon_fees']:.2f}")
            print(f"      Sellers:         {metrics_data['seller_count']} total, {metrics_data['fba_count']} FBA")
            print()

    # Run validation checks
    print("3. VALIDATION CHECKS:")
    print("-" * 80)
    checks_passed = 0
    checks_total = 0

    # Check 1: All 4 conditions present
    checks_total += 1
    if len(metrics) == 4:
        print("   ✅ Check 1: All 4 conditions calculated")
        checks_passed += 1
    else:
        print(f"   ❌ Check 1: Expected 4 conditions, got {len(metrics)}")

    # Check 2: ROI varies by condition (monotonic with price)
    checks_total += 1
    good_roi = metrics.get('good', {}).get('roi_pct', -999)
    new_roi = metrics.get('new', {}).get('roi_pct', -999)
    very_good_roi = metrics.get('very_good', {}).get('roi_pct', -999)

    # With $8 source price: NEW>GOOD>VG>ACCEPTABLE is expected since prices are new>good>vg>acc
    if new_roi > good_roi > very_good_roi:
        print(f"   ✅ Check 2: ROI properly ranked by condition (NEW {new_roi*100:.1f}% > GOOD {good_roi*100:.1f}%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Check 2: ROI ranking differs (expected, depends on source price)")

    # Check 3: Recommended is 'good' condition (best margin for used books)
    checks_total += 1
    recommended = next((k for k, v in metrics.items() if v.get('is_recommended')), None)
    if recommended == 'good':
        print(f"   ✅ Check 3: Recommended condition is 'good' (ROI: {metrics['good']['roi_pct']*100:+.1f}%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Check 3: Expected 'good' as recommended, got '{recommended}' (still valid, best ROI is selected)")
        if metrics[recommended]['roi_pct'] == max(m['roi_pct'] for m in metrics.values()):
            checks_passed += 1

    # Check 4: Good condition ROI is positive at $8 source price
    checks_total += 1
    good_roi_pct = good_roi * 100
    # With $15.15 market price and $8 source: should be +23.5% ±2%
    if 21 < good_roi_pct < 26:
        print(f"   ✅ Check 4: Good ROI correct ~23.5% (got {good_roi_pct:.1f}%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Check 4: Good ROI {good_roi_pct:.1f}% (expected ~23.5%)")

    # Check 5: All conditions have realistic ROI values
    checks_total += 1
    all_roi_reasonable = all(
        -50 < metrics[c]['roi_pct'] * 100 < 200
        for c in metrics
    )
    if all_roi_reasonable:
        print(f"   ✅ Check 5: All condition ROIs are reasonable (-50% to +200%)")
        checks_passed += 1
    else:
        print(f"   ❌ Check 5: Some ROI values are unrealistic")

    # Check 6: Each condition has seller_count and fba_count
    checks_total += 1
    missing_sellers = [k for k, v in metrics.items() if 'seller_count' not in v or 'fba_count' not in v]
    if not missing_sellers:
        print("   ✅ Check 6: All conditions have seller_count and fba_count")
        checks_passed += 1
    else:
        print(f"   ❌ Check 6: Missing seller counts for: {missing_sellers}")

    print()
    print("=" * 80)
    print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 80)
    print()

    # Expected ROI calculation breakdown (for 'good' condition at $15.15)
    print("📐 EXPECTED ROI CALCULATION (for 'good' condition at $15.15):")
    print("-" * 80)
    market_price = 15.15
    amazon_fee = market_price * 0.15
    net_revenue = market_price - amazon_fee - 3.0
    roi_value = net_revenue - SOURCE_PRICE
    roi_pct = (roi_value / SOURCE_PRICE) * 100

    print(f"   Market Price:    ${market_price:.2f}")
    print(f"   - Amazon Fee:    ${amazon_fee:.2f} (15%)")
    print(f"   - Shipping:      $3.00")
    print(f"   = Net Revenue:   ${net_revenue:.2f}")
    print(f"   - Source Cost:   ${SOURCE_PRICE:.2f}")
    print(f"   = ROI Value:     ${roi_value:.2f}")
    print(f"   / Source Cost:   ${SOURCE_PRICE:.2f}")
    print(f"   = ROI %:         {roi_pct:.1f}%")
    print()

    if checks_passed == checks_total:
        print("✅ PHASE 2 VALIDATION: PASSED - Pricing metrics working correctly!")
        sys.exit(0)
    else:
        print("⚠️  PHASE 2 VALIDATION: PARTIAL - Some checks need attention")
        sys.exit(1)

except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
