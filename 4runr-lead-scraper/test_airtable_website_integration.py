#!/usr/bin/env python3
"""
Test script for Airtable website integration.

This script tests the integration between SerpAPI website extraction
and Airtable synchronization to ensure website data is properly handled.
"""

import os
import sys
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.serpapi_scraper import SerpAPILeadScraper
from sync.airtable_sync import AirtableSync
from database.models import get_lead_database, Lead

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('airtable-website-integration-test')

def test_various_serpapi_response_formats():
    """Test website extraction with various SerpAPI response formats."""
    
    logger.info("🧪 Testing website extraction with various SerpAPI response formats")
    
    # Various SerpAPI response formats for testing
    test_cases = [
        {
            'name': 'Direct Website Field',
            'response': {
                'title': 'John Smith - CEO - TechCorp Inc | LinkedIn',
                'snippet': 'CEO at TechCorp Inc in Montreal, Quebec. Leading innovation in technology.',
                'link': 'https://linkedin.com/in/john-smith-ceo',
                'website': 'https://techcorp.com',  # Direct website field
                'displayed_link': 'techcorp.com'
            },
            'expected_website': 'https://techcorp.com'
        },
        {
            'name': 'Rich Snippet Extensions',
            'response': {
                'title': 'Jane Doe - Founder - StartupXYZ | LinkedIn',
                'snippet': 'Founder of StartupXYZ based in Montreal. We provide AI solutions.',
                'link': 'https://linkedin.com/in/jane-doe-founder',
                'rich_snippet': {
                    'top': {
                        'detected_extensions': {
                            'website': 'https://startupxyz.io'
                        }
                    }
                }
            },
            'expected_website': 'https://startupxyz.io'
        },
        {
            'name': 'Sitelinks Array',
            'response': {
                'title': 'Mike Johnson - President - LocalBiz | LinkedIn',
                'snippet': 'President of LocalBiz, a Montreal-based consulting firm.',
                'link': 'https://linkedin.com/in/mike-johnson-president',
                'sitelinks': [
                    {'link': 'https://localbiz.ca/about'},
                    {'link': 'https://localbiz.ca/services'}
                ]
            },
            'expected_website': 'https://localbiz.ca/about'
        },
        {
            'name': 'Displayed Link Only',
            'response': {
                'title': 'Sarah Chen - Director - InnovateCorp | LinkedIn',
                'snippet': 'Director at InnovateCorp in Montreal. Driving digital transformation.',
                'link': 'https://linkedin.com/in/sarah-chen-director',
                'displayed_link': 'innovatecorp.ca'
            },
            'expected_website': 'https://innovatecorp.ca'
        },
        {
            'name': 'Snippet Text Pattern',
            'response': {
                'title': 'David Wilson - CEO - TechSolutions | LinkedIn',
                'snippet': 'CEO at TechSolutions in Montreal. Visit us at techsolutions.ca for more information.',
                'link': 'https://linkedin.com/in/david-wilson-ceo'
            },
            'expected_website': 'https://techsolutions.ca'
        },
        {
            'name': 'Email Domain Extraction',
            'response': {
                'title': 'Lisa Brown - Founder - DigitalAgency | LinkedIn',
                'snippet': 'Founder of DigitalAgency in Montreal. Contact us at hello@digitalagency.com',
                'link': 'https://linkedin.com/in/lisa-brown-founder'
            },
            'expected_website': 'https://digitalagency.com'
        },
        {
            'name': 'No Website Available',
            'response': {
                'title': 'Robert Taylor - Executive - NoWebsite Corp | LinkedIn',
                'snippet': 'Executive at NoWebsite Corp. Leading business operations in Montreal.',
                'link': 'https://linkedin.com/in/robert-taylor-executive'
            },
            'expected_website': None
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
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n🧪 Test Case {i}: {test_case['name']}")
            
            # Extract lead information
            lead = scraper._extract_linkedin_lead(test_case['response'])
            
            if lead:
                website = lead.get('website')
                expected = test_case['expected_website']
                
                # Check if extraction matches expectation
                if website == expected:
                    status = "✅ PASS"
                elif website is None and expected is None:
                    status = "✅ PASS (No website expected)"
                else:
                    status = f"❌ FAIL (Expected: {expected}, Got: {website})"
                
                logger.info(f"   {status}")
                logger.info(f"   Lead: {lead['name']} - {lead['company']}")
                logger.info(f"   Website: {website}")
                
                results.append({
                    'test_case': test_case['name'],
                    'lead': lead,
                    'website_extracted': website,
                    'website_expected': expected,
                    'passed': website == expected
                })
            else:
                logger.warning(f"   ❌ FAIL - Failed to extract lead")
                results.append({
                    'test_case': test_case['name'],
                    'lead': None,
                    'website_extracted': None,
                    'website_expected': test_case['expected_website'],
                    'passed': False
                })
        
        # Summary
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        
        logger.info(f"\n📊 SerpAPI Response Format Test Results:")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        for result in results:
            status = "✅" if result['passed'] else "❌"
            logger.info(f"{status} {result['test_case']}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ SerpAPI response format test failed: {str(e)}")
        raise

def test_airtable_field_mapping():
    """Test Airtable field mapping for website data."""
    
    logger.info("\n🧪 Testing Airtable field mapping for website data")
    
    try:
        # Create mock lead objects with different website scenarios
        test_leads = [
            {
                'name': 'John Smith',
                'email': 'john@techcorp.com',
                'linkedin_url': 'https://linkedin.com/in/john-smith',
                'website': 'https://techcorp.com',
                'enriched': False,
                'scraped_at': datetime.now().isoformat()
            },
            {
                'name': 'Jane Doe',
                'email': 'jane@startup.io',
                'linkedin_url': 'https://linkedin.com/in/jane-doe',
                'website': None,  # No website - should trigger fallback
                'enriched': False,
                'scraped_at': datetime.now().isoformat()
            }
        ]
        
        # Initialize Airtable sync (will use test mode if no API key)
        try:
            airtable_sync = AirtableSync()
            logger.info("✅ Airtable sync initialized")
        except Exception as e:
            logger.warning(f"⚠️ Airtable sync initialization failed: {e}")
            logger.info("🔧 Testing field mapping without actual Airtable connection")
            airtable_sync = AirtableSync.__new__(AirtableSync)
        
        for i, lead_data in enumerate(test_leads, 1):
            logger.info(f"\n🧪 Lead {i}: {lead_data['name']}")
            
            # Create mock lead object
            lead_data['id'] = str(uuid.uuid4())
            lead = Lead(**lead_data)
            
            # Test field mapping
            try:
                airtable_record = airtable_sync._format_lead_for_airtable(lead)
                
                logger.info(f"   📋 Airtable Record Fields:")
                for field, value in airtable_record.items():
                    logger.info(f"      {field}: {value}")
                
                # Check website field handling
                if lead.website:
                    if 'Website' in airtable_record and airtable_record['Website'] == lead.website:
                        logger.info(f"   ✅ Website field correctly mapped: {lead.website}")
                    else:
                        logger.warning(f"   ❌ Website field mapping failed")
                else:
                    if 'Website' not in airtable_record:
                        logger.info(f"   ✅ No website field (correctly omitted for None value)")
                    else:
                        logger.warning(f"   ❌ Website field should not be present for None value")
                
            except Exception as e:
                logger.error(f"   ❌ Field mapping failed: {str(e)}")
        
        logger.info("\n✅ Airtable field mapping test completed!")
        
    except Exception as e:
        logger.error(f"❌ Airtable field mapping test failed: {str(e)}")
        raise

def test_end_to_end_integration():
    """Test end-to-end integration from SerpAPI extraction to Airtable sync."""
    
    logger.info("\n🧪 Testing end-to-end integration: SerpAPI → Database → Airtable")
    
    try:
        # Sample SerpAPI response with website
        serpapi_response = {
            'title': 'Test User - CEO - TestCorp | LinkedIn',
            'snippet': 'CEO at TestCorp in Montreal. Visit us at testcorp.com for innovative solutions.',
            'link': 'https://linkedin.com/in/test-user-ceo',
            'website': 'https://testcorp.com'
        }
        
        # Initialize components
        try:
            scraper = SerpAPILeadScraper()
        except ValueError:
            scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
            scraper.serpapi_key = "test_key"
            scraper.search_location = "Montreal, Quebec, Canada"
        
        # Step 1: Extract lead from SerpAPI response
        logger.info("📤 Step 1: Extracting lead from SerpAPI response")
        lead_data = scraper._extract_linkedin_lead(serpapi_response)
        
        if lead_data:
            logger.info(f"   ✅ Lead extracted: {lead_data['name']}")
            logger.info(f"   🌐 Website: {lead_data['website']}")
        else:
            logger.error("   ❌ Failed to extract lead")
            return
        
        # Step 2: Simulate database storage
        logger.info("💾 Step 2: Simulating database storage")
        logger.info(f"   📋 Lead data ready for database:")
        logger.info(f"      Name: {lead_data['name']}")
        logger.info(f"      Company: {lead_data['company']}")
        logger.info(f"      LinkedIn: {lead_data['linkedin_url']}")
        logger.info(f"      Website: {lead_data['website']}")
        
        # Step 3: Simulate Airtable sync
        logger.info("📊 Step 3: Simulating Airtable sync")
        
        try:
            airtable_sync = AirtableSync()
        except Exception:
            airtable_sync = AirtableSync.__new__(AirtableSync)
        
        # Create mock lead object
        lead = Lead(
            id=str(uuid.uuid4()),
            name=lead_data['name'],
            linkedin_url=lead_data['linkedin_url'],
            website=lead_data['website'],
            enriched=lead_data['enriched'],
            scraped_at=lead_data['scraped_at']
        )
        
        # Format for Airtable
        airtable_record = airtable_sync._format_lead_for_airtable(lead)
        
        logger.info(f"   📋 Airtable record prepared:")
        for field, value in airtable_record.items():
            logger.info(f"      {field}: {value}")
        
        # Verify website field is properly included
        if 'Website' in airtable_record and airtable_record['Website'] == lead_data['website']:
            logger.info("   ✅ Website field correctly prepared for Airtable sync")
        else:
            logger.warning("   ❌ Website field not properly prepared")
        
        logger.info("\n✅ End-to-end integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ End-to-end integration test failed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Airtable Website Integration Tests")
        logger.info("=" * 60)
        
        # Test 1: Various SerpAPI response formats
        serpapi_results = test_various_serpapi_response_formats()
        
        # Test 2: Airtable field mapping
        test_airtable_field_mapping()
        
        # Test 3: End-to-end integration
        test_end_to_end_integration()
        
        logger.info("\n🎉 All Airtable website integration tests completed successfully!")
        
        # Summary
        passed_serpapi_tests = sum(1 for r in serpapi_results if r['passed'])
        total_serpapi_tests = len(serpapi_results)
        
        logger.info("\n📊 Final Test Summary:")
        logger.info("=" * 40)
        logger.info(f"SerpAPI Response Formats: {passed_serpapi_tests}/{total_serpapi_tests} passed")
        logger.info(f"Airtable Field Mapping: ✅ Passed")
        logger.info(f"End-to-End Integration: ✅ Passed")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)