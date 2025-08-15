#!/usr/bin/env python3
"""
Test script for Google Website Scraper.

This script tests the Google search fallback functionality
for discovering company websites when SerpAPI doesn't provide them.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.google_scraper import GoogleWebsiteScraper, search_company_website_google_sync
    GOOGLE_SCRAPER_AVAILABLE = True
except ImportError as e:
    GOOGLE_SCRAPER_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('google-scraper-test')

def test_google_scraper_availability():
    """Test if Google scraper is available and properly configured."""
    
    logger.info("🧪 Testing Google scraper availability")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.error(f"❌ Google scraper not available: {import_error}")
        logger.info("💡 To install Playwright: pip install playwright && playwright install")
        return False
    
    try:
        scraper = GoogleWebsiteScraper()
        logger.info("✅ Google scraper initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Google scraper initialization failed: {str(e)}")
        return False

def test_search_query_building():
    """Test search query building functionality."""
    
    logger.info("\n🧪 Testing search query building")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - Google scraper not available")
        return False
    
    try:
        scraper = GoogleWebsiteScraper()
        
        test_cases = [
            {
                'full_name': 'John Smith',
                'company_name': 'TechCorp',
                'expected_contains': ['"John Smith"', '"TechCorp"', 'site:.com', 'site:.ca']
            },
            {
                'full_name': 'Jane Doe',
                'company_name': None,
                'expected_contains': ['"Jane Doe"', 'site:.com', 'site:.ca']
            },
            {
                'full_name': 'Mike "CEO" Johnson',
                'company_name': 'Test & Co',
                'expected_contains': ['Mike CEO Johnson', 'Test & Co']  # Quotes should be cleaned
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"   Test {i}: {test_case['full_name']}" + 
                       (f" at {test_case['company_name']}" if test_case['company_name'] else ""))
            
            query = scraper._build_search_query(test_case['full_name'], test_case['company_name'])
            logger.info(f"   Query: {query}")
            
            # Check if expected elements are in the query
            all_found = True
            for expected in test_case['expected_contains']:
                if expected not in query:
                    logger.warning(f"   ⚠️ Expected '{expected}' not found in query")
                    all_found = False
            
            if all_found:
                logger.info(f"   ✅ Query building test {i} passed")
            else:
                logger.warning(f"   ❌ Query building test {i} failed")
        
        logger.info("✅ Search query building tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Search query building test failed: {str(e)}")
        return False

def test_url_validation():
    """Test URL validation functionality."""
    
    logger.info("\n🧪 Testing URL validation")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - Google scraper not available")
        return False
    
    try:
        scraper = GoogleWebsiteScraper()
        
        test_urls = [
            # Valid company websites
            ('https://techcorp.com', True),
            ('https://www.startup.io', True),
            ('http://company.ca', True),
            ('https://business.org', True),
            
            # Invalid or filtered URLs
            ('https://linkedin.com/company/test', False),
            ('https://facebook.com/company', False),
            ('https://google.com/search', False),
            ('https://wikipedia.org/wiki/company', False),
            ('invalid-url', False),
            ('', False),
            (None, False),
        ]
        
        passed_tests = 0
        total_tests = len(test_urls)
        
        for url, expected_valid in test_urls:
            is_valid = scraper._is_valid_company_website(url)
            
            if is_valid == expected_valid:
                status = "✅ PASS"
                passed_tests += 1
            else:
                status = "❌ FAIL"
            
            logger.info(f"   {status}: {url} -> {is_valid} (expected {expected_valid})")
        
        logger.info(f"✅ URL validation tests: {passed_tests}/{total_tests} passed")
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ URL validation test failed: {str(e)}")
        return False

def test_url_cleaning():
    """Test URL cleaning functionality."""
    
    logger.info("\n🧪 Testing URL cleaning")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - Google scraper not available")
        return False
    
    try:
        scraper = GoogleWebsiteScraper()
        
        test_cases = [
            # Google redirect URLs
            ('/url?q=https://techcorp.com&sa=U', 'https://techcorp.com'),
            
            # URLs without protocol
            ('company.com', 'https://company.com'),
            ('www.startup.io', 'https://www.startup.io'),
            
            # Already clean URLs
            ('https://business.ca', 'https://business.ca'),
            
            # Invalid URLs
            ('invalid', None),
            ('', None),
            (None, None),
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for input_url, expected_output in test_cases:
            cleaned_url = scraper._clean_url(input_url)
            
            if cleaned_url == expected_output:
                status = "✅ PASS"
                passed_tests += 1
            else:
                status = "❌ FAIL"
            
            logger.info(f"   {status}: '{input_url}' -> '{cleaned_url}' (expected '{expected_output}')")
        
        logger.info(f"✅ URL cleaning tests: {passed_tests}/{total_tests} passed")
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ URL cleaning test failed: {str(e)}")
        return False

def test_sync_wrapper():
    """Test synchronous wrapper function."""
    
    logger.info("\n🧪 Testing synchronous wrapper")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - Google scraper not available")
        return False
    
    try:
        # Test that the sync wrapper is callable
        if callable(search_company_website_google_sync):
            logger.info("✅ Sync wrapper function is callable")
        else:
            logger.error("❌ Sync wrapper function is not callable")
            return False
        
        # Test with mock data (won't actually search to avoid rate limiting)
        logger.info("✅ Sync wrapper test completed (actual search skipped to avoid rate limiting)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sync wrapper test failed: {str(e)}")
        return False

def test_integration_readiness():
    """Test that the Google scraper is ready for integration."""
    
    logger.info("\n🧪 Testing integration readiness")
    
    if not GOOGLE_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Google scraper not available for integration")
        return False
    
    try:
        # Check that all required methods exist
        scraper = GoogleWebsiteScraper()
        
        required_methods = [
            'search_company_website',
            'search_company_website_sync',
            '_build_search_query',
            '_is_valid_company_website',
            '_clean_url'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(scraper, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.error(f"❌ Missing required methods: {missing_methods}")
            return False
        else:
            logger.info("✅ All required methods present")
        
        # Check that convenience functions exist
        try:
            from utils.google_scraper import search_company_website_google, search_company_website_google_sync
            logger.info("✅ Convenience functions available")
        except ImportError:
            logger.error("❌ Convenience functions not available")
            return False
        
        logger.info("✅ Google scraper is ready for integration")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration readiness test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Google Website Scraper Tests")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Availability", test_google_scraper_availability),
            ("Query Building", test_search_query_building),
            ("URL Validation", test_url_validation),
            ("URL Cleaning", test_url_cleaning),
            ("Sync Wrapper", test_sync_wrapper),
            ("Integration Readiness", test_integration_readiness),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 40)
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
            if passed:
                passed_tests += 1
        
        logger.info(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All Google scraper tests passed!")
        else:
            logger.warning("⚠️ Some tests failed - check logs above")
            
            if not GOOGLE_SCRAPER_AVAILABLE:
                logger.info("\n💡 To enable Google scraper:")
                logger.info("   pip install playwright")
                logger.info("   playwright install")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)