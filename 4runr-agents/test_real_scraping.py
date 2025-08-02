#!/usr/bin/env python3
"""
Test script to diagnose real LinkedIn scraping issues
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scraper-test')

def test_environment():
    """Test environment variables"""
    print("=== ENVIRONMENT CHECK ===")
    print(f"LINKEDIN_EMAIL: {os.getenv('LINKEDIN_EMAIL', 'NOT SET')}")
    print(f"LINKEDIN_PASSWORD: {'SET' if os.getenv('LINKEDIN_PASSWORD') else 'NOT SET'}")
    print(f"SEARCH_URL: {os.getenv('SEARCH_URL', 'NOT SET')}")
    print(f"APIFY_TOKEN: {'SET' if os.getenv('APIFY_TOKEN') else 'NOT SET'}")
    print(f"USE_REAL_SCRAPING: {os.getenv('USE_REAL_SCRAPING', 'NOT SET')}")
    print()

async def test_playwright_scraper():
    """Test Playwright LinkedIn scraper"""
    print("=== TESTING PLAYWRIGHT SCRAPER ===")
    try:
        from scraper.linkedin_scraper import scrape_linkedin_leads
        logger.info("Playwright scraper imported successfully")
        
        # Test the scraper
        leads = await scrape_linkedin_leads()
        print(f"Playwright scraper returned {len(leads)} leads")
        
        if leads:
            print("Sample lead:")
            print(f"  Name: {leads[0].get('name', 'N/A')}")
            print(f"  Title: {leads[0].get('title', 'N/A')}")
            print(f"  Company: {leads[0].get('company', 'N/A')}")
            print(f"  LinkedIn URL: {leads[0].get('linkedin_url', 'N/A')}")
        
        return leads
        
    except ImportError as e:
        logger.error(f"Failed to import Playwright scraper: {e}")
        return []
    except Exception as e:
        logger.error(f"Playwright scraper failed: {e}")
        return []

async def test_apify_scraper():
    """Test Apify LinkedIn scraper"""
    print("\n=== TESTING APIFY SCRAPER ===")
    try:
        from scraper.apify_linkedin_scraper import scrape_linkedin_leads_apify
        logger.info("Apify scraper imported successfully")
        
        # Test the scraper
        leads = await scrape_linkedin_leads_apify()
        print(f"Apify scraper returned {len(leads)} leads")
        
        if leads:
            print("Sample lead:")
            print(f"  Name: {leads[0].get('name', 'N/A')}")
            print(f"  Title: {leads[0].get('title', 'N/A')}")
            print(f"  Company: {leads[0].get('company', 'N/A')}")
            print(f"  LinkedIn URL: {leads[0].get('linkedin_url', 'N/A')}")
        
        return leads
        
    except ImportError as e:
        logger.error(f"Failed to import Apify scraper: {e}")
        return []
    except Exception as e:
        logger.error(f"Apify scraper failed: {e}")
        return []

async def test_simple_scraper():
    """Test Simple LinkedIn scraper"""
    print("\n=== TESTING SIMPLE SCRAPER ===")
    try:
        from scraper.simple_linkedin_scraper import scrape_linkedin_leads_simple
        logger.info("Simple scraper imported successfully")
        
        # Test the scraper
        leads = await scrape_linkedin_leads_simple()
        print(f"Simple scraper returned {len(leads)} leads")
        
        if leads:
            print("Sample lead:")
            print(f"  Name: {leads[0].get('name', 'N/A')}")
            print(f"  Title: {leads[0].get('title', 'N/A')}")
            print(f"  Company: {leads[0].get('company', 'N/A')}")
            print(f"  LinkedIn URL: {leads[0].get('linkedin_url', 'N/A')}")
        
        return leads
        
    except ImportError as e:
        logger.error(f"Failed to import Simple scraper: {e}")
        return []
    except Exception as e:
        logger.error(f"Simple scraper failed: {e}")
        return []

def validate_linkedin_urls(leads):
    """Validate if LinkedIn URLs are real"""
    print("\n=== VALIDATING LINKEDIN URLS ===")
    import requests
    
    for i, lead in enumerate(leads[:3]):  # Test first 3 leads
        url = lead.get('linkedin_url', '')
        if url:
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                status = "VALID" if response.status_code == 200 else f"INVALID ({response.status_code})"
                print(f"  {lead['name']}: {url} - {status}")
            except Exception as e:
                print(f"  {lead['name']}: {url} - ERROR ({str(e)})")
        else:
            print(f"  {lead['name']}: NO URL")

async def main():
    """Main test function"""
    test_environment()
    
    # Test all scrapers
    playwright_leads = await test_playwright_scraper()
    apify_leads = await test_apify_scraper()
    simple_leads = await test_simple_scraper()
    
    # Validate URLs if we have leads
    if simple_leads:
        validate_linkedin_urls(simple_leads)
    
    print("\n=== SUMMARY ===")
    print(f"Playwright leads: {len(playwright_leads)}")
    print(f"Apify leads: {len(apify_leads)}")
    print(f"Simple leads: {len(simple_leads)}")
    
    # Determine what's actually working
    if len(playwright_leads) > 0:
        print("✅ Playwright scraper is working")
    else:
        print("❌ Playwright scraper is not working")
    
    if len(apify_leads) > 0:
        print("✅ Apify scraper is working")
    else:
        print("❌ Apify scraper is not working")
    
    if len(simple_leads) > 0:
        print("⚠️  Simple scraper is working (but generating mock data)")
    else:
        print("❌ Simple scraper is not working")

if __name__ == "__main__":
    asyncio.run(main())