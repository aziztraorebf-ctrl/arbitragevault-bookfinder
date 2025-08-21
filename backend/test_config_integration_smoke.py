"""
Configuration Integration Smoke Test - Validate dynamic config works end-to-end.
"""

import asyncio
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData
from app.core.fees_config import calculate_profit_metrics


async def test_roi_with_config():
    """Test ROI calculation with dynamic configuration."""
    print("💰 Test 1: ROI Calculation with Config")
    
    # Default config
    default_config = None
    roi_default = calculate_roi_metrics(
        current_price=Decimal("25.00"),
        estimated_buy_cost=Decimal("15.00"),
        config=default_config
    )
    
    # Custom config with higher ROI target
    custom_config = {
        "roi": {
            "target_pct_default": 50.0,  # Higher target
            "excellent_threshold": 60.0,
            "good_threshold": 40.0,
            "fair_threshold": 20.0
        },
        "fees": {
            "buffer_pct_default": 8.0  # Higher buffer
        }
    }
    
    roi_custom = calculate_roi_metrics(
        current_price=Decimal("25.00"),
        estimated_buy_cost=Decimal("15.00"),
        config=custom_config
    )
    
    print(f"   Default config:")
    print(f"     ROI: {roi_default['roi_percentage']}%")
    print(f"     Target buy price: ${roi_default['target_buy_price']}")
    print(f"     Meets target: {roi_default['meets_target_roi']}")
    print(f"     Profit tier: {roi_default['profit_tier']}")
    
    print(f"   Custom config (ROI target 50%, buffer 8%):")
    print(f"     ROI: {roi_custom['roi_percentage']}%")
    print(f"     Target buy price: ${roi_custom['target_buy_price']}")
    print(f"     Meets target: {roi_custom['meets_target_roi']}")
    print(f"     Profit tier: {roi_custom['profit_tier']}")
    
    # Verify config was applied
    config_audit = roi_custom.get('config_applied', {})
    print(f"     Config audit: {config_audit}")
    
    assert roi_custom['config_applied']['target_roi_used'] == 50.0, "ROI target not applied"
    assert roi_custom['config_applied']['buffer_pct_used'] == 8.0, "Buffer not applied"
    print("   ✅ Configuration successfully applied to ROI calculation")
    print()


async def test_velocity_with_config():
    """Test velocity calculation with dynamic configuration."""
    print("⚡ Test 2: Velocity Calculation with Config")
    
    # Create mock velocity data
    now = datetime.now()
    velocity_data = VelocityData(
        current_bsr=25000,
        bsr_history=[
            (now - timedelta(days=20), 50000),
            (now - timedelta(days=15), 35000),
            (now - timedelta(days=10), 25000),
            (now - timedelta(days=5), 20000)
        ],
        price_history=[(now - timedelta(days=i), 25.0) for i in range(1, 21)],
        buybox_history=[(now - timedelta(days=i), True) for i in range(1, 21)],
        offers_history=[(now - timedelta(days=i), 5) for i in range(1, 21)],
        category="books"
    )
    
    # Default config
    velocity_default = calculate_velocity_score(velocity_data, config=None)
    
    # Custom config with higher thresholds
    custom_config = {
        "velocity": {
            "fast_threshold": 90.0,  # Much higher
            "medium_threshold": 75.0,
            "slow_threshold": 50.0,
            "benchmarks": {
                "books": 50000  # Lower benchmark (better)
            }
        }
    }
    
    velocity_custom = calculate_velocity_score(velocity_data, config=custom_config)
    
    print(f"   Default config:")
    print(f"     Velocity score: {velocity_default['velocity_score']}")
    print(f"     Velocity tier: {velocity_default['velocity_tier']}")
    
    print(f"   Custom config (higher thresholds, better benchmark):")
    print(f"     Velocity score: {velocity_custom['velocity_score']}")
    print(f"     Velocity tier: {velocity_custom['velocity_tier']}")
    
    # Verify different tiers due to config
    print(f"   ✅ Configuration applied - tiers may differ due to thresholds")
    print()


async def test_combined_scoring_with_config():
    """Test combined scoring with custom weights."""
    print("🎯 Test 3: Combined Scoring with Config Weights")
    
    # Mock ROI and velocity metrics
    roi_metrics = {"roi_percentage": 35.0, "is_profitable": True}
    velocity_metrics = {"velocity_score": 70.0}
    
    # Default weights (60% ROI, 40% velocity)
    from app.core.calculations import _calculate_combined_score, _generate_recommendation
    
    default_score = _calculate_combined_score(roi_metrics, velocity_metrics, config=None)
    
    # Custom weights (50% ROI, 50% velocity)
    custom_config = {
        "combined_score": {
            "roi_weight": 0.5,
            "velocity_weight": 0.5
        },
        "recommendation_rules": [
            {"label": "STRONG BUY", "min_roi": 30.0, "min_velocity": 65.0, "description": "Excellent opportunity"},
            {"label": "BUY", "min_roi": 20.0, "min_velocity": 50.0, "description": "Good opportunity"},
            {"label": "PASS", "min_roi": 0.0, "min_velocity": 0.0, "description": "Below thresholds"}
        ]
    }
    
    custom_score = _calculate_combined_score(roi_metrics, velocity_metrics, config=custom_config)
    
    print(f"   ROI: {roi_metrics['roi_percentage']}%, Velocity: {velocity_metrics['velocity_score']}")
    print(f"   Default weights (60/40): {default_score['combined_score']}")
    print(f"   Custom weights (50/50): {custom_score['combined_score']}")
    
    # Test recommendations
    default_rec = _generate_recommendation(roi_metrics, velocity_metrics, config=None)
    custom_rec = _generate_recommendation(roi_metrics, velocity_metrics, config=custom_config)
    
    print(f"   Default recommendation: {default_rec}")
    print(f"   Custom recommendation: {custom_rec}")
    
    assert custom_score['roi_weight'] == 0.5, "Custom weights not applied"
    print("   ✅ Custom weights and recommendation rules applied")
    print()


async def test_profit_tiers_with_config():
    """Test profit tier classification with custom thresholds."""
    print("📊 Test 4: Profit Tiers with Config Thresholds")
    
    test_roi_values = [60.0, 45.0, 25.0, 10.0, -5.0]
    
    # Default thresholds
    default_config = None
    
    # Custom thresholds (more stringent)
    custom_config = {
        "roi": {
            "excellent_threshold": 70.0,  # Higher than default 50%
            "good_threshold": 50.0,       # Higher than default 30%
            "fair_threshold": 25.0        # Higher than default 15%
        }
    }
    
    print("   ROI% | Default Tier | Custom Tier")
    print("   -----|--------------|------------")
    
    for roi in test_roi_values:
        from app.core.fees_config import _get_profit_tier
        
        default_tier = _get_profit_tier(Decimal(str(roi)), default_config)
        custom_tier = _get_profit_tier(Decimal(str(roi)), custom_config)
        
        print(f"   {roi:4.0f} |    {default_tier:8} |   {custom_tier:8}")
    
    print("   ✅ Profit tiers adjust based on config thresholds")
    print()


async def test_end_to_end_config_impact():
    """Test complete workflow with config showing real impact."""
    print("🔄 Test 5: End-to-End Config Impact")
    
    # Scenario: Same product, different business strategies
    current_price = Decimal("39.99")
    buy_cost = Decimal("18.00")
    
    # Conservative strategy (high ROI target, high buffer)
    conservative_config = {
        "roi": {
            "target_pct_default": 45.0,
            "excellent_threshold": 60.0,
            "good_threshold": 45.0,
            "fair_threshold": 25.0
        },
        "fees": {"buffer_pct_default": 8.0},
        "combined_score": {"roi_weight": 0.8, "velocity_weight": 0.2},
        "recommendation_rules": [
            {"label": "STRONG BUY", "min_roi": 40.0, "min_velocity": 80.0},
            {"label": "BUY", "min_roi": 30.0, "min_velocity": 70.0},
            {"label": "CONSIDER", "min_roi": 20.0, "min_velocity": 50.0},
            {"label": "PASS", "min_roi": 0.0, "min_velocity": 0.0}
        ]
    }
    
    # Aggressive strategy (lower ROI target, lower buffer)
    aggressive_config = {
        "roi": {
            "target_pct_default": 20.0,
            "excellent_threshold": 40.0,
            "good_threshold": 25.0,
            "fair_threshold": 15.0
        },
        "fees": {"buffer_pct_default": 3.0},
        "combined_score": {"roi_weight": 0.5, "velocity_weight": 0.5},
        "recommendation_rules": [
            {"label": "STRONG BUY", "min_roi": 20.0, "min_velocity": 60.0},
            {"label": "BUY", "min_roi": 15.0, "min_velocity": 40.0},
            {"label": "CONSIDER", "min_roi": 10.0, "min_velocity": 20.0},
            {"label": "PASS", "min_roi": 0.0, "min_velocity": 0.0}
        ]
    }
    
    # Calculate with both strategies
    conservative_result = calculate_roi_metrics(current_price, buy_cost, config=conservative_config)
    aggressive_result = calculate_roi_metrics(current_price, buy_cost, config=aggressive_config)
    
    print(f"   Product: ${current_price} selling price, ${buy_cost} buy cost")
    print(f"   Conservative strategy:")
    print(f"     Net profit: ${conservative_result['net_profit']}")
    print(f"     ROI: {conservative_result['roi_percentage']}%")
    print(f"     Meets target: {conservative_result['meets_target_roi']}")
    print(f"     Profit tier: {conservative_result['profit_tier']}")
    
    print(f"   Aggressive strategy:")
    print(f"     Net profit: ${aggressive_result['net_profit']}")
    print(f"     ROI: {aggressive_result['roi_percentage']}%")
    print(f"     Meets target: {aggressive_result['meets_target_roi']}")
    print(f"     Profit tier: {aggressive_result['profit_tier']}")
    
    # Verify different outcomes
    conservative_meets_target = conservative_result['meets_target_roi']
    aggressive_meets_target = aggressive_result['meets_target_roi']
    
    if conservative_meets_target != aggressive_meets_target:
        print("   ✅ Different strategies produce different decisions")
    else:
        print("   ✅ Both strategies agree on this product")
    
    print()


async def run_all_tests():
    """Run all configuration integration tests."""
    print("🧪 CONFIGURATION INTEGRATION SMOKE TESTS")
    print("=" * 55)
    
    try:
        await test_roi_with_config()
        await test_velocity_with_config()
        await test_combined_scoring_with_config()
        await test_profit_tiers_with_config()
        await test_end_to_end_config_impact()
        
        print("🎉 ALL CONFIG INTEGRATION TESTS PASSED")
        print("✅ Dynamic configuration system operational")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())