"""
Tests de performance et charge pour valider la robustesse du backend
Vérifie les temps de réponse et la stabilité sous stress

NOTE: Ces tests nécessitent un serveur backend en cours d'exécution.
Ils sont skippés par défaut pour ne pas bloquer les tests unitaires.
Pour exécuter: démarrer le backend avec 'uvicorn app.main:app' puis pytest avec --run-e2e
"""
import pytest
import httpx
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import statistics

BASE_URL = "http://localhost:8000"
PERFORMANCE_TIMEOUT = 60.0

# Skip all E2E tests by default unless --run-e2e flag is provided
pytestmark = pytest.mark.skip(reason="Requires running backend server - use pytest --run-e2e to enable")

class TestPerformanceLoad:
    """Tests de performance et charge du backend corrigé"""
    
    async def test_response_times_baseline(self):
        """Test 1: Temps de réponse baseline des endpoints critiques"""
        endpoints = [
            "/health",
            "/api/v1/batches?page=1&size=10",
            "/api/v1/analyses?page=1&size=10", 
            "/api/v1/views/profit_hunter",
            "/api/v1/views/velocity"
        ]
        
        response_times = {}
        
        async with httpx.AsyncClient(timeout=PERFORMANCE_TIMEOUT) as client:
            for endpoint in endpoints:
                start_time = time.time()
                response = await client.get(f"{BASE_URL}{endpoint}")
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times[endpoint] = response_time
                
                # Assertion temps de réponse < 2 secondes (règle projet)
                assert response_time < 2.0, f"Endpoint {endpoint} trop lent: {response_time:.2f}s"
                assert response.status_code == 200
        
        # Affichage résultats
        print("\n⏱️ TEMPS DE RÉPONSE BASELINE:")
        for endpoint, time_ms in response_times.items():
            print(f"  {endpoint}: {time_ms:.3f}s")
        
        avg_time = statistics.mean(response_times.values())
        print(f"📊 Temps moyen: {avg_time:.3f}s")
        assert avg_time < 1.0, "Temps moyen trop élevé"
        
        return response_times

    async def test_concurrent_requests(self):
        """Test 2: Requêtes simultanées (10 clients concurrents)"""
        concurrent_clients = 10
        requests_per_client = 5
        endpoint = "/api/v1/batches?page=1&size=5"
        
        async def make_requests(client_id: int) -> List[float]:
            """Fait plusieurs requêtes pour un client"""
            times = []
            async with httpx.AsyncClient(timeout=PERFORMANCE_TIMEOUT) as client:
                for _ in range(requests_per_client):
                    start = time.time()
                    response = await client.get(f"{BASE_URL}{endpoint}")
                    end = time.time()
                    
                    assert response.status_code == 200
                    times.append(end - start)
            return times
        
        # Lancement concurrent
        start_total = time.time()
        tasks = [make_requests(i) for i in range(concurrent_clients)]
        all_times = await asyncio.gather(*tasks)
        end_total = time.time()
        
        # Analyse résultats
        flat_times = [t for client_times in all_times for t in client_times]
        total_requests = concurrent_clients * requests_per_client
        
        avg_response = statistics.mean(flat_times)
        max_response = max(flat_times)
        total_duration = end_total - start_total
        
        print(f"\n🚀 CHARGE CONCURRENTE:")
        print(f"  Clients simultanés: {concurrent_clients}")
        print(f"  Requêtes totales: {total_requests}")
        print(f"  Durée totale: {total_duration:.2f}s")
        print(f"  Temps moyen: {avg_response:.3f}s")
        print(f"  Temps max: {max_response:.3f}s")
        
        # Assertions performance
        assert avg_response < 2.0, "Temps de réponse moyen dégradé sous charge"
        assert max_response < 5.0, "Temps de réponse maximum inacceptable"
        
        return {"avg": avg_response, "max": max_response, "total_duration": total_duration}

    async def test_batch_creation_performance(self):
        """Test 3: Performance création de batches avec ISBNs multiples"""
        isbn_sizes = [10, 25, 50, 75]  # Tailles croissantes
        performance_data = {}
        
        async with httpx.AsyncClient(timeout=PERFORMANCE_TIMEOUT) as client:
            for size in isbn_sizes:
                # Générer liste ISBN de test
                test_isbns = [f"978000000{str(i).zfill(4)}" for i in range(size)]
                
                batch_data = {
                    "name": f"Perf Test Batch - {size} ISBNs",
                    "description": f"Test performance avec {size} ISBNs",
                    "asin_list": test_isbns,
                    "config_name": "profit_hunter"
                }
                
                start = time.time()
                response = await client.post(f"{BASE_URL}/api/v1/batches", json=batch_data)
                end = time.time()
                
                creation_time = end - start
                performance_data[size] = creation_time
                
                assert response.status_code == 201
                # Temps de création doit rester raisonnable
                assert creation_time < 10.0, f"Création batch {size} ISBNs trop lente: {creation_time:.2f}s"
        
        print(f"\n📦 PERFORMANCE CRÉATION BATCHES:")
        for size, time_taken in performance_data.items():
            print(f"  {size} ISBNs: {time_taken:.3f}s")
        
        # Vérifier évolutivité linéaire
        if len(performance_data) >= 2:
            times = list(performance_data.values())
            # Le temps ne doit pas exploser de façon exponentielle
            ratio_max = max(times) / min(times)
            assert ratio_max < 10.0, f"Dégradation performance non-linéaire: ratio {ratio_max:.2f}"
        
        return performance_data

    async def test_memory_stability(self):
        """Test 4: Stabilité mémoire sur opérations répétées"""
        iterations = 20
        endpoint = "/api/v1/views/profit_hunter"
        
        response_times = []
        
        async with httpx.AsyncClient(timeout=PERFORMANCE_TIMEOUT) as client:
            for i in range(iterations):
                start = time.time()
                response = await client.get(f"{BASE_URL}{endpoint}")
                end = time.time()
                
                response_time = end - start
                response_times.append(response_time)
                
                assert response.status_code == 200
                
                # Pause courte entre requêtes
                await asyncio.sleep(0.1)
        
        # Analyse stabilité
        first_half = response_times[:iterations//2]
        second_half = response_times[iterations//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        print(f"\n🧠 STABILITÉ MÉMOIRE ({iterations} itérations):")
        print(f"  Première moitié: {avg_first:.3f}s")
        print(f"  Seconde moitié: {avg_second:.3f}s")
        print(f"  Différence: {abs(avg_second - avg_first):.3f}s")
        
        # Vérifier pas de dégradation significative
        degradation = avg_second / avg_first
        assert degradation < 2.0, f"Dégradation mémoire détectée: {degradation:.2f}x plus lent"
        
        return {"first_half_avg": avg_first, "second_half_avg": avg_second, "degradation": degradation}

    async def test_keepa_api_performance(self):
        """Test 5: Performance intégration Keepa API avec ISBNs réels"""
        real_isbns = [
            "1292025824",   # Business Analytics
            "0134683943",   # Computer Networks  
            "1337569321"    # Calculus
        ]
        
        keepa_times = {}
        
        async with httpx.AsyncClient(timeout=PERFORMANCE_TIMEOUT) as client:
            for isbn in real_isbns:
                batch_data = {
                    "name": f"Keepa Test - {isbn}",
                    "description": "Test performance Keepa API",
                    "asin_list": [isbn],
                    "config_name": "velocity"
                }
                
                start = time.time()
                response = await client.post(f"{BASE_URL}/api/v1/batches", json=batch_data)
                end = time.time()
                
                creation_time = end - start
                keepa_times[isbn] = creation_time
                
                # Vérifier création réussie
                assert response.status_code == 201
                
                # Attendre un peu avant ISBN suivant
                await asyncio.sleep(1)
        
        avg_keepa_time = statistics.mean(keepa_times.values())
        max_keepa_time = max(keepa_times.values())
        
        print(f"\n🔗 PERFORMANCE INTÉGRATION KEEPA:")
        for isbn, time_taken in keepa_times.items():
            print(f"  {isbn}: {time_taken:.3f}s")
        print(f"📊 Temps moyen: {avg_keepa_time:.3f}s")
        print(f"📈 Temps max: {max_keepa_time:.3f}s")
        
        # Assertions performance Keepa
        assert avg_keepa_time < 15.0, "Intégration Keepa trop lente en moyenne"
        assert max_keepa_time < 30.0, "Intégration Keepa timeout individuel"
        
        return keepa_times

# Test principal d'exécution
@pytest.mark.asyncio
async def test_complete_performance_suite():
    """Suite complète des tests de performance"""
    tester = TestPerformanceLoad()
    
    print("\n🔥 DÉBUT TESTS PERFORMANCE & CHARGE")
    print("=" * 60)
    
    results = {}
    
    try:
        results["baseline"] = await tester.test_response_times_baseline()
        results["concurrent"] = await tester.test_concurrent_requests()
        results["batch_creation"] = await tester.test_batch_creation_performance()
        results["memory_stability"] = await tester.test_memory_stability()
        results["keepa_performance"] = await tester.test_keepa_api_performance()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS PERFORMANCE RÉUSSIS")
        print("🚀 Backend validé sous charge et stress")
        
        return results
        
    except Exception as e:
        print(f"❌ ÉCHEC TEST PERFORMANCE: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_complete_performance_suite())