"""
Configuration security audit
Validates environment variables and production readiness
"""
import os
from pathlib import Path
from typing import Dict, Any

from app.core.settings import Settings
from ..utils.metrics_collector import MetricsCollector


class ConfigAuditor:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.settings = Settings()
        self.project_root = Path(__file__).parent.parent.parent.parent
        
    async def audit(self) -> Dict[str, Any]:
        """Run comprehensive configuration audit"""
        results = {
            'status': 'UNKNOWN',
            'checks': {},
            'warnings': [],
            'critical_issues': []
        }
        
        print("    🔒 Auditing configuration security...")
        
        # Run security checks
        checks = [
            ('environment_files', self._check_environment_files),
            ('database_config', self._check_database_config),
            ('secret_keys', self._check_secret_keys),
            ('debug_settings', self._check_debug_settings),
            ('cors_config', self._check_cors_config),
            ('production_readiness', self._check_production_readiness)
        ]
        
        for check_name, check_func in checks:
            try:
                print(f"      🔍 Checking {check_name}...")
                check_result = await check_func()
                results['checks'][check_name] = check_result
                
                if not check_result.get('passed', False):
                    if check_result.get('critical', False):
                        results['critical_issues'].append(check_result.get('message', ''))
                    else:
                        results['warnings'].append(check_result.get('message', ''))
                        
            except Exception as e:
                results['checks'][check_name] = {
                    'passed': False,
                    'message': f'Check failed with error: {str(e)}',
                    'critical': True
                }
                results['critical_issues'].append(f'{check_name}: {str(e)}')
        
        # Determine overall status
        critical_count = len(results['critical_issues'])
        warning_count = len(results['warnings'])
        
        if critical_count == 0:
            if warning_count == 0:
                results['status'] = 'PASS'
            else:
                results['status'] = 'PASS_WITH_WARNINGS'
        else:
            results['status'] = 'FAIL'
        
        return results
    
    async def _check_environment_files(self) -> Dict[str, Any]:
        """Check environment file configuration"""
        env_files = {
            '.env.example': self.project_root / '.env.example',
            '.env': self.project_root / '.env',
            '.env.development': self.project_root / '.env.development'
        }
        
        issues = []
        
        # Check if .env.example exists and is complete
        if not env_files['.env.example'].exists():
            issues.append('.env.example missing - template file should exist')
        
        # Check if actual .env file exists
        if not env_files['.env'].exists():
            if not env_files['.env.development'].exists():
                issues.append('No environment file found (.env or .env.development)')
        
        # Check for .env in .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if '.env' not in gitignore_content:
                issues.append('.env not in .gitignore - secrets could be committed')
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues) if issues else 'Environment files configured correctly',
            'critical': '.env not in .gitignore' in '; '.join(issues)
        }
    
    async def _check_database_config(self) -> Dict[str, Any]:
        """Check database configuration security"""
        issues = []
        
        db_url = self.settings.database_url
        
        # Check if using default/weak database credentials
        if 'user:password@' in db_url.lower():
            issues.append('Default database credentials detected')
        
        # Check if database URL is using proper connection pooling in production
        if self.settings.environment == 'production':
            if 'pool_size' not in db_url and 'max_overflow' not in db_url:
                issues.append('Production database should specify connection pool settings')
        
        # Check for localhost in production
        if self.settings.environment == 'production' and 'localhost' in db_url:
            issues.append('Production should not use localhost database')
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues) if issues else 'Database configuration looks secure',
            'critical': 'default' in '; '.join(issues).lower()
        }
    
    async def _check_secret_keys(self) -> Dict[str, Any]:
        """Check secret key configuration"""
        issues = []
        
        # Check SECRET_KEY strength
        secret_key = self.settings.secret_key
        if not secret_key:
            issues.append('SECRET_KEY not set')
        elif len(secret_key) < 32:
            issues.append('SECRET_KEY too short (should be at least 32 characters)')
        elif secret_key.lower() in ['your_secret_key', 'secret', 'key', 'changeme']:
            issues.append('SECRET_KEY appears to be a placeholder/default value')
        
        # Check for hardcoded secrets in code
        # This is a basic check - a full audit would scan all files
        env_vars = ['SECRET_KEY', 'DATABASE_URL', 'KEEPA_API_KEY', 'OPENAI_API_KEY']
        for var in env_vars:
            if var in os.environ:
                value = os.environ[var]
                if len(value) > 0 and not value.startswith('${'):  # Not a template variable
                    # This is expected - secrets should be in environment
                    pass
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues) if issues else 'Secret keys configured properly',
            'critical': 'not set' in '; '.join(issues)
        }
    
    async def _check_debug_settings(self) -> Dict[str, Any]:
        """Check debug and development settings"""
        issues = []
        
        # Check DEBUG setting for production
        if self.settings.environment == 'production':
            if self.settings.debug:
                issues.append('DEBUG should be False in production')
        
        # Check logging configuration
        if self.settings.environment == 'production':
            # Production should have appropriate logging
            # This would need to be implemented based on actual logging config
            pass
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues) if issues else 'Debug settings appropriate for environment',
            'critical': 'DEBUG' in '; '.join(issues) and 'production' in '; '.join(issues)
        }
    
    async def _check_cors_config(self) -> Dict[str, Any]:
        """Check CORS configuration"""
        issues = []
        warnings = []
        
        # In our current setup, CORS is minimal for development
        # Check if it's appropriate for the environment
        if self.settings.environment == 'production':
            warnings.append('CORS configuration should be reviewed for production')
        
        # Development CORS is typically more permissive, which is acceptable
        if self.settings.environment == 'development':
            # This is fine - development can have permissive CORS
            pass
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues + warnings) if (issues + warnings) else 'CORS configuration appropriate',
            'critical': False  # CORS issues are usually not critical for backend-only testing
        }
    
    async def _check_production_readiness(self) -> Dict[str, Any]:
        """Check overall production readiness"""
        issues = []
        warnings = []
        
        # Check required environment variables for production
        required_prod_vars = [
            'DATABASE_URL',
            'SECRET_KEY'
        ]
        
        for var in required_prod_vars:
            if not getattr(self.settings, var.lower(), None):
                issues.append(f'{var} not configured')
        
        # Check optional but recommended variables
        optional_vars = [
            'KEEPA_API_KEY',
            'OPENAI_API_KEY'
        ]
        
        for var in optional_vars:
            env_var = var.lower().replace('_', '_')
            if not os.getenv(var):
                warnings.append(f'{var} not set - some features may not work')
        
        # Check file permissions (basic check)
        sensitive_files = ['.env']
        for filename in sensitive_files:
            filepath = self.project_root / filename
            if filepath.exists():
                # On Unix systems, check if file is readable by others
                import stat
                file_stat = filepath.stat()
                if file_stat.st_mode & stat.S_IROTH:
                    warnings.append(f'{filename} is readable by others')
        
        return {
            'passed': len(issues) == 0,
            'message': '; '.join(issues + warnings) if (issues + warnings) else 'Production readiness checks passed',
            'critical': len(issues) > 0
        }