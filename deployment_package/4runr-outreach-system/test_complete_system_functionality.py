#!/usr/bin/env python3
"""
Complete System Functionality Test

This test verifies that all the outreach system fixes are working correctly:
1. Dependencies are properly installed
2. Knowledge base is correctly structured
3. System can initialize without errors
4. Success messages appear in logs
"""

import sys
import subprocess
import re
import os
from pathlib import Path
from typing import Tuple, List

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

class SystemFunctionalityTester:
    """Test complete system functionality after fixes."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = []
    
    def run_all_tests(self) -> bool:
        """Run all system functionality tests."""
        print("🧪 Complete System Functionality Test")
        print("=" * 45)
        
        tests = [
            ("Dependencies Import Test", self.test_dependencies_import),
            ("Knowledge Base Validation", self.test_knowledge_base),
            ("Engager Agent Initialization", self.test_engager_initialization),
            ("Success Message Verification", self.test_success_messages),
            ("System Integration Test", self.test_system_integration)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                success, message = test_func()
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"   {status}: {message}")
                self.test_results.append((test_name, success, message))
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.test_results.append((test_name, False, f"Exception: {e}"))
                all_passed = False
        
        self.print_summary()
        return all_passed
    
    def test_dependencies_import(self) -> Tuple[bool, str]:
        """Test that all required dependencies can be imported."""
        try:
            # Test key dependencies
            import requests
            import openai
            from bs4 import BeautifulSoup
            from pyairtable import Api
            import validators
            from dotenv import load_dotenv
            from jinja2 import Template
            from playwright.async_api import async_playwright
            
            return True, "All required dependencies imported successfully"
            
        except ImportError as e:
            return False, f"Dependency import failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def test_knowledge_base(self) -> Tuple[bool, str]:
        """Test knowledge base validation."""
        try:
            from engager.knowledge_base_loader import KnowledgeBaseLoader
            
            loader = KnowledgeBaseLoader()
            is_valid = loader.validate_knowledge_base()
            
            if is_valid:
                content = loader.load_knowledge_base()
                return True, f"Knowledge base valid ({len(content)} characters)"
            else:
                return False, "Knowledge base validation failed"
                
        except Exception as e:
            return False, f"Knowledge base test failed: {e}"
    
    def test_engager_initialization(self) -> Tuple[bool, str]:
        """Test that the engager agent can initialize without errors."""
        try:
            # Run the engager agent in dry-run mode
            result = subprocess.run([
                sys.executable, "-m", "engager.enhanced_engager_agent", 
                "--dry-run", "--limit", "1"
            ], capture_output=True, text=True, timeout=30)
            
            output = result.stdout + result.stderr
            
            # Check for successful initialization messages (more important than exit code)
            success_indicators = [
                "Enhanced Engager Agent initialized successfully",
                "4Runr knowledge base loaded successfully"
            ]
            
            found_indicators = sum(1 for indicator in success_indicators 
                                 if indicator in output)
            
            # Also check that there are no critical initialization errors
            critical_errors = [
                "Failed to initialize",
                "Knowledge base missing sections",
                "ModuleNotFoundError",
                "ImportError"
            ]
            
            found_critical_errors = [error for error in critical_errors 
                                   if error in output]
            
            if found_indicators >= 2 and not found_critical_errors:
                return True, f"Engager agent initialized successfully ({found_indicators} success indicators)"
            else:
                return False, f"Initialization issues: {found_indicators} indicators, {len(found_critical_errors)} critical errors"
                
        except subprocess.TimeoutExpired:
            return False, "Engager agent initialization timed out"
        except Exception as e:
            return False, f"Engager initialization test failed: {e}"
    
    def test_success_messages(self) -> Tuple[bool, str]:
        """Test that the expected success messages appear in logs."""
        try:
            # Run the engager agent and capture output
            result = subprocess.run([
                sys.executable, "-m", "engager.enhanced_engager_agent", 
                "--dry-run", "--limit", "1"
            ], capture_output=True, text=True, timeout=30)
            
            output = result.stdout + result.stderr
            
            # Check for the key success message
            success_patterns = [
                r"4Runr knowledge base loaded successfully",
                r"Knowledge base loaded successfully from data/4runr_knowledge\.md",
                r"Enhanced Engager Agent initialized successfully"
            ]
            
            found_messages = []
            for pattern in success_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    found_messages.append(pattern.replace(r'\\', ''))
            
            if len(found_messages) >= 2:  # At least 2 key messages
                return True, f"Found {len(found_messages)} success messages"
            else:
                return False, f"Only found {len(found_messages)} success messages, expected at least 2"
                
        except Exception as e:
            return False, f"Success message test failed: {e}"
    
    def test_system_integration(self) -> Tuple[bool, str]:
        """Test overall system integration."""
        try:
            # Test with PYTHONPATH approach as mentioned in requirements
            env = {**dict(os.environ), "PYTHONPATH": "."}
            result = subprocess.run([
                sys.executable, "-m", "engager.enhanced_engager_agent", 
                "--dry-run", "--limit", "1"
            ], capture_output=True, text=True, timeout=30, env=env)
            
            output = result.stdout + result.stderr
            
            # Check for absence of critical errors related to our fixes
            critical_errors = [
                "Knowledge base missing sections",
                "Knowledge base content validation failed",
                "ModuleNotFoundError",
                "ImportError"
            ]
            
            found_errors = []
            for error in critical_errors:
                if error.lower() in output.lower():
                    found_errors.append(error)
            
            # Check for success indicators
            success_indicators = [
                "4Runr knowledge base loaded successfully",
                "Enhanced Engager Agent initialized successfully"
            ]
            
            found_success = sum(1 for indicator in success_indicators 
                              if indicator in output)
            
            if not found_errors and found_success >= 2:
                return True, f"System integration passed ({found_success} success indicators, no critical errors)"
            else:
                return False, f"Integration issues: {len(found_errors)} critical errors, {found_success} success indicators"
                
        except Exception as e:
            return False, f"Integration test failed: {e}"
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 45)
        print("📊 System Functionality Test Results")
        print("=" * 45)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL SYSTEM TESTS PASSED!")
            print("   The outreach system fixes are working correctly.")
            print("   Expected success message should appear:")
            print("   '✅ 4Runr knowledge base loaded successfully'")
        else:
            print(f"\n⚠️  {total - passed} TEST(S) FAILED!")
            print("   System needs attention before use.")
            
            print("\nFailed Tests:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"   ❌ {test_name}: {message}")

def main():
    """Main test function."""
    import os
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    tester = SystemFunctionalityTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)