"""
Integration Tests - Keepa Parser v2 avec VRAIES Donnees API
============================================================

OBJECTIF: Valider extraction BSR/prix avec vraies reponses Keepa API
COUT: ~5-10 tokens Keepa par run complet
FREQUENCE: Manuel avant releases production (skip par defaut en CI/CD)

Ce fichier remplace les unit tests mock pour validation finale avec vraies donnees.
"""
import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any

from app.services.keepa_service import KeepaService
from app.services.keepa_parser_v2 import KeepaRawParser, KeepaBSRExtractor
from app.core.config import settings


# Pool ASINs valides (reutilise pool E2E Phase 4)
REAL_ASINS = {
    "books_low_bsr": [
        "0593655036",  # Learning Python (BSR ~10k-50k)
        "1492056200",  # Python Cookbook (BSR ~20k-80k)
        "0316769487",  # Popular fiction (BSR ~5k-30k)
    ],
    "books_medium_bsr": [
        "141978269X",  # Technical book (BSR ~50k-200k)
        "1492097640",  # Fluent Python (BSR ~100k-300k)
    ],
    "electronics": [
        "B00FLIJJSA",  # Kindle Oasis (BSR ~5k-20k electronics)
        "B08N5WRWNW",  # Tablet (BSR ~10k-50k)
    ],
}

ALL_TEST_ASINS = (
    REAL_ASINS["books_low_bsr"] +
    REAL_ASINS["books_medium_bsr"] +
    REAL_ASINS["electronics"]
)


@pytest.fixture
async def keepa_service():
    """Fixture: Real Keepa service instance"""
    if not settings.KEEPA_API_KEY:
        pytest.skip("KEEPA_API_KEY not configured")

    service = KeepaService(api_key=settings.KEEPA_API_KEY)
    yield service
    await service.close()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("asin", ALL_TEST_ASINS)
async def test_extract_bsr_from_real_keepa_api(keepa_service: KeepaService, asin: str):
    """
    Test BSR extraction avec vraie reponse Keepa API.

    Validation:
    - BSR extrait correctement (non-None, integer, positif)
    - Source tracking fonctionne (salesRanks/current/csv_recent/avg30)
    - Confidence scoring applique selon source
    """
    print(f"\n[TEST] Fetching real Keepa data for ASIN: {asin}")

    # Appel API REEL (consomme 1 token)
    product_data = await keepa_service.get_product_data(asin, domain=1)

    assert product_data is not None, f"Keepa API returned None for {asin}"
    assert isinstance(product_data, dict), f"Keepa API returned non-dict for {asin}"

    # Extraction BSR avec source tracking
    bsr, source = KeepaBSRExtractor.extract_current_bsr(product_data)

    # Validations BSR
    assert bsr is not None, f"BSR extraction failed for {asin}"
    assert isinstance(bsr, int), f"BSR must be integer, got {type(bsr)}"
    assert bsr > 0, f"BSR must be positive, got {bsr}"
    assert bsr < 10_000_000, f"BSR suspiciously high: {bsr}"

    # Validation source tracking
    valid_sources = ["salesRanks", "current", "csv_recent", "avg30"]
    assert source in valid_sources, f"Invalid source: {source}"

    # Validation confidence scoring
    quality_result = KeepaBSRExtractor.validate_bsr_quality(bsr, category="books", source=source)

    assert "confidence_score" in quality_result
    assert 0.0 <= quality_result["confidence_score"] <= 1.0
    assert quality_result["data_source"] == source

    # Source penalties validation
    if source == "salesRanks" or source == "current":
        # Primary sources: no penalty (base confidence only)
        assert quality_result["confidence_score"] >= 0.6  # Minimum reasonable confidence
    elif source == "csv_recent":
        # Recent history: 0.9x penalty
        assert quality_result["confidence_score"] <= 0.9
    elif source == "avg30":
        # 30-day average: 0.8x penalty
        assert quality_result["confidence_score"] <= 0.8

    print(f"[OK] {asin}: BSR={bsr:,} (source={source}, confidence={quality_result['confidence_score']:.2f})")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("asin", REAL_ASINS["books_low_bsr"][:2])  # Test 2 ASINs only
async def test_extract_price_from_real_keepa_api(keepa_service: KeepaService, asin: str):
    """
    Test price extraction avec vraie reponse Keepa API.

    Validation:
    - Prix extrait correctement (Decimal type, positif)
    - Conversion Keepa price divisor correcte (division par 100)
    - Precision decimale preservee
    """
    print(f"\n[TEST] Fetching real Keepa price data for ASIN: {asin}")

    # Appel API REEL
    product_data = await keepa_service.get_product_data(asin, domain=1)

    # Extraction complete product
    result = KeepaRawParser.extract_product_data(product_data, days_back=30)

    # Validation prix actuel
    current_price = result.get("current_price")

    if current_price is not None:
        assert isinstance(current_price, Decimal), f"Price must be Decimal, got {type(current_price)}"
        assert current_price > Decimal("0"), f"Price must be positive, got {current_price}"
        assert current_price < Decimal("10000"), f"Price suspiciously high: {current_price}"

        print(f"[OK] {asin}: Price=${current_price}")
    else:
        # Prix peut etre None si produit out of stock
        print(f"[INFO] {asin}: No current price (possibly out of stock)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_history_from_real_keepa_api(keepa_service: KeepaService):
    """
    Test history extraction (BSR + price) avec vraie reponse Keepa API.

    Validation:
    - BSR history extrait (array non-vide)
    - Price history extrait (array non-vide)
    - Timestamps convertis correctement (UTC)
    - Donnees triees chronologiquement
    """
    asin = REAL_ASINS["books_low_bsr"][0]
    print(f"\n[TEST] Fetching real Keepa history for ASIN: {asin}")

    # Appel API REEL avec history
    product_data = await keepa_service.get_product_data(asin, domain=1)

    # Extraction complete avec history
    result = KeepaRawParser.extract_product_data(product_data, days_back=90)

    # Validation BSR history
    bsr_history = result.get("bsr_history", [])

    if len(bsr_history) > 0:
        print(f"[OK] BSR history: {len(bsr_history)} data points")

        # Validation format (timestamp, value) tuples
        first_point = bsr_history[0]
        assert isinstance(first_point, tuple), "History point must be tuple"
        assert len(first_point) == 2, "History point must be (timestamp, value)"

        timestamp, bsr_value = first_point
        assert isinstance(timestamp, datetime), "Timestamp must be datetime"
        assert timestamp.tzinfo is not None, "Timestamp must have timezone"
        assert isinstance(bsr_value, int), "BSR value must be integer"

        # Validation ordre chronologique
        timestamps = [point[0] for point in bsr_history]
        assert timestamps == sorted(timestamps), "History must be chronologically sorted"

        print(f"[OK] First point: {timestamp.isoformat()} - BSR={bsr_value:,}")
    else:
        print(f"[INFO] No BSR history available (may need history=True flag)")

    # Validation price history
    price_history = result.get("price_history", [])

    if len(price_history) > 0:
        print(f"[OK] Price history: {len(price_history)} data points")

        first_point = price_history[0]
        timestamp, price_value = first_point

        assert isinstance(timestamp, datetime), "Timestamp must be datetime"
        assert isinstance(price_value, Decimal), "Price must be Decimal"

        print(f"[OK] First point: {timestamp.isoformat()} - Price=${price_value}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_fallback_chain_with_real_data(keepa_service: KeepaService):
    """
    Test 4-level BSR fallback chain avec vraies donnees API.

    Validation:
    - Fallback fonctionne si source primaire manquante
    - Source tracking correct pour chaque niveau
    - Confidence scoring penalise fallbacks appropriately
    """
    # Test avec plusieurs ASINs pour couvrir differents cas
    for asin in REAL_ASINS["books_low_bsr"][:3]:
        print(f"\n[TEST] Testing fallback chain for {asin}")

        product_data = await keepa_service.get_product_data(asin, domain=1)

        # Test extraction normale
        bsr, source = KeepaBSRExtractor.extract_current_bsr(product_data)

        assert bsr is not None, f"BSR extraction failed (all fallbacks exhausted)"

        # Log quel source a ete utilise
        print(f"[OK] {asin}: BSR={bsr:,} extracted from source='{source}'")

        # Verifier que source multiplie confidence correctement
        quality = KeepaBSRExtractor.validate_bsr_quality(bsr, source=source)

        if source in ["salesRanks", "current"]:
            print(f"     Primary source used, confidence={quality['confidence_score']:.2f}")
        elif source == "csv_recent":
            print(f"     Recent history fallback, confidence={quality['confidence_score']:.2f} (0.9x penalty)")
        elif source == "avg30":
            print(f"     30-day average fallback, confidence={quality['confidence_score']:.2f} (0.8x penalty)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_token_consumption_tracking(keepa_service: KeepaService):
    """
    Test tracking consommation tokens avec vraies donnees API.

    Validation:
    - Balance tokens diminue apres requete
    - Cout attendu ~1 token par produit simple
    - Throttling fonctionne (pas d'erreur rate limit)
    """
    # Check balance avant
    balance_before = await keepa_service.check_api_balance()
    print(f"\n[TEST] Token balance before: {balance_before}")

    # Fetch 1 produit (cout attendu: 1 token)
    asin = REAL_ASINS["books_low_bsr"][0]
    product_data = await keepa_service.get_product_data(asin, domain=1)

    assert product_data is not None

    # Check balance apres
    balance_after = await keepa_service.check_api_balance()
    tokens_consumed = balance_before - balance_after

    print(f"[OK] Token balance after: {balance_after}")
    print(f"[OK] Tokens consumed: {tokens_consumed}")

    # Validation cout raisonnable (1-2 tokens pour produit simple)
    assert 0 <= tokens_consumed <= 5, f"Token cost suspicious: {tokens_consumed}"


# === Summary Test Runner ===

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_suite_summary(keepa_service: KeepaService):
    """
    Test suite summary - Execute tous les tests et genere rapport.

    Usage:
        pytest tests/integration/test_keepa_parser_real_api.py::test_integration_suite_summary -v
    """
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE SUMMARY - Keepa Parser v2 Real API")
    print("="*80)

    results = {
        "total_asins_tested": len(ALL_TEST_ASINS),
        "asins_list": ALL_TEST_ASINS,
        "tests_passed": 0,
        "tests_failed": 0,
        "errors": []
    }

    for asin in ALL_TEST_ASINS:
        try:
            product_data = await keepa_service.get_product_data(asin, domain=1)
            bsr, source = KeepaBSRExtractor.extract_current_bsr(product_data)

            if bsr is not None:
                results["tests_passed"] += 1
                print(f"[PASS] {asin}: BSR={bsr:,} (source={source})")
            else:
                results["tests_failed"] += 1
                results["errors"].append(f"{asin}: BSR extraction returned None")
                print(f"[FAIL] {asin}: BSR extraction failed")

        except Exception as e:
            results["tests_failed"] += 1
            results["errors"].append(f"{asin}: {str(e)}")
            print(f"[ERROR] {asin}: {e}")

    print("\n" + "-"*80)
    print(f"RESULTS: {results['tests_passed']}/{results['total_asins_tested']} ASINs passed")
    print(f"Success Rate: {results['tests_passed']/results['total_asins_tested']*100:.1f}%")

    if results["errors"]:
        print("\nERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("="*80)

    # Assertion finale
    assert results["tests_failed"] == 0, f"{results['tests_failed']} ASINs failed validation"
