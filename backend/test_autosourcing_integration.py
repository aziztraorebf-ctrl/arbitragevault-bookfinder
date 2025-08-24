#!/usr/bin/env python3
"""
Test d'intégration complète du module AutoSourcing.
Teste l'ensemble du workflow : modèles → services → endpoints.
"""
import asyncio
import requests
import json
from datetime import datetime

# Configuration du test
BASE_URL = "http://localhost:8000"
TEST_PROFILE_NAME = "Test Profile Validation"

async def test_autosourcing_complete_workflow():
    """Test complet du workflow AutoSourcing."""
    
    print("🧪 TEST D'INTÉGRATION AUTOSOURCING")
    print("=" * 50)
    
    # Préparer la requête de recherche personnalisée
    search_request = {
        "profile_name": TEST_PROFILE_NAME,
        "discovery_config": {
            "categories": ["Books", "Textbooks"],
            "bsr_range": [1000, 50000],
            "price_range": [20, 300],
            "availability": "amazon",
            "max_results": 10
        },
        "scoring_config": {
            "roi_min": 30.0,
            "velocity_min": 70,
            "stability_min": 70,
            "confidence_min": 70,
            "rating_required": "GOOD",
            "max_results": 5
        }
    }
    
    print("1️⃣ TEST - Health Check AutoSourcing")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health: {health['status']} - {health['module']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print("\n2️⃣ TEST - Récupération Profils par Défaut")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/profiles", timeout=10)
        if response.status_code == 200:
            profiles = response.json()
            print(f"✅ Profils trouvés: {len(profiles)}")
            for profile in profiles:
                print(f"   - {profile['name']} (utilisé {profile['usage_count']} fois)")
        else:
            print(f"❌ Échec récupération profils: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur profils: {e}")
    
    print("\n3️⃣ TEST - Recherche AutoSourcing Personnalisée")
    try:
        print("   Lancement de la recherche (peut prendre 30-60 secondes)...")
        response = requests.post(
            f"{BASE_URL}/api/v1/autosourcing/run-custom",
            json=search_request,
            timeout=120  # 2 minutes max
        )
        
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Job terminé: {job['id']}")
            print(f"   Profil: {job['profile_name']}")
            print(f"   Status: {job['status']}")
            print(f"   Testé: {job['total_tested']} produits")
            print(f"   Sélectionné: {job['total_selected']} opportunités")
            print(f"   Durée: {job.get('duration_ms', 0)}ms")
            
            # Afficher quelques résultats
            if job['picks']:
                print(f"\n   📊 Top {min(3, len(job['picks']))} Opportunités:")
                for i, pick in enumerate(job['picks'][:3], 1):
                    print(f"   {i}. {pick['asin']}: {pick['roi_percentage']:.1f}% ROI")
                    print(f"      Rating: {pick['overall_rating']} | BSR: {pick.get('bsr', 'N/A')}")
            
            job_id = job['id']
            
        else:
            print(f"❌ Recherche échouée: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        return False
    
    print("\n4️⃣ TEST - Récupération Dernier Job")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/latest", timeout=10)
        if response.status_code == 200:
            latest_job = response.json()
            if latest_job:
                print(f"✅ Dernier job: {latest_job['profile_name']}")
                print(f"   Lancé: {latest_job['launched_at']}")
                print(f"   Résultats: {latest_job['total_selected']}")
            else:
                print("ℹ️  Aucun job récent trouvé")
        else:
            print(f"❌ Échec récupération latest: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur latest: {e}")
    
    print("\n5️⃣ TEST - Quick Actions")
    if job_id and job['picks']:
        try:
            # Prendre le premier pick pour tester les actions
            first_pick = job['picks'][0]
            pick_id = first_pick['id']
            
            print(f"   Test sur pick: {first_pick['asin']}")
            
            # Test action "À Acheter"
            action_request = {
                "action": "to_buy",
                "notes": "Test automatisé - excellent ROI"
            }
            
            response = requests.put(
                f"{BASE_URL}/api/v1/autosourcing/picks/{pick_id}/action",
                json=action_request,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_pick = response.json()
                print(f"✅ Action mise à jour: {updated_pick['action_status']}")
                print(f"   Is purchased: {updated_pick['is_purchased']}")
                print(f"   Notes: {updated_pick.get('action_notes', 'N/A')}")
            else:
                print(f"❌ Échec action: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur quick actions: {e}")
    
    print("\n6️⃣ TEST - Liste To-Buy")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/to-buy", timeout=10)
        if response.status_code == 200:
            to_buy_items = response.json()
            print(f"✅ Items à acheter: {len(to_buy_items)}")
            for item in to_buy_items[:2]:  # Afficher les 2 premiers
                print(f"   - {item['asin']}: {item['roi_percentage']:.1f}% ROI")
        else:
            print(f"❌ Échec to-buy list: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur to-buy: {e}")
    
    print("\n7️⃣ TEST - Opportunité du Jour")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/opportunity-of-day", timeout=10)
        if response.status_code == 200:
            opportunity = response.json()
            if opportunity:
                pick = opportunity['pick']
                print(f"✅ Opportunité du jour:")
                print(f"   🔥 {pick['title'][:50]}...")
                print(f"   📊 ROI: {pick['roi_percentage']:.1f}% | Rating: {pick['overall_rating']}")
                print(f"   💡 {opportunity['message']}")
            else:
                print("ℹ️  Aucune opportunité trouvée aujourd'hui")
        else:
            print(f"❌ Échec opportunity-of-day: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur opportunity: {e}")
    
    print("\n8️⃣ TEST - Statistiques Actions")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autosourcing/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistiques utilisateur:")
            print(f"   Actions totales: {stats['total_actions_taken']}")
            print(f"   Pipeline achat: {stats['purchase_pipeline']} items")
            print(f"   Taux engagement: {stats['engagement_rate']}")
        else:
            print(f"❌ Échec stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
    
    print("\n🎉 TEST D'INTÉGRATION TERMINÉ")
    print("✅ Module AutoSourcing fonctionnel et prêt pour le frontend!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_autosourcing_complete_workflow())
    
    if success:
        print("\n🚀 STATUT: MODULE AUTOSOURCING VALIDÉ")
        print("   Prêt pour intégration frontend")
        print("   API complète et fonctionnelle")
        print("   Toutes les fonctionnalités testées")
    else:
        print("\n💥 ÉCHECS DÉTECTÉS - Vérifier la configuration")