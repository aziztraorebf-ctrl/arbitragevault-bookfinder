"""
🎯 TIER 1 VALIDATION - 30 ASINs Keepa Réels
============================================

Validation avec vraies données API Keepa, pas de mocks.

Catégories testées:
- Best-sellers (BSR 1k-10k) : 8 ASINs
- Mid-tier (BSR 10k-50k) : 6 ASINs
- Textbooks (BSR 50k-200k) : 5 ASINs
- Electronics (BSR 100-5k) : 4 ASINs
- Long-tail (BSR 200k-500k) : 4 ASINs
- Dead products (BSR > 500k) : 2 ASINs
- Edge cases (invalid ASINs) : 1 ASIN

Total: 30 ASINs

Critères de succès: 90%+ (27/30 ASINs parsent correctement)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

BASE_URL = "https://arbitragevault-backend-v2.onrender.com"


@dataclass
class ASINTestCase:
    """Test case pour un ASIN spécifique."""
    asin: str
    category: str
    expected_bsr_range: tuple  # (min, max) ou None si invalide
    description: str


# 30 ASINs réels couvrant tous les cas d'usage
TEST_ASINS = [
    # ===== BEST-SELLERS (BSR 1k-10k) - 8 ASINs =====
    ASINTestCase("0593655036", "best_seller", (1000, 10000), "Anxious Generation (best-seller validé)"),
    ASINTestCase("1668026473", "best_seller", (1000, 10000), "Fourth Wing (fantasy populaire)"),
    ASINTestCase("0385348371", "best_seller", (1000, 10000), "Atomic Habits (non-fiction)"),
    ASINTestCase("1250301696", "best_seller", (1000, 10000), "Iron Flame (suite Fourth Wing)"),
    ASINTestCase("0593418816", "best_seller", (1000, 10000), "A Court of Thorns and Roses"),
    ASINTestCase("0593728092", "best_seller", (1000, 10000), "The Women (Kristin Hannah)"),
    ASINTestCase("0735219095", "best_seller", (1000, 10000), "Where the Crawdads Sing"),
    ASINTestCase("0316769177", "best_seller", (1000, 10000), "The Catcher in the Rye"),

    # ===== MID-TIER (BSR 10k-50k) - 6 ASINs =====
    ASINTestCase("0062316095", "mid_tier", (10000, 50000), "Sapiens (Yuval Noah Harari)"),
    ASINTestCase("0143127748", "mid_tier", (10000, 50000), "Thinking Fast and Slow"),
    ASINTestCase("1501110365", "mid_tier", (10000, 50000), "It Ends with Us (Colleen Hoover)"),
    ASINTestCase("0553213695", "mid_tier", (10000, 50000), "A Brief History of Time"),
    ASINTestCase("0345816021", "mid_tier", (10000, 50000), "Fifty Shades of Grey"),
    ASINTestCase("1501139231", "mid_tier", (10000, 50000), "The Seven Husbands of Evelyn Hugo"),

    # ===== TEXTBOOKS (BSR 50k-200k) - 5 ASINs =====
    ASINTestCase("1449355730", "textbook", (50000, 200000), "Learning Python (5e édition)"),
    ASINTestCase("0134685997", "textbook", (50000, 200000), "Effective Java (3e édition)"),
    ASINTestCase("0132350882", "textbook", (50000, 200000), "Clean Code (Robert Martin)"),
    ASINTestCase("0321125215", "textbook", (50000, 200000), "Domain-Driven Design (Eric Evans)"),
    ASINTestCase("0201633612", "textbook", (50000, 200000), "Design Patterns (Gang of Four)"),

    # ===== ELECTRONICS (BSR 100-5k) - 4 ASINs =====
    ASINTestCase("B07ZPKN6YR", "electronics", (100, 5000), "Blink Mini Security Camera"),
    ASINTestCase("B0BSHF7LLL", "electronics", (100, 5000), "Amazon Echo Pop"),
    ASINTestCase("B09B8RXYR3", "electronics", (100, 5000), "Fire TV Stick 4K Max"),
    ASINTestCase("B0D3QK6FC6", "electronics", (100, 5000), "Amazon Echo Dot (5th Gen)"),

    # ===== LONG-TAIL (BSR 200k-500k) - 4 ASINs =====
    ASINTestCase("0136083250", "long_tail", (200000, 500000), "Computer Networks (Tanenbaum)"),
    ASINTestCase("0201835959", "long_tail", (200000, 500000), "The Mythical Man-Month"),
    ASINTestCase("0470128720", "long_tail", (200000, 500000), "Beginning Android Programming"),
    ASINTestCase("0201616416", "long_tail", (200000, 500000), "The Pragmatic Programmer"),

    # ===== DEAD PRODUCTS (BSR > 500k) - 2 ASINs =====
    ASINTestCase("0470112840", "dead", (500000, 2000000), "Windows Vista Secrets (obsolète)"),
    ASINTestCase("0471486922", "dead", (500000, 2000000), "Java 2 For Dummies (obsolète)"),

    # ===== EDGE CASES - 1 ASIN =====
    ASINTestCase("B000INVALID", "invalid", None, "ASIN invalide (devrait échouer)"),
]


@dataclass
class ValidationResult:
    """Résultat de validation pour un ASIN."""
    asin: str
    category: str
    success: bool
    status_code: int
    error_message: Optional[str]
    bsr_parsed: Optional[int]
    bsr_in_expected_range: bool
    parsing_issues: List[str]
    response_time_ms: int


def validate_asin(test_case: ASINTestCase) -> ValidationResult:
    """
    Valide un ASIN contre l'API production Keepa.

    Returns:
        ValidationResult avec détails complets
    """
    print(f"\n📍 Testing {test_case.asin} ({test_case.category})")
    print(f"   {test_case.description}")

    start_time = datetime.now()
    parsing_issues = []

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/keepa/{test_case.asin}/metrics",
            timeout=30
        )

        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Cas 1: ASIN invalide attendu
        if test_case.expected_bsr_range is None:
            if response.status_code in [400, 404]:
                print(f"   ✅ Échec attendu (invalid ASIN)")
                return ValidationResult(
                    asin=test_case.asin,
                    category=test_case.category,
                    success=True,  # Succès = échec attendu
                    status_code=response.status_code,
                    error_message=None,
                    bsr_parsed=None,
                    bsr_in_expected_range=True,
                    parsing_issues=[],
                    response_time_ms=response_time_ms
                )
            else:
                print(f"   ❌ Devrait échouer mais status {response.status_code}")
                return ValidationResult(
                    asin=test_case.asin,
                    category=test_case.category,
                    success=False,
                    status_code=response.status_code,
                    error_message=f"Expected failure but got {response.status_code}",
                    bsr_parsed=None,
                    bsr_in_expected_range=False,
                    parsing_issues=["Invalid ASIN should fail"],
                    response_time_ms=response_time_ms
                )

        # Cas 2: ASIN valide
        if response.status_code != 200:
            print(f"   ❌ Status {response.status_code}")
            error_msg = response.json().get("detail", "Unknown error") if response.text else "No response body"
            return ValidationResult(
                asin=test_case.asin,
                category=test_case.category,
                success=False,
                status_code=response.status_code,
                error_message=error_msg,
                bsr_parsed=None,
                bsr_in_expected_range=False,
                parsing_issues=[f"HTTP {response.status_code}"],
                response_time_ms=response_time_ms
            )

        # Validation structure réponse
        data = response.json()

        # Champs requis
        required_fields = ["asin", "analysis", "keepa_metadata", "trace_id"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            parsing_issues.append(f"Missing fields: {missing_fields}")

        # Validation analysis
        analysis = data.get("analysis", {})
        if not analysis:
            parsing_issues.append("Empty analysis object")

        analysis_required = ["roi", "velocity", "confidence_score", "overall_rating"]
        missing_analysis = [f for f in analysis_required if f not in analysis]
        if missing_analysis:
            parsing_issues.append(f"Missing analysis fields: {missing_analysis}")

        # Extraction BSR
        keepa_metadata = data.get("keepa_metadata", {})
        bsr_parsed = keepa_metadata.get("current_bsr")

        if bsr_parsed is None:
            parsing_issues.append("BSR not parsed (current_bsr = null)")
            bsr_in_range = False
        else:
            # Vérifier range attendu
            min_bsr, max_bsr = test_case.expected_bsr_range
            bsr_in_range = min_bsr <= bsr_parsed <= max_bsr

            if not bsr_in_range:
                parsing_issues.append(
                    f"BSR {bsr_parsed:,} outside expected range [{min_bsr:,} - {max_bsr:,}]"
                )

        # Success = 200 + no critical parsing issues
        success = (
            response.status_code == 200 and
            bsr_parsed is not None and
            bsr_in_range
        )

        if success:
            print(f"   ✅ BSR: {bsr_parsed:,} ({response_time_ms}ms)")
        else:
            print(f"   ⚠️  Issues: {'; '.join(parsing_issues)}")

        return ValidationResult(
            asin=test_case.asin,
            category=test_case.category,
            success=success,
            status_code=response.status_code,
            error_message=None,
            bsr_parsed=bsr_parsed,
            bsr_in_expected_range=bsr_in_range,
            parsing_issues=parsing_issues,
            response_time_ms=response_time_ms
        )

    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout après 30s")
        return ValidationResult(
            asin=test_case.asin,
            category=test_case.category,
            success=False,
            status_code=0,
            error_message="Request timeout",
            bsr_parsed=None,
            bsr_in_expected_range=False,
            parsing_issues=["Timeout"],
            response_time_ms=30000
        )
    except Exception as e:
        print(f"   ❌ Exception: {type(e).__name__}: {e}")
        return ValidationResult(
            asin=test_case.asin,
            category=test_case.category,
            success=False,
            status_code=0,
            error_message=str(e),
            bsr_parsed=None,
            bsr_in_expected_range=False,
            parsing_issues=[str(e)],
            response_time_ms=0
        )


def generate_report(results: List[ValidationResult]) -> Dict[str, Any]:
    """Génère rapport détaillé des résultats."""

    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed
    success_rate = (passed / total) * 100 if total > 0 else 0

    # Succès par catégorie
    by_category = {}
    for result in results:
        cat = result.category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0, "failed": 0}

        by_category[cat]["total"] += 1
        if result.success:
            by_category[cat]["passed"] += 1
        else:
            by_category[cat]["failed"] += 1

    # Performances
    response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    # Issues fréquents
    all_issues = []
    for result in results:
        all_issues.extend(result.parsing_issues)

    from collections import Counter
    issue_counts = Counter(all_issues)

    report = {
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate_pct": round(success_rate, 2),
            "target_rate_pct": 90.0,
            "meets_criteria": success_rate >= 90.0
        },
        "by_category": by_category,
        "performance": {
            "avg_response_time_ms": int(avg_response_time),
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0
        },
        "top_issues": dict(issue_counts.most_common(5)),
        "failed_asins": [
            {
                "asin": r.asin,
                "category": r.category,
                "error": r.error_message or "; ".join(r.parsing_issues)
            }
            for r in results if not r.success
        ]
    }

    return report


def print_report(report: Dict[str, Any]):
    """Affiche rapport formaté."""

    print("\n" + "="*80)
    print("📊 TIER 1 VALIDATION REPORT - 30 ASINs Keepa Réels")
    print("="*80)

    summary = report["summary"]
    print(f"\n✅ SUCCÈS: {summary['passed']}/{summary['total_tests']} ({summary['success_rate_pct']}%)")
    print(f"❌ ÉCHECS: {summary['failed']}/{summary['total_tests']}")
    print(f"🎯 CIBLE: {summary['target_rate_pct']}%")

    if summary["meets_criteria"]:
        print("\n🎉 CRITÈRE TIER 1 ATTEINT (≥ 90%)")
    else:
        print(f"\n⚠️  CRITÈRE TIER 1 NON ATTEINT (manque {summary['target_rate_pct'] - summary['success_rate_pct']:.1f}%)")

    print("\n📂 Résultats par Catégorie:")
    for category, stats in report["by_category"].items():
        rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"   {category:15s} : {stats['passed']:2d}/{stats['total']:2d} ({rate:5.1f}%)")

    perf = report["performance"]
    print(f"\n⚡ Performance:")
    print(f"   Temps moyen  : {perf['avg_response_time_ms']:,}ms")
    print(f"   Temps min    : {perf['min_response_time_ms']:,}ms")
    print(f"   Temps max    : {perf['max_response_time_ms']:,}ms")

    if report["top_issues"]:
        print(f"\n🔍 Top Issues:")
        for issue, count in report["top_issues"].items():
            print(f"   • {issue} ({count}x)")

    if report["failed_asins"]:
        print(f"\n❌ ASINs Échoués ({len(report['failed_asins'])}):")
        for failure in report["failed_asins"][:10]:  # Max 10
            print(f"   • {failure['asin']} ({failure['category']}): {failure['error']}")

    print("\n" + "="*80)


def main():
    """Exécute validation Tier 1 complète."""

    print("🎯 TIER 1 VALIDATION - 30 ASINs Keepa Réels")
    print(f"Backend: {BASE_URL}")
    print(f"Total tests: {len(TEST_ASINS)}")
    print("="*80)

    results = []

    for test_case in TEST_ASINS:
        result = validate_asin(test_case)
        results.append(result)

    # Génération rapport
    report = generate_report(results)
    print_report(report)

    # Export JSON
    output_file = "tier1_validation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "report": report,
            "detailed_results": [
                {
                    "asin": r.asin,
                    "category": r.category,
                    "success": r.success,
                    "status_code": r.status_code,
                    "bsr_parsed": r.bsr_parsed,
                    "bsr_in_expected_range": r.bsr_in_expected_range,
                    "parsing_issues": r.parsing_issues,
                    "response_time_ms": r.response_time_ms
                }
                for r in results
            ]
        }, f, indent=2)

    print(f"\n📄 Résultats exportés: {output_file}")

    # Exit code
    success = report["summary"]["meets_criteria"]
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
