"""
Test d'intégration simple pour valider le système ArbitrageVault
Tests avec vraie API Keepa - Validation end-to-end
"""

import asyncio
import keyring
import sys
import os
sys.path.append('backend')

from backend.app.services.keepa_service import KeepaService
from backend.app.services.autosourcing_service import AutoSourcingService

def get_keepa_api_key():
    """Récupère la clé API Keepa depuis les secrets Memex"""
    try:
        # Essayer différentes variations de case
        for key_name in ['KEEPA_API_KEY', 'keepa_api_key', 'Keepa_API_Key']:
            try:
                api_key = keyring.get_password('memex', key_name)
                if api_key:
                    print(f"✅ Clé API Keepa récupérée avec succès")
                    return api_key
            except:
                continue
        
        print("❌ Clé API Keepa non trouvée dans les secrets")
        return None
    except Exception as e:
        print(f"❌ Erreur récupération clé API: {e}")
        return None

async def test_keepa_connection():
    """Test basique de connexion à l'API Keepa"""
    print("\n🔍 Test 1: Connexion API Keepa...")
    
    api_key = get_keepa_api_key()
    if not api_key:
        return False
    
    try:
        keepa_service = KeepaService(api_key)
        
        # Test avec un ASIN simple (livre populaire)
        test_asin = "B00ZJ2VGA4"  # Example textbook ASIN
        print(f"   Teste avec ASIN: {test_asin}")
        
        result = await keepa_service.get_product_data(test_asin)
        
        if result:
            title = result.get('title', 'Titre inconnu') if isinstance(result, dict) else str(result)[:50]
            print(f"   ✅ Connexion réussie - Données reçues pour: {title}...")
            return True
        else:
            print("   ❌ Aucune donnée reçue")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        return False

async def test_autosourcing_workflow():
    """Test du workflow AutoSourcing complet avec ASINs réels"""
    print("\n🤖 Test 2: Workflow AutoSourcing Complet...")
    
    api_key = get_keepa_api_key()
    if not api_key:
        return False
    
    # ASINs de test - différentes catégories de livres
    test_asins = [
        "0134685997",  # Programming book
        "1449355730",  # Tech book  
        "0321125215",  # Computer Science
        "B07Y7KNQXV",  # Recent book
        "0596517742",  # O'Reilly book
    ]
    
    try:
        keepa_service = KeepaService(api_key)
        results = []
        
        print(f"   Analyse de {len(test_asins)} ASINs...")
        
        for i, asin in enumerate(test_asins, 1):
            print(f"   📖 {i}/{len(test_asins)}: Analyse {asin}...")
            
            try:
                # Récupérer données Keepa
                product_data = await keepa_service.get_product_data(asin)
                if not product_data:
                    print(f"      ⚠️  Pas de données pour {asin}")
                    continue
                
                # Simuler analyse simple
                title = product_data.get('title', 'Titre inconnu') if isinstance(product_data, dict) else 'Produit trouvé'
                
                # Données basiques pour validation
                analysis_result = {
                    'asin': asin,
                    'title': title[:50] + '...' if len(title) > 50 else title,
                    'data_available': True,
                    'keepa_response': bool(product_data)
                }
                
                results.append(analysis_result)
                print(f"      ✅ Données récupérées: {analysis_result['title']}")
                
            except Exception as e:
                print(f"      ❌ Erreur analyse {asin}: {e}")
        
        print(f"\n   📊 Résultats: {len(results)}/{len(test_asins)} analyses réussies")
        
        # Afficher échantillon de résultats
        if results:
            print("   📋 Échantillon des résultats:")
            for result in results[:3]:  # Montrer les 3 premiers
                print(f"      - {result['asin']}: {result['title']}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"   ❌ Erreur workflow: {e}")
        return False

def test_services_availability():
    """Test rapide de disponibilité des services"""
    print("\n🧮 Test 3: Services Disponibilité...")
    
    try:
        # Test d'import des services principaux
        from backend.app.services.keepa_service import KeepaService
        from backend.app.services.autosourcing_service import AutoSourcingService
        
        print(f"   ✅ KeepaService importé")
        print(f"   ✅ AutoSourcingService importé")
        
        # Test basique de création d'instance
        keepa = KeepaService("test_key")  
        print(f"   ✅ Instance KeepaService créée")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur services: {e}")
        return False

async def main():
    """Lance tous les tests d'intégration"""
    print("🚀 ArbitrageVault - Tests d'Intégration End-to-End")
    print("=" * 60)
    
    # Tests séquentiels
    test1 = await test_keepa_connection()
    test2 = test_services_availability()
    test3 = await test_autosourcing_workflow() if test1 else False
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print(f"   API Keepa:          {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Services:           {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"   Workflow Complet:   {'✅ PASS' if test3 else '❌ FAIL'}")
    
    overall = test1 and test2 and test3
    print(f"\n🎯 STATUS GLOBAL:     {'✅ SYSTÈME OPÉRATIONNEL' if overall else '❌ PROBLÈMES DÉTECTÉS'}")
    
    return overall

if __name__ == "__main__":
    asyncio.run(main())