#!/usr/bin/env python3
"""Test script for Phase 1 endpoints."""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_endpoints():
    """Test the newly created endpoints."""
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        
        print("🔍 Testing Phase 1 Endpoints")
        print("=" * 40)
        
        # Test 1: Health check
        print("1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    print("   ✅ Health check OK")
                else:
                    print("   ❌ Health check failed")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
        
        # Test 2: Analyses list (empty)
        print("\n2. Testing analyses list...")
        try:
            async with session.get(f"{base_url}/analyses") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Analyses list OK - Total: {data.get('total', 0)}")
                else:
                    print("   ❌ Analyses list failed")
        except Exception as e:
            print(f"   ❌ Analyses endpoint error: {e}")
        
        # Test 3: Batches list (empty)
        print("\n3. Testing batches list...")
        try:
            async with session.get(f"{base_url}/batches") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Batches list OK - Total: {data.get('total', 0)}")
                else:
                    print("   ❌ Batches list failed")
        except Exception as e:
            print(f"   ❌ Batches endpoint error: {e}")
        
        # Test 4: Keepa stub
        print("\n4. Testing Keepa stub...")
        try:
            async with session.get(f"{base_url}/keepa/test?isbn=9780134685991") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Keepa stub OK - Phase: {data.get('phase', 'unknown')}")
                else:
                    print("   ❌ Keepa stub failed")
        except Exception as e:
            print(f"   ❌ Keepa endpoint error: {e}")
        
        # Test 5: OpenAPI docs
        print("\n5. Testing OpenAPI docs...")
        try:
            async with session.get("http://localhost:8000/openapi.json") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    print("   ✅ OpenAPI docs available")
                else:
                    print("   ❌ OpenAPI docs failed")
        except Exception as e:
            print(f"   ❌ OpenAPI docs error: {e}")

if __name__ == "__main__":
    print("🚀 Phase 1 Endpoint Tests")
    print("Make sure to start the FastAPI server first:")
    print("uv run python app/main.py")
    print()
    
    asyncio.run(test_endpoints())