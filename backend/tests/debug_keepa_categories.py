"""
Debug script to test Keepa /bestsellers endpoint for different category IDs.
This helps identify which categories return data and which don't.
"""
import httpx
import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
if not KEEPA_API_KEY:
    print("ERROR: KEEPA_API_KEY not found in environment")
    exit(1)

# Categories to test
CATEGORIES_TO_TEST = {
    # Currently used in autosourcing_service.py
    3738: "Medical Books (current default)",
    4277: "Textbooks",
    3546: "Programming",
    4142: "Engineering",
    2578: "Accounting",
    # Amazon root categories
    283155: "Books (root)",
    # Textbooks subcategories (from Amazon category tree)
    465600: "Textbooks (root)",
    468216: "Science & Mathematics",
    468220: "Engineering",
    468206: "Business & Finance",
    468226: "Computer Science",
    # Other book categories
    173507: "Computer & Technology",
    173508: "Programming",
    3: "Arts & Photography",
}


async def test_bestsellers_category(category_id: int, category_name: str) -> dict:
    """Test if a category returns bestsellers data."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"https://api.keepa.com/bestsellers?key={KEEPA_API_KEY}&domain=1&category={category_id}"
            response = await client.get(url)

            if response.status_code != 200:
                return {
                    "category_id": category_id,
                    "name": category_name,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "asin_count": 0
                }

            data = response.json()

            # Check response structure
            has_bestsellers = "bestSellersList" in data
            asin_list = data.get("bestSellersList", {}).get("asinList", [])
            tokens_left = data.get("tokensLeft", "N/A")

            return {
                "category_id": category_id,
                "name": category_name,
                "success": has_bestsellers and len(asin_list) > 0,
                "has_bestSellersList": has_bestsellers,
                "asin_count": len(asin_list),
                "tokens_left": tokens_left,
                "sample_asins": asin_list[:3] if asin_list else []
            }

        except Exception as e:
            return {
                "category_id": category_id,
                "name": category_name,
                "success": False,
                "error": str(e),
                "asin_count": 0
            }


async def main():
    print("=" * 80)
    print("KEEPA BESTSELLERS API - CATEGORY TEST")
    print("=" * 80)
    print(f"Testing {len(CATEGORIES_TO_TEST)} categories...\n")

    results = []
    working = []
    not_working = []

    for category_id, category_name in CATEGORIES_TO_TEST.items():
        result = await test_bestsellers_category(category_id, category_name)
        results.append(result)

        status = "OK" if result["success"] else "FAIL"
        asin_count = result.get("asin_count", 0)

        print(f"[{status}] Category {category_id} ({category_name}): {asin_count} ASINs")

        if result["success"]:
            working.append(result)
        else:
            not_working.append(result)

        # Rate limiting - wait between requests
        await asyncio.sleep(0.5)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nWORKING CATEGORIES ({len(working)}):")
    for r in working:
        print(f"  - {r['category_id']}: {r['name']} ({r['asin_count']} ASINs)")
        if r.get("sample_asins"):
            print(f"    Sample: {r['sample_asins']}")

    print(f"\nNOT WORKING CATEGORIES ({len(not_working)}):")
    for r in not_working:
        error = r.get("error", "No ASINs returned")
        print(f"  - {r['category_id']}: {r['name']} - {error}")

    print(f"\nTokens remaining: {results[-1].get('tokens_left', 'N/A')}")

    # Save detailed results
    with open("keepa_category_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to keepa_category_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
