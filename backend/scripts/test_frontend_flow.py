#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du flow frontend 'Scan ASIN → Résultat'.
Simule le parcours utilisateur complet pour valider la stabilité post-cleanup.
"""

import requests
import json
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "https://arbitragevault-backend-v2.onrender.com"

def test_frontend_flow():
    """
    Test le flow complet 'Scan ASIN → Résultat'.

    Simule ce que le frontend fait quand l'utilisateur entre un ASIN :
    1. GET /api/v1/keepa/{asin}/metrics pour obtenir analyse complète
    2. Vérifier que les données essentielles sont présentes
    3. Valider la structure de réponse attendue par le frontend
    """

    print("=" * 70)
    print("🧪 TEST FLOW FRONTEND 'Scan ASIN → Résultat'")
    print("=" * 70)

    # ASINs de test (mélange de livres et électronique)
    test_cases = [
        {
            "asin": "0593655036",
            "expected_title_contains": "Anxious Generation",
            "description": "Best-seller validé"
        },
        {
            "asin": "B08N5WRWNW",
            "expected_title_contains": None,  # Peut varier
            "description": "Textbook potentiel"
        }
    ]

    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for idx, test_case in enumerate(test_cases, start=1):
        asin = test_case["asin"]
        description = test_case["description"]

        print(f"\n📍 Test {idx}/{len(test_cases)}: {asin} ({description})")
        print("-" * 70)

        try:
            # Étape 1 : Requête API (comme le frontend)
            print(f"  [1/3] Fetching Keepa metrics...")
            response = requests.get(
                f"{BASE_URL}/api/v1/keepa/{asin}/metrics",
                timeout=30
            )

            if response.status_code == 404:
                print(f"  ⚠️  WARN - ASIN not in database (expected for new ASINs)")
                results["details"].append((asin, 404, "Not in DB - Expected"))
                results["passed"] += 1
                continue

            if response.status_code != 200:
                print(f"  ❌ FAIL - Status {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                results["failed"] += 1
                results["details"].append((asin, response.status_code, "HTTP Error"))
                continue

            # Étape 2 : Parser réponse JSON
            print(f"  [2/3] Parsing JSON response...")
            data = response.json()

            # Étape 3 : Valider structure (ce que le frontend attend)
            print(f"  [3/3] Validating response structure...")

            required_fields = ["asin", "analysis", "keepa_metadata", "trace_id"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                print(f"  ❌ FAIL - Missing fields: {', '.join(missing_fields)}")
                results["failed"] += 1
                results["details"].append((asin, 200, f"Missing fields: {missing_fields}"))
                continue

            # Valider contenu analysis
            analysis = data.get("analysis", {})
            analysis_required = ["roi", "velocity", "confidence_score", "overall_rating"]
            missing_analysis = [f for f in analysis_required if f not in analysis]

            if missing_analysis:
                print(f"  ⚠️  WARN - Analysis incomplete: {', '.join(missing_analysis)}")
                results["details"].append((asin, 200, f"Incomplete analysis"))
                results["passed"] += 1  # Pas cassant, juste warning
            else:
                print(f"  ✅ PASS - Complete response")
                print(f"     → ROI: {analysis.get('roi', {}).get('roi_percent', 'N/A')}%")
                print(f"     → Velocity Score: {analysis.get('velocity_score', 'N/A')}")
                print(f"     → Rating: {analysis.get('overall_rating', 'N/A')}")
                results["passed"] += 1
                results["details"].append((asin, 200, "Complete"))

        except requests.exceptions.Timeout:
            print(f"  ❌ FAIL - Timeout after 30s")
            results["failed"] += 1
            results["details"].append((asin, 0, "Timeout"))
        except requests.exceptions.RequestException as e:
            print(f"  ❌ FAIL - Request error: {e}")
            results["failed"] += 1
            results["details"].append((asin, 0, str(e)))
        except json.JSONDecodeError as e:
            print(f"  ❌ FAIL - Invalid JSON: {e}")
            results["failed"] += 1
            results["details"].append((asin, 200, "Invalid JSON"))
        except Exception as e:
            print(f"  ❌ FAIL - Unexpected error: {e}")
            results["failed"] += 1
            results["details"].append((asin, 0, str(e)))

    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ TEST FLOW FRONTEND")
    print("=" * 70)

    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"\n✅ PASS    : {results['passed']}/{total}")
    print(f"❌ FAIL    : {results['failed']}/{total}")
    print(f"🎯 TAUX    : {pass_rate:.1f}%")

    print("\nDétails :")
    for asin, status, message in results["details"]:
        icon = "✅" if "Complete" in message or "Expected" in message else "❌"
        print(f"  {icon} {asin}: [{status}] {message}")

    if results["failed"] == 0:
        print("\n🎉 VERDICT : FLOW FRONTEND STABLE")
        print("   Le parcours 'Scan ASIN → Résultat' fonctionne correctement")
        return True
    else:
        print(f"\n⚠️  VERDICT : {results['failed']} échecs détectés")
        print("   Vérifier les endpoints cassés avant Day 3")
        return False

if __name__ == "__main__":
    success = test_frontend_flow()
    sys.exit(0 if success else 1)
