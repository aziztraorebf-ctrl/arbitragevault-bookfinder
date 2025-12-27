"""
Analyze Keepa offers to understand New vs Used pricing.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.keepa_service import KeepaService
from app.core.config import settings


CONDITION_MAP = {
    0: "Unknown",
    1: "New",
    2: "Used-LikeNew",
    3: "Used-VeryGood",
    4: "Used-Good",
    5: "Used-Acceptable",
    6: "Refurbished",
}


async def analyze_offers(asin: str):
    keepa = KeepaService(api_key=settings.KEEPA_API_KEY)

    try:
        product = await keepa.get_product_data(asin, domain=1, force_refresh=True)

        if not product:
            print("Product not found")
            return

        print(f"Product: {product.get('title', 'N/A')[:60]}")
        print(f"ASIN: {asin}")

        # Get stats.current
        stats = product.get("stats", {})
        current = stats.get("current", [])

        # Indices: 0=Amazon, 1=New, 2=Used, 3=BSR
        amazon_price = current[0] if len(current) > 0 and current[0] and current[0] > 0 else None
        new_price = current[1] if len(current) > 1 and current[1] and current[1] > 0 else None
        used_price = current[2] if len(current) > 2 and current[2] and current[2] > 0 else None
        bsr = current[3] if len(current) > 3 else None

        print(f"\n{'='*60}")
        print("PRIX ACTUELS (stats.current)")
        print(f"{'='*60}")
        print(f"  Amazon price (index 0): ${amazon_price/100:.2f}" if amazon_price else "  Amazon price: N/A (Amazon ne vend pas)")
        print(f"  New price (index 1):    ${new_price/100:.2f}" if new_price else "  New price: N/A")
        print(f"  Used price (index 2):   ${used_price/100:.2f}" if used_price else "  Used price: N/A")
        print(f"  BSR (index 3):          #{bsr:,}" if bsr else "  BSR: N/A")

        # Analyze live offers
        offers = product.get("offers", [])
        live_order = product.get("liveOffersOrder", [])

        print(f"\n{'='*60}")
        print(f"ANALYSE DES OFFRES: {len(live_order)} live / {len(offers)} total")
        print(f"{'='*60}")

        new_offers = []
        used_offers = []

        for idx in live_order[:20]:
            if idx >= len(offers):
                continue
            offer = offers[idx]

            cond = offer.get("condition", 0)
            cond_str = CONDITION_MAP.get(cond, f"Unknown({cond})")
            is_amazon = offer.get("isAmazon", False)
            is_fba = offer.get("isFBA", False)
            seller_id = offer.get("sellerId", "Unknown")[:15]

            offer_csv = offer.get("offerCSV", [])
            price_cents = offer_csv[-1] if offer_csv and len(offer_csv) >= 2 else None
            price = price_cents / 100 if price_cents and price_cents > 0 else None

            if not price:
                continue

            shipping = offer.get("shipping", 0)
            shipping_usd = shipping / 100 if shipping and shipping > 0 else 0

            total = price + shipping_usd

            offer_info = {
                "condition": cond_str,
                "condition_code": cond,
                "price": price,
                "shipping": shipping_usd,
                "total": total,
                "is_amazon": is_amazon,
                "is_fba": is_fba,
                "seller_id": seller_id
            }

            if cond == 1:  # New
                new_offers.append(offer_info)
            else:
                used_offers.append(offer_info)

        print(f"\n--- OFFRES NEW ({len(new_offers)}) ---")
        if new_offers:
            for o in sorted(new_offers, key=lambda x: x["total"])[:5]:
                seller = "AMAZON" if o["is_amazon"] else ("FBA" if o["is_fba"] else "FBM")
                print(f"  {o['condition']:15} ${o['price']:7.2f} + ${o['shipping']:5.2f} = ${o['total']:7.2f} [{seller}]")
        else:
            print("  Aucune offre NEW disponible!")

        print(f"\n--- OFFRES USED ({len(used_offers)}) ---")
        if used_offers:
            for o in sorted(used_offers, key=lambda x: x["total"])[:5]:
                seller = "AMAZON" if o["is_amazon"] else ("FBA" if o["is_fba"] else "FBM")
                print(f"  {o['condition']:15} ${o['price']:7.2f} + ${o['shipping']:5.2f} = ${o['total']:7.2f} [{seller}]")
        else:
            print("  Aucune offre USED disponible!")

        print(f"\n{'='*60}")
        print("CONCLUSION")
        print(f"{'='*60}")

        if new_offers:
            cheapest_new = min(new_offers, key=lambda x: x["total"])
            print(f"Prix NEW le moins cher:  ${cheapest_new['total']:.2f}")
        else:
            print("Prix NEW: AUCUNE OFFRE")

        if used_offers:
            cheapest_used = min(used_offers, key=lambda x: x["total"])
            print(f"Prix USED le moins cher: ${cheapest_used['total']:.2f}")

        # Profit analysis
        print(f"\n{'='*60}")
        print("ANALYSE PROFIT REALISTE")
        print(f"{'='*60}")

        # For arbitrage, we need to compare:
        # - Buy NEW at price X -> Sell NEW at New price
        # - Buy USED at price Y -> Sell USED at Used price

        if new_price and new_offers:
            cheapest_new = min(new_offers, key=lambda x: x["total"])
            # Skip Amazon as source
            non_amazon_new = [o for o in new_offers if not o["is_amazon"]]
            if non_amazon_new:
                cheapest = min(non_amazon_new, key=lambda x: x["total"])
                sell = new_price / 100
                buy = cheapest["total"]
                # FBA fees approximation
                fees = sell * 0.15 + 1.80 + 3.97 + 0.90  # referral + closing + FBA + prep
                profit = sell - buy - fees
                print(f"\nArbitrage NEW -> NEW:")
                print(f"  Acheter a: ${buy:.2f}")
                print(f"  Vendre a:  ${sell:.2f}")
                print(f"  Frais FBA: ${fees:.2f}")
                print(f"  PROFIT:    ${profit:.2f}")
                if profit < 0:
                    print("  --> PAS RENTABLE")

        if used_price and used_offers:
            non_amazon_used = [o for o in used_offers if not o["is_amazon"]]
            if non_amazon_used:
                cheapest = min(non_amazon_used, key=lambda x: x["total"])
                sell = used_price / 100
                buy = cheapest["total"]
                fees = sell * 0.15 + 1.80 + 3.97 + 0.90
                profit = sell - buy - fees
                print(f"\nArbitrage USED -> USED:")
                print(f"  Acheter a: ${buy:.2f}")
                print(f"  Vendre a:  ${sell:.2f}")
                print(f"  Frais FBA: ${fees:.2f}")
                print(f"  PROFIT:    ${profit:.2f}")
                if profit < 0:
                    print("  --> PAS RENTABLE")

        print(f"\n{'='*60}")
        print("IMPORTANT: L'erreur dans l'UI actuelle")
        print(f"{'='*60}")
        print("L'UI compare prix USED ($3.99) avec prix de vente NEW ($135)")
        print("C'est FAUX car on ne peut pas vendre du Used comme New!")
        print("Il faut comparer: Used->Used OU New->New")

    finally:
        await keepa.close()


if __name__ == "__main__":
    asin = sys.argv[1] if len(sys.argv) > 1 else "0399210709"  # First Christmas
    asyncio.run(analyze_offers(asin))
