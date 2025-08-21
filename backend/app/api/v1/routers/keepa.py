"""Keepa integration endpoints - Phase 2 implementation."""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Dict, Any

from app.services.keepa_service import KeepaService, get_keepa_service

router = APIRouter()


@router.get("/health")
async def keepa_health_check(
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> Dict[str, Any]:
    """
    Check Keepa API health and service status.
    """
    try:
        async with keepa_service:
            health_status = await keepa_service.health_check()
            cache_stats = keepa_service.get_cache_stats()
            
            return {
                "service": "keepa",
                "timestamp": "2024-08-17T18:30:00Z",
                "health": health_status,
                "cache": cache_stats,
                "concurrency": keepa_service.concurrency
            }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Keepa service unavailable: {str(e)}")


@router.get("/test")
async def test_keepa_connection(
    identifier: str = Query(..., description="ASIN or ISBN to test with Keepa API"),
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> Dict[str, Any]:
    """
    Test Keepa API connection with given identifier.
    
    PHASE 2 IMPLEMENTATION - Real Keepa API integration.
    """
    # Validate identifier format (basic)
    cleaned_id = identifier.strip().replace("-", "").replace(" ", "")
    
    if not (len(cleaned_id) in [10, 13] or (len(cleaned_id) == 10 and cleaned_id.isalnum())):
        return {
            "success": False,
            "error": "Invalid ASIN/ISBN format",
            "identifier": identifier
        }
    
    try:
        async with keepa_service:
            # Test actual Keepa API call
            product_data = await keepa_service.get_product_data(cleaned_id)
            
            if product_data is None:
                return {
                    "success": False,
                    "error": "Product not found in Keepa",
                    "identifier": cleaned_id
                }
            
            # Extract basic info for test response
            asin = product_data.get('asin', 'unknown')
            title = product_data.get('title', 'Unknown Title')
            
            return {
                "success": True,
                "identifier": cleaned_id,
                "resolved_asin": asin,
                "title": title,
                "message": "Keepa API connection successful",
                "phase": "PHASE_2_REAL",
                "has_price_data": 'csv' in product_data,
                "has_stats": 'stats' in product_data
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Keepa API error: {str(e)}",
            "identifier": cleaned_id
        }