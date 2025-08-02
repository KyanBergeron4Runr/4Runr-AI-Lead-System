#!/usr/bin/env python3
"""
Test script for the upgraded stealth LinkedIn scraper
Tests with known LinkedIn profiles to validate functionality
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('stealth-scraper-test')

# Test profiles - known Montreal executives
TEST_PROFILES = [
    {
        "name": "Tobias Lütke",
        "linkedin_url": "https://www.linkedin.com/in/tobi/",
        "company": "Shopify",
        "title": "CEO"
    },
    {
        "name": "Dax Dasilva", 
        "linkedin_url": "https://www.linkedin.com/in/daxdasilva/",
        "company": "Lightspeed Commerce",
        "title": "CEO"
    },
    {
        "name": "Alexandre Taillefer",
        "linkedin_url": "https://www.linkedin.com/in/alexandretaillefer/",
        "company": "XPND Capital",
        "title": "CEO"
    }
]

def create_test_raw_leads():
    """Create test raw_leads.json with known profiles"""
    shared_dir = Path(__file__).parent / "shared"
    shared_dir.mkdir(exist_ok=True)
    
    raw_leads = []
    for profile in TEST_PROFILES:
        raw_lead = {
            "uuid": f"test-{profile['name'].lower().replace(' ', '-')}",
            "full_name": profile["name"],
            "linkedin_url": profile["linkedin_url"],
            "email": None,
            "verified": False,
            "enriched": False,
            "engagement_method": None,
            "scraped_at": datetime.now().isoformat(),
            "source": "Test Data - Known Profiles"
        }
        raw_leads.append(raw_lead)
    
    raw_leads_file = shared_dir / "raw_leads.json"
    with open(raw_leads_file, 'w') as f:
        json.dump(raw_leads, f, indent=2)
    
    logger.info(f"✅ Created test raw_leads.json with {len(raw_leads)} known profiles")
    return raw_leads_file

async def test_production_scraper():
    """Test the production scraper with real LinkedIn search"""
    try:
        # Import the upgraded scraper
        from scraper.production_linkedin_scraper import scrape_real_linkedin_leads
        
        logger.info("🚀 Testing upgraded production LinkedIn scraper...")
        
        # Set test environment variables
        os.environ['MAX_LEADS_PER_RUN'] = '3'
        os.environ['LINKEDIN_SEARCH_QUERY'] = 'CEO Montreal'
        os.environ['HEADLESS'] = 'false'  # Show browser for testing
        
        # Run the scraper
        leads = await scrape_real_linkedin_leads()
        
        if leads:
            logger.info(f"✅ SUCCESS: Scraped {len(leads)} real LinkedIn profiles")
            
            # Log details of scraped leads
            for i, lead in enumerate(leads, 1):
                logger.info(f"   {i}. {lead['name']} - {lead['title']} at {lead['company']}")
                logger.info(f"      🔗 {lead['linkedin_url']}")
                logger.info(f"      📍 {lead.get('location', 'N/A')}")
            
            return True
        else:
            logger.error("❌ FAILED: No leads scraped")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

def test_scraper_integration():
    """Test the full scraper integration"""
    try:
        # Import main scraper
        import sys
        sys.path.append(str(Path(__file__).parent / "scraper"))
        
        from scraper.app import main as scraper_main
        
        logger.info("🧪 Testing full scraper integration...")
        
        # Set environment for single run
        os.environ['RUN_ONCE'] = 'true'
        os.environ['MAX_LEADS_PER_RUN'] = '3'
        
        # Run the scraper
        scraper_main()
        
        # Check if raw_leads.json was created
        shared_dir = Path(__file__).parent / "shared"
        raw_leads_file = shared_dir / "raw_leads.json"
        
        if raw_leads_file.exists():
            with open(raw_leads_file, 'r') as f:
                leads = json.load(f)
            
            logger.info(f"✅ Integration test SUCCESS: {len(leads)} leads in raw_leads.json")
            
            # Validate lead format
            for lead in leads[:3]:
                required_fields = ['uuid', 'full_name', 'linkedin_url', 'scraped_at']
                missing_fields = [field for field in required_fields if field not in lead]
                
                if missing_fields:
                    logger.error(f"❌ Lead missing fields: {missing_fields}")
                    return False
                else:
                    logger.info(f"   ✅ {lead['full_name']} - Valid format")
            
            return True
        else:
            logger.error("❌ Integration test FAILED: No raw_leads.json created")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🧪 Starting Stealth LinkedIn Scraper Tests")
    logger.info("=" * 60)
    
    # Test 1: Create test data
    logger.info("\n📋 Test 1: Creating test raw leads...")
    create_test_raw_leads()
    
    # Test 2: Test production scraper directly
    logger.info("\n🚀 Test 2: Testing production scraper...")
    production_success = await test_production_scraper()
    
    # Test 3: Test full integration
    logger.info("\n🔗 Test 3: Testing scraper integration...")
    integration_success = test_scraper_integration()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 TEST SUMMARY:")
    logger.info(f"   Production Scraper: {'✅ PASS' if production_success else '❌ FAIL'}")
    logger.info(f"   Integration Test:   {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if production_success and integration_success:
        logger.info("🎉 ALL TESTS PASSED - Stealth scraper is working!")
    else:
        logger.error("❌ SOME TESTS FAILED - Check logs above")
    
    logger.info("\n💡 Next steps:")
    logger.info("   1. Check shared/raw_leads.json for scraped data")
    logger.info("   2. Run: python pipeline_cli.py verifier")
    logger.info("   3. Run: python pipeline_cli.py enricher") 
    logger.info("   4. Run: python pipeline_cli.py engager")

if __name__ == "__main__":
    asyncio.run(main())