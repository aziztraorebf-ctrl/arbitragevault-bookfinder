"""
Strategic Views Router
Endpoints pour les différentes vues stratégiques d'analyse
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.db import get_db_session
from app.services.sales_velocity_service import get_sales_velocity_service, SalesVelocityService
from app.services.keepa_service import get_keepa_service, KeepaService
from app.services.strategic_views_service import StrategicViewsService
from app.schemas.analysis import StrategicViewResponseSchema
import logging

logger = logging.getLogger(__name__)

class ViewType(str, Enum):
    """Types de vues stratégiques disponibles"""
    PROFIT_HUNTER = "profit-hunter"      # Vue originale - Focus ROI
    VELOCITY = "velocity"                # Vue originale - Focus rotation
    CASHFLOW_HUNTER = "cashflow-hunter"  # NOUVEAU - Profit × Velocity
    VOLUME_PLAYER = "volume-player"      # NOUVEAU - Focus volume pur
    BALANCED_SCORE = "balanced-score"    # NOUVEAU - Score composite

router = APIRouter(prefix="/api/v1/views", tags=["Strategic Views"])

# Dependency injection for StrategicViewsService
def get_strategic_views_service() -> StrategicViewsService:
    """Get StrategicViewsService instance."""
    return StrategicViewsService()


@router.get("/{view_type}")
async def get_strategic_view(
    view_type: ViewType,
    asins: str = Query(..., description="Comma-separated list of ASINs to analyze"),
    limit: int = Query(50, le=100, description="Max results to return"),
    min_roi: float = Query(0, description="Minimum ROI filter"),
    min_sales: int = Query(0, description="Minimum monthly sales filter"),
    velocity_tiers: Optional[str] = Query(None, description="Comma-separated velocity tiers to include"),
    db: AsyncSession = Depends(get_db_session),
    velocity_service: SalesVelocityService = Depends(get_sales_velocity_service),
    keepa_service: KeepaService = Depends(get_keepa_service)
):
    """
    Get strategic view of products with velocity-enhanced analysis
    
    Enrichit les données produit avec estimations de ventes et les trie selon la vue choisie
    """
    try:
        # Parse ASINs
        asin_list = [asin.strip().upper() for asin in asins.split(',') if asin.strip()]
        if not asin_list:
            raise HTTPException(status_code=400, detail="At least one ASIN required")
        
        if len(asin_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 ASINs per request")
        
        logger.info(f"Strategic view {view_type} requested for {len(asin_list)} ASINs")
        
        # Parse velocity tiers filter
        tier_filter = None
        if velocity_tiers:
            tier_filter = [tier.strip().upper() for tier in velocity_tiers.split(',')]
        
        # Analyze each ASIN with velocity data
        enriched_results = []
        
        for asin in asin_list:
            try:
                # Get velocity data from Keepa
                velocity_data = await keepa_service.get_sales_velocity_data(asin)
                
                # Get real product analysis from Keepa API
                basic_analysis = await _get_real_product_analysis(asin, keepa_service)
                
                # Enrich with velocity analysis
                velocity_analysis = velocity_service.analyze_product_velocity(
                    velocity_data, 
                    basic_analysis.get('roi_percent', 0),
                    basic_analysis.get('profit_net', 0)
                )
                
                # Combine results
                combined_result = {
                    **basic_analysis,
                    **velocity_analysis,
                    "view_type": view_type
                }
                
                # Apply filters
                if _passes_filters(combined_result, min_roi, min_sales, tier_filter):
                    enriched_results.append(combined_result)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze ASIN {asin}: {e}")
                continue
        
        # Sort by strategic view
        sorted_results = _sort_by_strategic_view(enriched_results, view_type)
        
        # Limit results
        final_results = sorted_results[:limit]
        
        # Generate response
        return {
            "view_type": view_type,
            "total_analyzed": len(asin_list),
            "results_found": len(enriched_results), 
            "results_returned": len(final_results),
            "results": final_results,
            "metadata": _get_view_metadata(view_type),
            "filters_applied": {
                "min_roi": min_roi,
                "min_sales": min_sales,
                "velocity_tiers": tier_filter
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in strategic view {view_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/")
async def list_available_views():
    """List all available strategic views with descriptions"""
    return {
        "available_views": [
            {
                "type": "profit-hunter",
                "name": "Profit Hunter",
                "description": "Highest ROI opportunities - maximize margins",
                "best_for": "High margin focus, quality over quantity",
                "icon": "💰"
            },
            {
                "type": "velocity", 
                "name": "Velocity",
                "description": "Fastest moving products - maximize turnover",
                "best_for": "Quick inventory turnover, cashflow focus",
                "icon": "⚡"
            },
            {
                "type": "cashflow-hunter",
                "name": "Cashflow Hunter", 
                "description": "Best profit × velocity combination",
                "best_for": "Fast cashflow generation, balanced approach",
                "icon": "💸"
            },
            {
                "type": "volume-player",
                "name": "Volume Player",
                "description": "Highest sales volume products",
                "best_for": "Volume-based strategies, market share",
                "icon": "📊"
            },
            {
                "type": "balanced-score",
                "name": "Balanced Score",
                "description": "Optimal ROI × velocity × profit composite",
                "best_for": "Balanced portfolio, diversified risk",
                "icon": "⚖️"
            }
        ]
    }


def _sort_by_strategic_view(results: List[Dict], view_type: ViewType) -> List[Dict]:
    """Sort results according to strategic view logic"""
    try:
        if view_type == ViewType.PROFIT_HUNTER:
            # Sort by ROI descending
            return sorted(results, key=lambda x: x.get('roi_percent', 0), reverse=True)
            
        elif view_type == ViewType.VELOCITY:
            # Sort by monthly sales descending
            return sorted(results, key=lambda x: x.get('sales_estimate_30d', 0), reverse=True)
            
        elif view_type == ViewType.CASHFLOW_HUNTER:
            # Sort by cashflow potential (profit × sales)
            return sorted(results, key=lambda x: x.get('cashflow_potential', 0), reverse=True)
            
        elif view_type == ViewType.VOLUME_PLAYER:
            # Sort by sales volume
            return sorted(results, key=lambda x: x.get('sales_estimate_30d', 0), reverse=True)
            
        elif view_type == ViewType.BALANCED_SCORE:
            # Sort by opportunity score  
            return sorted(results, key=lambda x: x.get('opportunity_score', 0), reverse=True)
        
        # Default fallback
        return results
        
    except Exception as e:
        logger.error(f"Error sorting by view type {view_type}: {e}")
        return results


def _passes_filters(result: Dict, min_roi: float, min_sales: int, tier_filter: Optional[List[str]]) -> bool:
    """Check if result passes all filters"""
    try:
        # ROI filter
        if result.get('roi_percent', 0) < min_roi:
            return False
            
        # Sales filter
        if result.get('sales_estimate_30d', 0) < min_sales:
            return False
            
        # Velocity tier filter
        if tier_filter and result.get('velocity_tier', 'UNKNOWN') not in tier_filter:
            return False
            
        return True
        
    except Exception:
        return False


def _get_view_metadata(view_type: ViewType) -> Dict[str, Any]:
    """Get metadata for strategic view"""
    metadata = {
        ViewType.PROFIT_HUNTER: {
            "sorting_criteria": "ROI percentage (descending)",
            "recommended_for": "Investors seeking high margins and quality opportunities",
            "strategy_focus": "Quality over quantity",
            "typical_use_case": "Limited capital, focus on best margin deals"
        },
        ViewType.VELOCITY: {
            "sorting_criteria": "Monthly sales estimate (descending)",
            "recommended_for": "Cashflow-focused investors needing quick turnover",
            "strategy_focus": "Speed and volume",
            "typical_use_case": "Ample capital, need fast inventory movement"
        },
        ViewType.CASHFLOW_HUNTER: {
            "sorting_criteria": "Profit × velocity combination",
            "recommended_for": "Balanced investors wanting best of both worlds",
            "strategy_focus": "Optimized cashflow generation",
            "typical_use_case": "Medium capital, balanced risk/reward approach"
        },
        ViewType.VOLUME_PLAYER: {
            "sorting_criteria": "Pure sales volume",
            "recommended_for": "Volume-focused strategies and market share building",
            "strategy_focus": "Market presence and volume",
            "typical_use_case": "Large capital, brand building, market dominance"
        },
        ViewType.BALANCED_SCORE: {
            "sorting_criteria": "Composite opportunity score (ROI × √velocity × profit)",
            "recommended_for": "Strategic investors wanting optimal overall opportunities",
            "strategy_focus": "Mathematical optimization",
            "typical_use_case": "Data-driven investment decisions, portfolio optimization"
        }
    }
    
    return metadata.get(view_type, {
        "sorting_criteria": "Default sorting",
        "recommended_for": "General use",
        "strategy_focus": "Balanced",
        "typical_use_case": "Standard analysis"
    })


async def _get_real_product_analysis(asin: str, keepa_service: KeepaService) -> Dict[str, Any]:
    """
    Get real product analysis using Keepa API data
    
    Calculates ROI, profit estimates from actual marketplace data
    """
    try:
        # Get real product data from Keepa
        product_data = await keepa_service.get_product_data(asin)
        
        if not product_data:
            logger.warning(f"No Keepa data available for {asin}")
            return _create_empty_analysis(asin)
        
        # Extract pricing data from Keepa response
        title = product_data.get('title', f'Product {asin}')
        current_prices = product_data.get('csv', {})
        
        # Extract current Buy Box price (Keepa index 18 = Buy Box)
        # Note: Keepa prices are in cents (pennies)
        buy_box_price_cents = None
        new_price_cents = None
        
        # Try to get current Buy Box price
        if current_prices and len(current_prices) > 18:
            buy_box_price_cents = current_prices[18][-1] if current_prices[18] else None
            
        # Fallback to New price (index 0) if Buy Box not available
        if not buy_box_price_cents and current_prices and len(current_prices) > 0:
            new_price_cents = current_prices[0][-1] if current_prices[0] else None
            buy_box_price_cents = new_price_cents
        
        # Convert from cents to dollars
        current_price = buy_box_price_cents / 100.0 if buy_box_price_cents else 0
        
        # Calculate basic profit analysis (using standard FBA fees estimation)
        if current_price > 0:
            # Estimate FBA fees (roughly 15% + $3 for books)
            estimated_fees = (current_price * 0.15) + 3.0
            
            # Estimate buy price (current price minus expected margin) 
            estimated_buy_price = current_price * 0.7  # Assume can buy at 70% of sell price
            
            # Calculate profit
            profit_net = current_price - estimated_fees - estimated_buy_price
            roi_percent = (profit_net / estimated_buy_price * 100) if estimated_buy_price > 0 else 0
        else:
            estimated_buy_price = 0
            profit_net = 0
            roi_percent = 0
        
        # Extract category information
        category_info = product_data.get('categoryTree', [])
        category = 'Books'  # Default
        if category_info:
            # Get main category name
            for cat in category_info:
                if cat.get('name'):
                    category = cat['name']
                    break
        
        # Extract BSR
        current_bsr = product_data.get('salesRank', 0)
        
        return {
            "asin": asin,
            "title": title,
            "buy_price": round(estimated_buy_price, 2),
            "sell_price": round(current_price, 2),
            "roi_percent": round(roi_percent, 1),
            "profit_net": round(profit_net, 2),
            "current_bsr": current_bsr,
            "category": category,
            "source": "keepa_api",
            "analysis_metadata": {
                "buy_box_available": buy_box_price_cents is not None,
                "price_source": "buy_box" if buy_box_price_cents else "new",
                "fee_estimation": "15% + $3 FBA standard"
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing real data for {asin}: {e}")
        return _create_empty_analysis(asin)


def _create_empty_analysis(asin: str) -> Dict[str, Any]:
    """Create empty analysis structure for failed lookups"""
    return {
        "asin": asin,
        "title": f"Unknown Product {asin}",
        "buy_price": 0,
        "sell_price": 0,
        "roi_percent": 0,
        "profit_net": 0,
        "current_bsr": 0,
        "category": "Unknown",
        "source": "no_data"
    }


@router.get("/{view_type}/target-prices")
async def get_strategic_view_with_target_prices(
    view_type: ViewType,
    asins: str = Query(..., description="Comma-separated list of ASINs to analyze"),
    limit: int = Query(20, le=50, description="Max results to return"),
    include_calculation_details: bool = Query(False, description="Include detailed calculation breakdown"),
    strategic_service: StrategicViewsService = Depends(get_strategic_views_service),
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> StrategicViewResponseSchema:
    """
    Get strategic view with target price calculations for each product.
    
    This endpoint enriches product analysis with target selling prices based on 
    strategic view ROI targets and provides achievability assessment.
    """
    try:
        # Parse ASINs
        asin_list = [asin.strip().upper() for asin in asins.split(',') if asin.strip()]
        if not asin_list:
            raise HTTPException(status_code=400, detail="At least one ASIN required")
        
        if len(asin_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 ASINs per request for target price analysis")
        
        logger.info(f"Target price analysis for view {view_type} with {len(asin_list)} ASINs")
        
        # Get product data for all ASINs
        products_data = []
        
        for asin in asin_list:
            try:
                # Get real product data from Keepa
                product_analysis = await _get_real_product_analysis(asin, keepa_service)
                
                # Convert strategic view type to our service format
                view_name_mapping = {
                    ViewType.PROFIT_HUNTER: "profit_hunter",
                    ViewType.VELOCITY: "velocity",
                    ViewType.CASHFLOW_HUNTER: "cashflow_hunter",
                    ViewType.BALANCED_SCORE: "balanced_score",
                    ViewType.VOLUME_PLAYER: "volume_player"
                }
                
                view_name = view_name_mapping.get(view_type, "balanced_score")
                
                # Prepare product data for target price calculation
                product_data = {
                    "id": asin,
                    "isbn_or_asin": asin,
                    "buy_price": product_analysis.get("buy_price", 0),
                    "current_price": product_analysis.get("buy_price", 0),
                    "fba_fee": 3.50,  # Standard book FBA fee estimate
                    "buybox_price": product_analysis.get("sell_price", 0),
                    "referral_fee_rate": 0.15,  # Default books rate
                    "storage_fee": 0.50,  # Monthly storage estimate
                    "roi_percentage": product_analysis.get("roi_percent", 0),
                    "velocity_score": 0.70,  # Placeholder
                    "profit_estimate": product_analysis.get("profit_net", 0),
                    "competition_level": "MEDIUM",  # Placeholder
                    "price_volatility": 0.20,  # Placeholder
                    "demand_consistency": 0.80,  # Placeholder
                    "data_confidence": 0.85  # Placeholder
                }
                
                products_data.append(product_data)
                
            except Exception as e:
                logger.warning(f"Failed to analyze ASIN {asin} for target price: {e}")
                continue
        
        # Get strategic view with target prices
        strategic_view_result = strategic_service.get_strategic_view_with_target_prices(
            view_name, products_data
        )
        
        # Filter calculation details if not requested
        if not include_calculation_details:
            for product in strategic_view_result["products"]:
                if "target_price_result" in product and isinstance(product["target_price_result"], dict):
                    if "calculation_details" in product["target_price_result"]:
                        product["target_price_result"]["calculation_details"] = {
                            "details_available": True,
                            "request_with_include_calculation_details": "true"
                        }
        
        # Limit results
        strategic_view_result["products"] = strategic_view_result["products"][:limit]
        strategic_view_result["products_count"] = len(strategic_view_result["products"])
        
        # Add metadata for API response
        strategic_view_result["api_metadata"] = {
            "requested_asins": len(asin_list),
            "processed_products": len(products_data),
            "returned_products": len(strategic_view_result["products"]),
            "view_type": view_type,
            "calculation_details_included": include_calculation_details
        }
        
        return strategic_view_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in target price analysis for view {view_type}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Target price analysis failed: {str(e)}"
        )