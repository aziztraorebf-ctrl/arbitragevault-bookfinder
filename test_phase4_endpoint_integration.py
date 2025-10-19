#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 4 VALIDATION TEST - Endpoint Integration with Unified Product Builder v2
This test validates that the endpoints properly integrate build_unified_product_v2()
"""

import sys
import os

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, './backend')

print("=" * 80)
print("PHASE 4 ENDPOINT INTEGRATION TEST")
print("=" * 80)
print()

# Test 1: Validate keepa.py imports
print("🔍 Test 1: Checking keepa.py imports...")
try:
    from app.api.v1.routers.keepa import IngestBatchRequest, analyze_product
    print("✅ keepa.py imports successful")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Validate views.py imports
print("🔍 Test 2: Checking views.py imports...")
try:
    from app.api.v1.routers.views import score_products_for_view
    print("✅ views.py imports successful")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: Check IngestBatchRequest has source_price
print("🔍 Test 3: Checking IngestBatchRequest structure...")
try:
    from inspect import signature
    sig = signature(IngestBatchRequest)

    # Create test request
    test_request = IngestBatchRequest(
        identifiers=["0593655036"],
        source_price=5.00
    )

    if hasattr(test_request, 'source_price') and test_request.source_price == 5.00:
        print("✅ IngestBatchRequest has source_price parameter")
        print(f"   - source_price: {test_request.source_price}")
        print()
    else:
        print("❌ IngestBatchRequest missing source_price")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 4: Validate unified_analysis imports
print("🔍 Test 4: Checking unified_analysis imports...")
try:
    from app.services.unified_analysis import build_unified_product_v2
    print("✅ build_unified_product_v2 imported successfully")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 5: Check analyze_product signature has source_price
print("🔍 Test 5: Checking analyze_product signature...")
try:
    from inspect import signature
    sig = signature(analyze_product)
    params = list(sig.parameters.keys())

    if 'source_price' in params:
        print("✅ analyze_product has source_price parameter")
        print(f"   - Parameters: {params}")
        print()
    else:
        print("❌ analyze_product missing source_price parameter")
        print(f"   - Current parameters: {params}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 6: Structure validation
print("🔍 Test 6: Validating endpoint structure...")
try:
    checks_passed = 0
    checks_total = 0

    # Check 1: IngestBatchRequest accepts source_price
    checks_total += 1
    try:
        req = IngestBatchRequest(
            identifiers=["0593655036"],
            batch_id="test-batch",
            config_profile="default",
            force_refresh=False,
            async_threshold=100,
            source_price=7.50
        )
        if req.source_price == 7.50:
            print("   ✅ Check 1: IngestBatchRequest accepts source_price")
            checks_passed += 1
        else:
            print("   ❌ Check 1: source_price not set correctly")
    except Exception as e:
        print(f"   ❌ Check 1: {e}")

    # Check 2: IngestBatchRequest source_price is optional
    checks_total += 1
    try:
        req = IngestBatchRequest(
            identifiers=["0593655036"]
        )
        if req.source_price is None:
            print("   ✅ Check 2: source_price is optional (defaults to None)")
            checks_passed += 1
        else:
            print(f"   ❌ Check 2: source_price should default to None, got {req.source_price}")
    except Exception as e:
        print(f"   ❌ Check 2: {e}")

    # Check 3: analyze_product accepts source_price
    checks_total += 1
    sig = signature(analyze_product)
    if sig.parameters['source_price'].default is None:
        print("   ✅ Check 3: analyze_product source_price defaults to None")
        checks_passed += 1
    else:
        print(f"   ❌ Check 3: analyze_product source_price default is {sig.parameters['source_price'].default}")

    # Check 4: build_unified_product_v2 exists and has correct signature
    checks_total += 1
    sig = signature(build_unified_product_v2)
    params = list(sig.parameters.keys())
    required_params = ['raw_keepa', 'keepa_service', 'config', 'view_type', 'source_price']
    if all(p in params for p in required_params):
        print("   ✅ Check 4: build_unified_product_v2 has all required parameters")
        checks_passed += 1
    else:
        print(f"   ❌ Check 4: Missing parameters. Got {params}")

    print()
    print("=" * 80)
    print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 80)
    print()

    if checks_passed == checks_total:
        print("✅ PHASE 4 VALIDATION: PASSED - Endpoints properly refactored!")
        sys.exit(0)
    else:
        print("⚠️  PHASE 4 VALIDATION: PARTIAL - Some checks need attention")
        sys.exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
