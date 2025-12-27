"""
Simulation Utilisateur: Recherche Textbooks et Calcul Profit Realiste

Simule exactement ce qu'un utilisateur ferait:
1. Rechercher des textbooks via Product Finder
2. Analyser chaque produit
3. Calculer le profit realiste

USAGE:
    cd backend
    python scripts/simulate_textbook_user.py
"""

import asyncio
import os
import sys
from pathlib import Path
from decimal import Decimal

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import httpx

# Load .env
env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key, value)

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"

# Textbook strategy parameters - ALIGNED WITH PDF GUIDE
# Page 5: BSR under 250,000 (Golden Rule)
# Page 13: Price $40+ minimum (fees eat profit on cheap books)
# Page 13: Price under $300-400 max (return fraud risk)
# Page 10: Check for Whales (avoid if seller has 100+ copies)
TEXTBOOK_CONFIG = {
    "bsr_range": (30000, 250000),  # PDF Golden Rule: under 250K
    "price_range": (40.0, 300.0),  # PDF: $40+ min, $300 max
    "max_fba_sellers": 5,          # Low competition
    "exclude_amazon": True
}

# FBA Fee structure for Books
FBA_FEES = {
    "referral_percent": 0.15,  # 15%
    "closing_fee": 1.80,       # Books closing fee
    "fba_base": 3.22,          # Base fulfillment
    "fba_per_lb": 0.75,        # Per pound over 1lb
    "avg_book_weight": 1.5,    # Average textbook weight
    "prep_fee": 0.50,          # Prep/label fee
    "inbound_shipping": 0.40,  # Per book inbound
}

# Source price factor (FBM arbitrage)
SOURCE_PRICE_FACTOR = 0.50  # Buy at 50% of sell price


def calculate_fba_fees(sell_price: float, weight_lbs: float = 1.5) -> dict:
    """Calculate all FBA fees for a book."""
    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]

    # Fulfillment fee (base + weight)
    extra_weight = max(0, weight_lbs - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])

    prep = FBA_FEES["prep_fee"]
    inbound = FBA_FEES["inbound_shipping"]

    total_fees = referral + closing + fulfillment + prep + inbound

    return {
        "referral": round(referral, 2),
        "closing": closing,
        "fulfillment": round(fulfillment, 2),
        "prep": prep,
        "inbound": inbound,
        "total": round(total_fees, 2)
    }


def calculate_profit(sell_price: float, source_factor: float = 0.50) -> dict:
    """Calculate realistic profit for a textbook."""
    buy_cost = sell_price * source_factor
    fees = calculate_fba_fees(sell_price)

    profit = sell_price - buy_cost - fees["total"]
    roi = (profit / buy_cost) * 100 if buy_cost > 0 else 0

    return {
        "sell_price": round(sell_price, 2),
        "buy_cost": round(buy_cost, 2),
        "fees": fees,
        "profit_net": round(profit, 2),
        "roi_percent": round(roi, 1),
        "margin_percent": round((profit / sell_price) * 100, 1) if sell_price > 0 else 0
    }


async def discover_textbooks() -> list:
    """Discover textbooks via Keepa Product Finder."""

    # Use Books root category - MINIMAL filters for API, post-filter locally
    # Product Finder doesn't support all filter combos, so we use basic ones
    selection = {
        "rootCategory": 283155,  # Books
        "perPage": 100,
        "current_SALES_gte": TEXTBOOK_CONFIG["bsr_range"][0],
        "current_SALES_lte": TEXTBOOK_CONFIG["bsr_range"][1],
        "current_NEW_gte": int(TEXTBOOK_CONFIG["price_range"][0] * 100),
        "current_NEW_lte": int(TEXTBOOK_CONFIG["price_range"][1] * 100)
        # NOTE: FBA and Amazon filters done in post-processing
    }

    print("\n" + "="*70)
    print("SIMULATION UTILISATEUR: RECHERCHE TEXTBOOKS")
    print("="*70)
    print(f"\nParametres de recherche:")
    print(f"  - BSR: {TEXTBOOK_CONFIG['bsr_range'][0]:,} - {TEXTBOOK_CONFIG['bsr_range'][1]:,}")
    print(f"  - Prix: ${TEXTBOOK_CONFIG['price_range'][0]:.0f} - ${TEXTBOOK_CONFIG['price_range'][1]:.0f}")
    print(f"  - Max FBA sellers: {TEXTBOOK_CONFIG['max_fba_sellers']}")
    print(f"  - Amazon exclu: Oui")

    async with httpx.AsyncClient(timeout=30.0) as client:
        import json
        params = {
            "key": KEEPA_API_KEY,
            "domain": 1,
            "selection": json.dumps(selection)
        }

        response = await client.get(f"{KEEPA_BASE_URL}/query", params=params)

        if response.status_code != 200:
            print(f"\nErreur API: {response.status_code}")
            print(response.text[:200])
            return []

        data = response.json()
        asins = data.get("asinList", [])
        total = data.get("totalResults", 0)

        print(f"\nResultats: {total} produits trouves, {len(asins)} retournes")

        return asins  # Analyze all returned ASINs (up to 100)


async def get_product_details(asins: list) -> list:
    """Get detailed info for each ASIN."""
    if not asins:
        return []

    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": ",".join(asins),
        "stats": 1,
        "history": 0
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/product", params=params)

        if response.status_code != 200:
            return []

        data = response.json()
        products = []

        for p in data.get("products", []):
            asin = p.get("asin")
            title = p.get("title", "?")[:60]
            stats = p.get("stats", {})
            current = stats.get("current", [])

            # Extract metrics
            amazon_price = current[0] if len(current) > 0 else None
            new_price = current[1] if len(current) > 1 else None
            bsr = current[3] if len(current) > 3 else None
            fba_count = current[11] if len(current) > 11 else None

            # Skip if Amazon is selling
            availability_amazon = p.get("availabilityAmazon", -1)
            if availability_amazon >= 0:
                print(f"  [SKIP] {asin}: Amazon vend ce produit")
                continue

            # Skip if too many FBA sellers (competition)
            if fba_count is not None and fba_count > TEXTBOOK_CONFIG["max_fba_sellers"]:
                print(f"  [SKIP] {asin}: Trop de FBA sellers ({fba_count} > {TEXTBOOK_CONFIG['max_fba_sellers']})")
                continue

            # Skip if no valid price
            if not new_price or new_price <= 0:
                continue

            price_dollars = new_price / 100

            # Skip if outside price range
            if price_dollars < TEXTBOOK_CONFIG["price_range"][0] or price_dollars > TEXTBOOK_CONFIG["price_range"][1]:
                continue

            products.append({
                "asin": asin,
                "title": title,
                "price": price_dollars,
                "bsr": bsr,
                "fba_sellers": fba_count,
                "availability_amazon": availability_amazon,
                "sales_drops_30": stats.get("salesRankDrops30", 0),
                "sales_drops_90": stats.get("salesRankDrops90", 0)
            })

        return products


async def run_simulation():
    """Run full user simulation."""

    # Step 1: Discover products
    asins = await discover_textbooks()

    if not asins:
        print("\nAucun produit trouve avec ces criteres.")
        return

    # Step 2: Get details and filter
    print(f"\nAnalyse de {len(asins)} produits...")
    products = await get_product_details(asins)

    if not products:
        print("\nAucun produit valide apres filtrage.")
        return

    print(f"\n{len(products)} produits valides trouves!")

    # Step 3: Calculate profits
    print("\n" + "="*70)
    print("ANALYSE DE PROFIT PAR PRODUIT")
    print("="*70)

    total_investment = 0
    total_profit = 0
    profitable_products = []

    for p in products:
        profit_data = calculate_profit(p["price"])

        # Estimate monthly sales based on BSR and sales drops
        sales_velocity = "FAST" if p["bsr"] < 50000 else "MEDIUM" if p["bsr"] < 100000 else "SLOW"
        est_monthly_sales = p.get("sales_drops_30", 0)  # Sales drops ~ sales

        print(f"\n{'='*60}")
        print(f"ASIN: {p['asin']}")
        print(f"Titre: {p['title']}...")
        print(f"BSR: #{p['bsr']:,} | FBA Sellers: {p['fba_sellers']} | Velocite: {sales_velocity}")
        print(f"Sales drops (30j): {est_monthly_sales}")
        print(f"\n  Prix de vente:      ${profit_data['sell_price']:.2f}")
        print(f"  Cout d'achat (50%): ${profit_data['buy_cost']:.2f}")
        print(f"  Frais FBA total:    ${profit_data['fees']['total']:.2f}")
        print(f"    - Referral (15%): ${profit_data['fees']['referral']:.2f}")
        print(f"    - Closing fee:    ${profit_data['fees']['closing']:.2f}")
        print(f"    - Fulfillment:    ${profit_data['fees']['fulfillment']:.2f}")
        print(f"    - Prep + Inbound: ${profit_data['fees']['prep'] + profit_data['fees']['inbound']:.2f}")
        print(f"  -----------------------------------------")
        print(f"  PROFIT NET:         ${profit_data['profit_net']:.2f}")
        print(f"  ROI:                {profit_data['roi_percent']:.1f}%")
        print(f"  Marge:              {profit_data['margin_percent']:.1f}%")

        if profit_data['profit_net'] > 0:
            profitable_products.append({
                **p,
                "profit": profit_data['profit_net'],
                "roi": profit_data['roi_percent'],
                "buy_cost": profit_data['buy_cost']
            })
            total_investment += profit_data['buy_cost']
            total_profit += profit_data['profit_net']

    # Summary
    print("\n\n" + "="*70)
    print("RESUME DE LA SIMULATION")
    print("="*70)

    print(f"\nProduits analyses: {len(products)}")
    print(f"Produits rentables: {len(profitable_products)}")

    if profitable_products:
        avg_profit = total_profit / len(profitable_products)
        avg_roi = (total_profit / total_investment) * 100 if total_investment > 0 else 0

        print(f"\n--- Si vous achetez TOUS les {len(profitable_products)} produits rentables ---")
        print(f"Investissement total: ${total_investment:.2f}")
        print(f"Profit total (1 vente chacun): ${total_profit:.2f}")
        print(f"ROI moyen: {avg_roi:.1f}%")
        print(f"Profit moyen par livre: ${avg_profit:.2f}")

        # Scenario: Buy 5 books
        print(f"\n--- Scenario realiste: Acheter 5 meilleurs livres ---")
        top_5 = sorted(profitable_products, key=lambda x: x['profit'], reverse=True)[:5]
        scenario_investment = sum(p['buy_cost'] for p in top_5)
        scenario_profit = sum(p['profit'] for p in top_5)

        print(f"Investissement: ${scenario_investment:.2f}")
        print(f"Profit (si tout vendu en 1-2 mois): ${scenario_profit:.2f}")
        print(f"ROI: {(scenario_profit/scenario_investment)*100:.1f}%")

        print("\nTop 5 produits:")
        for i, p in enumerate(top_5, 1):
            print(f"  {i}. {p['asin']} - ${p['profit']:.2f} profit ({p['roi']:.0f}% ROI) - BSR #{p['bsr']:,}")

    return profitable_products


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    asyncio.run(run_simulation())
