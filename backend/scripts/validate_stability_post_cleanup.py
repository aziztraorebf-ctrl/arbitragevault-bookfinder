#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation de stabilité après nettoyage des 109 scripts.
Teste les 5 endpoints critiques pour détecter les régressions.
"""

import requests
import json
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "https://arbitragevault-backend-v2.onrender.com"

def test_critical_endpoints():
    """Test des 5 endpoints les plus critiques."""

    print("=" * 70)
    print("🔍 VALIDATION STABILITÉ POST-NETTOYAGE")
    print("=" * 70)

    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "details": []
    }

    # 1. Health check
    print("\n📍 Test 1/5: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/ready", timeout=10)
        if response.status_code == 200:
            print("   ✅ PASS - Health check OK")
            results["passed"] += 1
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["failed"] += 1
        results["details"].append(("Health Check", response.status_code, "OK" if response.status_code == 200 else "FAIL"))
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        results["failed"] += 1
        results["details"].append(("Health Check", 0, str(e)))

    # 2. Keepa Metrics (endpoint critique métier)
    print("\n📍 Test 2/5: Keepa Metrics (ASIN test)")
    test_asin = "0593655036"
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/keepa/{test_asin}/metrics",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            has_analysis = "analysis" in data
            has_roi = "analysis" in data and "roi" in data.get("analysis", {})

            if has_analysis and has_roi:
                print(f"   ✅ PASS - Metrics complets pour {test_asin}")
                results["passed"] += 1
            else:
                print(f"   ⚠️ WARN - Données incomplètes")
                results["warnings"] += 1
            results["details"].append(("Keepa Metrics", response.status_code, "OK" if has_roi else "INCOMPLETE"))
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["failed"] += 1
            results["details"].append(("Keepa Metrics", response.status_code, "FAIL"))
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        results["failed"] += 1
        results["details"].append(("Keepa Metrics", 0, str(e)))

    # 3. Analyses List
    print("\n📍 Test 3/5: Analyses List")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/analyses?per_page=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            has_items = "items" in data
            print(f"   ✅ PASS - {len(data.get('items', []))} analyses trouvées")
            results["passed"] += 1
            results["details"].append(("Analyses List", response.status_code, f"{len(data.get('items', []))} items"))
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["failed"] += 1
            results["details"].append(("Analyses List", response.status_code, "FAIL"))
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        results["failed"] += 1
        results["details"].append(("Analyses List", 0, str(e)))

    # 4. Business Config
    print("\n📍 Test 4/5: Business Config")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/config/?domain_id=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            has_config = "config" in data
            has_roi = has_config and "roi" in data.get("config", {})

            if has_config and has_roi:
                print("   ✅ PASS - Config chargée avec ROI params")
                results["passed"] += 1
            else:
                print("   ⚠️ WARN - Config incomplète")
                results["warnings"] += 1
            results["details"].append(("Business Config", response.status_code, "OK" if has_roi else "INCOMPLETE"))
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["failed"] += 1
            results["details"].append(("Business Config", response.status_code, "FAIL"))
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        results["failed"] += 1
        results["details"].append(("Business Config", 0, str(e)))

    # 5. Views Scoring (nouveau système v1.5)
    print("\n📍 Test 5/5: View-Specific Scoring")
    try:
        payload = {"identifiers": ["0593655036", "B08N5WRWNW"]}
        response = requests.post(
            f"{BASE_URL}/api/v1/views/dashboard",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            has_products = "products" in data and len(data.get("products", [])) > 0

            if has_products:
                print(f"   ✅ PASS - {len(data['products'])} produits scorés")
                results["passed"] += 1
            else:
                print("   ⚠️ WARN - Aucun produit retourné")
                results["warnings"] += 1
            results["details"].append(("View Scoring", response.status_code, f"{len(data.get('products', []))} products"))
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["failed"] += 1
            results["details"].append(("View Scoring", response.status_code, "FAIL"))
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        results["failed"] += 1
        results["details"].append(("View Scoring", 0, str(e)))

    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ VALIDATION")
    print("=" * 70)

    total = results["passed"] + results["failed"] + results["warnings"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"\n✅ PASS    : {results['passed']}/{total}")
    print(f"❌ FAIL    : {results['failed']}/{total}")
    print(f"⚠️  WARNING : {results['warnings']}/{total}")
    print(f"\n🎯 TAUX DE RÉUSSITE : {pass_rate:.1f}%")

    if results["failed"] == 0 and results["warnings"] == 0:
        print("\n🎉 VERDICT : STABILITÉ CONFIRMÉE - Aucune régression détectée")
        return True
    elif results["failed"] == 0:
        print(f"\n⚠️  VERDICT : STABLE AVEC AVERTISSEMENTS - {results['warnings']} warnings à investiguer")
        return True
    else:
        print(f"\n❌ VERDICT : RÉGRESSION DÉTECTÉE - {results['failed']} endpoints cassés!")
        return False

if __name__ == "__main__":
    success = test_critical_endpoints()
    sys.exit(0 if success else 1)