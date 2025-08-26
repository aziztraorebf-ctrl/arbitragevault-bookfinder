"""
Debug script - Inspecter structure réelle des données Keepa
"""
import keyring
import requests
import json

def debug_keepa_response():
    """Inspecter réponse brute Keepa"""
    
    # Récupérer clé
    keepa_key = keyring.get_password("memex", "KEEPA_API_KEY")
    
    # Test avec un ASIN simple
    test_asin = "B08N5WRWNW"  # Echo Dot
    
    print(f"🔍 Debug réponse Keepa pour: {test_asin}")
    
    url = "https://api.keepa.com/product"
    params = {
        "key": keepa_key,
        "domain": "1",  # Amazon.com
        "asin": test_asin,
        "offers": "20",
        "stats": "180"
    }
    
    print(f"📡 Appel API...")
    response = requests.get(url, params=params, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Réponse reçue")
        print(f"📊 Clés racine: {list(data.keys())}")
        
        # Inspecter products
        products = data.get("products", [])
        print(f"🛒 Nombre de produits: {len(products)}")
        
        if products:
            product = products[0]
            print(f"\n📦 Structure produit:")
            print(f"   Clés: {list(product.keys())}")
            
            # Titre
            title = product.get("title")
            print(f"   📖 Titre: {title}")
            
            # Offres - structure détaillée
            offers = product.get("offers")
            print(f"\n🛒 Offres:")
            print(f"   Type: {type(offers)}")
            print(f"   Contenu: {offers}")
            
            if offers and len(offers) > 0:
                print(f"\n📋 Première offre détaillée:")
                first_offer = offers[0] 
                print(f"   Type: {type(first_offer)}")
                print(f"   Structure: {first_offer}")
                
                if isinstance(first_offer, dict):
                    print(f"   Clés: {list(first_offer.keys())}")
            
            # Autres champs utiles
            print(f"\n📈 Autres données:")
            for key in ['asin', 'brand', 'categoryTree', 'salesRank']:
                value = product.get(key)
                print(f"   {key}: {value}")
        
        # Sauvegarder réponse complète pour inspection
        with open('keepa_debug_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Réponse sauvée dans keepa_debug_response.json")
        
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Réponse: {response.text}")

if __name__ == "__main__":
    debug_keepa_response()