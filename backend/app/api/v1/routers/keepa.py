"""Keepa integration endpoints (stub for Phase 2)."""

from fastapi import APIRouter, Query
from typing import Dict, Any

router = APIRouter()


@router.get("/test")
async def test_keepa_connection(
    isbn: str = Query(..., description="ISBN/ASIN to test with Keepa API")
) -> Dict[str, Any]:
    """
    Test Keepa API connection with given ISBN/ASIN.
    
    STUB IMPLEMENTATION - Returns mock data for Phase 1.
    Will be replaced with real Keepa integration in Phase 2.
    """
    # Validate ISBN format (basic)
    cleaned_isbn = isbn.strip().replace("-", "").replace(" ", "")
    
    if not (len(cleaned_isbn) in [10, 13] and cleaned_isbn.isalnum()):
        return {
            "success": False,
            "error": "Invalid ISBN/ASIN format",
            "isbn": isbn
        }
    
    # Mock successful response
    return {
        "success": True,
        "isbn": cleaned_isbn,
        "message": "Keepa connection stub - ready for Phase 2 integration",
        "mock_data": {
            "title": f"Sample Book for {cleaned_isbn}",
            "current_price": 24.99,
            "sales_rank": 15432,
            "availability": "In Stock"
        },
        "phase": "PHASE_1_STUB"
    }