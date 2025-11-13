"""
Smoke test pour Keepa Service - Phase 2 Validation
"""

import asyncio
import subprocess
from app.services.keepa_service import KeepaService


async def smoke_test():
    """Test direct du service Keepa."""
    
    print("🧪 PHASE 2 - KEEPA SERVICE SMOKE TEST")
    print("=" * 50)
    
    # Récupération clé API
    try:
        result = subprocess.run(
            ["keyring", "get", "memex", "KEEPA_API_KEY"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            api_key = result.stdout.strip()
            print(f"✅ API Key retrieved (length: {len(api_key)})")
        else:
            print("❌ KEEPA_API_KEY not found in secrets")
            return
            
    except Exception as e:
        print(f"❌ Error getting API key: {e}")
        return
    
    # Test service instantiation
    try:
        service = KeepaService(api_key=api_key, concurrency=3)
        print("✅ KeepaService instantiated")
    except Exception as e:
        print(f"❌ Service instantiation failed: {e}")
        return
    
    async with service:
        
        # Test 1: Health Check
        print("\n📋 Test 1: Health Check")
        try:
            health = await service.health_check()
            print(f"✅ Health check: {health['status']}")
            
            if health['status'] == 'healthy':
                print(f"   Tokens left: {health.get('tokens_left', 'unknown')}")
                print(f"   Circuit breaker: {health.get('circuit_breaker_state', 'unknown')}")
            else:
                print(f"   Error: {health.get('error', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # Test 2: Product Data (ASIN test)
        print("\n📋 Test 2: Product Data - ASIN")
        test_asin = "B00FLIJJSA"  # Example ASIN
        
        try:
            product = await service.get_product_data(test_asin)
            
            if product:
                title = product.get('title', 'No title')[:50]
                asin = product.get('asin', 'unknown')
                print(f"✅ Product found: {title}...")
                print(f"   ASIN: {asin}")
                print(f"   Has price data: {'csv' in product}")
                print(f"   Has stats: {'stats' in product}")
            else:
                print("⚠️  Product not found (could be normal)")
                
        except Exception as e:
            print(f"❌ Product data failed: {e}")
        
        # Test 3: Product Data (ISBN-13 test)
        print("\n📋 Test 3: Product Data - ISBN-13")
        test_isbn = "9780134685991"  # Example technical book ISBN
        
        try:
            product = await service.get_product_data(test_isbn)
            
            if product:
                title = product.get('title', 'No title')[:50]
                asin = product.get('asin', 'unknown')  
                print(f"✅ ISBN resolved: {title}...")
                print(f"   Resolved ASIN: {asin}")
            else:
                print("⚠️  ISBN not resolved (could be normal)")
                
        except Exception as e:
            print(f"❌ ISBN resolution failed: {e}")
        
        # Test 4: Cache Statistics
        print("\n📋 Test 4: Cache Statistics")
        try:
            cache_stats = service.get_cache_stats()
            print(f"✅ Cache stats:")
            print(f"   Total entries: {cache_stats['total_entries']}")
            print(f"   Active entries: {cache_stats['active_entries']}")
            print(f"   Entries by type: {cache_stats['entries_by_type']}")
        except Exception as e:
            print(f"❌ Cache stats failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 SMOKE TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(smoke_test())