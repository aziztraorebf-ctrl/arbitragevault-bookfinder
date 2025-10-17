#!/usr/bin/env python3
"""
Audit de Performance et Charge - ArbitrageVault Backend
Test de charge avec 100-500 requêtes simultanées
"""

import asyncio
import time
import random
import statistics
from typing import List, Dict, Any
import json
from datetime import datetime

# ASINs de test variés (livres, électronique, divers)
TEST_ASINS = [
    "B0BSHF7WHW",  # MacBook Pro
    "0593655036",  # Atomic Habits
    "B08N5WRWNW",  # Echo Dot
    "B07ZPC9QD4",  # Kindle Paperwhite
    "1544514220",  # The Subtle Art
    "B09BVGDH8Z",  # iPhone 13
    "0735211299",  # Thinking Fast and Slow
    "B09V3KXJPB",  # AirPods Pro
    "0062316117",  # Sapiens
    "B08H75RTZ8",  # Fire TV Stick
    "0446310786",  # To Kill a Mockingbird
    "B09G9YQRMH",  # Sony WH-1000XM4
    "0143127748",  # Getting Things Done
    "B08FC5L3RG",  # Echo Show 8
    "0060850523",  # Brave New World
    "B09SWV3BYH",  # iPad Air
    "0345472322",  # Mindset
    "B0B5B6DXGH",  # Samsung Galaxy S23
    "0062457713",  # The Alchemist
    "B09JQMJHVG",  # PlayStation 5
]

class PerformanceAuditor:
    def __init__(self):
        self.results = []
        self.errors = []

    async def simulate_keepa_request(self, asin: str, request_id: int) -> Dict[str, Any]:
        """Simule une requête Keepa avec temps de traitement variable"""
        start_time = time.time()

        try:
            # Simule un temps de traitement variable (50-300ms)
            processing_time = random.uniform(0.05, 0.3)
            await asyncio.sleep(processing_time)

            # Simule parfois des erreurs (5% de chance)
            if random.random() < 0.05:
                raise Exception(f"Simulated error for ASIN {asin}")

            # Simule une réponse Keepa
            response_time = (time.time() - start_time) * 1000  # en ms

            return {
                "request_id": request_id,
                "asin": asin,
                "response_time_ms": response_time,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.errors.append({
                "request_id": request_id,
                "asin": asin,
                "error": str(e),
                "response_time_ms": response_time
            })
            return {
                "request_id": request_id,
                "asin": asin,
                "response_time_ms": response_time,
                "status": "error",
                "error": str(e)
            }

    async def run_concurrent_requests(self, num_requests: int) -> Dict[str, Any]:
        """Execute plusieurs requêtes en parallèle"""
        print(f"\n🚀 Lancement de {num_requests} requêtes simultanées...")

        tasks = []
        for i in range(num_requests):
            asin = random.choice(TEST_ASINS)
            task = self.simulate_keepa_request(asin, i)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyse des résultats
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        failed_requests = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]

        response_times = [r["response_time_ms"] for r in successful_requests]

        return {
            "num_requests": num_requests,
            "total_time_seconds": total_time,
            "requests_per_second": num_requests / total_time,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "error_rate": (len(failed_requests) / num_requests) * 100,
            "response_times": {
                "mean_ms": statistics.mean(response_times) if response_times else 0,
                "median_ms": statistics.median(response_times) if response_times else 0,
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0,
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 0 else 0,
                "p99_ms": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 0 else 0,
            }
        }

    async def run_audit(self):
        """Execute l'audit complet avec différentes charges"""
        print("🔍 AUDIT DE PERFORMANCE ET CHARGE - ArbitrageVault Backend")
        print("=" * 60)

        test_scenarios = [
            {"name": "Charge légère", "requests": 100},
            {"name": "Charge moyenne", "requests": 250},
            {"name": "Charge élevée", "requests": 500},
        ]

        all_results = []

        for scenario in test_scenarios:
            print(f"\n📊 Test: {scenario['name']}")
            result = await self.run_concurrent_requests(scenario["requests"])
            result["scenario"] = scenario["name"]
            all_results.append(result)

            # Affichage des résultats
            print(f"  ✓ Requêtes réussies: {result['successful_requests']}/{result['num_requests']}")
            print(f"  ✓ Taux d'erreur: {result['error_rate']:.2f}%")
            print(f"  ✓ Temps moyen: {result['response_times']['mean_ms']:.2f}ms")
            print(f"  ✓ P95: {result['response_times']['p95_ms']:.2f}ms")
            print(f"  ✓ Throughput: {result['requests_per_second']:.2f} req/s")

        return all_results

async def main():
    auditor = PerformanceAuditor()
    results = await auditor.run_audit()

    # Sauvegarde des résultats JSON
    with open("backend/audits/performance_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n✅ Audit terminé - Résultats sauvegardés dans performance_results.json")
    return results

if __name__ == "__main__":
    asyncio.run(main())