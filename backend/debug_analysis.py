"""
Debug script to analyze the root cause of calculation and parser errors.
"""

import traceback
import sys
sys.path.insert(0, '.')

def test_parser_with_minimal_data():
    """Test parser with minimal Keepa data to reproduce null errors."""
    print("🔍 TESTING PARSER WITH MINIMAL DATA")
    
    try:
        from app.services.keepa_parser import parse_keepa_product
        
        # Test case 1: Very minimal data
        test_data_minimal = {
            'asin': 'B00FLIJJSA', 
            'title': 'Test Book'
        }
        
        print("📋 Input data:", test_data_minimal)
        result = parse_keepa_product(test_data_minimal)
        print("✅ Parser result type:", type(result))
        print("📊 Parser result keys:", list(result.keys()) if isinstance(result, dict) else "Not a dict")
        print("📈 Current price:", result.get('current_price', 'MISSING'))
        print("📉 Current BSR:", result.get('current_bsr', 'MISSING'))
        
    except Exception as e:
        print(f"❌ Parser error: {e}")
        traceback.print_exc()
        return None
    
    return result

def test_calculation_with_parsed_data(parsed_data):
    """Test calculation logic with parsed data to reproduce type errors."""
    print("\n🧮 TESTING CALCULATIONS WITH PARSED DATA")
    
    if not parsed_data:
        print("⚠️ No parsed data to test calculations")
        return
    
    try:
        from decimal import Decimal
        from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData
        
        print("📋 Testing type conversions...")
        
        # This is where the error likely occurs
        current_price_raw = parsed_data.get('current_price', 20.0)
        print(f"🏷️ Current price raw: {current_price_raw} (type: {type(current_price_raw)})")
        
        # Try the conversion that's failing
        try:
            current_price = Decimal(str(current_price_raw))
            print(f"💰 Current price Decimal: {current_price}")
            
            # This line is likely causing the error
            estimated_cost = current_price * Decimal('0.75')
            print(f"💵 Estimated cost: {estimated_cost}")
            
        except Exception as conv_error:
            print(f"❌ Type conversion error: {conv_error}")
            print(f"🔍 Raw value repr: {repr(current_price_raw)}")
            
        # Test weight conversion
        weight_raw = parsed_data.get('weight', 1.0)
        print(f"⚖️ Weight raw: {weight_raw} (type: {type(weight_raw)})")
        
        weight = Decimal(str(weight_raw))
        print(f"📦 Weight Decimal: {weight}")
        
        # Test config fallback
        from app.services.business_config_service import BusinessConfigService
        config_service = BusinessConfigService()
        
        print("🔧 Testing config loading...")
        
    except Exception as e:
        print(f"❌ Calculation test error: {e}")
        traceback.print_exc()

def test_real_keepa_data():
    """Test with actual Keepa API call to see real data structure."""
    print("\n🌐 TESTING WITH REAL KEEPA DATA")
    
    try:
        from app.services.keepa_service import KeepaService
        import asyncio
        
        async def get_real_data():
            keepa_service = KeepaService()
            async with keepa_service:
                # Test with real ASIN
                real_data = await keepa_service.get_product_data('B00FLIJJSA')
                if real_data:
                    print("📡 Real Keepa data received")
                    print(f"🔑 Top-level keys: {list(real_data.keys())[:10]}...")
                    
                    # Check specific fields that might cause issues
                    if 'stats' in real_data:
                        stats = real_data['stats']
                        print(f"📊 Stats type: {type(stats)}")
                        if isinstance(stats, dict):
                            print(f"📈 Stats keys: {list(stats.keys())[:5]}...")
                    
                    if 'csv' in real_data:
                        csv_data = real_data['csv']
                        print(f"📋 CSV data type: {type(csv_data)}")
                        if isinstance(csv_data, list) and csv_data:
                            print(f"📊 CSV first few values: {csv_data[:5] if len(csv_data) >= 5 else csv_data}")
                    
                    return real_data
                else:
                    print("❌ No real data received from Keepa")
                    return None
        
        real_keepa_data = asyncio.run(get_real_data())
        
        if real_keepa_data:
            print("\n🔧 Testing parser with real data...")
            from app.services.keepa_parser import parse_keepa_product
            parsed_real = parse_keepa_product(real_keepa_data)
            print(f"✅ Real data parsed successfully")
            print(f"💰 Parsed current_price: {parsed_real.get('current_price')} (type: {type(parsed_real.get('current_price'))})")
            return parsed_real
            
    except Exception as e:
        print(f"❌ Real data test error: {e}")
        traceback.print_exc()
        return None

def main():
    """Run all diagnostic tests."""
    print("🚀 DIAGNOSTIC & ROOT CAUSE ANALYSIS")
    print("=" * 60)
    
    # Test 1: Parser with minimal data
    parsed_minimal = test_parser_with_minimal_data()
    
    # Test 2: Calculations with parsed data  
    test_calculation_with_parsed_data(parsed_minimal)
    
    # Test 3: Real Keepa data flow
    test_real_keepa_data()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()