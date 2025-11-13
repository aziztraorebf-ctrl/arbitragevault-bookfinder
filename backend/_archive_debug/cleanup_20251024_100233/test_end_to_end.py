"""
Option 2: Test end-to-end du service complet
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.stock_estimate_service import StockEstimateService

async def test_end_to_end_service():
    """Test complet du service avec vraie API"""
    
    print("🧪 OPTION 2 - Test Service End-to-End")
    print("="*40)
    
    # Initialiser service
    service = StockEstimateService()
    
    # Test 1: ASIN qui fonctionne
    asin = "1292025824" 
    print(f"📖 Test service avec ASIN: {asin}")
    
    try:
        # Test sans prix cible
        result1 = await service.get_stock_estimate(asin)
        print(f"\n✅ RÉSULTAT SANS PRIX:")
        print(f"   ASIN: {result1.asin}")
        print(f"   Units: {result1.estimated_units}")
        print(f"   Confidence: {result1.confidence}")
        print(f"   Source: {result1.data_source}")
        print(f"   Cache: {result1.from_cache}")
        
        # Test avec prix cible
        result2 = await service.get_stock_estimate(asin, target_price=80.0)
        print(f"\n✅ RÉSULTAT AVEC PRIX $80:")
        print(f"   ASIN: {result2.asin}")
        print(f"   Units: {result2.estimated_units}")
        print(f"   Confidence: {result2.confidence}")
        print(f"   Source: {result2.data_source}")
        print(f"   Cache: {result2.from_cache}")
        
        # Test cache (deuxième appel)
        result3 = await service.get_stock_estimate(asin)
        print(f"\n✅ RÉSULTAT CACHE:")
        print(f"   Cache: {result3.from_cache}")
        print(f"   Units: {result3.estimated_units}")
        
        print(f"\n🎉 OPTION 2 - SERVICE END-TO-END VALIDÉ !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_end_to_end_service())