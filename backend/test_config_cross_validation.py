#!/usr/bin/env python3
"""
Test cross-field validation for Config Service.

This script tests that business logic validation works correctly.
"""

import sys
from decimal import Decimal

sys.path.append('/app')
sys.path.append('.')

from app.schemas.config import ROIConfig, VelocityTier, VelocityConfig

print("=" * 60)
print("CONFIG CROSS-FIELD VALIDATION TESTS")
print("=" * 60 + "\n")

# Test 1: ROI validation - target < min (should fail)
print("[TEST 1] ROI target < min_acceptable (should FAIL)...")
try:
    roi = ROIConfig(
        min_acceptable=Decimal("50.0"),
        target=Decimal("30.0"),  # < min_acceptable
        excellent_threshold=Decimal("70.0")
    )
    print("  [FAIL] Validation should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"  [OK] Caught expected error: {e}")

# Test 2: ROI validation - excellent < target (should fail)
print("\n[TEST 2] ROI excellent < target (should FAIL)...")
try:
    roi = ROIConfig(
        min_acceptable=Decimal("15.0"),
        target=Decimal("50.0"),
        excellent_threshold=Decimal("30.0")  # < target
    )
    print("  [FAIL] Validation should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"  [OK] Caught expected error: {e}")

# Test 3: ROI validation - valid ordering (should pass)
print("\n[TEST 3] ROI valid ordering (should PASS)...")
try:
    roi = ROIConfig(
        min_acceptable=Decimal("15.0"),
        target=Decimal("30.0"),
        excellent_threshold=Decimal("50.0")
    )
    print(f"  [OK] Valid ROI config created: {roi.min_acceptable}% < {roi.target}% < {roi.excellent_threshold}%")
except ValueError as e:
    print(f"  [FAIL] Should not have raised error: {e}")
    sys.exit(1)

# Test 4: VelocityTier - max < min (should fail)
print("\n[TEST 4] VelocityTier max_score < min_score (should FAIL)...")
try:
    tier = VelocityTier(
        name="TEST",
        min_score=80,
        max_score=60,  # < min_score
        bsr_threshold=10000
    )
    print("  [FAIL] Validation should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"  [OK] Caught expected error: {e}")

# Test 5: VelocityTier - valid range (should pass)
print("\n[TEST 5] VelocityTier valid range (should PASS)...")
try:
    tier = VelocityTier(
        name="PREMIUM",
        min_score=80,
        max_score=100,
        bsr_threshold=10000
    )
    print(f"  [OK] Valid tier created: {tier.name} (score {tier.min_score}-{tier.max_score})")
except ValueError as e:
    print(f"  [FAIL] Should not have raised error: {e}")
    sys.exit(1)

# Test 6: VelocityConfig - overlapping tiers (should fail)
print("\n[TEST 6] VelocityConfig overlapping tiers (should FAIL)...")
try:
    velocity = VelocityConfig(
        tiers=[
            VelocityTier(name="HIGH", min_score=60, max_score=80, bsr_threshold=50000),
            VelocityTier(name="PREMIUM", min_score=75, max_score=100, bsr_threshold=10000)  # Overlaps with HIGH
        ]
    )
    print("  [FAIL] Validation should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"  [OK] Caught expected error: {e}")

# Test 7: VelocityConfig - valid non-overlapping tiers (should pass)
print("\n[TEST 7] VelocityConfig non-overlapping tiers (should PASS)...")
try:
    velocity = VelocityConfig(
        tiers=[
            VelocityTier(name="PREMIUM", min_score=80, max_score=100, bsr_threshold=10000),
            VelocityTier(name="HIGH", min_score=60, max_score=79, bsr_threshold=50000),
            VelocityTier(name="MEDIUM", min_score=40, max_score=59, bsr_threshold=100000)
        ]
    )
    print(f"  [OK] Valid velocity config with {len(velocity.tiers)} non-overlapping tiers")
except ValueError as e:
    print(f"  [FAIL] Should not have raised error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[SUCCESS] ALL VALIDATION TESTS PASSED")
print("=" * 60)

print("\n[SUMMARY]")
print("  - ROI threshold ordering: OK")
print("  - VelocityTier score ranges: OK")
print("  - VelocityConfig tier overlaps: OK")
print("\n[READY] Validation system is working correctly!")

sys.exit(0)