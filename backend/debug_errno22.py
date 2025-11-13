"""
Debug script pour identifier Errno 22 dans /api/v1/niches/discover
"""
import asyncio
import traceback
import sys
from app.services.keepa_service import KeepaService
from app.services.config_service import ConfigService
from app.services.keepa_product_finder import KeepaProductFinderService
from app.services.niche_templates import discover_curated_niches, CURATED_NICHES
from app.core.config import settings
from app.core.db import get_db_session, db_manager


async def main():
    """Test exact flow of /niches/discover endpoint"""

    print("="*80)
    print("DEBUG: /api/v1/niches/discover - Errno 22 Reproduction")
    print("="*80)

    # Step 0: Initialize database
    print("\n[0] Initializing database...")
    try:
        await db_manager.initialize()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[ERROR] Database init failed: {e}")
        traceback.print_exc()
        return

    # Step 1: Initialize services
    print("\n[1] Initializing services...")
    try:
        keepa_service = KeepaService(api_key=settings.KEEPA_API_KEY)
        print("[OK] KeepaService initialized")
        print(f"   - API key configured: {bool(settings.KEEPA_API_KEY)}")
        print(f"   - Base URL: {keepa_service.BASE_URL}")
    except Exception as e:
        print(f"[ERROR] KeepaService init failed: {e}")
        traceback.print_exc()
        return

    # Step 2: Get DB session
    print("\n[2] Getting database session...")
    try:
        async for db in get_db_session():
            print("[OK] Database session obtained")

            try:
                config_service = ConfigService(db)
                print("[OK] ConfigService initialized")
            except Exception as e:
                print(f"[ERROR] ConfigService init failed: {e}")
                traceback.print_exc()
                return

            try:
                finder_service = KeepaProductFinderService(keepa_service, config_service, db)
                print("[OK] KeepaProductFinderService initialized")
            except Exception as e:
                print(f"[ERROR] ProductFinder init failed: {e}")
                traceback.print_exc()
                return

            # Step 3: Test template selection
            print("\n[3] Testing template selection...")
            print(f"   - Total templates available: {len(CURATED_NICHES)}")
            test_template = CURATED_NICHES[0]
            print(f"   - Test template: {test_template['id']}")
            print(f"   - Categories: {test_template['categories']}")

            # Step 4: Call discover_curated_niches (exact replica of endpoint)
            print("\n[4] Calling discover_curated_niches...")
            try:
                niches = await discover_curated_niches(
                    db=db,
                    product_finder=finder_service,
                    count=1,  # Just test 1 niche
                    shuffle=False
                )
                print(f"[OK] discover_curated_niches succeeded")
                print(f"   - Niches validated: {len(niches)}")
                for niche in niches:
                    print(f"   - {niche['id']}: {niche['products_found']} products")

            except Exception as e:
                print(f"[ERROR] discover_curated_niches FAILED")
                print(f"   - Exception type: {type(e).__name__}")
                print(f"   - Exception message: {e}")
                print(f"   - Errno check: {'[Errno 22]' in str(e)}")
                print("\n[FULL TRACEBACK]")
                traceback.print_exc()

                # Additional debugging
                print("\n[ADDITIONAL DEBUG INFO]")
                print(f"   - Exception args: {e.args}")
                if hasattr(e, '__cause__'):
                    print(f"   - Exception cause: {e.__cause__}")
                if hasattr(e, '__context__'):
                    print(f"   - Exception context: {e.__context__}")

            finally:
                await keepa_service.close()
                print("\n[OK] KeepaService closed")

            break  # Only need one DB session iteration

    except Exception as e:
        print(f"[ERROR] Database session failed: {e}")
        traceback.print_exc()

    print("\n" + "="*80)
    print("DEBUG COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
