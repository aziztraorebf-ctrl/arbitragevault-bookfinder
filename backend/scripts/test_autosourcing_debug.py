#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script pour tester les endpoints AutoSourcing et identifier le problème.
"""

import requests
import json
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "https://arbitragevault-backend-v2.onrender.com"

def test_autosourcing_endpoints():
    """Test tous les endpoints AutoSourcing."""

    print("=" * 60)
    print("🔍 DEBUG AUTOSOURCING")
    print("=" * 60)

    # 1. Test run_custom
    print("\n📍 Test 1: /api/v1/autosourcing/run-custom")
    payload = {
        "profile_name": "Test Debug",
        "discovery_config": {
            "categories": ["Books"],
            "price_range": [5, 50],
            "bsr_range": [10000, 100000],
            "max_results": 10
        },
        "scoring_config": {
            "roi_min": 30,
            "velocity_min": 70,
            "stability_min": 70,
            "confidence_min": 70,
            "rating_required": "GOOD"
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/autosourcing/run-custom",
            json=payload,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")

        if response.status_code >= 400:
            print(f"   ❌ Erreur: {response.text}")
        else:
            data = response.json()
            print(f"   ✅ Réponse: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # 2. Test latest
    print("\n📍 Test 2: /api/v1/autosourcing/latest")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/autosourcing/latest",
            timeout=30
        )
        print(f"   Status: {response.status_code}")

        if response.status_code >= 400:
            print(f"   ❌ Erreur: {response.text}")
        else:
            data = response.json()
            print(f"   ✅ Réponse: Jobs trouvés" if data else "   ⚠️ Aucun job récent")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # 3. Test opportunity_of_day
    print("\n📍 Test 3: /api/v1/autosourcing/opportunity-of-day")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/autosourcing/opportunity-of-day",
            timeout=30
        )
        print(f"   Status: {response.status_code}")

        if response.status_code >= 400:
            print(f"   ❌ Erreur: {response.text[:500]}")  # Limiter l'output
        else:
            data = response.json()
            print(f"   ✅ Réponse: {json.dumps(data, indent=2)[:500]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 60)
    print("ANALYSE PROBLÈME:")
    print("=" * 60)

    print("""
    Possibilités d'erreur 500:

    1. ❓ Méthode keepa.product_finder n'existe pas
       → La librairie keepa 1.3.15 n'a pas cette méthode

    2. ❓ Tables DB manquantes
       → Les tables autosourcing_* ne sont pas créées

    3. ❓ AsyncSession mal configurée
       → Problème de connexion DB async

    4. ❓ Import de module échoué
       → Un import dans le service AutoSourcing échoue
    """)

if __name__ == "__main__":
    test_autosourcing_endpoints()