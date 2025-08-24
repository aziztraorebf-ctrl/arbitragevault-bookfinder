#!/usr/bin/env python3
"""
Test Keepa Product Finder avec la librairie officielle keepa
"""
import asyncio
import keyring
import keepa
from pprint import pprint

async def test_keepa_product_finder():
    """Test de la méthode product_finder officielle"""
    
    # Récupération de l'API key
    try:
        api_key = keyring.get_password("memex", "KEEPA_API_KEY")
        if not api_key:
            print("❌ API key non trouvée")
            return
            
        print(f"✅ API Key récupérée: {api_key[:12]}...")
        
        # Initialisation de l'API Keepa
        api = keepa.Keepa(api_key)
        
        # Test 1: Status des tokens
        print("\n🔍 Test 1: Status des tokens")
        status = api.status
        print(f"Tokens restants: {status.get('tokensLeft', 'N/A')}")
        print(f"Token refill rate: {status.get('refillRate', 'N/A')}")
        
        # Test 2: Product Finder - Recherche simple livres
        print("\n🔍 Test 2: Product Finder - Livres")
        
        # Paramètres de recherche pour livres
        product_params = {
            'categories_include': [1000],  # Books category
            'current_NEW_gte': 1000,      # Prix minimum $10 (en cents)
            'current_NEW_lte': 5000,      # Prix maximum $50 (en cents)  
            'avg30_SALES_gte': 1,         # BSR minimum (meilleur que 100k)
            'avg30_SALES_lte': 100000,    # BSR maximum
        }
        
        print("Paramètres de recherche:")
        pprint(product_params)
        
        # Appel product_finder
        try:
            results = api.product_finder(
                product_params, 
                domain='US',
                wait=True
            )
            
            print(f"✅ Product Finder OK - {len(results)} ASINs trouvés")
            print("Premiers résultats:")
            for i, asin in enumerate(results[:5]):
                print(f"  {i+1}. {asin}")
                
        except Exception as e:
            print(f"❌ Erreur Product Finder: {e}")
            print(f"Type d'erreur: {type(e)}")
            
        # Test 3: Détail d'un produit trouvé
        if 'results' in locals() and results:
            print("\n🔍 Test 3: Détail produit")
            test_asin = results[0]
            try:
                products = api.query(test_asin)
                if products:
                    product = products[0]
                    print(f"✅ Produit {test_asin}:")
                    print(f"  Titre: {product.get('title', 'N/A')[:80]}")
                    print(f"  Prix actuel: {product.get('stats', {}).get('current', {}).get('NEW', 'N/A')}")
                    print(f"  BSR: {product.get('stats', {}).get('avg30', {}).get('SALES', 'N/A')}")
            except Exception as e:
                print(f"❌ Erreur détail produit: {e}")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        print(f"Type d'erreur: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_keepa_product_finder())