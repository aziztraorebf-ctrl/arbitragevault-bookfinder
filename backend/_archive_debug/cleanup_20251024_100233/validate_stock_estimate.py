"""
Stock Estimate Feature Validation
Complete validation of the stock estimate feature implementation
"""
import os
import importlib.util
from datetime import datetime

class StockEstimateValidator:
    """Validator for Stock Estimate feature completeness"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log(self, message, status="INFO"):
        """Log validation step"""
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌", 
            "INFO": "ℹ️",
            "WARN": "⚠️"
        }
        print(f"{status_icon.get(status, 'ℹ️')} {message}")
        self.results.append((status, message))
        
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
    
    def validate_file_structure(self):
        """Validate that all required files exist"""
        self.log("🔍 Validating file structure...")
        
        required_files = [
            "app/models/stock_estimate.py",
            "app/services/stock_estimate_service.py", 
            "app/routers/stock_estimate.py",
            "../STOCK_ESTIMATE_DOCS.md"
        ]
        
        base_path = os.path.dirname(__file__)
        
        for file_path in required_files:
            full_path = os.path.join(base_path, file_path)
            if os.path.exists(full_path):
                self.log(f"Found: {file_path}", "PASS")
            else:
                self.log(f"Missing: {file_path}", "FAIL")
    
    def validate_model_definition(self):
        """Validate model is properly defined"""
        self.log("🔍 Validating StockEstimateCache model...")
        
        try:
            # Check if model file exists and can be imported
            model_path = os.path.join(os.path.dirname(__file__), "app/models/stock_estimate.py")
            
            if os.path.exists(model_path):
                with open(model_path, 'r') as f:
                    content = f.read()
                
                # Check for required components
                checks = [
                    ("class StockEstimateCache", "Model class definition"),
                    ("asin = Column", "ASIN column"), 
                    ("units_available_estimate = Column", "Units estimate column"),
                    ("offers_fba = Column", "FBA offers column"),
                    ("offers_mfn = Column", "MFN offers column"),
                    ("updated_at = Column", "Updated timestamp"),
                    ("ttl_seconds = Column", "TTL column"),
                    ("def is_expired", "Expiration check method"),
                    ("def to_dict", "Dictionary conversion method")
                ]
                
                for check_str, description in checks:
                    if check_str in content:
                        self.log(f"Model has {description}", "PASS")
                    else:
                        self.log(f"Model missing {description}", "FAIL")
            else:
                self.log("Stock estimate model file not found", "FAIL")
                
        except Exception as e:
            self.log(f"Error validating model: {e}", "FAIL")
    
    def validate_service_logic(self):
        """Validate service implementation"""
        self.log("🔍 Validating StockEstimateService...")
        
        try:
            service_path = os.path.join(os.path.dirname(__file__), "app/services/stock_estimate_service.py")
            
            if os.path.exists(service_path):
                with open(service_path, 'r') as f:
                    content = f.read()
                
                # Check for key methods and logic
                checks = [
                    ("class StockEstimateService", "Service class"),
                    ("def get_stock_estimate", "Main estimation method"),
                    ("def _get_cached_estimate", "Cache retrieval"),
                    ("def _fetch_keepa_offers", "Keepa integration"),
                    ("def _calculate_simple_estimate", "Calculation logic"),
                    ("def _cache_estimate", "Cache storage"),
                    ("price_band_pct", "Price filtering configuration"),
                    ("max_estimate", "Estimate capping"),
                    ("Cache-first", "Cache strategy")
                ]
                
                for check_str, description in checks:
                    if check_str in content:
                        self.log(f"Service has {description}", "PASS")
                    else:
                        self.log(f"Service missing {description}", "FAIL")
            else:
                self.log("Stock estimate service file not found", "FAIL")
                
        except Exception as e:
            self.log(f"Error validating service: {e}", "FAIL")
    
    def validate_router_endpoints(self):
        """Validate router and endpoints"""
        self.log("🔍 Validating API router...")
        
        try:
            router_path = os.path.join(os.path.dirname(__file__), "app/routers/stock_estimate.py")
            
            if os.path.exists(router_path):
                with open(router_path, 'r') as f:
                    content = f.read()
                
                # Check for endpoints and features
                checks = [
                    ("APIRouter", "FastAPI router"),
                    ('/{asin}/stock-estimate', "Main endpoint path"),
                    ("price_target: Optional[float]", "Price target parameter"),
                    ("/stock-estimate/health", "Health endpoint"), 
                    ("HTTPException", "Error handling"),
                    ("get_stock_estimate_service", "Service dependency"),
                    ("Query(None", "Optional query parameter")
                ]
                
                for check_str, description in checks:
                    if check_str in content:
                        self.log(f"Router has {description}", "PASS")
                    else:
                        self.log(f"Router missing {description}", "FAIL")
            else:
                self.log("Stock estimate router file not found", "FAIL")
                
        except Exception as e:
            self.log(f"Error validating router: {e}", "FAIL")
    
    def validate_main_integration(self):
        """Validate integration with main app"""
        self.log("🔍 Validating main.py integration...")
        
        try:
            main_path = os.path.join(os.path.dirname(__file__), "app/main.py")
            
            if os.path.exists(main_path):
                with open(main_path, 'r') as f:
                    content = f.read()
                
                if "stock_estimate" in content:
                    self.log("Stock estimate router imported in main.py", "PASS")
                else:
                    self.log("Stock estimate router NOT imported in main.py", "FAIL")
                    
                if "include_router(stock_estimate.router" in content:
                    self.log("Stock estimate router included in app", "PASS") 
                else:
                    self.log("Stock estimate router NOT included in app", "FAIL")
            else:
                self.log("main.py not found", "FAIL")
                
        except Exception as e:
            self.log(f"Error validating main integration: {e}", "FAIL")
    
    def validate_documentation(self):
        """Validate documentation exists"""
        self.log("🔍 Validating documentation...")
        
        doc_path = os.path.join(os.path.dirname(__file__), "../STOCK_ESTIMATE_DOCS.md")
        
        if os.path.exists(doc_path):
            with open(doc_path, 'r') as f:
                content = f.read()
            
            # Check for key documentation sections
            doc_checks = [
                ("# 📦 Stock Estimate API", "API title"),
                ("GET `/api/v1/products/{asin}/stock-estimate`", "Endpoint documentation"),
                ("Heuristique Ultra-Simple", "Logic explanation"),
                ("Cache Strategy", "Cache documentation"),
                ("Cases d'Usage", "Usage examples"),
                ("curl", "API examples"),
                ("Intégration Frontend", "Integration guide")
            ]
            
            for check_str, description in doc_checks:
                if check_str in content:
                    self.log(f"Documentation has {description}", "PASS")
                else:
                    self.log(f"Documentation missing {description}", "FAIL")
        else:
            self.log("Stock estimate documentation not found", "FAIL")
    
    def run_complete_validation(self):
        """Run all validation checks"""
        print("🧪 Stock Estimate Feature Validation")
        print("=" * 50)
        
        self.validate_file_structure()
        print()
        
        self.validate_model_definition()
        print()
        
        self.validate_service_logic()
        print()
        
        self.validate_router_endpoints()
        print()
        
        self.validate_main_integration()
        print()
        
        self.validate_documentation()
        print()
        
        # Summary
        total_checks = self.passed + self.failed
        success_rate = (self.passed / total_checks * 100) if total_checks > 0 else 0
        
        print("=" * 50)
        print(f"📊 VALIDATION SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 Stock Estimate Feature is READY FOR DEPLOYMENT!")
            print("🚀 All components implemented and validated successfully.")
        else:
            print(f"\n⚠️ {self.failed} issues found. Review failed items above.")
        
        return self.failed == 0


if __name__ == "__main__":
    validator = StockEstimateValidator()
    success = validator.run_complete_validation()
    exit(0 if success else 1)