#!/usr/bin/env python3
"""
Test final de l'intégration Keepa Product Finder dans KeepaService
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.keepa_service import KeepaService

async def test_keepa_integration():
    """Test de l'intégration complète Keepa Product Finder"""
    
    print("🔍 Test intégration Keepa Product Finder")
    
    # Récupération API key depuis secrets
    import keyring
    api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    if not api_key:
        print("❌ API key non trouvée")
        return
        
    print(f"✅ API Key récupérée: {api_key[:12]}...")
    
    # Initialisation KeepaService
    keepa_service = KeepaService(api_key=api_key)
    
    # Test 1: Product Finder avec critères livres
    print("\n📚 Test 1: Recherche livres (Books)")
    search_criteria = {
        'categories': [1000],  # Books
        'price_min_cents': 1000,  # $10
        'price_max_cents': 5000,  # $50
        'bsr_min': 1,
        'bsr_max': 100000
    }
    
    try:
        asins = await keepa_service.find_products(
            search_criteria=search_criteria,
            domain=1,  # US
            max_results=10
        )
        
        print(f"✅ Résultats: {len(asins)} ASINs trouvés")
        for i, asin in enumerate(asins[:5]):
            print(f"  {i+1}. {asin}")
            
    except Exception as e:
        print(f"❌ Erreur Product Finder: {e}")
    
    # Test 2: Détail produit pour validation
    if 'asins' in locals() and asins:
        print(f"\n📖 Test 2: Détail du produit {asins[0]}")
        try:
            product_data = await keepa_service.get_product_data([asins[0]])
            if product_data:
                product = product_data[0]
                title = product.get('title', 'N/A')[:80]
                current_price = product.get('stats', {}).get('current', [])
                bsr = product.get('stats', {}).get('current', [])
                
                print(f"✅ Produit validé:")
                print(f"  Titre: {title}")
                print(f"  Données reçues: {len(product.keys())} champs")
                print(f"  Success!")
        except Exception as e:
            print(f"❌ Erreur détail produit: {e}")
    
    await keepa_service.close()
    print("\n🎉 Test intégration Keepa terminé!")

if __name__ == "__main__":
    asyncio.run(test_keepa_integration())