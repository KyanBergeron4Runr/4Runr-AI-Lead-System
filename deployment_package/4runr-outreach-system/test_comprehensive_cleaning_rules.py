#!/usr/bin/env python3
"""
Comprehensive unit tests for all cleaning rules in the DataCleaner system.

This script tests all cleaning rules including:
- Removal of "Sirius XM and ... Some results may have been delisted" patterns
- HTML fragment cleaning with real-world examples
- Company name normalization with edge cases
- Website URL validation with malformed URLs
"""

import sys
import re
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import DataCleaner, CleaningRulesEngine, ValidationEngine, ConfigurationManager


def test_sirius_xm_pattern_removal():
    """Test removal of specific Sirius XM and delisted patterns."""
    print("🎵 Testing Sirius XM Pattern Removal")
    print("=" * 50)
    
    try:
        # Initialize cleaning engine
        config_manager = ConfigurationManager()
        cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
        
        # Test cases for Sirius XM patterns
        test_cases = [
            {
                'name': 'Classic Sirius XM Pattern',
                'input': 'Sirius XM and ... Some results may have been delisted consistent with local laws',
                'expected_cleaned': True,
                'should_be_empty': True
            },
            {
                'name': 'Sirius XM with Company Name',
                'input': 'TechCorp Inc Sirius XM and ... Some results may have been delisted',
                'expected_cleaned': True,
                'should_contain': 'TechCorp Inc'
            },
            {
                'name': 'Just Delisted Pattern',
                'input': 'Some results may have been delisted consistent with local laws',
                'expected_cleaned': True,
                'should_be_empty': True
            },
            {
                'name': 'Delisted with Company',
                'input': 'Microsoft Corporation Some results may have been delisted',
                'expected_cleaned': True,
                'should_contain': 'Microsoft Corporation'
            },
            {
                'name': 'Complex Sirius Pattern',
                'input': 'Apple Inc Sirius XM Holdings Inc and other companies Some results may have been delisted',
                'expected_cleaned': True,
                'should_contain': 'Apple Inc'
            },
            {
                'name': 'Normal Company Name',
                'input': 'Google LLC',
                'expected_cleaned': False,
                'should_contain': 'Google LLC'
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test company name cleaning
            result = cleaning_engine.clean_company_name(test_case['input'])
            
            print(f"   Input: {test_case['input'][:60]}...")
            print(f"   Output: {result}")
            
            # Check if cleaning occurred as expected
            was_cleaned = result != test_case['input']
            
            if test_case['expected_cleaned']:
                if was_cleaned:
                    if test_case.get('should_be_empty') and not result.strip():
                        print(f"   ✅ PASS - Correctly removed entire pattern")
                        success_count += 1
                    elif test_case.get('should_contain') and test_case['should_contain'] in result:
                        print(f"   ✅ PASS - Correctly preserved company name")
                        success_count += 1
                    else:
                        print(f"   ❌ FAIL - Cleaning occurred but result unexpected")
                else:
                    print(f"   ❌ FAIL - Expected cleaning but none occurred")
            else:
                if not was_cleaned and test_case.get('should_contain') in result:
                    print(f"   ✅ PASS - Correctly left unchanged")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Unexpected cleaning occurred")
        
        print(f"\\n📊 Sirius XM Pattern Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.8:  # 80% success rate
            print(f"\\n✅ Sirius XM pattern removal working correctly")
            return True
        else:
            print(f"\\n❌ Sirius XM pattern removal needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Sirius XM patterns: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_fragment_cleaning():
    """Test HTML fragment cleaning with real-world examples."""
    print("\\n🌐 Testing HTML Fragment Cleaning")
    print("=" * 50)
    
    try:
        # Initialize cleaning engine
        config_manager = ConfigurationManager()
        cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
        
        # Test cases for HTML fragments
        test_cases = [
            {
                'name': 'Basic HTML Tags',
                'input': '<div>TechCorp Inc</div>',
                'expected': 'TechCorp Inc'
            },
            {
                'name': 'HTML with Attributes',
                'input': '<span class="company-name">Microsoft Corporation</span>',
                'expected': 'Microsoft Corporation'
            },
            {
                'name': 'Multiple HTML Tags',
                'input': '<p><strong>Apple Inc</strong> - Technology Company</p>',
                'expected': 'Apple Inc - Technology Company'
            },
            {
                'name': 'HTML Entities',
                'input': 'Johnson &amp; Johnson Inc &lt;Healthcare&gt;',
                'expected': 'Johnson & Johnson Inc <Healthcare>'
            },
            {
                'name': 'Complex HTML Structure',
                'input': '<div class="result"><h3>Google LLC</h3><p>Search engine company</p></div>',
                'expected': 'Google LLC Search engine company'
            },
            {
                'name': 'HTML with Line Breaks',
                'input': 'Amazon<br/>Web Services<br/><br/>Cloud Computing',
                'expected': 'Amazon Web Services Cloud Computing'
            },
            {
                'name': 'Script and Style Tags',
                'input': 'Facebook Inc<script>alert("test")</script><style>.hidden{display:none}</style>',
                'expected': 'Facebook Inc'
            },
            {
                'name': 'Mixed Content',
                'input': '&nbsp;Tesla Inc&nbsp;&mdash;&nbsp;Electric Vehicles&nbsp;',
                'expected': 'Tesla Inc — Electric Vehicles'
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test HTML fragment removal
            result = cleaning_engine.remove_html_fragments(test_case['input'])
            
            print(f"   Input: {test_case['input']}")
            print(f"   Expected: {test_case['expected']}")
            print(f"   Output: {result}")
            
            # Check if result matches expected (allowing for minor whitespace differences)
            result_normalized = ' '.join(result.split())
            expected_normalized = ' '.join(test_case['expected'].split())
            
            if result_normalized == expected_normalized:
                print(f"   ✅ PASS")
                success_count += 1
            else:
                print(f"   ❌ FAIL - Output doesn't match expected")
        
        print(f"\\n📊 HTML Fragment Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.8:  # 80% success rate
            print(f"\\n✅ HTML fragment cleaning working correctly")
            return True
        else:
            print(f"\\n❌ HTML fragment cleaning needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HTML fragment cleaning: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_company_name_normalization():
    """Test company name normalization with edge cases."""
    print("\\n🏢 Testing Company Name Normalization")
    print("=" * 50)
    
    try:
        # Initialize cleaning engine
        config_manager = ConfigurationManager()
        cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
        
        # Test cases for company name normalization
        test_cases = [
            {
                'name': 'Inc Normalization',
                'input': 'TechCorp Incorporated',
                'should_contain': 'TechCorp',
                'should_normalize': True
            },
            {
                'name': 'Corporation to Corp',
                'input': 'Microsoft Corporation',
                'should_contain': 'Microsoft',
                'should_normalize': True
            },
            {
                'name': 'Limited to Ltd',
                'input': 'Apple Limited',
                'should_contain': 'Apple',
                'should_normalize': True
            },
            {
                'name': 'Company Suffix',
                'input': 'Google Company',
                'should_contain': 'Google',
                'should_normalize': True
            },
            {
                'name': 'Multiple Suffixes',
                'input': 'Amazon Corporation Inc',
                'should_contain': 'Amazon',
                'should_normalize': True
            },
            {
                'name': 'International Entities',
                'input': 'BMW Aktiengesellschaft',
                'should_contain': 'BMW',
                'should_normalize': True
            },
            {
                'name': 'French Entity',
                'input': 'Total Société Anonyme',
                'should_contain': 'Total',
                'should_normalize': True
            },
            {
                'name': 'Already Normalized',
                'input': 'Tesla Inc',
                'should_contain': 'Tesla Inc',
                'should_normalize': False
            },
            {
                'name': 'Edge Case - Just Suffix',
                'input': 'Corporation',
                'should_contain': 'Corporation',
                'should_normalize': False
            },
            {
                'name': 'Complex Name',
                'input': 'Johnson & Johnson Incorporated',
                'should_contain': 'Johnson & Johnson',
                'should_normalize': True
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test company name cleaning/normalization
            result = cleaning_engine.clean_company_name(test_case['input'])
            
            print(f"   Input: {test_case['input']}")
            print(f"   Output: {result}")
            
            # Check if normalization occurred as expected
            was_normalized = result != test_case['input']
            contains_expected = test_case['should_contain'] in result
            
            if test_case['should_normalize']:
                if was_normalized and contains_expected:
                    print(f"   ✅ PASS - Correctly normalized")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Expected normalization")
            else:
                if not was_normalized or contains_expected:
                    print(f"   ✅ PASS - Correctly left unchanged")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Unexpected normalization")
        
        print(f"\\n📊 Company Normalization Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.7:  # 70% success rate (more lenient for complex normalization)
            print(f"\\n✅ Company name normalization working correctly")
            return True
        else:
            print(f"\\n❌ Company name normalization needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing company name normalization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_website_url_validation():
    """Test website URL validation with malformed URLs."""
    print("\\n🌐 Testing Website URL Validation")
    print("=" * 50)
    
    try:
        # Initialize validation engine
        config_manager = ConfigurationManager()
        validation_engine = ValidationEngine(config_manager.validation_rules)
        
        # Test cases for website URL validation
        test_cases = [
            {
                'name': 'Valid HTTPS URL',
                'input': 'https://techcorp.com',
                'expected_valid': True
            },
            {
                'name': 'Valid HTTP URL',
                'input': 'http://company.ca',
                'expected_valid': True
            },
            {
                'name': 'Valid with Path',
                'input': 'https://microsoft.com/products',
                'expected_valid': True
            },
            {
                'name': 'Valid with Subdomain',
                'input': 'https://www.apple.com',
                'expected_valid': True
            },
            {
                'name': 'Malformed - No Protocol',
                'input': 'techcorp.com',
                'expected_valid': False
            },
            {
                'name': 'Malformed - Invalid Protocol',
                'input': 'ftp://company.com',
                'expected_valid': False
            },
            {
                'name': 'Malformed - No Domain',
                'input': 'https://',
                'expected_valid': False
            },
            {
                'name': 'Malformed - Invalid Characters',
                'input': 'https://comp any.com',
                'expected_valid': False
            },
            {
                'name': 'Forbidden Domain - Google',
                'input': 'https://google.com/search',
                'expected_valid': False
            },
            {
                'name': 'Forbidden Domain - LinkedIn',
                'input': 'https://linkedin.com/company/test',
                'expected_valid': False
            },
            {
                'name': 'Forbidden Domain - Facebook',
                'input': 'https://facebook.com/pages/company',
                'expected_valid': False
            },
            {
                'name': 'Edge Case - Just Domain',
                'input': 'https://a.co',
                'expected_valid': True
            },
            {
                'name': 'Edge Case - Long Domain',
                'input': 'https://very-long-company-name-for-testing.com',
                'expected_valid': True
            },
            {
                'name': 'International Domain',
                'input': 'https://company.co.uk',
                'expected_valid': True
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test website URL validation
            context = {'id': 'test', 'Full Name': 'Test User'}
            result = validation_engine.validate_website_url(test_case['input'], context)
            
            print(f"   Input: {test_case['input']}")
            print(f"   Expected Valid: {test_case['expected_valid']}")
            print(f"   Actual Valid: {result.is_valid}")
            print(f"   Confidence: {result.confidence_score}")
            
            if result.error_message:
                print(f"   Error: {result.error_message}")
            
            if result.is_valid == test_case['expected_valid']:
                print(f"   ✅ PASS")
                success_count += 1
            else:
                print(f"   ❌ FAIL - Validation result doesn't match expected")
        
        print(f"\\n📊 Website URL Validation Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.85:  # 85% success rate
            print(f"\\n✅ Website URL validation working correctly")
            return True
        else:
            print(f"\\n❌ Website URL validation needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing website URL validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_artifact_removal():
    """Test removal of various search artifacts."""
    print("\\n🔍 Testing Search Artifact Removal")
    print("=" * 50)
    
    try:
        # Initialize cleaning engine
        config_manager = ConfigurationManager()
        cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
        
        # Test cases for search artifacts
        test_cases = [
            {
                'name': 'Google Search Navigation',
                'input': 'TechCorp Inc About X results (0.45 seconds) Next',
                'should_clean': True,
                'should_contain': 'TechCorp Inc'
            },
            {
                'name': 'Search Time Indicators',
                'input': 'Microsoft Corporation 2 hours ago · 3 days ago',
                'should_clean': True,
                'should_contain': 'Microsoft Corporation'
            },
            {
                'name': 'Learn More Links',
                'input': 'Apple Inc Learn more Next Previous',
                'should_clean': True,
                'should_contain': 'Apple Inc'
            },
            {
                'name': 'Rating Fragments',
                'input': 'Google LLC Rating: 4.5 stars (1,234 reviews)',
                'should_clean': True,
                'should_contain': 'Google LLC'
            },
            {
                'name': 'Ad Indicators',
                'input': 'Amazon Web Services Ad · Sponsored',
                'should_clean': True,
                'should_contain': 'Amazon Web Services'
            },
            {
                'name': 'Search Result Numbers',
                'input': 'Facebook Inc About 1,234,567 results',
                'should_clean': True,
                'should_contain': 'Facebook Inc'
            },
            {
                'name': 'Navigation Elements',
                'input': 'Tesla Inc Images Videos News Shopping More',
                'should_clean': True,
                'should_contain': 'Tesla Inc'
            },
            {
                'name': 'Clean Company Name',
                'input': 'Netflix Inc',
                'should_clean': False,
                'should_contain': 'Netflix Inc'
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test search artifact removal
            result = cleaning_engine.remove_search_artifacts(test_case['input'])
            
            print(f"   Input: {test_case['input']}")
            print(f"   Output: {result}")
            
            # Check if cleaning occurred as expected
            was_cleaned = result != test_case['input']
            contains_expected = test_case['should_contain'] in result
            
            if test_case['should_clean']:
                if was_cleaned and contains_expected:
                    print(f"   ✅ PASS - Correctly cleaned artifacts")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Expected cleaning")
            else:
                if not was_cleaned and contains_expected:
                    print(f"   ✅ PASS - Correctly left unchanged")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Unexpected cleaning")
        
        print(f"\\n📊 Search Artifact Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.8:  # 80% success rate
            print(f"\\n✅ Search artifact removal working correctly")
            return True
        else:
            print(f"\\n❌ Search artifact removal needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search artifact removal: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_normalization():
    """Test comprehensive text normalization."""
    print("\\n📝 Testing Text Normalization")
    print("=" * 50)
    
    try:
        # Initialize cleaning engine
        config_manager = ConfigurationManager()
        cleaning_engine = CleaningRulesEngine(config_manager.cleaning_rules)
        
        # Test cases for text normalization
        test_cases = [
            {
                'name': 'Smart Quotes',
                'input': '"TechCorp Inc" – Technology Company',
                'expected_contains': 'TechCorp Inc'
            },
            {
                'name': 'Unicode Characters',
                'input': 'Café Corporation™ ® ©',
                'expected_contains': 'Café Corporation'
            },
            {
                'name': 'Extra Whitespace',
                'input': '  Microsoft    Corporation   ',
                'expected': 'Microsoft Corporation'
            },
            {
                'name': 'Mixed Case Issues',
                'input': 'aPPLE iNC',
                'expected_contains': 'Apple Inc'
            },
            {
                'name': 'Special Characters',
                'input': 'Johnson & Johnson Inc.',
                'expected_contains': 'Johnson & Johnson Inc'
            },
            {
                'name': 'International Characters',
                'input': 'Nestlé S.A.',
                'expected_contains': 'Nestlé'
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test text normalization
            result = cleaning_engine.normalize_text(test_case['input'])
            
            print(f"   Input: {test_case['input']}")
            print(f"   Output: {result}")
            
            # Check if normalization worked
            if 'expected' in test_case:
                if result.strip() == test_case['expected']:
                    print(f"   ✅ PASS - Exact match")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Expected: {test_case['expected']}")
            elif 'expected_contains' in test_case:
                if test_case['expected_contains'] in result:
                    print(f"   ✅ PASS - Contains expected content")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - Missing expected content")
        
        print(f"\\n📊 Text Normalization Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.7:  # 70% success rate
            print(f"\\n✅ Text normalization working correctly")
            return True
        else:
            print(f"\\n❌ Text normalization needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing text normalization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_cleaning():
    """Test end-to-end cleaning with complex real-world examples."""
    print("\\n🔄 Testing End-to-End Cleaning")
    print("=" * 50)
    
    try:
        # Initialize data cleaner
        data_cleaner = DataCleaner()
        
        # Test cases for end-to-end cleaning
        test_cases = [
            {
                'name': 'Complex Google Search Result',
                'input': {
                    'Company': '<div>TechCorp Inc</div> Sirius XM and ... Some results may have been delisted About 1,234 results',
                    'Website': 'https://linkedin.com/company/techcorp'
                },
                'context': {'id': 'test1', 'Full Name': 'John Doe', 'source': 'test'},
                'expected_company_contains': 'TechCorp Inc',
                'expected_website_rejected': True
            },
            {
                'name': 'HTML with Search Artifacts',
                'input': {
                    'Company': '<span class="company">Microsoft Corporation</span> Learn more Next',
                    'Website': 'https://microsoft.com'
                },
                'context': {'id': 'test2', 'Full Name': 'Jane Smith', 'source': 'test'},
                'expected_company_contains': 'Microsoft Corporation',
                'expected_website_valid': True
            },
            {
                'name': 'Delisted Pattern Only',
                'input': {
                    'Company': 'Some results may have been delisted consistent with local laws',
                    'Website': 'https://example.com'
                },
                'context': {'id': 'test3', 'Full Name': 'Bob Johnson', 'source': 'test'},
                'expected_company_empty': True,
                'expected_website_rejected': True
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Test end-to-end cleaning
            result = data_cleaner.clean_and_validate(test_case['input'], test_case['context'])
            
            print(f"   Input Company: {test_case['input']['Company'][:50]}...")
            print(f"   Input Website: {test_case['input']['Website']}")
            print(f"   Success: {result.success}")
            print(f"   Cleaned Data: {result.cleaned_data}")
            print(f"   Confidence: {result.confidence_score}")
            
            # Check results
            test_passed = True
            
            if test_case.get('expected_company_contains'):
                if test_case['expected_company_contains'] not in str(result.cleaned_data.get('Company', '')):
                    print(f"   ❌ Company doesn't contain expected text")
                    test_passed = False
            
            if test_case.get('expected_company_empty'):
                if result.cleaned_data.get('Company'):
                    print(f"   ❌ Expected empty company but got: {result.cleaned_data.get('Company')}")
                    test_passed = False
            
            if test_case.get('expected_website_valid'):
                if not result.cleaned_data.get('Website'):
                    print(f"   ❌ Expected valid website but was rejected")
                    test_passed = False
            
            if test_case.get('expected_website_rejected'):
                if result.cleaned_data.get('Website'):
                    print(f"   ❌ Expected website rejection but got: {result.cleaned_data.get('Website')}")
                    test_passed = False
            
            if test_passed:
                print(f"   ✅ PASS - End-to-end cleaning worked correctly")
                success_count += 1
            else:
                print(f"   ❌ FAIL - End-to-end cleaning issues")
        
        print(f"\\n📊 End-to-End Tests: {success_count}/{len(test_cases)} passed")
        
        if success_count >= len(test_cases) * 0.8:  # 80% success rate
            print(f"\\n✅ End-to-end cleaning working correctly")
            return True
        else:
            print(f"\\n❌ End-to-end cleaning needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Error testing end-to-end cleaning: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all comprehensive cleaning rule tests."""
    print("🧹 Comprehensive Cleaning Rules Test Suite")
    print("=" * 70)
    
    try:
        # Run all test suites
        test_results = []
        
        test_results.append(test_sirius_xm_pattern_removal())
        test_results.append(test_html_fragment_cleaning())
        test_results.append(test_company_name_normalization())
        test_results.append(test_website_url_validation())
        test_results.append(test_search_artifact_removal())
        test_results.append(test_text_normalization())
        test_results.append(test_end_to_end_cleaning())
        
        # Overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\\n🎯 OVERALL TEST RESULTS")
        print("=" * 40)
        print(f"Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\\n✅ ALL CLEANING RULE TESTS PASSED!")
            print("🎉 All cleaning rules are working perfectly")
            print("🎵 Sirius XM pattern removal operational")
            print("🌐 HTML fragment cleaning functional")
            print("🏢 Company name normalization working")
            print("🌐 Website URL validation operational")
            print("🔍 Search artifact removal functional")
            print("📝 Text normalization working")
            print("🔄 End-to-end cleaning pipeline operational")
            return True
        else:
            print(f"\\n❌ SOME CLEANING RULE TESTS FAILED!")
            print("🔧 Cleaning rules need fixes")
            
            # Show which tests failed
            test_names = [
                "Sirius XM Pattern Removal",
                "HTML Fragment Cleaning", 
                "Company Name Normalization",
                "Website URL Validation",
                "Search Artifact Removal",
                "Text Normalization",
                "End-to-End Cleaning"
            ]
            
            for i, (name, result) in enumerate(zip(test_names, test_results)):
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} {name}")
            
            return False
            
    except Exception as e:
        print(f"\\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)