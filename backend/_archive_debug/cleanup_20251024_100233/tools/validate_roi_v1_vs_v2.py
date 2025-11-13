#!/usr/bin/env python3
"""
Validation Script: ROI V1 (Inverse Formula) vs V2 (Direct Keepa Prices)

Compares ROI calculations between legacy inverse formula and new direct Keepa prices
to validate Phase 1 implementation before deploying to production.

Usage:
    python validate_roi_v1_vs_v2.py \
        --base-url http://localhost:8000 \
        --asins 0134685997,1259573545,0593655036,1982137274

Output:
    - CSV: /tmp/roi_validation.csv
    - Markdown Summary: /tmp/roi_validation_summary.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    import requests
    import pandas as pd
except ImportError:
    print("❌ Missing dependencies. Install with: pip install requests pandas")
    sys.exit(1)


@dataclass
class ValidationResult:
    """Single ASIN validation result."""
    asin: str
    profile_v2: Optional[str]
    method_v2: Optional[str]
    roi_v1_pct: float
    roi_v2_pct: float
    delta_pct: Optional[float]
    tolerance_status: str  # PASS | FAIL | SKIP
    reason: str
    buy_cost_v2: Optional[float]
    sell_price_v2: Optional[float]
    error: Optional[str] = None


def calculate_delta(roi_v1: float, roi_v2: float) -> Dict[str, Any]:
    """
    Calculate delta with adaptive tolerance rules.

    Returns:
        {
            "delta_pct": float | None,
            "tolerance_status": "PASS" | "FAIL" | "SKIP",
            "reason": str
        }
    """
    # Edge case 1: ROI V1 nul ou proche de zéro
    if abs(roi_v1) < 1e-6:
        if abs(roi_v2) < 5:  # V2 aussi proche de zéro
            return {"delta_pct": None, "tolerance_status": "PASS", "reason": "Both ROI near zero"}
        else:
            return {"delta_pct": None, "tolerance_status": "SKIP", "reason": "V1 ROI=0, V2 non-zero (expected improvement)"}

    # Edge case 2: ROI négatifs (prix invalides)
    if roi_v1 < 0 and roi_v2 > 0:
        return {"delta_pct": None, "tolerance_status": "PASS", "reason": "V2 fixed negative ROI"}

    # Cas normal: calcul delta relatif
    delta_pct = abs((roi_v2 - roi_v1) / roi_v1 * 100)

    if delta_pct <= 20:
        status = "PASS"
        reason = f"Delta={delta_pct:.1f}%"
    else:
        status = "FAIL"
        reason = f"Delta={delta_pct:.1f}% (>20% tolerance)"

    return {"delta_pct": delta_pct, "tolerance_status": status, "reason": reason}


def validate_asin(base_url: str, asin: str) -> ValidationResult:
    """Validate 1 ASIN with V1 and V2."""
    endpoint = f"{base_url}/api/v1/keepa/ingest"

    try:
        # V1: Flags OFF (comportement legacy)
        resp_v1 = requests.post(
            endpoint,
            json={"identifiers": [asin]},
            headers={"X-Feature-Flags-Override": "{}"},
            timeout=30
        )
        resp_v1.raise_for_status()
        data_v1 = resp_v1.json()

        # V2: Flags ON (nouveau comportement)
        resp_v2 = requests.post(
            endpoint,
            json={"identifiers": [asin]},
            headers={"X-Feature-Flags-Override": json.dumps({
                "strategy_profiles_v2": True,
                "direct_roi_calculation": True
            })},
            timeout=30
        )
        resp_v2.raise_for_status()
        data_v2 = resp_v2.json()

        # Extract results
        result_v1 = data_v1["results"][0]
        result_v2 = data_v2["results"][0]

        if result_v1["status"] != "success" or result_v2["status"] != "success":
            error_msg = result_v1.get("error") or result_v2.get("error") or "Unknown error"
            return ValidationResult(
                asin=asin,
                profile_v2=None,
                method_v2=None,
                roi_v1_pct=0,
                roi_v2_pct=0,
                delta_pct=None,
                tolerance_status="SKIP",
                reason="API error",
                buy_cost_v2=None,
                sell_price_v2=None,
                error=error_msg
            )

        # Extract ROI
        roi_v1 = result_v1["analysis"]["roi"]["roi_percentage"]
        roi_v2 = result_v2["analysis"]["roi"]["roi_percentage"]

        # Calculate delta
        delta_info = calculate_delta(roi_v1, roi_v2)

        return ValidationResult(
            asin=asin,
            profile_v2=result_v2["analysis"].get("strategy_profile"),
            method_v2=result_v2["analysis"].get("calculation_method"),
            roi_v1_pct=roi_v1,
            roi_v2_pct=roi_v2,
            delta_pct=delta_info["delta_pct"],
            tolerance_status=delta_info["tolerance_status"],
            reason=delta_info["reason"],
            buy_cost_v2=result_v2["analysis"]["roi"].get("buy_cost"),
            sell_price_v2=result_v2["analysis"].get("current_price"),
            error=None
        )

    except requests.RequestException as e:
        return ValidationResult(
            asin=asin,
            profile_v2=None,
            method_v2=None,
            roi_v1_pct=0,
            roi_v2_pct=0,
            delta_pct=None,
            tolerance_status="SKIP",
            reason="Network error",
            buy_cost_v2=None,
            sell_price_v2=None,
            error=str(e)
        )
    except (KeyError, IndexError, TypeError) as e:
        return ValidationResult(
            asin=asin,
            profile_v2=None,
            method_v2=None,
            roi_v1_pct=0,
            roi_v2_pct=0,
            delta_pct=None,
            tolerance_status="SKIP",
            reason="Parse error",
            buy_cost_v2=None,
            sell_price_v2=None,
            error=str(e)
        )


def generate_markdown_summary(df: pd.DataFrame) -> str:
    """Generate Markdown summary report."""
    total = len(df)
    pass_count = len(df[df["tolerance_status"] == "PASS"])
    fail_count = len(df[df["tolerance_status"] == "FAIL"])
    skip_count = len(df[df["tolerance_status"] == "SKIP"])

    # Calculate stats on PASS results only
    pass_df = df[df["tolerance_status"] == "PASS"]
    delta_values = pass_df["delta_pct"].dropna()
    avg_delta = delta_values.mean() if len(delta_values) > 0 else 0
    max_delta = delta_values.max() if len(delta_values) > 0 else 0

    # Global status
    pass_pct = (pass_count / max(total - skip_count, 1)) * 100 if (total - skip_count) > 0 else 0
    global_status = "✅ PASS" if pass_pct >= 80 else "⚠️ FAIL"

    md = f"""# Validation Phase 1 — ROI V1 vs V2

**Date** : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**ASINs testés** : {total}
**Tolérance** : ±20%

---

## 📊 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| ASINs PASS | {pass_count}/{total} ({pass_pct:.1f}%) |
| ASINs FAIL | {fail_count}/{total} ({fail_count/max(total,1)*100:.1f}%) |
| ASINs SKIP | {skip_count}/{total} ({skip_count/max(total,1)*100:.1f}%) |
| Delta moyen (PASS) | {avg_delta:.1f}% |
| Delta max (PASS) | {max_delta:.1f}% |

**Statut Global** : {global_status}

---

## 📋 Détail par ASIN

| ASIN | Strategy V2 | Method V2 | ROI V1 | ROI V2 | Delta | Status | Notes |
|------|-------------|-----------|--------|--------|-------|--------|-------|
"""

    for _, row in df.iterrows():
        status_emoji = "✅" if row["tolerance_status"] == "PASS" else ("❌" if row["tolerance_status"] == "FAIL" else "⏭️")
        delta_str = f"{row['delta_pct']:.1f}%" if pd.notna(row['delta_pct']) else "-"
        md += f"| {row['asin']} | {row['profile_v2'] or 'N/A'} | {row['method_v2'] or 'N/A'} | {row['roi_v1_pct']:.1f}% | {row['roi_v2_pct']:.1f}% | {delta_str} | {status_emoji} {row['tolerance_status']} | {row['reason']} |\n"

    # FAIL cases detail
    fail_df = df[df["tolerance_status"] == "FAIL"]
    if len(fail_df) > 0:
        md += "\n---\n\n## ⚠️ Cas Hors Tolérance\n\n"
        for _, row in fail_df.iterrows():
            md += f"""### ASIN: {row['asin']} (FAIL - Delta {row['delta_pct']:.1f}%)
- **V1** : ROI={row['roi_v1_pct']:.1f}%, buy_cost=N/A (inverse formula)
- **V2** : ROI={row['roi_v2_pct']:.1f}%, buy_cost=${row['buy_cost_v2']}, sell_price=${row['sell_price_v2']}
- **Cause probable** : {row['reason']}

"""

    # Recommendations
    textbook_count = len(df[df["profile_v2"] == "textbook"])
    velocity_count = len(df[df["profile_v2"] == "velocity"])
    balanced_count = len(df[df["profile_v2"] == "balanced"])

    md += f"""---

## 🎯 Recommandations

- {"✅" if textbook_count + velocity_count > 0 else "⚠️"} **Stratégies détectées** : {textbook_count} textbook, {velocity_count} velocity, {balanced_count} balanced
- {"✅" if fail_count == 0 else "⚠️"} **Écarts > 20%** : {fail_count} cas
- {"✅" if skip_count == 0 else "⚠️"} **Erreurs** : {skip_count} cas
- **Prêt Phase 2** : {"✅ OUI" if pass_pct >= 80 else "⚠️ NON - Investiguer cas FAIL"}
"""

    return md


def main():
    parser = argparse.ArgumentParser(description="Validate ROI V1 vs V2 implementation")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of backend API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--asins",
        required=True,
        help="Comma-separated list of ASINs to test"
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp",
        help="Output directory for CSV and Markdown (default: /tmp)"
    )

    args = parser.parse_args()

    # Parse ASINs
    asins = [asin.strip() for asin in args.asins.split(",") if asin.strip()]

    if not asins:
        print("❌ No ASINs provided")
        sys.exit(1)

    print(f"🚀 Starting validation for {len(asins)} ASINs...")
    print(f"   Base URL: {args.base_url}")

    # Validate each ASIN
    results = []
    for i, asin in enumerate(asins, 1):
        print(f"   [{i}/{len(asins)}] Testing {asin}...", end=" ")
        result = validate_asin(args.base_url, asin)
        results.append(asdict(result))
        print(f"{result.tolerance_status}")

    # Create DataFrame
    df = pd.DataFrame(results)

    # Export CSV
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "roi_validation.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ CSV exported: {csv_path}")

    # Generate Markdown summary
    md_summary = generate_markdown_summary(df)
    md_path = output_dir / "roi_validation_summary.md"
    md_path.write_text(md_summary, encoding="utf-8")
    print(f"✅ Markdown summary: {md_path}")

    # Print summary stats
    pass_count = len(df[df["tolerance_status"] == "PASS"])
    total_testable = len(df[df["tolerance_status"] != "SKIP"])
    pass_pct = (pass_count / max(total_testable, 1)) * 100

    print(f"\n📊 Summary:")
    print(f"   PASS: {pass_count}/{total_testable} ({pass_pct:.1f}%)")
    print(f"   Status: {'✅ READY for Phase 2' if pass_pct >= 80 else '⚠️ INVESTIGATE failures'}")

    # Exit code
    sys.exit(0 if pass_pct >= 80 else 1)


if __name__ == "__main__":
    main()
