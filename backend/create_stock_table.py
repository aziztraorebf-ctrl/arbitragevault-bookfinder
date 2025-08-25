"""
Manual table creation for stock_estimate_cache
Simple script to create the table without alembic migration
"""
from app.core.database import engine, Base
from app.models.stock_estimate import StockEstimateCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_stock_estimate_table():
    """Create stock estimate cache table manually"""
    try:
        # Import all models to ensure they're registered
        from app.models import *
        
        logger.info("Creating stock_estimate_cache table...")
        
        # Create only the stock estimate table
        StockEstimateCache.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ stock_estimate_cache table created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise

if __name__ == "__main__":
    create_stock_estimate_table()