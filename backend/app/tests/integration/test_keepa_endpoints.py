"""
Integration tests for Keepa API endpoints - Phase 4.
Tests real API interactions with multiple ASINs and configuration profiles.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.main import app

client = TestClient(app)

# Test data - Real ASINs for different scenarios
TEST_ASINS = {
    "book_textbook": "B00FLIJJSA",  # Programming textbook
    "book_fiction": "B08N5WRWNW",  # Popular fiction
    "book_reference": "B07FNW9FGJ",  # Reference manual
    "book_rare": "B0001X7HVE",     # Rare/OOP book
    "isbn_standard": "9780134685991",  # Standard textbook ISBN
    "isbn_invalid": "1234567890123"    # Invalid ISBN
}

CONFIG_PROFILES = {
    "conservative": {
        "roi": {"target_roi_percent": 40, "buffer_percent": 8},
        "velocity": {"min_velocity_score": 60}
    },
    "neutral": {
        "roi": {"target_roi_percent": 30, "buffer_percent": 6}, 
        "velocity": {"min_velocity_score": 50}
    },
    "aggressive": {
        "roi": {"target_roi_percent": 20, "buffer_percent": 4},
        "velocity": {"min_velocity_score": 40}
    }
}


class TestKeepaHealthEndpoint:
    """Test enhanced health endpoint with observability metrics."""
    
    def test_health_check_success(self):
        """Test successful health check with metrics."""
        response = client.get("/api/v1/keepa/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "service" in data
        assert data["service"] == "keepa"
        assert "timestamp" in data
        assert "tokens" in data
        assert "cache" in data
        assert "circuit_breaker" in data
        assert "performance" in data
        
        # Verify token metrics
        tokens = data["tokens"]
        assert "remaining" in tokens
        assert "total_used" in tokens
        assert "requests_made" in tokens
        
        # Verify cache metrics
        cache = data["cache"]
        assert "hit_rate_percent" in cache
        assert "total_entries" in cache


class TestKeepaTestConnection:
    """Test connection testing endpoint."""
    
    def test_valid_asin_connection(self):
        """Test connection with valid ASIN."""
        response = client.get(f"/api/v1/keepa/test?identifier={TEST_ASINS['book_textbook']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "trace_id" in data
        assert "phase" in data
        assert data["phase"] == "PHASE_4_COMPLETE"
        
        if data["success"]:
            assert "resolved_asin" in data
            assert "title" in data
            assert "tokens_remaining" in data
    
    def test_invalid_identifier_format(self):
        """Test with invalid identifier format."""
        response = client.get("/api/v1/keepa/test?identifier=INVALID123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid ASIN/ISBN format" in data["error"]
        assert "trace_id" in data


class TestIngestBatchEndpoint:
    """Test batch ingestion endpoint with various scenarios."""
    
    def test_small_batch_sync_processing(self):
        """Test synchronous processing for small batch."""
        payload = {
            "identifiers": [
                TEST_ASINS["book_textbook"],
                TEST_ASINS["book_fiction"]
            ],
            "batch_id": "test-batch-001",
            "config_profile": "neutral",
            "async_threshold": 100
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sync response structure
        assert data["batch_id"] == "test-batch-001"
        assert data["total_items"] == 2
        assert data["processed"] == data["total_items"]
        assert data["job_id"] is None  # Sync mode
        assert data["status_url"] is None
        assert "trace_id" in data
        assert len(data["results"]) == 2
        
        # Verify result structure
        for result in data["results"]:
            assert "identifier" in result
            assert "status" in result
            assert result["status"] in ["success", "error", "not_found"]
            
            if result["status"] == "success":
                assert result["asin"] is not None
                assert result["analysis"] is not None
                assert "roi" in result["analysis"]
                assert "velocity" in result["analysis"]
                assert "recommendation" in result["analysis"]
    
    def test_large_batch_async_mode(self):
        """Test async mode for large batch."""
        # Create batch with 101 items to trigger async mode
        identifiers = [TEST_ASINS["book_textbook"]] * 101
        
        payload = {
            "identifiers": identifiers,
            "async_threshold": 100
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify async response
        assert data["total_items"] == 101
        assert data["processed"] == 0  # Not processed yet
        assert data["job_id"] is not None
        assert data["status_url"] is not None
        assert "/jobs/" in data["status_url"]
    
    def test_batch_with_mixed_results(self):
        """Test batch with valid and invalid identifiers."""
        payload = {
            "identifiers": [
                TEST_ASINS["book_textbook"],  # Should work
                "INVALID123",                 # Should fail
                TEST_ASINS["isbn_invalid"]    # Should fail
            ],
            "config_profile": "conservative"
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_items"] == 3
        assert data["processed"] == 3
        assert data["successful"] + data["failed"] == 3
        
        # Check individual results
        success_count = sum(1 for r in data["results"] if r["status"] == "success")
        error_count = sum(1 for r in data["results"] if r["status"] == "error")
        
        assert success_count == data["successful"]
        assert error_count + sum(1 for r in data["results"] if r["status"] == "not_found") == data["failed"]


class TestProductMetricsEndpoint:
    """Test individual product metrics endpoint."""
    
    def test_get_metrics_success(self):
        """Test successful metrics retrieval."""
        asin = TEST_ASINS["book_textbook"]
        response = client.get(f"/api/v1/keepa/{asin}/metrics?config_profile=neutral")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            assert data["asin"] == asin.upper()
            assert "analysis" in data
            assert "config_audit" in data
            assert "keepa_metadata" in data
            assert "trace_id" in data
            
            # Verify analysis structure
            analysis = data["analysis"]
            assert "roi" in analysis
            assert "velocity" in analysis
            assert "recommendation" in analysis
            assert analysis["recommendation"] in ["BUY", "WATCH", "PASS", "ERROR"]
            assert "confidence_score" in analysis
            assert 0 <= analysis["confidence_score"] <= 100
            
            # Verify config audit
            config_audit = data["config_audit"]
            assert "version" in config_audit
            assert "hash" in config_audit
            assert config_audit["profile"] == "neutral"
            
            # Verify Keepa metadata
            keepa_metadata = data["keepa_metadata"]
            assert "snapshot_at" in keepa_metadata
            assert "cache_hit" in keepa_metadata
            assert isinstance(keepa_metadata["cache_hit"], bool)
        
        elif response.status_code == 404:
            # Product not found - acceptable for test
            data = response.json()
            assert data["detail"]["code"] == "PRODUCT_NOT_FOUND"
            assert "trace_id" in data["detail"]
    
    def test_get_metrics_invalid_asin(self):
        """Test metrics with invalid ASIN."""
        response = client.get("/api/v1/keepa/INVALID123/metrics")
        
        # Should normalize and try, but likely fail
        assert response.status_code in [404, 500]
        data = response.json()
        assert "detail" in data
        assert "trace_id" in data["detail"]


class TestRawKeepaDataEndpoint:
    """Test raw Keepa data endpoint."""
    
    def test_get_raw_data_success(self):
        """Test successful raw data retrieval."""
        asin = TEST_ASINS["book_textbook"]
        response = client.get(f"/api/v1/keepa/{asin}/raw")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            assert "_metadata" in data
            assert "keepa_data" in data
            
            # Verify metadata
            metadata = data["_metadata"]
            assert metadata["asin"] == asin.upper()
            assert "retrieved_at" in metadata
            assert "trace_id" in metadata
            assert "cache_hit" in metadata
            
            # Keepa data should be raw dict
            assert isinstance(data["keepa_data"], dict)
        
        elif response.status_code == 404:
            # Product not found - acceptable for test
            data = response.json()
            assert data["detail"]["code"] == "PRODUCT_NOT_FOUND"


class TestConfigurationProfiles:
    """Test different configuration profiles affect results."""
    
    @pytest.mark.asyncio
    async def test_different_profiles_different_recommendations(self):
        """Test that different config profiles can yield different recommendations."""
        asin = TEST_ASINS["book_textbook"]
        
        # Test with conservative profile
        response_conservative = client.get(f"/api/v1/keepa/{asin}/metrics?config_profile=conservative")
        
        # Test with aggressive profile  
        response_aggressive = client.get(f"/api/v1/keepa/{asin}/metrics?config_profile=aggressive")
        
        # If both succeed, they might have different recommendations
        if response_conservative.status_code == 200 and response_aggressive.status_code == 200:
            data_conservative = response_conservative.json()
            data_aggressive = response_aggressive.json()
            
            # Config hashes should be different
            assert data_conservative["config_audit"]["hash"] != data_aggressive["config_audit"]["hash"]
            
            # Analysis might differ (but not guaranteed)
            # At minimum, verify structure is consistent
            for data in [data_conservative, data_aggressive]:
                assert "analysis" in data
                assert data["analysis"]["recommendation"] in ["BUY", "WATCH", "PASS", "ERROR"]


class TestErrorHandling:
    """Test comprehensive error handling."""
    
    def test_malformed_ingest_request(self):
        """Test malformed batch request."""
        payload = {
            "identifiers": [],  # Empty list should fail validation
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_too_many_identifiers(self):
        """Test batch size limit."""
        payload = {
            "identifiers": ["B00TEST001"] * 1001  # Over limit
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_identifiers_in_batch(self):
        """Test validation of identifier format in batch."""
        payload = {
            "identifiers": [
                "VALID10CHR",  # 10 chars, might be valid ASIN
                "TOO_SHORT",   # Invalid
                "WAY_TOO_LONG_FOR_ASIN_OR_ISBN"  # Invalid
            ]
        }
        
        response = client.post("/api/v1/keepa/ingest", json=payload)
        
        # Pydantic validation should catch invalid formats
        if response.status_code == 422:
            # Expected validation error
            assert True
        else:
            # Might pass validation but fail during processing
            data = response.json()
            assert data["failed"] > 0


if __name__ == "__main__":
    # Run individual test for quick validation
    test = TestKeepaHealthEndpoint()
    test.test_health_check_success()
    print("✅ Health endpoint test passed")
    
    test = TestKeepaTestConnection()
    test.test_valid_asin_connection()
    print("✅ Connection test passed")
    
    print("🚀 All smoke tests passed - ready for full pytest run")