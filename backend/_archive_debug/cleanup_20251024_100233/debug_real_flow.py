"""
Debug the real data flow that causes the errors in smoke test.
Reproduce the exact same calls that fail.
"""

import sys
import traceback
import asyncio
import json
sys.path.insert(0, '.')

async def debug_batch_ingest_flow():
    """Reproduce the exact flow from batch ingest that fails."""
    print("🔍 REPRODUCING BATCH INGEST FLOW")
    
    try:
        from app.services.keepa_service import get_keepa_service
        from app.services.business_config_service import get_business_config_service
        from app.api.v1.routers.keepa import analyze_product
        
        # Get services like the real endpoint does
        keepa_service = await get_keepa_service()
        config_service = await get_business_config_service()
        
        print("✅ Services loaded")
        
        # Get config like real endpoint
        try:
            config = await config_service.get_effective_config(
                domain_id=1,
                category="books" 
            )
            print(f"✅ Config loaded: {type(config)}")
            print(f"🔧 Config keys: {list(config.keys())}")
        except Exception as config_error:
            print(f"⚠️ Config loading failed: {config_error}")
            # This explains the "Database not initialized" error
            config = {
                "roi": {"target_roi_percent": 30, "buffer_percent": 6},
                "velocity": {"min_velocity_score": 50}
            }
            print("🔄 Using fallback config")
        
        # Test with real identifier
        identifier = "B00FLIJJSA"
        
        # Get product data like real endpoint
        async with keepa_service:
            print(f"🌐 Calling Keepa API for {identifier}...")
            keepa_data = await keepa_service.get_product_data(identifier, force_refresh=False)
            
            if keepa_data:
                print(f"📡 Keepa data received: {type(keepa_data)}")
                print(f"🔑 Top-level keys: {list(keepa_data.keys())[:10]}")
                
                # This is where the parsing likely fails
                print("\n🔧 TESTING PARSE STEP...")
                from app.services.keepa_parser import parse_keepa_product
                
                try:
                    parsed_data = parse_keepa_product(keepa_data)
                    print(f"✅ Parsed data: {type(parsed_data)}")
                    
                    # Show the exact values that go to calculation
                    current_price = parsed_data.get('current_price')
                    print(f"💰 Current price: {current_price} (type: {type(current_price)})")
                    
                    weight = parsed_data.get('weight')
                    print(f"⚖️ Weight: {weight} (type: {type(weight)})")
                    
                    # NOW TEST THE ACTUAL ANALYZE FUNCTION
                    print("\n🧮 TESTING ANALYZE_PRODUCT...")
                    asin = keepa_data.get('asin', identifier)
                    
                    analysis = await analyze_product(asin, keepa_data, config, keepa_service)
                    print(f"📊 Analysis result: {analysis.recommendation}")
                    
                except Exception as parse_error:
                    print(f"❌ Parse/analyze error: {parse_error}")
                    traceback.print_exc()
                    
                    # Let's examine the raw data structure that's causing issues
                    print(f"\n🔍 RAW KEEPA DATA INSPECTION:")
                    if isinstance(keepa_data, dict):
                        for key, value in list(keepa_data.items())[:5]:
                            print(f"  {key}: {type(value)} = {str(value)[:100]}...")
                    
            else:
                print("❌ No Keepa data received")
                
    except Exception as e:
        print(f"❌ Debug flow error: {e}")
        traceback.print_exc()

def examine_smoke_test_output():
    """Parse the actual error from smoke test to understand the issue."""
    print("\n🔍 EXAMINING SMOKE TEST ERROR PATTERNS")
    
    error_messages = [
        "can't multiply sequence by non-int of type 'float'",
        "object of type 'NoneType' has no len()"
    ]
    
    print("🚨 Error #1: Type multiplication issue")
    print("   - Likely: string/list * float instead of number * float")
    print("   - Location: analyze_product() calculations")
    
    print("🚨 Error #2: NoneType has no len()")  
    print("   - Likely: trying to check len() on None value")
    print("   - Location: parse_keepa_product() processing arrays")

async def main():
    print("🚀 DEBUGGING REAL DATA FLOW")
    print("=" * 60)
    
    examine_smoke_test_output()
    await debug_batch_ingest_flow()
    
    print("\n" + "=" * 60)
    print("🎯 REAL FLOW DEBUG COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())