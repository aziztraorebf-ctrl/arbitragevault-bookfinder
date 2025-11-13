"""
Test de validation du fix epoch Keepa avec des produits réels.

Ce script teste que les timestamps Keepa affichent maintenant 2025, pas 2015.

Auteur: Claude Sonnet 4.5
Date: 15 octobre 2025
"""

import asyncio
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_keepa_timestamps_with_real_asins():
    """Test avec 3 ASINs réels pour valider le fix epoch."""

    # Import services
    from app.services.keepa_service import KeepaService
    from app.services.keepa_parser_v2 import KeepaTimestampExtractor
    from app.utils.keepa_utils import keepa_to_datetime

    # Get API key
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        logger.error("❌ KEEPA_API_KEY not found in environment")
        return False

    # Test ASINs (variété de produits)
    test_asins = [
        ("0735211299", "Atomic Habits (Bestseller 2024)"),
        ("B0CHWRXH8B", "AirPods Pro 2024"),
        ("0593655036", "All the Light We Cannot See")
    ]

    logger.info("=" * 70)
    logger.info("Test de Validation du Fix Epoch Keepa")
    logger.info("=" * 70)
    logger.info("")

    service = KeepaService(api_key=api_key)
    all_passed = True

    try:
        for asin, description in test_asins:
            logger.info(f"📦 Test: {asin} - {description}")
            logger.info("-" * 70)

            # Fetch product data
            product_data = await service.get_product_data(asin, force_refresh=True)

            if not product_data:
                logger.error(f"❌ No data returned for {asin}")
                all_passed = False
                continue

            # Extract lastPriceChange
            last_price_change = product_data.get("lastPriceChange", -1)

            if last_price_change == -1:
                logger.warning(f"⚠️ No lastPriceChange for {asin}")
                continue

            # Convert using official formula
            timestamp = keepa_to_datetime(last_price_change)

            if timestamp is None:
                logger.error(f"❌ Failed to convert keepa_time={last_price_change}")
                all_passed = False
                continue

            # Calculate age
            age_days = (datetime.now() - timestamp).days

            # Validation critères
            year_ok = timestamp.year >= 2025
            age_reasonable = age_days < 365  # Moins d'1 an

            # Log résultats
            logger.info(f"  keepa_time: {last_price_change}")
            logger.info(f"  Timestamp: {timestamp.isoformat()}")
            logger.info(f"  Year: {timestamp.year}")
            logger.info(f"  Age: {age_days} days")
            logger.info(f"  Status: {'✅ PASS' if year_ok and age_reasonable else '❌ FAIL'}")

            if not year_ok:
                logger.error(f"  ❌ CRITICAL: Year {timestamp.year} < 2025 (ancien epoch!)")
                all_passed = False

            if timestamp.year == 2015:
                logger.error(f"  ❌ REGRESSION: Utilise l'ancien epoch (971222400)")
                all_passed = False

            if not age_reasonable:
                logger.warning(f"  ⚠️ Data très ancienne: {age_days} jours")

            logger.info("")

        # Résumé final
        logger.info("=" * 70)
        if all_passed:
            logger.info("✅ VALIDATION RÉUSSIE: Tous les timestamps affichent 2025+")
            logger.info("   Le fix epoch Keepa fonctionne correctement!")
        else:
            logger.error("❌ VALIDATION ÉCHOUÉE: Problème détecté")
            logger.error("   Vérifier les logs ci-dessus pour détails")
        logger.info("=" * 70)

        return all_passed

    finally:
        await service.close()


async def test_timestamp_extractor():
    """Test KeepaTimestampExtractor avec un timestamp connu."""
    from app.services.keepa_parser_v2 import KeepaTimestampExtractor
    from app.utils.keepa_utils import keepa_to_datetime

    logger.info("")
    logger.info("=" * 70)
    logger.info("Test KeepaTimestampExtractor")
    logger.info("=" * 70)

    # Mock data avec le timestamp officiel du support Keepa
    mock_data = {
        "asin": "TEST123",
        "lastPriceChange": 7777548  # Doit donner 2025-10-15 01:48:00 UTC
    }

    extractor = KeepaTimestampExtractor()
    timestamp = extractor.extract_data_freshness_timestamp(mock_data)

    if timestamp:
        logger.info(f"✅ Extracted timestamp: {timestamp.isoformat()}")
        logger.info(f"   Year: {timestamp.year}")

        if timestamp.year == 2025 and timestamp.month == 10 and timestamp.day == 15:
            logger.info("✅ PASS: Timestamp correct selon support Keepa")
            return True
        else:
            logger.error(f"❌ FAIL: Expected 2025-10-15, got {timestamp.date()}")
            return False
    else:
        logger.error("❌ FAIL: No timestamp extracted")
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("🚀 Démarrage de la validation du fix epoch Keepa")
    logger.info("")

    # Test 1: Timestamp extraction
    loop = asyncio.get_event_loop()
    test1_passed = loop.run_until_complete(test_timestamp_extractor())

    # Test 2: Real ASINs
    test2_passed = loop.run_until_complete(test_keepa_timestamps_with_real_asins())

    # Résultat final
    logger.info("")
    logger.info("=" * 70)
    logger.info("RÉSUMÉ FINAL")
    logger.info("=" * 70)
    logger.info(f"Test Extractor: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    logger.info(f"Test Real ASINs: {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        logger.info("")
        logger.info("🎉 SUCCESS: Le fix epoch Keepa est validé!")
        logger.info("   Tous les timestamps affichent maintenant des dates correctes (2025+)")
        exit(0)
    else:
        logger.error("")
        logger.error("❌ FAILURE: Des problèmes persistent")
        exit(1)
