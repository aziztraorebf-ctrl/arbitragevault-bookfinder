#!/usr/bin/env python3
"""
Test rapide du système d'optimisation avec quelques ASINs seulement.
"""
import asyncio
import sys
import os

# Add path to the standalone script
sys.path.insert(0, os.path.dirname(__file__))

from optimize_scoring_standalone import (
    SimpleKeepaClient, 
    analyze_product, 
    KEEPA_API_KEY,
    ensure_directories,
    load_business_rules
)

async def test_single_asin():
    """Test avec un seul ASIN pour validation."""
    print("🧪 Test du système d'optimisation")
    print("=" * 40)
    
    ensure_directories()
    
    # Test avec un ASIN de livre populaire
    test_asin = "0134093410"  # Un manuel technique
    
    # Load business rules
    try:
        business_rules = load_business_rules()
        thresholds = business_rules.get('advanced_scoring', {}).get('thresholds', {
            'roi_min': 30,
            'velocity_min': 70,
            'stability_min': 70,
            'confidence_min': 70
        })
        print(f"Thresholds loaded: {thresholds}")
    except Exception as e:
        print(f"Error loading business rules: {e}")
        thresholds = {'roi_min': 30, 'velocity_min': 70, 'stability_min': 70, 'confidence_min': 70}
    
    print(f"\nTesting ASIN: {test_asin}")
    
    async with SimpleKeepaClient(KEEPA_API_KEY) as client:
        # Fetch data
        product_data = await client.get_product_data(test_asin)
        
        if not product_data:
            print("❌ No data retrieved from Keepa API")
            return False
            
        print("✅ Data retrieved successfully")
        print(f"Title: {product_data.get('title', 'Unknown')[:60]}...")
        
        # Debug: Print data structure
        print(f"\n🔍 Data structure debug:")
        print(f"  Keys: {list(product_data.keys())}")
        if 'stats' in product_data:
            print(f"  Stats keys: {list(product_data['stats'].keys()) if product_data['stats'] else 'None'}")
            if product_data['stats'] and 'current' in product_data['stats']:
                current = product_data['stats']['current']
                print(f"  Stats current length: {len(current) if current else 0}")
                print(f"  Stats current sample: {current[:5] if current else 'None'}")
        
        if 'csv' in product_data:
            csv_data = product_data['csv'] 
            print(f"  CSV data type: {type(csv_data)}")
            print(f"  CSV data length: {len(csv_data) if csv_data else 0}")
            if csv_data and len(csv_data) > 0:
                print(f"  CSV sample: {csv_data[:10]}")
                # Note: Keepa CSV format corresponds to current stats, not time-series data
                
        # Show sales ranks
        if 'salesRanks' in product_data:
            ranks = product_data['salesRanks']
            print(f"  Sales Ranks: {ranks}")
        if 'salesRankReference' in product_data:
            rank_ref = product_data['salesRankReference'] 
            print(f"  Sales Rank Ref: {rank_ref}")
        
        # Analyze product
        analysis = analyze_product(product_data, thresholds)
        analysis['asin'] = test_asin
        
        print(f"\n📊 Analysis Results:")
        print(f"  Current Price: ${analysis['current_price']:.2f}")
        print(f"  ROI: {analysis['roi_percentage']:.1f}%")
        print(f"  Velocity Score: {analysis['velocity_score']:.1f}")
        print(f"  Stability Score: {analysis['stability_score']:.1f}")
        print(f"  Confidence Score: {analysis['confidence_score']:.1f}")
        print(f"  Overall Rating: {analysis['overall_rating']}")
        print(f"  BSR: {analysis.get('bsr', 'N/A')}")
        print(f"  Price History Points: {analysis['price_history_points']}")
        
        return True

if __name__ == "__main__":
    success = asyncio.run(test_single_asin())
    if success:
        print("\n✅ Test successful! Ready for full optimization.")
    else:
        print("\n❌ Test failed. Check configuration.")