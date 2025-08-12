#!/usr/bin/env python3
"""
Test script to verify existing scraper functionality is maintained.

This script tests that the enhanced website extraction doesn't break
existing SerpAPI scraper functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.serpapi_scraper import SerpAPILeadScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('scraper-functionality-test')

def test_existing_functionality():
    """Test that existing scraper functionality is maintained."""
    
    logger.info("🧪 Testing existing SerpAPI scraper functionality")
    
    # Sample SerpAPI response in the original format
    original_response = {
        'title': 'John Smith - CEO - TechCorp Inc | LinkedIn',
        'snippet': 'CEO at TechCorp Inc in Montreal, Quebec. Leading innovation in technology.',
        'link': 'https://linkedin.com/in/john-smith-ceo',
        'displayed_link': 'linkedin.com/in/john-smith-ceo'
        # No website field - this is the original format
    }
    
    try:
        # Initialize scraper
        try:
            scraper = SerpAPILeadScraper()
        except ValueError:
            scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
            scraper.serpapi_key = "test_key"
            scraper.search_location = "Montreal, Quebec, Canada"
            logger.info("🔧 Using mock scraper for testing")
        
        # Test lead extraction
        logger.info("📋 Testing lead extraction from original SerpAPI format")
        lead = scraper._extract_linkedin_lead(original_response)
        
        if lead:
            logger.info("✅ Lead extraction successful")
            logger.info(f"   Name: {lead['name']}")
            logger.info(f"   Title: {lead['title']}")
            logger.info(f"   Company: {lead['company']}")
            logger.info(f"   LinkedIn URL: {lead['linkedin_url']}")
            logger.info(f"   Website: {lead['website']}")
            logger.info(f"   Status: {lead['status']}")
            logger.info(f"   Scraped At: {lead['scraped_at']}")
            
            # Verify all expected fields are present
            required_fields = [
                'name', 'title', 'company', 'linkedin_url', 'location',
                'email', 'website', 'verified', 'enriched', 'scraped_at',
                'scraping_source', 'search_context', 'status'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in lead:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"⚠️ Missing fields: {missing_fields}")
            else:
                logger.info("✅ All required fields present")
            
            # Verify website field behavior
            if lead['website'] is None:
                logger.info("✅ Website field correctly set to None (will trigger Google fallback)")
            else:
                logger.info(f"✅ Website field set to: {lead['website']}")
            
            return True
            
        else:
            logger.error("❌ Lead extraction failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing code."""
    
    logger.info("\n🧪 Testing backward compatibility")
    
    try:
        # Test scraper initialization
        try:
            scraper = SerpAPILeadScraper()
            logger.info("✅ Scraper initialization successful")
        except ValueError:
            scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
            scraper.serpapi_key = "test_key"
            scraper.search_location = "Montreal, Quebec, Canada"
            scraper.search_queries = ['CEO', 'Founder', 'President']
            logger.info("✅ Mock scraper initialization successful")
        
        # Test that all original methods exist
        original_methods = [
            'search_montreal_ceos',
            'search_by_company_type',
            'validate_linkedin_profiles',
            '_build_search_queries',
            '_execute_serpapi_search',
            '_extract_linkedin_lead',
            '_extract_company_from_snippet',
            '_get_location_indicators'
        ]
        
        missing_methods = []
        for method in original_methods:
            if not hasattr(scraper, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.warning(f"⚠️ Missing methods: {missing_methods}")
            return False
        else:
            logger.info("✅ All original methods present")
        
        # Test that new methods exist
        new_methods = [
            '_extract_website_from_serpapi_result',
            '_extract_website_from_text',
            '_is_valid_website_url'
        ]
        
        missing_new_methods = []
        for method in new_methods:
            if not hasattr(scraper, method):
                missing_new_methods.append(method)
        
        if missing_new_methods:
            logger.warning(f"⚠️ Missing new methods: {missing_new_methods}")
            return False
        else:
            logger.info("✅ All new methods present")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backward compatibility test failed: {str(e)}")
        return False

def test_async_wrapper():
    """Test that async wrapper functions still work."""
    
    logger.info("\n🧪 Testing async wrapper functions")
    
    try:
        # Import async functions
        from scraper.serpapi_scraper import scrape_linkedin_leads_serpapi_sync
        
        logger.info("✅ Async wrapper import successful")
        
        # Test that the function exists and is callable
        if callable(scrape_linkedin_leads_serpapi_sync):
            logger.info("✅ Sync wrapper function is callable")
        else:
            logger.error("❌ Sync wrapper function is not callable")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Async wrapper test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting scraper functionality tests")
        logger.info("=" * 50)
        
        # Test 1: Existing functionality
        test1_passed = test_existing_functionality()
        
        # Test 2: Backward compatibility
        test2_passed = test_backward_compatibility()
        
        # Test 3: Async wrapper
        test3_passed = test_async_wrapper()
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 30)
        logger.info(f"Existing Functionality: {'✅ PASS' if test1_passed else '❌ FAIL'}")
        logger.info(f"Backward Compatibility: {'✅ PASS' if test2_passed else '❌ FAIL'}")
        logger.info(f"Async Wrapper: {'✅ PASS' if test3_passed else '❌ FAIL'}")
        
        if all([test1_passed, test2_passed, test3_passed]):
            logger.info("\n🎉 All functionality tests passed!")
            logger.info("✅ Enhanced website extraction maintains existing functionality")
        else:
            logger.error("\n❌ Some functionality tests failed!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)