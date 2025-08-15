#!/usr/bin/env python3
"""
Comprehensive Knowledge Base Validation Test

This test validates that the 4Runr knowledge base is properly structured
and contains all required sections for the engager agent to function correctly.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from engager.knowledge_base_loader import KnowledgeBaseLoader, KnowledgeBaseError

class KnowledgeBaseValidator:
    """Comprehensive validator for the 4Runr knowledge base."""
    
    def __init__(self):
        """Initialize the validator."""
        self.loader = KnowledgeBaseLoader()
        self.required_sections = [
            "4Runr Knowledge Base",
            "Core Philosophy", 
            "Systems Thinking",
            "Infrastructure-First",
            "AI-as-a-Layer",
            "Business Value"
        ]
        self.test_results = []
    
    def run_all_tests(self) -> bool:
        """Run all validation tests."""
        print("🧪 Comprehensive Knowledge Base Validation")
        print("=" * 50)
        
        tests = [
            ("File Existence", self.test_file_exists),
            ("Content Loading", self.test_content_loading),
            ("Section Validation", self.test_section_validation),
            ("Content Quality", self.test_content_quality),
            ("UTF-8 Encoding", self.test_encoding),
            ("Caching Mechanism", self.test_caching),
            ("Error Handling", self.test_error_handling),
            ("Integration Test", self.test_integration)
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
    
    def test_file_exists(self) -> Tuple[bool, str]:
        """Test that the knowledge base file exists."""
        file_path = self.loader.absolute_path
        if file_path.exists():
            return True, f"Knowledge base file found at {file_path}"
        else:
            return False, f"Knowledge base file not found at {file_path}"
    
    def test_content_loading(self) -> Tuple[bool, str]:
        """Test that content can be loaded successfully."""
        try:
            content = self.loader.load_knowledge_base()
            if content and len(content) > 100:
                return True, f"Content loaded successfully ({len(content)} characters)"
            else:
                return False, "Content is empty or too short"
        except Exception as e:
            return False, f"Failed to load content: {e}"
    
    def test_section_validation(self) -> Tuple[bool, str]:
        """Test that all required sections are present."""
        try:
            content = self.loader.load_knowledge_base()
            content_lower = content.lower()
            
            missing_sections = []
            found_sections = []
            
            for section in self.required_sections:
                if section.lower() in content_lower:
                    found_sections.append(section)
                else:
                    missing_sections.append(section)
            
            if not missing_sections:
                return True, f"All {len(self.required_sections)} required sections found"
            else:
                return False, f"Missing sections: {missing_sections}"
                
        except Exception as e:
            return False, f"Section validation failed: {e}"
    
    def test_content_quality(self) -> Tuple[bool, str]:
        """Test content quality and completeness."""
        try:
            content = self.loader.load_knowledge_base()
            
            # Check minimum content length
            if len(content) < 5000:
                return False, f"Content too short ({len(content)} chars, expected >5000)"
            
            # Check for key 4Runr concepts
            key_concepts = [
                "infrastructure", "systems", "ai", "business", 
                "permanent", "sovereign", "automation"
            ]
            
            content_lower = content.lower()
            missing_concepts = [concept for concept in key_concepts 
                              if concept not in content_lower]
            
            if missing_concepts:
                return False, f"Missing key concepts: {missing_concepts}"
            
            # Check for 4Runr branding
            if "4runr" not in content_lower:
                return False, "Missing 4Runr branding"
            
            return True, f"Content quality good ({len(content)} chars, all key concepts present)"
            
        except Exception as e:
            return False, f"Content quality check failed: {e}"
    
    def test_encoding(self) -> Tuple[bool, str]:
        """Test UTF-8 encoding."""
        try:
            with open(self.loader.absolute_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to encode/decode to verify UTF-8 compatibility
            content.encode('utf-8').decode('utf-8')
            
            return True, "UTF-8 encoding verified"
            
        except UnicodeDecodeError as e:
            return False, f"UTF-8 encoding error: {e}"
        except Exception as e:
            return False, f"Encoding test failed: {e}"
    
    def test_caching(self) -> Tuple[bool, str]:
        """Test the caching mechanism."""
        try:
            # Clear cache and load
            self.loader._cached_knowledge = None
            self.loader._last_loaded = None
            
            start_time = time.time()
            content1 = self.loader.load_knowledge_base()
            first_load_time = time.time() - start_time
            
            # Load again (should use cache)
            start_time = time.time()
            content2 = self.loader.load_knowledge_base()
            second_load_time = time.time() - start_time
            
            if content1 == content2:
                return True, f"Caching works (1st: {first_load_time:.3f}s, 2nd: {second_load_time:.3f}s)"
            else:
                return False, "Cache returned different content"
                
        except Exception as e:
            return False, f"Caching test failed: {e}"
    
    def test_error_handling(self) -> Tuple[bool, str]:
        """Test error handling with invalid paths."""
        try:
            # Test with non-existent file
            invalid_loader = KnowledgeBaseLoader("nonexistent/path.md")
            fallback_content = invalid_loader.load_knowledge_base()
            
            if fallback_content and "fallback" in fallback_content.lower():
                return True, "Error handling works, fallback content provided"
            else:
                return False, "Error handling failed, no fallback content"
                
        except Exception as e:
            return False, f"Error handling test failed: {e}"
    
    def test_integration(self) -> Tuple[bool, str]:
        """Test integration with the actual validation method."""
        try:
            # Use the actual validation method from the loader
            is_valid = self.loader.validate_knowledge_base()
            
            if is_valid:
                # Test knowledge summary extraction
                summary = self.loader.get_knowledge_summary()
                
                expected_keys = ['systems_thinking', 'infrastructure_first', 
                               'ai_as_layer', 'business_value', 'tone', 'value_props']
                
                missing_keys = [key for key in expected_keys if key not in summary]
                
                if not missing_keys:
                    return True, f"Integration test passed, summary contains {len(summary)} components"
                else:
                    return False, f"Summary missing keys: {missing_keys}"
            else:
                return False, "Knowledge base validation failed"
                
        except Exception as e:
            return False, f"Integration test failed: {e}"
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Knowledge base is properly configured and ready for use.")
        else:
            print(f"\n⚠️  {total - passed} TEST(S) FAILED!")
            print("   Knowledge base needs attention before use.")
            
            print("\nFailed Tests:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"   ❌ {test_name}: {message}")

def main():
    """Main test function."""
    validator = KnowledgeBaseValidator()
    success = validator.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)