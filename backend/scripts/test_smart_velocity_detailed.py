"""
Test Script: Smart Velocity Detailed Analysis
More thorough test with larger sample size.
"""

import asyncio
import httpx
import os
import json
from typing import Dict, List
from datetime import datetime

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"
DOMAIN_US = 1
BOOKS_ROOT_CATEGORY = 283155

# FBA Fee Structure
REFERRAL_FEE_PERCENT = 0.15
CLOSING_FEE = 1.80
FULFILLMENT_FEE = 3.60
PREP_INBOUND_FEE = 0.90


def calculate_profit(sell_price: float, buy_price: float) -> Dict[str, float]:
    """Calculate net profit using 50% rule and FBA fees."""
    referral = sell_price * REFERRAL_FEE_PERCENT
    total_fees = referral + CLOSING_FEE + FULFILLMENT_FEE + PREP_INBOUND_FEE
    gross_profit = sell_price - buy_price - total_fees
    roi_percent = (gross_profit / buy_price * 100) if buy_price > 0 else 0
    return {
        "fees": round(total_fees, 2),
        "gross_profit": round(gross_profit, 2),
        "roi_percent": round(roi_percent, 1)
    }


async def test_config(
    client: httpx.AsyncClient,
    name: str,
    bsr_min: int,
    bsr_max: int,
    price_min: float,
    price_max: float,
    max_fba: int,
    min_margin: float,
    min_roi: float
) -> Dict:
    """Test a single configuration."""
    print(f"\n{'='*70}")
    print(f"TESTING: {name}")
    print(f"  BSR: {bsr_min:,} - {bsr_max:,}")
    print(f"  Price: ${price_min} - ${price_max}")
    print(f"  Max FBA: {max_fba}, Min Margin: ${min_margin}, Min ROI: {min_roi}%")
    print(f"{'='*70}")

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
    print(f"\nProduct Finder: {total_matches:,} total matches, {len(asins)} returned")

    if not asins:
        return {"name": name, "total_matches": total_matches, "qualifying": 0, "products": []}

    # Get product details - sample 50 ASINs
    sample_asins = asins[:50]
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "asin": ",".join(sample_asins),
        "stats": 1,
        "history": 0,
        "offers": 20
    }

    response = await client.get(f"{KEEPA_BASE_URL}/product", params=params, timeout=60)
    data = response.json()
    products_data = data.get("products", [])
    tokens = data.get("tokensConsumed", 0)
    print(f"Product details: {len(products_data)} products, {tokens} tokens")

    # Analyze products
    qualifying = []
    stats = {
        "amazon_selling": 0,
        "no_price": 0,
        "bsr_out_of_range": 0,
        "too_many_fba": 0,
        "low_margin": 0,
        "low_roi": 0,
        "passed": 0
    }

    for product in products_data:
        asin = product.get("asin")
        title = product.get("title", "N/A")[:50]
        stats_data = product.get("stats", {})
        current = stats_data.get("current", [])

        # Extract metrics
        amazon_price = current[0] if len(current) > 0 and current[0] and current[0] > 0 else None
        new_price = current[1] if len(current) > 1 and current[1] and current[1] > 0 else None
        bsr = current[3] if len(current) > 3 and current[3] else None
        fba_count = current[11] if len(current) > 11 and current[11] else 0

        # Filter: Amazon selling
        if amazon_price:
            stats["amazon_selling"] += 1
            continue

        # Filter: No price
        if not new_price:
            stats["no_price"] += 1
            continue

        sell_price = new_price / 100

        # Filter: BSR range
        if bsr is None or not (bsr_min <= bsr <= bsr_max):
            stats["bsr_out_of_range"] += 1
            continue

        # Filter: FBA competition
        if fba_count > max_fba:
            stats["too_many_fba"] += 1
            continue

        # Calculate profit (50% rule)
        buy_price = sell_price * 0.50
        profit = calculate_profit(sell_price, buy_price)

        # Filter: Minimum margin
        if profit["gross_profit"] < min_margin:
            stats["low_margin"] += 1
            continue

        # Filter: Minimum ROI
        if profit["roi_percent"] < min_roi:
            stats["low_roi"] += 1
            continue

        stats["passed"] += 1
        qualifying.append({
            "asin": asin,
            "title": title,
            "bsr": bsr,
            "sell_price": sell_price,
            "buy_price": buy_price,
            "fba_count": fba_count,
            "profit": profit["gross_profit"],
            "roi": profit["roi_percent"],
            "fees": profit["fees"]
        })

    # Print filter stats
    print(f"\nFilter breakdown (of {len(products_data)} products):")
    print(f"  - Amazon selling: {stats['amazon_selling']}")
    print(f"  - No price data: {stats['no_price']}")
    print(f"  - BSR out of range: {stats['bsr_out_of_range']}")
    print(f"  - Too many FBA ({max_fba}+ sellers): {stats['too_many_fba']}")
    print(f"  - Low margin (<${min_margin}): {stats['low_margin']}")
    print(f"  - Low ROI (<{min_roi}%): {stats['low_roi']}")
    print(f"  - PASSED ALL FILTERS: {stats['passed']}")

    # Print qualifying products
    if qualifying:
        print(f"\n{'ASIN':<12} {'Title':<40} {'BSR':>10} {'Price':>8} {'FBA':>4} {'Profit':>8} {'ROI':>7}")
        print("-" * 95)
        for p in sorted(qualifying, key=lambda x: -x["profit"])[:15]:
            print(
                f"{p['asin']:<12} "
                f"{p['title'][:38]:<40} "
                f"#{p['bsr']:>9,} "
                f"${p['sell_price']:>6.2f} "
                f"{p['fba_count']:>4} "
                f"${p['profit']:>6.2f} "
                f"{p['roi']:>6.1f}%"
            )

        avg_profit = sum(p["profit"] for p in qualifying) / len(qualifying)
        avg_roi = sum(p["roi"] for p in qualifying) / len(qualifying)
        avg_bsr = sum(p["bsr"] for p in qualifying) / len(qualifying)

        print(f"\n--- AVERAGES ---")
        print(f"Profit: ${avg_profit:.2f} | ROI: {avg_roi:.1f}% | BSR: #{avg_bsr:,.0f}")

    return {
        "name": name,
        "total_matches": total_matches,
        "analyzed": len(products_data),
        "qualifying": len(qualifying),
        "stats": stats,
        "products": qualifying
    }


async def run_detailed_tests():
    """Run detailed comparison tests."""
    print("="*70)
    print("SMART VELOCITY DETAILED OPTIMIZATION TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        return

    results = []

    async with httpx.AsyncClient() as client:
        # Test 1: Current Smart Velocity
        r1 = await test_config(
            client,
            name="CURRENT Smart Velocity",
            bsr_min=10000,
            bsr_max=80000,
            price_min=15.0,
            price_max=60.0,
            max_fba=5,
            min_margin=12.0,
            min_roi=30.0
        )
        results.append(r1)
        await asyncio.sleep(2)

        # Test 2: Optimized Smart Velocity (Option A)
        r2 = await test_config(
            client,
            name="OPTIMIZED Smart Velocity (Option A)",
            bsr_min=20000,
            bsr_max=100000,
            price_min=20.0,
            price_max=70.0,
            max_fba=4,
            min_margin=15.0,
            min_roi=35.0
        )
        results.append(r2)
        await asyncio.sleep(2)

        # Test 3: Alternative - Wider BSR, same competition
        r3 = await test_config(
            client,
            name="ALTERNATIVE: Wider BSR (10K-120K)",
            bsr_min=10000,
            bsr_max=120000,
            price_min=20.0,
            price_max=80.0,
            max_fba=4,
            min_margin=15.0,
            min_roi=35.0
        )
        results.append(r3)
        await asyncio.sleep(2)

        # Test 4: Higher price focus
        r4 = await test_config(
            client,
            name="HIGH VALUE: $30-100, BSR 20K-150K",
            bsr_min=20000,
            bsr_max=150000,
            price_min=30.0,
            price_max=100.0,
            max_fba=4,
            min_margin=18.0,
            min_roi=40.0
        )
        results.append(r4)

    # Final comparison
    print("\n" + "="*70)
    print("FINAL COMPARISON SUMMARY")
    print("="*70)
    print(f"\n{'Configuration':<40} {'Matches':>10} {'Qualify':>10} {'Avg Profit':>12} {'Avg ROI':>10}")
    print("-"*85)

    for r in results:
        avg_profit = "-"
        avg_roi = "-"
        if r["products"]:
            avg_profit = f"${sum(p['profit'] for p in r['products']) / len(r['products']):.2f}"
            avg_roi = f"{sum(p['roi'] for p in r['products']) / len(r['products']):.1f}%"

        print(
            f"{r['name']:<40} "
            f"{r['total_matches']:>10,} "
            f"{r['qualifying']:>10} "
            f"{avg_profit:>12} "
            f"{avg_roi:>10}"
        )

    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    # Find best config
    best = max(results, key=lambda x: (len(x["products"]), sum(p["profit"] for p in x["products"]) if x["products"] else 0))
    print(f"\nBest configuration: {best['name']}")
    print(f"  - {best['qualifying']} qualifying products found")
    if best["products"]:
        print(f"  - Average profit: ${sum(p['profit'] for p in best['products']) / len(best['products']):.2f}")


if __name__ == "__main__":
    asyncio.run(run_detailed_tests())
