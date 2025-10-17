#!/usr/bin/env python3
"""
Test PgBouncer Endpoints - Context7 BUILD-TEST-VALIDATE Pattern
Validation des endpoints critiques après déploiement PgBouncer

Tests focus sur les endpoints qui causaient "connection was closed":
- POST /api/v1/analyses/batch
- GET /api/v1/analyses  
- GET /api/v1/batches/latest
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    success: bool
    response_time: float
    error: str = ""

class PgBouncerEndpointTester:
    def __init__(self, base_url: str = "https://arbitragevault-backend-v2.onrender.com"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_endpoints(self) -> List[TestResult]:
        """Test basic health endpoints first."""
        results = []
        
        health_tests = [
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/health/ready"),
        ]
        
        for method, endpoint in health_tests:
            result = await self._test_single_endpoint(method, endpoint)
            results.append(result)
            
        return results
    
    async def test_critical_endpoints(self) -> List[TestResult]:
        """Test endpoints qui causaient les erreurs de connection pool."""
        results = []
        
        # Tests endpoints critiques
        critical_tests = [
            ("GET", "/api/v1/analyses"),
            ("GET", "/api/v1/batches/latest"),
        ]
        
        for method, endpoint in critical_tests:
            result = await self._test_single_endpoint(method, endpoint)
            results.append(result)
            
        return results
    
    async def test_batch_analysis_endpoint(self) -> TestResult:
        """Test spécifique pour POST /api/v1/analyses/batch (le plus problématique)."""
        
        # Payload minimal pour test
        test_payload = {
            "asins": ["B00TEST123"],
            "analysis_request": {
                "target_roi": 30,
                "max_investment": 100
            }
        }
        
        return await self._test_single_endpoint(
            "POST", 
            "/api/v1/analyses/batch",
            json_data=test_payload
        )
    
    async def stress_test_connections(self, concurrent_requests: int = 5) -> List[TestResult]:
        """Test de stress pour vérifier la gestion des connexions concurrentes."""
        
        print(f"🔄 Running stress test with {concurrent_requests} concurrent requests...")
        
        tasks = []
        for i in range(concurrent_requests):
            task = self._test_single_endpoint("GET", "/api/v1/health")
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TestResult(
                    endpoint="/api/v1/health",
                    method="GET",
                    status_code=0,
                    success=False,
                    response_time=0.0,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
                
        return processed_results
    
    async def _test_single_endpoint(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Dict[str, Any] = None
    ) -> TestResult:
        """Test un seul endpoint et retourne le résultat."""
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    success = response.status < 400
                    
                    return TestResult(
                        endpoint=endpoint,
                        method=method,
                        status_code=response.status,
                        success=success,
                        response_time=response_time
                    )
            elif method == "POST":
                async with self.session.post(url, json=json_data) as response:
                    response_time = time.time() - start_time
                    success = response.status < 400
                    
                    return TestResult(
                        endpoint=endpoint,
                        method=method,
                        status_code=response.status,
                        success=success,
                        response_time=response_time
                    )
        
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                success=False,
                response_time=response_time,
                error=str(e)
            )

def print_test_results(results: List[TestResult], test_name: str):
    """Affiche les résultats de test de manière formatée."""
    
    print(f"\n📊 {test_name} Results:")
    print("-" * 60)
    
    success_count = 0
    total_time = 0
    
    for result in results:
        status_icon = "✅" if result.success else "❌"
        error_info = f" - {result.error}" if result.error else ""
        
        print(f"{status_icon} {result.method} {result.endpoint}")
        print(f"   Status: {result.status_code} | Time: {result.response_time:.3f}s{error_info}")
        
        if result.success:
            success_count += 1
        total_time += result.response_time
    
    avg_time = total_time / len(results) if results else 0
    success_rate = (success_count / len(results)) * 100 if results else 0
    
    print(f"\n📈 Summary: {success_count}/{len(results)} passed ({success_rate:.1f}%)")
    print(f"⏱️  Average response time: {avg_time:.3f}s")
    
    return success_count == len(results)

async def main():
    """Fonction principale de test PgBouncer."""
    
    print("🧪 PGBOUNCER ENDPOINT VALIDATION - Context7 Pattern")
    print("=" * 60)
    print("Testing endpoints qui causaient 'connection was closed' errors")
    
    async with PgBouncerEndpointTester() as tester:
        all_tests_passed = True
        
        # 1. Test health endpoints
        health_results = await tester.test_health_endpoints()
        health_passed = print_test_results(health_results, "Health Endpoints")
        all_tests_passed &= health_passed
        
        # 2. Test endpoints critiques
        critical_results = await tester.test_critical_endpoints()
        critical_passed = print_test_results(critical_results, "Critical Endpoints")
        all_tests_passed &= critical_passed
        
        # 3. Test batch analysis (le plus problématique)
        print(f"\n🎯 Testing Most Critical Endpoint...")
        batch_result = await tester.test_batch_analysis_endpoint()
        batch_passed = print_test_results([batch_result], "Batch Analysis")
        all_tests_passed &= batch_passed
        
        # 4. Test de stress connexions
        stress_results = await tester.stress_test_connections(concurrent_requests=5)
        stress_passed = print_test_results(stress_results, "Connection Stress Test")
        all_tests_passed &= stress_passed
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - PgBouncer configuration successful!")
        print("✅ Connection pool errors resolved")
        print("✅ Endpoints /api/v1/analyses /api/v1/batches operational") 
    else:
        print("⚠️  SOME TESTS FAILED - PgBouncer needs investigation")
        print("❌ Connection pool issues may persist")
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)