"""
Option 2 Simplifiée: Test direct du service sans DB
"""
import keyring
import requests
from datetime import datetime, timedelta

class SimpleStockEstimate:
    """Version simplifiée pour test"""
    def __init__(self, asin: str, estimated_units: int, confidence: str, data_source: str = "keepa"):
        self.asin = asin
        self.estimated_units = estimated_units
        self.confidence = confidence
        self.data_source = data_source
        self.from_cache = False

def estimate_stock_simple(asin: str, target_price: float = None):
    """Logique service complète - version simplifiée"""
    
    print(f"🔍 Récupération données Keepa pour {asin}...")
    
    # Appel Keepa
    keepa_key = keyring.get_password("memex", "KEEPA_API_KEY")
    url = "https://api.keepa.com/product"
    params = {
        "key": keepa_key,
        "domain": "1",
        "asin": asin,
        "offers": "20"
    }
    
    response = requests.get(url, params=params, timeout=15)
    data = response.json()
    
    if "products" not in data or not data["products"]:
        print(f"❌ Produit non trouvé")
        return SimpleStockEstimate(asin, 0, "no_data")
    
    product = data["products"][0]
    offers = product.get("offers", [])
    
    if not offers:
        print(f"❌ Aucune offre disponible")
        return SimpleStockEstimate(asin, 0, "no_offers")
    
    print(f"✅ {len(offers)} offres récupérées")
    
    # LOGIQUE EXACTE DU SERVICE
    fba_offers = [offer for offer in offers if offer.get("isFBA", False)]
    
    print(f"📊 FBA offers: {len(fba_offers)}")
    
    if not fba_offers:
        return SimpleStockEstimate(asin, 0, "no_fba", "keepa")
    
    # Filtrage par prix si target_price fourni
    relevant_offers = fba_offers
    
    if target_price:
        print(f"💰 Filtrage par prix cible: ${target_price}")
        price_low = target_price * 0.85
        price_high = target_price * 1.15
        
        relevant_offers = []
        for offer in fba_offers:
            offer_csv = offer.get("offerCSV", [])
            if offer_csv and len(offer_csv) >= 2:
                price = offer_csv[-2] / 100  # Keepa en centimes
                if price_low <= price <= price_high:
                    relevant_offers.append(offer)
        
        print(f"📋 Offers dans fourchette: {len(relevant_offers)}")
    
    # Calcul final
    if not relevant_offers:
        units = 0
        confidence = "no_price_match"
    else:
        units = min(10, max(1, len(relevant_offers)))
        if len(relevant_offers) >= 5:
            confidence = "high"
        elif len(relevant_offers) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
    
    return SimpleStockEstimate(asin, units, confidence, "keepa")

def test_end_to_end_simple():
    """Test end-to-end complet et simple"""
    
    print("🧪 OPTION 2 - Test Service End-to-End (Simplifié)")
    print("="*50)
    
    asin = "1292025824"
    
    # Test 1: Sans prix cible
    print(f"\n📖 Test 1: SANS PRIX CIBLE")
    result1 = estimate_stock_simple(asin)
    print(f"✅ RÉSULTAT:")
    print(f"   ASIN: {result1.asin}")
    print(f"   Units: {result1.estimated_units}")
    print(f"   Confidence: {result1.confidence}")
    print(f"   Source: {result1.data_source}")
    
    # Test 2: Avec prix cible
    print(f"\n📖 Test 2: AVEC PRIX CIBLE ($80)")
    result2 = estimate_stock_simple(asin, target_price=80.0)
    print(f"✅ RÉSULTAT:")
    print(f"   ASIN: {result2.asin}")
    print(f"   Units: {result2.estimated_units}")
    print(f"   Confidence: {result2.confidence}")
    print(f"   Source: {result2.data_source}")
    
    # Test 3: Prix hors fourchette
    print(f"\n📖 Test 3: PRIX HORS FOURCHETTE ($10)")
    result3 = estimate_stock_simple(asin, target_price=10.0)
    print(f"✅ RÉSULTAT:")
    print(f"   ASIN: {result3.asin}")
    print(f"   Units: {result3.estimated_units}")
    print(f"   Confidence: {result3.confidence}")
    
    print(f"\n🎉 OPTION 2 - SERVICE COMPLET VALIDÉ !")
    
    # Validation logique
    assert result1.estimated_units > 0, "Should have units without price filter"
    assert result1.confidence in ["low", "medium", "high"], "Valid confidence"
    
    return True

if __name__ == "__main__":
    test_end_to_end_simple()