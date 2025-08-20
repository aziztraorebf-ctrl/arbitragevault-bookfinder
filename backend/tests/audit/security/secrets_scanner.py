"""
Secrets scanner for audit suite
Scans code files for hardcoded secrets and sensitive information
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Set

from ..utils.metrics_collector import MetricsCollector


class SecretsScanner:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Patterns for detecting potential secrets
        self.secret_patterns = {
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'"]([a-zA-Z0-9_-]{20,})[\'"]'),
            'password': re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"]([^\'"\s]{8,})[\'"]'),
            'secret_key': re.compile(r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*[\'"]([a-zA-Z0-9_-]{20,})[\'"]'),
            'database_url': re.compile(r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*[\'"]([^\'"\s]+://[^\'"\s]+)[\'"]'),
            'jwt_secret': re.compile(r'(?i)(jwt[_-]?secret|token[_-]?secret)\s*[:=]\s*[\'"]([a-zA-Z0-9_-]{20,})[\'"]'),
            'aws_key': re.compile(r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret)\s*[:=]\s*[\'"]([A-Z0-9]{20,})[\'"]'),
            'private_key': re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----'),
            'openai_key': re.compile(r'sk-[a-zA-Z0-9]{48}'),
            'generic_secret': re.compile(r'(?i)(secret|token|key)\s*[:=]\s*[\'"]([a-zA-Z0-9_-]{32,})[\'"]')
        }
        
        # File extensions to scan
        self.scannable_extensions = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini'}
        
        # Files/directories to exclude
        self.exclude_patterns = {
            '.git', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache',
            'venv', '.venv', 'dist', 'build', '.ruff_cache'
        }
        
        # Known safe patterns (to reduce false positives)
        self.safe_patterns = {
            'your_secret_key',
            'changeme',
            'placeholder',
            'example_key',
            'test_key',
            'dummy_key',
            'fake_key',
            'sample_key'
        }
    
    async def scan(self) -> Dict[str, Any]:
        """Run comprehensive secrets scanning"""
        results = {
            'files_scanned': 0,
            'issues_found': 0,
            'findings': [],
            'summary': {}
        }
        
        print("    🔍 Scanning for hardcoded secrets...")
        
        # Scan all eligible files
        for file_path in self._get_scannable_files():
            try:
                file_results = await self._scan_file(file_path)
                if file_results['issues']:
                    results['findings'].extend(file_results['issues'])
                    results['issues_found'] += len(file_results['issues'])
                
                results['files_scanned'] += 1
                
                # Progress indicator
                if results['files_scanned'] % 50 == 0:
                    print(f"      📄 Scanned {results['files_scanned']} files...")
                    
            except Exception as e:
                print(f"      ⚠️  Error scanning {file_path}: {e}")
        
        # Generate summary
        results['summary'] = self._generate_summary(results['findings'])
        
        print(f"      ✅ Scan complete: {results['files_scanned']} files, {results['issues_found']} issues")
        
        return results
    
    def _get_scannable_files(self) -> List[Path]:
        """Get list of files to scan for secrets"""
        scannable_files = []
        
        def should_exclude(path: Path) -> bool:
            """Check if path should be excluded"""
            path_str = str(path)
            for exclude_pattern in self.exclude_patterns:
                if exclude_pattern in path_str:
                    return True
            return False
        
        # Recursively find scannable files
        for path in self.project_root.rglob('*'):
            if path.is_file() and not should_exclude(path):
                if path.suffix.lower() in self.scannable_extensions:
                    scannable_files.append(path)
        
        return sorted(scannable_files)
    
    async def _scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a single file for secrets"""
        issues = []
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Apply each pattern
            for pattern_name, pattern in self.secret_patterns.items():
                matches = pattern.finditer(content)
                
                for match in matches:
                    # Extract the potential secret
                    if len(match.groups()) >= 2:
                        secret_value = match.group(2)
                    else:
                        secret_value = match.group(0)
                    
                    # Check if it's a known safe pattern
                    if any(safe in secret_value.lower() for safe in self.safe_patterns):
                        continue
                    
                    # Get line number
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Create issue report
                    issue = {
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_number,
                        'pattern_type': pattern_name,
                        'matched_text': match.group(0)[:100],  # Truncate for safety
                        'severity': self._determine_severity(pattern_name, secret_value),
                        'recommendation': self._get_recommendation(pattern_name)
                    }
                    
                    issues.append(issue)
        
        except Exception as e:
            # File couldn't be read (binary, permissions, etc.)
            pass
        
        return {'issues': issues}
    
    def _determine_severity(self, pattern_type: str, secret_value: str) -> str:
        """Determine severity of a potential secret"""
        # High severity patterns
        high_severity = {
            'private_key', 'aws_key', 'openai_key'
        }
        
        # Medium severity patterns
        medium_severity = {
            'api_key', 'secret_key', 'jwt_secret', 'database_url'
        }
        
        if pattern_type in high_severity:
            return 'HIGH'
        elif pattern_type in medium_severity:
            return 'MEDIUM'
        else:
            # Check length and complexity for generic patterns
            if len(secret_value) > 40 and any(c.isdigit() for c in secret_value):
                return 'MEDIUM'
            else:
                return 'LOW'
    
    def _get_recommendation(self, pattern_type: str) -> str:
        """Get recommendation for fixing the issue"""
        recommendations = {
            'api_key': 'Move API key to environment variable',
            'password': 'Use environment variable or secure secret management',
            'secret_key': 'Use environment variable for secret key',
            'database_url': 'Use environment variable for database connection',
            'jwt_secret': 'Use environment variable for JWT secret',
            'aws_key': 'Use AWS IAM roles or environment variables',
            'private_key': 'Store private keys in secure key management system',
            'openai_key': 'Use environment variable for OpenAI API key',
            'generic_secret': 'Move to environment variable or config file'
        }
        
        return recommendations.get(pattern_type, 'Review and move to secure storage')
    
    def _generate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of findings"""
        if not findings:
            return {
                'status': 'CLEAN',
                'message': 'No hardcoded secrets detected'
            }
        
        # Count by severity
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for finding in findings:
            severity_counts[finding['severity']] += 1
        
        # Count by pattern type
        pattern_counts = {}
        for finding in findings:
            pattern_type = finding['pattern_type']
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        # Determine overall status
        if severity_counts['HIGH'] > 0:
            status = 'CRITICAL'
            message = f"Found {severity_counts['HIGH']} high-severity secrets"
        elif severity_counts['MEDIUM'] > 0:
            status = 'WARNING'
            message = f"Found {severity_counts['MEDIUM']} medium-severity potential secrets"
        else:
            status = 'INFO'
            message = f"Found {severity_counts['LOW']} low-severity potential secrets"
        
        return {
            'status': status,
            'message': message,
            'severity_breakdown': severity_counts,
            'pattern_breakdown': pattern_counts,
            'files_affected': len(set(f['file'] for f in findings))
        }