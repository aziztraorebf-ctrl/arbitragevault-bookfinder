"""
Integration Test for Stock Estimate Endpoint
Test the full API endpoint with mocked dependencies
"""
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


def create_test_app():
    """Create FastAPI test app with mocked dependencies"""
    from fastapi import FastAPI, Depends
    from app.routers.stock_estimate import router
    
    # Create test app
    app = FastAPI()
    
    # Mock database session
    def mock_db():
        return Mock()
    
    # Mock Keepa service
    def mock_keepa_service():
        keepa_mock = Mock()
        # Mock successful API response
        keepa_mock.get_product_data.return_value = {
            'offers': [
                {"isFBA": True, "price": 15.99, "condition": "Used - Good"},
                {"isFBA": True, "price": 16.99, "condition": "Used - Very Good"},
                {"isFBA": False, "price": 14.99, "condition": "Used - Good"}
            ]
        }
        return keepa_mock
    
    # Override dependencies
    app.dependency_overrides = {}
    
    # Include the router
    app.include_router(router)
    
    return app, mock_db, mock_keepa_service


def test_endpoint_integration():
    """Test the stock estimate endpoint with mocked data"""
    print("🧪 Testing Stock Estimate API Integration...")
    
    try:
        # Create test app
        app, mock_db, mock_keepa = create_test_app()
        
        # Create test client
        client = TestClient(app)
        
        # Mock successful cache miss scenario (no existing cache)
        with patch('app.services.stock_estimate_service.StockEstimateService') as mock_service_class:
            # Create mock service instance
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock successful response
            expected_response = {
                "asin": "B00TEST123",
                "units_available_estimate": 2,
                "offers_fba": 2,
                "offers_mfn": 1,
                "source": "fresh",
                "updated_at": "2025-01-17T20:00:00Z",
                "ttl": 86400
            }
            
            mock_service.get_stock_estimate.return_value = expected_response
            
            # Test API call
            response = client.get("/api/v1/products/B00TEST123/stock-estimate")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["asin"] == "B00TEST123"
            assert data["units_available_estimate"] == 2
            assert data["offers_fba"] == 2
            assert data["offers_mfn"] == 1
            assert data["source"] == "fresh"
            
            print("✅ Test 1: Successful API call - passed")
        
        # Test with price target parameter
        with patch('app.services.stock_estimate_service.StockEstimateService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            expected_response["units_available_estimate"] = 1  # Filtered result
            mock_service.get_stock_estimate.return_value = expected_response
            
            response = client.get("/api/v1/products/B00TEST123/stock-estimate?price_target=15.50")
            
            assert response.status_code == 200
            data = response.json()
            assert data["asin"] == "B00TEST123"
            
            # Verify service was called with price target
            mock_service.get_stock_estimate.assert_called_with("B00TEST123", 15.50)
            
            print("✅ Test 2: API call with price target - passed")
        
        # Test health endpoint
        response = client.get("/api/v1/products/stock-estimate/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "stock_estimate"
        assert data["status"] == "healthy"
        print("✅ Test 3: Health endpoint - passed")
        
        # Test invalid ASIN
        response = client.get("/api/v1/products/123/stock-estimate")  # Too short
        assert response.status_code == 400
        print("✅ Test 4: Invalid ASIN rejection - passed")
        
        print("\n✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n🧪 Testing Error Scenarios...")
    
    try:
        app, _, _ = create_test_app()
        client = TestClient(app)
        
        # Test service error
        with patch('app.services.stock_estimate_service.StockEstimateService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock error response
            error_response = {
                "asin": "B00ERROR123",
                "units_available_estimate": 0,
                "offers_fba": 0,
                "offers_mfn": 0,
                "source": "error",
                "updated_at": "2025-01-17T20:00:00Z",
                "ttl": 0,
                "error": "Keepa API timeout"
            }
            
            mock_service.get_stock_estimate.return_value = error_response
            
            response = client.get("/api/v1/products/B00ERROR123/stock-estimate")
            
            # Should return 504 for timeout errors
            assert response.status_code == 504
            print("✅ Error handling test - passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scenario test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_endpoint_integration()
    success = success and test_error_scenarios()
    
    if success:
        print("\n🎉 All Stock Estimate tests passed! Ready for deployment.")
    else:
        print("\n❌ Some tests failed. Check implementation.")