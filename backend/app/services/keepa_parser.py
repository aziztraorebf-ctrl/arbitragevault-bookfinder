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
    """Extract current pricing and availability data."""
    current_data = {}
    
    # Current prices from 'csv' field (last values in arrays)
    csv_data = raw_data.get("csv", [])
    if csv_data and len(csv_data) > 0:
        # Keepa CSV format: each element is [timestamp_minutes, price_or_rank]
        # Different indexes represent different data types
        
        # Amazon price (index 0)
        amazon_prices = csv_data[0] if len(csv_data) > 0 else []
        if amazon_prices and len(amazon_prices) >= 2:
            current_data["current_amazon_price"] = _keepa_price_to_decimal(amazon_prices[-1])
        
        # Marketplace (FBM) price (index 1) 
        marketplace_prices = csv_data[1] if len(csv_data) > 1 else []
        if marketplace_prices and len(marketplace_prices) >= 2:
            current_data["current_fbm_price"] = _keepa_price_to_decimal(marketplace_prices[-1])
        
        # Sales rank (index 3)
        sales_ranks = csv_data[3] if len(csv_data) > 3 else []
        if sales_ranks and len(sales_ranks) >= 2:
            rank_value = sales_ranks[-1]
            if rank_value != -1:  # Keepa uses -1 for no data
                current_data["current_bsr"] = int(rank_value)
        
        # FBA price (index 7)
        fba_prices = csv_data[7] if len(csv_data) > 7 else []
        if fba_prices and len(fba_prices) >= 2:
            current_data["current_fba_price"] = _keepa_price_to_decimal(fba_prices[-1])
        
        # Buy Box price (index 18) 
        buybox_prices = csv_data[18] if len(csv_data) > 18 else []
        if buybox_prices and len(buybox_prices) >= 2:
            current_data["current_buybox_price"] = _keepa_price_to_decimal(buybox_prices[-1])
    
    # Offers count
    if "offersCount" in raw_data:
        current_data["offers_count"] = raw_data["offersCount"]
    
    # Buybox seller info
    buybox_info = raw_data.get("buyBoxSellerIdHistory")
    if buybox_info:
        current_data["buybox_seller_type"] = _determine_seller_type(buybox_info)
    
    return current_data


def _extract_history_data(raw_data: Dict[str, Any], days_back: int = 90) -> Dict[str, Any]:
    """Extract historical price and rank data for calculations."""
    history_data = {}
    
    csv_data = raw_data.get("csv", [])
    if not csv_data:
        return history_data
    
    # Calculate cutoff timestamp (Keepa uses minutes since epoch)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    keepa_cutoff = int((cutoff_date.timestamp() * 1000 + 21564000) / 60000)  # Keepa epoch conversion
    
    # Extract BSR history
    if len(csv_data) > 3:
        bsr_history = []
        sales_ranks = csv_data[3]
        
        for i in range(0, len(sales_ranks), 2):
            if i + 1 < len(sales_ranks):
                timestamp_keepa = sales_ranks[i]
                rank_value = sales_ranks[i + 1]
                
                if timestamp_keepa >= keepa_cutoff and rank_value != -1:
                    timestamp = _keepa_timestamp_to_datetime(timestamp_keepa)
                    bsr_history.append((timestamp, int(rank_value)))
        
        history_data["bsr_history"] = bsr_history
    
    # Extract price history (using Amazon price)
    if len(csv_data) > 0:
        price_history = []
        amazon_prices = csv_data[0]
        
        for i in range(0, len(amazon_prices), 2):
            if i + 1 < len(amazon_prices):
                timestamp_keepa = amazon_prices[i]
                price_value = amazon_prices[i + 1]
                
                if timestamp_keepa >= keepa_cutoff and price_value != -1:
                    timestamp = _keepa_timestamp_to_datetime(timestamp_keepa)
                    price = _keepa_price_to_decimal(price_value)
                    if price > 0:
                        price_history.append((timestamp, float(price)))
        
        history_data["price_history"] = price_history
    
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