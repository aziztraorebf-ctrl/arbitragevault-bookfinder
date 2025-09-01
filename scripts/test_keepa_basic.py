#!/usr/bin/env python3
"""
Test basique de connectivité Keepa API
======================================
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

import keyring
from app.services.keepa_service import KeepaService

async def test_keepa_connectivity():
    """Test basique de l'API Keepa."""
    print("🔧 Test de connectivité Keepa API")
    print("=" * 50)
    
    try:
        # Récupérer la clé API
        keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
        if not keepa_api_key:
            print("❌ Clé API Keepa non trouvée dans keyring")
            return False
        
        print(f"✅ Clé API récupérée : {keepa_api_key[:8]}...")
        
        # Créer le service
        keepa_service = KeepaService(keepa_api_key)
        
        # Test health check
        print("\n🏥 Test health check...")
        health = await keepa_service.health_check()
        print(f"Health check : {health}")
        
        # Test avec un ASIN simple et connu
        test_asin = "B000F83SZQ"  # Un livre Amazon classique
        print(f"\n📚 Test avec ASIN : {test_asin}")
        
        result = await keepa_service.get_product_data([test_asin])
        
        print(f"Type de résultat : {type(result)}")
        
        # Debug : affichage structure complète mais limitée
        if isinstance(result, dict):
            print("Clés principales du dictionnaire :")
            for key in result.keys():
                if key == 'products':
                    products = result[key]
                    print(f"  - {key}: liste de {len(products) if products else 0} produits")
                else:
                    print(f"  - {key}: {type(result[key])}")
            
            products = result.get('products', [])
            print(f"\nProduits trouvés : {len(products)}")
            
            if products and len(products) > 0:
                product = products[0]
                print("\nDétails du premier produit :")
                print(f"  - Titre : {product.get('title', 'Non disponible')}")
                print(f"  - ASIN : {product.get('asin', 'Non disponible')}")
                print(f"  - availabilityAmazon : {product.get('availabilityAmazon', 'Non disponible')}")
                print(f"  - csv présent : {'Oui' if product.get('csv') else 'Non'}")
                if product.get('csv'):
                    print(f"  - csv longueur : {len(product['csv'])}")
                print("✅ Test réussi !")
                return True
            else:
                print("❌ Aucun produit dans le résultat")
                return False
        elif isinstance(result, list):
            print(f"Liste directe de {len(result)} éléments")
            if result:
                product = result[0]
                print(f"Titre : {product.get('title', 'Non disponible')}")
                print("✅ Test réussi !")
                return True
            else:
                print("❌ Liste vide")
                return False
        else:
            print(f"❌ Format de résultat inattendu : {result}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

async def main():
    success = await test_keepa_connectivity()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())