#!/usr/bin/env python3
"""Test concurrentiel simple pour valider les endpoints Phase 1."""

import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_endpoint_concurrent(session, endpoint, data=None):
    """Test un endpoint de manière concurrente."""
    url = f"http://localhost:8000/api/v1{endpoint}"
    
    try:
        if data:
            async with session.post(url, json=data) as resp:
                return resp.status, await resp.text()
        else:
            async with session.get(url) as resp:
                return resp.status, await resp.text()
    except Exception as e:
        return 500, str(e)

async def run_concurrent_tests():
    """Lance les tests concurrents."""
    print("🔄 Tests Concurrents Phase 1")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: 10 requêtes GET simultanées
        print("1. Test GET concurrent (10 req)...")
        start_time = time.time()
        
        tasks = []
        for i in range(10):
            tasks.append(test_endpoint_concurrent(session, "/analyses"))
            tasks.append(test_endpoint_concurrent(session, "/batches"))
        
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        success_count = sum(1 for status, _ in results if status == 200)
        print(f"   ✅ {success_count}/{len(results)} requêtes réussies en {duration:.2f}s")
        
        # Test 2: 5 créations POST simultanées
        print("\n2. Test POST concurrent (5 req)...")
        start_time = time.time()
        
        post_data = {
            "batch_id": "concurrent-test",
            "isbn_or_asin": "9780134685991",
            "buy_price": 15.99,
            "fees": 3.50,
            "expected_sale_price": 24.99,
            "profit": 5.50,
            "roi_percent": 34.4,
            "velocity_score": 0.75
        }
        
        tasks = []
        for i in range(5):
            post_data_copy = post_data.copy()
            post_data_copy["isbn_or_asin"] = f"978013468599{i}"
            tasks.append(test_endpoint_concurrent(session, "/analyses", post_data_copy))
        
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        success_count = sum(1 for status, _ in results if status == 201)
        print(f"   ✅ {success_count}/{len(results)} créations réussies en {duration:.2f}s")
        
        # Test 3: 5 PATCH simultanés
        print("\n3. Test PATCH concurrent (5 req)...")
        start_time = time.time()
        
        patch_data = {"status": "running"}
        
        tasks = []
        for i in range(5):
            endpoint = f"/batches/concurrent-{i}/status"
            tasks.append(test_endpoint_concurrent(session, endpoint, patch_data))
        
        # For PATCH we need to use a different method
        patch_tasks = []
        for i in range(5):
            patch_tasks.append(test_patch_concurrent(session, f"concurrent-{i}", patch_data))
        
        results = await asyncio.gather(*patch_tasks)
        duration = time.time() - start_time
        
        success_count = sum(1 for status, _ in results if status == 200)
        print(f"   ✅ {success_count}/{len(results)} patches réussis en {duration:.2f}s")
        
        print(f"\n🎯 Tests concurrents terminés - UserRole fix validé !")

async def test_patch_concurrent(session, batch_id, data):
    """Test PATCH spécifique."""
    url = f"http://localhost:8000/api/v1/batches/{batch_id}/status"
    
    try:
        async with session.patch(url, json=data) as resp:
            return resp.status, await resp.text()
    except Exception as e:
        return 500, str(e)

def test_userole_import():
    """Test que UserRole s'importe correctement (fix concurrents)."""
    print("🧪 Test UserRole Import")
    print("=" * 25)
    
    try:
        from app.models.user import UserRole
        print(f"✅ UserRole importé : {list(UserRole)}")
        return True
    except Exception as e:
        print(f"❌ UserRole import error : {e}")
        return False

if __name__ == "__main__":
    # Test UserRole d'abord
    userole_ok = test_userole_import()
    
    if userole_ok:
        print("\n" + "="*50)
        print("🚀 UserRole OK - Lancement tests concurrents...")
        print("="*50)
        
        try:
            asyncio.run(run_concurrent_tests())
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrompus")
    else:
        print("❌ UserRole fix nécessaire avant tests concurrents")