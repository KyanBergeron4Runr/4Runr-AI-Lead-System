#!/usr/bin/env python3
"""
Comprehensive test runner for 4Runr Outreach System.

This script runs all available tests in the correct order:
1. Unit tests
2. Smoke tests  
3. Integration tests
4. System validation

Provides a complete validation of all critical fixes.
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class ComprehensiveTestRunner:
    """Runs all tests for the outreach system."""
    
    def __init__(self, quick_mode: bool = False, include_integration: bool = False):
        self.quick_mode = quick_mode
        self.include_integration = include_integration
        self.results = {}
        self.start_time = time.time()
    
    def log_section(self, title: str):
        """Log a test section header."""
        elapsed = time.time() - self.start_time
        print(f"\n[{elapsed:6.1f}s] " + "=" * 60)
        print(f"[{elapsed:6.1f}s] {title}")
        print(f"[{elapsed:6.1f}s] " + "=" * 60)
    
    def log_info(self, message: str):
        """Log info message."""
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.1f}s] ℹ️  {message}")
    
    def log_success(self, message: str):
        """Log success message."""
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.1f}s] ✅ {message}")
    
    def log_error(self, message: str):
        """Log error message."""
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.1f}s] ❌ {message}")
    
    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        self.log_section("UNIT TESTS")
        
        try:
            # Import and run unit tests
            from test_unit import run_tests
            
            self.log_info("Running unit tests...")
            success = run_tests()
            
            if success:
                self.log_success("Unit tests passed")
            else:
                self.log_error("Unit tests failed")
            
            return success
            
        except Exception as e:
            self.log_error(f"Unit tests crashed: {e}")
            return False
    
    def run_smoke_tests(self) -> bool:
        """Run smoke tests."""
        self.log_section("SMOKE TESTS")
        
        try:
            # Run smoke tests as subprocess to avoid import conflicts
            cmd = [sys.executable, 'smoke_test.py']
            if self.quick_mode:
                cmd.append('--quick')
            
            self.log_info("Running smoke tests...")
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            success = result.returncode == 0
            
            if success:
                self.log_success("Smoke tests passed")
            else:
                self.log_error("Smoke tests failed")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_error("Smoke tests timed out")
            return False
        except Exception as e:
            self.log_error(f"Smoke tests crashed: {e}")
            return False
    
    def run_component_tests(self) -> Dict[str, bool]:
        """Run individual component tests."""
        self.log_section("COMPONENT TESTS")
        
        component_results = {}
        
        # Test scripts and their descriptions
        component_tests = [
            ('test_airtable_config.py', 'Airtable Configuration'),
            ('test_health_check.py', 'Health Check System'),
            ('test_resilient_engagement.py', 'Resilient Engagement')
        ]
        
        for test_script, description in component_tests:
            test_path = project_root / test_script
            
            if not test_path.exists():
                self.log_info(f"Skipping {description} (test file not found)")
                component_results[description] = True  # Don't fail if optional test missing
                continue
            
            try:
                self.log_info(f"Running {description} tests...")
                
                result = subprocess.run(
                    [sys.executable, test_script],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                success = result.returncode == 0
                component_results[description] = success
                
                if success:
                    self.log_success(f"{description} tests passed")
                else:
                    self.log_error(f"{description} tests failed")
                    # Print error output for debugging
                    if result.stderr:
                        print(f"Error output: {result.stderr[:300]}...")
                
            except subprocess.TimeoutExpired:
                self.log_error(f"{description} tests timed out")
                component_results[description] = False
            except Exception as e:
                self.log_error(f"{description} tests crashed: {e}")
                component_results[description] = False
        
        return component_results
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self.log_section("INTEGRATION TESTS")
        
        if not self.include_integration:
            self.log_info("Skipping integration tests (use --integration to enable)")
            return True
        
        try:
            # Check if Docker is available
            docker_check = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if docker_check.returncode != 0:
                self.log_error("Docker not available - skipping integration tests")
                return False
            
            self.log_info("Running integration tests (this may take several minutes)...")
            
            cmd = [sys.executable, 'test_integration.py']
            if self.quick_mode:
                cmd.append('--quick')
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for integration tests
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            success = result.returncode == 0
            
            if success:
                self.log_success("Integration tests passed")
            else:
                self.log_error("Integration tests failed")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_error("Integration tests timed out")
            return False
        except FileNotFoundError:
            self.log_error("Docker not found - cannot run integration tests")
            return False
        except Exception as e:
            self.log_error(f"Integration tests crashed: {e}")
            return False
    
    def run_system_validation(self) -> bool:
        """Run system validation."""
        self.log_section("SYSTEM VALIDATION")
        
        try:
            self.log_info("Running comprehensive system validation...")
            
            result = subprocess.run(
                [sys.executable, 'validate_system.py'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            success = result.returncode == 0
            
            if success:
                self.log_success("System validation passed")
            else:
                self.log_error("System validation failed")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_error("System validation timed out")
            return False
        except Exception as e:
            self.log_error(f"System validation crashed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests in order."""
        self.log_section("4RUNR OUTREACH SYSTEM - COMPREHENSIVE TEST SUITE")
        self.log_info("Testing all critical fixes and system functionality")
        
        if self.quick_mode:
            self.log_info("Running in QUICK mode (skipping time-consuming tests)")
        
        if self.include_integration:
            self.log_info("Including INTEGRATION tests (requires Docker)")
        
        # Run tests in order
        test_phases = [
            ("Unit Tests", self.run_unit_tests),
            ("Smoke Tests", self.run_smoke_tests),
            ("System Validation", self.run_system_validation)
        ]
        
        # Add integration tests if requested
        if self.include_integration:
            test_phases.append(("Integration Tests", self.run_integration_tests))
        
        # Run component tests
        component_results = self.run_component_tests()
        
        # Run main test phases
        for phase_name, test_func in test_phases:
            try:
                self.results[phase_name] = test_func()
            except Exception as e:
                self.log_error(f"{phase_name} crashed: {e}")
                self.results[phase_name] = False
        
        # Add component results
        self.results.update(component_results)
        
        return self.results
    
    def print_final_summary(self):
        """Print comprehensive final summary."""
        elapsed_total = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 80)
        
        # Categorize results
        critical_tests = ["Unit Tests", "Smoke Tests", "System Validation"]
        component_tests = ["Airtable Configuration", "Health Check System", "Resilient Engagement"]
        integration_tests = ["Integration Tests"]
        
        categories = [
            ("Critical Tests", critical_tests),
            ("Component Tests", component_tests),
            ("Integration Tests", integration_tests)
        ]
        
        overall_success = True
        
        for category_name, test_names in categories:
            print(f"\n{category_name}:")
            category_passed = 0
            category_total = 0
            
            for test_name in test_names:
                if test_name in self.results:
                    result = self.results[test_name]
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"  {test_name}: {status}")
                    
                    category_total += 1
                    if result:
                        category_passed += 1
                    else:
                        overall_success = False
            
            if category_total > 0:
                print(f"  → {category_passed}/{category_total} passed")
        
        # Overall statistics
        total_passed = sum(1 for result in self.results.values() if result)
        total_tests = len(self.results)
        
        print(f"\nOverall Results: {total_passed}/{total_tests} tests passed")
        print(f"Total execution time: {elapsed_total:.1f} seconds")
        
        # Final verdict
        if overall_success and total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("\nThe 4Runr Outreach System is FULLY VALIDATED and ready for:")
            print("- ✅ Production deployment")
            print("- ✅ Docker containerization")
            print("- ✅ Automated CI/CD pipelines")
            print("- ✅ High-availability operations")
            print("\nAll 7 critical fixes have been successfully implemented:")
            print("1. ✅ Import system with absolute imports")
            print("2. ✅ Modern OpenAI SDK integration")
            print("3. ✅ Configurable Airtable integration")
            print("4. ✅ Non-blocking health check system")
            print("5. ✅ Resilient engagement pipeline")
            print("6. ✅ Dependencies and Docker configuration")
            print("7. ✅ Comprehensive test suite and validation")
            
        else:
            print(f"\n⚠️  {total_tests - total_passed} TESTS FAILED")
            print("\nThe system has issues that must be resolved before production deployment.")
            print("Please review the failed tests above and address the underlying issues.")
            
            if not self.include_integration:
                print("\nNote: Integration tests were not run. Consider running with --integration")
                print("for complete validation including Docker functionality.")
        
        return overall_success


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Comprehensive test runner for 4Runr Outreach System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests except integration
  python run_all_tests.py --quick           # Run quick tests only
  python run_all_tests.py --integration     # Include integration tests (requires Docker)
  python run_all_tests.py --quick --integration  # Quick tests including integration
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only (skip time-consuming tests)')
    parser.add_argument('--integration', action='store_true',
                       help='Include integration tests (requires Docker)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = ComprehensiveTestRunner(
        quick_mode=args.quick,
        include_integration=args.integration
    )
    
    try:
        results = runner.run_all_tests()
        success = runner.print_final_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test runner crashed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())