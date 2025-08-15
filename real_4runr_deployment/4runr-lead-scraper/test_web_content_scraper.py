#!/usr/bin/env python3
"""
Test script for Web Content Scraper.

This script tests the web content scraper with various website types
including SaaS, marketing agency, local service, error pages, and redirects.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.web_content_scraper import WebContentScraper, scrape_website_content_sync
    WEB_SCRAPER_AVAILABLE = True
except ImportError as e:
    WEB_SCRAPER_AVAILABLE = False
    import_error = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('web-content-scraper-test')

def test_scraper_availability():
    """Test if web content scraper is available and properly configured."""
    
    logger.info("🧪 Testing web content scraper availability")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.error(f"❌ Web scraper not available: {import_error}")
        return False
    
    try:
        scraper = WebContentScraper()
        logger.info("✅ Web content scraper initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Web scraper initialization failed: {str(e)}")
        return False

def test_real_websites():
    """Test scraping on 5 real websites as specified."""
    
    logger.info("\n🧪 Testing web scraper on real websites")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - web scraper not available")
        return False
    
    # Test cases as specified
    test_cases = [
        {
            'name': 'SaaS Homepage',
            'url': 'https://stripe.com',
            'expected_content': ['payment', 'api', 'developer', 'business'],
            'min_length': 500
        },
        {
            'name': 'Marketing Agency',
            'url': 'https://www.hubspot.com',
            'expected_content': ['marketing', 'sales', 'crm', 'growth'],
            'min_length': 500
        },
        {
            'name': 'Local Service Provider',
            'url': 'https://www.plumbingtoday.com',
            'expected_content': ['plumbing', 'service', 'repair'],
            'min_length': 200
        },
        {
            'name': 'Error Page (404)',
            'url': 'https://httpstat.us/404',
            'expected_error': True,
            'min_length': 0
        },
        {
            'name': 'Redirect Test',
            'url': 'http://github.com',  # Should redirect to https
            'expected_content': ['github', 'code', 'repository'],
            'min_length': 300
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🧪 Test Case {i}: {test_case['name']}")
        logger.info(f"   URL: {test_case['url']}")
        
        try:
            # Scrape the website
            result = scrape_website_content_sync(test_case['url'])
            
            # Analyze results
            test_result = {
                'name': test_case['name'],
                'url': test_case['url'],
                'success': result['success'],
                'method': result.get('method', 'unknown'),
                'content_length': result.get('content_length', 0),
                'has_title': bool(result.get('page_title', '').strip()),
                'has_meta': bool(result.get('meta_description', '').strip()),
                'error': result.get('error', ''),
                'passed': False
            }
            
            # Check if test passed
            if test_case.get('expected_error'):
                # This should fail or have minimal content
                if not result['success'] or result.get('content_length', 0) < 100:
                    test_result['passed'] = True
                    logger.info("   ✅ Error page correctly handled")
                else:
                    logger.warning("   ⚠️ Error page not detected as expected")
            else:
                # This should succeed
                if result['success']:
                    content_length = result.get('content_length', 0)
                    if content_length >= test_case['min_length']:
                        # Check for expected content
                        text_lower = result.get('text', '').lower()
                        expected_found = 0
                        for expected in test_case.get('expected_content', []):
                            if expected.lower() in text_lower:
                                expected_found += 1
                        
                        if expected_found > 0:
                            test_result['passed'] = True
                            logger.info(f"   ✅ Scraping successful: {content_length} chars, {expected_found} keywords found")
                        else:
                            logger.warning(f"   ⚠️ Expected content not found")
                    else:
                        logger.warning(f"   ⚠️ Content too short: {content_length} < {test_case['min_length']}")
                else:
                    logger.error(f"   ❌ Scraping failed: {result.get('error', 'Unknown error')}")
            
            # Log details
            logger.info(f"   📊 Method: {test_result['method']}")
            logger.info(f"   📊 Content Length: {test_result['content_length']}")
            logger.info(f"   📊 Has Title: {test_result['has_title']}")
            logger.info(f"   📊 Has Meta: {test_result['has_meta']}")
            
            if result.get('page_title'):
                logger.info(f"   📋 Title: {result['page_title'][:100]}...")
            
            if result.get('meta_description'):
                logger.info(f"   📋 Meta: {result['meta_description'][:100]}...")
            
            results.append(test_result)
            
        except Exception as e:
            logger.error(f"   ❌ Test case failed with exception: {str(e)}")
            results.append({
                'name': test_case['name'],
                'url': test_case['url'],
                'success': False,
                'error': str(e),
                'passed': False
            })
    
    # Summary
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    logger.info(f"\n📊 Real Website Test Results:")
    logger.info("=" * 50)
    logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['passed'] else "❌"
        logger.info(f"{status} {result['name']}: {result.get('method', 'failed')}")
    
    return passed_tests == total_tests

def test_content_extraction():
    """Test content extraction capabilities."""
    
    logger.info("\n🧪 Testing content extraction capabilities")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - web scraper not available")
        return False
    
    try:
        # Test with a reliable website
        test_url = "https://example.com"
        logger.info(f"   Testing with: {test_url}")
        
        result = scrape_website_content_sync(test_url)
        
        if result['success']:
            logger.info("   ✅ Basic scraping successful")
            
            # Check required fields
            required_fields = ['text', 'meta_description', 'page_title', 'success', 'url', 'scraped_at', 'method', 'content_length']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                logger.error(f"   ❌ Missing required fields: {missing_fields}")
                return False
            else:
                logger.info("   ✅ All required fields present")
            
            # Check content quality
            if result['content_length'] > 0:
                logger.info(f"   ✅ Content extracted: {result['content_length']} characters")
            else:
                logger.warning("   ⚠️ No content extracted")
            
            if result['page_title']:
                logger.info(f"   ✅ Title extracted: {result['page_title']}")
            else:
                logger.warning("   ⚠️ No title extracted")
            
            return True
        else:
            logger.error(f"   ❌ Scraping failed: {result.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Content extraction test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for various failure scenarios."""
    
    logger.info("\n🧪 Testing error handling")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - web scraper not available")
        return False
    
    error_test_cases = [
        {
            'name': 'Invalid URL',
            'url': 'not-a-valid-url',
            'should_fail': True
        },
        {
            'name': 'Non-existent domain',
            'url': 'https://this-domain-definitely-does-not-exist-12345.com',
            'should_fail': True
        },
        {
            'name': 'Empty URL',
            'url': '',
            'should_fail': True
        },
        {
            'name': 'None URL',
            'url': None,
            'should_fail': True
        }
    ]
    
    passed_tests = 0
    
    for test_case in error_test_cases:
        logger.info(f"   Testing: {test_case['name']}")
        
        try:
            result = scrape_website_content_sync(test_case['url'])
            
            if test_case['should_fail']:
                if not result['success']:
                    logger.info(f"   ✅ Correctly failed: {result.get('error', 'No error message')}")
                    passed_tests += 1
                else:
                    logger.error(f"   ❌ Should have failed but succeeded")
            else:
                if result['success']:
                    logger.info("   ✅ Correctly succeeded")
                    passed_tests += 1
                else:
                    logger.error(f"   ❌ Should have succeeded but failed: {result.get('error')}")
        
        except Exception as e:
            if test_case['should_fail']:
                logger.info(f"   ✅ Correctly failed with exception: {str(e)}")
                passed_tests += 1
            else:
                logger.error(f"   ❌ Unexpected exception: {str(e)}")
    
    logger.info(f"✅ Error handling tests: {passed_tests}/{len(error_test_cases)} passed")
    return passed_tests == len(error_test_cases)

def test_convenience_functions():
    """Test convenience functions."""
    
    logger.info("\n🧪 Testing convenience functions")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - web scraper not available")
        return False
    
    try:
        # Test sync function
        from utils.web_content_scraper import scrape_website_content_sync, scrape_website_content
        
        if callable(scrape_website_content_sync):
            logger.info("   ✅ scrape_website_content_sync available")
        else:
            logger.error("   ❌ scrape_website_content_sync not callable")
            return False
        
        if callable(scrape_website_content):
            logger.info("   ✅ scrape_website_content (async) available")
        else:
            logger.error("   ❌ scrape_website_content not callable")
            return False
        
        logger.info("✅ Convenience functions test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Convenience functions test failed: {str(e)}")
        return False

def test_integration_readiness():
    """Test that the scraper is ready for integration with enricher."""
    
    logger.info("\n🧪 Testing integration readiness")
    
    if not WEB_SCRAPER_AVAILABLE:
        logger.warning("⚠️ Skipping test - web scraper not available")
        return False
    
    try:
        # Test that scraper can be imported and used independently
        scraper = WebContentScraper()
        
        # Test that it returns the expected structure
        test_url = "https://example.com"
        result = scraper.scrape_website_sync(test_url)
        
        # Check result structure
        expected_keys = ['text', 'meta_description', 'page_title', 'success', 'url', 'scraped_at', 'method', 'content_length']
        
        for key in expected_keys:
            if key not in result:
                logger.error(f"   ❌ Missing key in result: {key}")
                return False
        
        logger.info("   ✅ Result structure correct")
        
        # Check that it can handle lead context (optional parameter)
        lead_context = {'name': 'John Doe', 'email_domain': 'example.com'}
        result_with_context = scraper.scrape_website_sync(test_url, lead_context)
        
        if 'success' in result_with_context:
            logger.info("   ✅ Lead context parameter handled correctly")
        else:
            logger.error("   ❌ Lead context parameter not handled")
            return False
        
        logger.info("✅ Integration readiness test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration readiness test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Web Content Scraper Tests")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Scraper Availability", test_scraper_availability),
            ("Real Websites", test_real_websites),
            ("Content Extraction", test_content_extraction),
            ("Error Handling", test_error_handling),
            ("Convenience Functions", test_convenience_functions),
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
            logger.info("🎉 All web content scraper tests passed!")
            logger.info("✅ Web scraper is ready for integration with enricher")
        else:
            logger.warning("⚠️ Some tests failed - check logs above")
            
            if not WEB_SCRAPER_AVAILABLE:
                logger.info("\n💡 To enable web content scraper:")
                logger.info("   pip install playwright beautifulsoup4")
                logger.info("   playwright install")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)