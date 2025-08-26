"""
Manual table creation for stock_estimate_cache
Simple script to create the table without alembic migration
"""
import asyncio
import logging
from sqlalchemy import text
from app.core.db import get_async_session
from app.models.stock_estimate import StockEstimateCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_stock_estimate_table():
    """Create stock estimate cache table manually"""
    try:
        logger.info("Creating stock_estimate_cache table...")
        
        # Create the table using raw SQL since we're in async context
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_estimate_cache (
            id SERIAL PRIMARY KEY,
            asin VARCHAR(20) NOT NULL,
            price_target DECIMAL(10,2),
            estimated_units INTEGER NOT NULL DEFAULT 0,
            total_offers INTEGER NOT NULL DEFAULT 0,
            fba_offers INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL,
            UNIQUE(asin, price_target)
        );
        """
        
        async for session in get_async_session():
            await session.execute(text(create_table_sql))
            await session.commit()
            break  # Only need one session
        
        logger.info("✅ stock_estimate_cache table created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_stock_estimate_table())