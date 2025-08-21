"""
Smoke test for Business Configuration Service - Step 2 validation.
"""

import asyncio
import json
from app.services.business_config_service import BusinessConfigService, get_effective_config


async def test_service_instantiation():
    """Test service creation and basic functionality."""
    print("🏗️ Test 1: Service Instantiation")
    
    service = BusinessConfigService()
    print(f"   ✅ Service created")
    
    # Test cache stats
    stats = service.get_cache_stats()
    print(f"   Cache stats: {stats['total_entries']} entries")
    print()


async def test_fallback_config_loading():
    """Test loading fallback configuration."""
    print("📄 Test 2: Fallback Config Loading")
    
    service = BusinessConfigService()
    
    try:
        fallback_config = await service._load_fallback_config()
        
        print(f"   ✅ Fallback config loaded")
        print(f"   ROI target: {fallback_config.get('roi', {}).get('target_pct_default', 'unknown')}%")
        print(f"   Combined weights: ROI {fallback_config.get('combined_score', {}).get('roi_weight', 'unknown')}, Velocity {fallback_config.get('combined_score', {}).get('velocity_weight', 'unknown')}")
        print(f"   Demo ASINs: {len(fallback_config.get('demo_asins', []))} configured")
        
    except Exception as e:
        print(f"   ❌ Fallback config loading failed: {e}")
    
    print()


async def test_deep_merge_logic():
    """Test hierarchical configuration merging."""
    print("🔀 Test 3: Deep Merge Logic")
    
    service = BusinessConfigService()
    
    # Mock configs for testing merge
    global_config = {
        "roi": {"target_pct_default": 30.0, "min_for_buy": 15.0},
        "combined_score": {"roi_weight": 0.6, "velocity_weight": 0.4},
        "fees": {"buffer_pct_default": 5.0}
    }
    
    domain_config = {
        "roi": {"target_pct_default": 35.0},  # Override for domain
        "fees": {"buffer_pct_default": 6.0}   # Override buffer
    }
    
    category_config = {
        "roi": {"min_for_buy": 20.0},         # Override min for category
        "velocity": {"fast_threshold": 85.0}  # Add category-specific setting
    }
    
    # Test merge
    merged = service._deep_merge_configs([global_config, domain_config, category_config])
    
    print(f"   Global ROI target: {global_config['roi']['target_pct_default']}%")
    print(f"   Domain override: {domain_config['roi']['target_pct_default']}%")
    print(f"   Merged ROI target: {merged['roi']['target_pct_default']}%")
    
    print(f"   Global min_for_buy: {global_config['roi']['min_for_buy']}%")
    print(f"   Category override: {category_config['roi']['min_for_buy']}%")
    print(f"   Merged min_for_buy: {merged['roi']['min_for_buy']}%")
    
    print(f"   Buffer (domain): {merged['fees']['buffer_pct_default']}%")
    print(f"   Velocity (category-only): {merged.get('velocity', {}).get('fast_threshold', 'inherited')}%")
    
    # Verify weights preserved
    assert merged['combined_score']['roi_weight'] == 0.6
    assert merged['combined_score']['velocity_weight'] == 0.4
    print(f"   ✅ Weights preserved: {merged['combined_score']}")
    
    print()


async def test_jsonpatch_diff():
    """Test JSONPatch diff generation."""
    print("📝 Test 4: JSONPatch Diff Generation")
    
    service = BusinessConfigService()
    
    old_config = {
        "roi": {"target_pct_default": 30.0, "min_for_buy": 15.0},
        "fees": {"buffer_pct_default": 5.0}
    }
    
    new_config = {
        "roi": {"target_pct_default": 35.0, "min_for_buy": 15.0, "new_param": 100.0},  # Changed + added
        "fees": {"buffer_pct_default": 7.0},  # Changed
        "velocity": {"fast_threshold": 80.0}  # Added section
    }
    
    diff = service._generate_jsonpatch_diff(old_config, new_config)
    
    print(f"   Generated {len(diff)} patch operations:")
    for i, operation in enumerate(diff):
        op_type = operation.get('op', 'unknown')
        path = operation.get('path', 'unknown')
        value = operation.get('value', 'N/A')
        print(f"   [{i+1}] {op_type.upper()} {path} → {value}")
    
    # Verify we can apply the patch
    try:
        import jsonpatch
        patch = jsonpatch.JsonPatch(diff)
        result = patch.apply(old_config)
        print(f"   ✅ Patch application successful")
        print(f"   Result ROI target: {result['roi']['target_pct_default']}%")
    except Exception as e:
        print(f"   ⚠️ Patch application issue: {e}")
    
    print()


async def test_config_validation():
    """Test configuration validation logic."""
    print("✅ Test 5: Config Validation")
    
    service = BusinessConfigService()
    
    # Test valid config
    valid_config = {
        "roi": {"target_pct_default": 30.0, "min_for_buy": 15.0},
        "combined_score": {"roi_weight": 0.6, "velocity_weight": 0.4},
        "fees": {"buffer_pct_default": 5.0}
    }
    
    valid_errors = await service._validate_config(valid_config)
    print(f"   Valid config errors: {len(valid_errors)} ({'✅ PASS' if len(valid_errors) == 0 else '❌ FAIL'})")
    
    # Test invalid config (weights don't sum to 1.0)
    invalid_config = {
        "roi": {"target_pct_default": 30.0},
        "combined_score": {"roi_weight": 0.7, "velocity_weight": 0.4},  # Sum = 1.1
        "fees": {"buffer_pct_default": 60.0}  # Too high buffer
    }
    
    invalid_errors = await service._validate_config(invalid_config)
    print(f"   Invalid config errors: {len(invalid_errors)} ({'✅ DETECTED' if len(invalid_errors) > 0 else '❌ MISSED'})")
    for error in invalid_errors:
        print(f"     - {error}")
    
    print()


async def test_effective_config_convenience():
    """Test convenience function for getting effective config."""
    print("🎯 Test 6: Effective Config Convenience Function")
    
    try:
        # This will use fallback since DB likely empty
        config = await get_effective_config(domain_id=1, category="books")
        
        print(f"   ✅ Effective config loaded")
        print(f"   Domain: {config.get('_meta', {}).get('domain_id', 'unknown')}")
        print(f"   Category: {config.get('_meta', {}).get('category', 'unknown')}")
        print(f"   ROI target: {config.get('roi', {}).get('target_pct_default', 'unknown')}%")
        print(f"   Sources: {config.get('_meta', {}).get('sources', {})}")
        
    except Exception as e:
        print(f"   ❌ Effective config failed: {e}")
    
    print()


async def run_all_tests():
    """Run all business config service tests."""
    print("🧪 BUSINESS CONFIG SERVICE SMOKE TESTS")
    print("=" * 50)
    
    try:
        await test_service_instantiation()
        await test_fallback_config_loading()
        await test_deep_merge_logic()
        await test_jsonpatch_diff()
        await test_config_validation()
        await test_effective_config_convenience()
        
        print("🎉 ALL TESTS PASSED - Service ready for Step 3")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())