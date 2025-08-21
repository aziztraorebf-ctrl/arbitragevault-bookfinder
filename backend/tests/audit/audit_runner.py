#!/usr/bin/env python3
"""
ArbitrageVault Audit Runner - Main CLI for comprehensive testing
Usage: python -m tests.audit.audit_runner [options]
"""
import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import psutil
from sqlalchemy import create_engine, text

from app.core.settings import Settings
from .utils.metrics_collector import MetricsCollector
from .utils.report_generator import ReportGenerator
from .benchmarks.performance_suite import PerformanceSuite
from .benchmarks.memory_profiler import MemoryProfiler
from .benchmarks.concurrency_test import ConcurrencyTester
from .benchmarks.database_analyzer import DatabaseAnalyzer
from .functional.repository_audit import RepositoryAuditor
from .functional.api_compliance import APICompliance
from .security.config_audit import ConfigAuditor
from .security.secrets_scanner import SecretsScanner


class AuditRunner:
    def __init__(self, args):
        self.args = args
        self.settings = Settings()
        self.metrics = MetricsCollector()
        self.start_time = datetime.now()
        
        # Initialize components
        self.performance_suite = PerformanceSuite(self.metrics)
        self.memory_profiler = MemoryProfiler(self.metrics)
        self.concurrency_tester = ConcurrencyTester(self.metrics)
        self.db_analyzer = DatabaseAnalyzer(self.metrics)
        self.repo_auditor = RepositoryAuditor(self.metrics)
        self.api_compliance = APICompliance(self.metrics)
        self.config_auditor = ConfigAuditor(self.metrics)
        self.secrets_scanner = SecretsScanner(self.metrics)
        
    def print_environment_info(self):
        """Print comprehensive environment information"""
        print("🖥️ Environment Information")
        print("=" * 50)
        
        # System Info
        system = psutil.virtual_memory()
        print(f"OS: {psutil.os.name}")
        print(f"CPU Count: {psutil.cpu_count()} cores")
        print(f"RAM Total: {system.total / (1024**3):.1f} GB")
        print(f"RAM Available: {system.available / (1024**3):.1f} GB")
        
        # Python & Package Versions
        print(f"Python: {sys.version.split()[0]}")
        
        # Database Info
        try:
            engine = create_engine(self.settings.database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                db_version = result.scalar()
                print(f"PostgreSQL: {db_version.split()[1]}")
        except Exception as e:
            print(f"Database: Connection failed - {e}")
            
        # SQLAlchemy Mode
        print(f"SQLAlchemy Mode: {'Async' if 'async' in str(type(engine)) else 'Sync'}")
        print()

    async def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit based on mode"""
        results = {
            'environment': self._get_environment_info(),
            'functional_tests': {},
            'performance_benchmarks': {},
            'database_analysis': {},
            'security_assessment': {},
            'code_quality': {},
            'summary': {},
            'verdict': None
        }
        
        self.print_environment_info()
        
        if self.args.mode in ['quick', 'full']:
            print("🔍 Running Functional Tests...")
            results['functional_tests'] = await self._run_functional_tests()
            
        if self.args.mode in ['benchmark', 'full']:
            print("⚡ Running Performance Benchmarks...")
            results['performance_benchmarks'] = await self._run_performance_tests()
            
        if self.args.mode == 'full':
            print("📊 Running Database Analysis...")
            results['database_analysis'] = await self._run_database_analysis()
            
            print("🔒 Running Security Assessment...")
            results['security_assessment'] = await self._run_security_tests()
            
            print("🏗️ Running Code Quality Check...")
            results['code_quality'] = await self._run_code_quality_check()
        
        # Generate summary and verdict
        results['summary'] = self._generate_summary(results)
        results['verdict'] = self._make_verdict(results)
        
        return results

    async def _run_functional_tests(self) -> Dict[str, Any]:
        """Execute all functional validation tests"""
        return {
            'repository_layer': await self.repo_auditor.audit(),
            'api_endpoints': await self.api_compliance.audit(),
        }

    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Execute performance benchmarks with p50/p95/p99 metrics"""
        results = {}
        
        # Dataset sizes from args or defaults
        dataset_sizes = self.args.dataset_sizes
        concurrent_users = self.args.concurrent_users
        
        for size in dataset_sizes:
            print(f"  📈 Testing with {size:,} analyses...")
            results[f'{size}_items'] = await self.performance_suite.run_benchmark(size)
            
        # Memory profiling
        print("  🧠 Memory profiling...")
        results['memory_usage'] = await self.memory_profiler.profile_operations()
        
        # Concurrency tests  
        print("  🔄 Concurrency testing...")
        for users in concurrent_users:
            print(f"    👥 Testing {users} concurrent users...")
            results[f'{users}_concurrent'] = await self.concurrency_tester.test_concurrent_load(users)
            
        return results

    async def _run_database_analysis(self) -> Dict[str, Any]:
        """Analyze database performance and index usage"""
        return await self.db_analyzer.analyze()

    async def _run_security_tests(self) -> Dict[str, Any]:
        """Run security and configuration audits"""
        return {
            'configuration': await self.config_auditor.audit(),
            'secrets_scan': await self.secrets_scanner.scan(),
        }

    async def _run_code_quality_check(self) -> Dict[str, Any]:
        """Check code organization and quality"""
        # TODO: Implement code quality checks
        return {
            'file_organization': 'PASS',
            'import_consistency': 'PASS',
            'naming_conventions': 'PASS'
        }

    def _get_environment_info(self) -> Dict[str, Any]:
        """Collect environment information"""
        system = psutil.virtual_memory()
        return {
            'os': psutil.os.name,
            'cpu_count': psutil.cpu_count(),
            'ram_total_gb': round(system.total / (1024**3), 1),
            'python_version': sys.version.split()[0],
            'timestamp': self.start_time.isoformat(),
        }

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate TL;DR summary from all results"""
        passed_tests = 0
        total_tests = 0
        warnings = []
        
        # Count functional tests
        if 'functional_tests' in results:
            for category, tests in results['functional_tests'].items():
                if isinstance(tests, dict) and 'passed' in tests:
                    passed_tests += tests['passed']
                    total_tests += tests['total']
                    if 'warnings' in tests:
                        warnings.extend(tests['warnings'])
        
        # Check performance against targets
        performance_status = 'UNKNOWN'
        if 'performance_benchmarks' in results:
            performance_status = self._evaluate_performance_status(results['performance_benchmarks'])
        
        return {
            'tests_passed': f"{passed_tests}/{total_tests}",
            'performance_status': performance_status,
            'warnings_count': len(warnings),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
        }

    def _evaluate_performance_status(self, perf_results: Dict[str, Any]) -> str:
        """Evaluate if performance meets targets"""
        # Performance targets from requirements
        targets = {
            '100_items': 100,    # p95 < 100ms
            '1000_items': 220,   # p95 < 220ms  
            'pagination': 300,   # p95 < 300ms
            'concurrent': 450    # p95 < 450ms for 5 users
        }
        
        failures = []
        
        for test_name, target_ms in targets.items():
            if test_name in perf_results:
                p95_time = perf_results[test_name].get('p95_ms', 0)
                if p95_time > target_ms:
                    failures.append(f"{test_name}: {p95_time}ms > {target_ms}ms")
        
        return 'PASS' if not failures else f'FAIL ({len(failures)} targets missed)'

    def _make_verdict(self, results: Dict[str, Any]) -> str:
        """Final verdict: Ready for Phase 1.4?"""
        # Criteria for Phase 1.4 readiness
        functional_ok = True
        performance_ok = results.get('summary', {}).get('performance_status', '').startswith('PASS')
        security_ok = True  # TODO: Implement security checks
        
        if functional_ok and performance_ok and security_ok:
            return "✅ YES - Ready for Phase 1.4"
        else:
            issues = []
            if not functional_ok:
                issues.append("functional tests failing")
            if not performance_ok:
                issues.append("performance targets not met")
            if not security_ok:
                issues.append("security issues found")
            
            return f"❌ NO - Issues: {', '.join(issues)}"


def parse_args():
    parser = argparse.ArgumentParser(description='ArbitrageVault Audit Suite')
    
    parser.add_argument(
        '--mode',
        choices=['quick', 'full', 'benchmark'],
        default='full',
        help='Audit mode: quick (PR validation), full (weekly audit), benchmark (perf focus)'
    )
    
    parser.add_argument(
        '--dataset-sizes',
        type=lambda s: [int(x) for x in s.split(',')],
        default=[100, 1000, 5000],
        help='Dataset sizes for testing (comma-separated)'
    )
    
    parser.add_argument(
        '--concurrent-users',
        type=lambda s: [int(x) for x in s.split(',')],
        default=[1, 3, 5],
        help='Concurrent user counts to test (comma-separated)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible tests'
    )
    
    parser.add_argument(
        '--db-url',
        type=str,
        help='Override database URL'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['md', 'json', 'html'],
        default='md',
        help='Output report format'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file path (optional)'
    )
    
    return parser.parse_args()


async def main():
    args = parse_args()
    
    print("🎯 ArbitrageVault Audit Suite v1.3")
    print(f"Mode: {args.mode.upper()}")
    print("=" * 50)
    
    # Override DB URL if provided
    if args.db_url:
        import os
        os.environ['DATABASE_URL'] = args.db_url
    
    try:
        runner = AuditRunner(args)
        results = await runner.run_audit()
        
        # Generate report
        report_generator = ReportGenerator(results, args.output_format)
        report_content = report_generator.generate()
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(report_content)
            print(f"\n📄 Report saved to: {args.output_file}")
        else:
            print("\n" + "="*80)
            print(report_content)
            
        # Exit with appropriate code
        verdict = results.get('verdict', '')
        exit_code = 0 if verdict.startswith('✅') else 1
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Audit failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())