#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'audit automatique des endpoints API ArbitrageVault
Phase 1 Jour 1 - Plan Turbo Optimisé
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import time
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
BASE_URL = "https://arbitragevault-backend-v2.onrender.com"
TIMEOUT = 30

# ASINs de test pour différents scénarios
TEST_ASINS = {
    "facile": "0593655036",  # Book populaire avec données complètes
    "moyen": "B08N5WRWNW",   # Echo Dot
    "difficile": "B00FLIJJSA",  # Ancien produit
    "invalide": "INVALID123"
}

class APIAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "endpoints": {},
            "summary": {
                "total": 0,
                "success": 0,
                "warning": 0,
                "error": 0
            }
        }

    def test_endpoint(self,
                      method: str,
                      path: str,
                      params: Dict = None,
                      json_data: Dict = None,
                      description: str = "") -> Dict:
        """Test un endpoint spécifique"""
        url = f"{BASE_URL}{path}"
        endpoint_key = f"{method} {path}"

        print(f"\n🔍 Testing: {endpoint_key}")
        print(f"   Description: {description}")

        result = {
            "method": method,
            "path": path,
            "description": description,
            "url": url,
            "params": params,
            "json": json_data,
            "status": "pending",
            "status_code": None,
            "response_time": None,
            "response": None,
            "error": None
        }

        try:
            start_time = time.time()

            if method == "GET":
                response = requests.get(url, params=params, timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=json_data, timeout=TIMEOUT)
            elif method == "PUT":
                response = requests.put(url, json=json_data, timeout=TIMEOUT)
            elif method == "DELETE":
                response = requests.delete(url, timeout=TIMEOUT)
            else:
                result["status"] = "error"
                result["error"] = f"Method {method} non supporté"
                return result

            response_time = time.time() - start_time

            result["status_code"] = response.status_code
            result["response_time"] = round(response_time, 3)

            # Analyser la réponse
            if response.status_code == 200:
                result["status"] = "success"
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text[:500]
                print(f"   ✅ Success ({response.status_code}) - {response_time:.2f}s")

            elif response.status_code in [201, 202, 204]:
                result["status"] = "success"
                result["response"] = response.text if response.text else "OK"
                print(f"   ✅ Success ({response.status_code}) - {response_time:.2f}s")

            elif response.status_code in [401, 403]:
                result["status"] = "warning"
                result["response"] = response.text[:500]
                print(f"   ⚠️ Auth Required ({response.status_code})")

            elif response.status_code == 404:
                result["status"] = "warning"
                result["response"] = "Not Found"
                print(f"   ⚠️ Not Found ({response.status_code})")

            elif response.status_code == 422:
                result["status"] = "warning"
                result["response"] = response.json() if response.text else "Validation Error"
                print(f"   ⚠️ Validation Error ({response.status_code})")

            elif response.status_code >= 500:
                result["status"] = "error"
                result["response"] = response.text[:500]
                print(f"   ❌ Server Error ({response.status_code})")

            else:
                result["status"] = "warning"
                result["response"] = response.text[:500]
                print(f"   ⚠️ Unexpected ({response.status_code})")

        except requests.exceptions.Timeout:
            result["status"] = "error"
            result["error"] = f"Timeout après {TIMEOUT}s"
            print(f"   ❌ Timeout ({TIMEOUT}s)")

        except requests.exceptions.ConnectionError as e:
            result["status"] = "error"
            result["error"] = f"Connection Error: {str(e)[:100]}"
            print(f"   ❌ Connection Error")

        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Exception: {str(e)[:100]}"
            print(f"   ❌ Exception: {str(e)[:50]}")

        # Mettre à jour résumé
        self.results["summary"]["total"] += 1
        if result["status"] == "success":
            self.results["summary"]["success"] += 1
        elif result["status"] == "warning":
            self.results["summary"]["warning"] += 1
        else:
            self.results["summary"]["error"] += 1

        # Stocker résultat
        self.results["endpoints"][endpoint_key] = result

        return result

    def run_audit(self):
        """Exécute l'audit complet de tous les endpoints"""

        print("\n" + "="*60)
        print("🚀 AUDIT API ARBITRAGEVAULT - PHASE 1 JOUR 1")
        print("="*60)

        # ===== HEALTH & INFO =====
        print("\n📌 SECTION 1: Health & Info")
        print("-"*40)

        self.test_endpoint(
            "GET", "/health",
            description="Endpoint santé basique"
        )

        self.test_endpoint(
            "GET", "/api/v1/health/ready",
            description="Readiness check avec DB"
        )

        self.test_endpoint(
            "GET", "/api/v1/health/live",
            description="Liveness check"
        )

        # ===== KEEPA ENDPOINTS =====
        print("\n📌 SECTION 2: Keepa Integration")
        print("-"*40)

        # Test avec différents ASINs
        for asin_type, asin in TEST_ASINS.items():
            if asin_type != "invalide":  # On teste l'invalide après
                self.test_endpoint(
                    "GET", f"/api/v1/keepa/{asin}/metrics",
                    description=f"Metrics pour ASIN {asin_type} ({asin})"
                )

                self.test_endpoint(
                    "GET", f"/api/v1/keepa/{asin}/raw",
                    description=f"Raw data pour ASIN {asin_type}"
                )

        # Test ASIN invalide
        self.test_endpoint(
            "GET", f"/api/v1/keepa/{TEST_ASINS['invalide']}/metrics",
            description=f"Test ASIN invalide"
        )

        # Test endpoint santé Keepa
        self.test_endpoint(
            "GET", "/api/v1/keepa/health",
            description="Health check Keepa service"
        )

        # Test connexion Keepa
        self.test_endpoint(
            "GET", "/api/v1/keepa/test",
            params={"identifier": TEST_ASINS["facile"]},
            description="Test connexion Keepa API"
        )

        # ===== ANALYSES ENDPOINTS =====
        print("\n📌 SECTION 3: Analyses")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/v1/analyses",
            params={"page": 1, "per_page": 5},
            description="Liste analyses paginées"
        )

        self.test_endpoint(
            "GET", "/api/v1/analyses/top",
            params={"batch_id": "test-batch", "limit": 5},
            description="Top analyses d'un batch"
        )

        # ===== BATCHES ENDPOINTS =====
        print("\n📌 SECTION 4: Batches")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/v1/batches",
            params={"page": 1, "per_page": 5},
            description="Liste batches"
        )

        # ===== CONFIG ENDPOINTS =====
        print("\n📌 SECTION 5: Business Configuration")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/v1/config/",
            params={"category": "books", "domain_id": 1},
            description="Config effective books US"
        )

        self.test_endpoint(
            "GET", "/api/v1/config/changes",
            params={"limit": 5},
            description="Historique changements config"
        )

        self.test_endpoint(
            "GET", "/api/v1/config/stats",
            description="Statistiques config service"
        )

        # ===== VIEWS ENDPOINTS =====
        print("\n📌 SECTION 6: Strategic Views")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/v1/views",
            description="Liste des vues disponibles"
        )

        self.test_endpoint(
            "POST", "/api/v1/views/mes_niches",
            json_data={
                "identifiers": [TEST_ASINS["facile"], TEST_ASINS["moyen"]]
            },
            description="Scoring view Mes Niches"
        )

        # ===== AUTOSOURCING ENDPOINTS =====
        print("\n📌 SECTION 7: AutoSourcing")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/v1/autosourcing/latest",
            description="Derniers résultats AutoSourcing"
        )

        self.test_endpoint(
            "GET", "/api/v1/autosourcing/jobs",
            params={"limit": 5},
            description="Jobs AutoSourcing récents"
        )

        self.test_endpoint(
            "GET", "/api/v1/autosourcing/profiles",
            description="Profils AutoSourcing sauvegardés"
        )

        self.test_endpoint(
            "GET", "/api/v1/autosourcing/health",
            description="Health check AutoSourcing"
        )

        # ===== PRODUCTS ENDPOINTS =====
        print("\n📌 SECTION 8: Products & Stock")
        print("-"*40)

        self.test_endpoint(
            "GET", f"/api/v1/products/{TEST_ASINS['facile']}/stock-estimate",
            description="Estimation stock produit"
        )

        # ===== AUTH ENDPOINTS =====
        print("\n📌 SECTION 9: Authentication")
        print("-"*40)

        self.test_endpoint(
            "POST", "/api/v1/auth/register",
            description="Register endpoint (placeholder)"
        )

        self.test_endpoint(
            "GET", "/api/v1/auth/me",
            description="Current user (auth required)"
        )

        # ===== NICHE DISCOVERY =====
        print("\n📌 SECTION 10: Niche Discovery")
        print("-"*40)

        self.test_endpoint(
            "GET", "/api/niche-discovery/categories",
            description="Categories disponibles pour niches"
        )

        self.test_endpoint(
            "GET", "/api/niche-discovery/stats",
            description="Stats service Niche Discovery"
        )

        print("\n" + "="*60)
        print("📊 RÉSUMÉ AUDIT")
        print("="*60)
        print(f"Total endpoints testés: {self.results['summary']['total']}")
        print(f"✅ Success: {self.results['summary']['success']}")
        print(f"⚠️  Warning: {self.results['summary']['warning']}")
        print(f"❌ Error: {self.results['summary']['error']}")

        # Sauvegarder résultats
        output_file = "doc/audit_backend.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")

        return self.results

    def generate_markdown_report(self):
        """Génère un rapport Markdown des résultats"""

        report = []
        report.append("# Audit Backend API - Phase 1 Jour 1")
        report.append(f"\n**Date**: {self.results['timestamp']}")
        report.append(f"**URL**: {self.results['base_url']}")
        report.append("\n## 📊 Résumé")
        report.append(f"- **Total endpoints**: {self.results['summary']['total']}")
        report.append(f"- **✅ Success**: {self.results['summary']['success']}")
        report.append(f"- **⚠️ Warning**: {self.results['summary']['warning']}")
        report.append(f"- **❌ Error**: {self.results['summary']['error']}")

        # Grouper par catégorie
        categories = {
            "Health": [],
            "Keepa": [],
            "Analyses": [],
            "Batches": [],
            "Config": [],
            "Views": [],
            "AutoSourcing": [],
            "Products": [],
            "Auth": [],
            "Niche": []
        }

        for endpoint_key, result in self.results["endpoints"].items():
            path = result["path"]
            if "/health" in path:
                categories["Health"].append((endpoint_key, result))
            elif "/keepa" in path:
                categories["Keepa"].append((endpoint_key, result))
            elif "/analyses" in path:
                categories["Analyses"].append((endpoint_key, result))
            elif "/batches" in path:
                categories["Batches"].append((endpoint_key, result))
            elif "/config" in path:
                categories["Config"].append((endpoint_key, result))
            elif "/views" in path:
                categories["Views"].append((endpoint_key, result))
            elif "/autosourcing" in path:
                categories["AutoSourcing"].append((endpoint_key, result))
            elif "/products" in path:
                categories["Products"].append((endpoint_key, result))
            elif "/auth" in path:
                categories["Auth"].append((endpoint_key, result))
            elif "/niche" in path:
                categories["Niche"].append((endpoint_key, result))

        # Générer sections
        for category, endpoints in categories.items():
            if endpoints:
                report.append(f"\n## {category}")
                report.append("\n| Endpoint | Status | Code | Time | Notes |")
                report.append("|----------|--------|------|------|-------|")

                for endpoint_key, result in endpoints:
                    status_emoji = {
                        "success": "✅",
                        "warning": "⚠️",
                        "error": "❌",
                        "pending": "⏳"
                    }.get(result["status"], "❓")

                    code = result["status_code"] if result["status_code"] else "N/A"
                    time_str = f"{result['response_time']}s" if result["response_time"] else "N/A"

                    notes = result["description"]
                    if result["error"]:
                        notes = f"ERROR: {result['error'][:50]}"

                    report.append(f"| `{endpoint_key}` | {status_emoji} | {code} | {time_str} | {notes} |")

        # Problèmes identifiés
        report.append("\n## 🔍 Problèmes Identifiés")

        errors = [
            (key, result)
            for key, result in self.results["endpoints"].items()
            if result["status"] == "error"
        ]

        if errors:
            report.append("\n### ❌ Erreurs Critiques")
            for endpoint_key, result in errors:
                report.append(f"\n**`{endpoint_key}`**")
                report.append(f"- Error: {result['error']}")

        warnings = [
            (key, result)
            for key, result in self.results["endpoints"].items()
            if result["status"] == "warning"
        ]

        if warnings:
            report.append("\n### ⚠️ Warnings")
            for endpoint_key, result in warnings:
                report.append(f"\n**`{endpoint_key}`**")
                report.append(f"- Status Code: {result['status_code']}")
                if result["response"]:
                    report.append(f"- Response: {str(result['response'])[:100]}")

        # Recommandations
        report.append("\n## 💡 Recommandations")
        report.append("\n1. **Endpoints Critiques à Fixer**:")
        for endpoint_key, _ in errors:
            report.append(f"   - {endpoint_key}")

        report.append("\n2. **Endpoints à Surveiller**:")
        for endpoint_key, _ in warnings[:5]:  # Top 5 warnings
            report.append(f"   - {endpoint_key}")

        # Sauvegarder rapport
        output_file = "doc/audit_backend.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        print(f"📝 Rapport Markdown sauvegardé dans: {output_file}")

        return "\n".join(report)


if __name__ == "__main__":
    auditor = APIAuditor()
    results = auditor.run_audit()
    report = auditor.generate_markdown_report()

    print("\n✅ Audit terminé avec succès!")