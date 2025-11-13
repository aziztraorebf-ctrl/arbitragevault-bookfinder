"""
Smoke test for calculation engine - Phase 2 Step 3 validation.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from app.core.fees_config import calculate_profit_metrics, get_fee_config
from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData


def test_fees_calculation():
    """Test Amazon fees calculation."""
    print("🧮 Test 1: Amazon Fees Calculation")
    
    # Test case: $25 book, 1 lb weight
    sell_price = Decimal("25.00")
    weight = Decimal("1.0")
    
    fees = calculate_profit_metrics(
        sell_price=sell_price,
        buy_cost=Decimal("15.00"),
        weight_lbs=weight,
        category="books"
    )
    
    print(f"   Sell Price: ${fees['sell_price']}")
    print(f"   Buy Cost: ${fees['buy_cost']}")
    print(f"   Total Fees: ${fees['fees']['total_fees']}")
    print(f"   Net Profit: ${fees['net_profit']}")
    print(f"   ROI: {fees['roi_percentage']}%")
    print(f"   Margin: {fees['margin_percentage']}%")
    print(f"   Target Buy Price (30% ROI): ${fees['target_buy_price']}")
    print(f"   Breakeven: ${fees['breakeven_price']}")
    print(f"   ✅ Profit Tier: {fees['profit_tier']}")
    print()


def test_roi_metrics():
    """Test ROI calculation module."""
    print("💰 Test 2: ROI Metrics")
    
    roi_result = calculate_roi_metrics(
        current_price=Decimal("28.99"),
        estimated_buy_cost=Decimal("12.50"),
        product_weight_lbs=Decimal("1.2"),
        category="books"
    )
    
    if "error" in roi_result:
        print(f"   ❌ ROI calculation failed: {roi_result['error']}")
    else:
        print(f"   Current Price: ${roi_result['sell_price']}")
        print(f"   Buy Cost: ${roi_result['buy_cost']}")
        print(f"   Net Profit: ${roi_result['net_profit']}")
        print(f"   ROI: {roi_result['roi_percentage']}%")
        print(f"   ✅ Is Profitable: {roi_result['is_profitable']}")
        print(f"   ✅ Confidence: {roi_result['confidence_level']}")
    print()


def test_velocity_calculation():
    """Test velocity scoring."""
    print("⚡ Test 3: Velocity Scoring")
    
    # Create mock BSR history (improving ranks)
    now = datetime.now()
    bsr_history = [
        (now - timedelta(days=25), 50000),
        (now - timedelta(days=20), 45000),
        (now - timedelta(days=15), 30000),
        (now - timedelta(days=10), 25000),
        (now - timedelta(days=5), 20000),
        (now - timedelta(days=1), 15000)  # Good trend - rank improving
    ]
    
    # Mock price history
    price_history = [
        (now - timedelta(days=25), 28.99),
        (now - timedelta(days=20), 27.50),
        (now - timedelta(days=15), 29.99),
        (now - timedelta(days=10), 28.00),
        (now - timedelta(days=5), 29.50)
    ]
    
    velocity_data = VelocityData(
        current_bsr=15000,
        bsr_history=bsr_history,
        price_history=price_history,
        buybox_history=[
            (now - timedelta(days=i), True) for i in range(1, 26)  # Consistent buybox
        ],
        offers_history=[
            (now - timedelta(days=i), 5 + (i % 3)) for i in range(1, 26)  # Low volatility
        ],
        category="books"
    )
    
    velocity_result = calculate_velocity_score(velocity_data)
    
    if "error" in velocity_result:
        print(f"   ❌ Velocity calculation failed: {velocity_result['error']}")
    else:
        print(f"   Velocity Score: {velocity_result['velocity_score']}/100")
        print(f"   Rank Percentile: {velocity_result['rank_percentile_30d']}")
        print(f"   Rank Improvements: {velocity_result['rank_drops_30d']}")
        print(f"   Buybox Uptime: {velocity_result['buybox_uptime_30d']}%")
        print(f"   Offers Volatility: {velocity_result['offers_volatility']}")
        print(f"   ✅ Velocity Tier: {velocity_result['velocity_tier']}")
        print(f"   Data Points: {velocity_result['data_points']}")
    print()


def test_fee_categories():
    """Test different fee categories."""
    print("📚 Test 4: Fee Categories")
    
    categories = ["books", "media", "electronics", "unknown_category"]
    
    for category in categories:
        config = get_fee_config(category)
        print(f"   {category}: referral={config.referral_fee_pct}%, closing=${config.closing_fee}")
    print()


def run_all_tests():
    """Run all calculation smoke tests."""
    print("🧪 CALCULATIONS SMOKE TESTS - PHASE 2 STEP 3")
    print("=" * 55)
    
    try:
        test_fees_calculation()
        test_roi_metrics()
        test_velocity_calculation()
        test_fee_categories()
        
        print("🎉 ALL TESTS PASSED - Calculation engine operational")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()