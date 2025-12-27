"""
Audit AutoSourcing Competition Filter
Phase 7.2 - Verify if AutoSourcing has same issue as Phase 6 Niche Discovery
"""
import requests
import json

BASE_URL = "https://arbitragevault-backend-v2.onrender.com/api/v1"


def run_audit():
    print("=" * 60)
    print("AUDIT: AutoSourcing Competition Analysis")
    print("=" * 60)

    # Test 1: Check token balance
    print("\n[1] Checking token balance...")
    try:
        resp = requests.get(f"{BASE_URL}/keepa/health", timeout=10)
        data = resp.json()
        tokens = data.get("tokens", {}).get("remaining", 0)
        print(f"    Tokens available: {tokens}")
        if tokens < 50:
            print("    WARNING: Low tokens, test may fail")
            return
    except Exception as e:
        print(f"    Error: {e}")
        return

    # Test 2: Run small AutoSourcing job
    print("\n[2] Running AutoSourcing job (10 products)...")
    run_payload = {
        "profile_name": "Audit-Competition-Check",
        "discovery_config": {
            "categories": ["books"],
            "bsr_range": [10000, 80000],
            "price_range": [15, 60],
            "max_results": 10
        },
        "scoring_config": {
            "roi_min": 20,
            "velocity_min": 30,
            "max_results": 5
        }
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/autosourcing/run-custom",
            json=run_payload,
            timeout=120
        )
        print(f"    Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"    Job ID: {data.get('id')}")
            print(f"    Job Status: {data.get('status')}")
            print(f"    ASINs discovered: {data.get('asins_discovered', 0)}")
            print(f"    Picks returned: {len(data.get('picks', []))}")

            picks = data.get("picks", [])
            if picks:
                print("\n[3] PICKS COMPETITION ANALYSIS:")
                print("-" * 50)

                amazon_present = 0
                high_fba = 0

                for i, pick in enumerate(picks[:5], 1):
                    asin = pick.get("asin", "N/A")
                    title = (pick.get("title") or "N/A")[:40]
                    bsr = pick.get("bsr", "N/A")
                    price = pick.get("amazon_price") or pick.get("buy_box_price") or "N/A"
                    roi = pick.get("roi_percentage", "N/A")
                    velocity = pick.get("velocity_score", "N/A")
                    fba_count = pick.get("fba_seller_count", "UNKNOWN")
                    amazon_sells = pick.get("amazon_on_listing", "UNKNOWN")

                    print(f"\n    Pick {i}:")
                    print(f"      ASIN: {asin}")
                    print(f"      Title: {title}...")
                    print(f"      BSR: {bsr}")
                    print(f"      Price: ${price}")
                    print(f"      ROI: {roi}%")
                    print(f"      Velocity: {velocity}")
                    print(f"      FBA Sellers: {fba_count}")
                    print(f"      Amazon Sells: {amazon_sells}")

                    # Track competition metrics
                    if amazon_sells in [True, "true", "True", 1]:
                        amazon_present += 1
                    if isinstance(fba_count, (int, float)) and fba_count > 5:
                        high_fba += 1

                print("\n" + "=" * 60)
                print("COMPETITION SUMMARY:")
                print("=" * 60)
                print(f"  Total picks: {len(picks)}")
                print(f"  Amazon present: {amazon_present}/{len(picks[:5])} (SHOULD BE 0)")
                print(f"  High FBA (>5): {high_fba}/{len(picks[:5])} (SHOULD BE 0)")

                if amazon_present > 0:
                    print("\n  *** PROBLEM: Amazon is present on some picks!")
                    print("  *** AutoSourcing may have same issue as Phase 6")
                elif high_fba > 0:
                    print("\n  *** WARNING: High FBA seller count on some picks")
                else:
                    print("\n  OK: Competition filtering appears to work")

            else:
                print("\n[3] NO PICKS RETURNED")
                print("    This could indicate:")
                print("    - Filters too restrictive (Phase 6 issue)")
                print("    - No products match criteria")
                print("    - API error")
                print(f"    Error message: {data.get('error_message', 'None')}")

        elif resp.status_code == 429:
            print("    ERROR: Insufficient tokens")
        else:
            print(f"    Error: {resp.text[:300]}")

    except Exception as e:
        print(f"    Error: {e}")


if __name__ == "__main__":
    run_audit()
