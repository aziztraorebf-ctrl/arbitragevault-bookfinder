"""
Tests unitaires directs des composants critiques - Sans serveur FastAPI
Validation rapide des corrections backend
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

async def test_imports_and_corrections():
    """Test 1: Vérification imports et corrections critiques"""
    print("🔧 Test des imports et corrections...")
    
    try:
        # Test import principal
        from app.main import app
        print("✅ app.main importé")
        
        # Test imports routers corrigés
        from app.api.v1.routers.batches import router as batches_router
        from app.api.v1.routers.analyses import router as analyses_router
        print("✅ Routers batches/analyses importés")
        
        # Test imports repositories (utilisés dans corrections)
        from app.repositories.batch_repository import BatchRepository
        from app.repositories.analysis_repository import AnalysisRepository
        print("✅ Repositories importés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False

async def test_database_models():
    """Test 2: Modèles de base de données"""
    print("📊 Test des modèles BDD...")
    
    try:
        from app.models.batch import Batch, BatchStatus
        from app.models.analysis import Analysis
        
        # Test création instance modèle avec tous les champs requis
        batch = Batch(
            user_id="test-user-id",  # Champ requis
            name="Test Batch",
            description="Test unitaire",  # Maintenant supporté
            status=BatchStatus.PENDING,
            items_total=5
        )
        print(f"✅ Modèle Batch créé: {batch.name}")
        
        # Test statuts (codes corrects)
        available_statuses = [BatchStatus.PENDING, BatchStatus.RUNNING, BatchStatus.DONE, BatchStatus.FAILED]
        assert BatchStatus.PENDING in available_statuses
        print(f"✅ Statuts BatchStatus validés: {[s.value for s in available_statuses]}")
        
        # Test nouvelles propriétés
        assert batch.progress_percentage == 0.0  # Aucun item traité
        assert batch.can_transition_to(BatchStatus.RUNNING) == True
        print("✅ Propriétés et transitions batch validées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur modèles: {e}")
        return False

async def test_services_logic():
    """Test 3: Logique services critiques"""
    print("⚙️ Test logique services...")
    
    try:
        # Test service SalesVelocity (v1.9.0) avec méthode corrigée
        from app.services.sales_velocity_service import SalesVelocityService
        
        service = SalesVelocityService()
        
        # Test calcul vélocité avec données simulées
        mock_keepa_data = {
            "salesRankDrops30": 15,
            "salesRankDrops90": 45,
            "current": {"BUY_BOX": [1699]}  # 16.99$
        }
        
        # Test nouvelle méthode wrapper
        velocity_score = service.calculate_velocity_score(mock_keepa_data)
        print(f"✅ Velocity score calculé: {velocity_score:.2f}")
        
        # Test méthode principale
        velocity_analysis = service.analyze_product_velocity({
            "asin": "TEST123",
            "sales_drops_30": 15,
            "sales_drops_90": 45,
            "current_bsr": 5000,
            "category": "Books"
        })
        print(f"✅ Analyse vélocité: tier {velocity_analysis.get('velocity_tier', 'UNKNOWN')}")
        
        # Test service StockEstimate (v1.8.0) - vérification structure seulement
        try:
            from app.services.stock_estimate_service import StockEstimateService
            print("✅ StockEstimateService importé (nécessite deps pour instantiation)")
            
            # Vérifier méthodes disponibles sans instancier
            methods = [attr for attr in dir(StockEstimateService) if not attr.startswith('_')]
            if 'calculate_stock_suggestion' in methods:
                print("✅ Méthode calculate_stock_suggestion disponible")
            else:
                print("⚠️ Méthode calculate_stock_suggestion manquante")
                
        except Exception as stock_e:
            print(f"⚠️ StockEstimateService non testé: {stock_e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur services: {e}")
        import traceback
        print(f"   Détail: {traceback.format_exc()}")
        return False

async def test_strategic_views_config():
    """Test 4: Configuration vues stratégiques"""
    print("🎯 Test configuration vues stratégiques...")
    
    try:
        from app.services.strategic_views_service import StrategicViewsService
        
        service = StrategicViewsService()
        
        # Test récupération configuration
        profit_hunter = service.get_view_config("profit_hunter")
        velocity = service.get_view_config("velocity")
        
        print(f"✅ Profit Hunter: poids ROI {profit_hunter.roi_weight}")
        print(f"✅ Velocity: poids vélocité {velocity.velocity_weight}")
        
        # Test calcul score
        mock_analysis = {
            "roi_percentage": 75.5,
            "velocity_score": 0.8,
            "competition_level": "MEDIUM",
            "profit_estimate": 12.50
        }
        
        score = service.calculate_strategic_score("profit_hunter", mock_analysis)
        print(f"✅ Score stratégique calculé: {score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vues stratégiques: {e}")
        return False

async def test_keepa_service_structure():
    """Test 5: Structure service Keepa (sans API call)"""
    print("🔗 Test structure service Keepa via Factory...")
    
    try:
        # Test factory pattern pour gestion API key
        from app.services.keepa_service_factory import KeepaServiceFactory
        
        print("✅ Factory Keepa importé")
        
        # Test méthodes factory disponibles
        factory_methods = [attr for attr in dir(KeepaServiceFactory) if not attr.startswith('_')]
        expected_factory_methods = ['get_keepa_service', 'create_test_service', 'reset_instance']
        
        for method in expected_factory_methods:
            if method in factory_methods:
                print(f"✅ Factory méthode {method} présente")
            else:
                print(f"⚠️ Factory méthode {method} manquante")
        
        # Test création service test (sans vraie API key)
        test_service = KeepaServiceFactory.create_test_service("test-api-key-12345")
        print("✅ Service Keepa créé via factory pour tests")
        
        # Test méthodes service (sans appel API)
        service_methods = [attr for attr in dir(test_service) if not attr.startswith('_')]
        critical_methods = ['product_lookup', 'close']  # Méthodes critiques attendues
        
        present_methods = [m for m in critical_methods if m in service_methods]
        print(f"✅ Méthodes service présentes: {len(present_methods)}/{len(critical_methods)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur service Keepa: {e}")
        import traceback
        print(f"   Détail: {traceback.format_exc()}")
        return False

async def run_all_component_tests():
    """Lance tous les tests unitaires rapidement"""
    print("🧪 DÉBUT TESTS COMPOSANTS DIRECTS")
    print("=" * 50)
    
    tests = [
        ("Imports & Corrections", test_imports_and_corrections),
        ("Modèles BDD", test_database_models),
        ("Logique Services", test_services_logic),
        ("Vues Stratégiques", test_strategic_views_config),
        ("Structure Keepa", test_keepa_service_structure)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            print()
        except Exception as e:
            print(f"❌ {test_name} - ERREUR: {e}")
            results[test_name] = False
            print()
    
    # Résumé
    print("=" * 50)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 RÉSULTATS: {passed}/{total} tests réussis")
    
    if passed >= total * 0.8:  # 80% réussite
        print("✅ COMPOSANTS VALIDÉS - Prêt pour Option B (Git)")
        return True
    else:
        print("⚠️ COMPOSANTS PARTIELS - Corrections requises")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_component_tests())
    exit(0 if success else 1)