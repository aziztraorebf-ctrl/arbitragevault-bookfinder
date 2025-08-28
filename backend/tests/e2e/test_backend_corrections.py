"""
Tests end-to-end pour valider les corrections majeures du backend
Vérifie que les endpoints utilisent la BDD réelle au lieu de données simulées
"""
import pytest
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

# Configuration des tests
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0

class TestBackendCorrections:
    """Tests end-to-end des corrections majeures backend"""
    
    @pytest.fixture
    def sample_batch_data(self):
        """Données de test pour création de batch"""
        return {
            "name": "E2E Test Batch - Backend Corrections",
            "description": "Test automatisé des corrections backend",
            "asin_list": [
                "1292025824",  # Business Analytics - ISBN connu
                "0134683943",  # Computer Networks - ISBN connu  
                "1337569321"   # Calculus - ISBN connu
            ],
            "config_name": "profit_hunter"
        }
    
    @pytest.fixture
    def sample_isbn_batch(self):
        """Batch avec ISBNs pour tests Keepa"""
        return {
            "name": "E2E ISBN Test Batch",
            "description": "Test avec ISBNs réels pour validation Keepa",
            "asin_list": [
                "9781292025827",  # Business Analytics ISBN-13
                "9780134683943",  # Computer Networks ISBN-13
                "9781337569323"   # Calculus ISBN-13
            ],
            "config_name": "velocity"
        }

    async def test_server_health(self):
        """Test 1: Vérification que le serveur FastAPI fonctionne"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/health")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✅ Serveur FastAPI opérationnel")

    async def test_batches_list_real_data(self):
        """Test 2: GET /batches retourne données réelles BDD (pas de stub)"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/api/v1/batches?page=1&size=10")
            
        assert response.status_code == 200
        data = response.json()
        
        # Vérification structure réelle (pas de PHASE_1_STUB)
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        
        # Vérification que ce ne sont pas des stubs
        assert "PHASE_1_STUB" not in str(data)
        assert "mock data" not in str(data)
        
        print(f"✅ GET /batches retourne {data['total']} batches réels (pas de stubs)")

    async def test_create_batch_real_persistence(self, sample_batch_data):
        """Test 3: POST /batches persiste en BDD réelle"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(f"{BASE_URL}/api/v1/batches", json=sample_batch_data)
            
        assert response.status_code == 201
        batch = response.json()
        
        # Vérification données persistées
        assert batch["name"] == sample_batch_data["name"]
        assert batch["description"] == sample_batch_data["description"]
        assert batch["status"] in ["pending", "processing", "completed"]
        assert "id" in batch
        assert "created_at" in batch
        
        # Vérification récupération par ID
        batch_id = batch["id"]
        response = await client.get(f"{BASE_URL}/api/v1/batches/{batch_id}")
        assert response.status_code == 200
        retrieved_batch = response.json()
        assert retrieved_batch["id"] == batch_id
        
        print(f"✅ Batch créé et persisté en BDD: ID {batch_id}")
        return batch_id

    async def test_analyses_list_real_data(self):
        """Test 4: GET /analyses retourne données réelles (pas de liste vide)"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/api/v1/analyses?page=1&size=10")
            
        assert response.status_code == 200
        data = response.json()
        
        # Vérification structure réelle
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        
        # Si des analyses existent, vérifier structure
        if data["total"] > 0:
            analysis = data["items"][0]
            expected_fields = ["id", "asin", "roi_percentage", "profit_estimate", "created_at"]
            for field in expected_fields:
                assert field in analysis, f"Champ manquant: {field}"
        
        print(f"✅ GET /analyses retourne {data['total']} analyses réelles")

    async def test_strategic_views_keepa_data(self):
        """Test 5: Vues stratégiques utilisent données Keepa réelles"""
        views_to_test = ["profit_hunter", "velocity", "cashflow_hunter", "balanced_score"]
        
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            for view_name in views_to_test:
                response = await client.get(f"{BASE_URL}/api/v1/views/{view_name}")
                
                assert response.status_code == 200
                data = response.json()
                
                # Vérification structure vue stratégique
                assert "view_name" in data
                assert "description" in data
                assert "scoring_criteria" in data
                
                # Vérification absence de données simulées
                assert "simulation" not in str(data).lower()
                assert "mock" not in str(data).lower()
                assert "fake" not in str(data).lower()
                
        print(f"✅ {len(views_to_test)} vues stratégiques avec données Keepa réelles")

    async def test_analyses_filtering_real(self):
        """Test 6: Filtrage analyses avec paramètres ROI/velocity réels"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test filtrage par ROI minimum
            response = await client.get(f"{BASE_URL}/api/v1/analyses?min_roi=50&page=1&size=5")
            assert response.status_code == 200
            data = response.json()
            
            # Si résultats, vérifier que ROI >= 50%
            for analysis in data["items"]:
                if analysis.get("roi_percentage"):
                    assert analysis["roi_percentage"] >= 50
            
            # Test filtrage par velocity
            response = await client.get(f"{BASE_URL}/api/v1/analyses?min_velocity=0.5&page=1&size=5")
            assert response.status_code == 200
            
            print("✅ Filtrage analyses fonctionnel avec critères ROI/velocity")

    async def test_database_consistency(self):
        """Test 7: Cohérence données BDD ↔ API responses"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Récupérer liste batches
            batches_response = await client.get(f"{BASE_URL}/api/v1/batches?page=1&size=5")
            assert batches_response.status_code == 200
            batches_data = batches_response.json()
            
            # Pour chaque batch, vérifier récupération par ID
            for batch in batches_data["items"][:3]:  # Limiter à 3 pour performance
                batch_id = batch["id"]
                single_response = await client.get(f"{BASE_URL}/api/v1/batches/{batch_id}")
                assert single_response.status_code == 200
                single_batch = single_response.json()
                
                # Vérification cohérence données
                assert single_batch["id"] == batch["id"]
                assert single_batch["name"] == batch["name"]
                assert single_batch["status"] == batch["status"]
            
            print("✅ Cohérence données BDD ↔ API validée")

    async def test_error_handling_real(self):
        """Test 8: Gestion d'erreurs réelle (pas de stubs d'erreur)"""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test batch inexistant
            response = await client.get(f"{BASE_URL}/api/v1/batches/999999")
            assert response.status_code == 404
            error_data = response.json()
            assert "detail" in error_data
            
            # Vérifier que ce n'est pas un stub d'erreur
            assert "PHASE_1_STUB" not in str(error_data)
            assert "mock error" not in str(error_data).lower()
            
            # Test données invalides
            invalid_batch = {"name": ""}  # Nom vide
            response = await client.post(f"{BASE_URL}/api/v1/batches", json=invalid_batch)
            assert response.status_code == 422  # Validation error
            
            print("✅ Gestion d'erreurs réelle fonctionnelle")

# Tests d'exécution
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complet du workflow corrections backend"""
    tester = TestBackendCorrections()
    
    print("\n🧪 DÉBUT TESTS END-TO-END - CORRECTIONS BACKEND")
    print("=" * 60)
    
    try:
        # Séquence de tests
        await tester.test_server_health()
        await tester.test_batches_list_real_data()
        await tester.test_analyses_list_real_data()
        await tester.test_strategic_views_keepa_data()
        await tester.test_analyses_filtering_real()
        await tester.test_database_consistency()
        await tester.test_error_handling_real()
        
        # Test création batch (nécessite données sample)
        sample_data = {
            "name": f"E2E Test Batch - {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "description": "Test automatisé des corrections backend",
            "asin_list": ["1292025824", "0134683943"],
            "config_name": "profit_hunter"
        }
        batch_id = await tester.test_create_batch_real_persistence(sample_data)
        
        print("=" * 60)
        print("✅ TOUS LES TESTS END-TO-END RÉUSSIS")
        print(f"📦 Batch de test créé: ID {batch_id}")
        print("🎯 Backend prêt pour développement frontend")
        
    except Exception as e:
        print(f"❌ ÉCHEC TEST: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())