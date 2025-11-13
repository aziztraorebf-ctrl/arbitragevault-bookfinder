"""
Debug script to identify which BSR extraction strategy is being used
"""
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.keepa_parser_v2 import KeepaBSRExtractor

# Load last API result
with open('last_api_result.json', 'r') as f:
    data = json.load(f)

raw_keepa = data

print("=" * 80)
print("BSR EXTRACTION STRATEGY DEBUG")
print("=" * 80)
print(f"ASIN: {raw_keepa.get('asin')}")
print()

# Check salesRanks
sales_ranks = raw_keepa.get("salesRanks", {})
sales_rank_ref = raw_keepa.get("salesRankReference")
print(f"salesRankReference: {sales_rank_ref}")
print(f"salesRanks keys: {list(sales_ranks.keys())}")
if sales_ranks:
    for cat_id, rank_data in sales_ranks.items():
        print(f"  Category {cat_id}: {rank_data}")
print()

# Check stats.current
stats = raw_keepa.get("stats", {})
current = stats.get("current", [])
print(f"stats.current[3] (BSR): {current[3] if len(current) > 3 else 'N/A'}")
print()

# Check stats.avg30
avg30 = stats.get("avg30", [])
print(f"stats.avg30[3] (30-day avg BSR): {avg30[3] if len(avg30) > 3 else 'N/A'}")
print()

# Check csv[3]
csv_data = raw_keepa.get("csv", [])
if csv_data and len(csv_data) > 3:
    sales_history = csv_data[3]
    if sales_history and len(sales_history) >= 2:
        last_timestamp = sales_history[-2]
        last_value = sales_history[-1]
        print(f"csv[3] last point: timestamp={last_timestamp}, BSR={last_value}")
print()

# Extract with actual method
extracted_bsr = KeepaBSRExtractor.extract_current_bsr(raw_keepa)
print("=" * 80)
print(f"EXTRACTED BSR: {extracted_bsr}")
print("=" * 80)
