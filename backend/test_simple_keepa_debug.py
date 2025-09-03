#!/usr/bin/env python3
"""
Simple Keepa Debug Test - Voir exactement ce qui est retourné
"""

import asyncio
import keyring
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "app"))

from app.services.keepa_service import KeepaService


async def simple_test():
    """Test simple pour voir format données Keepa."""
    
    # Récupérer clé API
    keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    if not keepa_api_key:
        print("❌ Clé API Keepa introuvable")
        return
    
    print(f"✅ Clé API: {keepa_api_key[:8]}...")
    
    # Initialiser service
    service = KeepaService(api_key=keepa_api_key)
    
    try:
        # Test health check d'abord
        print("\n🔍 Test Health Check:")
        health = await service.health_check()
        print(f"Health: {health}")
        
        if health.get('status') == 'healthy':
            print(f"✅ Tokens restants: {health.get('tokens_left', 'Unknown')}")
        
        # Test avec un ASIN simple
        test_asin = "B08N5WRWNW"
        print(f"\n🔍 Test ASIN: {test_asin}")
        
        result = await service.get_product_data(test_asin)
        
        print(f"\n📊 Résultat type: {type(result)}")
        
        if result is None:
            print("❌ Résultat est None")
        elif isinstance(result, dict):
            print(f"✅ Dict avec {len(result)} clés")
            print("🔍 Clés principales:")
            for key in list(result.keys())[:10]:
                value = result[key]
                print(f"   {key}: {type(value)} = {str(value)[:50]}...")
                
            # Chercher les champs essentiels
            essential_fields = ['asin', 'title', 'isAmazon', 'domain']
            print("\n🔍 Champs essentiels:")
            for field in essential_fields:
                if field in result:
                    print(f"   ✅ {field}: {result[field]}")
                else:
                    print(f"   ❌ {field}: MANQUANT")
            
            # Chercher tous les champs contenant "amazon" ou "seller"
            print("\n🔍 Champs liés à Amazon/Seller:")
            amazon_fields = [k for k in result.keys() if 'amazon' in k.lower() or 'seller' in k.lower()]
            for field in amazon_fields[:10]:
                print(f"   {field}: {result[field]}")
                
            # Chercher champs de titre
            print("\n🔍 Champs de titre/nom:")
            title_fields = [k for k in result.keys() if 'title' in k.lower() or 'name' in k.lower()]
            for field in title_fields:
                print(f"   {field}: {result[field]}")
                
            print("\n🔍 Tous les champs disponibles:")
            for key in sorted(result.keys()):
                if result[key] is not None and result[key] != -1:
                    print(f"   {key}: {type(result[key])} = {str(result[key])[:30]}...")
        else:
            print(f"⚠️  Type inattendu: {type(result)}")
            print(f"Contenu: {str(result)[:200]}...")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print(f"   Type: {type(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(simple_test())