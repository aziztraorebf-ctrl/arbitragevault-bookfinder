#!/usr/bin/env python3
"""
Test simple pour voir la structure réelle de l'API Keepa.
"""
import asyncio
import keyring
from app.services.keepa_service import KeepaService

async def test_keepa_simple():
    """Test simple pour voir comment l'API répond."""
    print("=== TEST SIMPLE KEEPA ===")
    
    # Get API key
    keepa_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    if not keepa_key:
        print("❌ No Keepa API key found")
        return
    
    service = KeepaService(api_key=keepa_key, concurrency=1)
    
    try:
        # Test 1: Essayer différents endpoints pour voir lesquels existent
        endpoints_to_test = [
            '/product',
            '/query', 
            '/token',
            '/deals',
            '/category'
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n🔍 Testing endpoint: {endpoint}")
            try:
                # Test avec paramètres minimums
                if endpoint == '/token':
                    data = await service._make_request(endpoint, {})
                    print(f"   ✅ {endpoint}: {data}")
                elif endpoint == '/product':
                    # Test avec un ASIN connu
                    data = await service._make_request(endpoint, {
                        'domain': 1,
                        'asin': 'B08N5WRWNW'
                    })
                    if data.get('products'):
                        print(f"   ✅ {endpoint}: Found {len(data['products'])} products")
                    else:
                        print(f"   ⚠️ {endpoint}: No products in response: {data}")
                else:
                    # Test avec paramètres basiques
                    data = await service._make_request(endpoint, {
                        'domain': 1
                    })
                    print(f"   ✅ {endpoint}: {data}")
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    print(f"   ❌ {endpoint}: Not Found (404)")
                elif "400" in error_msg:
                    print(f"   ❌ {endpoint}: Bad Request (400)")
                else:
                    print(f"   ❌ {endpoint}: {error_msg}")
        
        print("\n=== TEST TERMINÉ ===")
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_keepa_simple())