"""E2E Validation Script: Complete System Test with Real Keepa Data.

Tests all 4 views (mes_niches, phase_recherche, quick_flip, long_terme) with
real ASINs to validate Phase 2 (View-Specific Scoring) + Phase 2.5A (Amazon Check).

Usage:
    cd backend
    .venv/Scripts/python.exe validate_e2e_all_views.py

BUILD_TAG: PHASE_2_5A_STEP_1
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.keepa_service import KeepaService
from app.services.keepa_parser_v2 import parse_keepa_product
from app.services.scoring_v2 import compute_view_score, VIEW_WEIGHTS
from app.services.amazon_check_service import check_amazon_presence
from app.services.business_config_service import BusinessConfigService


# ============================================================================
# Test Configuration
# ============================================================================

TEST_ASINS = [
    "0593655036",  # Book - The Anxious Generation (validated in Phase 2.5A)
    "B07ZPKN6YR",  # Electronics - Apple AirPods Pro
    "B0BSHF7LLL",  # Electronics - Amazon Echo Dot 5th Gen
    "B08N5WRWNW",  # Book - potential textbook
    "B07FNW9FGJ",  # Mixed product
]

TEST_SCENARIOS = [
    {
        "view_type": "mes_niches",
        "asins": ["0593655036", "B07ZPKN6YR", "B0BSHF7LLL"],
        "strategy": "balanced",
        "description": "Niche management - ROI priority with stability"
    },
    {
        "view_type": "phase_recherche",
        "asins": ["0593655036", "B08N5WRWNW"],
        "strategy": "aggressive",
        "description": "Research phase - High standards"
    },
    {
        "view_type": "quick_flip",
        "asins": ["B07ZPKN6YR", "B0BSHF7LLL"],
        "strategy": "velocity",
        "description": "Quick flip - Fast rotation priority"
    },
    {
        "view_type": "long_terme",
        "asins": ["0593655036", "B08N5WRWNW"],
        "strategy": "textbook",
        "description": "Long term - High margin focus"
    }
]

# Map view_type to actual VIEW_WEIGHTS keys
VIEW_TYPE_MAPPING = {
    "mes_niches": "mes_niches",
    "phase_recherche": "analyse_strategique",  # Strategic analysis
    "quick_flip": "auto_sourcing",  # Fast automation
    "long_terme": "stock_estimates"  # Stability for long-term
}

OUTPUT_DIR = Path("e2e_validation_responses")


# ============================================================================
# Validation Functions
# ============================================================================

async def validate_view_scenario(
    scenario: Dict[str, Any],
    keepa_service: KeepaService,
    config_service: BusinessConfigService
) -> Dict[str, Any]:
    """
    Validate a single view scenario with real Keepa data.

    Args:
        scenario: Test scenario configuration
        keepa_service: Keepa API service instance
        config_service: Business config service

    Returns:
        Validation result with products, metadata, and timing
    """
    view_type = scenario["view_type"]
    asins = scenario["asins"]
    strategy = scenario["strategy"]

    # Map view_type to actual VIEW_WEIGHTS key
    actual_view_type = VIEW_TYPE_MAPPING.get(view_type, view_type)

    print(f"\n[TEST] View: {view_type} (mapped to {actual_view_type})")
    print(f"       Strategy: {strategy}")
    print(f"       ASINs: {', '.join(asins)}")
    print(f"       Description: {scenario['description']}")
    print("-" * 80)

    start_time = time.time()

    scored_products = []
    errors = []

    # Get business config (for feature flags)
    config = await config_service.get_effective_config(domain_id=1, category="books")
    feature_flags = config.get("feature_flags", {})
    amazon_check_enabled = feature_flags.get("amazon_check_enabled", False)

    print(f"[CONFIG] Amazon Check enabled: {amazon_check_enabled}")
    print()

    for asin in asins:
        try:
            print(f"  [FETCH] {asin}...", end=" ", flush=True)

            # Fetch Keepa data
            product_data = await keepa_service.get_product_data(asin, force_refresh=False)

            if not product_data:
                print("[FAIL] No data from Keepa")
                errors.append(f"{asin}: No data from Keepa")
                scored_products.append({
                    "asin": asin,
                    "title": None,
                    "score": 0.0,
                    "rank": 0,
                    "strategy_profile": None,
                    "weights_applied": {},
                    "components": {},
                    "raw_metrics": {},
                    "amazon_on_listing": False,
                    "amazon_buybox": False,
                    "error": "No data from Keepa"
                })
                continue

            # Parse Keepa product
            parsed = parse_keepa_product(product_data)

            # Compute view-specific score
            score_result = compute_view_score(
                parsed_data=parsed,
                view_type=actual_view_type,
                strategy_profile=strategy
            )

            # Run Amazon Check if enabled
            amazon_on_listing = False
            amazon_buybox = False

            if amazon_check_enabled:
                amazon_result = check_amazon_presence(product_data)
                amazon_on_listing = amazon_result.get("amazon_on_listing", False)
                amazon_buybox = amazon_result.get("amazon_buybox", False)

            # Build product result
            product = {
                "asin": parsed.get("asin", asin),
                "title": parsed.get("title"),
                "score": score_result["score"],
                "rank": 0,  # Will be assigned after sorting
                "strategy_profile": score_result["strategy_profile"],
                "weights_applied": score_result["weights_applied"],
                "components": score_result["components"],
                "raw_metrics": score_result["raw_metrics"],
                "amazon_on_listing": amazon_on_listing,
                "amazon_buybox": amazon_buybox,
                "error": None
            }

            scored_products.append(product)

            print(f"[OK] Score: {score_result['score']:.2f} | Amazon: {amazon_on_listing}/{amazon_buybox}")

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            errors.append(f"{asin}: {str(e)}")
            # Create error product with all required fields
            scored_products.append({
                "asin": asin,
                "title": None,
                "score": 0.0,
                "rank": 0,
                "strategy_profile": None,
                "weights_applied": {},
                "components": {},
                "raw_metrics": {},
                "amazon_on_listing": False,
                "amazon_buybox": False,
                "error": str(e)
            })

    # Sort by score descending and assign ranks
    scored_products.sort(key=lambda x: x.get("score", 0), reverse=True)
    for idx, product in enumerate(scored_products, start=1):
        product["rank"] = idx

    # Calculate metadata
    successful_scores = sum(1 for p in scored_products if p.get("error") is None)
    failed_scores = len(scored_products) - successful_scores
    valid_scores = [p["score"] for p in scored_products if p.get("error") is None]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    elapsed_time = time.time() - start_time

    # Get weights for metadata
    weights = VIEW_WEIGHTS.get(actual_view_type, VIEW_WEIGHTS["dashboard"])

    metadata = {
        "view_type": view_type,
        "actual_view_type": actual_view_type,
        "weights_used": {
            "roi": weights["roi"],
            "velocity": weights["velocity"],
            "stability": weights["stability"]
        },
        "total_products": len(scored_products),
        "successful_scores": successful_scores,
        "failed_scores": failed_scores,
        "avg_score": round(avg_score, 2),
        "strategy_requested": strategy,
        "elapsed_time_seconds": round(elapsed_time, 2)
    }

    print()
    print(f"[SUMMARY] Total: {len(scored_products)} | Success: {successful_scores} | Fail: {failed_scores}")
    print(f"          Avg Score: {avg_score:.2f} | Time: {elapsed_time:.2f}s")

    if errors:
        print(f"[ERRORS] {len(errors)} error(s):")
        for error in errors:
            print(f"         - {error}")

    return {
        "products": scored_products,
        "metadata": metadata,
        "errors": errors
    }


def validate_response_structure(result: Dict[str, Any]) -> List[str]:
    """
    Validate response structure against expected schema.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check top-level keys
    if "products" not in result:
        errors.append("Missing 'products' key")
    if "metadata" not in result:
        errors.append("Missing 'metadata' key")

    # Validate products array
    products = result.get("products", [])
    if not isinstance(products, list):
        errors.append("'products' must be an array")
    else:
        for idx, product in enumerate(products):
            required_fields = [
                "asin", "score", "rank", "weights_applied",
                "components", "raw_metrics", "amazon_on_listing", "amazon_buybox"
            ]
            for field in required_fields:
                if field not in product:
                    errors.append(f"Product {idx}: Missing field '{field}'")

            # Validate types
            if "score" in product and not isinstance(product["score"], (int, float)):
                errors.append(f"Product {idx}: 'score' must be numeric")
            if "amazon_on_listing" in product and not isinstance(product["amazon_on_listing"], bool):
                errors.append(f"Product {idx}: 'amazon_on_listing' must be boolean")
            if "amazon_buybox" in product and not isinstance(product["amazon_buybox"], bool):
                errors.append(f"Product {idx}: 'amazon_buybox' must be boolean")

    # Validate metadata
    metadata = result.get("metadata", {})
    required_metadata = [
        "view_type", "weights_used", "total_products",
        "successful_scores", "failed_scores", "avg_score"
    ]
    for field in required_metadata:
        if field not in metadata:
            errors.append(f"Metadata: Missing field '{field}'")

    return errors


async def run_full_validation():
    """Run complete E2E validation across all views."""

    print("=" * 80)
    print("E2E VALIDATION - ArbitrageVault Phase 2 + Phase 2.5A")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Build Tag: PHASE_2_5A_STEP_1")
    print()

    # Get API key
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("[ERROR] KEEPA_API_KEY not set in environment")
        return False

    print(f"[KEY] Keepa API Key: {'*' * 10}{api_key[-4:]}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"[OUTPUT] Responses will be saved to: {OUTPUT_DIR}/")
    print()

    # Initialize services
    keepa_service = KeepaService(api_key=api_key)
    config_service = BusinessConfigService()

    all_results = {}
    validation_errors = {}

    try:
        async with keepa_service:
            # Test each scenario
            for scenario in TEST_SCENARIOS:
                view_type = scenario["view_type"]

                # Run validation
                result = await validate_view_scenario(
                    scenario,
                    keepa_service,
                    config_service
                )

                all_results[view_type] = result

                # Validate response structure
                structure_errors = validate_response_structure(result)
                if structure_errors:
                    validation_errors[view_type] = structure_errors
                    print(f"\n[VALIDATION ERRORS] {view_type}:")
                    for error in structure_errors:
                        print(f"  - {error}")

                # Save response to file
                output_file = OUTPUT_DIR / f"{view_type}_response.json"
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"\n[SAVED] {output_file}")
                print()

    finally:
        await keepa_service.close()

    # Generate summary report
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    total_scenarios = len(TEST_SCENARIOS)
    successful_scenarios = sum(
        1 for result in all_results.values()
        if result["metadata"]["successful_scores"] > 0
    )

    print(f"\nScenarios Tested: {total_scenarios}")
    print(f"Successful: {successful_scenarios}")
    print(f"Failed: {total_scenarios - successful_scenarios}")
    print()

    # Per-view summary
    for view_type, result in all_results.items():
        metadata = result["metadata"]
        print(f"[{view_type.upper()}]")
        print(f"  Products: {metadata['total_products']}")
        print(f"  Success: {metadata['successful_scores']}")
        print(f"  Failed: {metadata['failed_scores']}")
        print(f"  Avg Score: {metadata['avg_score']:.2f}")
        print(f"  Time: {metadata['elapsed_time_seconds']:.2f}s")

        if view_type in validation_errors:
            print(f"  [STRUCTURE ERRORS]: {len(validation_errors[view_type])}")
        else:
            print(f"  [STRUCTURE]: OK")
        print()

    # Overall status
    all_valid = len(validation_errors) == 0 and successful_scenarios == total_scenarios

    if all_valid:
        print("[RESULT] ALL TESTS PASSED - System ready for production")
        print()
        print("Next Steps:")
        print("  1. Review saved JSON responses in e2e_validation_responses/")
        print("  2. Test production API with same ASINs")
        print("  3. Continue to Phase 2.5A Step 2 (Frontend Integration)")
        return True
    else:
        print("[RESULT] VALIDATION FAILED - Issues detected")
        print()
        print("Action Required:")
        print("  1. Review errors above")
        print("  2. Fix issues before continuing development")
        print("  3. Re-run validation after fixes")
        return False


async def main():
    """Main entry point."""
    success = await run_full_validation()

    if success:
        print("\n" + "=" * 80)
        print("[SUCCESS] E2E Validation Complete")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("[FAILURE] E2E Validation Failed")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
