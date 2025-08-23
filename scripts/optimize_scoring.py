#!/usr/bin/env python3
"""
Script for optimizing advanced scoring thresholds using real Keepa data.
"""
import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input/Output paths
ASIN_INPUT_FILE = "scripts/input_asins.json"
CACHE_DIR = "scripts/cache"
REPORT_DIR = "reports/scoring_opt"

# Keepa API settings
KEEPA_REQUEST_DELAY_SECONDS = 1.0  # Respect API rate limits

# Grid search parameters
GRID_SEARCH_PARAMS = {
    "roi_min": [25, 30, 35],
    "velocity_min": [50, 60, 70, 80],
    "stability_min": [50, 60, 70, 80],
    "confidence_min": [60, 70, 80]
}

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def get_cache_key(asin: str, config_hash: str, window_days: int) -> str:
    """Generate a unique cache key."""
    return f"{asin}_{config_hash}_{window_days}.json"

def load_from_cache(cache_key: str) -> Any:
    """Load data from local JSON cache."""
    cache_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

def save_to_cache(cache_key: str, data: Any):
    """Save data to local JSON cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_key)
    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)

# ============================================================================
# DATA FETCHING & ANALYSIS
# ============================================================================

# Add sys.path to import from backend
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from app.services.keepa_service import KeepaService
from app.services.business_config_service import BusinessConfigService
from app.services.keepa_parser import parse_keepa_product
from app.core.calculations import (
    calculate_roi_metrics,
    compute_advanced_velocity_score,
    compute_advanced_stability_score,
    compute_advanced_confidence_score,
    compute_overall_rating
)
from decimal import Decimal

async def fetch_and_analyze_asins(asins: List[str], use_cache: bool, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch Keepa data and run advanced scoring analysis for a list of ASINs.
    """
    print(f"Fetching and analyzing {len(asins)} ASINs...")
    
    results = []
    keepa_service = KeepaService()
    config_hash = str(hash(str(sorted(config.items()))))
    
    async with keepa_service:
        for asin in asins:
            try:
                # Cache handling
                cache_key = get_cache_key(asin, config_hash, 30)
                if use_cache:
                    cached_data = load_from_cache(cache_key)
                    if cached_data:
                        results.append(cached_data)
                        print(f"  - {asin}: CACHE HIT")
                        continue
                
                print(f"  - {asin}: API CALL")
                
                # Fetch Keepa data
                keepa_data = await keepa_service.get_product_data(asin)
                if not keepa_data:
                    continue
                
                # Parse data
                parsed_data = parse_keepa_product(keepa_data)
                
                # Calculate scores
                roi_result = calculate_roi_metrics(
                    current_price=Decimal(str(parsed_data.get('current_price', 0))),
                    estimated_buy_cost=Decimal(str(parsed_data.get('current_price', 0) * 0.75)),
                    config=config
                )
                
                _, velocity_score, _, _ = compute_advanced_velocity_score(parsed_data.get('bsr_history', []), config)
                _, stability_score, _, _ = compute_advanced_stability_score(parsed_data.get('price_history', []), config)
                _, confidence_score, _, _ = compute_advanced_confidence_score(
                    parsed_data.get('price_history', []),
                    parsed_data.get('bsr_history', []),
                    1, config
                )
                
                overall_rating = compute_overall_rating(
                    roi_result.get('roi_percentage', 0),
                    velocity_score,
                    stability_score,
                    confidence_score,
                    config
                )
                
                result = {
                    "asin": asin,
                    "roi_percentage": roi_result.get('roi_percentage', 0),
                    "velocity_score": velocity_score,
                    "price_stability_score": stability_score,
                    "confidence_score": confidence_score,
                    "overall_rating": overall_rating
                }
                
                results.append(result)
                save_to_cache(cache_key, result)
                
                await asyncio.sleep(KEEPA_REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                print(f"  - {asin}: ERROR - {e}")
    
    return results

# ============================================================================
# REPORTING & VISUALIZATION
# ============================================================================

def generate_reports(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """
    Generate reports and visualizations from analysis results.
    """
    os.makedirs(REPORT_DIR, exist_ok=True)
    df = pd.DataFrame(results)
    
    # 1. Distributions report
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    sns.histplot(df['velocity_score'], bins=20, kde=True, ax=axes[0]).set_title('Velocity Score Distribution')
    sns.histplot(df['price_stability_score'], bins=20, kde=True, ax=axes[1]).set_title('Stability Score Distribution')
    sns.histplot(df['confidence_score'], bins=20, kde=True, ax=axes[2]).set_title('Confidence Score Distribution')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, "distributions.png"))
    print(f"✅ Saved distributions report to {REPORT_DIR}/distributions.png")
    
    # 2. Ratings vs ROI report
    ratings_vs_roi = df.groupby('overall_rating')['roi_percentage'].agg(['mean', 'median', 'std', 'count']).reset_index()
    ratings_vs_roi.to_csv(os.path.join(REPORT_DIR, "ratings_vs_roi.csv"), index=False)
    print(f"✅ Saved ratings vs ROI report to {REPORT_DIR}/ratings_vs_roi.csv")
    
    # 3. Grid search report
    grid_search_results = run_grid_search(df, config)
    grid_search_results.to_csv(os.path.join(REPORT_DIR, "grid_search.csv"), index=False)
    print(f"✅ Saved grid search report to {REPORT_DIR}/grid_search.csv")

# ============================================================================
# GRID SEARCH
# ============================================================================

def run_grid_search(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Run grid search to find optimal thresholds.
    """
    print("\n🔍 Running grid search for optimal thresholds...")
    
    search_results = []
    
    from itertools import product
    
    # Create all combinations of thresholds
    param_combinations = list(product(
        GRID_SEARCH_PARAMS["roi_min"],
        GRID_SEARCH_PARAMS["velocity_min"],
        GRID_SEARCH_PARAMS["stability_min"],
        GRID_SEARCH_PARAMS["confidence_min"]
    ))
    
    for roi_min, velocity_min, stability_min, confidence_min in param_combinations:
        
        # Create a temporary config for this iteration
        temp_config = config.copy()
        temp_config["overall_rating"]["gating_rules"]["EXCELLENT"] = {
            "roi_min": roi_min,
            "velocity_min": velocity_min,
            "stability_min": stability_min,
            "confidence_min": confidence_min
        }
        
        # Recalculate ratings with new thresholds
        df['temp_rating'] = df.apply(
            lambda row: compute_overall_rating(
                row['roi_percentage'],
                row['velocity_score'],
                row['price_stability_score'],
                row['confidence_score'],
                temp_config
            ),
            axis=1
        )
        
        # Evaluate this set of thresholds
        excellent_df = df[df['temp_rating'] == 'EXCELLENT']
        excellent_pct = (len(excellent_df) / len(df)) * 100 if len(df) > 0 else 0
        excellent_roi_median = excellent_df['roi_percentage'].median() if not excellent_df.empty else 0
        
        search_results.append({
            "roi_min": roi_min,
            "velocity_min": velocity_min,
            "stability_min": stability_min,
            "confidence_min": confidence_min,
            "excellent_pct": round(excellent_pct, 2),
            "excellent_roi_median": round(excellent_roi_median, 2)
        })
        
    return pd.DataFrame(search_results)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main(use_cache: bool = True):
    """
    Main function to run the optimization script.
    """
    print("🚀 Starting Advanced Scoring Optimization Script\n")
    
    # 1. Load input ASINs
    if not os.path.exists(ASIN_INPUT_FILE):
        print(f"❌ Input file not found: {ASIN_INPUT_FILE}")
        print("   Please create it with a list of ASINs to test.")
        return
        
    with open(ASIN_INPUT_FILE, 'r') as f:
        input_data = json.load(f)
        asins = input_data.get("test_asins", [])
    
    if not asins:
        print("❌ No ASINs found in input file.")
        return
        
    # Load business config
    config_service = BusinessConfigService()
    config = await config_service.get_effective_config(domain_id=1, category='books')
        
    # 2. Fetch and analyze data
    analysis_results = await fetch_and_analyze_asins(asins, use_cache, config)
    
    # 3. Generate reports
    if analysis_results:
        generate_reports(analysis_results, config)
    
    print("\n🎉 Optimization script finished!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Optimize advanced scoring thresholds.")
    parser.add_argument("--no-cache", action="store_false", dest="use_cache", help="Disable cache and force Keepa API calls")
    args = parser.parse_args()
    
    asyncio.run(main(use_cache=args.use_cache))