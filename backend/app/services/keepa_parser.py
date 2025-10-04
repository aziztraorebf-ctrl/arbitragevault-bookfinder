"""
Keepa API response parser - converts raw Keepa data to structured models.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import logging

from app.models.keepa_models import ProductStatus
from app.core.calculations import VelocityData


logger = logging.getLogger(__name__)


def parse_keepa_product(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse raw Keepa product data into structured format.
    
    Args:
        raw_data: Raw Keepa API response for a single product
        
    Returns:
        Structured product data dict
    """
    try:
        # Basic product info
        product_data = {
            "asin": raw_data.get("asin", ""),
            "title": raw_data.get("title", ""),
            "category": _extract_category(raw_data),
            "brand": raw_data.get("brand", ""),
            "manufacturer": raw_data.get("manufacturer", ""),
            "status": ProductStatus.ACTIVE.value,
            "domain": raw_data.get("domainId", 1)
        }
        
        # Package dimensions (for FBA fee calculation)
        package_data = raw_data.get("packageDimensions", {})
        if package_data:
            product_data.update({
                "package_height": _safe_decimal(package_data.get("height")),
                "package_length": _safe_decimal(package_data.get("length")),
                "package_width": _safe_decimal(package_data.get("width")),
                "package_weight": _safe_decimal(package_data.get("weight"))
            })
        
        # Current pricing and BSR
        current_data = _extract_current_data(raw_data)
        product_data.update(current_data)
        
        # Parse price/BSR history
        history_data = _extract_history_data(raw_data)
        product_data.update(history_data)
        
        # Store raw data for debugging
        product_data["raw_data"] = raw_data
        
        # Metadata
        product_data["parsing_timestamp"] = datetime.now().isoformat()
        product_data["keepa_product_code"] = raw_data.get("productCode")
        
        logger.info(f"Parsed Keepa product: {product_data['asin']}")
        return product_data
        
    except Exception as e:
        logger.error(f"Failed to parse Keepa product data: {e}")
        return {
            "error": f"Parsing failed: {str(e)}",
            "raw_data": raw_data,
            "status": ProductStatus.UNRESOLVED.value
        }


def _extract_category(raw_data: Dict[str, Any]) -> str:
    """Extract product category from Keepa data."""
    # Try multiple fields for category info
    category_fields = [
        raw_data.get("category"),
        raw_data.get("categoryTree", [{}])[-1].get("name") if raw_data.get("categoryTree") else None,
        raw_data.get("productGroup"),
        raw_data.get("binding")
    ]
    
    for field in category_fields:
        if field and isinstance(field, str):
            return field.lower().strip()
    
    return "unknown"


def _extract_current_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract current pricing and availability data.
    
    Uses stats.current[] array for current prices (not csv[] which contains historical data).
    Keepa stats.current[] indices (official Keepa API structure):
      0: AMAZON - Amazon price
      1: NEW - Marketplace New price (3rd party + Amazon)
      2: USED - Used price
      3: SALES - Sales Rank (BSR) - NOT a price!
      4: LISTPRICE - List price
      7: NEW_FBM_SHIPPING - FBM price with shipping
      8: LIGHTNING_DEAL - Lightning Deal price
      10: NEW_FBA - FBA price (3rd party only, excluding Amazon)
      18: BUY_BOX_SHIPPING - Buy Box price with shipping
    
    Reference: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
    """
    current_data = {}
    
    # FIXED: Use stats.current[] for current prices, not csv[] historical arrays
    stats = raw_data.get("stats", {})
    current_array = stats.get("current", [])
    
    if current_array and isinstance(current_array, list) and len(current_array) > 0:
        # Amazon price (index 0)
        if len(current_array) > 0:
            amazon_price = current_array[0]
            if amazon_price and amazon_price != -1:
                current_data["current_amazon_price"] = _keepa_price_to_decimal(amazon_price)
        
        # New/Marketplace price (index 1) - includes both FBM and Amazon
        if len(current_array) > 1:
            new_price = current_array[1]
            if new_price and new_price != -1:
                current_data["current_fbm_price"] = _keepa_price_to_decimal(new_price)
        
        # Used price (index 2)
        if len(current_array) > 2:
            used_price = current_array[2]
            if used_price and used_price != -1:
                current_data["current_used_price"] = _keepa_price_to_decimal(used_price)
        
        # Sales rank (index 3) - BSR is NOT a price, do not convert
        if len(current_array) > 3:
            bsr = current_array[3]
            if bsr and bsr != -1 and isinstance(bsr, (int, float)):
                current_data["current_bsr"] = int(bsr)
        
        # FBA price (index 10) - 3rd party FBA offers only
        if len(current_array) > 10:
            fba_price = current_array[10]
            if fba_price and fba_price != -1:
                current_data["current_fba_price"] = _keepa_price_to_decimal(fba_price)
        
        # Buy Box price with shipping (index 18)
        if len(current_array) > 18:
            buybox_price = current_array[18]
            if buybox_price and buybox_price != -1:
                current_data["current_buybox_price"] = _keepa_price_to_decimal(buybox_price)
    
    # Offers count
    if "offersCount" in raw_data:
        current_data["offers_count"] = raw_data["offersCount"]
    
    # Buybox seller info
    buybox_info = raw_data.get("buyBoxSellerIdHistory")
    if buybox_info:
        current_data["buybox_seller_type"] = _determine_seller_type(buybox_info)
    
    # *** FIX TICKET #001: Determine best current_price from available prices ***
    current_data["current_price"] = _determine_best_current_price(current_data)
    
    return current_data


def _extract_history_data(raw_data: Dict[str, Any], days_back: int = 90) -> Dict[str, Any]:
    """Extract historical price and rank data for calculations."""
    history_data = {}
    
    csv_data = raw_data.get("csv", [])
    # *** FIX TICKET #002: Robust null checking ***
    if not csv_data or not isinstance(csv_data, list):
        logger.warning("CSV data missing or invalid format")
        return history_data
    
    # Calculate cutoff timestamp (Keepa uses minutes since epoch)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    keepa_cutoff = int((cutoff_date.timestamp() * 1000 + 21564000) / 60000)  # Keepa epoch conversion
    
    # Extract BSR history with robust null checking
    if len(csv_data) > 3 and csv_data[3] is not None:
        bsr_history = []
        sales_ranks = csv_data[3]
        
        # *** FIX TICKET #002: Check if sales_ranks is a list and has content ***
        if isinstance(sales_ranks, list) and len(sales_ranks) > 0:
            for i in range(0, len(sales_ranks), 2):
                if i + 1 < len(sales_ranks):
                    timestamp_keepa = sales_ranks[i]
                    rank_value = sales_ranks[i + 1]
                    
                    if timestamp_keepa and timestamp_keepa >= keepa_cutoff and rank_value != -1:
                        try:
                            timestamp = _keepa_timestamp_to_datetime(timestamp_keepa)
                            bsr_history.append((timestamp, int(rank_value)))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid BSR data point: {e}")
                            continue
        
        history_data["bsr_history"] = bsr_history
    else:
        history_data["bsr_history"] = []
    
    # Extract price history (using Amazon price) with robust null checking
    if len(csv_data) > 0 and csv_data[0] is not None:
        price_history = []
        amazon_prices = csv_data[0]
        
        # *** FIX TICKET #002: Check if amazon_prices is a list and has content ***
        if isinstance(amazon_prices, list) and len(amazon_prices) > 0:
            for i in range(0, len(amazon_prices), 2):
                if i + 1 < len(amazon_prices):
                    timestamp_keepa = amazon_prices[i]
                    price_value = amazon_prices[i + 1]
                    
                    if timestamp_keepa and timestamp_keepa >= keepa_cutoff and price_value != -1:
                        try:
                            timestamp = _keepa_timestamp_to_datetime(timestamp_keepa)
                            price = _keepa_price_to_decimal(price_value)
                            if price > 0:
                                price_history.append((timestamp, float(price)))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid price data point: {e}")
                            continue
        
        history_data["price_history"] = price_history
    else:
        history_data["price_history"] = []
    
    return history_data


def create_velocity_data_from_keepa(parsed_product: Dict[str, Any]) -> VelocityData:
    """
    Create VelocityData object from parsed Keepa product data.
    
    Args:
        parsed_product: Product data from parse_keepa_product()
        
    Returns:
        VelocityData object for velocity calculations
    """
    return VelocityData(
        current_bsr=parsed_product.get("current_bsr"),
        bsr_history=parsed_product.get("bsr_history", []),
        price_history=parsed_product.get("price_history", []),
        buybox_history=[],  # TODO: Extract from buyBoxSellerIdHistory if needed
        offers_history=[],  # TODO: Extract from offersCount history if available  
        category=parsed_product.get("category", "books")
    )


def _keepa_price_to_decimal(keepa_price: int) -> Optional[Decimal]:
    """Convert Keepa price (integer cents) to Decimal dollars."""
    if keepa_price is None or keepa_price == -1:
        return None
    
    try:
        # Keepa prices are in cents for US marketplace
        return Decimal(keepa_price) / Decimal("100")
    except:
        return None


def _keepa_timestamp_to_datetime(keepa_timestamp: int) -> datetime:
    """Convert Keepa timestamp to Python datetime."""
    # Keepa timestamps are minutes since their epoch (21564000 minutes before Unix epoch)
    unix_minutes = keepa_timestamp - 21564000
    unix_seconds = unix_minutes * 60
    return datetime.fromtimestamp(unix_seconds)


def _safe_decimal(value: Any) -> Optional[Decimal]:
    """Safely convert value to Decimal."""
    if value is None:
        return None
    
    try:
        return Decimal(str(value))
    except:
        return None


def _determine_seller_type(buybox_history: List[Any]) -> str:
    """Determine current buybox seller type from history."""
    if not buybox_history:
        return "Unknown"
    
    # This would need more detailed parsing of Keepa's buybox data structure
    # For now, return a placeholder
    return "Mixed"


def parse_identifier_resolution(
    identifier: str, 
    identifier_type: str,
    keepa_response: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse identifier resolution result from Keepa response.
    
    Args:
        identifier: Original identifier (ISBN/ASIN)
        identifier_type: Type ("isbn10", "isbn13", "asin")
        keepa_response: Raw Keepa API response
        
    Returns:
        Resolution log data
    """
    try:
        # Check if product was found
        products = keepa_response.get("products", [])
        
        if products and len(products) > 0:
            product = products[0]
            resolved_asin = product.get("asin")
            
            return {
                "original_identifier": identifier,
                "identifier_type": identifier_type,
                "resolved_asin": resolved_asin,
                "resolution_status": "success",
                "keepa_product_code": product.get("productCode"),
                "keepa_domain": keepa_response.get("domainId", 1),
                "error_message": None
            }
        else:
            return {
                "original_identifier": identifier,
                "identifier_type": identifier_type,
                "resolved_asin": None,
                "resolution_status": "not_found",
                "keepa_product_code": None,
                "keepa_domain": keepa_response.get("domainId", 1),
                "error_message": "Product not found in Keepa database"
            }
            
    except Exception as e:
        return {
            "original_identifier": identifier,
            "identifier_type": identifier_type,
            "resolved_asin": None,
            "resolution_status": "error",
            "keepa_product_code": None,
            "keepa_domain": 1,
            "error_message": str(e)
        }


def _determine_best_current_price(current_data: Dict[str, Any]) -> Optional[Decimal]:
    """
    Determine the best current price from available Keepa price sources.
    Priority: Buy Box > FBA > Amazon > Marketplace (FBM)
    
    Args:
        current_data: Extracted current data with various price fields
        
    Returns:
        Best available price as Decimal or None if no valid price found
    """
    # Priority order for price selection
    price_fields = [
        "current_buybox_price",
        "current_fba_price", 
        "current_amazon_price",
        "current_fbm_price"
    ]
    
    for field in price_fields:
        price = current_data.get(field)
        if price is not None and price > 0:
            logger.info(f"Selected {field} as current_price: ${price}")
            return price
    
    # No valid price found
    logger.warning("No valid current price found in any price field")
    return None