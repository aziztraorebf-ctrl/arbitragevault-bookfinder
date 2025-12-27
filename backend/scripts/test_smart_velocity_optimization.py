"""
Test Script: Smart Velocity Optimization Analysis
Compare current vs optimized parameters with real Keepa API data.

Test Plan:
1. Current Smart Velocity: BSR 10K-80K, $15-60, max 5 FBA
2. Optimized Smart Velocity: BSR 20K-100K, $20-70, max 4 FBA
3. Calculate profit nets for both
"""

import asyncio
import httpx
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Keepa API configuration
KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"
DOMAIN_US = 1
BOOKS_ROOT_CATEGORY = 283155

# FBA Fee Structure (from PDF Golden Rule)
REFERRAL_FEE_PERCENT = 0.15  # 15%
CLOSING_FEE = 1.80  # $1.80 per book
FULFILLMENT_FEE = 3.60  # ~$3.60 average for books
PREP_INBOUND_FEE = 0.90  # ~$0.90 prep + inbound


@dataclass
class TestConfig:
    """Test configuration for Smart Velocity variants."""
    name: str
    bsr_min: int
    bsr_max: int
    price_min: float
    price_max: float
    max_fba_sellers: int
    min_roi: float
    min_margin: float


# Test configurations
CURRENT_CONFIG = TestConfig(
    name="Smart Velocity (Current)",
    bsr_min=10000,
    bsr_max=80000,
    price_min=15.0,
    price_max=60.0,
    max_fba_sellers=5,
    min_roi=30.0,
    min_margin=12.0
)

OPTIMIZED_CONFIG = TestConfig(
    name="Smart Velocity (Optimized)",
    bsr_min=20000,
    bsr_max=100000,
    price_min=20.0,
    price_max=70.0,
    max_fba_sellers=4,
    min_roi=35.0,
    min_margin=15.0
)


def calculate_fba_fees(sell_price: float) -> Dict[str, float]:
    """Calculate FBA fees for a given sell price."""
    referral = sell_price * REFERRAL_FEE_PERCENT
    total_fees = referral + CLOSING_FEE + FULFILLMENT_FEE + PREP_INBOUND_FEE
    return {
        "referral": round(referral, 2),
        "closing": CLOSING_FEE,
        "fulfillment": FULFILLMENT_FEE,
        "prep_inbound": PREP_INBOUND_FEE,
        "total": round(total_fees, 2)
    }


def calculate_profit(sell_price: float, buy_price: float) -> Dict[str, float]:
    """Calculate net profit using 50% rule and FBA fees."""
    fees = calculate_fba_fees(sell_price)
    gross_profit = sell_price - buy_price - fees["total"]
    roi_percent = (gross_profit / buy_price * 100) if buy_price > 0 else 0

    return {
        "sell_price": sell_price,
        "buy_price": buy_price,
        "fees": fees["total"],
        "gross_profit": round(gross_profit, 2),
        "roi_percent": round(roi_percent, 1)
    }


async def query_product_finder(
    client: httpx.AsyncClient,
    config: TestConfig
) -> List[str]:
    """Query Keepa Product Finder with given config."""
    selection = {
        "rootCategory": BOOKS_ROOT_CATEGORY,
        "perPage": 100,
        "current_SALES_gte": config.bsr_min,
        "current_SALES_lte": config.bsr_max,
        "current_NEW_gte": int(config.price_min * 100),
        "current_NEW_lte": int(config.price_max * 100)
    }

    import json
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "selection": json.dumps(selection)
    }

    print(f"\n[QUERY] {config.name}")
    print(f"  BSR: {config.bsr_min:,} - {config.bsr_max:,}")
    print(f"  Price: ${config.price_min} - ${config.price_max}")

    response = await client.get(f"{KEEPA_BASE_URL}/query", params=params, timeout=30)
    data = response.json()

    asins = data.get("asinList", [])
    total = data.get("totalResults", 0)
    tokens = data.get("tokensConsumed", 0)

    print(f"  Total matches: {total:,}")
    print(f"  ASINs returned: {len(asins)}")
    print(f"  Tokens used: {tokens}")

    return asins


async def get_product_details(
    client: httpx.AsyncClient,
    asins: List[str]
) -> List[Dict]:
    """Get detailed product data for analysis."""
    if not asins:
        return []

    # Limit to 20 ASINs to save tokens
    asins = asins[:20]

    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "asin": ",".join(asins),
        "stats": 1,
        "history": 0,
        "offers": 20
    }

    response = await client.get(f"{KEEPA_BASE_URL}/product", params=params, timeout=60)
    data = response.json()

    products = []
    for product in data.get("products", []):
        asin = product.get("asin")
        title = product.get("title", "N/A")[:60]
        stats = product.get("stats", {})
        current = stats.get("current", [])

        # Extract key metrics
        amazon_price = current[0] if len(current) > 0 and current[0] and current[0] > 0 else None
        new_price = current[1] if len(current) > 1 and current[1] and current[1] > 0 else None
        bsr = current[3] if len(current) > 3 and current[3] else None
        fba_count = current[11] if len(current) > 11 else 0

        # Skip if Amazon is selling
        if amazon_price:
            continue

        # Convert prices from cents
        if new_price:
            new_price = new_price / 100

        # Get FBA offers for competition analysis
        offers = product.get("offers", [])
        fba_offers = [o for o in offers if o.get("isFBA") and o.get("condition") == 1]

        products.append({
            "asin": asin,
            "title": title,
            "bsr": bsr,
            "new_price": new_price,
            "fba_count": fba_count,
            "fba_offers": len(fba_offers),
            "amazon_selling": amazon_price is not None
        })

    return products


def analyze_products(
    products: List[Dict],
    config: TestConfig
) -> Dict:
    """Analyze products against config criteria."""
    qualifying = []

    for p in products:
        if p["amazon_selling"]:
            continue

        if p["bsr"] is None or p["new_price"] is None:
            continue

        # Check BSR range
        if not (config.bsr_min <= p["bsr"] <= config.bsr_max):
            continue

        # Check FBA competition
        if p["fba_count"] and p["fba_count"] > config.max_fba_sellers:
            continue

        # Calculate profit using 50% rule
        sell_price = p["new_price"]
        buy_price = sell_price * 0.50  # 50% rule
        profit_data = calculate_profit(sell_price, buy_price)

        # Check minimum margin
        if profit_data["gross_profit"] < config.min_margin:
            continue

        # Check minimum ROI
        if profit_data["roi_percent"] < config.min_roi:
            continue

        qualifying.append({
            **p,
            **profit_data,
            "passes_filters": True
        })

    return {
        "total_analyzed": len(products),
        "qualifying": len(qualifying),
        "products": qualifying
    }


def print_results(config: TestConfig, analysis: Dict):
    """Print analysis results in formatted table."""
    print(f"\n{'='*80}")
    print(f"RESULTS: {config.name}")
    print(f"{'='*80}")
    print(f"Products analyzed: {analysis['total_analyzed']}")
    print(f"Qualifying products: {analysis['qualifying']}")

    if analysis["products"]:
        print(f"\n{'ASIN':<12} {'Title':<35} {'BSR':>10} {'Price':>8} {'FBA':>4} {'Profit':>8} {'ROI':>6}")
        print("-" * 95)

        for p in analysis["products"][:10]:  # Top 10
            print(
                f"{p['asin']:<12} "
                f"{p['title'][:33]:<35} "
                f"#{p['bsr']:>9,} "
                f"${p['sell_price']:>6.2f} "
                f"{p['fba_count'] or 0:>4} "
                f"${p['gross_profit']:>6.2f} "
                f"{p['roi_percent']:>5.1f}%"
            )

        # Summary stats
        if analysis["products"]:
            avg_profit = sum(p["gross_profit"] for p in analysis["products"]) / len(analysis["products"])
            avg_roi = sum(p["roi_percent"] for p in analysis["products"]) / len(analysis["products"])
            avg_bsr = sum(p["bsr"] for p in analysis["products"]) / len(analysis["products"])

            print(f"\n--- SUMMARY ---")
            print(f"Average Profit: ${avg_profit:.2f}")
            print(f"Average ROI: {avg_roi:.1f}%")
            print(f"Average BSR: #{avg_bsr:,.0f}")
    else:
        print("\nNo qualifying products found with these criteria.")


async def run_comparison_test():
    """Run comparison test between current and optimized configs."""
    print("="*80)
    print("SMART VELOCITY OPTIMIZATION TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not set")
        return

    async with httpx.AsyncClient() as client:
        # Test 1: Current configuration
        print("\n" + "="*80)
        print("TEST 1: CURRENT SMART VELOCITY PARAMETERS")
        print("="*80)

        current_asins = await query_product_finder(client, CURRENT_CONFIG)
        current_products = await get_product_details(client, current_asins)
        current_analysis = analyze_products(current_products, CURRENT_CONFIG)
        print_results(CURRENT_CONFIG, current_analysis)

        # Small delay to avoid rate limiting
        await asyncio.sleep(2)

        # Test 2: Optimized configuration
        print("\n" + "="*80)
        print("TEST 2: OPTIMIZED SMART VELOCITY PARAMETERS")
        print("="*80)

        optimized_asins = await query_product_finder(client, OPTIMIZED_CONFIG)
        optimized_products = await get_product_details(client, optimized_asins)
        optimized_analysis = analyze_products(optimized_products, OPTIMIZED_CONFIG)
        print_results(OPTIMIZED_CONFIG, optimized_analysis)

        # Comparison summary
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        print(f"\n{'Metric':<30} {'Current':>15} {'Optimized':>15} {'Delta':>10}")
        print("-"*70)

        current_qual = current_analysis["qualifying"]
        optimized_qual = optimized_analysis["qualifying"]

        print(f"{'Qualifying Products':<30} {current_qual:>15} {optimized_qual:>15} {optimized_qual - current_qual:>+10}")

        if current_analysis["products"] and optimized_analysis["products"]:
            curr_avg_profit = sum(p["gross_profit"] for p in current_analysis["products"]) / len(current_analysis["products"])
            opt_avg_profit = sum(p["gross_profit"] for p in optimized_analysis["products"]) / len(optimized_analysis["products"])

            curr_avg_roi = sum(p["roi_percent"] for p in current_analysis["products"]) / len(current_analysis["products"])
            opt_avg_roi = sum(p["roi_percent"] for p in optimized_analysis["products"]) / len(optimized_analysis["products"])

            print(f"{'Avg Profit':<30} ${curr_avg_profit:>13.2f} ${opt_avg_profit:>13.2f} ${opt_avg_profit - curr_avg_profit:>+9.2f}")
            print(f"{'Avg ROI':<30} {curr_avg_roi:>14.1f}% {opt_avg_roi:>14.1f}% {opt_avg_roi - curr_avg_roi:>+9.1f}%")

        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(run_comparison_test())
