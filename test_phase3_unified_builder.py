#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 3 VALIDATION TEST - Unified Product Builder v2 with Real MCP Keepa Data
This test validates build_unified_product_v2() used by ALL endpoints
"""

import sys
import json
import os
import asyncio

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, './backend')

from app.services.unified_analysis import build_unified_product_v2

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

# Config
CONFIG = {
    'amazon_fee_pct': 0.15,
    'shipping_cost': 3.0,
    'default_source_price': 8.0
}

async def run_tests():
    print("=" * 80)
    print("PHASE 3 UNIFIED PRODUCT BUILDER v2 VALIDATION TEST")
    print("=" * 80)
    print()

    try:
        # Test 1: build_unified_product_v2 for Analyse Manuelle
        print("🔍 Test 1: Building product for ANALYSE MANUELLE...")
        product_manuelle = await build_unified_product_v2(
            raw_keepa=keepa_response,
            keepa_service=None,
            config=CONFIG,
            view_type='analyse_manuelle',
            compute_score=False,
            source_price=5.00  # Custom source price
        )
        print("✅ Analyse Manuelle product built!")
        print()

        # Test 2: build_unified_product_v2 for Mes Niches
        print("🔍 Test 2: Building product for MES NICHES...")
        product_mes_niches = await build_unified_product_v2(
            raw_keepa=keepa_response,
            keepa_service=None,
            config=CONFIG,
            view_type='mes_niches',
            strategy='arbitrage',
            compute_score=True,
            source_price=None  # Use config default
        )
        print("✅ Mes Niches product built!")
        print()

        # Test 3: build_unified_product_v2 for AutoSourcing
        print("🔍 Test 3: Building product for AUTOSOURCING...")
        product_autosourcing = await build_unified_product_v2(
            raw_keepa=keepa_response,
            keepa_service=None,
            config=CONFIG,
            view_type='autosourcing',
            strategy='velocity',
            compute_score=True,
            source_price=None  # Use config default
        )
        print("✅ AutoSourcing product built!")
        print()

        # Display results
        print("📊 PRODUCT STRUCTURE VALIDATION:")
        print("-" * 80)
        print()

        print("1. ANALYSE MANUELLE (source_price=$5.00):")
        print(f"   ASIN:                {product_manuelle.get('asin')}")
        title = product_manuelle.get('title')
        print(f"   Title:               {(title[:50] + '...') if title else 'N/A'}")
        print(f"   View Type:           {product_manuelle.get('view_type')}")
        print(f"   Pricing.Source:      ${product_manuelle['pricing'].get('source_price'):.2f}")
        print(f"   Recommended:         {product_manuelle['pricing'].get('recommended_condition')}")
        print(f"   Best Condition ROI:  {product_manuelle['pricing']['by_condition'].get(product_manuelle['pricing'].get('recommended_condition'), {}).get('roi_pct', 0)*100:+.1f}%")
        print(f"   Current BSR:         {product_manuelle.get('current_bsr')}")
        print(f"   Amazon on Listing:   {product_manuelle.get('amazon_on_listing')}")
        print(f"   Has Score:           {'score' in product_manuelle}")
        print()

        print("2. MES NICHES (source_price=$8.00 default):")
        print(f"   ASIN:                {product_mes_niches.get('asin')}")
        print(f"   View Type:           {product_mes_niches.get('view_type')}")
        print(f"   Pricing.Source:      ${product_mes_niches['pricing'].get('source_price'):.2f}")
        print(f"   Recommended:         {product_mes_niches['pricing'].get('recommended_condition')}")
        print(f"   Best Condition ROI:  {product_mes_niches['pricing']['by_condition'].get(product_mes_niches['pricing'].get('recommended_condition'), {}).get('roi_pct', 0)*100:+.1f}%")
        print(f"   Score:               {product_mes_niches.get('score', 'N/A')}")
        print(f"   Strategy Profile:    {product_mes_niches.get('strategy_profile', 'N/A')}")
        print()

        print("3. AUTOSOURCING:")
        print(f"   ASIN:                {product_autosourcing.get('asin')}")
        print(f"   View Type:           {product_autosourcing.get('view_type')}")
        print(f"   Pricing.Source:      ${product_autosourcing['pricing'].get('source_price'):.2f}")
        print(f"   Recommended:         {product_autosourcing['pricing'].get('recommended_condition')}")
        print(f"   Score:               {product_autosourcing.get('score', 'N/A')}")
        print(f"   Strategy Profile:    {product_autosourcing.get('strategy_profile', 'N/A')}")
        print()

        # Run validation checks
        print("4. VALIDATION CHECKS:")
        print("-" * 80)
        checks_passed = 0
        checks_total = 0

        # Check 1: All three views have ASIN
        checks_total += 1
        if (product_manuelle.get('asin') == product_mes_niches.get('asin') ==
            product_autosourcing.get('asin') == '0593655036'):
            print("   ✅ Check 1: All views have correct ASIN")
            checks_passed += 1
        else:
            print("   ❌ Check 1: ASIN mismatch between views")

        # Check 2: Analyse Manuelle and Mes Niches have same pricing (different source prices though!)
        checks_total += 1
        manuelle_roi = product_manuelle['pricing']['by_condition'].get(
            product_manuelle['pricing'].get('recommended_condition'), {}
        ).get('roi_pct')
        mes_niches_roi = product_mes_niches['pricing']['by_condition'].get(
            product_mes_niches['pricing'].get('recommended_condition'), {}
        ).get('roi_pct')

        # They should have different ROI because different source prices
        # But same structure
        if (manuelle_roi is not None and mes_niches_roi is not None and
            'by_condition' in product_manuelle['pricing'] and
            'by_condition' in product_mes_niches['pricing']):
            print(f"   ✅ Check 2: Both have pricing breakdown structure (different ROI due to source prices)")
            checks_passed += 1
        else:
            print("   ❌ Check 2: Missing pricing breakdown structure")

        # Check 3: Mes Niches has score, Analyse Manuelle does not
        checks_total += 1
        if 'score' not in product_manuelle and 'score' in product_mes_niches:
            print(f"   ✅ Check 3: Score correctly absent from Analyse Manuelle, present in Mes Niches")
            checks_passed += 1
        else:
            print(f"   ❌ Check 3: Score handling incorrect (Manuelle has: {'score' in product_manuelle}, Niches has: {'score' in product_mes_niches})")

        # Check 4: All views have current_bsr
        checks_total += 1
        if (product_manuelle.get('current_bsr') == product_mes_niches.get('current_bsr') ==
            product_autosourcing.get('current_bsr') == 66):
            print("   ✅ Check 4: All views have correct BSR=66")
            checks_passed += 1
        else:
            print(f"   ❌ Check 4: BSR mismatch (Manuelle={product_manuelle.get('current_bsr')}, Niches={product_mes_niches.get('current_bsr')}, Auto={product_autosourcing.get('current_bsr')})")

        # Check 5: All have pricing.by_condition with 4 conditions
        checks_total += 1
        manuelle_conds = len(product_manuelle['pricing'].get('by_condition', {}))
        niches_conds = len(product_mes_niches['pricing'].get('by_condition', {}))
        auto_conds = len(product_autosourcing['pricing'].get('by_condition', {}))

        if manuelle_conds == niches_conds == auto_conds == 4:
            print(f"   ✅ Check 5: All views have 4 conditions in pricing breakdown")
            checks_passed += 1
        else:
            print(f"   ❌ Check 5: Condition count mismatch (Manuelle={manuelle_conds}, Niches={niches_conds}, Auto={auto_conds})")

        # Check 6: View types are set correctly
        checks_total += 1
        if (product_manuelle.get('view_type') == 'analyse_manuelle' and
            product_mes_niches.get('view_type') == 'mes_niches' and
            product_autosourcing.get('view_type') == 'autosourcing'):
            print("   ✅ Check 6: View types correctly set")
            checks_passed += 1
        else:
            print("   ❌ Check 6: View type mismatch")

        # Check 7: All have velocity metrics
        checks_total += 1
        if (product_manuelle.get('velocity') and
            product_mes_niches.get('velocity') and
            product_autosourcing.get('velocity')):
            print("   ✅ Check 7: All views have velocity metrics")
            checks_passed += 1
        else:
            print("   ❌ Check 7: Missing velocity metrics")

        print()
        print("=" * 80)
        print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
        print("=" * 80)
        print()

        if checks_passed == checks_total:
            print("✅ PHASE 3 VALIDATION: PASSED - Unified builder working correctly!")
            return 0
        else:
            print("⚠️  PHASE 3 VALIDATION: PARTIAL - Some checks need attention")
            return 1

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
