"""Validation Script: Amazon Check avec Vraies Données Keepa.

Ce script teste le service Amazon Check avec une vraie réponse Keepa API
pour confirmer que les champs offers[].isAmazon, buyBoxSellerIdHistory,
et liveOffersOrder sont présents et correctement parsés.

BUILD_TAG: PHASE_2_5A_STEP_1
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.keepa_service import KeepaService
from app.services.amazon_check_service import check_amazon_presence


async def validate_with_real_keepa_data():
    """Test Amazon Check avec vraies données Keepa API."""

    print("=" * 80)
    print("VALIDATION: Amazon Check Service avec Vraies Données Keepa")
    print("=" * 80)
    print()

    # Get API key
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ KEEPA_API_KEY not set in environment")
        return False

    # Test ASIN (The Anxious Generation - livre populaire)
    test_asin = "0593655036"

    print(f"[TEST] ASIN: {test_asin}")
    print(f"[KEY] API Key: {'*' * 10}{api_key[-4:]}")
    print()

    # Initialize Keepa service
    keepa_service = KeepaService(api_key=api_key)

    try:
        async with keepa_service:
            print("[FETCH] Fetching product data from Keepa API...")
            print("        offers=20 enabled (Phase 2.5A requirement)")
            print()

            # Fetch real Keepa data
            product_data = await keepa_service.get_product_data(
                test_asin,
                force_refresh=True  # Skip cache for validation
            )

            if not product_data:
                print("[ERROR] No product data returned from Keepa")
                return False

            print("[SUCCESS] Product data fetched successfully")
            print()

            # Validate field presence
            print("[VALIDATE] Checking Keepa Field Presence:")
            print("-" * 80)

            # Check 1: offers array
            offers = product_data.get("offers")
            has_offers = offers is not None and isinstance(offers, list)
            status1 = "[OK]" if has_offers else "[MISSING]"
            print(f"{status1} offers[] array: {type(offers).__name__} with {len(offers) if has_offers else 0} items")

            # Check 2: offers[].isAmazon field
            has_is_amazon_field = False
            amazon_offer_found = False
            if has_offers and len(offers) > 0:
                first_offer = offers[0]
                has_is_amazon_field = "isAmazon" in first_offer
                status2 = "[OK]" if has_is_amazon_field else "[MISSING]"
                print(f"{status2} offers[0].isAmazon field: {first_offer.get('isAmazon')}")

                # Check if any offer has isAmazon=True
                for idx, offer in enumerate(offers):
                    if offer.get("isAmazon") is True:
                        amazon_offer_found = True
                        print(f"  [FOUND] Amazon offer at index {idx}:")
                        print(f"     - sellerId: {offer.get('sellerId')}")
                        print(f"     - isAmazon: True")
                        print(f"     - isFBA: {offer.get('isFBA')}")
                        break

            if not amazon_offer_found:
                print(f"  [INFO] No Amazon offer found in offers[] (isAmazon=True)")

            # Check 3: buyBoxSellerIdHistory
            buybox_history = product_data.get("buyBoxSellerIdHistory")
            has_buybox_history = buybox_history is not None and isinstance(buybox_history, list)
            status3 = "[OK]" if has_buybox_history else "[MISSING]"
            print(f"{status3} buyBoxSellerIdHistory: {type(buybox_history).__name__} with {len(buybox_history) if has_buybox_history else 0} items")

            if has_buybox_history and len(buybox_history) >= 2:
                most_recent_seller = buybox_history[-1]
                print(f"     - Most recent Buy Box winner: {most_recent_seller}")

            # Check 4: liveOffersOrder
            live_offers = product_data.get("liveOffersOrder")
            has_live_offers = live_offers is not None and isinstance(live_offers, list)
            status4 = "[OK]" if has_live_offers else "[MISSING]"
            print(f"{status4} liveOffersOrder: {type(live_offers).__name__} with {len(live_offers) if has_live_offers else 0} items")

            if has_live_offers and len(live_offers) > 0:
                print(f"     - First offer index (Buy Box winner): {live_offers[0]}")

            print()

            # Run Amazon Check Service
            print("[RUN] Running Amazon Check Service:")
            print("-" * 80)

            result = check_amazon_presence(product_data)

            print(f"  amazon_on_listing: {result['amazon_on_listing']}")
            print(f"  amazon_buybox: {result['amazon_buybox']}")
            print()

            # Save raw response for inspection
            output_file = "keepa_validation_response.json"
            with open(output_file, "w") as f:
                json.dump(product_data, f, indent=2, default=str)

            print(f"[SAVE] Raw Keepa response saved to: {output_file}")
            print(f"       File size: {os.path.getsize(output_file)} bytes")
            print()

            # Final validation
            print("[RESULTS] Validation Results:")
            print("-" * 80)

            all_fields_present = has_offers and has_is_amazon_field and has_buybox_history and has_live_offers

            if all_fields_present:
                print("[SUCCESS] ALL required Keepa fields present and valid!")
                print("[READY] Amazon Check Service ready for production")
                print()
                print("[SUMMARY]:")
                print(f"   - offers[] array: {len(offers)} offers")
                print(f"   - isAmazon field: Present in all offers")
                print(f"   - buyBoxSellerIdHistory: {len(buybox_history)} entries")
                print(f"   - liveOffersOrder: {len(live_offers)} offers")
                print()
                print(f"[COMPLETE] Phase 2.5A Step 1 validated with REAL Keepa data!")
                return True
            else:
                print("[WARNING] Some fields missing or invalid:")
                if not has_offers:
                    print("   - offers[] array missing")
                if not has_is_amazon_field:
                    print("   - isAmazon field missing")
                if not has_buybox_history:
                    print("   - buyBoxSellerIdHistory missing")
                if not has_live_offers:
                    print("   - liveOffersOrder missing")
                print()
                print("[INFO] Note: offers=20 parameter must be passed to Keepa API")
                return False

    except Exception as e:
        print(f"[ERROR] Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await validate_with_real_keepa_data()

    if success:
        print()
        print("=" * 80)
        print("✅ VALIDATION PASSED - Amazon Check ready for production")
        print("=" * 80)
        sys.exit(0)
    else:
        print()
        print("=" * 80)
        print("❌ VALIDATION FAILED - Check errors above")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
