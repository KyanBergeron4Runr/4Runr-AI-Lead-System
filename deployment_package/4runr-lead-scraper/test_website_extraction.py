#!/usr/bin/env python3
"""
Test script for enhanced SerpAPI website extraction.

This script tests the improved website extraction functionality
to ensure it properly extracts website URLs from SerpAPI responses.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.serpapi_scraper import SerpAPILeadScraper

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('website-extraction-test')

def test_website_extraction():
    """Test the enhanced website extraction functionality."""
    
    logger.info("🧪 Testing enhanced SerpAPI website extraction")
    
    # Sample SerpAPI response data for testing
    test_results = [
        {
            'title': 'John Smith - CEO - TechCorp Inc | LinkedIn',
            'snippet': 'CEO at TechCorp Inc in Montreal, Quebec. Visit us at techcorp.com for innovative solutions.',
            'link': 'https://linkedin.com/in/john-smith-ceo',
            'website': 'https://techcorp.com',  # Direct website field
            'displayed_link': 'techcorp.com'
        },
        {
            'title': 'Jane Doe - Founder - StartupXYZ | LinkedIn',
            'snippet': 'Founder of StartupXYZ based in Montreal. We provide AI solutions. Contact us at hello@startupxyz.io',
            'link': 'https://linkedin.com/in/jane-doe-founder',
            'rich_snippet': {
                'top': {
                    'detected_extensions': {
                        'website': 'https://startupxyz.io'
                    }
                }
            }
        },
        {
            'title': 'Mike Johnson - President - LocalBiz | LinkedIn',
            'snippet': 'President of LocalBiz, a Montreal-based consulting firm. Website: localbiz.ca',
            'link': 'https://linkedin.com/in/mike-johnson-president',
            'sitelinks': [
                {'link': 'https://localbiz.ca/about'},
                {'link': 'https://localbiz.ca/services'}
            ]
        },
        {
            'title': 'Sarah Wilson - Director - NoWebsite Corp | LinkedIn',
            'snippet': 'Director at NoWebsite Corp. Leading innovation in Montreal.',
            'link': 'https://linkedin.com/in/sarah-wilson-director'
            # No website information available
        }
    ]
    
    try:
        # Initialize scraper (will use test mode if no API key)
        try:
            scraper = SerpAPILeadScraper()
        except ValueError:
            # Create a mock scraper for testing without API key
            scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
            scraper.serpapi_key = "test_key"
            scraper.search_location = "Montreal, Quebec, Canada"
            logger.info("🔧 Using mock scraper for testing (no API key required)")
        
        results = []
        
        for i, test_result in enumerate(test_results, 1):
            logger.info(f"\n🧪 Test Case {i}: {test_result['title']}")
            
            # Extract lead information
            lead = scraper._extract_linkedin_lead(test_result)
            
            if lead:
                website = lead.get('website')
                logger.info(f"✅ Lead extracted: {lead['name']}")
                logger.info(f"🏢 Company: {lead['company']}")
                logger.info(f"🌐 Website: {website if website else 'None (will trigger Google fallback)'}")
                
                results.append({
                    'name': lead['name'],
                    'company': lead['company'],
                    'website': website,
                    'website_found': website is not None
                })
            else:
                logger.warning(f"❌ Failed to extract lead from test case {i}")
                results.append({
                    'name': 'Failed',
                    'company': 'Failed',
                    'website': None,
                    'website_found': False
                })
        
        # Summary
        logger.info("\n📊 Website Extraction Test Results:")
        logger.info("=" * 50)
        
        websites_found = sum(1 for r in results if r['website_found'])
        total_tests = len(results)
        
        for i, result in enumerate(results, 1):
            status = "✅ Found" if result['website_found'] else "⚠️ None (fallback needed)"
            logger.info(f"{i}. {result['name']} - {status}")
            if result['website']:
                logger.info(f"   🌐 {result['website']}")
        
        logger.info(f"\n📈 Success Rate: {websites_found}/{total_tests} ({websites_found/total_tests*100:.1f}%)")
        
        # Test website extraction methods directly
        logger.info("\n🔍 Testing individual extraction methods:")
        
        # Test direct website field
        test_result_with_website = test_results[0]
        website = scraper._extract_website_from_serpapi_result(test_result_with_website)
        logger.info(f"Direct website field: {website}")
        
        # Test rich snippet extraction
        test_result_with_rich = test_results[1]
        website = scraper._extract_website_from_serpapi_result(test_result_with_rich)
        logger.info(f"Rich snippet extraction: {website}")
        
        # Test text extraction
        test_snippet = "Visit us at techsolutions.ca for more information about our services"
        website = scraper._extract_website_from_text(test_snippet)
        logger.info(f"Text extraction: {website}")
        
        logger.info("\n✅ Website extraction testing completed!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Website extraction test failed: {str(e)}")
        raise

def test_website_validation():
    """Test website URL validation."""
    
    logger.info("\n🧪 Testing website URL validation")
    
    test_urls = [
        "https://example.com",
        "http://test-company.ca",
        "https://www.startup.io",
        "invalid-url",
        "linkedin.com/company/test",  # Should be filtered out
        "https://techcorp.ai",
        ""
    ]
    
    try:
        scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
        
        for url in test_urls:
            is_valid = scraper._is_valid_website_url(url)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            logger.info(f"{status}: {url}")
        
        logger.info("✅ Website validation testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Website validation test failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Run website extraction tests
        results = test_website_extraction()
        
        # Run website validation tests
        test_website_validation()
        
        logger.info("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)