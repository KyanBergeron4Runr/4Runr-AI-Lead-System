#!/usr/bin/env python3
"""
Test runner for 4runr-lead-scraper

Runs unit tests for the engagement defaults functionality.
"""

import sys
import subprocess
from pathlib import Path

def run_engagement_defaults_tests():
    """Run engagement defaults unit tests."""
    print("🧪 Running EngagementDefaultsManager unit tests...")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_engagement_defaults.py', 
            '-v', '--tb=short'
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ All unit tests passed!")
            return True
        else:
            print("❌ Some unit tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests for sync with defaults."""
    print("🧪 Running sync with defaults integration tests...")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_integration_sync_defaults.py', 
            '-v', '--tb=short'
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ All integration tests passed!")
            return True
        else:
            print("❌ Some integration tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_cli_tests():
    """Run CLI command tests."""
    print("🧪 Running CLI command tests...")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_cli_apply_defaults.py', 
            '-v', '--tb=short'
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ All CLI tests passed!")
            return True
        else:
            print("❌ Some CLI tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running CLI tests: {e}")
        return False

def run_all_tests():
    """Run all available tests."""
    print("🧪 Running all tests...")
    
    success = True
    
    # Run engagement defaults unit tests
    if not run_engagement_defaults_tests():
        success = False
    
    # Run integration tests
    if not run_integration_tests():
        success = False
    
    # Run CLI tests
    if not run_cli_tests():
        success = False
    
    # Add other test suites here as they are created
    
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run unit tests for 4runr-lead-scraper')
    parser.add_argument('--engagement-defaults', action='store_true', 
                       help='Run only engagement defaults unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--cli', action='store_true',
                       help='Run only CLI command tests')
    parser.add_argument('--all', action='store_true', default=True,
                       help='Run all tests (default)')
    
    args = parser.parse_args()
    
    if args.engagement_defaults:
        success = run_engagement_defaults_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.cli:
        success = run_cli_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)