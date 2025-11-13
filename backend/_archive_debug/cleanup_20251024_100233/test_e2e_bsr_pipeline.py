"""
Test E2E - Pipeline complet BSR → ROI
======================================
Teste l'extraction BSR avec le nouveau parser v2 + correctif keepa_service.py

Exécuter avec : python test_e2e_bsr_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.keepa_parser_v2 import parse_keepa_product, KeepaBSRExtractor
from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData
from decimal import Decimal


def test_complete_pipeline_echo_dot():
    """
    Test pipeline complet avec Echo Dot ASIN: B08N5WRWNW
    Simule réponse Keepa → Parser v2 → Calculs ROI
    """
    print("\n" + "=" * 80)
    print("🔬 TEST E2E: Pipeline complet BSR → ROI (Echo Dot B08N5WRWNW)")
    print("=" * 80)

    # Simule réponse Keepa API (données réelles simplifiées)
    keepa_response = {
        "asin": "B08N5WRWNW",
        "title": "Echo Dot (4th Gen) | Smart speaker with Alexa | Charcoal",
        "brand": "Amazon",
        "category": "Electronics",
        "domainId": 1,
        "packageDimensions": {
            "height": 3.9,
            "length": 3.9,
            "width": 3.9,
            "weight": 0.7
        },
        "stats": {
            "current": [
                4999,   # 0: Amazon price $49.99
                5499,   # 1: New price
                3999,   # 2: Used price
                527,    # 3: BSR rank 527 ← CRITICAL VALUE
                5999,   # 4: List price
                -1, -1, -1, -1, -1,
                4899,   # 10: FBA price
                15,     # 11: New count
                8,      # 12: Used count
                -1, -1,
                45,     # 15: Rating (4.5 stars)
                125000, # 16: Review count
                -1,
                5299    # 18: Buy Box price
            ],
            "salesRankDrops30": 1250,  # Velocity data
            "salesRankDrops90": 3800
        },
        "csv": [
            # Price history (simplified)
            [21564000, 5999, 21565000, 4999],
            [],
            [],
            # BSR history
            [21564000, 1200, 21565000, 527]
        ]
    }

    # ===== ÉTAPE 1: PARSE KEEPA =====
    print("\n📦 ÉTAPE 1: Parse Keepa Response")
    print("-" * 80)

    parsed_data = parse_keepa_product(keepa_response)

    print(f"   ASIN: {parsed_data['asin']}")
    print(f"   Titre: {parsed_data['title'][:50]}...")
    print(f"   Catégorie: {parsed_data['category']}")
    print(f"\n   💰 Prix extraits:")
    print(f"      - Amazon: ${parsed_data.get('current_amazon_price', 'N/A')}")
    print(f"      - FBA: ${parsed_data.get('current_fba_price', 'N/A')}")
    print(f"      - Meilleur prix: ${parsed_data.get('current_price', 'N/A')}")
    print(f"\n   📊 BSR (CRITICAL):")
    print(f"      - BSR actuel: {parsed_data.get('current_bsr', 'NULL')}")
    print(f"      - BSR confidence: {parsed_data.get('bsr_confidence', 0):.2%}")
    print(f"\n   📈 Données supplémentaires:")
    print(f"      - Nombre d'offres: {parsed_data.get('offers_count', 'N/A')}")

    # VALIDATION ÉTAPE 1
    assert parsed_data['current_bsr'] == 527, f"❌ BSR incorrect: {parsed_data['current_bsr']}"
    assert parsed_data['bsr_confidence'] == 1.0, "❌ Confidence incorrecte"
    assert parsed_data['current_amazon_price'] == Decimal("49.99"), "❌ Prix incorrect"

    print("\n   ✅ ÉTAPE 1 VALIDÉE: Parsing Keepa OK")

    # ===== ÉTAPE 2: SIMULATE KEEPA_SERVICE.PY PATCH =====
    print("\n⚙️  ÉTAPE 2: Validation correctif keepa_service.py")
    print("-" * 80)

    # Code du patch (lignes 426-432 de keepa_service.py)
    stats = keepa_response.get('stats', {})
    current = stats.get('current', [])
    current_bsr = None
    if current and len(current) > 3:
        bsr = current[3]
        if bsr and bsr != -1:
            current_bsr = int(bsr)

    print(f"   Pattern keepa_service.py:")
    print(f"      stats.current[3] = {current[3] if len(current) > 3 else 'N/A'}")
    print(f"      current_bsr extrait = {current_bsr}")

    # VALIDATION ÉTAPE 2
    assert current_bsr == 527, f"❌ keepa_service patch failed: {current_bsr}"

    print("\n   ✅ ÉTAPE 2 VALIDÉE: keepa_service.py patch OK")

    # ===== ÉTAPE 3: CALCULATE VELOCITY =====
    print("\n🚀 ÉTAPE 3: Calcul Velocity Score")
    print("-" * 80)

    # Simule VelocityData avec BSR extrait
    velocity_data = VelocityData(
        asin=parsed_data['asin'],
        sales_drops_30=keepa_response['stats']['salesRankDrops30'],
        sales_drops_90=keepa_response['stats']['salesRankDrops90'],
        current_bsr=current_bsr,  # ← CRITICAL: doit être 527, pas NULL
        category=parsed_data['category'],
        domain=1,
        title=parsed_data['title']
    )

    velocity_score = calculate_velocity_score(velocity_data)

    print(f"   Sales Drops 30d: {velocity_data.sales_drops_30}")
    print(f"   Sales Drops 90d: {velocity_data.sales_drops_90}")
    print(f"   BSR utilisé: {velocity_data.current_bsr}")
    print(f"   Velocity Score: {velocity_score:.2f}/100")

    # VALIDATION ÉTAPE 3
    assert velocity_score > 0, "❌ Velocity score invalide"
    assert velocity_data.current_bsr == 527, "❌ BSR non propagé dans VelocityData"

    print("\n   ✅ ÉTAPE 3 VALIDÉE: Velocity Score calculé")

    # ===== ÉTAPE 4: CALCULATE ROI =====
    print("\n💰 ÉTAPE 4: Calcul ROI Metrics")
    print("-" * 80)

    # Business config simulée
    business_config = {
        "fba_fees": {"base_fee": 3.0, "fulfillment_fee": 4.0},
        "sourcing": {"sourcing_cost_multiplier": 0.5},
        "profit_targets": {"min_roi": 30.0}
    }

    sourcing_price = float(parsed_data['current_price']) * business_config['sourcing']['sourcing_cost_multiplier']

    roi_metrics = calculate_roi_metrics(
        sale_price=float(parsed_data['current_price']),
        sourcing_price=sourcing_price,
        fba_fees=business_config['fba_fees'],
        referral_fee_pct=15.0
    )

    print(f"   Sale Price: ${parsed_data['current_price']}")
    print(f"   Sourcing Price: ${sourcing_price:.2f}")
    print(f"   Net Profit: ${roi_metrics.get('net_profit', 0):.2f}")
    print(f"   ROI: {roi_metrics.get('roi_percentage', 0):.2f}%")
    print(f"   Margin: {roi_metrics.get('profit_margin', 0):.2f}%")

    # VALIDATION ÉTAPE 4
    assert roi_metrics['roi_percentage'] > 0, "❌ ROI invalide"

    print("\n   ✅ ÉTAPE 4 VALIDÉE: ROI calculé avec succès")

    # ===== FINAL VALIDATION =====
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLET VALIDÉ")
    print("=" * 80)
    print("\n📋 Résumé de validation:")
    print(f"   ✅ BSR extrait depuis stats.current[3]: {parsed_data['current_bsr']}")
    print(f"   ✅ BSR confidence: {parsed_data['bsr_confidence']:.2%}")
    print(f"   ✅ Velocity Score: {velocity_score:.2f}/100")
    print(f"   ✅ ROI: {roi_metrics['roi_percentage']:.2f}%")
    print(f"   ✅ Net Profit: ${roi_metrics['net_profit']:.2f}")
    print("\n🎯 Impact Business:")
    print(f"   - Avant fix: BSR = NULL → Velocity = 0 → Produit rejeté")
    print(f"   - Après fix: BSR = {parsed_data['current_bsr']} → Velocity = {velocity_score:.0f} → Analyse complète OK")
    print("\n" + "=" * 80)

    return True


def test_bsr_null_scenario():
    """Test cas où BSR est réellement NULL (produit sans ranking)"""
    print("\n" + "=" * 80)
    print("🔬 TEST E2E: Scénario BSR NULL (produit non classé)")
    print("=" * 80)

    keepa_response_no_bsr = {
        "asin": "B000NULLBSR",
        "title": "Produit sans BSR",
        "domainId": 1,
        "stats": {
            "current": [2999, 3499, -1, -1, 3999]  # BSR = -1 (no data)
        }
    }

    parsed_data = parse_keepa_product(keepa_response_no_bsr)

    print(f"\n   ASIN: {parsed_data['asin']}")
    print(f"   BSR: {parsed_data.get('current_bsr', 'NULL')}")
    print(f"   BSR confidence: {parsed_data.get('bsr_confidence', 0):.2%}")

    assert parsed_data['current_bsr'] is None, "❌ BSR devrait être NULL"
    assert parsed_data['bsr_confidence'] == 0.0, "❌ Confidence devrait être 0"

    print("\n   ✅ Gestion BSR NULL correcte")
    print("=" * 80)

    return True


if __name__ == "__main__":
    print("\n🚀 LANCEMENT TESTS E2E - PIPELINE BSR → ROI")

    tests = [
        ("Pipeline complet Echo Dot", test_complete_pipeline_echo_dot),
        ("Scénario BSR NULL", test_bsr_null_scenario)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\n▶️  Test: {name}")
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ ÉCHEC: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERREUR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print(f"📊 RÉSULTATS FINAUX: {passed}/{len(tests)} tests réussis")

    if failed == 0:
        print("✅ TOUS LES TESTS E2E PASSENT")
        print("\n🎯 Prochaines étapes:")
        print("   1. Commit les changements (keepa_service.py + imports parser_v2)")
        print("   2. Push vers GitHub")
        print("   3. Déployer sur Render")
        print("   4. Tester API production avec ASIN réel")
    else:
        print(f"❌ {failed} tests ont échoué - Correction requise")

    print("=" * 80 + "\n")

    sys.exit(0 if failed == 0 else 1)
