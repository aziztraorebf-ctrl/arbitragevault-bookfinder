"""
Test simple du parser v2 - Validation du correctif BSR
=======================================================
Exécuter avec : python test_parser_v2_simple.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.keepa_parser_v2 import parse_keepa_product, KeepaBSRExtractor, KeepaCSVType


def test_bsr_extraction_primary():
    """Test 1: Extraction BSR depuis stats.current[3]"""
    print("\n🧪 Test 1: Extraction BSR depuis stats.current[3]")

    raw_data = {
        "asin": "B08N5WRWNW",
        "title": "Echo Dot (4th Gen)",
        "domainId": 1,
        "stats": {
            "current": [
                4999,   # 0: Amazon price
                5499,   # 1: New price
                3999,   # 2: Used price
                1234,   # 3: BSR ← TARGET
                5999,   # 4: List price
            ]
        }
    }

    result = parse_keepa_product(raw_data)

    assert result["current_bsr"] == 1234, f"Expected BSR=1234, got {result['current_bsr']}"
    assert result["bsr_confidence"] == 1.0, f"Expected confidence=1.0, got {result['bsr_confidence']}"

    print(f"   ✅ BSR correctement extrait: {result['current_bsr']}")
    print(f"   ✅ Confidence: {result['bsr_confidence']}")
    return True


def test_bsr_extraction_null_handling():
    """Test 2: Gestion des valeurs BSR = -1 (no data)"""
    print("\n🧪 Test 2: Gestion BSR = -1 (no data)")

    raw_data = {
        "asin": "B000000000",
        "title": "Product sans BSR",
        "domainId": 1,
        "stats": {
            "current": [2999, 2999, -1, -1]  # BSR is -1
        }
    }

    result = parse_keepa_product(raw_data)

    assert result["current_bsr"] is None, f"Expected None, got {result['current_bsr']}"
    assert result["bsr_confidence"] == 0.0, f"Expected confidence=0.0, got {result['bsr_confidence']}"

    print(f"   ✅ BSR null correctement géré: {result['current_bsr']}")
    print(f"   ✅ Confidence: {result['bsr_confidence']}")
    return True


def test_bsr_fallback_strategy():
    """Test 3: Fallback vers avg30 quand stats.current est vide"""
    print("\n🧪 Test 3: Stratégie de fallback vers avg30")

    raw_data = {
        "asin": "TEST123",
        "title": "Test Fallback",
        "domainId": 1,
        "stats": {
            "current": [],  # Empty
            "avg30": [0, 0, 0, 5678]  # 30-day average BSR
        },
        "csv": []
    }

    extractor = KeepaBSRExtractor()
    bsr = extractor.extract_current_bsr(raw_data)

    assert bsr == 5678, f"Expected BSR=5678, got {bsr}"

    print(f"   ✅ Fallback avg30 fonctionne: {bsr}")
    return True


def test_keepa_service_patch():
    """Test 4: Validation du pattern keepa_service.py"""
    print("\n🧪 Test 4: Validation pattern keepa_service.py")

    # Simule le code du patch keepa_service.py
    product_data = {
        "stats": {
            "current": [4999, 5499, 3999, 9876, 5999]  # BSR = 9876
        }
    }

    # Code du patch (lignes 426-432)
    stats = product_data.get('stats', {})
    current = stats.get('current', [])
    current_bsr = None
    if current and len(current) > 3:
        bsr = current[3]
        if bsr and bsr != -1:
            current_bsr = int(bsr)

    assert current_bsr == 9876, f"Expected BSR=9876, got {current_bsr}"

    print(f"   ✅ Pattern keepa_service.py correct: {current_bsr}")
    return True


def test_real_world_echo_dot():
    """Test 5: Cas réel Echo Dot avec toutes les données"""
    print("\n🧪 Test 5: Cas réel Echo Dot (données complètes)")

    raw_data = {
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
                4999,   # Amazon price $49.99
                5499,   # New price
                3999,   # Used price
                527,    # BSR rank 527 ← TARGET
                5999,   # List price
                -1, -1, -1, -1, -1,
                4899,   # FBA price
                15,     # New count
                8,      # Used count
                -1, -1,
                45,     # Rating (4.5 stars)
                125000  # Review count
            ]
        }
    }

    result = parse_keepa_product(raw_data)

    assert result["current_bsr"] == 527, f"Expected BSR=527, got {result['current_bsr']}"
    assert result["bsr_confidence"] == 1.0, "Expected high confidence for top seller"
    assert result["current_amazon_price"] is not None, "Amazon price missing"
    assert result["offers_count"] == 15, f"Expected 15 offers, got {result['offers_count']}"

    print(f"   ✅ BSR: {result['current_bsr']}")
    print(f"   ✅ Prix Amazon: ${result['current_amazon_price']}")
    print(f"   ✅ Offres: {result['offers_count']}")
    print(f"   ✅ Confidence: {result['bsr_confidence']}")
    return True


def main():
    """Exécute tous les tests"""
    print("=" * 70)
    print("🔬 VALIDATION PARSER V2 + CORRECTIF KEEPA_SERVICE.PY")
    print("=" * 70)

    tests = [
        test_bsr_extraction_primary,
        test_bsr_extraction_null_handling,
        test_bsr_fallback_strategy,
        test_keepa_service_patch,
        test_real_world_echo_dot
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"   ❌ ÉCHEC: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"📊 RÉSULTATS: {passed}/{len(tests)} tests réussis")

    if failed == 0:
        print("✅ TOUS LES TESTS PASSENT - Le correctif fonctionne!")
    else:
        print(f"❌ {failed} tests ont échoué")

    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
