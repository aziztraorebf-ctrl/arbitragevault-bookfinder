"""
Test de validation des PRIX après fix epoch Keepa.

Ce script vérifie que les PRIX retournés par Keepa sont corrects et à jour,
pas seulement les timestamps.

Auteur: Claude Sonnet 4.5
Date: 15 octobre 2025
"""

import asyncio
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def validate_prices_post_epoch_fix():
    """Valide que les prix retournés sont corrects après le fix epoch."""

    from app.services.keepa_service import KeepaService
    from app.services.keepa_parser_v2 import parse_keepa_product

    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        logger.error("❌ KEEPA_API_KEY not found")
        return False

    # Test avec un bestseller connu avec prix stable
    test_asin = "0735211299"  # Atomic Habits
    expected_price_range = (10.0, 25.0)  # Prix attendu entre $10-$25

    logger.info("=" * 70)
    logger.info("🔍 VALIDATION DES PRIX POST-FIX EPOCH")
    logger.info("=" * 70)
    logger.info("")

    service = KeepaService(api_key=api_key)

    try:
        logger.info(f"📦 Test ASIN: {test_asin} (Atomic Habits)")
        logger.info(f"   Prix attendu: ${expected_price_range[0]}-${expected_price_range[1]}")
        logger.info("")

        # Fetch avec force_refresh pour avoir données live
        logger.info("🔄 Fetching avec force_refresh=True...")
        raw_data = await service.get_product_data(test_asin, force_refresh=True)

        if not raw_data:
            logger.error("❌ No data returned")
            return False

        logger.info("✅ Data received, parsing...")
        logger.info("")

        # Parse le produit
        parsed = parse_keepa_product(raw_data)

        # Afficher les infos brutes de Keepa
        logger.info("=" * 70)
        logger.info("📊 DONNÉES BRUTES KEEPA")
        logger.info("=" * 70)

        # Prix directs depuis Keepa
        logger.info("Prix disponibles dans Keepa 'data' arrays:")
        data_section = raw_data.get('data', {})

        prices_found = {}
        for key in ['AMAZON', 'NEW', 'USED', 'BUY_BOX_SHIPPING']:
            if key in data_section:
                arr = data_section[key]
                if arr is not None and hasattr(arr, '__len__') and len(arr) > 0:
                    # Convertir en list si numpy array
                    if hasattr(arr, 'tolist'):
                        arr = arr.tolist()
                    # Dernière valeur valide
                    last_val = None
                    for val in reversed(arr):
                        if val is not None and val != -1:
                            last_val = val
                            break
                    if last_val:
                        price_usd = last_val / 100.0
                        prices_found[key] = price_usd
                        logger.info(f"  - {key}: ${price_usd:.2f}")

        logger.info("")

        # Stats from keepa library
        stats = raw_data.get('stats', {})
        if stats:
            logger.info("Stats disponibles:")
            current = stats.get('current')
            if current and len(current) > 1:
                if current[1] and current[1] != -1:
                    logger.info(f"  - current[1] (NEW price): ${current[1]/100:.2f}")

        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 DONNÉES PARSÉES PAR NOTRE CODE")
        logger.info("=" * 70)

        # Prix parsés
        logger.info(f"current_price: ${parsed.current_price}" if parsed.current_price else "current_price: None")
        logger.info(f"amazon_price: ${parsed.amazon_price}" if parsed.amazon_price else "amazon_price: None")
        logger.info(f"new_price: ${parsed.new_price}" if parsed.new_price else "new_price: None")
        logger.info(f"used_price: ${parsed.used_price}" if parsed.used_price else "used_price: None")
        logger.info(f"list_price: ${parsed.list_price}" if parsed.list_price else "list_price: None")

        logger.info("")
        logger.info(f"current_bsr: {parsed.current_bsr}" if parsed.current_bsr else "current_bsr: None")

        logger.info("")
        logger.info("=" * 70)
        logger.info("🎯 VALIDATION")
        logger.info("=" * 70)

        # Validation
        issues = []

        # Check 1: Prix existe
        if not parsed.current_price:
            issues.append("❌ current_price est None")

        # Check 2: Prix dans une range raisonnable
        if parsed.current_price:
            if parsed.current_price < 0.1:
                issues.append(f"❌ Prix trop bas: ${parsed.current_price} (probablement faux)")
            elif parsed.current_price < expected_price_range[0]:
                issues.append(f"⚠️ Prix plus bas qu'attendu: ${parsed.current_price}")
            elif parsed.current_price > expected_price_range[1]:
                issues.append(f"⚠️ Prix plus haut qu'attendu: ${parsed.current_price}")
            else:
                logger.info(f"✅ Prix dans la range attendue: ${parsed.current_price:.2f}")

        # Check 3: BSR n'est pas confondu avec prix
        if parsed.current_bsr and parsed.current_price:
            if abs(parsed.current_price - parsed.current_bsr) < 1:
                issues.append(f"⚠️ POSSIBLE CONFUSION: price={parsed.current_price}, bsr={parsed.current_bsr}")

        # Check 4: Timestamp est récent (grâce au fix)
        if parsed.last_updated_at:
            age_days = (datetime.now() - parsed.last_updated_at).days
            if age_days < 7:
                logger.info(f"✅ Timestamp récent: {parsed.last_updated_at.date()} ({age_days} jours)")
            else:
                issues.append(f"⚠️ Timestamp ancien: {age_days} jours")

        logger.info("")

        if issues:
            logger.error("⚠️ PROBLÈMES DÉTECTÉS:")
            for issue in issues:
                logger.error(f"  {issue}")
            return False
        else:
            logger.info("🎉 VALIDATION RÉUSSIE!")
            logger.info("   - Prix corrects et à jour ✅")
            logger.info("   - Timestamps corrects (fix epoch fonctionne) ✅")
            logger.info("   - Pas de confusion BSR/prix ✅")
            return True

    finally:
        await service.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(validate_prices_post_epoch_fix())

    if success:
        logger.info("")
        logger.info("✅ Le fix epoch + parsing prix fonctionne correctement!")
        exit(0)
    else:
        logger.error("")
        logger.error("❌ Problèmes détectés - investigation nécessaire")
        exit(1)
