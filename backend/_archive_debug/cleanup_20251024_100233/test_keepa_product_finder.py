#!/usr/bin/env python3
"""
Test Keepa Product Finder integration.
"""
import asyncio
import keyring
from app.services.keepa_service import KeepaService

async def test_keepa_product_finder():
    """Test the new find_products method."""
    print("=== KEEPA PRODUCT FINDER TEST ===")
    
    # Get API key
    keepa_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    if not keepa_key:
        print("❌ No Keepa API key found")
        return
    
    print(f"✅ Keepa API key loaded: {keepa_key[:10]}...")
    
    # Initialize service
    service = KeepaService(api_key=keepa_key, concurrency=1)
    
    try:
        # Test 1: Health check
        print("\n1. Testing Keepa service health...")
        health = await service.health_check()
        print(f"   Health: {health}")
        
        if health.get("status") != "healthy":
            print("❌ Keepa service not healthy")
            return
        
        # Test 2: Basic product finder search
        print("\n2. Testing Product Finder search...")
        search_criteria = {
            "categories_include": 1000,  # Books category
            "current_NEW_gte": 1000,     # Min $10.00 
            "current_NEW_lte": 5000,     # Max $50.00
            "avg30_SALES_lte": 100000,   # BSR better than 100k
            "sort": ["current_SALES", "asc"]
        }
        
        asins = await service.find_products(search_criteria, domain=1, max_results=10)
        print(f"   Found {len(asins)} ASINs:")
        for i, asin in enumerate(asins[:5], 1):
            print(f"   {i}. {asin}")
        
        # Test 3: Get details for first ASIN
        if asins:
            print(f"\n3. Testing product details for {asins[0]}...")
            product_data = await service.get_product_data(asins[0])
            
            if product_data:
                title = product_data.get('title', 'Unknown')
                print(f"   Title: {title}")
                print("   ✅ Product data retrieval working")
            else:
                print("   ⚠️ No product data returned")
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_keepa_product_finder())