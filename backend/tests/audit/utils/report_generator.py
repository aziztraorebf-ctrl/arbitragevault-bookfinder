"""
Report generation utilities for audit suite
Generates comprehensive Markdown reports with all audit results
"""
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class ReportGenerator:
    def __init__(self, results: Dict[str, Any], output_format: str = 'md'):
        self.results = results
        self.output_format = output_format
        self.timestamp = datetime.now()
    
    def generate(self) -> str:
        """Generate report in specified format"""
        if self.output_format == 'md':
            return self._generate_markdown()
        elif self.output_format == 'json':
            return self._generate_json()
        elif self.output_format == 'html':
            return self._generate_html()
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}")
    
    def _generate_markdown(self) -> str:
        """Generate comprehensive Markdown audit report"""
        report = []
        
        # Header
        report.append("# ArbitrageVault Audit Report v1.3")
        report.append("")
        report.append(f"**Generated**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # TL;DR Summary
        report.extend(self._generate_tldr_section())
        
        # Verdict
        verdict = self.results.get('verdict', 'UNKNOWN')
        status_icon = "✅" if verdict.startswith('✅') else "❌"
        report.append(f"## 🎯 Verdict: {verdict}")
        report.append("")
        
        # Environment Info
        report.extend(self._generate_environment_section())
        
        # Functional Tests
        if 'functional_tests' in self.results:
            report.extend(self._generate_functional_section())
        
        # Performance Benchmarks
        if 'performance_benchmarks' in self.results:
            report.extend(self._generate_performance_section())
        
        # Database Analysis
        if 'database_analysis' in self.results:
            report.extend(self._generate_database_section())
        
        # Security Assessment
        if 'security_assessment' in self.results:
            report.extend(self._generate_security_section())
        
        # Code Quality
        if 'code_quality' in self.results:
            report.extend(self._generate_code_quality_section())
        
        return '\n'.join(report)
    
    def _generate_tldr_section(self) -> List[str]:
        """Generate TL;DR summary section"""
        summary = self.results.get('summary', {})
        
        lines = [
            "## 📈 TL;DR Summary",
            "",
            f"**Tests Passed**: {summary.get('tests_passed', 'Unknown')}",
            f"**Performance Status**: {summary.get('performance_status', 'Unknown')}",
            f"**Warnings**: {summary.get('warnings_count', 0)}",
            f"**Duration**: {summary.get('duration_seconds', 0):.1f}s",
            ""
        ]
        
        return lines
    
    def _generate_environment_section(self) -> List[str]:
        """Generate environment information section"""
        env = self.results.get('environment', {})
        
        lines = [
            "## 🖥️ Environment Information",
            "",
            f"**Operating System**: {env.get('os', 'Unknown')}",
            f"**CPU Cores**: {env.get('cpu_count', 'Unknown')}",
            f"**Total RAM**: {env.get('ram_total_gb', 'Unknown')} GB",
            f"**Python Version**: {env.get('python_version', 'Unknown')}",
            f"**SQLAlchemy Mode**: Sync", # We know this from our architecture
            ""
        ]
        
        return lines
    
    def _generate_functional_section(self) -> List[str]:
        """Generate functional tests section"""
        functional = self.results.get('functional_tests', {})
        
        lines = [
            "## ✅ Functional Tests",
            ""
        ]
        
        # Repository Layer Tests
        repo_tests = functional.get('repository_layer', {})
        if repo_tests:
            lines.extend([
                "### Repository Layer",
                "",
                f"**Status**: {repo_tests.get('status', 'Unknown')}",
                f"**Tests Passed**: {repo_tests.get('passed', 0)}/{repo_tests.get('total', 0)}",
                ""
            ])
            
            if 'details' in repo_tests:
                for test_name, result in repo_tests['details'].items():
                    status_icon = "✅" if result.get('status') == 'PASS' else "❌"
                    lines.append(f"- {status_icon} {test_name}: {result.get('message', '')}")
                lines.append("")
        
        # API Compliance Tests
        api_tests = functional.get('api_endpoints', {})
        if api_tests:
            lines.extend([
                "### API Endpoints",
                "",
                f"**Status**: {api_tests.get('status', 'Unknown')}",
                f"**Endpoints Tested**: {api_tests.get('endpoints_tested', 0)}",
                ""
            ])
            
            if 'endpoint_results' in api_tests:
                for endpoint, result in api_tests['endpoint_results'].items():
                    status_icon = "✅" if result.get('status') == 'PASS' else "❌"
                    lines.append(f"- {status_icon} `{endpoint}`: {result.get('message', '')}")
                lines.append("")
        
        return lines
    
    def _generate_performance_section(self) -> List[str]:
        """Generate performance benchmarks section"""
        perf = self.results.get('performance_benchmarks', {})
        
        lines = [
            "## ⚡ Performance Benchmarks",
            "",
            "### Response Time Targets",
            "",
            "| Test Case | Target (p95) | Actual (p95) | Status |",
            "|-----------|--------------|--------------|--------|"
        ]
        
        # Define targets for comparison
        targets = {
            '100_items': 100,
            '1000_items': 220,
            '5000_items': 300,  # Assuming similar to pagination
            '5_concurrent': 450
        }
        
        for test_key, target_ms in targets.items():
            if test_key in perf:
                result = perf[test_key]
                actual_p95 = result.get('p95_ms', 0)
                status = "✅ PASS" if actual_p95 <= target_ms else "❌ FAIL"
                lines.append(f"| {test_key.replace('_', ' ')} | {target_ms}ms | {actual_p95:.1f}ms | {status} |")
        
        lines.extend(["", "### Detailed Performance Metrics", ""])
        
        # Detailed metrics for each test
        for test_name, metrics in perf.items():
            if isinstance(metrics, dict) and 'p95_ms' in metrics:
                lines.extend([
                    f"#### {test_name.replace('_', ' ').title()}",
                    "",
                    f"- **Count**: {metrics.get('count', 0)} iterations",
                    f"- **Mean**: {metrics.get('mean_ms', 0):.1f}ms",
                    f"- **p50**: {metrics.get('p50_ms', 0):.1f}ms",
                    f"- **p95**: {metrics.get('p95_ms', 0):.1f}ms",
                    f"- **p99**: {metrics.get('p99_ms', 0):.1f}ms",
                    f"- **Max**: {metrics.get('max_ms', 0):.1f}ms",
                    ""
                ])
        
        # Memory Usage
        if 'memory_usage' in perf:
            memory = perf['memory_usage']
            lines.extend([
                "### Memory Usage",
                "",
                f"**RSS Peak**: {memory.get('peak_rss_mb', 0):.1f} MB",
                f"**Memory Delta**: {memory.get('delta_mb', 0):.1f} MB",
                f"**Target**: < 100 MB for 10k analyses",
                ""
            ])
        
        return lines
    
    def _generate_database_section(self) -> List[str]:
        """Generate database analysis section"""
        db = self.results.get('database_analysis', {})
        
        lines = [
            "## 📊 Database Analysis",
            ""
        ]
        
        # Index Usage
        if 'index_usage' in db:
            lines.extend([
                "### Index Usage Analysis",
                "",
                "| Query | Index Used | Seq Scan | Status |",
                "|-------|------------|----------|--------|"
            ])
            
            for query_name, analysis in db['index_usage'].items():
                index_used = analysis.get('index_used', False)
                seq_scan = analysis.get('seq_scan_detected', True)
                status = "✅ PASS" if index_used and not seq_scan else "⚠️ WARNING"
                lines.append(f"| {query_name} | {index_used} | {seq_scan} | {status} |")
            
            lines.append("")
        
        # Query Performance  
        if 'query_performance' in db:
            lines.extend([
                "### Query Performance",
                ""
            ])
            
            for query, perf in db['query_performance'].items():
                lines.extend([
                    f"#### {query}",
                    f"- **Execution Time**: {perf.get('execution_time_ms', 0):.1f}ms",
                    f"- **Rows Processed**: {perf.get('rows', 0):,}",
                    f"- **Index Hits**: {perf.get('index_hits', 0)}",
                    ""
                ])
        
        return lines
    
    def _generate_security_section(self) -> List[str]:
        """Generate security assessment section"""
        security = self.results.get('security_assessment', {})
        
        lines = [
            "## 🔒 Security Assessment",
            ""
        ]
        
        # Configuration Audit
        config = security.get('configuration', {})
        if config:
            lines.extend([
                "### Configuration Security",
                "",
                f"**Status**: {config.get('status', 'Unknown')}",
                ""
            ])
            
            for check_name, result in config.get('checks', {}).items():
                status_icon = "✅" if result.get('passed', False) else "⚠️"
                lines.append(f"- {status_icon} {check_name}: {result.get('message', '')}")
            
            lines.append("")
        
        # Secrets Scan
        secrets = security.get('secrets_scan', {})
        if secrets:
            lines.extend([
                "### Secrets Scanning",
                "",
                f"**Files Scanned**: {secrets.get('files_scanned', 0)}",
                f"**Issues Found**: {secrets.get('issues_found', 0)}",
                ""
            ])
        
        return lines
    
    def _generate_code_quality_section(self) -> List[str]:
        """Generate code quality section"""
        quality = self.results.get('code_quality', {})
        
        lines = [
            "## 🏗️ Code Quality Assessment",
            "",
            f"**File Organization**: {quality.get('file_organization', 'Unknown')}",
            f"**Import Consistency**: {quality.get('import_consistency', 'Unknown')}",
            f"**Naming Conventions**: {quality.get('naming_conventions', 'Unknown')}",
            ""
        ]
        
        return lines
    
    def _generate_json(self) -> str:
        """Generate JSON format report"""
        return json.dumps(self.results, indent=2, default=str)
    
    def _generate_html(self) -> str:
        """Generate HTML format report"""
        # Convert markdown to HTML (basic implementation)
        md_content = self._generate_markdown()
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ArbitrageVault Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .warning {{ color: orange; }}
    </style>
</head>
<body>
    <pre>{md_content}</pre>
</body>
</html>
        """
        
        return html_template.strip()