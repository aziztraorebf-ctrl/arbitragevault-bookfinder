#!/usr/bin/env python3
"""
Test Simulation - Niche Discovery Phase 1 KISS
===============================================

Script de validation de la logique Niche Discovery sans appeler l'API Keepa.
Utilise des données simulées pour valider les calculs et le workflow.
"""

import sys
import asyncio
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.models.niche import NicheAnalysisCriteria, NicheAnalysisRequest
from app.services.niche_scoring_service import NicheScoringService
from app.services.category_analyzer import CategoryAnalyzer
from unittest.mock import Mock


class NicheDiscoverySimulator:
    """Simulateur pour tester Niche Discovery sans API calls."""
    
    def __init__(self):
        self.scoring_service = NicheScoringService()
        # Mock Keepa service pour éviter appels API
        self.mock_keepa = Mock()
        self.category_analyzer = CategoryAnalyzer(self.mock_keepa)
    
    def test_scoring_algorithms(self):
        """Test des algorithmes de scoring avec données simulées."""
        print("🧮 TEST ALGORITHMES DE SCORING")
        print("=" * 50)
        
        criteria = NicheAnalysisCriteria(
            bsr_range=(15000, 45000),
            max_sellers=3,
            min_margin_percent=25.0,
            min_price_stability=0.70
        )
        
        # Simuler différents types de niches
        test_scenarios = [
            {
                "name": "Niche Excellente (Medical Textbooks)",
                "metrics": {
                    "avg_sellers": 1.8,
                    "avg_bsr": 28000,
                    "avg_price": 95.0,
                    "price_stability": 0.88,
                    "profit_margin": 42.0,
                    "total_products": 60,
                    "viable_products": 48  # 80%
                }
            },
            {
                "name": "Niche Correcte (Engineering Books)",
                "metrics": {
                    "avg_sellers": 3.2,
                    "avg_bsr": 35000,
                    "avg_price": 78.0,
                    "price_stability": 0.75,
                    "profit_margin": 28.5,
                    "total_products": 40,
                    "viable_products": 24  # 60%
                }
            },
            {
                "name": "Niche Médiocre (General Fiction)",
                "metrics": {
                    "avg_sellers": 8.5,
                    "avg_bsr": 25000,
                    "avg_price": 14.99,
                    "price_stability": 0.45,
                    "profit_margin": 12.0,
                    "total_products": 100,
                    "viable_products": 8  # 8%
                }
            }
        ]
        
        for scenario in test_scenarios:
            from app.models.niche import NicheMetrics
            
            metrics = NicheMetrics(
                competition_level="",
                **scenario["metrics"]
            )
            
            score, confidence, quality = self.scoring_service.calculate_niche_score(
                metrics, criteria
            )
            
            competition_level = self.scoring_service.classify_competition_level(
                metrics.avg_sellers
            )
            
            print(f"\n📊 {scenario['name']}")
            print(f"   Score Global    : {score}/10")
            print(f"   Concurrence     : {competition_level} ({metrics.avg_sellers:.1f} vendeurs)")
            print(f"   BSR Moyen       : {metrics.avg_bsr:,}")
            print(f"   Marge Profit    : {metrics.profit_margin:.1f}%")
            print(f"   Stabilité Prix  : {metrics.price_stability:.2f}")
            print(f"   Produits Viables: {metrics.viable_products}/{metrics.total_products} ({metrics.viable_products/metrics.total_products*100:.1f}%)")
            print(f"   Confiance       : {confidence}")
            print(f"   Qualité         : {quality}")
            
        return True
    
    def test_category_analysis_logic(self):
        """Test de la logique d'analyse des catégories."""
        print("\n📚 TEST LOGIQUE ANALYSE CATÉGORIES")
        print("=" * 50)
        
        # Test disponibilité des catégories
        categories = self.category_analyzer.get_available_categories()
        print(f"✅ Catégories disponibles : {len(categories)}")
        
        for cat in categories[:5]:  # Afficher les 5 premières
            print(f"   • {cat.category_name} (ID: {cat.category_id})")
        
        # Test catégories recommandées
        recommended = self.category_analyzer.get_recommended_categories()
        print(f"\n✅ Catégories recommandées : {len(recommended)}")
        
        # Test génération d'échantillons ASIN
        for cat_id in recommended[:3]:
            sample_asins = self.category_analyzer._get_sample_asins_for_category(cat_id)
            cat_name = self.category_analyzer.target_categories.get(cat_id, f"Category {cat_id}")
            print(f"   • {cat_name}: {len(sample_asins)} ASINs d'échantillon")
        
        return True
    
    def test_product_analysis_methods(self):
        """Test des méthodes d'analyse de produits."""
        print("\n🔍 TEST MÉTHODES ANALYSE PRODUITS")
        print("=" * 50)
        
        # Simuler un produit Keepa typique
        sample_product = {
            'asin': 'B123456789',
            'title': 'Advanced Medical Procedures Textbook',
            'availabilityAmazon': 0,  # En stock
            'salesRanks': {1000: 25000},  # BSR Books = 25k
            'salesRankReference': 25000,
            'csv': [
                # csv[0] = Prix Amazon (centimes)
                [7500, 7600, 7550, 7580, 7520, 7590, 7570],
                # csv[1] = Prix NEW
                [8200, 8300, 8250, 8280, 8220, 8290],
                # csv[2] = Prix USED  
                [5500, 5600, 5550, 5580, 5520]
            ]
        }
        
        # Test extraction BSR
        bsr = self.category_analyzer._extract_bsr(sample_product)
        print(f"✅ BSR extrait : {bsr:,}")
        
        # Test extraction prix
        price = self.category_analyzer._extract_current_price(sample_product)
        print(f"✅ Prix actuel : ${price:.2f}")
        
        # Test estimation vendeurs
        sellers = self.category_analyzer._estimate_seller_count(sample_product)
        print(f"✅ Vendeurs estimés : {sellers:.1f}")
        
        # Test stabilité prix
        stability = self.category_analyzer._calculate_price_stability(sample_product)
        print(f"✅ Stabilité prix : {stability:.3f}")
        
        # Test estimation marge
        criteria = NicheAnalysisCriteria()
        margin = self.category_analyzer._estimate_profit_margin(sample_product, criteria)
        print(f"✅ Marge profit estimée : {margin:.1f}%")
        
        # Test viabilité
        viable = self.category_analyzer._is_product_viable(sample_product, criteria)
        print(f"✅ Produit viable : {'Oui' if viable else 'Non'}")
        
        return True
    
    def test_export_functionality(self):
        """Test des fonctionnalités d'export."""
        print("\n📤 TEST EXPORT DONNÉES")  
        print("=" * 50)
        
        # Simuler quelques niches découvertes
        from app.models.niche import DiscoveredNiche, NicheMetrics
        
        sample_niches = []
        for i, (name, score) in enumerate([
            ("Medical Textbooks", 8.7),
            ("Engineering Manuals", 7.2),
            ("Certification Prep", 6.8)
        ]):
            criteria = NicheAnalysisCriteria()
            metrics = NicheMetrics(
                avg_sellers=2.0 + i * 0.5,
                avg_bsr=25000 + i * 5000,
                avg_price=50.0 + i * 10,
                price_stability=0.85 - i * 0.05,
                profit_margin=35.0 - i * 3,
                total_products=50,
                viable_products=40 - i * 5,
                competition_level="Low" if i == 0 else "Medium"
            )
            
            niche = DiscoveredNiche(
                category_name=name,
                category_id=3000 + i,
                metrics=metrics,
                niche_score=score,
                confidence_level="High",
                sample_quality="Good",
                criteria_used=criteria
            )
            sample_niches.append(niche)
        
        # Test formatage pour export
        from app.services.niche_discovery_service import NicheDiscoveryService
        mock_keepa = Mock()
        service = NicheDiscoveryService(mock_keepa)
        
        # Note: export_niches_data est async mais ne fait pas d'appels API
        async def test_export():
            export_data = await service.export_niches_data(sample_niches)
            
            print(f"✅ Niches formatées pour export : {len(export_data)}")
            
            for data in export_data:
                print(f"   • {data.category_name}: Score {data.niche_score}, "
                     f"Marge {data.profit_margin:.1f}%")
            
            return len(export_data) > 0
        
        result = asyncio.run(test_export())
        return result
    
    def run_all_tests(self):
        """Exécute tous les tests de simulation."""
        print("🚀 SIMULATION NICHE DISCOVERY - PHASE 1 KISS")
        print("=" * 80)
        
        tests = [
            ("Algorithmes de Scoring", self.test_scoring_algorithms),
            ("Logique Analyse Catégories", self.test_category_analysis_logic),
            ("Méthodes Analyse Produits", self.test_product_analysis_methods),
            ("Fonctionnalité Export", self.test_export_functionality)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success, None))
                print(f"\n✅ {test_name}: {'RÉUSSI' if success else 'ÉCHOUÉ'}")
            except Exception as e:
                results.append((test_name, False, str(e)))
                print(f"\n❌ {test_name}: ERREUR - {e}")
        
        # Résumé final
        print("\n" + "=" * 80)
        print("📋 RÉSUMÉ SIMULATION")
        print("=" * 80)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_name, success, error in results:
            status = "✅ PASSÉ" if success else f"❌ ÉCHOUÉ ({error})" if error else "❌ ÉCHOUÉ"
            print(f"   {test_name:30} : {status}")
        
        print(f"\n🎯 Score Global : {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 SIMULATION COMPLÈTE : Niche Discovery Phase 1 KISS fonctionne parfaitement !")
            return True
        else:
            print("⚠️  PROBLÈMES DÉTECTÉS : Corrections nécessaires avant tests E2E.")
            return False


def main():
    """Point d'entrée principal."""
    simulator = NicheDiscoverySimulator()
    success = simulator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()