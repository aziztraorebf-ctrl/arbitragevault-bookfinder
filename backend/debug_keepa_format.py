#!/usr/bin/env python3
"""
Debug Keepa API Response Format
==============================
Vérifier le format exact des données retournées par l'API Keepa.
"""

import asyncio
import keyring
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "app"))

from app.services.keepa_service import KeepaService


async def debug_keepa_response():
    """Déboguer le format de réponse Keepa."""
    
    # Récupérer clé API
    keepa_api_key = keyring.get_password("memex", "KEEPA_API_KEY")
    if not keepa_api_key:
        print("❌ Clé API Keepa introuvable")
        return
    
    print(f"✅ Clé API: {keepa_api_key[:8]}...")
    
    # Initialiser service
    service = KeepaService(api_key=keepa_api_key)
    
    try:
        # Test avec un seul ASIN
        test_asin = "B08N5WRWNW"
        print(f"\n🔍 Test ASIN: {test_asin}")
        
        result = await service.get_product_data([test_asin])
        
        print(f"\n📊 Type de résultat: {type(result)}")
        print(f"📊 Longueur: {len(result) if result else 'None'}")
        
        if result:
            print(f"📊 Premier élément type: {type(result[0])}")
            print(f"📊 Premier élément contenu:")
            
            if isinstance(result[0], dict):
                for key, value in list(result[0].items())[:10]:  # First 10 keys
                    print(f"   {key}: {type(value)} = {str(value)[:100]}...")
            else:
                print(f"   Contenu brut: {str(result[0])[:200]}...")
        else:
            print("❌ Résultat vide")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print(f"   Type erreur: {type(e)}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(debug_keepa_response())