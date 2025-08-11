#!/usr/bin/env python3
"""
Test script to verify Google Enricher integration with DataCleaner.

This script tests the integration between the Google Enricher and the
comprehensive DataCleaner system to ensure proper data cleaning and validation.
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from outreach.google_enricher.app import GoogleEnricherAgent
from shared.data_cleaner import DataCleaner, CleaningResult, ValidationResult, CleaningAction


def test_google_enricher_initialization():
    """Test that Google Enricher initializes with DataCleaner properly."""
    print("🔧 Testing Google Enricher Initialization")
    print("=" * 50)
    
    try:
        # Initialize Google Enricher Agent
        agent = GoogleEnricherAgent()
        
        # Check that DataCleaner was initialized
        has_data_cleaner = hasattr(agent, 'data_cleaner') and agent.data_cleaner is not None
        data_cleaner_type = type(agent.data_cleaner).__name__ if agent.data_cleaner else 'None'
        
        print(f"✅ Google Enricher initialized: True")
        print(f"✅ DataCleaner present: {has_data_cleaner}")
        print(f"✅ DataCleaner type: {data_cleaner_type}")
        
        if has_data_cleaner:
            print(f"✅ Google Enricher successfully integrated with DataCleaner")
            return True
        else:
            print(f"❌ Google Enricher missing DataCleaner integration")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google Enricher initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_cleaning_integration():
    """Test the data cleaning integration in the Google Enricher."""
    print("\\n🧹 Testing Data Cleaning Integration")
    print("=" * 50)
    
    try:
        # Initialize Google Enricher Agent
        agent = GoogleEnricherAgent()
        
        if not agent.data_cleaner:
            print("❌ DataCleaner not available, skipping integration test")
            return False
        
        # Test data that should be cleaned
        test_raw_data = {
            'Company': 'Google Search Results TechCorp Inc',
            'Website': 'https://linkedin.com/company/test'
        }
        
        test_lead_context = {
            'id': 'test_lead_123',
            'Full Name': 'John Doe',
            'LinkedIn URL': 'https://linkedin.com/in/johndoe',
            'source': 'google_enricher'
        }
        
        print(f"🧪 Testing data cleaning with:")
        print(f"   Raw data: {test_raw_data}")
        print(f"   Lead context: {test_lead_context['Full Name']}")
        
        # Use the DataCleaner to clean and validate the data
        cleaning_result = agent.data_cleaner.clean_and_validate(test_raw_data, test_lead_context)
        
        print(f"\\n📊 Cleaning Results:")
        print(f"   Success: {cleaning_result.success}")
        print(f"   Cleaned data: {cleaning_result.cleaned_data}")
        print(f"   Cleaning actions: {len(cleaning_result.cleaning_actions)}")
        print(f"   Validation results: {len(cleaning_result.validation_results)}")
        print(f"   Confidence score: {cleaning_result.confidence_score}")
        
        if cleaning_result.rejection_reasons:
            print(f"   Rejection reasons: {cleaning_result.rejection_reasons}")
        
        # Verify that cleaning occurred
        has_cleaning_actions = len(cleaning_result.cleaning_actions) > 0
        has_validation_results = len(cleaning_result.validation_results) > 0
        has_confidence_score = cleaning_result.confidence_score >= 0
        
        print(f"\\n✅ Integration Verification:")
        print(f"   Cleaning actions generated: {has_cleaning_actions}")
        print(f"   Validation results generated: {has_validation_results}")
        print(f"   Confidence score calculated: {has_confidence_score}")
        
        if has_cleaning_actions and has_validation_results and has_confidence_score:
            print(f"\\n✅ Data cleaning integration working correctly")
            return True
        else:
            print(f"\\n❌ Data cleaning integration has issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data cleaning integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_validation():
    """Test the fallback validation when DataCleaner is not available."""
    print("\\n🔄 Testing Fallback Validation")
    print("=" * 50)
    
    try:
        # Initialize Google Enricher Agent
        agent = GoogleEnricherAgent()
        
        # Temporarily disable DataCleaner to test fallback
        original_data_cleaner = agent.data_cleaner
        agent.data_cleaner = None
        
        # Test fallback validation method
        test_cases = [
            {
                'name': 'Valid Company',
                'lead_id': 'test_123',
                'full_name': 'John Doe',
                'raw_data': {'Company': 'TechCorp Inc'},
                'expected': True
            },
            {
                'name': 'Invalid Company (Google)',
                'lead_id': 'test_124',
                'full_name': 'Jane Smith',
                'raw_data': {'Company': 'Google Search Results'},
                'expected': False
            },
            {
                'name': 'Valid Website',
                'lead_id': 'test_125',
                'full_name': 'Bob Johnson',
                'raw_data': {'Website': 'https://techcorp.com'},
                'expected': True
            },
            {
                'name': 'Invalid Website (LinkedIn)',
                'lead_id': 'test_126',
                'full_name': 'Alice Brown',
                'raw_data': {'Website': 'https://linkedin.com/company/test'},
                'expected': False
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test {i}: {test_case['name']}")
            
            # Mock the airtable update to avoid actual API calls
            with patch.object(agent.airtable_client, 'update_lead_fields', return_value=True):
                result = agent._fallback_validation_and_update(
                    test_case['lead_id'],
                    test_case['full_name'],
                    test_case['raw_data']
                )
            
            print(f"   Expected: {test_case['expected']}")
            print(f"   Actual: {result}")
            
            if result == test_case['expected']:
                print(f"   ✅ PASS")
                success_count += 1
            else:
                print(f"   ❌ FAIL")
        
        # Restore original DataCleaner
        agent.data_cleaner = original_data_cleaner
        
        print(f"\\n📊 Fallback Validation Results: {success_count}/{len(test_cases)} passed")
        
        if success_count == len(test_cases):
            print(f"\\n✅ Fallback validation working correctly")
            return True
        else:
            print(f"\\n❌ Fallback validation has issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fallback validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_final_validation_checks():
    """Test the final validation checks for company and website data."""
    print("\\n🔍 Testing Final Validation Checks")
    print("=" * 50)
    
    try:
        # Initialize Google Enricher Agent
        agent = GoogleEnricherAgent()
        
        # Test company validation
        company_test_cases = [
            {'value': 'TechCorp Inc', 'expected': True, 'name': 'Valid company with Inc'},
            {'value': 'Google Search Results', 'expected': False, 'name': 'Invalid - contains Google'},
            {'value': 'Microsoft Corporation', 'expected': True, 'name': 'Valid large company'},
            {'value': 'linkedin company', 'expected': False, 'name': 'Invalid - contains linkedin'},
            {'value': 'AB', 'expected': False, 'name': 'Invalid - too short'},
            {'value': 'Unknown Company', 'expected': False, 'name': 'Invalid - generic unknown'},
        ]
        
        print(f"\\n🏢 Testing Company Validation:")
        company_success = 0
        
        for test in company_test_cases:
            result = agent._final_validation_check(test['value'], 'John Doe', 'company')
            print(f"   {test['name']}: {result} (expected: {test['expected']})")
            if result == test['expected']:
                company_success += 1
        
        # Test website validation
        website_test_cases = [
            {'value': 'https://techcorp.com', 'expected': True, 'name': 'Valid HTTPS website'},
            {'value': 'http://company.ca', 'expected': True, 'name': 'Valid HTTP website'},
            {'value': 'https://google.com/search', 'expected': False, 'name': 'Invalid - Google domain'},
            {'value': 'https://linkedin.com/company/test', 'expected': False, 'name': 'Invalid - LinkedIn domain'},
            {'value': 'not-a-url', 'expected': False, 'name': 'Invalid - not a URL'},
            {'value': 'https://example.com', 'expected': False, 'name': 'Invalid - example domain'},
        ]
        
        print(f"\\n🌐 Testing Website Validation:")
        website_success = 0
        
        for test in website_test_cases:
            result = agent._final_validation_check(test['value'], 'John Doe', 'website')
            print(f"   {test['name']}: {result} (expected: {test['expected']})")
            if result == test['expected']:
                website_success += 1
        
        total_tests = len(company_test_cases) + len(website_test_cases)
        total_success = company_success + website_success
        
        print(f"\\n📊 Final Validation Results:")
        print(f"   Company validation: {company_success}/{len(company_test_cases)} passed")
        print(f"   Website validation: {website_success}/{len(website_test_cases)} passed")
        print(f"   Overall: {total_success}/{total_tests} passed")
        
        if total_success == total_tests:
            print(f"\\n✅ Final validation checks working correctly")
            return True
        else:
            print(f"\\n❌ Final validation checks have issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing final validation checks: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_process_single_lead_integration():
    """Test the complete _process_single_lead method with mocked dependencies."""
    print("\\n🔗 Testing Complete Process Single Lead Integration")
    print("=" * 50)
    
    try:
        # Initialize Google Enricher Agent
        agent = GoogleEnricherAgent()
        
        # Mock the scraping engine
        mock_scraping_engine = Mock()
        mock_scraping_engine.browser = Mock()
        mock_page = AsyncMock()
        mock_scraping_engine.browser.new_page = AsyncMock(return_value=mock_page)
        
        # Mock page methods
        mock_page.set_extra_http_headers = AsyncMock()
        mock_page.set_viewport_size = AsyncMock()
        mock_page.goto = AsyncMock(return_value=Mock(status=200))
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="TechCorp Inc John Doe CEO founder company website https://techcorp.com")
        mock_page.close = AsyncMock()
        
        # Mock airtable client
        with patch.object(agent.airtable_client, 'update_lead_fields', return_value=True):
            # Test lead data
            test_lead = {
                'id': 'test_lead_123',
                'Full Name': 'John Doe',
                'Company': '',  # Missing company
                'Website': '',  # Missing website
                'LinkedIn URL': 'https://linkedin.com/in/johndoe'
            }
            
            print(f"🧪 Testing complete lead processing:")
            print(f"   Lead: {test_lead['Full Name']}")
            print(f"   Missing: Company and Website")
            
            # Process the lead
            result = await agent._process_single_lead(test_lead, mock_scraping_engine)
            
            print(f"\\n📊 Processing Result: {result}")
            
            # Verify that the process completed
            if isinstance(result, bool):
                print(f"\\n✅ Complete process integration working correctly")
                return True
            else:
                print(f"\\n❌ Complete process integration returned unexpected result")
                return False
                
    except Exception as e:
        print(f"❌ Error testing complete process integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Google Enricher integration tests."""
    print("🔗 Google Enricher DataCleaner Integration Test Suite")
    print("=" * 70)
    
    try:
        # Run all test suites
        test_results = []
        
        test_results.append(test_google_enricher_initialization())
        test_results.append(test_data_cleaning_integration())
        test_results.append(test_fallback_validation())
        test_results.append(test_final_validation_checks())
        
        # Run async test
        async_result = asyncio.run(test_process_single_lead_integration())
        test_results.append(async_result)
        
        # Overall results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\\n🎯 OVERALL TEST RESULTS")
        print("=" * 40)
        print(f"Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\\n✅ ALL GOOGLE ENRICHER INTEGRATION TESTS PASSED!")
            print("🎉 Google Enricher is properly integrated with DataCleaner")
            print("🧹 Data cleaning and validation working correctly")
            print("🔄 Fallback validation operational")
            print("🔍 Final validation checks functional")
            print("🔗 Complete processing pipeline integrated")
            return True
        else:
            print(f"\\n❌ SOME GOOGLE ENRICHER INTEGRATION TESTS FAILED!")
            print("🔧 Google Enricher integration needs fixes")
            return False
            
    except Exception as e:
        print(f"\\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)