"""
Test script for Bookmarks API endpoints validation.

Tests complete CRUD flow against production backend:
https://arbitragevault-backend-v2.onrender.com

Author: Claude + Aziz
Date: 2025-11-02
"""

import requests
import json
from typing import Dict, Any, Optional

# Production backend URL
BASE_URL = "https://arbitragevault-backend-v2.onrender.com"
BOOKMARKS_ENDPOINT = f"{BASE_URL}/api/v1/bookmarks/niches"

# Mock authentication header (temporary for testing without real auth)
MOCK_USER_ID = "test-user-001"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "X-User-ID": MOCK_USER_ID
}


class BookmarksAPITest:
    """Test suite for Bookmarks API endpoints."""

    def __init__(self):
        self.created_bookmark_id: Optional[str] = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.test_results["total_tests"] += 1

        if passed:
            self.test_results["passed"] += 1
            print(f"PASS: {test_name}")
            if message:
                print(f"      {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append({test_name: message})
            print(f"FAIL: {test_name}")
            print(f"      ERROR: {message}")
        print()

    def test_1_create_bookmark(self) -> bool:
        """Test POST /api/v1/bookmarks/niches - Create new bookmark."""
        print("=" * 60)
        print("TEST 1: Create Bookmark")
        print("=" * 60)

        payload = {
            "niche_name": "Test Niche - Python Books",
            "category_id": 3617,
            "category_name": "Programming Books",
            "filters": {
                "bsr_range": [10000, 50000],
                "price_range": [15, 40],
                "min_roi": 30
            },
            "last_score": 85.5,
            "description": "Test bookmark for validation"
        }

        try:
            response = requests.post(BOOKMARKS_ENDPOINT, json=payload)

            print(f"Status Code: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

            if response.status_code == 201:
                data = response.json()
                required_fields = ["id", "niche_name", "filters", "created_at", "updated_at"]

                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    self.log_test(
                        "Create Bookmark",
                        False,
                        f"Missing fields in response: {missing_fields}"
                    )
                    return False

                self.created_bookmark_id = data["id"]

                if data["niche_name"] != payload["niche_name"]:
                    self.log_test(
                        "Create Bookmark",
                        False,
                        f"niche_name mismatch: expected '{payload['niche_name']}', got '{data['niche_name']}'"
                    )
                    return False

                self.log_test(
                    "Create Bookmark",
                    True,
                    f"Bookmark created with ID: {self.created_bookmark_id}"
                )
                return True
            else:
                self.log_test(
                    "Create Bookmark",
                    False,
                    f"Expected 201, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("Create Bookmark", False, f"Exception: {str(e)}")
            return False

    def test_2_list_bookmarks(self) -> bool:
        """Test GET /api/v1/bookmarks/niches - List all bookmarks."""
        print("=" * 60)
        print("TEST 2: List All Bookmarks")
        print("=" * 60)

        try:
            response = requests.get(BOOKMARKS_ENDPOINT)

            print(f"Status Code: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                data = response.json()

                if "niches" not in data or "total_count" not in data:
                    self.log_test(
                        "List Bookmarks",
                        False,
                        "Missing 'niches' or 'total_count' in response"
                    )
                    return False

                if not isinstance(data["niches"], list):
                    self.log_test(
                        "List Bookmarks",
                        False,
                        f"'niches' should be list, got {type(data['niches'])}"
                    )
                    return False

                bookmark_found = False
                if self.created_bookmark_id:
                    bookmark_found = any(
                        b["id"] == self.created_bookmark_id
                        for b in data["niches"]
                    )

                if self.created_bookmark_id and not bookmark_found:
                    self.log_test(
                        "List Bookmarks",
                        False,
                        f"Created bookmark ID {self.created_bookmark_id} not found in list"
                    )
                    return False

                self.log_test(
                    "List Bookmarks",
                    True,
                    f"Found {data['total_count']} bookmarks, created bookmark present"
                )
                return True
            else:
                self.log_test(
                    "List Bookmarks",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("List Bookmarks", False, f"Exception: {str(e)}")
            return False

    def test_3_get_single_bookmark(self) -> bool:
        """Test GET /api/v1/bookmarks/niches/{id} - Get specific bookmark."""
        print("=" * 60)
        print("TEST 3: Get Single Bookmark")
        print("=" * 60)

        if not self.created_bookmark_id:
            self.log_test("Get Single Bookmark", False, "No bookmark ID available")
            return False

        try:
            url = f"{BOOKMARKS_ENDPOINT}/{self.created_bookmark_id}"
            response = requests.get(url)

            print(f"Status Code: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                data = response.json()

                if data["id"] != self.created_bookmark_id:
                    self.log_test(
                        "Get Single Bookmark",
                        False,
                        f"ID mismatch: expected {self.created_bookmark_id}, got {data['id']}"
                    )
                    return False

                required_fields = ["id", "niche_name", "filters", "created_at", "updated_at"]
                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    self.log_test(
                        "Get Single Bookmark",
                        False,
                        f"Missing fields: {missing_fields}"
                    )
                    return False

                self.log_test(
                    "Get Single Bookmark",
                    True,
                    f"Retrieved bookmark: {data['niche_name']}"
                )
                return True
            else:
                self.log_test(
                    "Get Single Bookmark",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("Get Single Bookmark", False, f"Exception: {str(e)}")
            return False

    def test_4_update_bookmark(self) -> bool:
        """Test PUT /api/v1/bookmarks/niches/{id} - Update bookmark."""
        print("=" * 60)
        print("TEST 4: Update Bookmark")
        print("=" * 60)

        if not self.created_bookmark_id:
            self.log_test("Update Bookmark", False, "No bookmark ID available")
            return False

        try:
            url = f"{BOOKMARKS_ENDPOINT}/{self.created_bookmark_id}"
            update_payload = {
                "niche_name": "Updated - Python Books Advanced",
                "description": "Updated description for testing"
            }

            response = requests.put(url, json=update_payload)

            print(f"Status Code: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                data = response.json()

                if data["niche_name"] != update_payload["niche_name"]:
                    self.log_test(
                        "Update Bookmark",
                        False,
                        f"niche_name not updated: expected '{update_payload['niche_name']}', got '{data['niche_name']}'"
                    )
                    return False

                if data.get("description") != update_payload["description"]:
                    self.log_test(
                        "Update Bookmark",
                        False,
                        f"description not updated: expected '{update_payload['description']}', got '{data.get('description')}'"
                    )
                    return False

                self.log_test(
                    "Update Bookmark",
                    True,
                    f"Updated niche_name to: {data['niche_name']}"
                )
                return True
            else:
                self.log_test(
                    "Update Bookmark",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("Update Bookmark", False, f"Exception: {str(e)}")
            return False

    def test_5_get_filters(self) -> bool:
        """Test GET /api/v1/bookmarks/niches/{id}/filters - Get filters for re-run."""
        print("=" * 60)
        print("TEST 5: Get Bookmark Filters")
        print("=" * 60)

        if not self.created_bookmark_id:
            self.log_test("Get Filters", False, "No bookmark ID available")
            return False

        try:
            url = f"{BOOKMARKS_ENDPOINT}/{self.created_bookmark_id}/filters"
            response = requests.get(url)

            print(f"Status Code: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                data = response.json()

                if "filters" not in data:
                    self.log_test(
                        "Get Filters",
                        False,
                        "Missing 'filters' field in response"
                    )
                    return False

                filters = data["filters"]
                expected_filter_keys = ["bsr_range", "price_range", "min_roi"]

                if not all(key in filters for key in expected_filter_keys):
                    self.log_test(
                        "Get Filters",
                        False,
                        f"Missing expected filter keys. Found: {list(filters.keys())}"
                    )
                    return False

                self.log_test(
                    "Get Filters",
                    True,
                    f"Retrieved filters: {json.dumps(filters)}"
                )
                return True
            else:
                self.log_test(
                    "Get Filters",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("Get Filters", False, f"Exception: {str(e)}")
            return False

    def test_6_delete_bookmark(self) -> bool:
        """Test DELETE /api/v1/bookmarks/niches/{id} - Delete bookmark."""
        print("=" * 60)
        print("TEST 6: Delete Bookmark")
        print("=" * 60)

        if not self.created_bookmark_id:
            self.log_test("Delete Bookmark", False, "No bookmark ID available")
            return False

        try:
            url = f"{BOOKMARKS_ENDPOINT}/{self.created_bookmark_id}"
            response = requests.delete(url)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 204:
                self.log_test(
                    "Delete Bookmark",
                    True,
                    f"Bookmark {self.created_bookmark_id} deleted successfully"
                )
                return True
            else:
                self.log_test(
                    "Delete Bookmark",
                    False,
                    f"Expected 204, got {response.status_code}: {response.text if response.text else 'No content'}"
                )
                return False

        except Exception as e:
            self.log_test("Delete Bookmark", False, f"Exception: {str(e)}")
            return False

    def test_7_verify_deletion(self) -> bool:
        """Test verification that bookmark was deleted."""
        print("=" * 60)
        print("TEST 7: Verify Deletion")
        print("=" * 60)

        if not self.created_bookmark_id:
            self.log_test("Verify Deletion", False, "No bookmark ID available")
            return False

        try:
            url = f"{BOOKMARKS_ENDPOINT}/{self.created_bookmark_id}"
            response = requests.get(url)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 404:
                self.log_test(
                    "Verify Deletion",
                    True,
                    "Bookmark not found (correctly deleted)"
                )
                return True
            elif response.status_code == 200:
                self.log_test(
                    "Verify Deletion",
                    False,
                    "Bookmark still exists after deletion"
                )
                return False
            else:
                self.log_test(
                    "Verify Deletion",
                    False,
                    f"Expected 404, got {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_test("Verify Deletion", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "=" * 60)
        print("BOOKMARKS API TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {BASE_URL}")
        print("=" * 60 + "\n")

        # Run tests in sequence
        self.test_1_create_bookmark()
        self.test_2_list_bookmarks()
        self.test_3_get_single_bookmark()
        self.test_4_update_bookmark()
        self.test_5_get_filters()
        self.test_6_delete_bookmark()
        self.test_7_verify_deletion()

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print("=" * 60)

        if self.test_results["failed"] > 0:
            print("\nFAILED TESTS:")
            for error in self.test_results["errors"]:
                for test_name, message in error.items():
                    print(f"  - {test_name}: {message}")

        print("\n" + "=" * 60)

        if self.test_results["failed"] == 0:
            print("SUCCESS: All tests passed!")
            print("=" * 60)
            return 0
        else:
            print(f"FAILURE: {self.test_results['failed']} test(s) failed")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    tester = BookmarksAPITest()
    exit_code = tester.run_all_tests()
    exit(exit_code)
