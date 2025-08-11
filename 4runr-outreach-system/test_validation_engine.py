#!/usr/bin/env python3
"""
Comprehensive unit tests for the ValidationEngine class.

This script tests all validation methods with real-world examples
to ensure proper quality checks, confidence scoring, and professional
standards validation.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import ValidationEngine, ConfigurationManager


def test_company_name_validation():
    """Test company name validation with various quality levels."""
    print("🏢 Testing Company Name Validation")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with different company name quality levels
    company_cases = [
        {
            'name': 'High Quality Professional Company',
            'input': 'Montreal Tech Solutions Inc',
            'context': {'Full Name': 'John Doe'},
            'expected_valid': True,
            'min_confidence': 0.8
        },
        {
            'name': 'Professional Company with LLC',
            'input': 'Digital Marketing Solutions LLC',
            'context': {'Full Name': 'Jane Smith'},
            'expected_valid': True,
            'min_confidence': 0.8
        },
        {
            'name': 'Simple Professional Company',
            'input': 'TechCorp',
            'context': {'Full Name': 'Bob Johnson'},
            'expected_valid': True,
            'min_confidence': 0.7
        },
        {
            'name': 'Company with Forbidden Pattern',
            'input': 'Google Search Results Company',
            'context': {'Full Name': 'Alice Brown'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Too Short Company Name',
            'input': 'A',
            'context': {'Full Name': 'Charlie Wilson'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Empty Company Name',
            'input': '',
            'context': {'Full Name': 'David Lee'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Company with Invalid Characters',
            'input': 'Tech@#$%Corp!!!',
            'context': {'Full Name': 'Eva Martinez'},
            'expected_valid': False,
            'min_confidence': 0.3
        },
        {
            'name': 'Professional Services Company',
            'input': 'Strategic Business Consulting Group',
            'context': {'Full Name': 'Frank Taylor'},
            'expected_valid': True,
            'min_confidence': 0.8
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(company_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Input: '{test_case['input']}'")
        
        # Validate the company name
        result = engine.validate_company_name(test_case['input'], test_case['context'])
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Rule: {result.validation_rule}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check expectations
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if result.is_valid == expected_valid and result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Company Name Tests: {success_count}/{len(company_cases)} passed")
    return success_count == len(company_cases)


def test_website_url_validation():
    """Test website URL validation with various formats and domains."""
    print("\n🌐 Testing Website URL Validation")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with different website URL quality levels
    website_cases = [
        {
            'name': 'High Quality HTTPS Website',
            'input': 'https://montrealtechsolutions.com',
            'context': {'Full Name': 'John Doe'},
            'expected_valid': True,
            'min_confidence': 0.9
        },
        {
            'name': 'Professional HTTP Website',
            'input': 'http://techcorp.com',
            'context': {'Full Name': 'Jane Smith'},
            'expected_valid': True,
            'min_confidence': 0.8
        },
        {
            'name': 'Business .org Website',
            'input': 'https://techfoundation.org',
            'context': {'Full Name': 'Bob Johnson'},
            'expected_valid': True,
            'min_confidence': 0.9
        },
        {
            'name': 'Forbidden Domain (Google)',
            'input': 'https://google.com/search',
            'context': {'Full Name': 'Alice Brown'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Forbidden Domain (LinkedIn)',
            'input': 'https://linkedin.com/company/tech',
            'context': {'Full Name': 'Charlie Wilson'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Invalid URL Format',
            'input': 'not-a-url',
            'context': {'Full Name': 'David Lee'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Empty Website',
            'input': '',
            'context': {'Full Name': 'Eva Martinez'},
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Canadian Business Website',
            'input': 'https://canadianbusiness.ca',
            'context': {'Full Name': 'Frank Taylor'},
            'expected_valid': True,
            'min_confidence': 0.9
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(website_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Input: '{test_case['input']}'")
        
        # Validate the website URL
        result = engine.validate_website_url(test_case['input'], test_case['context'])
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Rule: {result.validation_rule}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check expectations
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if result.is_valid == expected_valid and result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Website URL Tests: {success_count}/{len(website_cases)} passed")
    return success_count == len(website_cases)


def test_data_completeness_validation():
    """Test data completeness validation."""
    print("\n📋 Testing Data Completeness Validation")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with different completeness levels
    completeness_cases = [
        {
            'name': 'Complete Data',
            'input': {
                'company': 'TechCorp Inc',
                'website': 'https://techcorp.com'
            },
            'expected_valid': True,
            'min_confidence': 1.0
        },
        {
            'name': 'Missing Company',
            'input': {
                'website': 'https://techcorp.com'
            },
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Missing Website',
            'input': {
                'company': 'TechCorp Inc'
            },
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Empty Company',
            'input': {
                'company': '',
                'website': 'https://techcorp.com'
            },
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'Empty Website',
            'input': {
                'company': 'TechCorp Inc',
                'website': ''
            },
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'All Empty',
            'input': {
                'company': '',
                'website': ''
            },
            'expected_valid': False,
            'min_confidence': 0.0
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(completeness_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        
        # Validate data completeness
        result = engine.validate_data_completeness(test_case['input'])
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Rule: {result.validation_rule}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check expectations
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if result.is_valid == expected_valid and result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Data Completeness Tests: {success_count}/{len(completeness_cases)} passed")
    return success_count == len(completeness_cases)


def test_professional_standards_validation():
    """Test professional standards validation."""
    print("\n✨ Testing Professional Standards Validation")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with different professional quality levels
    professional_cases = [
        {
            'name': 'High Professional Quality',
            'input': {
                'company': 'Montreal Tech Solutions Inc',
                'website': 'https://montrealtechsolutions.com'
            },
            'expected_valid': True,
            'min_confidence': 0.5
        },
        {
            'name': 'Good Professional Quality',
            'input': {
                'company': 'TechCorp LLC',
                'website': 'https://techcorp.com'
            },
            'expected_valid': True,
            'min_confidence': 0.5
        },
        {
            'name': 'Moderate Quality (HTTP)',
            'input': {
                'company': 'Business Services',
                'website': 'http://business.com'
            },
            'expected_valid': True,
            'min_confidence': 0.4
        },
        {
            'name': 'Low Quality (No Entity)',
            'input': {
                'company': 'techcorp',
                'website': 'http://techcorp.com'
            },
            'expected_valid': False,
            'min_confidence': 0.3
        },
        {
            'name': 'Very Low Quality (Social Media)',
            'input': {
                'company': 'company',
                'website': 'https://facebook.com/company'
            },
            'expected_valid': False,
            'min_confidence': 0.2
        },
        {
            'name': 'No Data',
            'input': {
                'company': '',
                'website': ''
            },
            'expected_valid': False,
            'min_confidence': 0.0
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(professional_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        
        # Validate professional standards
        result = engine.validate_professional_standards(test_case['input'])
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Rule: {result.validation_rule}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check expectations
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if result.is_valid == expected_valid and result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Professional Standards Tests: {success_count}/{len(professional_cases)} passed")
    return success_count == len(professional_cases)


def test_context_consistency_validation():
    """Test context consistency validation."""
    print("\n🔗 Testing Context Consistency Validation")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with different consistency levels
    consistency_cases = [
        {
            'name': 'Consistent Company and Website',
            'data': {
                'company': 'TechCorp Solutions Inc',
                'website': 'https://techcorp.com'
            },
            'context': {'Full Name': 'John Doe'},
            'expected_valid': True,
            'min_confidence': 0.7
        },
        {
            'name': 'Partially Consistent',
            'data': {
                'company': 'Montreal Tech Inc',
                'website': 'https://montreal-solutions.com'
            },
            'context': {'Full Name': 'Jane Smith'},
            'expected_valid': True,
            'min_confidence': 0.7
        },
        {
            'name': 'Inconsistent Company and Website',
            'data': {
                'company': 'ABC Company',
                'website': 'https://xyz-corp.com'
            },
            'context': {'Full Name': 'Bob Johnson'},
            'expected_valid': False,
            'min_confidence': 0.5
        },
        {
            'name': 'Name in Company (Suspicious)',
            'data': {
                'company': 'John Doe Consulting',
                'website': 'https://johndoe.com'
            },
            'context': {'Full Name': 'John Doe'},
            'expected_valid': True,  # This might be legitimate
            'min_confidence': 0.6
        },
        {
            'name': 'Google Mismatch',
            'data': {
                'company': 'Google Inc',
                'website': 'https://google.com'
            },
            'context': {'Full Name': 'Alice Brown'},
            'expected_valid': False,
            'min_confidence': 0.3
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(consistency_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        print(f"   Context: {test_case['context']}")
        
        # Validate context consistency
        result = engine.validate_context_consistency(test_case['data'], test_case['context'])
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Rule: {result.validation_rule}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        # Check expectations
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if result.is_valid == expected_valid and result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Context Consistency Tests: {success_count}/{len(consistency_cases)} passed")
    return success_count == len(consistency_cases)


def test_validation_statistics():
    """Test validation statistics tracking."""
    print("\n📊 Testing Validation Statistics")
    print("=" * 50)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Run several validations to generate statistics
    test_data = [
        ('TechCorp Inc', {'Full Name': 'John Doe'}),
        ('', {'Full Name': 'Jane Smith'}),
        ('Google Search Results', {'Full Name': 'Bob Johnson'}),
        ('Professional Services LLC', {'Full Name': 'Alice Brown'})
    ]
    
    print("Running validation tests to generate statistics...")
    
    for company, context in test_data:
        result = engine.validate_company_name(company, context)
        print(f"   Validated '{company}': {result.is_valid}")
    
    # Get statistics
    stats = engine.get_validation_statistics()
    
    print(f"\n📈 Validation Statistics:")
    print(f"   Total Validations: {stats['total_validations']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Failure Rate: {stats['failure_rate']:.1f}%")
    
    print(f"\n📋 By Rule:")
    for rule, counts in stats['by_rule'].items():
        total = counts['passed'] + counts['failed']
        success_rate = (counts['passed'] / total * 100) if total > 0 else 0
        print(f"   {rule}: {counts['passed']}/{total} ({success_rate:.1f}%)")
    
    print(f"\n📋 By Field:")
    for field, counts in stats['by_field'].items():
        total = counts['passed'] + counts['failed']
        success_rate = (counts['passed'] / total * 100) if total > 0 else 0
        print(f"   {field}: {counts['passed']}/{total} ({success_rate:.1f}%)")
    
    # Check if statistics are reasonable
    if stats['total_validations'] == len(test_data) and stats['total_validations'] > 0:
        print(f"\n✅ Statistics tracking working correctly")
        return True
    else:
        print(f"\n❌ Statistics tracking failed")
        return False


def main():
    """Run all ValidationEngine tests."""
    print("🔍 ValidationEngine Comprehensive Test Suite")
    print("=" * 60)
    
    try:
        # Run all test suites
        test_results = []
        
        test_results.append(test_company_name_validation())
        test_results.append(test_website_url_validation())
        test_results.append(test_data_completeness_validation())
        test_results.append(test_professional_standards_validation())
        test_results.append(test_context_consistency_validation())
        test_results.append(test_validation_statistics())
        
        # Overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n🎯 OVERALL TEST RESULTS")
        print("=" * 30)
        print(f"Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n✅ ALL TESTS PASSED!")
            print("🎉 ValidationEngine is working perfectly")
            print("🔍 Professional standards validation working correctly")
            print("📊 Statistics tracking and confidence scoring operational")
            print("🔗 Context consistency validation functional")
            return True
        else:
            print(f"\n❌ SOME TESTS FAILED!")
            print("🔧 ValidationEngine needs fixes")
            return False
            
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)