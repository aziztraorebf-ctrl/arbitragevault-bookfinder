"""
FastAPI endpoints compliance audit
Validates all API endpoints and HTTP behavior
"""
import asyncio
import json
from typing import Dict, Any
import aiohttp

from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class APICompliance:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.data_generator = SampleDataGenerator()
        self.api_base_url = "http://localhost:8000"
        
    async def audit(self) -> Dict[str, Any]:
        """Run comprehensive API compliance audit"""
        results = {
            'status': 'UNKNOWN',
            'endpoints_tested': 0,
            'endpoint_results': {},
            'warnings': []
        }
        
        print("    🌐 Auditing API compliance...")
        
        # Check if API is available
        if not await self._check_api_availability():
            return {
                'status': 'SKIPPED',
                'reason': 'FastAPI server not available',
                'endpoints_tested': 0,
                'endpoint_results': {},
                'warnings': ['API server must be running for compliance test']
            }
        
        # Test all endpoints
        endpoint_tests = [
            ('health_endpoint', self._test_health_endpoint),
            ('create_analysis', self._test_create_analysis_endpoint),
            ('list_analyses', self._test_list_analyses_endpoint),
            ('top_analyses', self._test_top_analyses_endpoint),
            ('list_batches', self._test_list_batches_endpoint),
            ('update_batch_status', self._test_update_batch_status_endpoint),
            ('error_scenarios', self._test_error_scenarios)
        ]
        
        passed_tests = 0
        for test_name, test_func in endpoint_tests:
            try:
                print(f"      🔗 Testing {test_name}...")
                test_result = await test_func()
                results['endpoint_results'][test_name] = test_result
                results['endpoints_tested'] += 1
                
                if test_result.get('status') == 'PASS':
                    passed_tests += 1
                    
            except Exception as e:
                print(f"        ❌ Error testing {test_name}: {e}")
                results['endpoint_results'][test_name] = {
                    'status': 'ERROR',
                    'message': str(e)
                }
                results['endpoints_tested'] += 1
        
        # Overall status
        if passed_tests == results['endpoints_tested']:
            results['status'] = 'PASS'
        elif passed_tests > results['endpoints_tested'] // 2:
            results['status'] = 'PARTIAL'
        else:
            results['status'] = 'FAIL'
        
        return results
    
    async def _check_api_availability(self) -> bool:
        """Check if FastAPI server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/health",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _test_health_endpoint(self) -> Dict[str, Any]:
        """Test health check endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/health"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        expected_fields = ['status', 'database']
                        for field in expected_fields:
                            if field not in data:
                                return {
                                    'status': 'FAIL',
                                    'message': f'Health response missing field: {field}'
                                }
                        
                        return {
                            'status': 'PASS',
                            'message': 'Health endpoint working correctly',
                            'response_data': data
                        }
                    else:
                        return {
                            'status': 'FAIL',
                            'message': f'Health endpoint returned status {response.status}'
                        }
                        
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Health endpoint test failed: {str(e)}'
            }
    
    async def _test_create_analysis_endpoint(self) -> Dict[str, Any]:
        """Test analysis creation endpoint"""
        try:
            # First create a test batch via direct API
            batch_data = {
                "name": "API Test Batch",
                "total_items": 1
            }
            
            analysis_data = {
                "isbn_or_asin": "9781234567890",
                "book_title": "Test Book API",
                "selling_price": "25.99",
                "cost_price": "15.00",
                "amazon_fees": "3.90",
                "net_profit": "7.09",
                "roi_percent": "47.27",
                "velocity_score": "0.65",
                "profit_score": "0.75",
                "rank_bsr": 15000,
                "raw_keepa_data": {"test": "data"}
            }
            
            async with aiohttp.ClientSession() as session:
                # Test POST /api/v1/analyses
                async with session.post(
                    f"{self.api_base_url}/api/v1/analyses",
                    json=analysis_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status in [200, 201]:
                        data = await response.json()
                        
                        # Validate response structure
                        if 'id' in data and 'isbn_or_asin' in data:
                            return {
                                'status': 'PASS',
                                'message': 'Analysis creation successful',
                                'created_id': data.get('id')
                            }
                        else:
                            return {
                                'status': 'FAIL',
                                'message': 'Analysis creation response missing required fields'
                            }
                    else:
                        response_text = await response.text()
                        return {
                            'status': 'FAIL',
                            'message': f'Analysis creation failed with status {response.status}: {response_text}'
                        }
                        
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Analysis creation test failed: {str(e)}'
            }
    
    async def _test_list_analyses_endpoint(self) -> Dict[str, Any]:
        """Test analyses listing endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic listing
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        expected_fields = ['items', 'total', 'page', 'size', 'pages']
                        for field in expected_fields:
                            if field not in data:
                                return {
                                    'status': 'FAIL',
                                    'message': f'List response missing field: {field}'
                                }
                        
                        # Test with filters
                        async with session.get(
                            f"{self.api_base_url}/api/v1/analyses",
                            params={
                                'min_roi': 30.0,
                                'max_roi': 80.0,
                                'limit': 10
                            }
                        ) as filter_response:
                            if filter_response.status == 200:
                                filter_data = await filter_response.json()
                                
                                return {
                                    'status': 'PASS',
                                    'message': 'List analyses endpoint working correctly',
                                    'basic_count': len(data.get('items', [])),
                                    'filtered_count': len(filter_data.get('items', []))
                                }
                            else:
                                return {
                                    'status': 'PARTIAL',
                                    'message': 'Basic listing works but filtering failed'
                                }
                    else:
                        return {
                            'status': 'FAIL',
                            'message': f'List analyses returned status {response.status}'
                        }
                        
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'List analyses test failed: {str(e)}'
            }
    
    async def _test_top_analyses_endpoint(self) -> Dict[str, Any]:
        """Test top analyses endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test all strategies
                strategies = ['roi', 'velocity', 'profit', 'balanced']
                strategy_results = {}
                
                for strategy in strategies:
                    async with session.get(
                        f"{self.api_base_url}/api/v1/analyses/top",
                        params={
                            'n': 5,
                            'strategy': strategy
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'analyses' in data:
                                strategy_results[strategy] = len(data['analyses'])
                            else:
                                return {
                                    'status': 'FAIL',
                                    'message': f'Top analyses response missing analyses field for {strategy}'
                                }
                        else:
                            return {
                                'status': 'FAIL',
                                'message': f'Top analyses failed for strategy {strategy}: {response.status}'
                            }
                
                return {
                    'status': 'PASS',
                    'message': 'Top analyses endpoint working for all strategies',
                    'strategy_results': strategy_results
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Top analyses test failed: {str(e)}'
            }
    
    async def _test_list_batches_endpoint(self) -> Dict[str, Any]:
        """Test batches listing endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/batches"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Validate response structure
                        expected_fields = ['items', 'total', 'page', 'size', 'pages']
                        for field in expected_fields:
                            if field not in data:
                                return {
                                    'status': 'FAIL',
                                    'message': f'Batches list response missing field: {field}'
                                }
                        
                        return {
                            'status': 'PASS',
                            'message': 'List batches endpoint working correctly',
                            'batch_count': len(data.get('items', []))
                        }
                    else:
                        return {
                            'status': 'FAIL',
                            'message': f'List batches returned status {response.status}'
                        }
                        
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'List batches test failed: {str(e)}'
            }
    
    async def _test_update_batch_status_endpoint(self) -> Dict[str, Any]:
        """Test batch status update endpoint"""
        try:
            # This test assumes there's at least one batch to update
            async with aiohttp.ClientSession() as session:
                # First get a batch ID
                async with session.get(
                    f"{self.api_base_url}/api/v1/batches",
                    params={'limit': 1}
                ) as list_response:
                    if list_response.status == 200:
                        list_data = await list_response.json()
                        batches = list_data.get('items', [])
                        
                        if not batches:
                            return {
                                'status': 'SKIPPED',
                                'message': 'No batches available to test status update'
                            }
                        
                        batch_id = batches[0]['id']
                        current_status = batches[0]['status']
                        
                        # Try to update status (keep it the same to avoid side effects)
                        async with session.patch(
                            f"{self.api_base_url}/api/v1/batches/{batch_id}/status",
                            json={'status': current_status}
                        ) as update_response:
                            if update_response.status == 200:
                                return {
                                    'status': 'PASS',
                                    'message': 'Batch status update endpoint working correctly'
                                }
                            else:
                                return {
                                    'status': 'FAIL',
                                    'message': f'Batch status update failed: {update_response.status}'
                                }
                    else:
                        return {
                            'status': 'FAIL',
                            'message': 'Could not retrieve batches for status update test'
                        }
                        
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Batch status update test failed: {str(e)}'
            }
    
    async def _test_error_scenarios(self) -> Dict[str, Any]:
        """Test error handling scenarios"""
        try:
            error_tests = {}
            
            async with aiohttp.ClientSession() as session:
                # Test 404 - Non-existent batch
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses",
                    params={'batch_id': 99999}
                ) as response:
                    # Should return 200 with empty results, not 404
                    if response.status == 200:
                        data = await response.json()
                        if len(data.get('items', [])) == 0:
                            error_tests['non_existent_batch'] = 'PASS'
                        else:
                            error_tests['non_existent_batch'] = 'FAIL - returned data for non-existent batch'
                    else:
                        error_tests['non_existent_batch'] = f'FAIL - status {response.status}'
                
                # Test 422 - Invalid sort field
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses",
                    params={'sort': 'invalid_field'}
                ) as response:
                    if response.status == 422:
                        error_tests['invalid_sort_field'] = 'PASS'
                    else:
                        error_tests['invalid_sort_field'] = f'FAIL - expected 422, got {response.status}'
                
                # Test 422 - Invalid strategy
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses/top",
                    params={'strategy': 'invalid_strategy', 'n': 5}
                ) as response:
                    if response.status == 422:
                        error_tests['invalid_strategy'] = 'PASS'
                    else:
                        error_tests['invalid_strategy'] = f'FAIL - expected 422, got {response.status}'
            
            # Check overall error handling
            passed_error_tests = sum(1 for result in error_tests.values() if result == 'PASS')
            total_error_tests = len(error_tests)
            
            if passed_error_tests == total_error_tests:
                return {
                    'status': 'PASS',
                    'message': 'All error scenarios handled correctly',
                    'error_test_results': error_tests
                }
            else:
                return {
                    'status': 'PARTIAL',
                    'message': f'Some error scenarios failed ({passed_error_tests}/{total_error_tests})',
                    'error_test_results': error_tests
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error scenarios test failed: {str(e)}'
            }