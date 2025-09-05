"""Test simple de connectivité Keepa pour valider l'intégration de base."""

import sys
import os
import asyncio

sys.path.append('C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\backend')

from app.services.keepa_service import KeepaService

try:
    import keyring
except ImportError:
    print("❌ Keyring requis: uv tool install keyring")
    sys.exit(1)


def get_keepa_api_key():
    """Récupère la clé API Keepa."""
    key_variants = ["KEEPA_API_KEY", "keepa_api_key", "Keepa_API_Key", "KEEPA_KEY"]
    
    for variant in key_variants:
        try:
            key = keyring.get_password("memex", variant)
            if key:
                return key
        except:
            continue
    return None


async def test_simple_keepa_connection():
    """Test de connectivité de base avec Keepa."""
    
    print("=== TEST SIMPLE CONNECTIVITÉ KEEPA ===")
    
    # Récupérer la clé
    keepa_key = get_keepa_api_key()
    if not keepa_key:
        print("❌ Clé API Keepa non trouvée")
        return False
    
    print(f"✅ Clé API récupérée ({len(keepa_key)} caractères)")
    
    try:
        # Initialiser le service
        keepa_service = KeepaService(api_key=keepa_key)
        print("✅ Service Keepa initialisé")
        
        # Test 1: Vérifier la santé de l'API
        print("\n🔍 Test de santé de l'API...")
        health = await keepa_service.health_check()
        
        if health.get('status') == 'healthy':
            tokens_left = health.get('tokens_left', 'N/A')
            print(f"✅ API Keepa en bonne santé")
            print(f"   Tokens restants: {tokens_left}")
            print(f"   État circuit breaker: {health.get('circuit_breaker_state')}")
            
            # Test 2: Requête simple de produit
            print("\n🔍 Test requête produit simple...")
            test_asin = "B0088PUEPK"  # ASIN d'exemple de la documentation Keepa
            product = await keepa_service.get_product_data(test_asin)
            
            if product:
                title = product.get('title', 'N/A')
                print(f"✅ Produit récupéré: {title[:50]}...")
                return True
            else:
                print("⚠️ Aucun produit trouvé, mais connexion OK")
                return True  # Connexion fonctionne même si produit pas trouvé
                
        else:
            print(f"❌ API Keepa non disponible: {health.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur initialisation Keepa: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("🚀 TEST CONNECTIVITÉ KEEPA BASIQUE")
    print("=" * 50)
    
    success = await test_simple_keepa_connection()
    
    if success:
        print("\n✅ CONNECTIVITÉ KEEPA VALIDÉE!")
        print("   Nous pouvons passer aux tests d'intégration complets")
    else:
        print("\n❌ PROBLÈME DE CONNECTIVITÉ KEEPA")
        print("   Vérifiez la clé API et la configuration")


if __name__ == "__main__":
    asyncio.run(main())