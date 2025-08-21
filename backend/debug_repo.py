#!/usr/bin/env python3
"""Debug repository issues quickly."""

import asyncio
from app.core.db import get_db_session
from app.repositories.analysis_repository import AnalysisRepository

async def test_repo():
    """Test if repository works."""
    try:
        async for session in get_db_session():
            repo = AnalysisRepository(session)
            print("✅ Repository created successfully")
            
            # Test simple list
            try:
                page = await repo.list(offset=0, limit=10)
                print(f"✅ Repository list works - {len(page.items)} items")
            except Exception as e:
                print(f"❌ Repository list error: {e}")
            break
            
    except Exception as e:
        print(f"❌ Session error: {e}")

if __name__ == "__main__":
    asyncio.run(test_repo())