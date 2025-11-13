"""Test corrected parsing with problematic ASINs."""
import asyncio
import keyring
from app.services.keepa_service import KeepaService
from app.services.keepa_parser import parse_keepa_product

async def test_parsing_correction():
    """Test parsing correction with ASINs that failed before."""
    api_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    keepa_service = KeepaService(api_key=api_key)
    
    # ASINs that showed 100% N/A in frontend tests
    test_asins = [
        ('B0D1XD1ZV3', 'AirPods Pro 2 - Should have price'),
        ('B0CHTKM281', 'Bestseller - May have no price'),
        ('B09B8RXYM5', 'Echo Dot 5th - Should have price'),
    ]
    
    results = []
    
    async with keepa_service:
        for asin, description in test_asins:
            print(f"\n{'='*70}")
            print(f"Testing: {asin} ({description})")
            print('='*70)
            
            try:
                # Fetch data
                raw_data = await keepa_service.get_product_data(asin)
                
                if not raw_data:
                    print("❌ No data returned from Keepa")
                    results.append((asin, 'NO_DATA', None))
                    continue
                
                # Parse with corrected parser
                parsed = parse_keepa_product(raw_data)
                
                # Extract key fields
                current_price = parsed.get('current_price')
                current_bsr = parsed.get('current_bsr')
                title = parsed.get('title', 'N/A')
                
                print(f"✅ Parsing successful:")
                print(f"   Title: {title[:60] if title and title != 'N/A' else 'N/A'}...")
                print(f"   Current Price: ${current_price if current_price else 'N/A'}")
                print(f"   BSR: {current_bsr if current_bsr else 'N/A'}")
                
                # Check if we have enough data for ROI calculation
                has_price = current_price is not None and current_price > 0
                has_bsr = current_bsr is not None and current_bsr > 0
                
                status = 'OK' if (has_price and has_bsr) else 'PARTIAL'
                if not has_price:
                    print(f"   ⚠️ No valid price found")
                    status = 'NO_PRICE'
                if not has_bsr:
                    print(f"   ⚠️ No BSR found")
                
                results.append((asin, status, current_price))
                
            except Exception as e:
                print(f"❌ Error parsing {asin}: {e}")
                import traceback
                traceback.print_exc()
                results.append((asin, 'ERROR', None))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    for asin, status, price in results:
        price_str = f"${price}" if price else "N/A"
        print(f"{asin}: {status:12} - Price: {price_str}")
    
    # Count successes
    ok_count = sum(1 for _, status, _ in results if status == 'OK')
    total = len(results)
    print(f"\n✅ Success rate: {ok_count}/{total} ({ok_count/total*100:.1f}%)")
    
    if ok_count == total:
        print("🎉 ALL TESTS PASSED - Parsing correction successful!")
    elif ok_count > 0:
        print("⚠️ PARTIAL SUCCESS - Some ASINs still have issues")
    else:
        print("❌ ALL TESTS FAILED - Further investigation needed")

if __name__ == '__main__':
    asyncio.run(test_parsing_correction())
