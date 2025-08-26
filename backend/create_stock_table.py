"""
Manual table creation for stock_estimate_cache
Simple script to create the table using SQLAlchemy models
"""
import asyncio
import logging
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.db import Base, db_manager
from app.models.stock_estimate import StockEstimateCache
from app.core.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_stock_estimate_table():
    """Create stock estimate cache table manually"""
    try:
        logger.info("Starting stock_estimate_cache table creation...")
        
        # Initialize database manager
        await db_manager.initialize()
        
        # Get the engine for table creation
        engine = db_manager._engine
        if not engine:
            raise RuntimeError("Database engine not initialized")
        
        logger.info("Creating stock_estimate_cache table...")
        
        # Create the specific table using metadata
        async with engine.begin() as conn:
            await conn.run_sync(StockEstimateCache.metadata.create_all)
        
        logger.info("✅ stock_estimate_cache table created successfully")
        
        # Verify table exists
        async with db_manager.session() as session:
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_estimate_cache'"))
            table_exists = result.fetchone()
            
            if table_exists:
                logger.info("✅ Table verification: stock_estimate_cache exists")
            else:
                logger.warning("⚠️  Table verification failed")
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        logger.error(f"Error type: {type(e)}")
        raise
    finally:
        # Clean up database connection
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(create_stock_estimate_table())