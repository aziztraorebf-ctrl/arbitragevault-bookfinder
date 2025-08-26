"""
Quick script to verify stock_estimate_cache table structure
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.db import db_manager

async def check_table():
    await db_manager.initialize()
    async with db_manager.session() as session:
        result = await session.execute(text('PRAGMA table_info(stock_estimate_cache)'))
        columns = result.fetchall()
        print('✅ stock_estimate_cache table structure:')
        for col in columns:
            print(f'  {col[1]} ({col[2]}) - {"NOT NULL" if col[3] else "NULLABLE"} - Default: {col[4]}')
    await db_manager.close()

asyncio.run(check_table())