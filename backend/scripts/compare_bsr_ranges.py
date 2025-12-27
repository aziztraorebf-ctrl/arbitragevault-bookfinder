"""
Comparison Test: BSR 30K-100K vs BSR 100K-250K

Tests both BSR ranges with corrected parameters:
- Price: $40-$150
- FBA sellers: <= 5
- No Amazon

USAGE:
    cd backend
    python scripts/compare_bsr_ranges.py
"""

import asyncio
import os
import sys
import json
from pathlib import Path

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

# FBA Fee structure for Books
FBA_FEES = {
    "referral_percent": 0.15,
    "closing_fee": 1.80,
    "fba_base": 3.22,
    "fba_per_lb": 0.75,
    "avg_book_weight": 1.5,
    "prep_fee": 0.50,
    "inbound_shipping": 0.40,
}

SOURCE_PRICE_FACTOR = 0.50


def calculate_profit(sell_price):
    """Calculate realistic profit for a textbook."""
    buy_cost = sell_price * SOURCE_PRICE_FACTOR

    referral = sell_price * FBA_FEES["referral_percent"]
    closing = FBA_FEES["closing_fee"]
    extra_weight = max(0, FBA_FEES["avg_book_weight"] - 1)
    fulfillment = FBA_FEES["fba_base"] + (extra_weight * FBA_FEES["fba_per_lb"])
    prep = FBA_FEES["prep_fee"]
    inbound = FBA_FEES["inbound_shipping"]

    total_fees = referral + closing + fulfillment + prep + inbound
    profit = sell_price - buy_cost - total_fees
    roi = (profit / buy_cost) * 100 if buy_cost > 0 else 0

    return {
        "sell_price": round(sell_price, 2),
        "buy_cost": round(buy_cost, 2),
        "fees": round(total_fees, 2),
        "profit": round(profit, 2),
        "roi": round(roi, 1)
    }


async def query_product_finder(bsr_min, bsr_max, price_min, price_max):
    """Query Keepa Product Finder."""
    selection = {
        "rootCategory": 283155,  # Books
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
            return {"error": response.text[:200], "asins": [], "total": 0}

        data = response.json()
        return {
            "asins": data.get("asinList", []),
            "total": data.get("totalResults", 0),
            "tokens": data.get("tokensConsumed", 0)
        }


async def get_product_details(asins):
    """Get details for ASINs and filter."""
    if not asins:
        return []

    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,
        "asin": ",".join(asins[:50]),  # Limit to 50 for token efficiency
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
            title = p.get("title", "?")[:50]
            stats = p.get("stats", {})
            current = stats.get("current", [])

            # Extract metrics
            amazon_price = current[0] if len(current) > 0 else None
            new_price = current[1] if len(current) > 1 else None
            bsr = current[3] if len(current) > 3 else None
            fba_count = current[11] if len(current) > 11 else None

            # Availability check
            availability_amazon = p.get("availabilityAmazon", -1)

            # Skip if Amazon is selling
            if availability_amazon >= 0:
                continue

            # Skip if too many FBA sellers
            if fba_count is not None and fba_count > 5:
                continue

            # Skip if no valid price
            if not new_price or new_price <= 0:
                continue

            price_dollars = new_price / 100

            # Skip if outside price range
            if price_dollars < 40 or price_dollars > 150:
                continue

            # Calculate profit
            profit_data = calculate_profit(price_dollars)

            products.append({
                "asin": asin,
                "title": title,
                "price": price_dollars,
                "bsr": bsr,
                "fba_sellers": fba_count if fba_count else 0,
                "sales_drops_30": stats.get("salesRankDrops30", 0),
                "profit": profit_data["profit"],
                "roi": profit_data["roi"]
            })

        return products


async def run_comparison():
    """Run comparison between two BSR ranges."""

    print("\n" + "="*70)
    print("COMPARISON TEST: BSR RANGES")
    print("Parameters: Price $40-$150, FBA<=5, No Amazon")
    print("="*70)

    # Test A: BSR 30K-100K (Faster rotation, more competition)
    print("\n>>> TEST A: BSR 30,000 - 100,000 <<<")
    result_a = await query_product_finder(30000, 100000, 40, 150)
    print(f"API Result: {result_a['total']} products found")

    products_a = await get_product_details(result_a.get("asins", []))
    print(f"After filtering: {len(products_a)} valid products")

    # Test B: BSR 100K-250K (Slower rotation, less competition)
    print("\n>>> TEST B: BSR 100,000 - 250,000 <<<")
    result_b = await query_product_finder(100000, 250000, 40, 150)
    print(f"API Result: {result_b['total']} products found")

    products_b = await get_product_details(result_b.get("asins", []))
    print(f"After filtering: {len(products_b)} valid products")

    # Analysis
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    def analyze_group(products, name):
        if not products:
            print(f"\n{name}: No products found")
            return None

        avg_profit = sum(p["profit"] for p in products) / len(products)
        avg_roi = sum(p["roi"] for p in products) / len(products)
        avg_fba = sum(p["fba_sellers"] for p in products) / len(products)
        avg_sales_30 = sum(p["sales_drops_30"] for p in products) / len(products)
        avg_bsr = sum(p["bsr"] for p in products if p["bsr"]) / len([p for p in products if p["bsr"]])
        profitable = [p for p in products if p["profit"] >= 20]

        print(f"\n{name}:")
        print(f"  Products found: {len(products)}")
        print(f"  Profitable ($20+): {len(profitable)} ({len(profitable)/len(products)*100:.0f}%)")
        print(f"  Avg Profit: ${avg_profit:.2f}")
        print(f"  Avg ROI: {avg_roi:.1f}%")
        print(f"  Avg FBA Sellers: {avg_fba:.1f} (competition)")
        print(f"  Avg Sales/30d: {avg_sales_30:.1f} (rotation)")
        print(f"  Avg BSR: {avg_bsr:,.0f}")

        return {
            "count": len(products),
            "profitable": len(profitable),
            "avg_profit": avg_profit,
            "avg_roi": avg_roi,
            "avg_fba": avg_fba,
            "avg_sales_30": avg_sales_30,
            "products": products
        }

    stats_a = analyze_group(products_a, "TEST A (BSR 30K-100K)")
    stats_b = analyze_group(products_b, "TEST B (BSR 100K-250K)")

    # Show top products from each
    print("\n" + "="*70)
    print("TOP 5 PRODUCTS FROM EACH TEST")
    print("="*70)

    for name, products in [("TEST A", products_a), ("TEST B", products_b)]:
        print(f"\n{name}:")
        top_5 = sorted(products, key=lambda x: x["profit"], reverse=True)[:5]
        for i, p in enumerate(top_5, 1):
            print(f"  {i}. {p['asin']} - ${p['profit']:.2f} profit - BSR #{p['bsr']:,} - FBA={p['fba_sellers']} - Sales/30d={p['sales_drops_30']}")
            print(f"     {p['title']}...")

    # Recommendation
    print("\n" + "="*70)
    print("RECOMMENDATION FOR PDF STRATEGY")
    print("(Patience + Volume + Diversification)")
    print("="*70)

    if stats_a and stats_b:
        # Compare based on strategy criteria
        if stats_b["avg_fba"] < stats_a["avg_fba"]:
            print("\n[+] TEST B has LESS competition (fewer FBA sellers)")
        else:
            print("\n[-] TEST A has LESS competition")

        if stats_b["avg_profit"] > stats_a["avg_profit"]:
            print("[+] TEST B has HIGHER average profit")
        else:
            print("[-] TEST A has HIGHER average profit")

        if stats_b["profitable"] > stats_a["profitable"]:
            print("[+] TEST B has MORE profitable products ($20+)")
        else:
            print("[-] TEST A has MORE profitable products ($20+)")

        # Overall recommendation
        b_score = 0
        if stats_b["avg_fba"] < stats_a["avg_fba"]: b_score += 1
        if stats_b["avg_profit"] > stats_a["avg_profit"]: b_score += 1
        if stats_b["profitable"] > stats_a["profitable"]: b_score += 1

        print("\n>>> VERDICT <<<")
        if b_score >= 2:
            print("TEST B (BSR 100K-250K) aligns better with PDF strategy:")
            print("- Less competition = easier to win Buy Box")
            print("- Higher profits = better ROI despite slower rotation")
            print("- Patience strategy: 5-10 sales/month OK if profit is $20+")
        else:
            print("TEST A (BSR 30K-100K) may be better for faster turnover.")
            print("Consider using BOTH ranges for diversification.")

    return {"test_a": stats_a, "test_b": stats_b}


if __name__ == "__main__":
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        sys.exit(1)

    asyncio.run(run_comparison())
