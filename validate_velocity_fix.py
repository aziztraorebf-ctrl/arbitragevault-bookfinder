"""
Validation du fix de velocity score avec ASINs diversifiés.

Ce script teste le système de scoring avec différents types de produits
pour confirmer que le tri chronologique fonctionne correctement.

Usage:
    python validate_velocity_fix.py
"""

import requests
import json
from typing import Dict, List, Any
from datetime import datetime


class VelocityValidator:
    """Validateur pour le fix de velocity score."""

    def __init__(self, base_url: str = "https://arbitragevault-backend-v2.onrender.com/api/v1"):
        self.base_url = base_url
        self.results = []

    def test_asin(self, asin: str, expected_category: str) -> Dict[str, Any]:
        """
        Teste un ASIN et valide les résultats.

        Args:
            asin: ASIN à tester
            expected_category: Catégorie attendue (book, ebook, textbook, etc.)

        Returns:
            Résultats du test avec statut de validation
        """
        print(f"\n{'='*60}")
        print(f"Test ASIN: {asin} ({expected_category})")
        print(f"{'='*60}")

        try:
            # Requête API avec force refresh
            url = f"{self.base_url}/keepa/{asin}/metrics"
            params = {"config_profile": "default", "force_refresh": "true"}

            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                return {
                    "asin": asin,
                    "category": expected_category,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }

            data = response.json()
            analysis = data.get("analysis", {})
            velocity_breakdown = analysis.get("score_breakdown", {}).get("velocity", {})

            # Extraction des métriques clés
            result = {
                "asin": asin,
                "category": expected_category,
                "title": analysis.get("title", "N/A")[:80],
                "velocity_score": velocity_breakdown.get("score", 0),
                "velocity_notes": velocity_breakdown.get("notes", ""),
                "confidence_score": analysis.get("confidence_score", 0),
                "overall_rating": analysis.get("overall_rating", "UNKNOWN"),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }

            # Validation des résultats
            notes = velocity_breakdown.get("notes", "")

            if "Insufficient data" in notes:
                result["validation"] = "⚠️  AUCUNE DONNÉE - Keepa ne track pas ce produit"
                result["has_data"] = False
            else:
                # Extraire nombre de points et trend
                import re
                points_match = re.search(r'(\d+) BSR data points', notes)
                trend_match = re.search(r'([-]?\d+\.?\d*)% trend', notes)

                num_points = int(points_match.group(1)) if points_match else 0
                trend_pct = float(trend_match.group(1)) if trend_match else 0

                result["num_bsr_points"] = num_points
                result["trend_pct"] = trend_pct
                result["has_data"] = True

                # Validation du fix
                if num_points > 100 and abs(trend_pct) < 200:
                    result["validation"] = "✅ FIX VALIDÉ - Trend raisonnable avec données riches"
                elif num_points > 10 and abs(trend_pct) < 500:
                    result["validation"] = "✅ OK - Données suffisantes"
                else:
                    result["validation"] = f"❌ SUSPECT - Trend {trend_pct}% semble anormal"

            # Affichage résumé
            print(f"Titre: {result['title']}")
            print(f"Velocity Score: {result['velocity_score']}")
            print(f"Notes: {result['velocity_notes']}")
            print(f"Confidence: {result['confidence_score']}")
            print(f"Validation: {result['validation']}")

            return result

        except Exception as e:
            return {
                "asin": asin,
                "category": expected_category,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_validation_suite(self):
        """Execute la suite complète de tests de validation."""

        print("\n" + "="*80)
        print("VALIDATION DU FIX VELOCITY SCORE - BACKEND v1.6.3+")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend: {self.base_url}")

        # Suite de tests avec ASINs diversifiés
        test_cases = [
            # Livres populaires avec données riches
            ("0593655036", "popular_book"),  # The Anxious Generation - confirmé velocity 99
            ("0735224919", "popular_book"),  # Atomic Habits (bestseller constant)

            # Livres techniques/textbooks
            ("0134685997", "textbook"),      # Effective Java (tech book)
            ("1449355730", "textbook"),      # Learning Python (O'Reilly)

            # Ebooks (peuvent avoir données limitées)
            ("B08N5WRWNW", "ebook"),         # Ebook (confirmé aucune donnée)

            # Livres anciens/niche (données variables)
            ("0316769487", "classic_book"),  # Catcher in the Rye (actuellement 404)
        ]

        print(f"\nTests planifiés: {len(test_cases)} ASINs")
        print("\nDébut des tests...\n")

        for asin, category in test_cases:
            result = self.test_asin(asin, category)
            self.results.append(result)

        # Résumé final
        self.print_summary()

        # Sauvegarde résultats
        self.save_results()

    def print_summary(self):
        """Affiche le résumé des résultats de validation."""

        print("\n" + "="*80)
        print("RÉSUMÉ DE VALIDATION")
        print("="*80)

        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        with_data = sum(1 for r in self.results if r.get("has_data", False))
        validated = sum(1 for r in self.results if r.get("validation", "").startswith("✅"))

        print(f"\nTotal ASINs testés: {total}")
        print(f"Requêtes réussies: {successful}/{total}")
        print(f"ASINs avec données BSR: {with_data}/{successful}")
        print(f"Fix validé (trends raisonnables): {validated}/{with_data}")

        # Détails par catégorie
        print("\n" + "-"*80)
        print("RÉSULTATS PAR ASIN:")
        print("-"*80)

        for r in self.results:
            if not r.get("success", False):
                print(f"\n❌ {r['asin']} ({r['category']})")
                print(f"   Erreur: {r.get('error', 'Unknown')}")
            elif not r.get("has_data", False):
                print(f"\n⚠️  {r['asin']} ({r['category']})")
                print(f"   {r['validation']}")
            else:
                print(f"\n{r['validation'].split()[0]} {r['asin']} ({r['category']})")
                print(f"   Velocity: {r['velocity_score']} | Points: {r['num_bsr_points']} | Trend: {r['trend_pct']:.2f}%")

        # Conclusion
        print("\n" + "="*80)
        if validated == with_data and with_data > 0:
            print("✅ VALIDATION COMPLÈTE RÉUSSIE - Fix fonctionne correctement")
        elif validated > 0:
            print("⚠️  VALIDATION PARTIELLE - Certains ASINs présentent des anomalies")
        else:
            print("❌ VALIDATION ÉCHOUÉE - Problèmes détectés")
        print("="*80)

    def save_results(self):
        """Sauvegarde les résultats dans un fichier JSON."""

        output_file = "validation_results.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "backend_url": self.base_url,
                "total_tests": len(self.results),
                "results": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n[SAUVEGARDE] Résultats détaillés: {output_file}")


def main():
    """Point d'entrée du script."""
    validator = VelocityValidator()
    validator.run_validation_suite()


if __name__ == "__main__":
    main()
