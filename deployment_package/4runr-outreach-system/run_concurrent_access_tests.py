#!/usr/bin/env python3
"""
Comprehensive Test Runner for Concurrent Access Safety

This script runs all concurrent access safety tests including:
- Stress tests
- Thread safety tests  
- Integration tests
- Performance benchmarks

Usage:
    python run_concurrent_access_tests.py [--test-type TYPE] [--verbose] [--quick]
    
Test Types:
    - all: Run all tests (default)
    - stress: Run only stress tests
    - thread-safety: Run only thread safety tests
    - integration: Run only integration tests
    - benchmarks: Run only benchmark tests
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules
try:
    from test_concurrent_access_stress import run_stress_tests
    from test_thread_safety import run_thread_safety_tests
    from test_concurrent_integration import run_integration_tests
except ImportError as e:
    print(f"Error importing test modules: {e}")
    print("Make sure all test files are in the same directory as this script.")
    sys.exit(1)

class ConcurrentAccessTestRunner:
    """Comprehensive test runner for concurrent access safety"""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        """
        Initialize the test runner
        
        Args:
            verbose: Enable verbose output
            quick: Run quick tests only (reduced load)
        """
        self.verbose = verbose
        self.quick = quick
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> bool:
        """Run all concurrent access safety tests"""
        print("🚀 Starting Comprehensive Concurrent Access Safety Tests")
        print("=" * 80)
        
        self.start_time = time.time()
        overall_success = True
        
        # Test execution order (from basic to complex)
        test_suites = [
            ("Thread Safety Tests", self.run_thread_safety_tests),
            ("Stress Tests", self.run_stress_tests),
            ("Integration Tests", self.run_integration_tests),
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n{'='*20} {suite_name} {'='*20}")
            
            suite_start = time.time()
            try:
                success = test_function()
                suite_end = time.time()
                
                self.results[suite_name] = {
                    'success': success,
                    'duration': suite_end - suite_start,
                    'error': None
                }
                
                if success:
                    print(f"✅ {suite_name} completed successfully in {suite_end - suite_start:.2f}s")
                else:
                    print(f"❌ {suite_name} failed after {suite_end - suite_start:.2f}s")
                    overall_success = False
                    
            except Exception as e:
                suite_end = time.time()
                error_msg = str(e)
                
                self.results[suite_name] = {
                    'success': False,
                    'duration': suite_end - suite_start,
                    'error': error_msg
                }
                
                print(f"💥 {suite_name} crashed after {suite_end - suite_start:.2f}s: {error_msg}")
                overall_success = False
                
                if self.verbose:
                    import traceback
                    print(f"Full traceback:\n{traceback.format_exc()}")
        
        self.end_time = time.time()
        self._print_final_summary()
        
        return overall_success
    
    def run_stress_tests(self) -> bool:
        """Run stress tests"""
        print("🔥 Running Concurrent Access Stress Tests...")
        
        if self.quick:
            print("⚡ Quick mode: Running reduced stress tests")
            # In quick mode, we could modify test parameters
            # For now, just run normally but note the mode
        
        try:
            return run_stress_tests()
        except Exception as e:
            print(f"Stress tests failed with error: {e}")
            return False
    
    def run_thread_safety_tests(self) -> bool:
        """Run thread safety tests"""
        print("🧵 Running Thread Safety Tests...")
        
        try:
            return run_thread_safety_tests()
        except Exception as e:
            print(f"Thread safety tests failed with error: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        try:
            return run_integration_tests()
        except Exception as e:
            print(f"Integration tests failed with error: {e}")
            return False
    
    def run_specific_test_type(self, test_type: str) -> bool:
        """Run a specific type of test"""
        test_functions = {
            'stress': self.run_stress_tests,
            'thread-safety': self.run_thread_safety_tests,
            'integration': self.run_integration_tests,
        }
        
        if test_type not in test_functions:
            print(f"❌ Unknown test type: {test_type}")
            print(f"Available types: {', '.join(test_functions.keys())}")
            return False
        
        print(f"🎯 Running {test_type} tests only...")
        self.start_time = time.time()
        
        try:
            success = test_functions[test_type]()
            self.end_time = time.time()
            
            self.results[test_type] = {
                'success': success,
                'duration': self.end_time - self.start_time,
                'error': None
            }
            
            self._print_final_summary()
            return success
            
        except Exception as e:
            self.end_time = time.time()
            error_msg = str(e)
            
            self.results[test_type] = {
                'success': False,
                'duration': self.end_time - self.start_time,
                'error': error_msg
            }
            
            print(f"💥 {test_type} tests crashed: {error_msg}")
            self._print_final_summary()
            return False
    
    def _print_final_summary(self):
        """Print final test summary"""
        if not self.start_time or not self.end_time:
            return
        
        total_duration = self.end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 80)
        
        print(f"🕐 Total execution time: {total_duration:.2f} seconds")
        print(f"📅 Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.results:
            successful_suites = sum(1 for result in self.results.values() if result['success'])
            total_suites = len(self.results)
            
            print(f"📈 Test suites passed: {successful_suites}/{total_suites}")
            
            print("\n📋 Detailed Results:")
            for suite_name, result in self.results.items():
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                duration = result['duration']
                
                print(f"  {status} {suite_name}: {duration:.2f}s")
                
                if result['error']:
                    print(f"    💥 Error: {result['error']}")
            
            # Overall status
            overall_success = all(result['success'] for result in self.results.values())
            
            if overall_success:
                print("\n🎉 ALL TESTS PASSED! Concurrent access safety is verified.")
            else:
                print("\n⚠️  SOME TESTS FAILED! Please review the failures above.")
                
                # Provide guidance
                print("\n🔧 Troubleshooting Tips:")
                print("  - Check system resources (CPU, memory, disk space)")
                print("  - Ensure no other processes are heavily using the database")
                print("  - Review error messages for specific issues")
                print("  - Try running individual test suites to isolate problems")
                print("  - Use --verbose flag for more detailed error information")
        
        # Save results to file
        self._save_results_to_file()
    
    def _save_results_to_file(self):
        """Save test results to a JSON file"""
        try:
            results_file = f"concurrent_access_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            results_data = {
                'timestamp': datetime.now().isoformat(),
                'total_duration': self.end_time - self.start_time if self.start_time and self.end_time else 0,
                'test_configuration': {
                    'verbose': self.verbose,
                    'quick': self.quick
                },
                'results': self.results,
                'system_info': self._get_system_info()
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"📄 Test results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {e}")
    
    def _get_system_info(self) -> dict:
        """Get basic system information"""
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': os.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 2)
            }
        except ImportError:
            return {
                'platform': 'unknown',
                'python_version': 'unknown',
                'note': 'psutil not available for detailed system info'
            }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run concurrent access safety tests for the lead database system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_concurrent_access_tests.py                    # Run all tests
  python run_concurrent_access_tests.py --test-type stress # Run only stress tests
  python run_concurrent_access_tests.py --verbose --quick  # Quick run with verbose output
        """
    )
    
    parser.add_argument(
        '--test-type',
        choices=['all', 'stress', 'thread-safety', 'integration'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Run quick tests with reduced load'
    )
    
    parser.add_argument(
        '--list-tests',
        action='store_true',
        help='List available test types and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_tests:
        print("Available test types:")
        print("  all           - Run all test suites (default)")
        print("  stress        - High concurrency and load tests")
        print("  thread-safety - Thread safety and race condition tests")
        print("  integration   - End-to-end integration tests")
        return 0
    
    # Create test runner
    runner = ConcurrentAccessTestRunner(verbose=args.verbose, quick=args.quick)
    
    # Run tests
    if args.test_type == 'all':
        success = runner.run_all_tests()
    else:
        success = runner.run_specific_test_type(args.test_type)
    
    # Exit with appropriate code
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user (Ctrl+C)")
        print("🛑 Cleaning up and exiting...")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n💥 Unexpected error in test runner: {e}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)