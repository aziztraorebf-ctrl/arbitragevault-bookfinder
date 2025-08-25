"""
Stock Estimate API Router
Simple endpoints for stock availability estimation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.keepa_integration import get_keepa_service
from app.services.stock_estimate_service import StockEstimateService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["Stock Estimate"])


def get_stock_estimate_service(
    db: Session = Depends(get_db),
    keepa_service = Depends(get_keepa_service)
) -> StockEstimateService:
    """Dependency injection for StockEstimateService"""
    return StockEstimateService(db, keepa_service)


@router.get("/{asin}/stock-estimate")
async def get_stock_estimate(
    asin: str,
    price_target: Optional[float] = Query(None, description="Target price for filtering relevant offers"),
    service: StockEstimateService = Depends(get_stock_estimate_service)
):
    """
    Get stock availability estimate for a single ASIN
    
    Returns cached result if available and not expired (24h TTL),
    otherwise fetches fresh data from Keepa API.
    
    Args:
        asin: Amazon ASIN identifier
        price_target: Optional target price for filtering offers in price range
    
    Returns:
        Stock estimate with FBA/MFN offer counts and availability estimate
    """
    try:
        if not asin or len(asin.strip()) < 8:
            raise HTTPException(status_code=400, detail="Invalid ASIN format")
        
        asin = asin.strip().upper()
        
        logger.info(f"Stock estimate request for ASIN: {asin}, price_target: {price_target}")
        
        result = service.get_stock_estimate(asin, price_target)
        
        # Check if result indicates error
        if result.get("source") == "error":
            logger.error(f"Stock estimate failed for {asin}: {result.get('error')}")
            raise HTTPException(
                status_code=504,
                detail=f"Unable to get stock estimate: {result.get('error', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in stock estimate for {asin}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting stock estimate"
        )


@router.get("/stock-estimate/health")
async def stock_estimate_health():
    """
    Health check endpoint for stock estimate service
    """
    return {
        "service": "stock_estimate",
        "status": "healthy",
        "version": "v1.0.0",
        "endpoints": {
            "single": "GET /api/v1/products/{asin}/stock-estimate",
            "health": "GET /api/v1/products/stock-estimate/health"
        }
    }