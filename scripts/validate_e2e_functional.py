#!/usr/bin/env python3
"""
Validation Fonctionnelle End-to-End du AmazonFilterService
==========================================================

Ce script teste le AmazonFilterService avec des données réelles de l'API Keepa
pour valider que le filtrage fonctionne correctement selon différents scénarios.

Scénarios testés :
1. ASIN avec Amazon présent comme vendeur
2. ASIN avec Amazon absent (vendeurs tiers uniquement)
3. ASIN invalide/inexistant
"""

import os
import sys
import asyncio
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

import keyring
from app.services.amazon_filter_service import AmazonFilterService
from app.services.keepa_service import KeepaService

class FunctionalValidator:
    def __init__(self):
        # Récupérer la clé API depuis keyring
        try:
            keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
            if not keepa_api_key:
                raise ValueError("Clé API Keepa non configurée dans keyring")
        except Exception as e:
            raise ValueError(f"Impossible de récupérer la clé Keepa : {e}")
        
        self.keepa_service = KeepaService(keepa_api_key)
        self.amazon_filter = AmazonFilterService()
        
        # ASINs de test pour différents scénarios
        self.test_cases = {
            "amazon_present": {
                "asin": "1250301696",  # Livre avec forte probabilité Amazon  
                "description": "Livre bestseller - forte probabilité Amazon présent",
                "expected_filtered": True
            },
            "amazon_absent": {
                "asin": "0316769487",  # Livre plus ancien, vendeurs tiers
                "description": "Livre ancien - vendeurs tiers probables",
                "expected_filtered": False
            },
            "invalid_asin": {
                "asin": "INVALID123",
                "description": "ASIN invalide - Doit gérer l'erreur proprement",
                "expected_filtered": None  # Erreur attendue
            }
        }

    async def validate_scenario(self, scenario_name: str, test_case: dict):
        """Valide un scénario de test spécifique."""
        print(f"\n{'='*60}")
        print(f"🧪 TEST : {scenario_name.upper()}")
        print(f"📦 ASIN : {test_case['asin']}")
        print(f"📝 Description : {test_case['description']}")
        print(f"🎯 Résultat Attendu : {'Filtré' if test_case['expected_filtered'] else 'Non Filtré' if test_case['expected_filtered'] is False else 'Erreur Gérée'}")
        print(f"{'='*60}")

        try:
            # Récupérer les données depuis Keepa (un seul ASIN à la fois)
            print("🔄 Récupération des données Keepa...")
            product_data = await self.keepa_service.get_product_data(test_case['asin'])
            
            if not product_data:
                print("❌ ERREUR : Aucune donnée retournée par Keepa")
                return False
            print(f"✅ Données récupérées pour : {product_data.get('title', 'Titre non disponible')[:50]}...")
            
            # Afficher les indicateurs Amazon détectés
            self._display_amazon_indicators(product_data)
            
            # Tester le filtrage
            print("\n🔍 Test du filtrage Amazon...")
            filter_result = self.amazon_filter.filter_amazon_products([product_data])
            
            # Le service retourne maintenant un dictionnaire avec 'products'
            filtered_products = filter_result.get('products', [])
            is_filtered = len(filtered_products) == 0  # Si la liste est vide, le produit a été filtré
            
            # Afficher les métriques de filtrage
            if 'filter_rate_percentage' in filter_result:
                print(f"📊 Taux de filtrage : {filter_result['filter_rate_percentage']}%")
            if 'filter_impact' in filter_result:
                print(f"📋 Impact : {filter_result['filter_impact']}")
            
            print(f"📊 Résultat : {'Filtré (Amazon détecté)' if is_filtered else 'Non Filtré (Amazon non détecté)'}")
            
            # Vérifier si le résultat correspond aux attentes
            success = is_filtered == test_case['expected_filtered']
            status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
            
            print(f"\n{status} - Le comportement {'correspond' if success else 'ne correspond PAS'} aux attentes")
            
            return success
            
        except Exception as e:
            print(f"⚠️  EXCEPTION : {str(e)}")
            
            # Pour un ASIN invalide, une exception est acceptable
            if test_case['expected_filtered'] is None:
                print("✅ Exception attendue pour ASIN invalide - SUCCÈS")
                return True
            else:
                print("❌ Exception inattendue - ÉCHEC")
                return False

    def _display_amazon_indicators(self, product_data: dict):
        """Affiche les indicateurs utilisés pour détecter Amazon."""
        print("\n🔍 Indicateurs Amazon détectés :")
        
        # availabilityAmazon
        availability = product_data.get('availabilityAmazon', 'Non disponible')
        print(f"   • availabilityAmazon : {availability}")
        
        # csv (price history)
        csv_data = product_data.get('csv', [])
        has_price_history = len(csv_data) > 0
        print(f"   • Historique prix CSV : {'Présent' if has_price_history else 'Absent'} ({len(csv_data)} points)")
        
        # buyBoxSellerIdHistory
        buybox_history = product_data.get('buyBoxSellerIdHistory') or []
        has_buybox_amazon = False
        if buybox_history:
            has_buybox_amazon = any(seller_id == 1 for seller_id in buybox_history if isinstance(seller_id, int))
        print(f"   • Historique Buy Box Amazon : {'Détecté' if has_buybox_amazon else 'Non détecté'} ({buybox_history})")

    async def run_all_tests(self):
        """Exécute tous les tests de validation."""
        print("🚀 VALIDATION FONCTIONNELLE E2E - AmazonFilterService")
        print("=" * 80)
        
        print("🔑 Clé API Keepa configurée et prête")
        
        results = {}
        
        # Exécuter chaque test
        for scenario_name, test_case in self.test_cases.items():
            results[scenario_name] = await self.validate_scenario(scenario_name, test_case)
        
        # Résumé des résultats
        print(f"\n{'='*80}")
        print("📋 RÉSUMÉ DES TESTS")
        print(f"{'='*80}")
        
        total_tests = len(results)
        successful_tests = sum(results.values())
        
        for scenario_name, success in results.items():
            status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
            print(f"   {scenario_name:20} : {status}")
        
        print(f"\n🎯 Score Global : {successful_tests}/{total_tests} tests réussis")
        
        if successful_tests == total_tests:
            print("🎉 VALIDATION COMPLÈTE : Le AmazonFilterService fonctionne correctement !")
            return True
        else:
            print("⚠️  PROBLÈMES DÉTECTÉS : Des corrections sont nécessaires.")
            return False

async def main():
    """Point d'entrée principal."""
    validator = FunctionalValidator()
    success = await validator.run_all_tests()
    
    # Code de sortie pour intégration CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())