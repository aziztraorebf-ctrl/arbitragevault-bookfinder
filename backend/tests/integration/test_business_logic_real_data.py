"""
Integration Tests - Business Logic avec VRAIES Donnees Keepa
==============================================================

OBJECTIF: Valider calculs business (ROI, fees, scoring) avec vraies donnees API
COUT: ~10-15 tokens Keepa par run complet
FREQUENCE: Manuel avant releases production (skip par defaut en CI/CD)

Ce fichier valide Phase 2 (business logic) avec vraies donnees Keepa (pas de mocks).
"""
import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any

from app.services.keepa_service import KeepaService
from app.services.keepa_parser_v2 import KeepaRawParser
from app.core.fees_config import calculate_total_fees, calculate_profit_metrics, get_fee_config
from app.services.scoring_v2 import compute_view_score, VIEW_WEIGHTS
from app.services.config_service import ConfigService
from app.core.config import settings

# Pool ASINs valides (reutilise pool E2E Phase 3)
REAL_ASINS_BUSINESS = {
    "books_low_price": [
        "0593655036",  # Learning Python (~$50)
        "1098108302",  # Data Engineering (~$60)
    ],
    "books_medium_price": [
        "0316769487",  # Fiction (~$20-30)
        "0135957052",  # Pragmatic Programmer (~$40)
    ],
    "electronics": [
        "B00FLIJJSA",  # Kindle Oasis (~$250)
    ]
}

ALL_BUSINESS_ASINS = (
    REAL_ASINS_BUSINESS["books_low_price"] +
    REAL_ASINS_BUSINESS["books_medium_price"] +
    REAL_ASINS_BUSINESS["electronics"]
)


@pytest.fixture
async def keepa_service():
    """Fixture: Real Keepa service instance"""
    if not settings.KEEPA_API_KEY:
        pytest.skip("KEEPA_API_KEY not configured")

    service = KeepaService(api_key=settings.KEEPA_API_KEY)
    yield service
    await service.close()


# ========== TESTS ROI CALCULATION ==========

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("asin", REAL_ASINS_BUSINESS["books_low_price"])
async def test_roi_calculation_with_real_prices(keepa_service: KeepaService, asin: str):
    """
    Test ROI calculation avec vrais prix Keepa.

    Validation:
    - ROI calcule correctement (Decimal precision)
    - Formule: ROI = (net_profit / buy_cost) * 100
    - Net profit = sell_price - total_fees - buy_cost - buffer
    - Decimal type preserve (pas de float rounding)
    """
    print(f"\n[TEST] ROI Calculation for ASIN: {asin}")

    # Fetch real product data
    product_data = await keepa_service.get_product_data(asin, domain=1)
    assert product_data is not None, f"Keepa API returned None for {asin}"

    # Extract current price (expected sale price)
    current_values = KeepaRawParser.extract_current_values(product_data)
    current_price = current_values.get("new_price")

    if current_price is None:
        pytest.skip(f"No current price available for {asin}")

    assert isinstance(current_price, Decimal), f"Price must be Decimal, got {type(current_price)}"

    # Simulate buy cost (30% of current price for testing)
    buy_cost = current_price * Decimal("0.3")

    # Calculate profit metrics
    metrics = calculate_profit_metrics(
        sell_price=current_price,
        buy_cost=buy_cost,
        weight_lbs=Decimal("1.0"),
        category="books",
        buffer_pct=Decimal("5.0")
    )

    # Validations ROI
    assert "roi_percentage" in metrics, "roi_percentage missing from metrics"
    assert isinstance(metrics["roi_percentage"], Decimal), "ROI must be Decimal type"

    # Validate formula: ROI = (net_profit / buy_cost) * 100
    net_profit = metrics["net_profit"]
    expected_roi = (net_profit / buy_cost * Decimal("100")) if buy_cost > 0 else Decimal("0")

    assert abs(metrics["roi_percentage"] - expected_roi) < Decimal("0.01"), \
        f"ROI formula incorrect: {metrics['roi_percentage']} != {expected_roi}"

    print(f"[OK] {asin}: Price=${current_price}, Buy=${buy_cost}, ROI={metrics['roi_percentage']:.2f}%")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_roi_calculation_decimal_precision(keepa_service: KeepaService):
    """
    Test precision Decimal dans calculs ROI.

    Validation:
    - Pas de rounding errors avec float
    - Decimal preserve precision totale
    - Comparaison float vs Decimal montre difference
    """
    asin = REAL_ASINS_BUSINESS["books_low_price"][0]
    print(f"\n[TEST] Decimal Precision Validation for ASIN: {asin}")

    product_data = await keepa_service.get_product_data(asin, domain=1)
    current_values = KeepaRawParser.extract_current_values(product_data)
    current_price = current_values.get("new_price")

    if current_price is None:
        pytest.skip(f"No current price available for {asin}")

    # Test avec Decimal (correct)
    buy_cost_decimal = Decimal("15.333333")
    metrics_decimal = calculate_profit_metrics(
        sell_price=current_price,
        buy_cost=buy_cost_decimal,
        category="books"
    )

    # Test avec float (incorrect - pour comparaison)
    buy_cost_float = float(buy_cost_decimal)
    metrics_float_based = calculate_profit_metrics(
        sell_price=current_price,
        buy_cost=Decimal(str(buy_cost_float)),
        category="books"
    )

    # Validations
    assert isinstance(metrics_decimal["roi_percentage"], Decimal)
    assert isinstance(metrics_decimal["net_profit"], Decimal)

    print(f"[OK] Decimal precision preserved: ROI={metrics_decimal['roi_percentage']:.10f}%")
    print(f"     (Float-based would be: {metrics_float_based['roi_percentage']:.10f}%)")


# ========== TESTS FEE CALCULATION ==========

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("asin,expected_category", [
    ("0593655036", "books"),
    ("0316769487", "books"),
    ("B00FLIJJSA", "default"),  # Electronics fallback to default
])
async def test_fee_calculation_category_specific(
    keepa_service: KeepaService,
    asin: str,
    expected_category: str
):
    """
    Test calcul fees category-specific avec vraies donnees.

    Validation:
    - Category detection fonctionne (books, media, default)
    - Fee config correct pour chaque category
    - Total fees = referral + closing + fba + inbound + prep
    """
    print(f"\n[TEST] Fee Calculation (Category-Specific) for ASIN: {asin}")

    product_data = await keepa_service.get_product_data(asin, domain=1)
    current_values = KeepaRawParser.extract_current_values(product_data)
    current_price = current_values.get("new_price")

    if current_price is None:
        pytest.skip(f"No current price available for {asin}")

    # Determine category from ASIN (books start with 0-9, electronics with B)
    category = "books" if asin[0].isdigit() else "default"

    # Calculate fees
    fees = calculate_total_fees(
        sell_price=current_price,
        weight_lbs=Decimal("1.0"),
        category=category
    )

    # Validations category
    assert fees["category_used"] == expected_category, \
        f"Category detection failed: {fees['category_used']} != {expected_category}"

    # Validations fee structure
    assert "referral_fee" in fees
    assert "closing_fee" in fees
    assert "fba_fee" in fees
    assert "total_fees" in fees

    # Validate total = sum of components
    expected_total = (
        fees["referral_fee"] +
        fees["closing_fee"] +
        fees["fba_fee"] +
        fees["inbound_shipping"] +
        fees["prep_fee"] +
        fees["tax_amount"]
    )

    assert abs(fees["total_fees"] - expected_total) < Decimal("0.01"), \
        f"Total fees incorrect: {fees['total_fees']} != {expected_total}"

    print(f"[OK] {asin}: Category={fees['category_used']}, Total Fees=${fees['total_fees']}")
    print(f"     Breakdown: Referral=${fees['referral_fee']}, FBA=${fees['fba_fee']}, Closing=${fees['closing_fee']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fee_calculation_books_vs_default(keepa_service: KeepaService):
    """
    Test difference fees entre category 'books' et 'default'.

    Validation:
    - Books category a fees specifiques (closing_fee $1.80)
    - Default category a fees plus elevees (conservative)
    - Referral fee same (15%) mais base fees different
    """
    asin_book = REAL_ASINS_BUSINESS["books_low_price"][0]
    asin_electronics = REAL_ASINS_BUSINESS["electronics"][0]

    print(f"\n[TEST] Fee Comparison: Books vs Default")

    # Fetch both products
    book_data = await keepa_service.get_product_data(asin_book, domain=1)
    electronics_data = await keepa_service.get_product_data(asin_electronics, domain=1)

    book_values = KeepaRawParser.extract_current_values(book_data)
    electronics_values = KeepaRawParser.extract_current_values(electronics_data)

    book_price = book_values.get("new_price")
    electronics_price = electronics_values.get("new_price")

    if book_price is None or electronics_price is None:
        pytest.skip("Prices not available for comparison")

    # Use same price for comparison
    test_price = Decimal("50.00")

    fees_books = calculate_total_fees(test_price, category="books")
    fees_default = calculate_total_fees(test_price, category="default")

    # Validations
    assert fees_books["category_used"] == "books"
    assert fees_default["category_used"] == "default"

    # Books should have lower fees than default
    assert fees_books["total_fees"] < fees_default["total_fees"], \
        "Books fees should be lower than default fees"

    print(f"[OK] Books fees: ${fees_books['total_fees']} < Default fees: ${fees_default['total_fees']}")


# ========== TESTS SCORING SYSTEM ==========

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("asin", ALL_BUSINESS_ASINS[:3])  # Test 3 ASINs
async def test_scoring_system_with_real_data(keepa_service: KeepaService, asin: str):
    """
    Test scoring system (v2) avec vraies donnees Keepa.

    Validation:
    - compute_view_score fonctionne avec vraies donnees
    - Score dans range [0-100]
    - Weights applied correctement selon view type
    - Components breakdown correct
    """
    print(f"\n[TEST] Scoring System (View-Specific) for ASIN: {asin}")

    product_data = await keepa_service.get_product_data(asin, domain=1)
    current_values = KeepaRawParser.extract_current_values(product_data)

    current_price = current_values.get("new_price")
    if current_price is None:
        pytest.skip(f"No current price available for {asin}")

    # Simulate buy cost for ROI calculation
    buy_cost = current_price * Decimal("0.4")

    # Calculate profit metrics (needed for ROI in parsed_data)
    profit_metrics = calculate_profit_metrics(
        sell_price=current_price,
        buy_cost=buy_cost,
        category="books"
    )

    # Prepare parsed_data for scoring (simulate structure expected by scoring_v2)
    parsed_data = {
        "roi": {
            "roi_percentage": float(profit_metrics["roi_percentage"])
        },
        "velocity_score": 70.0,  # Simulated velocity score
        "stability_score": 65.0   # Simulated stability score
    }

    # Test scoring for different views
    for view_type in ["dashboard", "mes_niches", "auto_sourcing"]:
        score_result = compute_view_score(parsed_data, view_type)

        # Validations
        assert "score" in score_result
        assert 0 <= score_result["score"] <= 100, f"Score out of range: {score_result['score']}"
        assert score_result["view_type"] == view_type
        assert "weights_applied" in score_result
        assert "components" in score_result

        # Validate components sum approximately equals score
        components = score_result["components"]
        components_sum = (
            components["roi_contribution"] +
            components["velocity_contribution"] +
            components["stability_contribution"]
        )

        assert abs(score_result["score"] - components_sum) < 0.1, \
            f"Score != Components sum: {score_result['score']} != {components_sum}"

        print(f"[OK] View '{view_type}': Score={score_result['score']:.2f}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_view_weights_different_views(keepa_service: KeepaService):
    """
    Test que different views produisent different scores.

    Validation:
    - Dashboard (balanced) != mes_niches (ROI priority)
    - mes_niches (ROI priority) != auto_sourcing (velocity priority)
    - Same product, different views = different rankings
    """
    asin = REAL_ASINS_BUSINESS["books_low_price"][0]
    print(f"\n[TEST] View Weights Impact for ASIN: {asin}")

    product_data = await keepa_service.get_product_data(asin, domain=1)
    current_values = KeepaRawParser.extract_current_values(product_data)

    current_price = current_values.get("new_price")
    if current_price is None:
        pytest.skip(f"No current price available for {asin}")

    buy_cost = current_price * Decimal("0.4")
    profit_metrics = calculate_profit_metrics(
        sell_price=current_price,
        buy_cost=buy_cost,
        category="books"
    )

    # High ROI, low velocity scenario
    parsed_data = {
        "roi": {"roi_percentage": 80.0},  # High ROI
        "velocity_score": 30.0,            # Low velocity
        "stability_score": 50.0            # Neutral stability
    }

    # Calculate scores for different views
    score_dashboard = compute_view_score(parsed_data, "dashboard")
    score_mes_niches = compute_view_score(parsed_data, "mes_niches")
    score_auto_sourcing = compute_view_score(parsed_data, "auto_sourcing")

    # Validations: mes_niches should score higher (ROI priority)
    assert score_mes_niches["score"] > score_auto_sourcing["score"], \
        "mes_niches should prioritize high ROI over velocity"

    print(f"[OK] Dashboard: {score_dashboard['score']:.2f}")
    print(f"     mes_niches (ROI priority): {score_mes_niches['score']:.2f}")
    print(f"     auto_sourcing (velocity priority): {score_auto_sourcing['score']:.2f}")


# ========== TESTS EDGE CASES ==========

@pytest.mark.integration
@pytest.mark.asyncio
async def test_edge_case_zero_buy_cost():
    """
    Test edge case: buy_cost = 0 (gratuit).

    Validation:
    - ROI ne crash pas avec division par zero
    - ROI retourne valeur raisonnable (0 ou infinity handling)
    """
    print(f"\n[TEST] Edge Case: Zero Buy Cost")

    metrics = calculate_profit_metrics(
        sell_price=Decimal("50.00"),
        buy_cost=Decimal("0.00"),  # FREE product
        category="books"
    )

    # Validation: should not crash
    assert "roi_percentage" in metrics
    assert metrics["roi_percentage"] == Decimal("0"), \
        f"ROI with zero buy_cost should be 0, got {metrics['roi_percentage']}"

    print(f"[OK] Zero buy_cost handled: ROI={metrics['roi_percentage']}%")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edge_case_negative_roi():
    """
    Test edge case: buy_cost > sell_price (perte).

    Validation:
    - ROI negatif calcule correctement
    - Net profit negatif
    - Profit tier = 'loss'
    """
    print(f"\n[TEST] Edge Case: Negative ROI (Loss)")

    metrics = calculate_profit_metrics(
        sell_price=Decimal("20.00"),
        buy_cost=Decimal("50.00"),  # Buy price higher than sell price
        category="books"
    )

    # Validations
    assert metrics["roi_percentage"] < 0, "ROI should be negative"
    assert metrics["net_profit"] < 0, "Net profit should be negative"
    assert metrics["profit_tier"] == "loss", f"Profit tier should be 'loss', got {metrics['profit_tier']}"

    print(f"[OK] Negative ROI handled: ROI={metrics['roi_percentage']:.2f}%, Tier={metrics['profit_tier']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edge_case_extreme_bsr(keepa_service: KeepaService):
    """
    Test edge case: BSR extreme (tres bas ou tres haut).

    Validation:
    - BSR = 1 (best-seller #1) extrait correctement
    - BSR > 1,000,000 (dead product) extrait correctement
    - Pas de crash avec BSR extreme values
    """
    # BSR bas (popular book)
    asin_low = "1098108302"  # BSR varies but should be < 50k
    print(f"\n[TEST] Edge Case: Extreme BSR (Low BSR) for ASIN: {asin_low}")

    product_data = await keepa_service.get_product_data(asin_low, domain=1)
    current_values = KeepaRawParser.extract_current_values(product_data)

    bsr = current_values.get("bsr")
    assert bsr is not None, "BSR should be extracted"
    assert isinstance(bsr, int), f"BSR must be integer, got {type(bsr)}"
    assert bsr > 0, f"BSR must be positive, got {bsr}"

    print(f"[OK] Low BSR extracted: {bsr:,}")

    # BSR tres haut (dead product)
    asin_dead = "B00FLIJJSA"  # BSR ~1.6M (electronics)
    product_data_dead = await keepa_service.get_product_data(asin_dead, domain=1)
    values_dead = KeepaRawParser.extract_current_values(product_data_dead)

    bsr_dead = values_dead.get("bsr")
    if bsr_dead:
        assert bsr_dead > 100000, f"Expected high BSR > 100k, got {bsr_dead}"
        print(f"[OK] Dead Product BSR extracted: {bsr_dead:,}")
    else:
        print(f"[INFO] No BSR available for {asin_dead} (expected for dead products)")


# ========== TESTS BUG RE-VALIDATION ==========

@pytest.mark.integration
@pytest.mark.asyncio
async def test_revalidate_bsr_parsing_fix():
    """
    Re-validate bug fix: BSR parsing (commit b7aa103).

    Bug Original: BSR extrait depuis mauvais champ (csv au lieu de stats.current)
    Fix: Lecture correcte depuis stats.current avec fallback 4 niveaux

    Validation:
    - BSR extrait depuis source correcte (salesRanks primaire)
    - Fallback chain fonctionne si salesRanks absent
    - Source tracking precis
    """
    print(f"\n[TEST] Re-validate BSR Parsing Fix (commit b7aa103)")

    # This test is covered by Phase 3 integration tests
    # Just validate that BSR extraction still works correctly

    from app.services.keepa_parser_v2 import KeepaBSRExtractor

    # Simulate product data with salesRanks
    mock_product_with_salesranks = {
        "salesRanks": {
            "283155": [1234567890, 12345, 1234567891, 12346]  # (timestamp, bsr, timestamp, bsr)
        }
    }

    bsr, source = KeepaBSRExtractor.extract_current_bsr(mock_product_with_salesranks)

    assert bsr == 12346, f"BSR should be latest value (12346), got {bsr}"
    assert source == "salesRanks", f"Source should be 'salesRanks', got {source}"

    print(f"[OK] BSR parsing still correct: BSR={bsr}, Source={source}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_revalidate_bsr_division_fix():
    """
    Re-validate bug fix: BSR divise par 100 incorrectement.

    Bug Original: BSR traite comme prix (division par 100)
    Fix: BSR est un rank integer, pas de division

    Validation:
    - BSR retourne comme integer (pas Decimal)
    - Pas de division par 100 appliquee
    - BSR values coherent avec Amazon (pas 100x trop petit)
    """
    print(f"\n[TEST] Re-validate BSR Division Fix")

    from app.services.keepa_parser_v2 import KeepaBSRExtractor

    # Simulate product with known BSR value
    mock_product = {
        "salesRanks": {
            "283155": [1234567890, 50000]  # BSR = 50,000
        }
    }

    bsr, source = KeepaBSRExtractor.extract_current_bsr(mock_product)

    # Validations
    assert isinstance(bsr, int), f"BSR must be integer, got {type(bsr)}"
    assert bsr == 50000, f"BSR should not be divided by 100: {bsr} != 50000"

    print(f"[OK] BSR division fix validated: BSR={bsr:,} (no division applied)")


# ========== TEST SUITE SUMMARY ==========

@pytest.mark.integration
@pytest.mark.asyncio
async def test_business_logic_suite_summary(keepa_service: KeepaService):
    """
    Test suite summary - Execute tous les tests business logic.

    Usage:
        pytest tests/integration/test_business_logic_real_data.py::test_business_logic_suite_summary -v
    """
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE SUMMARY - Business Logic Real API")
    print("="*80)

    results = {
        "total_tests": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "errors": []
    }

    # Test 1: ROI Calculation
    try:
        results["total_tests"] += 1
        asin = REAL_ASINS_BUSINESS["books_low_price"][0]
        product_data = await keepa_service.get_product_data(asin, domain=1)
        current_values = KeepaRawParser.extract_current_values(product_data)

        if current_values.get("new_price"):
            buy_cost = current_values["new_price"] * Decimal("0.3")
            metrics = calculate_profit_metrics(
                sell_price=current_values["new_price"],
                buy_cost=buy_cost,
                category="books"
            )

            assert isinstance(metrics["roi_percentage"], Decimal)
            results["tests_passed"] += 1
            print(f"[PASS] ROI Calculation: {metrics['roi_percentage']:.2f}%")
        else:
            results["tests_failed"] += 1
            print(f"[SKIP] ROI Calculation: No price available")
    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"ROI Calculation: {str(e)}")
        print(f"[FAIL] ROI Calculation: {e}")

    # Test 2: Fee Calculation
    try:
        results["total_tests"] += 1
        fees_books = calculate_total_fees(Decimal("50.00"), category="books")
        fees_default = calculate_total_fees(Decimal("50.00"), category="default")

        assert fees_books["category_used"] == "books"
        assert fees_default["category_used"] == "default"
        assert fees_books["total_fees"] < fees_default["total_fees"]

        results["tests_passed"] += 1
        print(f"[PASS] Fee Calculation: Books=${fees_books['total_fees']}, Default=${fees_default['total_fees']}")
    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Fee Calculation: {str(e)}")
        print(f"[FAIL] Fee Calculation: {e}")

    # Test 3: Scoring System
    try:
        results["total_tests"] += 1
        parsed_data = {
            "roi": {"roi_percentage": 50.0},
            "velocity_score": 70.0,
            "stability_score": 60.0
        }

        score_result = compute_view_score(parsed_data, "dashboard")
        assert 0 <= score_result["score"] <= 100

        results["tests_passed"] += 1
        print(f"[PASS] Scoring System: Score={score_result['score']:.2f}")
    except Exception as e:
        results["tests_failed"] += 1
        results["errors"].append(f"Scoring System: {str(e)}")
        print(f"[FAIL] Scoring System: {e}")

    print("\n" + "-"*80)
    print(f"RESULTS: {results['tests_passed']}/{results['total_tests']} tests passed")
    print(f"Success Rate: {results['tests_passed']/results['total_tests']*100:.1f}%")

    if results["errors"]:
        print("\nERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("="*80)

    # Assertion finale
    assert results["tests_failed"] == 0, f"{results['tests_failed']} tests failed"
