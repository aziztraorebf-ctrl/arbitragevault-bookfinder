"""
Debug why the endpoint still fails while direct test works.
Compare direct call vs endpoint call flow.
"""

import sys
import traceback
import asyncio
import keyring
sys.path.insert(0, '.')

def get_keepa_api_key():
    """Securely retrieve Keepa API key from Memex secrets."""
    api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    if api_key and len(api_key) > 10:
        print("✅ Keepa API key retrieved securely")
        return api_key
    else:
        print("❌ Keepa API key not found or invalid")
        return None

async def test_endpoint_flow():
    """Reproduce the exact endpoint flow that still fails."""
    print("🔍 REPRODUCING ENDPOINT FLOW")
    
    api_key = get_keepa_api_key()
    if not api_key:
        return
    
    try:
        # Import exactly like the endpoint does
        from app.services.keepa_service import KeepaService
        from app.services.business_config_service import get_business_config_service
        from app.api.v1.routers.keepa import analyze_product
        from app.services.keepa_parser import parse_keepa_product
        
        # Create services exactly like endpoint
        keepa_service = KeepaService(api_key=api_key)
        config_service = get_business_config_service()
        
        # Get config exactly like endpoint
        try:
            config = await config_service.get_effective_config(
                domain_id=1,
                category="books"
            )
            print("✅ Config loaded successfully")
        except Exception as e:
            print(f"⚠️ Config error: {e}")
            config = {"roi": {"target_roi_percent": 30}}
        
        # Get data exactly like endpoint
        identifier = "B00FLIJJSA"
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(identifier, force_refresh=False)
            
            if keepa_data:
                print("✅ Keepa data received")
                
                # Test parsing exactly like endpoint
                parsed_data = parse_keepa_product(keepa_data)
                print(f"✅ Parsing done: current_price = {parsed_data.get('current_price')} ({type(parsed_data.get('current_price'))})")
                
                # Now call analyze_product exactly like endpoint
                asin = keepa_data.get('asin', identifier)
                
                print(f"🧮 Calling analyze_product with:")
                print(f"   asin: {asin}")
                print(f"   config type: {type(config)}")
                print(f"   keepa_service type: {type(keepa_service)}")
                
                analysis = await analyze_product(asin, keepa_data, config, keepa_service)
                print(f"📊 Analysis result: {analysis.recommendation}")
                
                if analysis.recommendation == "ERROR":
                    print("❌ Still getting ERROR - let's check analysis details")
                    print(f"ROI: {analysis.roi}")
                    print(f"Velocity: {analysis.velocity}")
                else:
                    print("✅ Analysis working correctly!")
                
    except Exception as e:
        print(f"❌ Endpoint flow error: {e}")
        traceback.print_exc()

async def test_weight_field():
    """Check if weight field is causing the sequence multiplication error."""
    print("\n🔍 TESTING WEIGHT FIELD SPECIFICALLY")
    
    api_key = get_keepa_api_key()
    if not api_key:
        return
        
    try:
        from app.services.keepa_service import KeepaService
        from app.services.keepa_parser import parse_keepa_product
        
        keepa_service = KeepaService(api_key=api_key)
        
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data("B00FLIJJSA")
            parsed_data = parse_keepa_product(keepa_data)
            
            # Check weight field specifically
            weight = parsed_data.get('weight')
            print(f"Weight field: {weight} (type: {type(weight)})")
            
            # Check package weight fields
            for key in ['package_weight', 'package_height', 'package_length', 'package_width']:
                value = parsed_data.get(key)
                print(f"{key}: {value} (type: {type(value)})")
                
            # Check if any field might be a string/list that could multiply with float
            for key, value in parsed_data.items():
                if isinstance(value, (str, list)) and key not in ['asin', 'title', 'raw_data']:
                    print(f"⚠️ Non-numeric field {key}: {type(value)} = {str(value)[:50]}")
                    
    except Exception as e:
        print(f"❌ Weight test error: {e}")
        traceback.print_exc()

async def main():
    print("🔍 DEBUGGING ENDPOINT VS DIRECT CALL DIFFERENCE")
    print("=" * 60)
    
    await test_endpoint_flow()
    await test_weight_field()
    
    print("\n" + "=" * 60)
    print("🎯 ENDPOINT DIFFERENCE DEBUG COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())