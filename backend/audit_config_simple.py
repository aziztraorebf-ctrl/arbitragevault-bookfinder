#!/usr/bin/env python
"""
Audit SIMPLIFIÉ du Config Service - Sans DB
Focus sur : Schemas, Validation, Keepa Integration
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.config import (
    FeeConfig, ROIConfig, VelocityConfig, VelocityTier,
    DataQualityThresholds, ProductFinderConfig,
    CategoryConfig, ConfigCreate
)


def test_schemas():
    """Test schemas Pydantic v2."""
    print("\n[TEST 1] SCHEMAS PYDANTIC V2")
    print("-" * 40)

    results = {}

    # Test FeeConfig
    try:
        fee = FeeConfig()
        results["FeeConfig"] = "OK"
        print(f"  [OK] FeeConfig - defaults working")
    except Exception as e:
        results["FeeConfig"] = f"FAIL: {e}"
        print(f"  [FAIL] FeeConfig: {e}")

    # Test ROIConfig
    try:
        roi = ROIConfig()
        results["ROIConfig"] = "OK"
        print(f"  [OK] ROIConfig - defaults working")
    except Exception as e:
        results["ROIConfig"] = f"FAIL: {e}"
        print(f"  [FAIL] ROIConfig: {e}")

    # Test VelocityConfig
    try:
        velocity = VelocityConfig(
            tiers=[
                VelocityTier(name="HIGH", min_score=60, max_score=79, bsr_threshold=50000),
                VelocityTier(name="PREMIUM", min_score=80, max_score=100, bsr_threshold=10000)
            ]
        )
        results["VelocityConfig"] = "OK"
        print(f"  [OK] VelocityConfig - non-overlapping tiers")
    except Exception as e:
        results["VelocityConfig"] = f"FAIL: {e}"
        print(f"  [FAIL] VelocityConfig: {e}")

    return results


def test_validation():
    """Test cross-field validation."""
    print("\n[TEST 2] VALIDATION CROSS-FIELD")
    print("-" * 40)

    results = {}

    # Test 1: ROI invalid order (should fail)
    try:
        roi = ROIConfig(
            min_acceptable=Decimal("50"),
            target=Decimal("30"),  # Invalid: < min_acceptable
            excellent_threshold=Decimal("70")
        )
        results["ROI_invalid"] = "FAIL - Should have rejected"
        print(f"  [FAIL] ROI validation - accepted invalid order")
    except ValueError:
        results["ROI_invalid"] = "OK"
        print(f"  [OK] ROI validation - correctly rejected invalid order")

    # Test 2: VelocityTier invalid range (should fail)
    try:
        tier = VelocityTier(
            name="INVALID",
            min_score=80,
            max_score=60,  # Invalid: < min_score
            bsr_threshold=10000
        )
        results["VelocityTier_invalid"] = "FAIL - Should have rejected"
        print(f"  [FAIL] VelocityTier - accepted invalid range")
    except ValueError:
        results["VelocityTier_invalid"] = "OK"
        print(f"  [OK] VelocityTier - correctly rejected invalid range")

    # Test 3: VelocityConfig overlapping (should fail)
    try:
        velocity = VelocityConfig(
            tiers=[
                VelocityTier(name="HIGH", min_score=60, max_score=80, bsr_threshold=50000),
                VelocityTier(name="PREMIUM", min_score=75, max_score=100, bsr_threshold=10000)
                # Overlap: 75-80 in both
            ]
        )
        results["Velocity_overlap"] = "FAIL - Should have rejected"
        print(f"  [FAIL] VelocityConfig - accepted overlapping tiers")
    except ValueError:
        results["Velocity_overlap"] = "OK"
        print(f"  [OK] VelocityConfig - correctly rejected overlapping tiers")

    return results


def test_keepa_integration():
    """Test Keepa data compatibility."""
    print("\n[TEST 3] KEEPA INTEGRATION")
    print("-" * 40)

    results = {}

    # Simulate Keepa product data
    keepa_product = {
        "asin": "0593655036",
        "title": "Fourth Wing",
        "stats": {
            "current": [1599, None, None, 42000]  # Buy Box cents, _, _, BSR
        }
    }

    try:
        # Extract price
        buy_box_cents = keepa_product["stats"]["current"][0]
        buy_box_price = Decimal(str(buy_box_cents / 100))

        # Create config
        config = ConfigCreate(
            name="Test Config",
            fees=FeeConfig(),
            roi=ROIConfig(),
            velocity=VelocityConfig(
                tiers=[
                    VelocityTier(name="PREMIUM", min_score=80, max_score=100, bsr_threshold=10000),
                    VelocityTier(name="HIGH", min_score=60, max_score=79, bsr_threshold=50000),
                    VelocityTier(name="MEDIUM", min_score=40, max_score=59, bsr_threshold=100000)
                ]
            ),
            data_quality=DataQualityThresholds(),
            product_finder=ProductFinderConfig()
        )

        # Calculate ROI
        source_price = buy_box_price * config.roi.source_price_factor

        # Calculate fees
        referral_fee = buy_box_price * (config.fees.referral_fee_percent / Decimal("100"))
        fba_fee = config.fees.fba_base_fee + config.fees.fba_per_pound
        total_fees = (
            referral_fee +
            fba_fee +
            config.fees.closing_fee +
            config.fees.prep_fee +
            config.fees.shipping_cost
        )

        profit = buy_box_price - source_price - total_fees
        roi_percent = (profit / source_price) * Decimal("100")

        results["price_extraction"] = "OK"
        print(f"  [OK] Price extraction: ${buy_box_price}")

        results["roi_calculation"] = "OK"
        print(f"  [OK] ROI calculation: {roi_percent:.1f}%")

        # Test velocity assignment
        bsr = keepa_product["stats"]["current"][3]
        velocity_tier = None
        for tier in config.velocity.tiers:
            if bsr <= tier.bsr_threshold:
                velocity_tier = tier.name
                break

        results["velocity_assignment"] = "OK" if velocity_tier else "FAIL"
        print(f"  [OK] Velocity tier: {velocity_tier} (BSR: {bsr})")

        # Test Books override
        books_override = CategoryConfig(
            category_id=283155,
            category_name="Books",
            fees=FeeConfig(
                fba_base_fee=Decimal("2.50"),  # vs 3.00 default
                fba_per_pound=Decimal("0.35"),  # vs 0.40 default
                prep_fee=Decimal("0.15"),       # vs 0.20 default
                shipping_cost=Decimal("0.35")   # vs 0.40 default
            )
        )

        # Recalculate with Books fees
        books_fees = books_override.fees
        books_total = (
            referral_fee +  # Same referral
            books_fees.fba_base_fee + books_fees.fba_per_pound +
            books_fees.closing_fee +
            books_fees.prep_fee +
            books_fees.shipping_cost
        )

        savings = float(total_fees - books_total)
        results["books_override"] = "OK"
        print(f"  [OK] Books override savings: ${savings:.2f}/unit")

    except Exception as e:
        results["keepa_integration"] = f"FAIL: {e}"
        print(f"  [FAIL] Keepa integration: {e}")

    return results


def test_json_serialization():
    """Test JSON serialization avec Decimals."""
    print("\n[TEST 4] JSON SERIALIZATION")
    print("-" * 40)

    try:
        config = ConfigCreate(
            name="JSON Test",
            fees=FeeConfig(),
            roi=ROIConfig(),
            velocity=VelocityConfig(
                tiers=[
                    VelocityTier(name="TEST", min_score=0, max_score=100, bsr_threshold=1000000)
                ]
            ),
            data_quality=DataQualityThresholds(),
            product_finder=ProductFinderConfig()
        )

        # Use Pydantic's JSON serialization which handles Decimals
        json_data = config.model_dump_json(indent=2)

        print(f"  [OK] JSON serialization successful")
        print(f"  [INFO] JSON size: {len(json_data)} bytes")
        return {"json_serialization": "OK", "size": len(json_data)}

    except Exception as e:
        print(f"  [FAIL] JSON serialization: {e}")
        return {"json_serialization": f"FAIL: {e}"}


def main():
    """Execute simplified audit."""
    print("\n" + "="*60)
    print("    AUDIT SIMPLIFIE CONFIG SERVICE - PHASE 2 JOUR 4")
    print("="*60)

    all_results = {}

    # Run tests
    all_results["schemas"] = test_schemas()
    all_results["validation"] = test_validation()
    all_results["keepa"] = test_keepa_integration()
    all_results["json"] = test_json_serialization()

    # Summary
    print("\n" + "="*60)
    print("RESUME FINAL")
    print("="*60)

    total_tests = 0
    passed_tests = 0

    for category, tests in all_results.items():
        for test_name, result in tests.items():
            # Skip 'size' as it's not a test
            if test_name == "size":
                continue
            total_tests += 1
            if result == "OK" or (isinstance(result, str) and result.startswith("OK")):
                passed_tests += 1

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTests reussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

    if success_rate == 100:
        print("\n[SUCCESS] TOUS LES TESTS CRITIQUES PASSES")
    elif success_rate >= 80:
        print(f"\n[WARNING] {100-success_rate:.1f}% des tests echoues")
    else:
        print(f"\n[FAILURE] {100-success_rate:.1f}% des tests echoues")

    # Save report
    report = {
        "results": all_results,
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "success_rate": success_rate
        }
    }

    report_path = Path(__file__).parent / "audit_simple_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nRapport sauve: {report_path}")

    return success_rate == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)