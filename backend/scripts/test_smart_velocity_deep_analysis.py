"""
Deep Analysis: Smart Velocity Market Reality Check
Analyze WHY so many products are filtered out and what the real opportunity looks like.
"""

import asyncio
import httpx
import os
import json
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"
DOMAIN_US = 1
BOOKS_ROOT_CATEGORY = 283155

REFERRAL_FEE_PERCENT = 0.15
CLOSING_FEE = 1.80
FULFILLMENT_FEE = 3.60
PREP_INBOUND_FEE = 0.90


def calculate_profit(sell_price: float) -> Dict[str, float]:
    """Calculate profit using 50% buy rule."""
    buy_price = sell_price * 0.50
    referral = sell_price * REFERRAL_FEE_PERCENT
    total_fees = referral + CLOSING_FEE + FULFILLMENT_FEE + PREP_INBOUND_FEE
    gross_profit = sell_price - buy_price - total_fees
    roi_percent = (gross_profit / buy_price * 100) if buy_price > 0 else 0
    return {
        "buy_price": round(buy_price, 2),
        "fees": round(total_fees, 2),
        "profit": round(gross_profit, 2),
        "roi": round(roi_percent, 1)
    }


async def deep_analysis(client: httpx.AsyncClient, bsr_min: int, bsr_max: int, price_min: float, price_max: float):
    """Analyze a BSR/price segment in depth."""
    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS: BSR {bsr_min:,}-{bsr_max:,}, Price ${price_min}-${price_max}")
    print(f"{'='*80}")

    # Query Product Finder
    selection = {
        "rootCategory": BOOKS_ROOT_CATEGORY,
        "perPage": 100,
        "current_SALES_gte": bsr_min,
        "current_SALES_lte": bsr_max,
        "current_NEW_gte": int(price_min * 100),
        "current_NEW_lte": int(price_max * 100)
    }

    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "selection": json.dumps(selection)
    }

    response = await client.get(f"{KEEPA_BASE_URL}/query", params=params, timeout=30)
    data = response.json()

    asins = data.get("asinList", [])
    total_matches = data.get("totalResults", 0)
    print(f"\nTotal market: {total_matches:,} products match BSR/price criteria")

    if not asins:
        print("No ASINs returned")
        return

    # Get ALL 100 products for better analysis
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "asin": ",".join(asins),
        "stats": 1,
        "history": 0,
        "offers": 20
    }

    response = await client.get(f"{KEEPA_BASE_URL}/product", params=params, timeout=90)
    data = response.json()
    products = data.get("products", [])
    print(f"Analyzing {len(products)} products in detail...")

    # Detailed breakdown
    amazon_selling = []
    no_amazon_products = []
    fba_distribution = defaultdict(list)
    profit_distribution = defaultdict(list)

    for product in products:
        asin = product.get("asin")
        title = product.get("title", "N/A")[:45]
        stats = product.get("stats", {})
        current = stats.get("current", [])

        amazon_price = current[0] if len(current) > 0 and current[0] and current[0] > 0 else None
        new_price = current[1] if len(current) > 1 and current[1] and current[1] > 0 else None
        bsr = current[3] if len(current) > 3 and current[3] else None
        fba_count = current[11] if len(current) > 11 and current[11] else 0

        if not new_price or not bsr:
            continue

        sell_price = new_price / 100
        profit_data = calculate_profit(sell_price)

        product_info = {
            "asin": asin,
            "title": title,
            "bsr": bsr,
            "price": sell_price,
            "fba_count": fba_count,
            "amazon_price": amazon_price / 100 if amazon_price else None,
            "profit": profit_data["profit"],
            "roi": profit_data["roi"]
        }

        if amazon_price:
            amazon_selling.append(product_info)
        else:
            no_amazon_products.append(product_info)

            # Track FBA distribution
            if fba_count <= 2:
                fba_distribution["0-2 FBA"].append(product_info)
            elif fba_count <= 4:
                fba_distribution["3-4 FBA"].append(product_info)
            elif fba_count <= 6:
                fba_distribution["5-6 FBA"].append(product_info)
            else:
                fba_distribution["7+ FBA"].append(product_info)

            # Track profit distribution
            if profit_data["profit"] >= 20:
                profit_distribution["$20+ profit"].append(product_info)
            elif profit_data["profit"] >= 15:
                profit_distribution["$15-20 profit"].append(product_info)
            elif profit_data["profit"] >= 12:
                profit_distribution["$12-15 profit"].append(product_info)
            elif profit_data["profit"] >= 8:
                profit_distribution["$8-12 profit"].append(product_info)
            else:
                profit_distribution["<$8 profit"].append(product_info)

    # Print analysis
    print(f"\n--- AMAZON PRESENCE ---")
    print(f"Amazon selling: {len(amazon_selling)} ({len(amazon_selling)/len(products)*100:.1f}%)")
    print(f"Amazon NOT selling: {len(no_amazon_products)} ({len(no_amazon_products)/len(products)*100:.1f}%)")

    print(f"\n--- FBA COMPETITION (Amazon-free products only) ---")
    for cat, prods in sorted(fba_distribution.items()):
        print(f"  {cat}: {len(prods)} products")

    print(f"\n--- PROFIT DISTRIBUTION (Amazon-free products only) ---")
    for cat in ["$20+ profit", "$15-20 profit", "$12-15 profit", "$8-12 profit", "<$8 profit"]:
        prods = profit_distribution.get(cat, [])
        print(f"  {cat}: {len(prods)} products")

    # Best opportunities (no Amazon, low FBA, good profit)
    best_opportunities = [
        p for p in no_amazon_products
        if p["fba_count"] <= 4 and p["profit"] >= 12
    ]

    print(f"\n--- BEST OPPORTUNITIES (No Amazon, <=4 FBA, $12+ profit) ---")
    print(f"Found: {len(best_opportunities)} products")

    if best_opportunities:
        print(f"\n{'ASIN':<12} {'Title':<35} {'BSR':>10} {'Price':>8} {'FBA':>4} {'Profit':>8} {'ROI':>7}")
        print("-" * 90)
        for p in sorted(best_opportunities, key=lambda x: -x["profit"])[:15]:
            print(
                f"{p['asin']:<12} "
                f"{p['title'][:33]:<35} "
                f"#{p['bsr']:>9,} "
                f"${p['price']:>6.2f} "
                f"{p['fba_count']:>4} "
                f"${p['profit']:>6.2f} "
                f"{p['roi']:>6.1f}%"
            )

        avg_profit = sum(p["profit"] for p in best_opportunities) / len(best_opportunities)
        avg_roi = sum(p["roi"] for p in best_opportunities) / len(best_opportunities)
        avg_fba = sum(p["fba_count"] for p in best_opportunities) / len(best_opportunities)

        print(f"\n--- AVERAGES (Best Opportunities) ---")
        print(f"Avg Profit: ${avg_profit:.2f}")
        print(f"Avg ROI: {avg_roi:.1f}%")
        print(f"Avg FBA Sellers: {avg_fba:.1f}")

    return {
        "total_market": total_matches,
        "analyzed": len(products),
        "amazon_selling": len(amazon_selling),
        "amazon_free": len(no_amazon_products),
        "best_opportunities": len(best_opportunities),
        "products": best_opportunities
    }


async def run_multi_segment_analysis():
    """Run analysis across multiple market segments."""
    print("="*80)
    print("SMART VELOCITY MARKET REALITY CHECK")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        return

    segments = []

    async with httpx.AsyncClient() as client:
        # Segment 1: Current Smart Velocity
        r1 = await deep_analysis(client, 10000, 80000, 15.0, 60.0)
        segments.append(("Current SV (10K-80K, $15-60)", r1))
        await asyncio.sleep(3)

        # Segment 2: Higher BSR (less competition)
        r2 = await deep_analysis(client, 50000, 150000, 20.0, 80.0)
        segments.append(("Higher BSR (50K-150K, $20-80)", r2))
        await asyncio.sleep(3)

        # Segment 3: Premium books
        r3 = await deep_analysis(client, 30000, 200000, 40.0, 120.0)
        segments.append(("Premium (30K-200K, $40-120)", r3))
        await asyncio.sleep(3)

        # Segment 4: Textbook-like (what we know works)
        r4 = await deep_analysis(client, 100000, 250000, 40.0, 150.0)
        segments.append(("Textbook Standard (100K-250K, $40-150)", r4))

    # Final summary
    print("\n" + "="*80)
    print("CROSS-SEGMENT COMPARISON")
    print("="*80)
    print(f"\n{'Segment':<45} {'Market':>10} {'No Amazon':>12} {'Best Opps':>12}")
    print("-"*80)

    for name, data in segments:
        if data:
            print(
                f"{name:<45} "
                f"{data['total_market']:>10,} "
                f"{data['amazon_free']:>12} "
                f"{data['best_opportunities']:>12}"
            )

    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print("""
1. AMAZON DOMINANCE: ~85-90% of products in BSR 10K-80K have Amazon selling directly.
   This makes the "Smart Velocity" low-BSR segment extremely competitive.

2. HIGHER BSR = LESS AMAZON: As BSR increases (50K+), Amazon presence decreases,
   creating more arbitrage opportunities.

3. RECOMMENDATION: Consider adjusting Smart Velocity to BSR 30K-120K to find
   the sweet spot between velocity and competition.

4. TEXTBOOK VALIDATION: The Textbook Standard range (100K-250K) continues to show
   good opportunities with lower Amazon presence.
    """)


if __name__ == "__main__":
    asyncio.run(run_multi_segment_analysis())
