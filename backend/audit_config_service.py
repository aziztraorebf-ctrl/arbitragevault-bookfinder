#!/usr/bin/env python
"""
Audit complet du Config Service - Phase 2 Jour 4
Vérifie : schemas, validation, API, intégration Keepa
"""

import json
import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.config import (
    FeeConfig, ROIConfig, VelocityConfig, VelocityTier,
    DataQualityThresholds, ProductFinderConfig,
    CategoryConfig, ConfigCreate, EffectiveConfig
)
from app.services.config_service import ConfigService
from app.database import SessionLocal

# ANSI Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    """Print formatted header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

def print_error(msg: str):
    """Print error message."""
    print(f"{Colors.RED}[FAIL]{Colors.END} {msg}")

def print_warning(msg: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")

def print_info(msg: str):
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")


class ConfigServiceAuditor:
    """Audit complet du Config Service."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "metrics": {},
            "errors": [],
            "warnings": []
        }
        self.db = SessionLocal()
        self.config_service = ConfigService(self.db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def audit_schemas(self) -> Dict[str, bool]:
        """Test 1: Vérifier tous les schemas Pydantic v2."""
        print_header("TEST 1: SCHEMAS PYDANTIC V2")
        results = {}

        # Test FeeConfig
        try:
            fee_config = FeeConfig(
                referral_fee_percent=Decimal("15.0"),
                fba_base_fee=Decimal("3.00"),
                fba_per_pound=Decimal("0.40"),
                closing_fee=Decimal("1.80"),
                prep_fee=Decimal("0.20"),
                shipping_cost=Decimal("0.40")
            )
            results["FeeConfig"] = True
            print_success("FeeConfig schema valid")
        except Exception as e:
            results["FeeConfig"] = False
            print_error(f"FeeConfig failed: {e}")
            self.results["errors"].append(f"FeeConfig: {str(e)}")

        # Test ROIConfig
        try:
            roi_config = ROIConfig(
                min_acceptable=Decimal("15.0"),
                target=Decimal("30.0"),
                excellent_threshold=Decimal("50.0"),
                source_price_factor=Decimal("0.6")
            )
            results["ROIConfig"] = True
            print_success("ROIConfig schema valid")
        except Exception as e:
            results["ROIConfig"] = False
            print_error(f"ROIConfig failed: {e}")
            self.results["errors"].append(f"ROIConfig: {str(e)}")

        # Test VelocityConfig
        try:
            velocity_config = VelocityConfig(
                tiers=[
                    VelocityTier(name="PREMIUM", min_score=80, max_score=100, bsr_threshold=10000),
                    VelocityTier(name="HIGH", min_score=60, max_score=79, bsr_threshold=50000),
                    VelocityTier(name="MEDIUM", min_score=40, max_score=59, bsr_threshold=100000),
                    VelocityTier(name="LOW", min_score=20, max_score=39, bsr_threshold=500000),
                    VelocityTier(name="DEAD", min_score=0, max_score=19, bsr_threshold=1000000)
                ]
            )
            results["VelocityConfig"] = True
            print_success("VelocityConfig schema valid")
        except Exception as e:
            results["VelocityConfig"] = False
            print_error(f"VelocityConfig failed: {e}")
            self.results["errors"].append(f"VelocityConfig: {str(e)}")

        # Test DataQualityThresholds
        try:
            quality = DataQualityThresholds(
                min_rank_history_days=30,
                min_price_history_days=30,
                min_offers_count=3,
                confidence_score_threshold=Decimal("70.0")
            )
            results["DataQualityThresholds"] = True
            print_success("DataQualityThresholds schema valid")
        except Exception as e:
            results["DataQualityThresholds"] = False
            print_error(f"DataQualityThresholds failed: {e}")
            self.results["errors"].append(f"DataQualityThresholds: {str(e)}")

        # Test ProductFinderConfig
        try:
            finder = ProductFinderConfig(
                max_results_per_search=100,
                cache_ttl_hours=24,
                min_roi_filter=Decimal("15.0"),
                min_velocity_filter=Decimal("40.0")
            )
            results["ProductFinderConfig"] = True
            print_success("ProductFinderConfig schema valid")
        except Exception as e:
            results["ProductFinderConfig"] = False
            print_error(f"ProductFinderConfig failed: {e}")
            self.results["errors"].append(f"ProductFinderConfig: {str(e)}")

        self.results["tests"]["schemas"] = results
        return results

    def audit_validation(self) -> Dict[str, bool]:
        """Test 2: Vérifier validation cross-field."""
        print_header("TEST 2: VALIDATION CROSS-FIELD")
        results = {}

        # Test 1: ROI invalid (target < min_acceptable)
        try:
            roi = ROIConfig(
                min_acceptable=Decimal("50.0"),
                target=Decimal("30.0"),  # Invalid
                excellent_threshold=Decimal("70.0")
            )
            results["ROI_invalid_order"] = False
            print_error("ROI validation failed - should reject invalid order")
        except ValueError as e:
            results["ROI_invalid_order"] = True
            print_success(f"ROI validation correctly rejected: {e}")

        # Test 2: ROI valid
        try:
            roi = ROIConfig(
                min_acceptable=Decimal("15.0"),
                target=Decimal("30.0"),
                excellent_threshold=Decimal("50.0")
            )
            results["ROI_valid_order"] = True
            print_success("ROI validation accepts valid order")
        except ValueError as e:
            results["ROI_valid_order"] = False
            print_error(f"ROI validation rejected valid config: {e}")

        # Test 3: VelocityTier invalid (max < min)
        try:
            tier = VelocityTier(
                name="INVALID",
                min_score=80,
                max_score=60,  # Invalid
                bsr_threshold=10000
            )
            results["VelocityTier_invalid_range"] = False
            print_error("VelocityTier validation failed - should reject invalid range")
        except ValueError as e:
            results["VelocityTier_invalid_range"] = True
            print_success(f"VelocityTier validation correctly rejected: {e}")

        # Test 4: VelocityConfig overlapping tiers
        try:
            velocity = VelocityConfig(
                tiers=[
                    VelocityTier(name="HIGH", min_score=60, max_score=80, bsr_threshold=50000),
                    VelocityTier(name="PREMIUM", min_score=75, max_score=100, bsr_threshold=10000)
                ]
            )
            results["VelocityConfig_overlap"] = False
            print_error("VelocityConfig validation failed - should reject overlaps")
        except ValueError as e:
            results["VelocityConfig_overlap"] = True
            print_success(f"VelocityConfig validation correctly rejected: {e}")

        # Test 5: VelocityConfig valid non-overlapping
        try:
            velocity = VelocityConfig(
                tiers=[
                    VelocityTier(name="HIGH", min_score=60, max_score=79, bsr_threshold=50000),
                    VelocityTier(name="PREMIUM", min_score=80, max_score=100, bsr_threshold=10000)
                ]
            )
            results["VelocityConfig_valid"] = True
            print_success("VelocityConfig validation accepts non-overlapping tiers")
        except ValueError as e:
            results["VelocityConfig_valid"] = False
            print_error(f"VelocityConfig validation rejected valid config: {e}")

        self.results["tests"]["validation"] = results
        return results

    def audit_service_layer(self) -> Dict[str, bool]:
        """Test 3: Vérifier service layer et DB operations."""
        print_header("TEST 3: SERVICE LAYER & DATABASE")
        results = {}

        # Test auto-création default config
        try:
            config = self.config_service.get_active_configuration()
            if config:
                results["auto_create_default"] = True
                print_success(f"Default config auto-created: ID={config.id}")
            else:
                results["auto_create_default"] = False
                print_error("No default config created")
        except Exception as e:
            results["auto_create_default"] = False
            print_error(f"Service layer error: {e}")
            self.results["errors"].append(f"Service layer: {str(e)}")

        # Test effective config avec category override
        try:
            books_category_id = 283155  # Books category
            effective = self.config_service.get_effective_config(category_id=books_category_id)

            if effective:
                results["effective_config"] = True
                print_success(f"Effective config retrieved for Books category")

                # Vérifier si overrides appliqués
                if effective.applied_overrides:
                    print_info(f"  Overrides applied: {effective.applied_overrides}")
                else:
                    print_info("  No overrides found for Books category")
            else:
                results["effective_config"] = False
                print_error("Failed to get effective config")
        except Exception as e:
            results["effective_config"] = False
            print_error(f"Effective config error: {e}")
            self.results["errors"].append(f"Effective config: {str(e)}")

        self.results["tests"]["service_layer"] = results
        return results

    def audit_keepa_integration(self) -> Dict[str, bool]:
        """Test 4: Vérifier intégration avec Keepa data structures."""
        print_header("TEST 4: INTEGRATION KEEPA")
        results = {}

        # Simuler structure Keepa
        keepa_product = {
            "asin": "0593655036",
            "title": "Fourth Wing",
            "csv": [0, 0, 1599, 0, 0],  # Prix en centimes
            "stats": {
                "current": [1599, None, None, 42000]  # Buy Box price, rank
            }
        }

        try:
            # Test extraction prix
            buy_box_cents = keepa_product["stats"]["current"][0]
            buy_box_price = Decimal(str(buy_box_cents / 100))

            # Test calcul ROI avec config
            config = self.config_service.get_active_configuration()
            if config:
                source_price = buy_box_price * config.roi.source_price_factor

                # Calculer fees
                fees = config.fees
                referral_fee = buy_box_price * (fees.referral_fee_percent / Decimal("100"))
                fba_fee = fees.fba_base_fee + fees.fba_per_pound
                total_fees = referral_fee + fba_fee + fees.closing_fee + fees.prep_fee + fees.shipping_cost

                profit = buy_box_price - source_price - total_fees
                roi_percent = (profit / source_price) * Decimal("100")

                results["keepa_price_extraction"] = True
                print_success(f"Keepa price extraction: ${buy_box_price}")

                results["roi_calculation"] = True
                print_success(f"ROI calculation: {roi_percent:.1f}%")

                # Test velocity assignment
                bsr = keepa_product["stats"]["current"][3]
                velocity_tier = None
                for tier in config.velocity.tiers:
                    if bsr <= tier.bsr_threshold:
                        velocity_tier = tier.name
                        break

                if velocity_tier:
                    results["velocity_assignment"] = True
                    print_success(f"Velocity tier assigned: {velocity_tier} (BSR: {bsr})")
                else:
                    results["velocity_assignment"] = False
                    print_error("Failed to assign velocity tier")
            else:
                results["keepa_price_extraction"] = False
                results["roi_calculation"] = False
                results["velocity_assignment"] = False
                print_error("No config available for Keepa integration test")

        except Exception as e:
            results["keepa_integration"] = False
            print_error(f"Keepa integration error: {e}")
            self.results["errors"].append(f"Keepa integration: {str(e)}")

        self.results["tests"]["keepa_integration"] = results
        return results

    def audit_performance(self) -> Dict[str, Any]:
        """Test 5: Mesurer performance."""
        print_header("TEST 5: PERFORMANCE METRICS")
        metrics = {}

        # Test temps de création config
        start = time.time()
        try:
            config = ConfigCreate(
                name="Performance Test",
                fees=FeeConfig(),
                roi=ROIConfig(),
                velocity=VelocityConfig(
                    tiers=[
                        VelocityTier(name="TEST", min_score=0, max_score=100, bsr_threshold=1000000)
                    ]
                ),
                data_quality=DataQualityThresholds(),
                product_finder=ProductFinderConfig()
            )
            creation_time = time.time() - start
            metrics["config_creation_time"] = f"{creation_time*1000:.2f}ms"
            print_success(f"Config creation time: {creation_time*1000:.2f}ms")
        except Exception as e:
            metrics["config_creation_time"] = "Failed"
            print_error(f"Performance test failed: {e}")

        # Test temps de récupération effective config
        start = time.time()
        try:
            effective = self.config_service.get_effective_config(category_id=283155)
            retrieval_time = time.time() - start
            metrics["effective_config_time"] = f"{retrieval_time*1000:.2f}ms"
            print_success(f"Effective config retrieval: {retrieval_time*1000:.2f}ms")
        except Exception as e:
            metrics["effective_config_time"] = "Failed"
            print_error(f"Retrieval test failed: {e}")

        # Test serialization JSON
        start = time.time()
        try:
            config_dict = config.model_dump()
            # Convert Decimals for JSON
            def convert_decimals(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                return obj

            json_data = json.dumps(convert_decimals(config_dict))
            serialization_time = time.time() - start
            metrics["json_serialization_time"] = f"{serialization_time*1000:.2f}ms"
            metrics["json_size_bytes"] = len(json_data)
            print_success(f"JSON serialization: {serialization_time*1000:.2f}ms ({len(json_data)} bytes)")
        except Exception as e:
            metrics["json_serialization_time"] = "Failed"
            print_error(f"Serialization test failed: {e}")

        self.results["metrics"] = metrics
        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """Générer rapport final."""
        print_header("RAPPORT FINAL")

        # Calculer totaux
        total_tests = 0
        passed_tests = 0

        for category, tests in self.results["tests"].items():
            for test_name, passed in tests.items():
                total_tests += 1
                if passed:
                    passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Afficher résumé
        print(f"\n{Colors.BOLD}RESULTATS:{Colors.END}")
        print(f"  Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"  Erreurs: {len(self.results['errors'])}")
        print(f"  Warnings: {len(self.results['warnings'])}")

        if self.results["errors"]:
            print(f"\n{Colors.RED}ERREURS:{Colors.END}")
            for error in self.results["errors"]:
                print(f"  - {error}")

        if self.results["warnings"]:
            print(f"\n{Colors.YELLOW}WARNINGS:{Colors.END}")
            for warning in self.results["warnings"]:
                print(f"  - {warning}")

        print(f"\n{Colors.BOLD}PERFORMANCE:{Colors.END}")
        for metric, value in self.results["metrics"].items():
            print(f"  {metric}: {value}")

        # Status final
        if success_rate == 100:
            print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] AUDIT COMPLET - TOUS TESTS PASSÉS{Colors.END}")
        elif success_rate >= 80:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARNING] AUDIT PARTIEL - {100-success_rate:.1f}% ÉCHOUÉS{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}[FAILURE] AUDIT ÉCHOUÉ - {100-success_rate:.1f}% ÉCHOUÉS{Colors.END}")

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "status": "SUCCESS" if success_rate == 100 else "PARTIAL" if success_rate >= 80 else "FAILED"
        }

        return self.results

    def save_report(self, filename: str = "audit_config_report.json"):
        """Sauvegarder rapport JSON."""
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj

        report_path = Path(__file__).parent / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(convert_decimals(self.results), f, indent=2)

        print(f"\n{Colors.CYAN}Rapport sauvegardé: {report_path}{Colors.END}")
        return report_path


def main():
    """Exécuter audit complet."""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("="*60)
    print("         AUDIT CONFIG SERVICE - PHASE 2 JOUR 4         ")
    print("="*60)
    print(Colors.END)

    try:
        with ConfigServiceAuditor() as auditor:
            # Exécuter tous les tests
            auditor.audit_schemas()
            auditor.audit_validation()
            auditor.audit_service_layer()
            auditor.audit_keepa_integration()
            auditor.audit_performance()

            # Générer et sauvegarder rapport
            report = auditor.generate_report()
            report_path = auditor.save_report()

            return report["summary"]["status"] == "SUCCESS"

    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}[CRITICAL ERROR] Audit failed: {e}{Colors.END}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)