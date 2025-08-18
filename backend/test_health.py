#!/usr/bin/env python
"""Quick health check test script."""

import asyncio
import httpx
from app.main import app

async def test_health_endpoints():
    """Test health endpoints."""
    from httpx import ASGITransport
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test liveness
        response = await client.get("/api/v1/health/live")
        print(f"Liveness: {response.status_code} - {response.json()}")
        
        # Test readiness  
        response = await client.get("/api/v1/health/ready")
        print(f"Readiness: {response.status_code} - {response.json()}")
        
        # Test root endpoint
        response = await client.get("/")
        print(f"Root: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_health_endpoints())