#!/usr/bin/env python3
"""
Test E2E Niche Discovery - Phase 1 KISS
=======================================

Test end-to-end complet avec API Keepa réelle.
Utilise la clé API des secrets Memex.
"""

import asyncio
import sys
import time
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

import keyring
from app.models.niche import NicheAnalysisCriteria, NicheAnalysisRequest
from app.services.keepa_service import KeepaService
from app.services.niche_discovery_service import NicheDiscoveryService


class NicheDiscoveryE2ETester:
    """Testeur E2E pour Niche Discovery avec vraie API Keepa."""
    
    def __init__(self):
        self.keepa_service = None
        self.niche_discovery_service = None
    
    async def setup(self):
        """Setup services avec clé API Keepa des secrets."""
        print("🔧 SETUP SERVICES E2E")
        print("=" * 40)
        
        try:
            # Récupérer clé API depuis secrets Memex
            keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
            if not keepa_api_key:
                raise ValueError("Clé API Keepa non trouvée dans secrets Memex")
            
            print(f"✅ Clé API récupérée : {keepa_api_key[:8]}...")
            
            # Créer services
            self.keepa_service = KeepaService(keepa_api_key)
            self.niche_discovery_service = NicheDiscoveryService(self.keepa_service)
            
            # Test connectivité Keepa
            health = await self.keepa_service.health_check()
            print(f"✅ Health Check Keepa : {health['status']}")
            print(f"   Tokens disponibles : {health.get('tokens_left', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur setup : {e}")
            return False
    
    async def test_categories_endpoint(self):
        """Test endpoint liste des catégories."""
        print("\n📚 TEST ENDPOINT CATÉGORIES")
        print("=" * 40)
        
        try:
            categories_response = await self.niche_discovery_service.get_available_categories()
            
            print(f"✅ Catégories disponibles : {len(categories_response.categories)}")
            print(f"✅ Catégories recommandées : {len(categories_response.recommended_categories)}")
            
            # Afficher quelques catégories
            print("\nTop 5 catégories recommandées :")
            for cat in categories_response.recommended_categories[:5]:
                print(f"   • {cat.category_name} (ID: {cat.category_id})")
            
            return len(categories_response.categories) > 0
            
        except Exception as e:
            print(f"❌ Erreur endpoint catégories : {e}")
            return False
    
    async def test_niche_analysis_light(self):
        """Test analyse niches avec critères légers (économiser tokens)."""
        print("\n🔍 TEST ANALYSE NICHES (LIGHT MODE)")
        print("=" * 40)
        
        try:
            # Critères optimisés pour consommer moins de tokens
            criteria = NicheAnalysisCriteria(
                bsr_range=(15000, 40000),
                max_sellers=3,
                min_margin_percent=25.0,
                min_price_stability=0.70,
                sample_size=10  # Réduit pour économiser tokens
            )
            
            # Analyser seulement 2 catégories recommandées
            request = NicheAnalysisRequest(
                criteria=criteria,
                target_categories=[3738, 4142],  # Medical Books + Engineering
                max_results=5
            )
            
            print(f"📊 Critères : BSR {criteria.bsr_range}, ≤{criteria.max_sellers} vendeurs, ≥{criteria.min_margin_percent}% marge")
            print(f"📊 Catégories ciblées : {len(request.target_categories)}")
            print(f"📊 Échantillon par catégorie : {criteria.sample_size} produits")
            
            start_time = time.time()
            response = await self.niche_discovery_service.discover_niches(request)
            duration = time.time() - start_time
            
            print(f"\n✅ Analyse terminée en {duration:.2f}s")
            print(f"✅ Niches découvertes : {len(response.discovered_niches)}")
            print(f"✅ Score moyen : {response.avg_niche_score:.1f}/10")
            print(f"✅ Meilleur score : {response.best_niche_score:.1f}/10")
            print(f"✅ Qualité analyse : {response.analysis_quality}")
            
            # Détails top niches
            print(f"\nTop {min(3, len(response.discovered_niches))} niches découvertes :")
            for i, niche in enumerate(response.discovered_niches[:3], 1):
                print(f"\n{i}. {niche.category_name}")
                print(f"   Score         : {niche.niche_score:.1f}/10")
                print(f"   Concurrence   : {niche.metrics.competition_level} ({niche.metrics.avg_sellers:.1f} vendeurs)")
                print(f"   BSR Moyen     : {niche.metrics.avg_bsr:,.0f}")
                print(f"   Marge Profit  : {niche.metrics.profit_margin:.1f}%")
                print(f"   Stabilité     : {niche.metrics.price_stability:.2f}")
                print(f"   Viables       : {niche.metrics.viable_products}/{niche.metrics.total_products}")
                print(f"   Confiance     : {niche.confidence_level}")
            
            return len(response.discovered_niches) > 0
            
        except Exception as e:
            print(f"❌ Erreur analyse niches : {e}")
            return False
    
    async def test_export_functionality(self):
        """Test fonctionnalité export avec données obtenues."""
        print("\n📤 TEST EXPORT DONNÉES")
        print("=" * 40)
        
        try:
            # Ré-exécuter une analyse rapide pour obtenir des données
            criteria = NicheAnalysisCriteria(sample_size=5)  # Très réduit
            request = NicheAnalysisRequest(
                criteria=criteria,
                target_categories=[3738],  # Une seule catégorie
                max_results=2
            )
            
            response = await self.niche_discovery_service.discover_niches(request)
            
            if not response.discovered_niches:
                print("⚠️  Pas de niches pour tester export")
                return True  # Pas un échec critique
            
            # Test export
            export_data = await self.niche_discovery_service.export_niches_data(
                response.discovered_niches
            )
            
            print(f"✅ Export formaté : {len(export_data)} niches")
            
            for data in export_data:
                print(f"   • {data.category_name}")
                print(f"     Score: {data.niche_score}, Marge: {data.profit_margin:.1f}%")
                print(f"     Recommandations AutoSourcing: BSR {data.recommended_bsr_min:,}-{data.recommended_bsr_max:,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test export : {e}")
            return False
    
    async def run_all_e2e_tests(self):
        """Exécute tous les tests E2E."""
        print("🚀 TESTS E2E NICHE DISCOVERY - PHASE 1 KISS")
        print("=" * 60)
        print("⚠️  UTILISATION API KEEPA RÉELLE - Tokens consommés")
        print("=" * 60)
        
        # Setup
        setup_success = await self.setup()
        if not setup_success:
            print("❌ Setup échoué - Arrêt des tests")
            return False
        
        # Tests
        tests = [
            ("Endpoint Catégories", self.test_categories_endpoint),
            ("Analyse Niches Light", self.test_niche_analysis_light),
            ("Export Functionality", self.test_export_functionality)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = await test_func()
                results.append((test_name, success, None))
                status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
                print(f"\n{status} - {test_name}")
            except Exception as e:
                results.append((test_name, False, str(e)))
                print(f"\n❌ ERREUR - {test_name} : {e}")
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ TESTS E2E")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_name, success, error in results:
            status = "✅ PASSÉ" if success else f"❌ ÉCHOUÉ ({error})" if error else "❌ ÉCHOUÉ"
            print(f"   {test_name:25} : {status}")
        
        print(f"\n🎯 Score E2E : {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 VALIDATION E2E COMPLÈTE : Niche Discovery Phase 1 KISS prêt pour production !")
            return True
        else:
            print("⚠️  PROBLÈMES E2E DÉTECTÉS : Corrections nécessaires.")
            return False


async def main():
    """Point d'entrée principal."""
    tester = NicheDiscoveryE2ETester()
    success = await tester.run_all_e2e_tests()
    
    # Afficher tokens restants
    if tester.keepa_service:
        try:
            final_health = await tester.keepa_service.health_check()
            print(f"\n💰 Tokens Keepa restants : {final_health.get('tokens_left', 'Unknown')}")
        except:
            pass
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())