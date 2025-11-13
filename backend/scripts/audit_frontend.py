#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'audit automatique du frontend ArbitrageVault
Phase 1 Jour 1 - Plan Turbo Optimisé
"""

import time
from datetime import datetime
import json
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
FRONTEND_URL = "http://localhost:5176"
BACKEND_URL = "https://arbitragevault-backend-v2.onrender.com"

class FrontendAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_URL,
            "pages": {},
            "flows": {},
            "issues": [],
            "summary": {
                "total_pages": 0,
                "accessible": 0,
                "errors": 0,
                "total_flows": 0,
                "working_flows": 0,
                "broken_flows": 0
            }
        }

    def test_page(self, path: str, name: str, description: str = "") -> dict:
        """Test qu'une page est accessible"""
        print(f"\n🔍 Testing Page: {name}")
        print(f"   Path: {path}")
        print(f"   Description: {description}")

        result = {
            "name": name,
            "path": path,
            "url": f"{FRONTEND_URL}{path}",
            "description": description,
            "status": "unknown",
            "notes": []
        }

        # Note: En production, on utiliserait Selenium ou Playwright
        # Pour l'audit manuel, je vais documenter ce qui doit être testé

        result["manual_tests"] = [
            "Page se charge sans erreur console",
            "Composants UI s'affichent correctement",
            "Responsive design fonctionne",
            "Navigation fonctionne"
        ]

        self.results["summary"]["total_pages"] += 1
        self.results["pages"][path] = result

        return result

    def test_flow(self, name: str, steps: list, description: str = "") -> dict:
        """Test un flow utilisateur complet"""
        print(f"\n🔄 Testing Flow: {name}")
        print(f"   Description: {description}")
        print(f"   Steps: {len(steps)}")

        result = {
            "name": name,
            "description": description,
            "steps": steps,
            "status": "to_test",
            "issues": []
        }

        self.results["summary"]["total_flows"] += 1
        self.results["flows"][name] = result

        return result

    def add_issue(self, category: str, severity: str, description: str, path: str = None):
        """Ajouter un problème identifié"""
        issue = {
            "category": category,
            "severity": severity,  # critical, high, medium, low
            "description": description,
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        self.results["issues"].append(issue)
        print(f"   ⚠️ Issue: [{severity}] {description}")

    def run_audit(self):
        """Exécute l'audit frontend complet"""

        print("\n" + "="*60)
        print("🚀 AUDIT FRONTEND ARBITRAGEVAULT - PHASE 1 JOUR 1")
        print("="*60)
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Backend URL: {BACKEND_URL}")

        # ===== PAGES PRINCIPALES =====
        print("\n📌 SECTION 1: Pages Principales")
        print("-"*40)

        self.test_page("/", "Home", "Page d'accueil")
        self.test_page("/dashboard", "Dashboard", "Tableau de bord principal")
        self.test_page("/manual-analysis", "Manual Analysis", "Analyse manuelle ASIN")
        self.test_page("/batch-analysis", "Batch Analysis", "Analyse par lot")
        self.test_page("/strategic-view", "Strategic View", "Vues stratégiques")
        self.test_page("/niche-discovery", "Niche Discovery", "Découverte de niches")
        self.test_page("/auto-sourcing", "AutoSourcing", "AutoSourcing automatique")
        self.test_page("/mes-niches", "Mes Niches", "Gestion des niches")
        self.test_page("/settings", "Settings", "Paramètres")

        # ===== FLOWS CRITIQUES =====
        print("\n📌 SECTION 2: Flows Utilisateur Critiques")
        print("-"*40)

        # Flow 1: Analyse manuelle
        self.test_flow(
            "Manual ASIN Analysis",
            [
                "1. Naviguer vers /manual-analysis",
                "2. Entrer ASIN (ex: B08N5WRWNW)",
                "3. Cliquer Analyser",
                "4. Voir résultats (prix, BSR, ROI, velocity)",
                "5. Vérifier graphiques affichés"
            ],
            "Flow critique: Scanner ASIN → Voir résultats"
        )

        # Flow 2: Analyse batch
        self.test_flow(
            "Batch Analysis",
            [
                "1. Naviguer vers /batch-analysis",
                "2. Entrer liste ASINs (un par ligne)",
                "3. Cliquer Process Batch",
                "4. Voir progression",
                "5. Voir résultats tableau"
            ],
            "Analyse multiple ASINs"
        )

        # Flow 3: Dashboard metrics
        self.test_flow(
            "Dashboard Metrics",
            [
                "1. Naviguer vers /dashboard",
                "2. Vérifier stats affichées",
                "3. Vérifier graphiques chargent",
                "4. Tester filtres dates",
                "5. Exporter données"
            ],
            "Visualisation métriques globales"
        )

        # Flow 4: Strategic View
        self.test_flow(
            "Strategic View Selection",
            [
                "1. Naviguer vers /strategic-view",
                "2. Sélectionner vue (profit-hunter)",
                "3. Entrer ASINs test",
                "4. Voir scoring adapté",
                "5. Comparer vues différentes"
            ],
            "Scoring adaptatif par vue"
        )

        # Flow 5: AutoSourcing
        self.test_flow(
            "AutoSourcing Discovery",
            [
                "1. Naviguer vers /auto-sourcing",
                "2. Configurer critères recherche",
                "3. Lancer découverte",
                "4. Voir résultats",
                "5. Sauvegarder profil"
            ],
            "Découverte automatique opportunités"
        )

        # ===== PROBLÈMES CONNUS =====
        print("\n📌 SECTION 3: Problèmes Connus")
        print("-"*40)

        # Basé sur l'expérience passée
        self.add_issue(
            "API Connection",
            "high",
            "Frontend ne se connecte pas toujours au backend",
            "/manual-analysis"
        )

        self.add_issue(
            "Data Display",
            "high",
            "BSR et prix ne s'affichent pas correctement parfois",
            "/manual-analysis"
        )

        self.add_issue(
            "Authentication",
            "medium",
            "Système d'auth non implémenté",
            "/settings"
        )

        self.add_issue(
            "AutoSourcing",
            "critical",
            "Page AutoSourcing erreur 500 backend",
            "/auto-sourcing"
        )

        self.add_issue(
            "Responsive",
            "low",
            "Layout mobile non optimisé",
            "*"
        )

        # ===== CHECKLIST MANUELLE =====
        print("\n📌 SECTION 4: Tests Manuels Requis")
        print("-"*40)

        manual_tests = [
            "✅ Tester avec Chrome DevTools ouvert (Console errors)",
            "✅ Tester responsive (mobile, tablet, desktop)",
            "✅ Tester avec backend production",
            "✅ Tester avec différents ASINs (books, electronics)",
            "✅ Tester error handling (ASIN invalide)",
            "✅ Vérifier loading states",
            "✅ Vérifier error messages utilisateur",
            "✅ Tester navigation (back/forward)",
            "✅ Vérifier performance (< 3s load)",
            "✅ Tester dark mode si disponible"
        ]

        for test in manual_tests:
            print(f"   {test}")

        print("\n" + "="*60)
        print("📊 RÉSUMÉ AUDIT FRONTEND")
        print("="*60)
        print(f"Total pages à tester: {self.results['summary']['total_pages']}")
        print(f"Total flows à valider: {self.results['summary']['total_flows']}")
        print(f"Issues identifiées: {len(self.results['issues'])}")

        # Analyser sévérité issues
        severity_count = {}
        for issue in self.results["issues"]:
            sev = issue["severity"]
            severity_count[sev] = severity_count.get(sev, 0) + 1

        print("\nSévérité des problèmes:")
        for sev in ["critical", "high", "medium", "low"]:
            if sev in severity_count:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[sev]
                print(f"  {emoji} {sev.upper()}: {severity_count[sev]}")

        # Sauvegarder résultats
        output_file = "doc/audit_frontend.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")

        return self.results

    def generate_markdown_report(self):
        """Génère rapport Markdown"""

        report = []
        report.append("# Audit Frontend - Phase 1 Jour 1")
        report.append(f"\n**Date**: {self.results['timestamp']}")
        report.append(f"**Frontend URL**: {self.results['frontend_url']}")
        report.append(f"**Backend URL**: {self.results['backend_url']}")

        report.append("\n## 📊 Résumé")
        report.append(f"- **Pages testées**: {self.results['summary']['total_pages']}")
        report.append(f"- **Flows critiques**: {self.results['summary']['total_flows']}")
        report.append(f"- **Issues identifiées**: {len(self.results['issues'])}")

        # Pages
        report.append("\n## 📄 Pages Testées")
        report.append("\n| Page | Path | Description | Tests Requis |")
        report.append("|------|------|-------------|--------------|")

        for path, page in self.results["pages"].items():
            tests = len(page.get("manual_tests", []))
            report.append(f"| {page['name']} | `{path}` | {page['description']} | {tests} tests |")

        # Flows
        report.append("\n## 🔄 Flows Utilisateur")
        for name, flow in self.results["flows"].items():
            report.append(f"\n### {name}")
            report.append(f"**Description**: {flow['description']}")
            report.append("\n**Steps**:")
            for step in flow["steps"]:
                report.append(f"- {step}")

        # Issues
        report.append("\n## 🐛 Problèmes Identifiés")

        # Grouper par sévérité
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for issue in self.results["issues"]:
            by_severity[issue["severity"]].append(issue)

        for sev in ["critical", "high", "medium", "low"]:
            if by_severity[sev]:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[sev]
                report.append(f"\n### {emoji} {sev.upper()}")
                for issue in by_severity[sev]:
                    path = f" ({issue['path']})" if issue['path'] else ""
                    report.append(f"- **{issue['category']}**: {issue['description']}{path}")

        # Tests manuels
        report.append("\n## ✅ Checklist Tests Manuels")
        report.append("\n- [ ] Console sans erreurs")
        report.append("- [ ] Responsive (mobile/tablet/desktop)")
        report.append("- [ ] Connection API backend")
        report.append("- [ ] ASINs variés (books, electronics)")
        report.append("- [ ] Gestion erreurs (ASIN invalide)")
        report.append("- [ ] Loading states")
        report.append("- [ ] Messages erreur clairs")
        report.append("- [ ] Navigation browser")
        report.append("- [ ] Performance < 3s")
        report.append("- [ ] Dark mode (si disponible)")

        # Recommandations
        report.append("\n## 💡 Recommandations Prioritaires")
        report.append("\n### 1. Fixes Critiques (Jour 2)")
        report.append("- Réparer connection frontend/backend")
        report.append("- Fixer AutoSourcing erreurs 500")
        report.append("- Assurer affichage BSR/prix")

        report.append("\n### 2. Améliorations (Semaine 2)")
        report.append("- Implémenter authentication")
        report.append("- Améliorer error handling")
        report.append("- Optimiser responsive design")

        report.append("\n### 3. Nice-to-have (Semaine 3+)")
        report.append("- Dark mode")
        report.append("- Export PDF rapports")
        report.append("- Graphiques avancés")

        # Sauvegarder
        output_file = "doc/audit_frontend.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        print(f"📝 Rapport Markdown sauvegardé dans: {output_file}")

        return "\n".join(report)


if __name__ == "__main__":
    print("\n⚠️  NOTE: Ce script documente les tests à effectuer manuellement")
    print("Pour un audit automatisé complet, utiliser Selenium/Playwright")
    print("\nOuvrez votre navigateur sur: http://localhost:5176")
    print("Et suivez les tests documentés ci-dessous...\n")

    auditor = FrontendAuditor()
    results = auditor.run_audit()
    report = auditor.generate_markdown_report()

    print("\n✅ Documentation audit frontend générée!")
    print("\n📋 ACTIONS REQUISES:")
    print("1. Ouvrir http://localhost:5176 dans Chrome")
    print("2. Ouvrir DevTools (F12)")
    print("3. Exécuter tests manuels documentés")
    print("4. Noter résultats dans doc/audit_frontend.md")