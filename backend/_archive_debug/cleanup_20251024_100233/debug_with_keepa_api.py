"""
Debug with real Keepa API using secure credentials from Memex secrets.
Reproduce the exact error conditions from the smoke test.
"""

import sys
import traceback
import asyncio
import keyring
from decimal import Decimal
sys.path.insert(0, '.')

def get_keepa_api_key():
    """Securely retrieve Keepa API key from Memex secrets."""
    try:
        # Get the secret in memory only - never print or log it
        api_key = keyring.get_password("memex", "KEEPA_API_KEY")
        if api_key and len(api_key) > 10:  # Basic validation
            print("✅ Keepa API key retrieved securely")
            return api_key
        else:
            print("❌ Keepa API key not found or invalid")
            return None
    except Exception as e:
        print(f"❌ Error retrieving Keepa API key: {e}")
        return None

async def test_real_keepa_flow():
    """Test the complete flow that causes errors in production."""
    print("🌐 TESTING REAL KEEPA API FLOW")
    
    # Get API key securely
    api_key = get_keepa_api_key()
    if not api_key:
        print("⚠️ Cannot proceed without API key")
        return None
    
    try:
        from app.services.keepa_service import KeepaService
        from app.services.keepa_parser import parse_keepa_product
        
        # Create service with real API key
        keepa_service = KeepaService(api_key=api_key)
        
        # Test with the same ASIN that fails in smoke test
        test_asin = "B00FLIJJSA"
        
        async with keepa_service:
            print(f"📡 Calling Keepa API for {test_asin}...")
            
            # This is the exact call from the smoke test
            keepa_data = await keepa_service.get_product_data(test_asin, force_refresh=False)
            
            if not keepa_data:
                print("❌ No data returned from Keepa API")
                return None
                
            print(f"✅ Keepa data received: {len(keepa_data)} top-level keys")
            
            # Examine the structure that causes parsing issues
            print("\n🔍 ANALYZING KEEPA DATA STRUCTURE")
            
            # Check for fields that might cause null errors
            critical_fields = ['stats', 'csv', 'title', 'asin']
            for field in critical_fields:
                value = keepa_data.get(field)
                print(f"  {field}: {type(value)} = {str(value)[:50] if value is not None else 'None'}...")
            
            # Now test parsing - this is where "NoneType has no len()" likely occurs
            print("\n🔧 TESTING PARSE_KEEPA_PRODUCT...")
            try:
                parsed_data = parse_keepa_product(keepa_data)
                print(f"✅ Parsing successful: {type(parsed_data)}")
                
                # Check the specific fields that go into calculations
                print("\n💰 PARSED DATA FOR CALCULATIONS:")
                current_price = parsed_data.get('current_price')
                print(f"  current_price: {current_price} (type: {type(current_price)})")
                
                weight = parsed_data.get('weight', 1.0) 
                print(f"  weight: {weight} (type: {type(weight)})")
                
                bsr = parsed_data.get('current_bsr')
                print(f"  current_bsr: {bsr} (type: {type(bsr)})")
                
                # Test the exact calculation that fails
                print("\n🧮 TESTING CALCULATION LOGIC...")
                return test_calculation_with_real_data(parsed_data, keepa_data)
                
            except Exception as parse_error:
                print(f"❌ PARSING ERROR: {parse_error}")
                traceback.print_exc()
                
                # Deep dive into what's causing the parse error
                analyze_parse_error(keepa_data, parse_error)
                return None
                
    except Exception as e:
        print(f"❌ Keepa service error: {e}")
        traceback.print_exc()
        return None

def test_calculation_with_real_data(parsed_data, original_keepa_data):
    """Test the calculation logic that causes type errors."""
    print("🧮 REPRODUCING CALCULATION ERROR")
    
    try:
        # This is the exact code from analyze_product() that fails
        current_price_raw = parsed_data.get('current_price', 20.0)
        print(f"  Step 1 - current_price_raw: {repr(current_price_raw)}")
        
        # The line that likely causes "can't multiply sequence by non-int of type 'float'"
        current_price = Decimal(str(current_price_raw))
        print(f"  Step 2 - current_price Decimal: {current_price}")
        
        estimated_cost = current_price * Decimal('0.75')
        print(f"  Step 3 - estimated_cost: {estimated_cost}")
        
        # Test weight calculation
        weight_raw = parsed_data.get('weight', 1.0)
        weight = Decimal(str(weight_raw))
        print(f"  Step 4 - weight: {weight}")
        
        print("✅ All calculations passed - error must be elsewhere")
        return True
        
    except Exception as calc_error:
        print(f"❌ CALCULATION ERROR REPRODUCED: {calc_error}")
        print(f"🔍 Error type: {type(calc_error).__name__}")
        
        # Analyze the specific values causing issues
        print(f"\n🔍 PROBLEMATIC VALUES:")
        print(f"  current_price_raw repr: {repr(parsed_data.get('current_price'))}")
        print(f"  current_price_raw type: {type(parsed_data.get('current_price'))}")
        
        if hasattr(parsed_data.get('current_price'), '__len__'):
            print(f"  current_price_raw length: {len(parsed_data.get('current_price'))}")
        
        traceback.print_exc()
        return False

def analyze_parse_error(keepa_data, error):
    """Analyze what in the Keepa data structure causes parsing to fail."""
    print(f"\n🔍 ANALYZING PARSE ERROR: {error}")
    
    if "NoneType" in str(error) and "len" in str(error):
        print("🎯 Root cause: Attempting len() on None value")
        print("🔍 Checking arrays/lists in Keepa data...")
        
        for key, value in keepa_data.items():
            if isinstance(value, list):
                print(f"  📋 {key}: list with {len(value)} items")
            elif value is None:
                print(f"  ⚠️ {key}: None (potential issue)")
            elif isinstance(value, dict) and not value:
                print(f"  📝 {key}: empty dict")

async def main():
    """Run complete diagnostic with real Keepa API."""
    print("🚀 REAL KEEPA API DIAGNOSTIC")
    print("=" * 60)
    
    result = await test_real_keepa_flow()
    
    print("\n" + "=" * 60)
    if result:
        print("✅ DIAGNOSTIC: Issue identified and reproduced")
    else:
        print("🔍 DIAGNOSTIC: Need deeper investigation")
    
    # Clear API key from memory
    api_key = None
    
if __name__ == "__main__":
    asyncio.run(main())