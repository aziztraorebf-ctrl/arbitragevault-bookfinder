#!/usr/bin/env python3
"""
Test des APIs de contrôle AutoScheduler
Validation des endpoints de gestion sans interface frontend
"""
import asyncio
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta
import httpx

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from fastapi.testclient import TestClient
from app.main import app

class AutoSchedulerAPITester:
    """Testeur pour les APIs AutoScheduler"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "/api/v1/autoscheduler"
        
    def test_health_check(self):
        """Test du health check AutoScheduler"""
        print("🔍 Test Health Check")
        
        response = self.client.get(f"{self.base_url}/health")
        
        assert response.status_code == 200, f"Status code: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "AutoScheduler Control"
        assert "current_config" in data
        
        print(f"✅ Health Check OK - Version: {data['version']}")
        return True
    
    def test_get_status(self):
        """Test récupération du statut"""
        print("\n🔍 Test Get Status")
        
        response = self.client.get(f"{self.base_url}/status")
        
        assert response.status_code == 200, f"Status code: {response.status_code}"
        
        data = response.json()
        required_fields = ["enabled", "scheduled_hours", "current_date", "skip_dates"]
        
        for field in required_fields:
            assert field in data, f"Champ manquant: {field}"
        
        print(f"✅ Status OK - Enabled: {data['enabled']}, Hours: {data['scheduled_hours']}")
        return data
    
    def test_enable_disable(self):
        """Test activation/désactivation"""
        print("\n🔍 Test Enable/Disable")
        
        # Test désactivation
        response = self.client.post(f"{self.base_url}/disable")
        assert response.status_code == 200
        
        disable_data = response.json()
        assert disable_data["enabled"] == False
        print("✅ Désactivation OK")
        
        # Vérifier statut
        status_response = self.client.get(f"{self.base_url}/status")
        status_data = status_response.json()
        assert status_data["enabled"] == False
        
        # Test activation
        response = self.client.post(f"{self.base_url}/enable")
        assert response.status_code == 200
        
        enable_data = response.json()
        assert enable_data["enabled"] == True
        print("✅ Activation OK")
        
        return True
    
    def test_pause_functionality(self):
        """Test des fonctions de pause"""
        print("\n🔍 Test Pause Functionality")
        
        # Test pause jusqu'à demain
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        pause_data = {
            "pause_until": tomorrow,
            "reason": "Test de pause API"
        }
        
        response = self.client.post(f"{self.base_url}/pause", json=pause_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["pause_until"] == tomorrow
        print(f"✅ Pause jusqu'au {tomorrow} OK")
        
        # Test pause aujourd'hui
        response = self.client.post(f"{self.base_url}/pause-today")
        assert response.status_code == 200
        
        today_data = response.json()
        assert today_data["skip_date"] == date.today().isoformat()
        print("✅ Pause aujourd'hui OK")
        
        # Réactiver pour nettoyer
        self.client.post(f"{self.base_url}/enable")
        
        return True
    
    def test_schedule_update(self):
        """Test modification des horaires"""
        print("\n🔍 Test Schedule Update")
        
        # Test horaires valides
        new_schedule = {"hours": [9, 14, 19]}
        
        response = self.client.put(f"{self.base_url}/schedule", json=new_schedule)
        assert response.status_code == 200
        
        data = response.json()
        assert data["new_schedule"] == [9, 14, 19]  # Doit être trié
        print(f"✅ Update schedule OK: {data['new_schedule']}")
        
        # Test horaires invalides
        invalid_schedule = {"hours": [25, -1]}
        
        response = self.client.put(f"{self.base_url}/schedule", json=invalid_schedule)
        assert response.status_code == 400
        print("✅ Validation horaires invalides OK")
        
        # Remettre horaires par défaut
        default_schedule = {"hours": [8, 15, 20]}
        self.client.put(f"{self.base_url}/schedule", json=default_schedule)
        
        return True
    
    def test_metrics_endpoint(self):
        """Test endpoint des métriques"""
        print("\n🔍 Test Metrics Endpoint")
        
        response = self.client.get(f"{self.base_url}/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "timestamp" in data
        
        metrics = data["data"]
        expected_fields = ["date", "runs_completed", "products_discovered", "tokens_consumed"]
        
        for field in expected_fields:
            assert field in metrics, f"Champ métrique manquant: {field}"
        
        print(f"✅ Métriques OK - Runs: {metrics['runs_completed']}, Produits: {metrics['products_discovered']}")
        return True
    
    def test_error_handling(self):
        """Test gestion d'erreurs"""
        print("\n🔍 Test Error Handling")
        
        # Test pause avec date invalide
        invalid_pause = {"pause_until": "invalid-date"}
        
        response = self.client.post(f"{self.base_url}/pause", json=invalid_pause)
        assert response.status_code == 400
        print("✅ Gestion erreur date invalide OK")
        
        # Test pause avec date passée
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        past_pause = {"pause_until": yesterday}
        
        response = self.client.post(f"{self.base_url}/pause", json=past_pause)
        assert response.status_code == 400
        print("✅ Gestion erreur date passée OK")
        
        return True

def run_api_tests():
    """Execute tous les tests d'API"""
    print("🚀 TEST APIs DE CONTRÔLE AUTOSCHEDULER")
    print("=" * 50)
    
    tester = AutoSchedulerAPITester()
    
    tests = [
        ("Health Check", tester.test_health_check),
        ("Get Status", tester.test_get_status),
        ("Enable/Disable", tester.test_enable_disable),
        ("Pause Functionality", tester.test_pause_functionality),
        ("Schedule Update", tester.test_schedule_update),
        ("Metrics Endpoint", tester.test_metrics_endpoint),
        ("Error Handling", tester.test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, True, None))
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            results.append((test_name, False, str(e)))
    
    # Résumé
    print("\n📊 RÉSULTATS TESTS APIs")
    print("=" * 40)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if error:
            print(f"    Erreur: {error}")
    
    print(f"\n📈 SCORE: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 TOUTES LES APIs DE CONTRÔLE FONCTIONNENT !")
        print("\n📋 APIs disponibles:")
        print("GET    /api/v1/autoscheduler/status      - État actuel")
        print("POST   /api/v1/autoscheduler/enable      - Activer")
        print("POST   /api/v1/autoscheduler/disable     - Désactiver")
        print("POST   /api/v1/autoscheduler/pause       - Pause jusqu'à date")
        print("POST   /api/v1/autoscheduler/pause-today - Pause aujourd'hui")
        print("PUT    /api/v1/autoscheduler/schedule    - Modifier horaires")
        print("GET    /api/v1/autoscheduler/metrics     - Métriques du jour")
        print("GET    /api/v1/autoscheduler/health      - Health check")
    else:
        print("⚠️ Certains tests ont échoué - corrections nécessaires")
    
    return passed == total

if __name__ == "__main__":
    success = run_api_tests()
    sys.exit(0 if success else 1)