#!/usr/bin/env python3
"""
Debug de la logique de détection Amazon
=======================================
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

import keyring
from app.services.keepa_service import KeepaService
from app.services.amazon_filter_service import AmazonFilterService

async def debug_amazon_detection():
    """Debug de la détection Amazon étape par étape."""
    print("🔍 DEBUG - Logique de détection Amazon")
    print("=" * 60)
    
    # Récupérer la clé API
    keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    keepa_service = KeepaService(keepa_api_key)
    amazon_filter = AmazonFilterService()
    
    # Test avec un livre qui DEVRAIT être non-Amazon
    test_asin = "0316769487"  # The Catcher in the Rye - livre ancien
    
    print(f"📚 Analyse détaillée pour : {test_asin}")
    product_data = await keepa_service.get_product_data(test_asin)
    
    if not product_data:
        print("❌ Aucune donnée récupérée")
        return
    
    print(f"\n📖 Titre : {product_data.get('title', 'Non disponible')}")
    
    # Analyser chaque critère de détection
    print("\n🔍 ANALYSE DES CRITÈRES :")
    
    # 1. availabilityAmazon
    availability = product_data.get('availabilityAmazon', -1)
    print(f"1. availabilityAmazon : {availability}")
    print(f"   → Signification : {_interpret_availability(availability)}")
    
    # 2. CSV data (historique prix)
    csv_data = product_data.get('csv', [])
    print(f"\n2. CSV data : {len(csv_data)} séries")
    if csv_data:
        # csv[0] = Prix Amazon
        amazon_prices = csv_data[0] if len(csv_data) > 0 else []
        print(f"   • Amazon prices (csv[0]) : {len(amazon_prices)} points")
        if amazon_prices:
            recent_amazon = [x for x in amazon_prices[-10:] if x is not None and x > 0]
            print(f"   • Prix Amazon récents (10 derniers) : {len(recent_amazon)} non-null")
            if recent_amazon:
                print(f"   • Derniers prix Amazon : {recent_amazon[-3:]}")
        
        # csv[18] = Prix FBA
        if len(csv_data) > 18:
            fba_prices = csv_data[18]
            if fba_prices is not None:
                print(f"   • FBA prices (csv[18]) : {len(fba_prices)} points")
                recent_fba = [x for x in fba_prices[-5:] if x is not None and x > 0]
                print(f"   • Prix FBA récents : {len(recent_fba)} non-null")
            else:
                print(f"   • FBA prices (csv[18]) : Aucune donnée FBA")
    
    # 3. Buy Box History
    buybox_history = product_data.get('buyBoxSellerIdHistory')
    print(f"\n3. Buy Box History : {type(buybox_history)}")
    if buybox_history:
        print(f"   • Longueur : {len(buybox_history)}")
        recent_sellers = buybox_history[-10:] if len(buybox_history) > 10 else buybox_history
        amazon_in_buybox = 1 in recent_sellers if recent_sellers else False
        print(f"   • Amazon (ID=1) dans Buy Box récent : {amazon_in_buybox}")
    else:
        print("   • Aucun historique Buy Box")
    
    # Test de la logique de détection
    print(f"\n🧪 TEST DE DÉTECTION :")
    is_amazon, reason = amazon_filter._detect_amazon_presence(product_data)
    print(f"   • Résultat : {'Amazon détecté' if is_amazon else 'Amazon NON détecté'}")
    print(f"   • Raison : {reason}")
    
    # Test avec niveau de détection différent
    print(f"\n🔧 TEST NIVEAU 'SAFE' :")
    amazon_filter.set_detection_level("safe")
    is_amazon_safe, reason_safe = amazon_filter._detect_amazon_presence(product_data)
    print(f"   • Résultat Safe : {'Amazon détecté' if is_amazon_safe else 'Amazon NON détecté'}")
    print(f"   • Raison Safe : {reason_safe}")

def _interpret_availability(availability):
    """Interpréter la valeur availabilityAmazon."""
    if availability == -1:
        return "Amazon non disponible"
    elif availability == 0:
        return "Amazon en stock immédiatement"
    elif availability > 0:
        return f"Amazon disponible dans {availability} jours"
    else:
        return f"Valeur inconnue: {availability}"

async def main():
    await debug_amazon_detection()

if __name__ == "__main__":
    asyncio.run(main())