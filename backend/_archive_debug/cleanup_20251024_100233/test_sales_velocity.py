"""
Tests pour le système Sales Velocity
Test unitaires et d'intégration des nouvelles fonctionnalités
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from app.services.sales_velocity_service import SalesVelocityService
from app.services.keepa_service import KeepaService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_velocity_classification():
    """Test de la classification des tiers de vélocité"""
    print("🧪 Testing velocity tier classification...")
    
    service = SalesVelocityService()
    
    # Test cases
    test_cases = [
        (150, 'PREMIUM'),
        (75, 'HIGH'), 
        (35, 'MEDIUM'),
        (12, 'LOW'),
        (2, 'DEAD'),
        (0, 'DEAD')
    ]
    
    all_passed = True
    for monthly_sales, expected_tier in test_cases:
        result = service.classify_velocity_tier(monthly_sales)
        if result == expected_tier:
            print(f"✅ {monthly_sales} sales/month → {result} (expected {expected_tier})")
        else:
            print(f"❌ {monthly_sales} sales/month → {result} (expected {expected_tier})")
            all_passed = False
    
    return all_passed


def test_opportunity_score():
    """Test du calcul du score d'opportunité"""
    print("\n🧪 Testing opportunity score calculation...")
    
    service = SalesVelocityService()
    
    # Test cases: (ROI%, Profit$, Sales/month, Expected Range)
    test_cases = [
        (40, 12, 100, (45, 55)),  # ROI 40%, Sales 100/month, Profit $12 = ~48
        (80, 25, 25, (95, 105)),  # High ROI, lower velocity
        (30, 8, 200, (33, 37)),   # Lower ROI, high velocity - adjusted expectation
        (0, 10, 50, (0, 0)),      # Zero ROI should be 0
        (50, 0, 100, (0, 0))      # Zero profit should be 0
    ]
    
    all_passed = True
    for roi, profit, sales, expected_range in test_cases:
        score = service.calculate_opportunity_score(roi, profit, sales)
        min_expected, max_expected = expected_range
        
        if min_expected <= score <= max_expected:
            print(f"✅ ROI {roi}%, Profit ${profit}, Sales {sales}/month → Score {score} ✓")
        else:
            print(f"❌ ROI {roi}%, Profit ${profit}, Sales {sales}/month → Score {score} (expected {min_expected}-{max_expected})")
            all_passed = False
    
    return all_passed


def test_monthly_sales_estimation():
    """Test des estimations de ventes mensuelles"""
    print("\n🧪 Testing monthly sales estimation...")
    
    service = SalesVelocityService()
    
    # Test cases: (sales_drops_30, BSR, category, expected_min, expected_max)
    test_cases = [
        (50, 5000, 'Books', 70, 90),      # Best-seller with good drops
        (20, 100000, 'Books', 15, 25),   # Average product
        (10, 800000, 'Books', 5, 10),    # Long-tail product
        (0, 1000000, 'Books', 0, 1),     # Dead product
        (30, 50000, 'Electronics', 30, 40)  # Electronics multiplier
    ]
    
    all_passed = True
    for drops, bsr, category, min_expected, max_expected in test_cases:
        result = service.estimate_monthly_sales(drops, bsr, category)
        
        if min_expected <= result <= max_expected:
            print(f"✅ Drops {drops}, BSR {bsr}, {category} → {result} sales/month ✓")
        else:
            print(f"❌ Drops {drops}, BSR {bsr}, {category} → {result} sales/month (expected {min_expected}-{max_expected})")
            all_passed = False
    
    return all_passed


def test_tier_descriptions():
    """Test des descriptions des tiers"""
    print("\n🧪 Testing tier descriptions...")
    
    service = SalesVelocityService()
    
    tiers = ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'DEAD']
    all_passed = True
    
    for tier in tiers:
        description = service.get_tier_description(tier)
        required_keys = ['label', 'description', 'strategy', 'icon']
        
        if all(key in description for key in required_keys):
            print(f"✅ {tier} tier description complete: {description['label']}")
        else:
            print(f"❌ {tier} tier description missing keys")
            all_passed = False
    
    return all_passed


async def test_keepa_velocity_integration():
    """Test de l'intégration avec KeepaService"""
    print("\n🧪 Testing Keepa velocity integration...")
    
    try:
        # Get API key from Memex secrets
        import subprocess
        try:
            result = subprocess.run(
                ["uv", "run", "keyring", "get", "memex", "KEEPA_API_KEY"],
                capture_output=True,
                text=True,
                cwd="."
            )
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                print(f"✅ Keepa API key retrieved from Memex secrets")
            else:
                print(f"❌ Failed to get Keepa API key from secrets")
                return False
        except Exception as e:
            print(f"❌ Error accessing Memex secrets: {e}")
            return False
        
        # Initialiser les services avec la clé API
        keepa_service = KeepaService(api_key=api_key)
        velocity_service = SalesVelocityService()
        
        # Test avec un ASIN connu
        test_asin = "1292025824"  # ASIN que nous avons testé avant
        
        print(f"Getting velocity data for {test_asin}...")
        velocity_data = await keepa_service.get_sales_velocity_data(test_asin)
        
        if velocity_data and velocity_data.get('asin') == test_asin:
            print(f"✅ Keepa velocity data retrieved for {test_asin}")
            print(f"   Sales drops 30d: {velocity_data.get('sales_drops_30', 'N/A')}")
            print(f"   Current BSR: {velocity_data.get('current_bsr', 'N/A')}")
            print(f"   Category: {velocity_data.get('category', 'N/A')}")
            
            # Test analyse complète
            analysis = velocity_service.analyze_product_velocity(velocity_data, 45.0, 12.5)
            print(f"   Monthly sales estimate: {analysis.get('sales_estimate_30d', 'N/A')}")
            print(f"   Velocity tier: {analysis.get('velocity_tier', 'N/A')}")
            print(f"   Opportunity score: {analysis.get('opportunity_score', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed to get velocity data for {test_asin}")
            return False
            
    except Exception as e:
        print(f"❌ Keepa velocity integration test failed: {e}")
        return False


def run_all_tests():
    """Exécuter tous les tests"""
    print("🚀 Starting Sales Velocity System Tests")
    print("=" * 50)
    
    tests = [
        ("Velocity Classification", test_velocity_classification),
        ("Opportunity Score", test_opportunity_score), 
        ("Monthly Sales Estimation", test_monthly_sales_estimation),
        ("Tier Descriptions", test_tier_descriptions)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Test async Keepa integration
    print("\n" + "=" * 50)
    try:
        keepa_result = asyncio.run(test_keepa_velocity_integration())
        results.append(("Keepa Integration", keepa_result))
    except Exception as e:
        print(f"❌ Keepa integration test crashed: {e}")
        results.append(("Keepa Integration", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Sales Velocity System ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Review implementation before deployment.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)