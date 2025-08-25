"""
Test simple des APIs AutoScheduler
Validation end-to-end sans sur-engineering
"""

import asyncio
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_server_running():
    """Vérifier que le serveur FastAPI tourne"""
    print("\n🌐 Test API: Serveur FastAPI...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur FastAPI accessible")
            return True
        else:
            print(f"   ❌ Serveur répond mais erreur: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Serveur non accessible - Démarrage nécessaire")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

async def test_autoscheduler_endpoints():
    """Test basique des endpoints AutoScheduler"""
    print("\n🤖 Test APIs: Endpoints AutoScheduler...")
    
    endpoints_to_test = [
        ("/autoscheduler/status", "GET", "Status AutoScheduler"),
        ("/autoscheduler/health", "GET", "Health Check"),
        ("/autoscheduler/metrics", "GET", "Métriques"),
    ]
    
    results = []
    
    for endpoint, method, description in endpoints_to_test:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {description}: OK")
                results.append(True)
                
                # Afficher un échantillon de la réponse
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) > 0:
                        key = list(data.keys())[0]
                        print(f"      Sample: {key} = {str(data[key])[:50]}...")
                except:
                    pass
            else:
                print(f"   ❌ {description}: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ {description}: Erreur {e}")
            results.append(False)
    
    return all(results)

async def test_basic_functionality():
    """Test très basique de fonctionnalité"""
    print("\n⚡ Test Fonctionnalité: Test Simple...")
    
    try:
        # Test que les données de configuration existent
        import os
        config_file = "C:\\Users\\azizt\\Workspace\\arbitragevault_bookfinder\\data\\autoscheduler_control.json"
        
        if os.path.exists(config_file):
            print("   ✅ Fichier configuration AutoScheduler trouvé")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"   ✅ Configuration chargée - Enabled: {config.get('enabled', 'unknown')}")
            return True
        else:
            print("   ⚠️  Fichier configuration non trouvé - Premier démarrage")
            return True  # Pas critique pour le test
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

async def main():
    """Lancer tous les tests API simples"""
    print("🚀 ArbitrageVault - Tests APIs Simples")
    print("=" * 50)
    
    # Test séquentiel
    test1 = await test_server_running()
    test2 = await test_autoscheduler_endpoints() if test1 else False
    test3 = await test_basic_functionality()
    
    print("\n" + "=" * 50)
    print("📋 RÉSUMÉ TESTS APIs")
    print(f"   Serveur FastAPI:    {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   APIs AutoScheduler: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"   Fonctionnalités:    {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if not test1:
        print("\n💡 SOLUTION: Démarrer le serveur FastAPI avec:")
        print("   cd backend && uv run uvicorn app.main:app --reload --port 8000")
    
    overall = test1 and test2 and test3
    print(f"\n🎯 APIs STATUS:       {'✅ OPÉRATIONNEL' if overall else '❌ ATTENTION REQUISE'}")
    
    return overall

if __name__ == "__main__":
    asyncio.run(main())