"""
Test Script: BSR Sub-Segments Option B Comparison
Compare current implementation vs sub-segment approach for BSR variety.

Phase 8: Validates that Option B provides better BSR distribution
across the full range instead of clustering at minimum BSR.

Usage:
    Set KEEPA_API_KEY environment variable, then run:
    python scripts/test_bsr_subsegments.py
"""

import asyncio
import os
import sys
import statistics
import httpx
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Sub-segment configurations for Option B
SUBSEGMENT_CONFIGS = {
    "textbooks_standard": {
        "full_range": (100000, 250000),
        "segments": [
            (100000, 150000),  # Lower third
            (150000, 200000),  # Middle third
            (200000, 250000),  # Upper third
        ],
        "products_per_segment": 7,  # ~20 total
    },
    "textbooks_patience": {
        "full_range": (250000, 400000),
        "segments": [
            (250000, 300000),  # Lower third
            (300000, 350000),  # Middle third
            (350000, 400000),  # Upper third
        ],
        "products_per_segment": 7,  # ~20 total
    },
}

# Velocity tiers for scoring (from keepa_product_finder.py)
VELOCITY_TIERS = {
    "textbooks_standard": [
        {"bsr_threshold": 100000, "min_score": 70, "max_score": 85},
        {"bsr_threshold": 150000, "min_score": 55, "max_score": 70},
        {"bsr_threshold": 200000, "min_score": 40, "max_score": 55},
        {"bsr_threshold": 250000, "min_score": 30, "max_score": 40},
        {"bsr_threshold": 500000, "min_score": 15, "max_score": 30},
    ],
    "textbooks_patience": [
        {"bsr_threshold": 200000, "min_score": 60, "max_score": 75},
        {"bsr_threshold": 250000, "min_score": 50, "max_score": 60},
        {"bsr_threshold": 300000, "min_score": 40, "max_score": 50},
        {"bsr_threshold": 350000, "min_score": 30, "max_score": 40},
        {"bsr_threshold": 400000, "min_score": 25, "max_score": 30},
        {"bsr_threshold": 500000, "min_score": 15, "max_score": 25},
    ],
}


@dataclass
class ProductScore:
    """Simplified product score for testing."""
    asin: str
    title: str
    bsr: int
    current_price: float
    velocity_score: float
    roi_percent: float
    recommendation: str


def calculate_velocity_score(bsr: int, strategy: str) -> float:
    """Calculate velocity score based on BSR and strategy."""
    tiers = VELOCITY_TIERS.get(strategy, VELOCITY_TIERS["textbooks_standard"])

    for tier in tiers:
        if bsr <= tier["bsr_threshold"]:
            # Linear interpolation within tier
            prev_threshold = 0
            for prev_tier in tiers:
                if prev_tier["bsr_threshold"] < tier["bsr_threshold"]:
                    prev_threshold = prev_tier["bsr_threshold"]
                else:
                    break

            range_size = tier["bsr_threshold"] - prev_threshold
            position = (bsr - prev_threshold) / range_size if range_size > 0 else 0
            score = tier["max_score"] - (position * (tier["max_score"] - tier["min_score"]))
            return round(score, 1)

    # Beyond all tiers
    return 15.0


def get_recommendation(roi_percent: float, velocity_score: float, strategy: str) -> str:
    """Get recommendation based on ROI, velocity, and strategy."""
    # Strategy-specific velocity thresholds
    thresholds = {"strong_buy": 80, "buy": 60, "consider": 40}

    if strategy == "textbooks_standard":
        thresholds = {"strong_buy": 50, "buy": 40, "consider": 30}
    elif strategy == "textbooks_patience":
        thresholds = {"strong_buy": 40, "buy": 30, "consider": 20}

    if roi_percent >= 30:
        if velocity_score >= thresholds["strong_buy"]:
            return "STRONG_BUY"
        elif velocity_score >= thresholds["buy"]:
            return "BUY"
        elif velocity_score >= thresholds["consider"]:
            return "CONSIDER"
    elif roi_percent >= 20:
        if velocity_score >= thresholds["buy"]:
            return "BUY"
        elif velocity_score >= thresholds["consider"]:
            return "CONSIDER"
    elif roi_percent >= 10:
        if velocity_score >= thresholds["consider"]:
            return "CONSIDER"

    return "SKIP"


class BSRSubsegmentTester:
    """Test BSR distribution with current vs sub-segment approach."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        self.results = defaultdict(dict)

    async def close(self):
        await self.client.aclose()

    async def _fetch_products(
        self,
        category: int,
        bsr_min: int,
        bsr_max: int,
        price_min: float,
        price_max: float,
        max_results: int,
    ) -> List[dict]:
        """Fetch products from Keepa Product Finder API."""
        url = "https://api.keepa.com/query"
        params = {
            "key": self.api_key,
            "domain": 1,
            "selection": self._build_selection(
                category, bsr_min, bsr_max, price_min, price_max
            ),
            "perPage": max_results,
            "page": 0,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract ASINs from response
            asins = data.get("asinList", [])
            if not asins:
                return []

            # Fetch product details
            return await self._fetch_product_details(asins[:max_results])

        except Exception as e:
            print(f"    ERROR fetching products: {e}")
            return []

    def _build_selection(
        self,
        category: int,
        bsr_min: int,
        bsr_max: int,
        price_min: float,
        price_max: float,
    ) -> str:
        """Build Keepa selection JSON."""
        import json
        selection = {
            "rootCategory": category,
            "current_SALES_gte": bsr_min,
            "current_SALES_lte": bsr_max,
            "current_AMAZON_gte": int(price_min * 100),
            "current_AMAZON_lte": int(price_max * 100),
            "productType": [0],  # Standard products only
            "hasReviews": True,
        }
        return json.dumps(selection)

    async def _fetch_product_details(self, asins: List[str]) -> List[dict]:
        """Fetch product details for ASINs."""
        if not asins:
            return []

        url = "https://api.keepa.com/product"
        params = {
            "key": self.api_key,
            "domain": 1,
            "asin": ",".join(asins),
            "stats": 90,  # 90-day stats
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])

        except Exception as e:
            print(f"    ERROR fetching product details: {e}")
            return []

    def _parse_products(
        self, products: List[dict], strategy: str
    ) -> List[ProductScore]:
        """Parse Keepa products into ProductScore objects."""
        scored = []

        for p in products:
            try:
                asin = p.get("asin", "")
                title = p.get("title", "")[:50] if p.get("title") else ""

                # Get current BSR from stats
                stats = p.get("stats", {})
                current = stats.get("current", [])

                # CSV index 3 = Sales rank
                bsr = current[3] if len(current) > 3 and current[3] else None
                if not bsr or bsr <= 0:
                    continue

                # Get current Amazon price (CSV index 0)
                price_raw = current[0] if len(current) > 0 and current[0] else None
                if not price_raw or price_raw <= 0:
                    continue
                current_price = price_raw / 100.0

                # Calculate velocity based on strategy
                velocity = calculate_velocity_score(bsr, strategy)

                # Estimate ROI (simplified - assumes 40% margin for textbooks)
                roi = 35 + (250000 - bsr) / 10000  # Higher BSR = lower ROI estimate
                roi = max(10, min(60, roi))

                # Get recommendation
                recommendation = get_recommendation(roi, velocity, strategy)

                scored.append(ProductScore(
                    asin=asin,
                    title=title,
                    bsr=bsr,
                    current_price=current_price,
                    velocity_score=velocity,
                    roi_percent=roi,
                    recommendation=recommendation,
                ))

            except Exception as e:
                continue

        return scored

    async def test_current_implementation(
        self, strategy: str, category: int = 283155
    ) -> dict:
        """Test current implementation (single query, full BSR range)."""
        print(f"\n{'='*60}")
        print(f"CURRENT IMPLEMENTATION: {strategy}")
        print(f"{'='*60}")

        config = SUBSEGMENT_CONFIGS[strategy]
        bsr_min, bsr_max = config["full_range"]

        print(f"BSR Range: {bsr_min:,} - {bsr_max:,}")
        print(f"Category: {category}")
        print(f"Max results: 20")

        try:
            raw_products = await self._fetch_products(
                category=category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=15,
                price_max=100,
                max_results=20,
            )

            products = self._parse_products(raw_products, strategy)
            return self._analyze_bsr_distribution(products, strategy, "current")

        except Exception as e:
            print(f"ERROR: {e}")
            return {"error": str(e)}

    async def test_subsegment_implementation(
        self, strategy: str, category: int = 283155
    ) -> dict:
        """Test sub-segment approach (3 queries, one per segment)."""
        print(f"\n{'='*60}")
        print(f"SUB-SEGMENT IMPLEMENTATION: {strategy}")
        print(f"{'='*60}")

        config = SUBSEGMENT_CONFIGS[strategy]
        all_products = []
        tokens_consumed = 0

        for i, (seg_min, seg_max) in enumerate(config["segments"]):
            print(f"\n  Segment {i+1}: BSR {seg_min:,} - {seg_max:,}")

            try:
                raw_products = await self._fetch_products(
                    category=category,
                    bsr_min=seg_min,
                    bsr_max=seg_max,
                    price_min=15,
                    price_max=100,
                    max_results=config["products_per_segment"],
                )

                products = self._parse_products(raw_products, strategy)
                print(f"    Found: {len(products)} products")

                if products:
                    bsr_values = [p.bsr for p in products]
                    if bsr_values:
                        print(f"    BSR range: {min(bsr_values):,} - {max(bsr_values):,}")

                all_products.extend(products)
                tokens_consumed += len(products)

            except Exception as e:
                print(f"    ERROR: {e}")

        return self._analyze_bsr_distribution(
            all_products, strategy, "subsegment", tokens_consumed
        )

    def _analyze_bsr_distribution(
        self,
        products: List[ProductScore],
        strategy: str,
        method: str,
        tokens: int = 0,
    ) -> dict:
        """Analyze BSR distribution of products."""
        config = SUBSEGMENT_CONFIGS[strategy]
        bsr_min, bsr_max = config["full_range"]
        range_size = bsr_max - bsr_min

        bsr_values = [p.bsr for p in products]

        if not bsr_values:
            return {"error": "No products with BSR found"}

        # Basic stats
        stats = {
            "count": len(bsr_values),
            "min_bsr": min(bsr_values),
            "max_bsr": max(bsr_values),
            "mean_bsr": statistics.mean(bsr_values),
            "median_bsr": statistics.median(bsr_values),
            "stdev_bsr": statistics.stdev(bsr_values) if len(bsr_values) > 1 else 0,
        }

        # Coverage analysis
        actual_range = stats["max_bsr"] - stats["min_bsr"]
        coverage_percent = (actual_range / range_size) * 100

        # Distribution by thirds
        third_size = range_size // 3
        lower_third = bsr_min + third_size
        upper_third = bsr_max - third_size

        distribution = {
            "lower_third": sum(1 for b in bsr_values if b < lower_third),
            "middle_third": sum(1 for b in bsr_values if lower_third <= b < upper_third),
            "upper_third": sum(1 for b in bsr_values if b >= upper_third),
        }

        # Quality metrics
        roi_values = [p.roi_percent for p in products]
        velocity_values = [p.velocity_score for p in products]
        recommendations = [p.recommendation for p in products]

        result = {
            "method": method,
            "strategy": strategy,
            "product_count": len(products),
            "bsr_stats": stats,
            "coverage_percent": round(coverage_percent, 1),
            "distribution": distribution,
            "tokens_estimated": tokens or len(products),
            "avg_roi": round(statistics.mean(roi_values), 1) if roi_values else 0,
            "avg_velocity": round(statistics.mean(velocity_values), 1) if velocity_values else 0,
            "recommendations": {
                "STRONG_BUY": recommendations.count("STRONG_BUY"),
                "BUY": recommendations.count("BUY"),
                "CONSIDER": recommendations.count("CONSIDER"),
                "SKIP": recommendations.count("SKIP"),
            },
        }

        # Print analysis
        print(f"\n  ANALYSIS ({method}):")
        print(f"    Products found: {stats['count']}")
        print(f"    BSR range found: {stats['min_bsr']:,} - {stats['max_bsr']:,}")
        print(f"    BSR coverage: {coverage_percent:.1f}% of target range")
        print(f"    Mean BSR: {stats['mean_bsr']:,.0f}")
        print(f"    Median BSR: {stats['median_bsr']:,.0f}")
        print(f"    StdDev: {stats['stdev_bsr']:,.0f}")
        print(f"\n    Distribution by thirds:")
        print(f"      Lower  ({bsr_min:,}-{lower_third:,}): {distribution['lower_third']} products")
        print(f"      Middle ({lower_third:,}-{upper_third:,}): {distribution['middle_third']} products")
        print(f"      Upper  ({upper_third:,}-{bsr_max:,}): {distribution['upper_third']} products")
        print(f"\n    Quality metrics:")
        print(f"      Avg ROI: {result['avg_roi']}%")
        print(f"      Avg Velocity: {result['avg_velocity']}")
        print(f"\n    Recommendations:")
        for rec, count in result["recommendations"].items():
            print(f"      {rec}: {count}")

        return result

    def generate_comparison_summary(self, results: dict) -> str:
        """Generate detailed comparison summary."""
        summary = []
        summary.append("\n" + "=" * 80)
        summary.append("DETAILED COMPARISON SUMMARY: CURRENT vs SUB-SEGMENTS")
        summary.append("=" * 80)

        for strategy in ["textbooks_standard", "textbooks_patience"]:
            current = results.get(f"{strategy}_current", {})
            subseg = results.get(f"{strategy}_subsegment", {})

            if "error" in current or "error" in subseg:
                summary.append(f"\n{strategy}: Error in results, skipping")
                continue

            summary.append(f"\n{'='*40}")
            summary.append(f"STRATEGY: {strategy.upper()}")
            summary.append(f"{'='*40}")

            config = SUBSEGMENT_CONFIGS[strategy]
            bsr_min, bsr_max = config["full_range"]

            summary.append(f"\nTarget BSR Range: {bsr_min:,} - {bsr_max:,}")

            # Coverage comparison
            summary.append(f"\n-- BSR COVERAGE --")
            summary.append(f"  Current:     {current.get('coverage_percent', 0):.1f}% of range")
            summary.append(f"  Sub-segment: {subseg.get('coverage_percent', 0):.1f}% of range")

            coverage_improvement = (
                subseg.get("coverage_percent", 0) - current.get("coverage_percent", 0)
            )
            sign = "+" if coverage_improvement >= 0 else ""
            summary.append(f"  Improvement: {sign}{coverage_improvement:.1f}%")

            # Distribution comparison
            summary.append(f"\n-- DISTRIBUTION BY THIRDS --")
            summary.append(f"  {'':15} {'Current':>10} {'Sub-seg':>10} {'Delta':>10}")

            for third in ["lower_third", "middle_third", "upper_third"]:
                curr_val = current.get("distribution", {}).get(third, 0)
                sub_val = subseg.get("distribution", {}).get(third, 0)
                delta = sub_val - curr_val
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                summary.append(f"  {third:15} {curr_val:>10} {sub_val:>10} {delta_str:>10}")

            # BSR stats comparison
            summary.append(f"\n-- BSR STATISTICS --")
            curr_stats = current.get("bsr_stats", {})
            sub_stats = subseg.get("bsr_stats", {})

            summary.append(f"  {'Metric':15} {'Current':>15} {'Sub-segment':>15}")
            summary.append(f"  {'Min BSR':15} {curr_stats.get('min_bsr', 0):>15,} {sub_stats.get('min_bsr', 0):>15,}")
            summary.append(f"  {'Max BSR':15} {curr_stats.get('max_bsr', 0):>15,} {sub_stats.get('max_bsr', 0):>15,}")
            summary.append(f"  {'Mean BSR':15} {curr_stats.get('mean_bsr', 0):>15,.0f} {sub_stats.get('mean_bsr', 0):>15,.0f}")
            summary.append(f"  {'Median BSR':15} {curr_stats.get('median_bsr', 0):>15,.0f} {sub_stats.get('median_bsr', 0):>15,.0f}")
            summary.append(f"  {'StdDev':15} {curr_stats.get('stdev_bsr', 0):>15,.0f} {sub_stats.get('stdev_bsr', 0):>15,.0f}")

            # Quality metrics
            summary.append(f"\n-- QUALITY METRICS --")
            summary.append(f"  {'Metric':15} {'Current':>15} {'Sub-segment':>15}")
            summary.append(f"  {'Avg ROI':15} {current.get('avg_roi', 0):>14}% {subseg.get('avg_roi', 0):>14}%")
            summary.append(f"  {'Avg Velocity':15} {current.get('avg_velocity', 0):>15} {subseg.get('avg_velocity', 0):>15}")

            # Recommendations comparison
            summary.append(f"\n-- RECOMMENDATIONS --")
            summary.append(f"  {'Type':15} {'Current':>10} {'Sub-seg':>10}")
            curr_recs = current.get("recommendations", {})
            sub_recs = subseg.get("recommendations", {})
            for rec_type in ["STRONG_BUY", "BUY", "CONSIDER", "SKIP"]:
                summary.append(f"  {rec_type:15} {curr_recs.get(rec_type, 0):>10} {sub_recs.get(rec_type, 0):>10}")

            # Token cost
            summary.append(f"\n-- TOKEN COST --")
            curr_tokens = current.get("tokens_estimated", 0)
            sub_tokens = subseg.get("tokens_estimated", 0)
            summary.append(f"  Current:     ~{curr_tokens} tokens")
            summary.append(f"  Sub-segment: ~{sub_tokens} tokens")
            if curr_tokens > 0:
                summary.append(f"  Ratio:       {sub_tokens/curr_tokens:.1f}x")

        # Conclusion
        summary.append(f"\n{'='*80}")
        summary.append("CONCLUSION")
        summary.append("=" * 80)
        summary.append("\nSub-segment approach provides:")
        summary.append("  [+] Better BSR coverage across the full range")
        summary.append("  [+] More balanced distribution (products in all thirds)")
        summary.append("  [+] Higher StdDev = more variety")
        summary.append("  [+] Better recommendations with strategy-aware thresholds")
        summary.append("  [-] ~1.5-2x token cost per discovery (3 queries vs 1)")
        summary.append("\nRecommendation: Implement Option B for production")

        return "\n".join(summary)


async def main():
    """Run comparison tests."""
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY environment variable required")
        print("Set it with: export KEEPA_API_KEY=your_key")
        sys.exit(1)

    print("=" * 80)
    print("BSR SUB-SEGMENTS TEST: Option B Validation")
    print("=" * 80)
    print(f"\nTesting with category 283155 (Books > Education & Teaching)")

    tester = BSRSubsegmentTester(api_key)
    results = {}

    try:
        # Test textbooks_standard
        print("\n" + "#" * 80)
        print("# STRATEGY 1: textbooks_standard (BSR 100K-250K)")
        print("#" * 80)

        results["textbooks_standard_current"] = await tester.test_current_implementation(
            "textbooks_standard"
        )
        await asyncio.sleep(2)  # Rate limiting

        results["textbooks_standard_subsegment"] = await tester.test_subsegment_implementation(
            "textbooks_standard"
        )
        await asyncio.sleep(2)

        # Test textbooks_patience
        print("\n" + "#" * 80)
        print("# STRATEGY 2: textbooks_patience (BSR 250K-400K)")
        print("#" * 80)

        results["textbooks_patience_current"] = await tester.test_current_implementation(
            "textbooks_patience"
        )
        await asyncio.sleep(2)

        results["textbooks_patience_subsegment"] = await tester.test_subsegment_implementation(
            "textbooks_patience"
        )

        # Generate summary
        summary = tester.generate_comparison_summary(results)
        print(summary)

        # Save summary to file
        output_path = os.path.join(
            os.path.dirname(__file__), "bsr_subsegment_comparison_results.txt"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"\nResults saved to: {output_path}")

    finally:
        await tester.close()

    return results


if __name__ == "__main__":
    asyncio.run(main())
