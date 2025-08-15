#!/usr/bin/env python3
"""
Comprehensive unit tests for enhanced ValidationEngine methods.

This script tests the enhanced data completeness and professional standards
validation with edge cases including international companies and unusual formats.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_cleaner import ValidationEngine, ConfigurationManager


def test_enhanced_data_completeness():
    """Test enhanced data completeness validation with edge cases."""
    print("📋 Testing Enhanced Data Completeness Validation")
    print("=" * 60)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with various completeness scenarios
    completeness_cases = [
        {
            'name': 'Complete Data with Optional Fields',
            'input': {
                'company': 'TechCorp Inc',
                'website': 'https://techcorp.com',
                'phone': '+1-555-123-4567',
                'email': 'info@techcorp.com'
            },
            'expected_valid': True,
            'min_confidence': 0.9
        },
        {
            'name': 'Required Fields Only',
            'input': {
                'company': 'Business Solutions LLC',
                'website': 'https://business.com'
            },
            'expected_valid': True,
            'min_confidence': 0.8
        },
        {
            'name': 'Quality Issues - Too Short Company',
            'input': {
                'company': 'A',
                'website': 'https://example.com'
            },
            'expected_valid': False,
            'min_confidence': 0.3  # Lowered expectation due to quality penalty
        },
        {
            'name': 'Quality Issues - Placeholder Values',
            'input': {
                'company': 'N/A',
                'website': 'https://example.com'
            },
            'expected_valid': False,
            'min_confidence': 0.3
        },
        {
            'name': 'Missing Required Field',
            'input': {
                'company': 'TechCorp Inc'
                # Missing website
            },
            'expected_valid': False,
            'min_confidence': 0.0
        },
        {
            'name': 'International Company with Optional Data',
            'input': {
                'company': 'München Tech GmbH',
                'website': 'https://muenchen-tech.de',
                'address': 'Munich, Germany'
            },
            'expected_valid': True,
            'min_confidence': 0.85
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
    
    print(f"\n📊 Enhanced Data Completeness Tests: {success_count}/{len(completeness_cases)} passed")
    return success_count == len(completeness_cases)


def test_international_professional_standards():
    """Test professional standards validation with international companies."""
    print("\n🌍 Testing International Professional Standards Validation")
    print("=" * 60)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with international company formats
    international_cases = [
        {
            'name': 'German GmbH Company',
            'input': {
                'company': 'Technologie Solutions GmbH',
                'website': 'https://techsolutions.de'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'French SARL Company',
            'input': {
                'company': 'Consulting Services SARL',
                'website': 'https://consulting.fr'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Australian Pty Ltd Company',
            'input': {
                'company': 'Melbourne Tech Pty Ltd',
                'website': 'https://melbournetech.com.au'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Swedish AB Company',
            'input': {
                'company': 'Stockholm Digital AB',
                'website': 'https://stockholm-digital.se'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Singapore Pte Ltd Company',
            'input': {
                'company': 'Asia Business Solutions Pte Ltd',
                'website': 'https://asiabusiness.com.sg'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Malaysian Sdn Bhd Company',
            'input': {
                'company': 'Kuala Lumpur Trading Sdn Bhd',
                'website': 'https://kltrading.com.my'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Non-English Company Name',
            'input': {
                'company': '北京科技有限公司',  # Beijing Technology Co Ltd in Chinese
                'website': 'https://beijing-tech.cn'
            },
            'expected_valid': False,  # Will fail due to no recognizable entity indicators
            'min_confidence': 0.3
        },
        {
            'name': 'Low Quality International',
            'input': {
                'company': 'test gmbh',
                'website': 'http://test.de'
            },
            'expected_valid': False,  # Should fail due to "test" being unprofessional
            'min_confidence': 0.2
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(international_cases, 1):
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
    
    print(f"\n📊 International Professional Standards Tests: {success_count}/{len(international_cases)} passed")
    return success_count == len(international_cases)


def test_edge_case_scenarios():
    """Test edge case scenarios for validation."""
    print("\n🔍 Testing Edge Case Scenarios")
    print("=" * 60)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test cases with edge cases and unusual formats
    edge_cases = [
        {
            'name': 'Very Long Company Name',
            'input': {
                'company': 'International Business Machines Corporation Global Technology Solutions and Services Division',
                'website': 'https://ibm.com'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Company with Numbers',
            'input': {
                'company': '3M Company',
                'website': 'https://3m.com'
            },
            'expected_valid': True,
            'min_confidence': 0.5
        },
        {
            'name': 'Company with Special Characters',
            'input': {
                'company': 'AT&T Inc.',
                'website': 'https://att.com'
            },
            'expected_valid': True,
            'min_confidence': 0.5
        },
        {
            'name': 'Hyphenated Company Name',
            'input': {
                'company': 'Rolls-Royce Holdings plc',
                'website': 'https://rolls-royce.com'
            },
            'expected_valid': True,
            'min_confidence': 0.6
        },
        {
            'name': 'Single Word Professional Company',
            'input': {
                'company': 'Microsoft',
                'website': 'https://microsoft.com'
            },
            'expected_valid': True,
            'min_confidence': 0.4
        },
        {
            'name': 'Obvious Test Data',
            'input': {
                'company': 'Test Company 123',
                'website': 'https://example.com'
            },
            'expected_valid': False,
            'min_confidence': 0.1  # Will have very low confidence due to penalties
        },
        {
            'name': 'Mixed Case Issues',
            'input': {
                'company': 'tEcH cOrP iNc',
                'website': 'https://techcorp.com'
            },
            'expected_valid': True,  # Should pass due to entity indicator
            'min_confidence': 0.4
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        
        # Test both completeness and professional standards
        completeness_result = engine.validate_data_completeness(test_case['input'])
        professional_result = engine.validate_professional_standards(test_case['input'])
        
        print(f"   Completeness Valid: {completeness_result.is_valid} (Score: {completeness_result.confidence_score:.2f})")
        print(f"   Professional Valid: {professional_result.is_valid} (Score: {professional_result.confidence_score:.2f})")
        
        # For edge cases, we primarily care about professional standards
        expected_valid = test_case['expected_valid']
        min_confidence = test_case['min_confidence']
        
        if professional_result.is_valid == expected_valid and professional_result.confidence_score >= min_confidence:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected valid: {expected_valid}, confidence >= {min_confidence}")
    
    print(f"\n📊 Edge Case Tests: {success_count}/{len(edge_cases)} passed")
    return success_count == len(edge_cases)


def test_validation_integration():
    """Test integration of all validation methods together."""
    print("\n🔗 Testing Validation Integration")
    print("=" * 60)
    
    # Initialize the validation engine
    config_manager = ConfigurationManager()
    engine = ValidationEngine(config_manager.validation_rules)
    
    # Test comprehensive validation scenarios
    integration_cases = [
        {
            'name': 'High Quality International Business',
            'data': {
                'company': 'München Technology Solutions GmbH',
                'website': 'https://muenchen-tech.de',
                'phone': '+49-89-123456',
                'email': 'info@muenchen-tech.de'
            },
            'context': {'Full Name': 'Hans Mueller'},
            'expected_results': {
                'completeness': True,
                'professional': True,
                'consistency': True
            }
        },
        {
            'name': 'Moderate Quality Business',
            'data': {
                'company': 'Business Services',
                'website': 'http://business.com'
            },
            'context': {'Full Name': 'John Smith'},
            'expected_results': {
                'completeness': True,
                'professional': True,  # Should pass with business indicator
                'consistency': True
            }
        },
        {
            'name': 'Low Quality Data',
            'data': {
                'company': 'test company',
                'website': 'https://facebook.com/test'
            },
            'context': {'Full Name': 'Test User'},
            'expected_results': {
                'completeness': True,
                'professional': False,  # Should fail due to test + social media
                'consistency': False    # Should fail due to social media
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(integration_cases, 1):
        print(f"\n🧪 Integration Test {i}: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        print(f"   Context: {test_case['context']}")
        
        # Run all validation methods
        completeness_result = engine.validate_data_completeness(test_case['data'])
        professional_result = engine.validate_professional_standards(test_case['data'])
        consistency_result = engine.validate_context_consistency(test_case['data'], test_case['context'])
        
        print(f"   Completeness: {completeness_result.is_valid} (Score: {completeness_result.confidence_score:.2f})")
        print(f"   Professional: {professional_result.is_valid} (Score: {professional_result.confidence_score:.2f})")
        print(f"   Consistency: {consistency_result.is_valid} (Score: {consistency_result.confidence_score:.2f})")
        
        # Check all expected results
        expected = test_case['expected_results']
        all_passed = (
            completeness_result.is_valid == expected['completeness'] and
            professional_result.is_valid == expected['professional'] and
            consistency_result.is_valid == expected['consistency']
        )
        
        if all_passed:
            print(f"   ✅ PASS")
            success_count += 1
        else:
            print(f"   ❌ FAIL - Expected: {expected}")
    
    print(f"\n📊 Integration Tests: {success_count}/{len(integration_cases)} passed")
    return success_count == len(integration_cases)


def main():
    """Run all enhanced validation tests."""
    print("🔍 Enhanced ValidationEngine Test Suite")
    print("=" * 70)
    
    try:
        # Run all test suites
        test_results = []
        
        test_results.append(test_enhanced_data_completeness())
        test_results.append(test_international_professional_standards())
        test_results.append(test_edge_case_scenarios())
        test_results.append(test_validation_integration())
        
        # Overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n🎯 OVERALL TEST RESULTS")
        print("=" * 40)
        print(f"Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n✅ ALL ENHANCED TESTS PASSED!")
            print("🎉 Enhanced ValidationEngine is working perfectly")
            print("🌍 International company support operational")
            print("🔍 Edge case handling functional")
            print("📊 Data completeness validation enhanced")
            print("✨ Professional standards validation improved")
            return True
        else:
            print(f"\n❌ SOME ENHANCED TESTS FAILED!")
            print("🔧 Enhanced ValidationEngine needs fixes")
            return False
            
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)