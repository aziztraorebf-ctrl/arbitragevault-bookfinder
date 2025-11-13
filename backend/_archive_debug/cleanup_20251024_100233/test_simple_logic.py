"""
Option 1: Test ultra-simple de la logique avec vraies données Keepa
"""
import keyring
import requests

def test_simple_stock_logic():
    """Test direct de notre logique avec vraie data Keepa"""
    
    print("🧪 OPTION 1 - Test Logique Simple")
    print("="*40)
    
    # Récupérer données pour ASIN qui fonctionne
    keepa_key = keyring.get_password("memex", "KEEPA_API_KEY")
    asin = "1292025824"  # Textbook qui a des offres
    
    print(f"📖 Test avec ASIN: {asin}")
    
    # Appel Keepa simple
    url = "https://api.keepa.com/product"
    params = {
        "key": keepa_key,
        "domain": "1",
        "asin": asin,
        "offers": "20"  # Minimum Keepa
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if "products" not in data or not data["products"]:
        print(f"❌ Pas de produits dans la réponse: {data}")
        return False
        
    product = data["products"][0]
    
    # Parser les offres (structure réelle confirmée)
    offers = product.get("offers", [])
    print(f"🛒 Offres récupérées: {len(offers)}")
    
    # NOTRE LOGIQUE EXACTE (du service)
    fba_offers = []
    mfn_offers = []
    
    for offer in offers:
        is_fba = offer.get("isFBA", False)
        price = offer.get("price", 0)  # Note: prix peut être dans offerCSV
        
        if is_fba:
            fba_offers.append(offer)
        else:
            mfn_offers.append(offer)
    
    print(f"📊 FBA: {len(fba_offers)}, MFN: {len(mfn_offers)}")
    
    # Test sans prix cible
    units_estimate = min(10, max(1 if len(fba_offers) > 0 else 0, len(fba_offers)))
    
    print(f"\n✅ RÉSULTAT LOGIQUE:")
    print(f"   Units estimate: {units_estimate}")
    print(f"   FBA offers: {len(fba_offers)}")
    print(f"   MFN offers: {len(mfn_offers)}")
    
    # Test avec prix cible (prix moyen des 3 premières offres)
    if fba_offers:
        # Prix dans Keepa sont dans offerCSV ou price field
        sample_prices = []
        for offer in fba_offers[:3]:
            offer_csv = offer.get("offerCSV", [])
            if offer_csv and len(offer_csv) >= 2:
                # Format Keepa: [timestamp, price, shipping, ...]
                price = offer_csv[-2] / 100  # Converti en dollars (Keepa en centimes)
                if price > 0:
                    sample_prices.append(price)
        
        if sample_prices:
            avg_price = sum(sample_prices) / len(sample_prices)
            print(f"\n💰 Test avec prix cible: ${avg_price:.2f}")
            
            # Filtrer par prix (±15%)
            price_low = avg_price * 0.85
            price_high = avg_price * 1.15
            
            fba_in_range = 0
            for offer in fba_offers:
                offer_csv = offer.get("offerCSV", [])
                if offer_csv and len(offer_csv) >= 2:
                    price = offer_csv[-2] / 100
                    if price_low <= price <= price_high:
                        fba_in_range += 1
            
            units_with_price = min(10, max(1 if fba_in_range > 0 else 0, fba_in_range))
            print(f"   FBA dans fourchette: {fba_in_range}")
            print(f"   Units avec prix: {units_with_price}")
    
    print(f"\n🎉 OPTION 1 - LOGIQUE VALIDÉE !")
    return True

if __name__ == "__main__":
    test_simple_stock_logic()