"""Check stats.current structure from Keepa API."""
import asyncio
import keyring
import json
from app.services.keepa_service import KeepaService

async def check_stats_current():
    """Check how Keepa returns current price data."""
    api_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    keepa_service = KeepaService(api_key=api_key)
    
    test_asins = [
        'B0D1XD1ZV3',  # AirPods Pro 2 (test réussi utilisateur)
        'B00FLIJJSA',  # Livre (test debug réussi)
        'B0CHTKM281',  # Bestseller (test 100% N/A)
    ]
    
    async with keepa_service:
        for asin in test_asins:
            print(f"\n{'='*60}")
            print(f"ASIN: {asin}")
            print('='*60)
            
            data = await keepa_service.get_product_data(asin)
            
            if not data:
                print("❌ No data returned")
                continue
            
            # Check stats.current structure
            stats = data.get('stats', {})
            current = stats.get('current', [])
            
            print(f"\n📊 stats.current (length: {len(current) if current else 0}):")
            if current and len(current) > 0:
                # Show first few values
                print(f"  Indices 0-9: {current[:10]}")
                print(f"  Indices 10-19: {current[10:20] if len(current) > 10 else 'N/A'}")
                
                # Check which indices have valid prices (not -1)
                valid_indices = []
                for i, val in enumerate(current):
                    if val != -1 and val is not None and val > 0:
                        valid_indices.append((i, val))
                
                print(f"\n✅ Valid price indices (not -1):")
                for idx, val in valid_indices[:10]:  # Show first 10
                    print(f"  Index {idx}: {val} ({val/100:.2f} USD)")
            else:
                print("  ❌ Empty or None")
            
            # Also check csv structure
            csv_data = data.get('csv', [])
            print(f"\n📈 csv structure (length: {len(csv_data) if csv_data else 0}):")
            if csv_data:
                print(f"  Number of price arrays: {len(csv_data)}")
                # Check if csv arrays have data
                for i in range(min(5, len(csv_data))):
                    arr = csv_data[i]
                    if arr and len(arr) > 0:
                        last_val = arr[-1] if len(arr) > 0 else None
                        print(f"  csv[{i}] last value: {last_val} ({last_val/100:.2f} USD if valid)" if last_val and last_val != -1 else f"  csv[{i}]: {last_val}")

if __name__ == '__main__':
    asyncio.run(check_stats_current())
