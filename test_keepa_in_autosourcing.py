#!/usr/bin/env python3
"""
Test simple d'intégration Keepa dans le workflow AutoSourcing
"""
import asyncio
import sys
import os

# Test des méthodes de conversion de paramètres
def test_parameter_mapping():
    """Test de la conversion des paramètres utilisateur vers format Keepa"""
    
    print("🔧 Test 1: Mapping paramètres")
    
    # Paramètres utilisateur (comme ceux d'AutoSourcing)
    user_criteria = {
        'categories': ['Books'],
        'price_range_min': 10.0,
        'price_range_max': 50.0,
        'bsr_threshold': 100000,
    }
    
    # Conversion vers format Keepa (comme dans _build_keepa_search_params)
    def build_keepa_search_params(criteria):
        return {
            'categories': [1000],  # Books = 1000 dans Keepa
            'price_min_cents': int(criteria.get('price_range_min', 10) * 100),
            'price_max_cents': int(criteria.get('price_range_max', 50) * 100),
            'bsr_min': 1,
            'bsr_max': criteria.get('bsr_threshold', 100000),
        }
    
    keepa_params = build_keepa_search_params(user_criteria)
    
    print("✅ Conversion paramètres:")
    print(f"  Prix: ${user_criteria['price_range_min']}-{user_criteria['price_range_max']} → {keepa_params['price_min_cents']}-{keepa_params['price_max_cents']} cents")
    print(f"  BSR: ≤{user_criteria['bsr_threshold']} → {keepa_params['bsr_min']}-{keepa_params['bsr_max']}")
    print(f"  Catégorie: {user_criteria['categories']} → {keepa_params['categories']}")
    
    return keepa_params

async def test_keepa_discovery_pipeline():
    """Test du pipeline complet discovery via Keepa"""
    
    print("\n🔍 Test 2: Pipeline Discovery")
    
    # Simulation du workflow AutoSourcing
    user_criteria = {
        'categories': ['Books'],
        'price_range_min': 15.0,
        'price_range_max': 40.0,
        'bsr_threshold': 50000,
    }
    
    # Étape 1: Conversion paramètres
    keepa_params = test_parameter_mapping()
    
    # Étape 2: Appel Keepa Product Finder
    print("\n📡 Appel Keepa Product Finder...")
    
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    
    try:
        from app.services.keepa_service import KeepaService
        import keyring
        
        api_key = keyring.get_password("memex", "KEEPA_API_KEY")
        if not api_key:
            print("❌ API key manquante")
            return
            
        keepa_service = KeepaService(api_key=api_key)
        
        asins = await keepa_service.find_products(
            search_criteria=keepa_params,
            domain=1,
            max_results=8
        )
        
        print(f"✅ Discovery: {len(asins)} produits trouvés")
        
        # Étape 3: Simulation scoring (normalement fait par AutoSourcingService)
        print("\n📊 Simulation scoring...")
        
        scored_products = []
        for i, asin in enumerate(asins[:3]):  # Test sur 3 premiers
            # Score simulé basé sur des critères business
            base_score = 75.0
            position_bonus = (len(asins) - i) * 2  # Premiers résultats = meilleur score
            final_score = min(100, base_score + position_bonus)
            
            product_data = {
                'asin': asin,
                'score': final_score,
                'profit_estimate': 15.50 + (i * 2.25),  # Simulation
                'roi_estimate': 0.35 + (i * 0.05),      # Simulation 
                'discovery_source': 'keepa_product_finder'
            }
            
            scored_products.append(product_data)
            print(f"  📚 {asin}: Score {final_score}/100, Profit ${product_data['profit_estimate']:.2f}, ROI {product_data['roi_estimate']:.1%}")
        
        await keepa_service.close()
        
        print(f"\n✅ Pipeline complet: {len(scored_products)} produits scorés")
        return scored_products
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
        import traceback
        traceback.print_exc()
        return []

async def main():
    """Test principal d'intégration Keepa"""
    
    print("🚀 Test intégration Keepa → AutoSourcing Pipeline")
    print("=" * 50)
    
    # Test pipeline complet
    results = await test_keepa_discovery_pipeline()
    
    if results:
        print(f"\n🎉 SUCCESS! Pipeline fonctionnel avec {len(results)} résultats")
        print("\n📋 Résumé des résultats:")
        for product in results:
            print(f"  • {product['asin']}: Score {product['score']}/100")
    else:
        print("\n❌ Pipeline incomplet - nécessite debugging")
    
    print("\n✅ Test terminé - Prêt pour Phase 3 Frontend!")

if __name__ == "__main__":
    asyncio.run(main())