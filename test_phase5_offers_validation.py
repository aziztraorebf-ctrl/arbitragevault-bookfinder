#!/usr/bin/env python
"""
Phase 5: Validate offers_by_condition Feature

This test validates that the unified product builder correctly:
1. Returns offers_by_condition in all API responses
2. Includes all 4 conditions (new, very_good, good, acceptable)
3. Has minimum_price and minimum_price_cents per condition
4. Includes seller_count and fba_count
5. Has is_recommended flag on best ROI condition

Uses real MCP Keepa data to validate complete feature.
"""

import sys
import os
import json
import asyncio
from decimal import Decimal

# UTF-8 encoding wrapper for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.keepa_parser_v2 import parse_keepa_product_unified
from app.services.pricing_service import calculate_pricing_metrics_unified
from app.services.unified_analysis import build_unified_product_v2
from app.services.amazon_check_service import check_amazon_presence


async def test_phase5_offers_validation():
    """Test Phase 5: offers_by_condition feature validation"""

    print("\n" + "=" * 80)
    print("PHASE 5: VALIDATE offers_by_condition FEATURE")
    print("=" * 80)

    # Real Keepa data from previous tests (ASIN 0593655036)
    # Using MCP Keepa response format (not wrapped in 'data' field)
    raw_keepa_response = {
        'asin': '0593655036',
        'title': 'The Midnight Library: A Novel',
        'stats': {
            'current': [1698, 1400, 971, 66, 3000, None, None, None, None, None, 1888, None, None, None, None, 45, 1200, None]
        },
        'offers': [
            {'condition': 1, 'sellerId': 'ATVPDKIKX0DER', 'isFBA': True, 'isPrime': True, 'isAmazon': True, 'offerCSV': [[7596600, 1698, 0]]},
            {'condition': 1, 'sellerId': 'seller1', 'isFBA': False, 'isPrime': False, 'isAmazon': False, 'offerCSV': [[7596600, 1499, 0]]},
            {'condition': 3, 'sellerId': 'seller2', 'isFBA': True, 'isPrime': False, 'isAmazon': False, 'offerCSV': [[7596600, 1199, 0]]},
            {'condition': 3, 'sellerId': 'seller3', 'isFBA': False, 'isPrime': False, 'isAmazon': False, 'offerCSV': [[7596600, 1299, 499]]},
            {'condition': 4, 'sellerId': 'seller4', 'isFBA': True, 'isPrime': False, 'isAmazon': False, 'offerCSV': [[7596600, 899, 0]]},
            {'condition': 5, 'sellerId': 'seller5', 'isFBA': False, 'isPrime': False, 'isAmazon': False, 'offerCSV': [[7596600, 599, 449]]},
        ]
    }

    # Configuration
    config = {
        'amazon_fee_pct': 0.15,
        'shipping_cost': 3.0,
        'default_source_price': 8.0
    }

    print("\n📋 TEST DATA:")
    print(f"   ASIN:          {raw_keepa_response['asin']}")
    print(f"   Title:         The Midnight Library: A Novel")
    print(f"   Source Price:  $8.00")
    print(f"   Amazon Fee:    15%")
    print(f"   Shipping Cost: $3.00")

    # Parse with unified parser (Phase 1)
    print("\n" + "-" * 80)
    print("STEP 1: Parse with unified parser")
    print("-" * 80)

    parsed = parse_keepa_product_unified(raw_keepa_response)
    offers_by_condition = parsed.get('offers_by_condition', {})

    print(f"✅ Parsed data contains {len(offers_by_condition)} conditions:")
    for condition, data in offers_by_condition.items():
        print(f"   {condition}:")
        print(f"      minimum_price_cents: {data.get('minimum_price_cents')}")
        print(f"      minimum_price:       ${data.get('minimum_price'):.2f}")
        print(f"      seller_count:        {data.get('seller_count')}")
        print(f"      fba_count:           {data.get('fba_count')}")

    # Calculate pricing metrics (Phase 2)
    print("\n" + "-" * 80)
    print("STEP 2: Calculate pricing metrics with Phase 2")
    print("-" * 80)

    pricing_metrics = calculate_pricing_metrics_unified(
        parsed_data=parsed,
        source_price=8.0,
        config=config
    )

    print(f"✅ Calculated metrics for {len(pricing_metrics)} conditions:")

    # Validate each condition has required fields
    required_fields = ['market_price', 'roi_pct', 'roi_value', 'seller_count',
                       'fba_count', 'is_recommended', 'net_revenue', 'amazon_fees']

    for condition, metrics in sorted(pricing_metrics.items(),
                                     key=lambda x: x[1].get('roi_pct', 0),
                                     reverse=True):
        roi_pct = metrics.get('roi_pct', 0) * 100
        recommended = "✨ RECOMMENDED" if metrics.get('is_recommended') else ""
        print(f"\n   {condition.upper()}:")
        print(f"      Market Price:     ${metrics['market_price']:.2f}")
        print(f"      ROI %:            {roi_pct:+.1f}% {recommended}")
        print(f"      ROI Value:        ${metrics['roi_value']:.2f}")
        print(f"      Seller Count:     {metrics['seller_count']}")
        print(f"      FBA Count:        {metrics['fba_count']}")
        print(f"      Net Revenue:      ${metrics['net_revenue']:.2f}")
        print(f"      Amazon Fees:      ${metrics['amazon_fees']:.2f}")

        # Validate all required fields present
        missing_fields = [f for f in required_fields if f not in metrics]
        if missing_fields:
            print(f"      ❌ Missing fields: {missing_fields}")

    # Build unified product (Phase 3)
    print("\n" + "-" * 80)
    print("STEP 3: Build unified product with all endpoints view types")
    print("-" * 80)

    # Mock keepa_service for this test
    class MockKeepaService:
        pass

    view_types = ['analyse_manuelle', 'mes_niches', 'autosourcing']
    all_responses = {}

    for view_type in view_types:
        print(f"\n   Building for view_type: {view_type}")

        response = await build_unified_product_v2(
            raw_keepa=raw_keepa_response,
            keepa_service=MockKeepaService(),
            config=config,
            view_type=view_type,
            strategy='balanced' if view_type in ['mes_niches', 'autosourcing'] else None,
            compute_score=view_type in ['mes_niches', 'autosourcing'],
            source_price=8.0
        )

        all_responses[view_type] = response

        # Validate response structure
        print(f"      ✅ Response ASIN: {response.get('asin')}")
        print(f"      ✅ Has pricing.by_condition: {bool(response.get('pricing', {}).get('by_condition'))}")
        print(f"      ✅ Has pricing.recommended_condition: {bool(response.get('pricing', {}).get('recommended_condition'))}")
        print(f"      ✅ Has pricing.current_prices: {bool(response.get('pricing', {}).get('current_prices'))}")

    # ========================================================================
    # VALIDATION CHECKS
    # ========================================================================

    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    checks_passed = 0
    checks_total = 0

    # CHECK 1: All conditions present in parsed data
    print("\n✓ CHECK 1: All 4 conditions extracted by parser")
    checks_total += 1
    expected_conditions = {'new', 'very_good', 'good', 'acceptable'}
    actual_conditions = set(offers_by_condition.keys())

    if expected_conditions == actual_conditions:
        print(f"  ✅ PASS - All conditions: {actual_conditions}")
        checks_passed += 1
    else:
        missing = expected_conditions - actual_conditions
        extra = actual_conditions - expected_conditions
        print(f"  ❌ FAIL - Missing: {missing}, Extra: {extra}")

    # CHECK 2: All conditions in pricing metrics
    print("\n✓ CHECK 2: All conditions have pricing metrics")
    checks_total += 1
    actual_metrics_conditions = set(pricing_metrics.keys())

    if expected_conditions == actual_metrics_conditions:
        print(f"  ✅ PASS - All conditions: {actual_metrics_conditions}")
        checks_passed += 1
    else:
        missing = expected_conditions - actual_metrics_conditions
        extra = actual_metrics_conditions - expected_conditions
        print(f"  ❌ FAIL - Missing: {missing}, Extra: {extra}")

    # CHECK 3: Only ONE condition marked as recommended
    print("\n✓ CHECK 3: Exactly one condition marked as recommended")
    checks_total += 1
    recommended_conditions = [c for c, m in pricing_metrics.items() if m.get('is_recommended')]

    if len(recommended_conditions) == 1:
        print(f"  ✅ PASS - Recommended: {recommended_conditions[0]}")
        checks_passed += 1
    else:
        print(f"  ❌ FAIL - Found {len(recommended_conditions)} recommended conditions: {recommended_conditions}")

    # CHECK 4: Recommended condition has best ROI
    print("\n✓ CHECK 4: Recommended condition has best ROI")
    checks_total += 1
    roi_by_condition = {k: v['roi_pct'] for k, v in pricing_metrics.items()}
    best_roi_condition = max(roi_by_condition.items(), key=lambda x: x[1])[0]
    recommended = recommended_conditions[0] if recommended_conditions else None

    if recommended == best_roi_condition:
        best_roi_pct = roi_by_condition[best_roi_condition] * 100
        print(f"  ✅ PASS - {recommended} has best ROI: {best_roi_pct:+.1f}%")
        checks_passed += 1
    else:
        print(f"  ❌ FAIL - {recommended} vs best {best_roi_condition}")

    # CHECK 5: pricing.by_condition in all API responses
    print("\n✓ CHECK 5: pricing.by_condition present in all view_type responses")
    checks_total += 1
    all_have_by_condition = all(
        response.get('pricing', {}).get('by_condition')
        for response in all_responses.values()
    )

    if all_have_by_condition:
        for view_type in view_types:
            condition_keys = set(all_responses[view_type]['pricing']['by_condition'].keys())
            print(f"  ✅ {view_type}: {condition_keys}")
        checks_passed += 1
    else:
        print(f"  ❌ FAIL - Missing pricing.by_condition in some responses")

    # CHECK 6: Each condition has required fields
    print("\n✓ CHECK 6: Each condition has all required fields")
    checks_total += 1
    all_fields_present = True

    for condition, metrics in pricing_metrics.items():
        missing = [f for f in required_fields if f not in metrics]
        if missing:
            print(f"  ❌ {condition}: Missing {missing}")
            all_fields_present = False

    if all_fields_present:
        print(f"  ✅ PASS - All conditions have required fields")
        checks_passed += 1
    else:
        print(f"  ❌ FAIL - Some fields missing")

    # CHECK 7: Seller count accuracy
    print("\n✓ CHECK 7: Seller count accuracy per condition")
    checks_total += 1

    # From test data: new=2, very_good=2, good=1, acceptable=1
    expected_sellers = {'new': 2, 'very_good': 2, 'good': 1, 'acceptable': 1}
    all_correct = True

    for condition, expected_count in expected_sellers.items():
        actual_count = pricing_metrics[condition]['seller_count']
        if actual_count == expected_count:
            print(f"  ✅ {condition}: {actual_count} sellers")
        else:
            print(f"  ❌ {condition}: expected {expected_count}, got {actual_count}")
            all_correct = False

    if all_correct:
        checks_passed += 1

    # CHECK 8: FBA count accuracy
    print("\n✓ CHECK 8: FBA count accuracy per condition")
    checks_total += 1

    # From test data: new=1 FBA, very_good=1 FBA, good=1 FBA, acceptable=0 FBA
    expected_fba = {'new': 1, 'very_good': 1, 'good': 1, 'acceptable': 0}
    all_correct = True

    for condition, expected_count in expected_fba.items():
        actual_count = pricing_metrics[condition]['fba_count']
        if actual_count == expected_count:
            print(f"  ✅ {condition}: {actual_count} FBA")
        else:
            print(f"  ❌ {condition}: expected {expected_count}, got {actual_count}")
            all_correct = False

    if all_correct:
        checks_passed += 1

    # CHECK 9: Minimum price extraction
    print("\n✓ CHECK 9: Minimum price extraction and conversion")
    checks_total += 1

    all_prices_correct = True
    expected_prices = {
        'new': 1499 / 100,        # $14.99
        'very_good': 1199 / 100,  # $11.99
        'good': 899 / 100,        # $8.99
        'acceptable': 599 / 100   # $5.99
    }

    for condition, expected_price in expected_prices.items():
        actual_price = pricing_metrics[condition]['market_price']
        if abs(actual_price - expected_price) < 0.01:
            print(f"  ✅ {condition}: ${actual_price:.2f}")
        else:
            print(f"  ❌ {condition}: expected ${expected_price:.2f}, got ${actual_price:.2f}")
            all_prices_correct = False

    if all_prices_correct:
        checks_passed += 1

    # FINAL SUMMARY
    print("\n" + "=" * 80)
    print("PHASE 5 RESULTS")
    print("=" * 80)
    print(f"✅ PASSED: {checks_passed}/{checks_total} checks\n")

    if checks_passed == checks_total:
        print("🎉 PHASE 5 VALIDATION: PASSED - offers_by_condition feature complete!")
        return True
    else:
        print(f"⚠️  PHASE 5 VALIDATION: PARTIAL - {checks_total - checks_passed} checks failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_phase5_offers_validation())
    sys.exit(0 if result else 1)
