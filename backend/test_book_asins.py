"""
Test avec ASINs de livres réels pour données d'offres
"""
import keyring
import requests
import json

def test_book_asins():
    """Tester avec ASINs de livres qui ont historiquement des offres"""
    
    keepa_key = keyring.get_password("memex", "KEEPA_API_KEY")
    
    # ASINs de livres populaires/manuels scolaires
    book_asins = [
        "0134685997",  # Textbook - Computer Networking
        "1292025824",  # International Edition textbook
        "0321832051",  # Technology textbook
        "B07VPLRXPN",  # Kindle book
        "0262033844"   # Technical book MIT Press
    ]
    
    print("🔍 Test ASINs de livres pour données d'offres")
    
    successful_asins = []
    
    for i, asin in enumerate(book_asins):
        print(f"\n📖 Test {i+1}/5: {asin}")
        
        url = "https://api.keepa.com/product"
        params = {
            "key": keepa_key,
            "domain": "1",  # Amazon.com
            "asin": asin,
            "offers": "20"  # Juste les offres, pas de stats
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if products:
                    product = products[0]
                    
                    # Vérifications
                    title = product.get("title", "N/A")
                    offers_successful = product.get("offersSuccessful", False)
                    
                    print(f"   📚 Titre: {title[:60]}...")
                    print(f"   🛒 Offres successful: {offers_successful}")
                    
                    if offers_successful:
                        # Chercher les données d'offres
                        # Dans Keepa, les offres peuvent être dans différents champs
                        live_offers = product.get("liveOffersOrder")
                        offers = product.get("offers")
                        
                        print(f"   📊 liveOffersOrder: {type(live_offers)} = {live_offers}")
                        print(f"   📊 offers: {type(offers)} = {offers}")
                        
                        # Vérifier d'autres champs potentiels d'offres
                        offer_fields = ['liveOffersOrder', 'offers', 'liveOffers']
                        for field in offer_fields:
                            value = product.get(field)
                            if value:
                                print(f"   ✅ {field}: {type(value)} avec données")
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"      Premier élément: {value[0]}")
                        
                        successful_asins.append({
                            "asin": asin,
                            "title": title,
                            "product_data": product
                        })
                        
                        # Sauvegarder le premier succès pour analyse
                        if len(successful_asins) == 1:
                            with open(f'successful_book_{asin}.json', 'w') as f:
                                json.dump(product, f, indent=2)
                            print(f"   💾 Données sauvées pour analyse détaillée")
                    
                    else:
                        print(f"   ❌ Pas d'offres disponibles pour {asin}")
                
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   ✅ ASINs avec offres: {len(successful_asins)}")
    
    if successful_asins:
        print(f"   📚 ASINs réussis:")
        for success in successful_asins:
            print(f"      {success['asin']}: {success['title'][:40]}...")
        return successful_asins[0]  # Retourner le premier succès
    else:
        print(f"   ❌ Aucun ASIN avec données d'offres trouvé")
        return None

if __name__ == "__main__":
    result = test_book_asins()
    
    if result:
        print(f"\n🎉 SUCCÈS: Données d'offres trouvées pour {result['asin']}")
        print(f"🚀 Prêt à tester la logique Stock Estimate avec vraies données")
    else:
        print(f"\n⚠️ Aucun ASIN avec offres - peut-être ajuster les paramètres API")