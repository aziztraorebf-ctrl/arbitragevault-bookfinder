"""
Test Script: Real Rotation Analysis from Keepa Data
Analyze actual sales velocity using Keepa salesDrops data.

This script fetches real products and analyzes their sales patterns
to determine realistic rotation expectations for textbook strategies.
"""

import asyncio
import os
import sys
import statistics
import httpx
from dataclasses import dataclass
from typing import List, Optional
from collections import defaultdict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ProductRotation:
    """Product with rotation data."""
    asin: str
    title: str
    bsr: int
    current_price: float
    sales_drops_30: int  # Estimated sales in last 30 days
    sales_drops_90: int  # Estimated sales in last 90 days
    days_to_sell: float  # Estimated days to sell 1 unit
    monthly_velocity: float  # Sales per month


# BSR ranges to test
BSR_RANGES = {
    "textbooks_standard_lower": (100000, 150000),
    "textbooks_standard_middle": (150000, 200000),
    "textbooks_standard_upper": (200000, 250000),
    "textbooks_patience_lower": (250000, 300000),
    "textbooks_patience_middle": (300000, 350000),
    "textbooks_patience_upper": (350000, 400000),
}


class RotationAnalyzer:
    """Analyze real rotation data from Keepa."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        await self.client.aclose()

    async def fetch_products_for_range(
        self,
        bsr_min: int,
        bsr_max: int,
        category: int = 283155,
        max_products: int = 20,
    ) -> List[dict]:
        """Fetch products in BSR range from Keepa."""
        import json

        # First get ASINs from Product Finder
        url = "https://api.keepa.com/query"
        selection = {
            "rootCategory": category,
            "current_SALES_gte": bsr_min,
            "current_SALES_lte": bsr_max,
            "current_AMAZON_gte": 1500,  # $15+
            "current_AMAZON_lte": 10000,  # $100
            "productType": [0],
            "hasReviews": True,
        }

        params = {
            "key": self.api_key,
            "domain": 1,
            "selection": json.dumps(selection),
            "perPage": max_products,
            "page": 0,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            asins = data.get("asinList", [])

            if not asins:
                return []

            # Fetch product details with stats
            return await self._fetch_product_details(asins[:max_products])

        except Exception as e:
            print(f"  ERROR: {e}")
            return []

    async def _fetch_product_details(self, asins: List[str]) -> List[dict]:
        """Fetch product details including sales drops."""
        if not asins:
            return []

        url = "https://api.keepa.com/product"
        params = {
            "key": self.api_key,
            "domain": 1,
            "asin": ",".join(asins),
            "stats": 90,  # 90-day stats for salesDrops
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])

        except Exception as e:
            print(f"  ERROR fetching details: {e}")
            return []

    def parse_rotation_data(self, products: List[dict]) -> List[ProductRotation]:
        """Parse products into rotation analysis objects."""
        results = []

        for p in products:
            try:
                asin = p.get("asin", "")
                title = (p.get("title") or "")[:40]

                stats = p.get("stats", {})
                current = stats.get("current", [])

                # Get BSR (index 3)
                bsr = current[3] if len(current) > 3 and current[3] else None
                if not bsr or bsr <= 0:
                    continue

                # Get price (index 0)
                price_raw = current[0] if len(current) > 0 and current[0] else None
                if not price_raw or price_raw <= 0:
                    continue
                current_price = price_raw / 100.0

                # Get sales drops - KEY DATA for rotation
                # salesDrops30 = estimated sales in last 30 days
                # salesDrops90 = estimated sales in last 90 days
                sales_drops_30 = 0
                sales_drops_90 = 0

                # Check different possible locations for sales drops
                # In stats.current array, index 32 = salesDrops30, index 33 = salesDrops90
                if len(current) > 32 and current[32] is not None:
                    sales_drops_30 = current[32]
                if len(current) > 33 and current[33] is not None:
                    sales_drops_90 = current[33]

                # Also check top-level stats
                if sales_drops_30 == 0:
                    sales_drops_30 = stats.get("salesDrops30", 0) or 0
                if sales_drops_90 == 0:
                    sales_drops_90 = stats.get("salesDrops90", 0) or 0

                # Calculate rotation metrics
                if sales_drops_30 > 0:
                    days_to_sell = 30.0 / sales_drops_30
                    monthly_velocity = sales_drops_30
                elif sales_drops_90 > 0:
                    days_to_sell = 90.0 / sales_drops_90
                    monthly_velocity = sales_drops_90 / 3.0
                else:
                    # Estimate from BSR if no drops data
                    # Rule of thumb: BSR 100K ~ 1/day, BSR 1M ~ 1/month
                    estimated_daily = max(0.1, 100000 / bsr)
                    days_to_sell = 1.0 / estimated_daily
                    monthly_velocity = estimated_daily * 30

                results.append(ProductRotation(
                    asin=asin,
                    title=title,
                    bsr=bsr,
                    current_price=current_price,
                    sales_drops_30=sales_drops_30,
                    sales_drops_90=sales_drops_90,
                    days_to_sell=round(days_to_sell, 1),
                    monthly_velocity=round(monthly_velocity, 1),
                ))

            except Exception as e:
                continue

        return results

    async def analyze_range(
        self, range_name: str, bsr_min: int, bsr_max: int
    ) -> dict:
        """Analyze rotation for a BSR range."""
        print(f"\n  Fetching products for {range_name} (BSR {bsr_min:,}-{bsr_max:,})...")

        raw_products = await self.fetch_products_for_range(bsr_min, bsr_max)
        products = self.parse_rotation_data(raw_products)

        if not products:
            return {"error": "No products found", "range": range_name}

        # Calculate statistics
        days_to_sell_values = [p.days_to_sell for p in products]
        monthly_velocity_values = [p.monthly_velocity for p in products]
        bsr_values = [p.bsr for p in products]
        drops_30_values = [p.sales_drops_30 for p in products]

        result = {
            "range": range_name,
            "bsr_min": bsr_min,
            "bsr_max": bsr_max,
            "product_count": len(products),
            "bsr": {
                "min": min(bsr_values),
                "max": max(bsr_values),
                "mean": round(statistics.mean(bsr_values)),
            },
            "sales_drops_30": {
                "min": min(drops_30_values),
                "max": max(drops_30_values),
                "mean": round(statistics.mean(drops_30_values), 1),
                "median": round(statistics.median(drops_30_values), 1),
            },
            "days_to_sell": {
                "min": round(min(days_to_sell_values), 1),
                "max": round(max(days_to_sell_values), 1),
                "mean": round(statistics.mean(days_to_sell_values), 1),
                "median": round(statistics.median(days_to_sell_values), 1),
            },
            "monthly_velocity": {
                "min": round(min(monthly_velocity_values), 1),
                "max": round(max(monthly_velocity_values), 1),
                "mean": round(statistics.mean(monthly_velocity_values), 1),
                "median": round(statistics.median(monthly_velocity_values), 1),
            },
            "sample_products": [
                {
                    "asin": p.asin,
                    "bsr": p.bsr,
                    "drops_30": p.sales_drops_30,
                    "days_to_sell": p.days_to_sell,
                }
                for p in sorted(products, key=lambda x: x.bsr)[:5]
            ],
        }

        # Print summary
        print(f"    Products analyzed: {len(products)}")
        print(f"    BSR range found: {result['bsr']['min']:,} - {result['bsr']['max']:,}")
        print(f"    Sales drops (30d): mean={result['sales_drops_30']['mean']}, median={result['sales_drops_30']['median']}")
        print(f"    Days to sell 1 unit: mean={result['days_to_sell']['mean']}, median={result['days_to_sell']['median']}")
        print(f"    Monthly velocity: mean={result['monthly_velocity']['mean']}, median={result['monthly_velocity']['median']}")

        return result


def generate_rotation_summary(results: dict) -> str:
    """Generate summary report."""
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("REAL ROTATION ANALYSIS - KEEPA SALES DROPS DATA")
    lines.append("=" * 80)
    lines.append("\nThis analysis uses Keepa's salesDrops data which tracks actual BSR drops")
    lines.append("(each drop = 1 estimated sale) to determine real rotation times.\n")

    # Group by strategy
    strategies = {
        "TEXTBOOKS_STANDARD (BSR 100K-250K)": [
            "textbooks_standard_lower",
            "textbooks_standard_middle",
            "textbooks_standard_upper",
        ],
        "TEXTBOOKS_PATIENCE (BSR 250K-400K)": [
            "textbooks_patience_lower",
            "textbooks_patience_middle",
            "textbooks_patience_upper",
        ],
    }

    for strategy_name, range_names in strategies.items():
        lines.append(f"\n{'='*60}")
        lines.append(f"STRATEGY: {strategy_name}")
        lines.append("=" * 60)

        strategy_days = []
        strategy_monthly = []

        for range_name in range_names:
            r = results.get(range_name, {})
            if "error" in r:
                lines.append(f"\n  {range_name}: No data")
                continue

            lines.append(f"\n  {range_name.upper()}")
            lines.append(f"    BSR Range: {r['bsr_min']:,} - {r['bsr_max']:,}")
            lines.append(f"    Products: {r['product_count']}")
            lines.append(f"    Sales/month (median): {r['monthly_velocity']['median']}")
            lines.append(f"    Days to sell (median): {r['days_to_sell']['median']}")

            strategy_days.append(r['days_to_sell']['median'])
            strategy_monthly.append(r['monthly_velocity']['median'])

        if strategy_days:
            avg_days = statistics.mean(strategy_days)
            avg_monthly = statistics.mean(strategy_monthly)

            lines.append(f"\n  --- STRATEGY SUMMARY ---")
            lines.append(f"  Average days to sell 1 unit: {avg_days:.1f} days")
            lines.append(f"  Average monthly velocity: {avg_monthly:.1f} sales/month")

            # Rotation interpretation
            if avg_days <= 7:
                rotation_label = "FAST (< 1 week)"
            elif avg_days <= 14:
                rotation_label = "MODERATE-FAST (1-2 weeks)"
            elif avg_days <= 30:
                rotation_label = "MODERATE (2-4 weeks)"
            elif avg_days <= 60:
                rotation_label = "SLOW (1-2 months)"
            else:
                rotation_label = "VERY SLOW (2+ months)"

            lines.append(f"  Rotation category: {rotation_label}")

    # Conclusion
    lines.append(f"\n{'='*80}")
    lines.append("CONCLUSION - RECOMMENDED LABELS")
    lines.append("=" * 80)

    std_result = results.get("textbooks_standard_middle", {})
    pat_result = results.get("textbooks_patience_middle", {})

    if std_result and not std_result.get("error"):
        std_days = std_result.get("days_to_sell", {}).get("median", "N/A")
        lines.append(f"\nTextbook Standard (BSR 100K-250K):")
        lines.append(f"  Median days to sell: {std_days}")
        if isinstance(std_days, (int, float)):
            if std_days <= 14:
                lines.append(f"  Recommended label: 'Rotation 1-2 semaines'")
            elif std_days <= 30:
                lines.append(f"  Recommended label: 'Rotation 2-4 semaines'")
            else:
                lines.append(f"  Recommended label: 'Rotation 4-6 semaines'")

    if pat_result and not pat_result.get("error"):
        pat_days = pat_result.get("days_to_sell", {}).get("median", "N/A")
        lines.append(f"\nTextbook Patience (BSR 250K-400K):")
        lines.append(f"  Median days to sell: {pat_days}")
        if isinstance(pat_days, (int, float)):
            if pat_days <= 30:
                lines.append(f"  Recommended label: 'Rotation 2-4 semaines'")
            elif pat_days <= 60:
                lines.append(f"  Recommended label: 'Rotation 4-8 semaines'")
            else:
                lines.append(f"  Recommended label: 'Rotation 8-12 semaines'")

    return "\n".join(lines)


async def main():
    """Run rotation analysis."""
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY environment variable required")
        sys.exit(1)

    print("=" * 80)
    print("ROTATION ANALYSIS: Real Sales Data from Keepa")
    print("=" * 80)
    print("\nCategory: 283155 (Books > Education & Teaching)")
    print("Using Keepa salesDrops data to measure actual sales velocity")

    analyzer = RotationAnalyzer(api_key)
    results = {}

    try:
        for range_name, (bsr_min, bsr_max) in BSR_RANGES.items():
            results[range_name] = await analyzer.analyze_range(range_name, bsr_min, bsr_max)
            await asyncio.sleep(1)  # Rate limiting

        # Generate summary
        summary = generate_rotation_summary(results)
        print(summary)

        # Save results
        output_path = os.path.join(
            os.path.dirname(__file__), "rotation_analysis_results.txt"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"\nResults saved to: {output_path}")

    finally:
        await analyzer.close()

    return results


if __name__ == "__main__":
    asyncio.run(main())
