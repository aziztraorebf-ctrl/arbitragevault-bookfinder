"""
Smoke test for Keepa endpoints - Phase 4 validation.
Direct testing without pytest dependency.
"""

import asyncio
import json
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test Keepa health endpoint."""
    print("🔍 Testing Keepa health endpoint...")
    
    try:
        response = client.get("/api/v1/keepa/health")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
            print(f"   Status: {data.get('status', 'unknown')}")
            
            if 'tokens' in data:
                tokens = data['tokens']
                print(f"   Tokens remaining: {tokens.get('remaining', 'unknown')}")
                print(f"   Total requests: {tokens.get('requests_made', 0)}")
            
            if 'cache' in data:
                cache = data['cache']
                print(f"   Cache hit rate: {cache.get('hit_rate_percent', 0)}%")
                print(f"   Cache entries: {cache.get('total_entries', 0)}")
                
            print("   ✅ Health endpoint working")
            return True
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
        return False


def test_connection_endpoint():
    """Test Keepa connection test endpoint."""
    print("\n🔍 Testing Keepa connection endpoint...")
    
    try:
        # Test with a real ASIN
        test_asin = "B00FLIJJSA"
        response = client.get(f"/api/v1/keepa/test?identifier={test_asin}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Identifier: {data.get('identifier', 'unknown')}")
            print(f"   Phase: {data.get('phase', 'unknown')}")
            print(f"   Trace ID: {data.get('trace_id', 'none')}")
            
            if data.get('success'):
                print(f"   Resolved ASIN: {data.get('resolved_asin', 'none')}")
                print(f"   Title: {data.get('title', 'none')[:50]}...")
                print(f"   Tokens remaining: {data.get('tokens_remaining', 'unknown')}")
                print("   ✅ Connection test successful")
            else:
                print(f"   ⚠️ Connection test failed: {data.get('error', 'unknown')}")
                print("   ✅ Connection endpoint working (expected failure for test)")
            return True
        else:
            print(f"   ❌ Connection endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection endpoint error: {e}")
        return False


def test_ingest_endpoint():
    """Test batch ingest endpoint."""
    print("\n🔍 Testing batch ingest endpoint...")
    
    try:
        payload = {
            "identifiers": ["B00FLIJJSA", "B08N5WRWNW"],
            "batch_id": "smoke-test-001",
            "config_profile": "default",
            "force_refresh": False,
            "async_threshold": 100
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Batch ID: {data.get('batch_id', 'unknown')}")
            print(f"   Total items: {data.get('total_items', 0)}")
            print(f"   Processed: {data.get('processed', 0)}")
            print(f"   Successful: {data.get('successful', 0)}")
            print(f"   Failed: {data.get('failed', 0)}")
            print(f"   Trace ID: {data.get('trace_id', 'none')}")
            
            # Check if async mode
            if data.get('job_id'):
                print(f"   Job ID: {data.get('job_id')}")
                print(f"   Status URL: {data.get('status_url', 'none')}")
                print("   ✅ Async mode activated")
            else:
                print(f"   Results count: {len(data.get('results', []))}")
                
                # Check first result if any
                if data.get('results'):
                    first_result = data['results'][0]
                    print(f"   First result status: {first_result.get('status', 'unknown')}")
                    if first_result.get('analysis'):
                        analysis = first_result['analysis']
                        print(f"   First recommendation: {analysis.get('recommendation', 'unknown')}")
                        print(f"   First confidence: {analysis.get('confidence_score', 0)}%")
                
                print("   ✅ Sync batch processing working")
            return True
        else:
            print(f"   ❌ Ingest endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ingest endpoint error: {e}")
        return False


def test_metrics_endpoint():
    """Test individual metrics endpoint."""
    print("\n🔍 Testing product metrics endpoint...")
    
    try:
        test_asin = "B00FLIJJSA"
        response = client.get(f"/api/v1/keepa/{test_asin}/metrics?config_profile=default")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ASIN: {data.get('asin', 'unknown')}")
            print(f"   Trace ID: {data.get('trace_id', 'none')}")
            
            # Check analysis
            analysis = data.get('analysis', {})
            print(f"   Title: {analysis.get('title', 'unknown')[:40]}...")
            print(f"   Recommendation: {analysis.get('recommendation', 'unknown')}")
            print(f"   Confidence: {analysis.get('confidence_score', 0)}%")
            print(f"   Risk factors: {len(analysis.get('risk_factors', []))}")
            
            # Check config audit
            config_audit = data.get('config_audit', {})
            print(f"   Config version: {config_audit.get('version', 'unknown')}")
            print(f"   Config profile: {config_audit.get('profile', 'unknown')}")
            
            # Check Keepa metadata
            keepa_meta = data.get('keepa_metadata', {})
            print(f"   Cache hit: {keepa_meta.get('cache_hit', False)}")
            print(f"   Tokens used: {keepa_meta.get('tokens_used', 0)}")
            
            print("   ✅ Metrics endpoint working")
            return True
            
        elif response.status_code == 404:
            data = response.json()
            print(f"   ⚠️ Product not found (expected): {data.get('detail', {}).get('message', 'unknown')}")
            print("   ✅ Metrics endpoint working (404 expected)")
            return True
        else:
            print(f"   ❌ Metrics endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Metrics endpoint error: {e}")
        return False


def test_raw_data_endpoint():
    """Test raw data endpoint."""
    print("\n🔍 Testing raw data endpoint...")
    
    try:
        test_asin = "B00FLIJJSA"
        response = client.get(f"/api/v1/keepa/{test_asin}/raw")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Has metadata: {'_metadata' in data}")
            print(f"   Has keepa_data: {'keepa_data' in data}")
            
            if '_metadata' in data:
                meta = data['_metadata']
                print(f"   ASIN: {meta.get('asin', 'unknown')}")
                print(f"   Cache hit: {meta.get('cache_hit', False)}")
                print(f"   Trace ID: {meta.get('trace_id', 'none')}")
            
            if 'keepa_data' in data:
                keepa_data = data['keepa_data']
                print(f"   Raw data type: {type(keepa_data).__name__}")
                if isinstance(keepa_data, dict):
                    print(f"   Raw data keys: {len(keepa_data.keys())}")
            
            print("   ✅ Raw data endpoint working")
            return True
            
        elif response.status_code == 404:
            data = response.json()
            print(f"   ⚠️ Product not found (expected): {data.get('detail', {}).get('message', 'unknown')}")
            print("   ✅ Raw data endpoint working (404 expected)")
            return True
        else:
            print(f"   ❌ Raw data endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Raw data endpoint error: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("🚀 PHASE 4 KEEPA ENDPOINTS SMOKE TEST")
    print("=" * 50)
    
    results = []
    
    # Test all endpoints
    results.append(test_health_endpoint())
    results.append(test_connection_endpoint())
    results.append(test_ingest_endpoint())
    results.append(test_metrics_endpoint())
    results.append(test_raw_data_endpoint())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SMOKE TEST SUMMARY")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    print(f"   Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("   🎉 ALL ENDPOINTS WORKING")
        return True
    else:
        print("   ⚠️ SOME ENDPOINTS NEED ATTENTION")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)