#!/usr/bin/env python3
"""Test direct de l'endpoint Keepa"""
import requests
import time

def test_keepa_endpoint():
    test_asin = "0134093410"  # Manuel Campbell Biology
    
    print(f"🧪 Test endpoint Keepa avec ASIN: {test_asin}")
    
    try:
        url = f"http://localhost:8000/api/v1/keepa/{test_asin}/metrics"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=60)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Succès!")
            print(f"  Titre: {data.get('title', 'N/A')[:60]}...")
            print(f"  ROI: {data.get('roi_percentage', 0):.1f}%")
            print(f"  Velocity Score: {data.get('velocity_score', 0):.1f}")
            print(f"  Stability Score: {data.get('stability_score', 0):.1f}")
            print(f"  Confidence Score: {data.get('confidence_score', 0):.1f}")
            print(f"  Overall Rating: {data.get('overall_rating', 'N/A')}")
            
            # Vérifier les scores pour le grid search
            if all(key in data for key in ['roi_percentage', 'velocity_score', 'stability_score', 'confidence_score']):
                print("✅ Toutes les métriques nécessaires sont présentes!")
                return True
            else:
                print("❌ Métriques manquantes")
                return False
                
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_keepa_endpoint()
    if success:
        print("\n🎉 L'endpoint Keepa fonctionne - prêt pour l'optimisation!")
    else:
        print("\n💥 Problème avec l'endpoint Keepa")