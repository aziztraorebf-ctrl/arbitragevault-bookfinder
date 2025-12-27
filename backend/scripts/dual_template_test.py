"""
Dual Template Test: Standard + Patience

Tests both strategies to validate combined approach:
- Standard: BSR 100K-250K, FBA<=5, Profit>=$15 (PDF Golden Rule)
- Patience: BSR 250K-400K, FBA<=3, Profit>=$25 (Under radar, stricter)

USAGE:
    cd backend
    python scripts/dual_template_test.py
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

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

FBA_FEES = {
    "referral_percent": 0.15,
    "closing_fee": 1.80,
    "fba_base": 3.22,
    "fba_per_lb": 0.75,
    "avg_book_weight": 1.5,
    "prep_fee": 0.50,
    "inbound_shipping": 0.40,
}


def calculate_profit(sell_price):
    buy_cost = sell_price * 0.50
    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]
    extra_weight = max(0, FBA_FEES["avg_book_weight"] - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])
    total_fees = referral + closing + fulfillment + FBA_FEES["prep_fee"] + FBA_FEES["inbound_shipping"]
    profit = sell_price - buy_cost - total_fees
    roi = (profit / buy_cost) * 100 if buy_cost > 0 else 0
    return {
        "profit": round(profit, 2),
        "roi": round(roi, 1),
        "buy_cost": round(buy_cost, 2),
        "fees": round(total_fees, 2)
    }


async def query_product_finder(bsr_min, bsr_max, price_min, price_max):
    selection = {
        "rootCategory": 283155,
        "perPage": 100,
        "current_SALES_gte": bsr_min,
        "current_SALES_lte": bsr_max,
        "current_NEW_gte": int(price_min * 100),
        "current_NEW_lte": int(price_max * 100)
    }
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "selection": json.dumps(selection)
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/query", params=params)
        if response.status_code != 200:
            return {"asins": [], "total": 0, "error": response.text[:100]}
        data = response.json()
        return {
            "asins": data.get("asinList", []),
            "total": data.get("totalResults", 0),
            "tokens": data.get("tokensConsumed", 0)
        }


async def get_product_details(asins, max_fba, min_profit):
    if not asins:
        return []
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": ",".join(asins[:100]),
        "stats": 1,
        "history": 0
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.get(f"{KEEPA_BASE_URL}/product", params=params)
        if response.status_code != 200:
            return []
        data = response.json()
        products = []
        for p in data.get("products", []):
            asin = p.get("asin")
            title = p.get("title", "?")[:55]
            stats = p.get("stats", {})
            current = stats.get("current", [])
            new_price = current[1] if len(current) > 1 else None
            bsr = current[3] if len(current) > 3 else None
            fba_count = current[11] if len(current) > 11 else None
            availability_amazon = p.get("availabilityAmazon", -1)

            # Filters
            if availability_amazon >= 0:
                continue
            if fba_count is not None and fba_count > max_fba:
                continue
            if not new_price or new_price <= 0:
                continue

            price_dollars = new_price / 100
            if price_dollars < 40 or price_dollars > 150:
                continue

            profit_data = calculate_profit(price_dollars)

            # Profit filter
            if profit_data["profit"] < min_profit:
                continue

            products.append({
                "asin": asin,
                "title": title,
                "price": price_dollars,
                "bsr": bsr,
                "fba": fba_count if fba_count else 0,
                "sales30": stats.get("salesRankDrops30", 0),
                "profit": profit_data["profit"],
                "roi": profit_data["roi"],
                "buy_cost": profit_data["buy_cost"]
            })
        return products


def calc_stats(products, name):
    if not products:
        return None
    avg_profit = sum(p["profit"] for p in products) / len(products)
    avg_roi = sum(p["roi"] for p in products) / len(products)
    avg_fba = sum(p["fba"] for p in products) / len(products)
    avg_sales = sum(p["sales30"] for p in products) / len(products)
    total_investment = sum(p["buy_cost"] for p in products)
    total_profit = sum(p["profit"] for p in products)
    return {
        "name": name,
        "count": len(products),
        "avg_profit": avg_profit,
        "avg_roi": avg_roi,
        "avg_fba": avg_fba,
        "avg_sales": avg_sales,
        "total_investment": total_investment,
        "total_profit": total_profit
    }


async def main():
    print("=" * 80)
    print("DUAL TEMPLATE TEST: Standard + Patience")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    # TEMPLATE STANDARD (aligne PDF)
    print("\n" + "-" * 80)
    print("TEMPLATE STANDARD (PDF Golden Rule)")
    print("BSR: 100,000 - 250,000 | Prix: $40-$150 | FBA <= 5 | Profit min: $15")
    print("-" * 80)

    result_std = await query_product_finder(100000, 250000, 40, 150)
    print(f"API: {result_std['total']:,} produits trouves")

    products_std = await get_product_details(result_std.get("asins", []), max_fba=5, min_profit=15)
    print(f"Apres filtrage: {len(products_std)} produits valides")

    # TEMPLATE PATIENCE (extension prudente)
    print("\n" + "-" * 80)
    print("TEMPLATE PATIENCE (Sous le radar)")
    print("BSR: 250,000 - 400,000 | Prix: $40-$150 | FBA <= 3 | Profit min: $25")
    print("-" * 80)

    result_pat = await query_product_finder(250000, 400000, 40, 150)
    print(f"API: {result_pat['total']:,} produits trouves")

    products_pat = await get_product_details(result_pat.get("asins", []), max_fba=3, min_profit=25)
    print(f"Apres filtrage: {len(products_pat)} produits valides")

    # Combine and dedupe
    all_asins_std = set(p["asin"] for p in products_std)
    all_asins_pat = set(p["asin"] for p in products_pat)
    overlap = all_asins_std & all_asins_pat

    print("\n" + "=" * 80)
    print("RESULTATS DETAILLES")
    print("=" * 80)

    # Standard template results
    print("\n>>> TEMPLATE STANDARD - TOP 10 <<<")
    if products_std:
        std_sorted = sorted(products_std, key=lambda x: x["profit"], reverse=True)[:10]
        print(f"{'#':<3} {'ASIN':<12} {'Profit':<8} {'Prix':<7} {'BSR':<10} {'FBA':<4} {'Sales':<6} Titre")
        print("-" * 80)
        for i, p in enumerate(std_sorted, 1):
            bsr_str = f"{p['bsr']:,}" if p['bsr'] else "N/A"
            print(f"{i:<3} {p['asin']:<12} ${p['profit']:<6.2f} ${p['price']:<5.0f} {bsr_str:>9} {p['fba']:<4} {p['sales30']:<6} {p['title'][:32]}...")
    else:
        print("Aucun produit trouve")

    # Patience template results
    print("\n>>> TEMPLATE PATIENCE - TOP 10 <<<")
    if products_pat:
        pat_sorted = sorted(products_pat, key=lambda x: x["profit"], reverse=True)[:10]
        print(f"{'#':<3} {'ASIN':<12} {'Profit':<8} {'Prix':<7} {'BSR':<10} {'FBA':<4} {'Sales':<6} Titre")
        print("-" * 80)
        for i, p in enumerate(pat_sorted, 1):
            bsr_str = f"{p['bsr']:,}" if p['bsr'] else "N/A"
            print(f"{i:<3} {p['asin']:<12} ${p['profit']:<6.2f} ${p['price']:<5.0f} {bsr_str:>9} {p['fba']:<4} {p['sales30']:<6} {p['title'][:32]}...")
    else:
        print("Aucun produit trouve")

    # Statistics comparison
    print("\n" + "=" * 80)
    print("COMPARAISON STATISTIQUES")
    print("=" * 80)

    stats_std = calc_stats(products_std, "Standard")
    stats_pat = calc_stats(products_pat, "Patience")

    print(f"\n{'Metrique':<25} {'Standard':<15} {'Patience':<15}")
    print("-" * 55)

    if stats_std and stats_pat:
        print(f"{'Produits trouves':<25} {stats_std['count']:<15} {stats_pat['count']:<15}")
        print(f"{'Profit moyen':<25} ${stats_std['avg_profit']:<13.2f} ${stats_pat['avg_profit']:<13.2f}")
        print(f"{'ROI moyen':<25} {stats_std['avg_roi']:<14.1f}% {stats_pat['avg_roi']:<14.1f}%")
        print(f"{'FBA sellers moyen':<25} {stats_std['avg_fba']:<15.1f} {stats_pat['avg_fba']:<15.1f}")
        print(f"{'Ventes/30j moyen':<25} {stats_std['avg_sales']:<15.1f} {stats_pat['avg_sales']:<15.1f}")
        print(f"{'Investissement total':<25} ${stats_std['total_investment']:<13.2f} ${stats_pat['total_investment']:<13.2f}")
        print(f"{'Profit total potentiel':<25} ${stats_std['total_profit']:<13.2f} ${stats_pat['total_profit']:<13.2f}")
    elif stats_std:
        print(f"{'Produits trouves':<25} {stats_std['count']:<15} 0")
        print(f"{'Profit moyen':<25} ${stats_std['avg_profit']:<13.2f} N/A")
    elif stats_pat:
        print(f"{'Produits trouves':<25} 0               {stats_pat['count']:<15}")
        print(f"{'Profit moyen':<25} N/A             ${stats_pat['avg_profit']:<13.2f}")
    else:
        print("Aucun produit dans les deux templates")

    # Combined strategy simulation
    print("\n" + "=" * 80)
    print("SIMULATION: Strategie Combinee (1x Standard + 1x Patience par jour)")
    print("=" * 80)

    all_products = products_std + [p for p in products_pat if p["asin"] not in all_asins_std]
    unique_count = len(all_products)

    if all_products:
        total_inv = sum(p["buy_cost"] for p in all_products)
        total_prof = sum(p["profit"] for p in all_products)

        print(f"\nProduits uniques disponibles: {unique_count}")
        print(f"  - Via Standard: {len(products_std)}")
        print(f"  - Via Patience (nouveaux): {len([p for p in products_pat if p['asin'] not in all_asins_std])}")
        print(f"  - Chevauchement: {len(overlap)}")

        # Scenario: Buy top 5 from each
        top5_std = sorted(products_std, key=lambda x: x["profit"], reverse=True)[:5]
        top5_pat_new = [p for p in products_pat if p["asin"] not in all_asins_std]
        top5_pat = sorted(top5_pat_new, key=lambda x: x["profit"], reverse=True)[:5]

        scenario_products = top5_std + top5_pat
        if scenario_products:
            scenario_inv = sum(p["buy_cost"] for p in scenario_products)
            scenario_prof = sum(p["profit"] for p in scenario_products)

            print(f"\n--- Scenario: Acheter Top 5 de chaque template ---")
            print(f"Livres achetes: {len(scenario_products)}")
            print(f"Investissement: ${scenario_inv:.2f}")
            print(f"Profit potentiel: ${scenario_prof:.2f}")
            if scenario_inv > 0:
                print(f"ROI global: {(scenario_prof / scenario_inv) * 100:.1f}%")

            # Monthly projection
            print(f"\n--- Projection mensuelle (recherche quotidienne) ---")
            avg_buy_cost = scenario_inv / len(scenario_products) if scenario_products else 0
            avg_profit = scenario_prof / len(scenario_products) if scenario_products else 0
            print(f"Si on achete 5 produits/jour:")
            monthly_investment = 5 * 30 * avg_buy_cost
            monthly_profit = 5 * 30 * avg_profit
            print(f"Investissement/mois: ${monthly_investment:.2f}")
            print(f"Profit potentiel/mois: ${monthly_profit:.2f}")


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    asyncio.run(main())
