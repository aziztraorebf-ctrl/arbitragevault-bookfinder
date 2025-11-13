"""Test parsing with REAL Amazon Bestsellers (October 2025)."""
import asyncio
import keyring
from app.services.keepa_service import KeepaService
from app.services.keepa_parser import parse_keepa_product

async def test_bestsellers():
    """Test parsing with confirmed active Amazon bestsellers."""
    api_key = keyring.get_password('memex', 'KEEPA_API_KEY')
    keepa_service = KeepaService(api_key=api_key)
    
    # REAL Amazon Bestsellers (Electronics) - October 4, 2025
    bestsellers = [
        ('B0CQMRKRV5', 'Amazon Fire TV Stick HD', '$17.99'),
        ('B0DCH8VDXF', 'Apple EarPods USB-C', '$16.99'),
        ('B0CJM1GNFQ', 'Fire TV Stick 4K', '$24.99'),
        ('B0CWXNS552', 'Apple AirTag (1 pack)', '$24.99'),
        ('B0D54JZTHY', 'Apple AirTag (4 pack)', '$74.99'),
        ('B08JHCVHTY', 'Blink Subscription Plus', '$10.00'),
        ('B0D1XD1ZV3', 'AirPods Pro 2', '$199.00'),  # Notre ASIN de contrôle qui fonctionne
    ]
    
    results = []
    
    async with keepa_service:
        for asin, description, expected_price in bestsellers:
            print(f"\n{'='*70}")
            print(f"Testing: {asin}")
            print(f"Product: {description}")
            print(f"Expected price: ~{expected_price}")
            print('='*70)
            
            try:
                # Fetch data
                raw_data = await keepa_service.get_product_data(asin)
                
                if not raw_data:
                    print("❌ No data returned from Keepa")
                    results.append((asin, description, 'NO_DATA', None, None))
                    continue
                
                # Parse
                parsed = parse_keepa_product(raw_data)
                
                # Extract fields
                current_price = parsed.get('current_price')
                current_bsr = parsed.get('current_bsr')
                title = parsed.get('title', 'N/A')
                
                # Display
                print(f"✅ Parsing successful:")
                title_display = title[:60] if title and title != 'N/A' else 'N/A'
                print(f"   Title: {title_display}...")
                print(f"   Keepa Price: ${current_price if current_price else 'N/A'}")
                print(f"   BSR: {current_bsr if current_bsr else 'N/A'}")
                
                # Validate
                has_price = current_price is not None and current_price > 0
                has_bsr = current_bsr is not None and current_bsr > 0
                has_title = title and title != 'N/A'
                
                if has_price and has_bsr and has_title:
                    status = 'COMPLETE'
                    print(f"   ✅ Complete data (price + BSR + title)")
                elif has_price:
                    status = 'PARTIAL'
                    print(f"   ⚠️ Price OK but missing BSR or title")
                else:
                    status = 'NO_PRICE'
                    print(f"   ❌ No valid price")
                
                results.append((asin, description, status, current_price, current_bsr))
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                results.append((asin, description, 'ERROR', None, None))
    
    # Summary Report
    print(f"\n{'='*70}")
    print("📊 BESTSELLERS PARSING TEST - FINAL REPORT")
    print('='*70)
    print(f"{'ASIN':<15} {'Status':<12} {'Price':<10} {'BSR':<12} Product")
    print('-'*70)
    
    for asin, desc, status, price, bsr in results:
        price_str = f"${price}" if price else "N/A"
        bsr_str = f"{bsr:,}" if bsr else "N/A"
        status_emoji = '✅' if status == 'COMPLETE' else '⚠️' if status == 'PARTIAL' else '❌'
        print(f"{asin:<15} {status_emoji} {status:<10} {price_str:<10} {bsr_str:<12} {desc[:30]}")
    
    # Statistics
    total = len(results)
    complete = sum(1 for _, _, s, _, _ in results if s == 'COMPLETE')
    partial = sum(1 for _, _, s, _, _ in results if s == 'PARTIAL')
    no_price = sum(1 for _, _, s, _, _ in results if s == 'NO_PRICE')
    errors = sum(1 for _, _, s, _, _ in results if s == 'ERROR')
    
    success_rate = (complete / total * 100) if total > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"📈 SUCCESS METRICS")
    print('='*70)
    print(f"Total ASINs tested: {total}")
    print(f"✅ Complete (Price + BSR + Title): {complete} ({complete/total*100:.1f}%)")
    print(f"⚠️  Partial (Price only): {partial} ({partial/total*100:.1f}%)")
    print(f"❌ No Price: {no_price} ({no_price/total*100:.1f}%)")
    print(f"❌ Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"\n🎯 Success Rate (Complete data): {success_rate:.1f}%")
    
    # Verdict
    print(f"\n{'='*70}")
    if success_rate >= 80:
        print("🎉 EXCELLENT - Parsing works correctly with real products!")
        print("✅ Ready to commit and deploy to production")
        return True
    elif success_rate >= 50:
        print("⚠️ GOOD - Parsing works but some data may be incomplete")
        print("Consider investigating partial results")
        return True
    else:
        print("❌ FAILED - Parsing needs more investigation")
        print("Check logs for errors")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_bestsellers())
    exit(0 if success else 1)
