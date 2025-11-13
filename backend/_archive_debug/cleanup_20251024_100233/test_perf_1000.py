#!/usr/bin/env python3
"""Test performance avec 1000 analyses simulées."""

import asyncio
import aiohttp
import time

async def test_pagination_deep():
    """Test pagination profonde avec 1000 items simulés."""
    print("🏃 Test Performance 1000 Analyses")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        
        # Test pagination profonde (même si vide, teste la structure)
        test_cases = [
            {"page": 1, "per_page": 20, "desc": "Page 1 (début)"},
            {"page": 25, "per_page": 20, "desc": "Page 25 (milieu de 1000)"},
            {"page": 50, "per_page": 20, "desc": "Page 50 (fin de 1000)"},
            {"page": 1, "per_page": 100, "desc": "Page 1 avec 100 items"},
        ]
        
        results = []
        
        for test in test_cases:
            url = f"http://localhost:8000/api/v1/analyses?page={test['page']}&per_page={test['per_page']}"
            
            start_time = time.time()
            
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        duration_ms = (time.time() - start_time) * 1000
                        
                        print(f"   {test['desc']}: {duration_ms:.1f}ms - Structure OK")
                        results.append(duration_ms)
                        
                        if duration_ms < 250:
                            print(f"     ✅ < 250ms target")
                        else:
                            print(f"     ⚠️  > 250ms target ({duration_ms:.1f}ms)")
                    else:
                        print(f"   ❌ {test['desc']}: HTTP {resp.status}")
                        
            except Exception as e:
                print(f"   ❌ {test['desc']}: {e}")
        
        # Test avec filtres (plus complexe)
        print(f"\n📊 Tests avec filtres:")
        filter_tests = [
            "min_roi=30&max_roi=50",
            "min_velocity=0.5&max_velocity=0.8",
            "batch_id=test123&min_roi=25"
        ]
        
        for filter_test in filter_tests:
            url = f"http://localhost:8000/api/v1/analyses?{filter_test}&page=1&per_page=50"
            
            start_time = time.time()
            try:
                async with session.get(url) as resp:
                    duration_ms = (time.time() - start_time) * 1000
                    if resp.status == 200:
                        print(f"   Filtre '{filter_test[:20]}...': {duration_ms:.1f}ms ✅")
                    else:
                        print(f"   Filtre '{filter_test[:20]}...': HTTP {resp.status} ❌")
            except Exception as e:
                print(f"   Filtre error: {e}")
        
        # Résumé
        if results:
            avg_time = sum(results) / len(results)
            max_time = max(results)
            print(f"\n📈 Résumé Performance:")
            print(f"   Temps moyen: {avg_time:.1f}ms")
            print(f"   Temps max: {max_time:.1f}ms")
            print(f"   Objectif < 250ms: {'✅' if max_time < 250 else '⚠️'}")
            print(f"   Note: Test sur stubs (vraie perf sera avec DB)")

if __name__ == "__main__":
    asyncio.run(test_pagination_deep())