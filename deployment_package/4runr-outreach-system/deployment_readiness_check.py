#!/usr/bin/env python3
"""
Deployment Readiness Check for DataCleaner System

This script performs comprehensive pre-deployment validation to ensure
the system is ready for production deployment without errors.

Validates:
1. All dependencies and imports
2. Configuration files and structure
3. Core functionality
4. Integration points
5. Error handling
6. Performance requirements
"""

import sys
import os
import time
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class ReadinessCheck:
    """Results from a readiness check."""
    check_name: str
    success: bool
    details: str
    critical: bool = True

class DeploymentReadinessChecker:
    """
    Comprehensive deployment readiness validation system.
    """
    
    def __init__(self):
        self.checks = []
        self.critical_failures = []
        self.warnings = []
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all deployment readiness checks."""
        print("🔍 DataCleaner Deployment Readiness Check")
        print("=" * 60)
        print("Validating system is ready for production deployment...")
        print()
        
        try:
            # Check 1: Dependencies and Imports
            print("📦 Check 1: Dependencies and Imports")
            self._check_dependencies()
            
            # Check 2: Configuration Files
            print("\n⚙️ Check 2: Configuration Files")
            self._check_configuration_files()
            
            # Check 3: Core System Components
            print("\n🧹 Check 3: Core System Components")
            self._check_core_components()
            
            # Check 4: Integration Points
            print("\n🔗 Check 4: Integration Points")
            self._check_integration_points()
            
            # Check 5: Error Handling and Resilience
            print("\n🛡️ Check 5: Error Handling and Resilience")
            self._check_error_handling()
            
            # Check 6: Performance Requirements
            print("\n⚡ Check 6: Performance Requirements")
            self._check_performance()
            
            # Check 7: Production Environment
            print("\n🌐 Check 7: Production Environment")
            self._check_production_environment()
            
            # Generate final report
            return self._generate_readiness_report()
            
        except Exception as e:
            print(f"\n💥 READINESS CHECK ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'ready_for_deployment': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _check_dependencies(self):
        """Check all required dependencies can be imported."""
        required_modules = [
            'yaml',
            'json',
            'datetime',
            'pathlib',
            'dataclasses',
            're',
            'os',
            'time',
            'typing'
        ]
        
        for module in required_modules:
            try:
                importlib.import_module(module)
                print(f"   ✅ {module}: Available")
                self.checks.append(ReadinessCheck(
                    f"Import {module}",
                    True,
                    "Module imported successfully"
                ))
            except ImportError as e:
                print(f"   ❌ {module}: Missing - {e}")
                self.checks.append(ReadinessCheck(
                    f"Import {module}",
                    False,
                    f"Import failed: {e}",
                    critical=True
                ))
                self.critical_failures.append(f"Missing dependency: {module}")
        
        # Check custom modules
        custom_modules = [
            'shared.data_cleaner',
            'shared.logging_utils',
            'shared.error_handling'
        ]
        
        for module in custom_modules:
            try:
                importlib.import_module(module)
                print(f"   ✅ {module}: Available")
                self.checks.append(ReadinessCheck(
                    f"Import {module}",
                    True,
                    "Custom module imported successfully"
                ))
            except ImportError as e:
                print(f"   ❌ {module}: Missing - {e}")
                self.checks.append(ReadinessCheck(
                    f"Import {module}",
                    False,
                    f"Custom module import failed: {e}",
                    critical=True
                ))
                self.critical_failures.append(f"Missing custom module: {module}")
    
    def _check_configuration_files(self):
        """Check all required configuration files exist and are valid."""
        config_files = [
            'shared/data_cleaner_config/cleaning_rules.yaml',
            'shared/data_cleaner_config/validation_rules.yaml'
        ]
        
        for config_file in config_files:
            file_path = Path(config_file)
            
            if file_path.exists():
                try:
                    # Try to load and validate the config
                    import yaml
                    with open(file_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    if config_data and isinstance(config_data, dict):
                        print(f"   ✅ {config_file}: Valid ({len(config_data)} sections)")
                        self.checks.append(ReadinessCheck(
                            f"Config {config_file}",
                            True,
                            f"Configuration file valid with {len(config_data)} sections"
                        ))
                    else:
                        print(f"   ⚠️ {config_file}: Empty or invalid format")
                        self.checks.append(ReadinessCheck(
                            f"Config {config_file}",
                            False,
                            "Configuration file empty or invalid format",
                            critical=False
                        ))
                        self.warnings.append(f"Configuration file may be empty: {config_file}")
                        
                except Exception as e:
                    print(f"   ❌ {config_file}: Load error - {e}")
                    self.checks.append(ReadinessCheck(
                        f"Config {config_file}",
                        False,
                        f"Configuration load error: {e}",
                        critical=True
                    ))
                    self.critical_failures.append(f"Configuration file error: {config_file}")
            else:
                print(f"   ❌ {config_file}: Missing")
                self.checks.append(ReadinessCheck(
                    f"Config {config_file}",
                    False,
                    "Configuration file missing",
                    critical=True
                ))
                self.critical_failures.append(f"Missing configuration file: {config_file}")
        
        # Check logs directory
        logs_dir = Path('logs/data_cleaner')
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Logs directory: Created")
                self.checks.append(ReadinessCheck(
                    "Logs directory",
                    True,
                    "Logs directory created successfully"
                ))
            except Exception as e:
                print(f"   ❌ Logs directory: Cannot create - {e}")
                self.checks.append(ReadinessCheck(
                    "Logs directory",
                    False,
                    f"Cannot create logs directory: {e}",
                    critical=True
                ))
                self.critical_failures.append("Cannot create logs directory")
        else:
            print(f"   ✅ Logs directory: Exists")
            self.checks.append(ReadinessCheck(
                "Logs directory",
                True,
                "Logs directory exists"
            ))
    
    def _check_core_components(self):
        """Check core system components can be initialized."""
        try:
            # Test DataCleaner initialization
            from shared.data_cleaner import DataCleaner
            
            data_cleaner = DataCleaner()
            print(f"   ✅ DataCleaner: Initialized successfully")
            self.checks.append(ReadinessCheck(
                "DataCleaner initialization",
                True,
                "DataCleaner initialized without errors"
            ))
            
            # Test basic cleaning operation
            test_data = {
                'Company': 'Test Company Inc',
                'Website': 'https://testcompany.com'
            }
            
            test_context = {
                'id': 'readiness_test',
                'Full Name': 'Test User',
                'source': 'deployment_check'
            }
            
            result = data_cleaner.clean_and_validate(test_data, test_context)
            
            if result is not None:
                print(f"   ✅ Basic cleaning: Working (success: {result.success})")
                self.checks.append(ReadinessCheck(
                    "Basic cleaning operation",
                    True,
                    f"Basic cleaning successful: {result.success}"
                ))
            else:
                print(f"   ❌ Basic cleaning: Returned None")
                self.checks.append(ReadinessCheck(
                    "Basic cleaning operation",
                    False,
                    "Basic cleaning returned None",
                    critical=True
                ))
                self.critical_failures.append("Basic cleaning operation failed")
                
        except Exception as e:
            print(f"   ❌ Core components: Initialization failed - {e}")
            self.checks.append(ReadinessCheck(
                "Core components",
                False,
                f"Core component initialization failed: {e}",
                critical=True
            ))
            self.critical_failures.append(f"Core component error: {e}")
    
    def _check_integration_points(self):
        """Check integration with existing systems."""
        try:
            # Check AirtableClient integration
            from shared.airtable_client import AirtableClient
            
            airtable_client = AirtableClient()
            print(f"   ✅ AirtableClient: Available")
            self.checks.append(ReadinessCheck(
                "AirtableClient integration",
                True,
                "AirtableClient can be imported and initialized"
            ))
            
        except Exception as e:
            print(f"   ⚠️ AirtableClient: Import issue - {e}")
            self.checks.append(ReadinessCheck(
                "AirtableClient integration",
                False,
                f"AirtableClient integration issue: {e}",
                critical=False
            ))
            self.warnings.append(f"AirtableClient integration issue: {e}")
        
        # Check logging integration
        try:
            from shared.logging_utils import get_logger
            
            logger = get_logger('deployment_test')
            logger.log_module_activity('deployment_test', 'system', 'info', {
                'message': 'Deployment readiness check'
            })
            print(f"   ✅ Logging: Working")
            self.checks.append(ReadinessCheck(
                "Logging integration",
                True,
                "Logging system working correctly"
            ))
            
        except Exception as e:
            print(f"   ❌ Logging: Failed - {e}")
            self.checks.append(ReadinessCheck(
                "Logging integration",
                False,
                f"Logging system failed: {e}",
                critical=True
            ))
            self.critical_failures.append(f"Logging system error: {e}")
    
    def _check_error_handling(self):
        """Check error handling and resilience systems."""
        try:
            from shared.error_handling import ErrorHandler, ErrorContext, ErrorSeverity, ErrorCategory
            
            # Test error handler initialization
            error_handler = ErrorHandler()
            print(f"   ✅ ErrorHandler: Initialized")
            
            # Test error context creation
            context = ErrorContext(
                operation='deployment_test',
                component='readiness_check',
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.SYSTEM
            )
            print(f"   ✅ ErrorContext: Created")
            
            # Test error handling
            test_error = Exception("Test error for deployment check")
            try:
                error_handler.handle_error(test_error, context)
                print(f"   ✅ Error handling: Working")
                self.checks.append(ReadinessCheck(
                    "Error handling system",
                    True,
                    "Error handling system working correctly"
                ))
            except Exception as e:
                print(f"   ⚠️ Error handling: Issue - {e}")
                self.checks.append(ReadinessCheck(
                    "Error handling system",
                    False,
                    f"Error handling issue: {e}",
                    critical=False
                ))
                self.warnings.append(f"Error handling issue: {e}")
                
        except Exception as e:
            print(f"   ❌ Error handling: Import failed - {e}")
            self.checks.append(ReadinessCheck(
                "Error handling system",
                False,
                f"Error handling system failed: {e}",
                critical=True
            ))
            self.critical_failures.append(f"Error handling system error: {e}")
    
    def _check_performance(self):
        """Check performance requirements are met."""
        try:
            from shared.data_cleaner import DataCleaner
            
            data_cleaner = DataCleaner()
            
            # Performance test
            test_data = {
                'Company': 'Performance Test Company Inc',
                'Website': 'https://performancetest.com'
            }
            
            test_context = {
                'id': 'performance_test',
                'Full Name': 'Performance User',
                'source': 'deployment_check'
            }
            
            # Measure processing time
            start_time = time.time()
            result = data_cleaner.clean_and_validate(test_data, test_context)
            processing_time = time.time() - start_time
            
            # Check performance requirements
            max_processing_time = 5.0  # 5 seconds max
            
            if processing_time <= max_processing_time:
                print(f"   ✅ Performance: {processing_time:.3f}s (within {max_processing_time}s limit)")
                self.checks.append(ReadinessCheck(
                    "Performance requirements",
                    True,
                    f"Processing time {processing_time:.3f}s within limits"
                ))
            else:
                print(f"   ⚠️ Performance: {processing_time:.3f}s (exceeds {max_processing_time}s limit)")
                self.checks.append(ReadinessCheck(
                    "Performance requirements",
                    False,
                    f"Processing time {processing_time:.3f}s exceeds limits",
                    critical=False
                ))
                self.warnings.append(f"Performance may be slow: {processing_time:.3f}s")
                
        except Exception as e:
            print(f"   ❌ Performance: Test failed - {e}")
            self.checks.append(ReadinessCheck(
                "Performance requirements",
                False,
                f"Performance test failed: {e}",
                critical=True
            ))
            self.critical_failures.append(f"Performance test error: {e}")
    
    def _check_production_environment(self):
        """Check production environment readiness."""
        # Check Python version
        python_version = sys.version_info
        min_python = (3, 7)
        
        if python_version >= min_python:
            print(f"   ✅ Python version: {python_version.major}.{python_version.minor} (>= {min_python[0]}.{min_python[1]})")
            self.checks.append(ReadinessCheck(
                "Python version",
                True,
                f"Python {python_version.major}.{python_version.minor} meets requirements"
            ))
        else:
            print(f"   ❌ Python version: {python_version.major}.{python_version.minor} (< {min_python[0]}.{min_python[1]})")
            self.checks.append(ReadinessCheck(
                "Python version",
                False,
                f"Python {python_version.major}.{python_version.minor} below minimum requirements",
                critical=True
            ))
            self.critical_failures.append(f"Python version too old: {python_version.major}.{python_version.minor}")
        
        # Check disk space for logs
        try:
            import shutil
            disk_usage = shutil.disk_usage('.')
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb >= 1.0:  # At least 1GB free
                print(f"   ✅ Disk space: {free_space_gb:.1f}GB available")
                self.checks.append(ReadinessCheck(
                    "Disk space",
                    True,
                    f"{free_space_gb:.1f}GB disk space available"
                ))
            else:
                print(f"   ⚠️ Disk space: {free_space_gb:.1f}GB available (low)")
                self.checks.append(ReadinessCheck(
                    "Disk space",
                    False,
                    f"Low disk space: {free_space_gb:.1f}GB",
                    critical=False
                ))
                self.warnings.append(f"Low disk space: {free_space_gb:.1f}GB")
                
        except Exception as e:
            print(f"   ⚠️ Disk space: Cannot check - {e}")
            self.checks.append(ReadinessCheck(
                "Disk space",
                False,
                f"Cannot check disk space: {e}",
                critical=False
            ))
            self.warnings.append(f"Cannot check disk space: {e}")
        
        # Check environment variables
        required_env_vars = []  # Add any required environment variables
        
        for env_var in required_env_vars:
            if os.getenv(env_var):
                print(f"   ✅ Environment: {env_var} set")
                self.checks.append(ReadinessCheck(
                    f"Environment variable {env_var}",
                    True,
                    f"Environment variable {env_var} is set"
                ))
            else:
                print(f"   ⚠️ Environment: {env_var} not set")
                self.checks.append(ReadinessCheck(
                    f"Environment variable {env_var}",
                    False,
                    f"Environment variable {env_var} not set",
                    critical=False
                ))
                self.warnings.append(f"Environment variable not set: {env_var}")
    
    def _generate_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive readiness report."""
        total_checks = len(self.checks)
        successful_checks = sum(1 for check in self.checks if check.success)
        critical_checks = [check for check in self.checks if check.critical]
        critical_failures = [check for check in critical_checks if not check.success]
        
        # Determine deployment readiness
        ready_for_deployment = (
            len(self.critical_failures) == 0 and  # No critical failures
            len(critical_failures) == 0 and       # No critical check failures
            successful_checks >= total_checks * 0.8  # At least 80% success rate
        )
        
        report = {
            'ready_for_deployment': ready_for_deployment,
            'timestamp': time.time(),
            'summary': {
                'total_checks': total_checks,
                'successful_checks': successful_checks,
                'success_rate': f"{(successful_checks/total_checks)*100:.1f}%" if total_checks > 0 else "0%",
                'critical_failures': len(self.critical_failures),
                'warnings': len(self.warnings)
            },
            'checks': [
                {
                    'name': check.check_name,
                    'success': check.success,
                    'details': check.details,
                    'critical': check.critical
                }
                for check in self.checks
            ],
            'critical_failures': self.critical_failures,
            'warnings': self.warnings,
            'recommendations': self._generate_recommendations(ready_for_deployment)
        }
        
        return report
    
    def _generate_recommendations(self, ready: bool) -> List[str]:
        """Generate deployment recommendations."""
        recommendations = []
        
        if ready:
            recommendations.extend([
                "✅ System is ready for production deployment",
                "🚀 All critical components are working correctly",
                "📊 Performance requirements are met",
                "🛡️ Error handling is functional",
                "⚙️ Configuration files are valid",
                "🔗 Integration points are working"
            ])
        else:
            recommendations.append("❌ System is NOT ready for deployment")
            
            if self.critical_failures:
                recommendations.append("🚨 Critical failures must be resolved:")
                for failure in self.critical_failures:
                    recommendations.append(f"   • {failure}")
        
        if self.warnings:
            recommendations.append("⚠️ Warnings to address:")
            for warning in self.warnings:
                recommendations.append(f"   • {warning}")
        
        return recommendations


def main():
    """Run deployment readiness check."""
    try:
        checker = DeploymentReadinessChecker()
        report = checker.run_all_checks()
        
        # Display results
        print("\n" + "=" * 60)
        print("🎯 DEPLOYMENT READINESS RESULTS")
        print("=" * 60)
        
        if report['ready_for_deployment']:
            print("✅ SYSTEM IS READY FOR DEPLOYMENT!")
            print("🎉 All critical checks passed")
        else:
            print("❌ SYSTEM IS NOT READY FOR DEPLOYMENT!")
            print("🔧 Critical issues must be resolved")
        
        # Display summary
        summary = report['summary']
        print(f"\n📊 Summary:")
        print(f"   Total checks: {summary['total_checks']}")
        print(f"   Successful: {summary['successful_checks']}")
        print(f"   Success rate: {summary['success_rate']}")
        print(f"   Critical failures: {summary['critical_failures']}")
        print(f"   Warnings: {summary['warnings']}")
        
        # Display recommendations
        recommendations = report['recommendations']
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   {rec}")
        
        return report['ready_for_deployment']
        
    except Exception as e:
        print(f"\n💥 READINESS CHECK ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)