"""
Test des cas limites du pipeline ArbitrageVault
================================================
Test exhaustif de tous les cas limites pour BSR → Velocity → ROI

Exécuter avec : python test_cas_limites_pipeline.py
"""

import sys
import os
import traceback
from decimal import Decimal
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.keepa_parser_v2 import parse_keepa_product, KeepaBSRExtractor
from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData
from datetime import datetime, timedelta


class TestCasLimites:
    """Suite de tests pour les cas limites du pipeline."""

    def __init__(self):
        self.results = []
        self.test_count = 0
        self.passed = 0
        self.failed = 0

    def run_test(self, test_name: str, test_func) -> bool:
        """Execute un test et enregistre les résultats."""
        self.test_count += 1
        print(f"\n{'='*80}")
        print(f"🧪 Test #{self.test_count}: {test_name}")
        print(f"{'='*80}")

        try:
            result = test_func()
            self.passed += 1
            self.results.append({
                "test": test_name,
                "status": "✅ PASS",
                "result": result
            })
            print(f"✅ TEST RÉUSSI")
            return True
        except AssertionError as e:
            self.failed += 1
            self.results.append({
                "test": test_name,
                "status": "❌ FAIL",
                "error": str(e)
            })
            print(f"❌ ASSERTION FAILED: {e}")
            return False
        except Exception as e:
            self.failed += 1
            self.results.append({
                "test": test_name,
                "status": "💥 ERROR",
                "error": f"{type(e).__name__}: {str(e)}"
            })
            print(f"💥 ERREUR: {type(e).__name__}: {e}")
            traceback.print_exc()
            return False

    def test_bsr_valide_10000(self) -> Dict[str, Any]:
        """Cas 1: BSR valide à 10 000 - produit moyennement populaire."""
        print("\n📊 Scénario: Produit avec BSR=10000 (moyenne popularité)")

        keepa_data = {
            "asin": "TEST10K",
            "title": "Produit BSR 10000",
            "category": "electronics",
            "domainId": 1,
            "stats": {
                "current": [
                    2999,   # Amazon price $29.99
                    3199,   # New price
                    2499,   # Used price
                    10000,  # BSR = 10,000
                    3499,   # List price
                ],
                "salesRankDrops30": 250,
                "salesRankDrops90": 800
            }
        }

        # Parse
        parsed = parse_keepa_product(keepa_data)
        print(f"   BSR extrait: {parsed['current_bsr']}")
        print(f"   Confidence: {parsed['bsr_confidence']:.2%}")

        assert parsed['current_bsr'] == 10000, f"BSR devrait être 10000, obtenu {parsed['current_bsr']}"
        assert parsed['bsr_confidence'] == 0.9, f"Confidence devrait être 0.9 pour BSR=10k"

        # Velocity calculation
        velocity_data = VelocityData(
            asin="TEST10K",
            sales_drops_30=250,
            sales_drops_90=800,
            current_bsr=parsed['current_bsr'],
            category="electronics",
            domain=1,
            title="Produit BSR 10000"
        )

        velocity = calculate_velocity_score(velocity_data)
        print(f"   Velocity Score: {velocity:.1f}/100")

        assert velocity > 60, f"Velocity devrait être >60 pour BSR 10k, obtenu {velocity}"

        # ROI calculation
        roi = calculate_roi_metrics(
            sale_price=float(parsed['current_price']),
            sourcing_price=15.00,  # 50% du prix de vente
            fba_fees={"base_fee": 3.0, "fulfillment_fee": 4.0},
            referral_fee_pct=15.0
        )

        print(f"   ROI: {roi['roi_percentage']:.1f}%")
        print(f"   Net Profit: ${roi['net_profit']:.2f}")

        return {
            "bsr": parsed['current_bsr'],
            "confidence": parsed['bsr_confidence'],
            "velocity": velocity,
            "roi": roi['roi_percentage']
        }

    def test_bsr_minus_one(self) -> Dict[str, Any]:
        """Cas 2: BSR = -1 (pas de données de ranking)."""
        print("\n📊 Scénario: BSR=-1 (no data)")

        keepa_data = {
            "asin": "TESTNULL",
            "title": "Produit sans BSR",
            "domainId": 1,
            "stats": {
                "current": [1999, 2199, 1699, -1, 2499]  # BSR = -1
            }
        }

        parsed = parse_keepa_product(keepa_data)
        print(f"   BSR extrait: {parsed['current_bsr']}")
        print(f"   Confidence: {parsed['bsr_confidence']:.2%}")

        assert parsed['current_bsr'] is None, f"BSR devrait être None pour -1"
        assert parsed['bsr_confidence'] == 0.0, f"Confidence devrait être 0.0"

        # Velocity avec BSR null
        velocity_data = VelocityData(
            asin="TESTNULL",
            sales_drops_30=0,
            sales_drops_90=0,
            current_bsr=None,
            category="unknown",
            domain=1,
            title="Produit sans BSR"
        )

        velocity = calculate_velocity_score(velocity_data)
        print(f"   Velocity Score: {velocity:.1f}/100 (expected 0 ou très bas)")

        return {
            "bsr": parsed['current_bsr'],
            "confidence": 0.0,
            "velocity": velocity,
            "roi": 0.0
        }

    def test_bsr_absent_stats_current(self) -> Dict[str, Any]:
        """Cas 3: BSR absent (stats.current array vide ou manquant)."""
        print("\n📊 Scénario: stats.current absent ou vide")

        keepa_data = {
            "asin": "TESTABSENT",
            "title": "Produit sans stats.current",
            "domainId": 1,
            "stats": {
                # Pas de current
                "avg30": [0, 0, 0, 25000]  # Fallback vers avg30
            }
        }

        extractor = KeepaBSRExtractor()
        bsr = extractor.extract_current_bsr(keepa_data)

        print(f"   BSR extrait (fallback avg30): {bsr}")

        assert bsr == 25000, f"Devrait fallback vers avg30[3]=25000"

        parsed = parse_keepa_product(keepa_data)
        print(f"   BSR final: {parsed['current_bsr']}")
        print(f"   Confidence: {parsed['bsr_confidence']:.2%}")

        return {
            "bsr": bsr,
            "confidence": parsed.get('bsr_confidence', 0.5),
            "velocity": 0,
            "roi": 0
        }

    def test_mauvaise_categorie(self) -> Dict[str, Any]:
        """Cas 4: Produit dans mauvaise catégorie (BSR hors limites)."""
        print("\n📊 Scénario: Electronics avec BSR=5M (hors limites)")

        keepa_data = {
            "asin": "TESTBADCAT",
            "title": "Electronics avec BSR trop élevé",
            "category": "Electronics",
            "domainId": 1,
            "stats": {
                "current": [4999, 5199, 4299, 5000000, 5999]  # BSR 5M
            }
        }

        parsed = parse_keepa_product(keepa_data)
        extractor = KeepaBSRExtractor()
        validation = extractor.validate_bsr_quality(5000000, "electronics")

        print(f"   BSR: {parsed['current_bsr']}")
        print(f"   Catégorie: Electronics")
        print(f"   Validation: {validation['valid']}")
        print(f"   Confidence: {validation['confidence']:.2%}")
        print(f"   Raison: {validation['reason']}")

        assert validation['valid'] is False, "BSR 5M devrait être invalide pour Electronics"
        assert validation['confidence'] == 0.3, "Confidence devrait être très basse"

        return {
            "bsr": 5000000,
            "valid": False,
            "confidence": 0.3,
            "reason": validation['reason']
        }

    def test_produit_sans_prix(self) -> Dict[str, Any]:
        """Cas 5: Produit sans prix de vente disponible."""
        print("\n📊 Scénario: Produit sans prix (tous les prix à -1 ou 0)")

        keepa_data = {
            "asin": "TESTNOPRICE",
            "title": "Produit sans prix",
            "domainId": 1,
            "stats": {
                "current": [-1, -1, -1, 5000, -1]  # Pas de prix, BSR=5000
            }
        }

        parsed = parse_keepa_product(keepa_data)

        print(f"   Prix Amazon: {parsed.get('current_amazon_price', 'N/A')}")
        print(f"   Prix FBA: {parsed.get('current_fba_price', 'N/A')}")
        print(f"   Prix final: {parsed.get('current_price', 'N/A')}")
        print(f"   BSR: {parsed['current_bsr']}")

        assert parsed['current_price'] is None, "Prix devrait être None"
        assert parsed['current_bsr'] == 5000, "BSR devrait être extrait malgré absence prix"

        # Test ROI avec prix null
        if parsed['current_price'] is None:
            print(f"   ROI: Non calculable (pas de prix)")
            roi_result = {"roi_percentage": 0, "net_profit": 0, "error": "No price"}
        else:
            roi_result = calculate_roi_metrics(
                sale_price=0,
                sourcing_price=10.0,
                fba_fees={"base_fee": 3.0, "fulfillment_fee": 4.0},
                referral_fee_pct=15.0
            )

        return {
            "bsr": 5000,
            "price": None,
            "roi": roi_result.get('roi_percentage', 0),
            "error": roi_result.get('error', '')
        }

    def test_bsr_tres_eleve(self) -> Dict[str, Any]:
        """Cas 6: BSR très élevé (>1M) - produit peu populaire."""
        print("\n📊 Scénario: BSR très élevé (2,500,000)")

        keepa_data = {
            "asin": "TESTHIGHBSR",
            "title": "Livre peu populaire",
            "category": "Books",  # Books permet BSR jusqu'à 5M
            "domainId": 1,
            "stats": {
                "current": [999, 1199, 799, 2500000, 1499],
                "salesRankDrops30": 5,  # Très peu de drops
                "salesRankDrops90": 12
            }
        }

        parsed = parse_keepa_product(keepa_data)

        print(f"   BSR: {parsed['current_bsr']:,}")
        print(f"   Catégorie: {parsed['category']}")
        print(f"   Confidence: {parsed['bsr_confidence']:.2%}")

        assert parsed['current_bsr'] == 2500000, "BSR devrait être 2.5M"
        assert parsed['bsr_confidence'] == 0.5, "Confidence devrait être 0.5 pour BSR élevé"

        # Velocity avec très peu de drops
        velocity_data = VelocityData(
            asin="TESTHIGHBSR",
            sales_drops_30=5,
            sales_drops_90=12,
            current_bsr=2500000,
            category="books",
            domain=1,
            title="Livre peu populaire"
        )

        velocity = calculate_velocity_score(velocity_data)
        print(f"   Velocity Score: {velocity:.1f}/100 (expected très bas)")

        assert velocity < 20, f"Velocity devrait être <20 pour BSR 2.5M, obtenu {velocity}"

        return {
            "bsr": 2500000,
            "confidence": 0.5,
            "velocity": velocity,
            "category": "books"
        }

    def test_bsr_top_seller(self) -> Dict[str, Any]:
        """Cas 7: BSR très bas (<100) - top seller."""
        print("\n📊 Scénario: Top Seller (BSR=42)")

        keepa_data = {
            "asin": "TESTTOP",
            "title": "Best Seller #42",
            "category": "Electronics",
            "domainId": 1,
            "stats": {
                "current": [9999, 10999, 8999, 42, 12999],  # BSR=42
                "salesRankDrops30": 2500,  # Beaucoup de ventes
                "salesRankDrops90": 7800
            }
        }

        parsed = parse_keepa_product(keepa_data)

        print(f"   BSR: {parsed['current_bsr']}")
        print(f"   Confidence: {parsed['bsr_confidence']:.2%}")

        assert parsed['current_bsr'] == 42, "BSR devrait être 42"
        assert parsed['bsr_confidence'] == 1.0, "Confidence devrait être 1.0 pour top seller"

        # Velocity très élevée
        velocity_data = VelocityData(
            asin="TESTTOP",
            sales_drops_30=2500,
            sales_drops_90=7800,
            current_bsr=42,
            category="electronics",
            domain=1,
            title="Best Seller #42"
        )

        velocity = calculate_velocity_score(velocity_data)
        print(f"   Velocity Score: {velocity:.1f}/100 (expected >90)")

        assert velocity > 90, f"Velocity devrait être >90 pour top seller, obtenu {velocity}"

        # ROI avec produit très demandé
        roi = calculate_roi_metrics(
            sale_price=float(parsed['current_price']),
            sourcing_price=50.0,  # Environ 50% du prix
            fba_fees={"base_fee": 3.0, "fulfillment_fee": 4.0},
            referral_fee_pct=15.0
        )

        print(f"   ROI: {roi['roi_percentage']:.1f}%")

        return {
            "bsr": 42,
            "confidence": 1.0,
            "velocity": velocity,
            "roi": roi['roi_percentage']
        }

    def test_fallback_cascade(self) -> Dict[str, Any]:
        """Cas 8: Test cascade de fallback (current → csv → avg30)."""
        print("\n📊 Scénario: Test fallback cascade complète")

        # Test avec seulement csv history récent
        now_keepa = int((datetime.now().timestamp() * 1000) / 60000) - 21564000
        hour_ago = now_keepa - 60

        keepa_data = {
            "asin": "TESTFALLBACK",
            "title": "Test Fallback Cascade",
            "domainId": 1,
            "stats": {
                "current": [],  # Vide
                "avg30": [0, 0, 0, 35000]  # Fallback ultime
            },
            "csv": [
                [],
                [],
                [],
                [hour_ago, 15000, now_keepa - 30, 18000]  # Histoire récent
            ]
        }

        extractor = KeepaBSRExtractor()
        bsr = extractor.extract_current_bsr(keepa_data)

        print(f"   BSR extrait (fallback csv récent): {bsr}")
        print(f"   Source: csv[3] history (< 24h)")

        assert bsr == 18000, f"Devrait utiliser csv[3][-1]=18000, obtenu {bsr}"

        # Test avec csv trop ancien
        keepa_data_old = {
            "asin": "TESTFALLBACK2",
            "title": "Test Fallback Old",
            "domainId": 1,
            "stats": {
                "current": [],
                "avg30": [0, 0, 0, 45000]
            },
            "csv": [
                [],
                [],
                [],
                [now_keepa - 2000, 20000]  # Trop ancien (>24h)
            ]
        }

        bsr_old = extractor.extract_current_bsr(keepa_data_old)
        print(f"   BSR avec csv ancien (fallback avg30): {bsr_old}")

        assert bsr_old == 45000, f"Devrait fallback vers avg30=45000"

        return {
            "bsr_recent": 18000,
            "bsr_fallback": 45000,
            "cascade": "current→csv→avg30"
        }

    def print_summary(self):
        """Affiche le résumé des tests."""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ AUDIT DES CAS LIMITES")
        print("="*80)

        print(f"\nTests exécutés: {self.test_count}")
        print(f"✅ Réussis: {self.passed}")
        print(f"❌ Échoués: {self.failed}")
        print(f"Taux de réussite: {(self.passed/self.test_count)*100:.1f}%")

        print("\n📋 Détail des résultats:")
        print("-"*80)
        for result in self.results:
            status = result['status']
            test = result['test']
            print(f"{status} {test}")
            if 'error' in result:
                print(f"    ↳ {result['error']}")

        return self.passed == self.test_count


def main():
    """Point d'entrée principal."""
    print("🔬 AUDIT COMPLET DU PIPELINE BSR → VELOCITY → ROI")
    print("="*80)

    tester = TestCasLimites()

    # Liste des tests à exécuter
    tests = [
        ("BSR valide à 10,000", tester.test_bsr_valide_10000),
        ("BSR = -1 (no data)", tester.test_bsr_minus_one),
        ("BSR absent (stats vide)", tester.test_bsr_absent_stats_current),
        ("Mauvaise catégorie", tester.test_mauvaise_categorie),
        ("Produit sans prix", tester.test_produit_sans_prix),
        ("BSR très élevé (2.5M)", tester.test_bsr_tres_eleve),
        ("Top Seller (BSR=42)", tester.test_bsr_top_seller),
        ("Fallback cascade", tester.test_fallback_cascade)
    ]

    # Exécution des tests
    for test_name, test_func in tests:
        tester.run_test(test_name, test_func)

    # Affichage du résumé
    success = tester.print_summary()

    if success:
        print("\n✅ TOUS LES CAS LIMITES SONT CORRECTEMENT GÉRÉS")
    else:
        print(f"\n⚠️  {tester.failed} cas limites ont échoué - Vérification requise")

    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)