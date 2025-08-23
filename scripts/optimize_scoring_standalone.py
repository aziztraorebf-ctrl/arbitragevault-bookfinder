#!/usr/bin/env python3
"""
Script autonome pour optimiser les seuils de scoring avancé sans dépendances DB.
"""
import asyncio
import json
import os
import time
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
import hashlib

# ============================================================================
# CONFIGURATION
# ============================================================================

# Clé API Keepa (récupérée depuis les secrets)
KEEPA_API_KEY = "rvd01p0nku3s8bsnbubeda6je1763vv5gc94jrng4eiakghlnv4bm3pmvd0sg7ru"

# Input/Output paths
ASIN_INPUT_FILE = "scripts/input_asins.json"
CACHE_DIR = "scripts/cache"
REPORT_DIR = "reports/scoring_opt"
BUSINESS_RULES_FILE = "backend/config/business_rules.json"

# Keepa API settings  
KEEPA_REQUEST_DELAY_SECONDS = 1.1  # Respect API rate limits
KEEPA_BASE_URL = "https://api.keepa.com"

# Grid search parameters
GRID_SEARCH_PARAMS = {
    "roi_min": [25, 30, 35],
    "velocity_min": [50, 60, 70, 80],
    "stability_min": [50, 60, 70, 80], 
    "confidence_min": [60, 70, 80]
}

# ============================================================================
# UTILITIES
# ============================================================================

def ensure_directories():
    """Create necessary directories."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

def load_business_rules() -> Dict[str, Any]:
    """Load business rules directly from JSON file."""
    script_dir = os.path.dirname(__file__)
    rules_path = os.path.join(script_dir, "..", BUSINESS_RULES_FILE)
    rules_path = os.path.abspath(rules_path)
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_cache_key(asin: str, config_hash: str) -> str:
    """Generate a unique cache key."""
    return f"{asin}_{config_hash}.json"

def load_from_cache(cache_key: str) -> Optional[Dict]:
    """Load data from local JSON cache."""
    cache_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                # Check if cache is still fresh (within 1 day)
                cached_time = datetime.fromisoformat(data.get('cached_at', '2020-01-01'))
                if datetime.now() - cached_time < timedelta(days=1):
                    return data
        except Exception as e:
            print(f"Cache read error for {cache_key}: {e}")
    return None

def save_to_cache(cache_key: str, data: Dict):
    """Save data to local JSON cache."""
    cache_path = os.path.join(CACHE_DIR, cache_key)
    data['cached_at'] = datetime.now().isoformat()
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Cache write error for {cache_key}: {e}")

# ============================================================================
# KEEPA API CLIENT
# ============================================================================

class SimpleKeepaClient:
    """Simple Keepa API client without database dependencies."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_product_data(self, asin: str) -> Optional[Dict]:
        """Fetch product data from Keepa API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        
        try:
            url = f"{KEEPA_BASE_URL}/product"
            params = {
                'key': self.api_key,
                'domain': 1,  # Amazon.com
                'asin': asin,
                'stats': 30,  # Last 30 days stats
                'history': 1   # Include price history
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'products' in data and data['products']:
                        return data['products'][0]
                else:
                    print(f"Keepa API error for {asin}: {response.status}")
        except Exception as e:
            print(f"Keepa API exception for {asin}: {e}")
        
        return None

# ============================================================================
# SCORING FUNCTIONS (Simplified versions without full imports)
# ============================================================================

def calculate_roi_basic(current_price: float, estimated_cost: float) -> Dict[str, float]:
    """Basic ROI calculation."""
    if not current_price or not estimated_cost or estimated_cost <= 0:
        return {"roi_percentage": 0.0, "profit_net": 0.0}
    
    # Simplified Amazon fees (30% total)
    fees = current_price * 0.30
    profit = current_price - fees - estimated_cost
    roi = (profit / estimated_cost) * 100 if estimated_cost > 0 else 0
    
    return {
        "roi_percentage": round(roi, 2),
        "profit_net": round(profit, 2)
    }

def compute_velocity_score_simple(bsr: Optional[int], category: str = "Books") -> float:
    """Simplified velocity scoring based on BSR."""
    if not bsr or bsr <= 0:
        return 50.0  # Neutral score for missing data
    
    # Books category BSR thresholds (simplified)
    if bsr <= 10000:
        return 90.0
    elif bsr <= 50000:
        return 75.0
    elif bsr <= 200000:
        return 60.0
    elif bsr <= 500000:
        return 40.0
    elif bsr <= 1000000:
        return 25.0
    else:
        return 10.0

def compute_stability_score_simple(price_history: List[int]) -> float:
    """Simplified price stability scoring."""
    if not price_history or len(price_history) < 5:
        return 50.0  # Neutral score for insufficient data
    
    # Convert Keepa price format to actual prices (divide by 100)
    prices = [p/100 for p in price_history if p > 0]
    
    if len(prices) < 3:
        return 50.0
    
    # Calculate coefficient of variation
    mean_price = sum(prices) / len(prices)
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    std_dev = variance ** 0.5
    
    cv = std_dev / mean_price if mean_price > 0 else 1.0
    
    # Convert CV to score (lower CV = higher stability = higher score)
    if cv <= 0.1:  # 10% variation
        return 90.0
    elif cv <= 0.2:  # 20% variation
        return 70.0
    elif cv <= 0.3:  # 30% variation
        return 50.0
    elif cv <= 0.5:  # 50% variation
        return 30.0
    else:
        return 10.0

def compute_confidence_score_simple(product_data: Dict) -> float:
    """Simplified confidence scoring based on data availability."""
    score = 0.0
    
    # Check for key data availability
    if product_data.get('title'):
        score += 20
    if product_data.get('imagesCSV'):
        score += 15  
    if product_data.get('stats', {}).get('current') and len(product_data['stats']['current']) > 0:
        score += 25
    if product_data.get('csv') and len(product_data.get('csv', [])) > 20:  # At least 20 price points
        score += 25
    if product_data.get('salesRanks') and product_data['salesRanks']:
        score += 15
    
    return min(score, 100.0)

def compute_overall_rating_simple(scores: Dict[str, float], thresholds: Dict[str, float]) -> str:
    """Compute overall rating based on scores and thresholds."""
    roi_score = scores.get('roi_percentage', 0)
    velocity_score = scores.get('velocity_score', 0)
    stability_score = scores.get('stability_score', 0)
    confidence_score = scores.get('confidence_score', 0)
    
    # Check if meets all thresholds for EXCELLENT
    if (roi_score >= thresholds.get('roi_min', 35) and
        velocity_score >= thresholds.get('velocity_min', 70) and
        stability_score >= thresholds.get('stability_min', 70) and
        confidence_score >= thresholds.get('confidence_min', 70)):
        return "EXCELLENT"
    
    # Check for GOOD rating (relaxed thresholds)
    elif (roi_score >= thresholds.get('roi_min', 25) and
          velocity_score >= thresholds.get('velocity_min', 60) and
          stability_score >= thresholds.get('stability_min', 60) and
          confidence_score >= thresholds.get('confidence_min', 60)):
        return "GOOD"
    
    # Check for FAIR rating (minimum viability)
    elif roi_score >= thresholds.get('roi_min', 20):
        return "FAIR"
    
    else:
        return "PASS"

# ============================================================================
# DATA FETCHING & ANALYSIS
# ============================================================================

async def fetch_and_analyze_asins(asins: List[str], thresholds: Dict[str, float], use_cache: bool = True) -> List[Dict[str, Any]]:
    """Fetch Keepa data and analyze ASINs with given thresholds."""
    print(f"Analyzing {len(asins)} ASINs with thresholds: {thresholds}")
    
    config_hash = hashlib.md5(str(sorted(thresholds.items())).encode()).hexdigest()[:8]
    results = []
    
    async with SimpleKeepaClient(KEEPA_API_KEY) as client:
        for i, asin in enumerate(asins):
            print(f"  [{i+1}/{len(asins)}] Processing {asin}...")
            
            # Check cache first
            cache_key = get_cache_key(asin, config_hash)
            if use_cache:
                cached_result = load_from_cache(cache_key)
                if cached_result and 'analysis' in cached_result:
                    results.append(cached_result['analysis'])
                    print(f"    ✓ Cache hit")
                    continue
            
            # Fetch from API
            product_data = await client.get_product_data(asin)
            await asyncio.sleep(KEEPA_REQUEST_DELAY_SECONDS)  # Rate limiting
            
            if not product_data:
                print(f"    ✗ No data available")
                continue
            
            # Analyze the product
            analysis = analyze_product(product_data, thresholds)
            analysis['asin'] = asin
            results.append(analysis)
            
            # Cache the result
            if use_cache:
                save_to_cache(cache_key, {'analysis': analysis})
            
            print(f"    ✓ ROI: {analysis['roi_percentage']:.1f}%, Rating: {analysis['overall_rating']}")
    
    return results

def analyze_product(product_data: Dict, thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Analyze a single product with advanced scoring."""
    
    # Extract basic info
    title = product_data.get('title', 'Unknown')
    current_price = 0.0
    bsr = None
    
    # Get current price - Keepa uses various price types
    stats_current = product_data.get('stats', {}).get('current', [])
    if stats_current:
        # Try buy box price first (index 0), then others
        for price_index in [0, 1, 2]:  # Different price types
            if len(stats_current) > price_index and stats_current[price_index] > 0:
                current_price = stats_current[price_index] / 100.0  # Keepa uses cents
                break
    
    # Get BSR - try different indices as BSR can be at different positions
    if stats_current:
        for bsr_index in [3, 4, 5]:
            if len(stats_current) > bsr_index and stats_current[bsr_index] > 0:
                bsr = stats_current[bsr_index]
                break
    
    # Alternative: try salesRanks directly
    if not bsr and product_data.get('salesRanks'):
        sales_ranks = product_data['salesRanks']
        if isinstance(sales_ranks, dict):
            # Get the first available rank
            for category_id, rank_data in sales_ranks.items():
                if isinstance(rank_data, list) and len(rank_data) > 1:
                    # Keepa format: [timestamp, rank]
                    bsr = rank_data[1]
                    break
    
    # For price history, use stats averages as proxy for stability
    price_history = []
    if stats_current:
        # Use available price data points as history approximation
        stats_obj = product_data.get('stats', {})
        price_points = []
        
        # Extract average prices - handle list format
        for avg_key in ['avg30', 'avg90', 'avg180', 'avg365']:
            if avg_key in stats_obj:
                avg_val = stats_obj[avg_key]
                # Handle both direct values and lists
                if isinstance(avg_val, list) and len(avg_val) > 0:
                    avg_val = avg_val[0]  # Take first element
                if isinstance(avg_val, (int, float)) and avg_val > 0:
                    price_points.append(avg_val)
        
        # Add current prices from different sources (skip -1 values)
        for i in range(min(5, len(stats_current))):
            if stats_current[i] > 0:
                price_points.append(stats_current[i])
        
        price_history = price_points
    
    # Calculate scores
    estimated_cost = current_price * 0.75  # Assume buying at 75% of current price
    roi_data = calculate_roi_basic(current_price, estimated_cost)
    
    velocity_score = compute_velocity_score_simple(bsr)
    stability_score = compute_stability_score_simple(price_history)
    confidence_score = compute_confidence_score_simple(product_data)
    
    # Combine all metrics
    scores = {
        'roi_percentage': roi_data['roi_percentage'],
        'velocity_score': velocity_score,
        'stability_score': stability_score,
        'confidence_score': confidence_score
    }
    
    overall_rating = compute_overall_rating_simple(scores, thresholds)
    
    return {
        'title': title,
        'current_price': current_price,
        'estimated_cost': estimated_cost,
        'profit_net': roi_data['profit_net'],
        'bsr': bsr,
        'price_history_points': len(price_history),
        **scores,
        'overall_rating': overall_rating
    }

# ============================================================================
# OPTIMIZATION & REPORTING  
# ============================================================================

def run_grid_search(data: List[Dict], grid_params: Dict) -> pd.DataFrame:
    """Run grid search on threshold combinations."""
    print("Running grid search optimization...")
    
    results = []
    total_combinations = 1
    for values in grid_params.values():
        total_combinations *= len(values)
    
    combo_count = 0
    
    for roi_min in grid_params['roi_min']:
        for velocity_min in grid_params['velocity_min']:
            for stability_min in grid_params['stability_min']:
                for confidence_min in grid_params['confidence_min']:
                    combo_count += 1
                    
                    thresholds = {
                        'roi_min': roi_min,
                        'velocity_min': velocity_min, 
                        'stability_min': stability_min,
                        'confidence_min': confidence_min
                    }
                    
                    # Re-compute ratings with these thresholds
                    ratings = [compute_overall_rating_simple(item, thresholds) for item in data]
                    rating_counts = {rating: ratings.count(rating) for rating in ['EXCELLENT', 'GOOD', 'FAIR', 'PASS']}
                    
                    # Calculate metrics
                    total_items = len(ratings)
                    excellent_items = [item for item, rating in zip(data, ratings) if rating == 'EXCELLENT']
                    good_plus_items = [item for item, rating in zip(data, ratings) if rating in ['EXCELLENT', 'GOOD']]
                    
                    excellent_pct = (rating_counts['EXCELLENT'] / total_items) * 100
                    good_plus_pct = ((rating_counts['EXCELLENT'] + rating_counts['GOOD']) / total_items) * 100
                    
                    # Calculate ROI stats for EXCELLENT items
                    excellent_rois = [item['roi_percentage'] for item in excellent_items] if excellent_items else [0]
                    good_plus_rois = [item['roi_percentage'] for item in good_plus_items] if good_plus_items else [0]
                    
                    results.append({
                        'roi_min': roi_min,
                        'velocity_min': velocity_min,
                        'stability_min': stability_min,
                        'confidence_min': confidence_min,
                        'excellent_count': rating_counts['EXCELLENT'],
                        'excellent_pct': excellent_pct,
                        'good_plus_count': rating_counts['EXCELLENT'] + rating_counts['GOOD'],
                        'good_plus_pct': good_plus_pct,
                        'excellent_median_roi': pd.Series(excellent_rois).median(),
                        'good_plus_median_roi': pd.Series(good_plus_rois).median(),
                        'total_items': total_items
                    })
                    
                    if combo_count % 10 == 0:
                        print(f"  Progress: {combo_count}/{total_combinations} combinations tested")
    
    return pd.DataFrame(results)

def generate_reports(data: List[Dict], grid_results: pd.DataFrame):
    """Generate analysis reports and visualizations."""
    print("Generating reports...")
    
    # 1. Score distributions plot
    plt.figure(figsize=(15, 10))
    plt.style.use('dark_background')
    
    scores_df = pd.DataFrame([{
        'ROI %': item['roi_percentage'],
        'Velocity Score': item['velocity_score'],
        'Stability Score': item['stability_score'],  
        'Confidence Score': item['confidence_score']
    } for item in data])
    
    for i, col in enumerate(['ROI %', 'Velocity Score', 'Stability Score', 'Confidence Score']):
        plt.subplot(2, 2, i+1)
        plt.hist(scores_df[col], bins=20, alpha=0.7, color=['red', 'blue', 'green', 'orange'][i])
        plt.title(f'{col} Distribution')
        plt.xlabel(col)
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, 'score_distributions.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Export detailed results
    detailed_df = pd.DataFrame(data)
    detailed_df.to_csv(os.path.join(REPORT_DIR, 'detailed_analysis.csv'), index=False)
    
    # 3. Export grid search results
    grid_results = grid_results.sort_values('excellent_median_roi', ascending=False)
    grid_results.to_csv(os.path.join(REPORT_DIR, 'grid_search_results.csv'), index=False)
    
    # 4. Top recommendations
    top_configs = grid_results.head(10)
    print("\n🏆 TOP 10 THRESHOLD CONFIGURATIONS:")
    print("=" * 80)
    for _, row in top_configs.iterrows():
        print(f"ROI≥{row['roi_min']}%, Vel≥{row['velocity_min']}, Stab≥{row['stability_min']}, Conf≥{row['confidence_min']} → "
              f"EXCELLENT: {row['excellent_count']} items ({row['excellent_pct']:.1f}%), "
              f"Median ROI: {row['excellent_median_roi']:.1f}%")
    
    print(f"\nReports saved to: {os.path.abspath(REPORT_DIR)}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main execution function."""
    print("🔍 ArbitrageVault - Advanced Scoring Optimization")
    print("=" * 60)
    
    ensure_directories()
    
    # Load test ASINs
    print("Loading test ASINs...")
    with open(ASIN_INPUT_FILE, 'r') as f:
        asin_data = json.load(f)
    
    all_asins = []
    # Handle nested structure: test_asins -> categories -> asins
    test_data = asin_data.get('test_asins', asin_data)
    for category, asins in test_data.items():
        all_asins.extend(asins)
        print(f"  - {category}: {len(asins)} ASINs")
    
    print(f"Total ASINs to analyze: {len(all_asins)}")
    
    # Load business rules
    business_rules = load_business_rules()
    default_thresholds = business_rules.get('advanced_scoring', {}).get('thresholds', {
        'roi_min': 30,
        'velocity_min': 70,
        'stability_min': 70,
        'confidence_min': 70
    })
    
    print(f"Current thresholds: {default_thresholds}")
    
    # Fetch and analyze data with default thresholds
    print("\n📊 Fetching Keepa data...")
    analysis_data = await fetch_and_analyze_asins(all_asins, default_thresholds, use_cache=True)
    
    if not analysis_data:
        print("❌ No data retrieved. Check Keepa API key and network connection.")
        return
    
    print(f"✅ Successfully analyzed {len(analysis_data)} products")
    
    # Run optimization
    print("\n🔧 Running threshold optimization...")
    grid_results = run_grid_search(analysis_data, GRID_SEARCH_PARAMS)
    
    # Generate reports
    print("\n📋 Generating reports...")
    generate_reports(analysis_data, grid_results)
    
    print("\n✅ Optimization complete!")

if __name__ == "__main__":
    asyncio.run(main())