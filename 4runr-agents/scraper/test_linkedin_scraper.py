#!/usr/bin/env python3
"""
Test script for LinkedIn scraper

This script tests the LinkedIn scraper functionality without running the full pipeline.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from linkedin_scraper import scrape_linkedin_leads

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_scraper():
    """Test the LinkedIn scraper"""
    print("Testing LinkedIn Scraper...")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = ['LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'SEARCH_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return
    
    print("✅ All required environment variables are set")
    print(f"📧 LinkedIn Email: {os.getenv('LINKEDIN_EMAIL')}")
    print(f"🔍 Search URL: {os.getenv('SEARCH_URL')}")
    print()
    
    try:
        # Run the scraper
        leads = await scrape_linkedin_leads()
        
        print(f"🎉 Successfully scraped {len(leads)} leads!")
        print()
        
        # Display the leads
        for i, lead in enumerate(leads, 1):
            print(f"Lead {i}:")
            print(f"  Name: {lead['name']}")
            print(f"  Title: {lead['title']}")
            print(f"  Company: {lead['company']}")
            print(f"  LinkedIn: {lead['linkedin_url']}")
            print()
        
        if leads:
            print("✅ LinkedIn scraper test completed successfully!")
        else:
            print("⚠️  No leads were scraped. Check your search URL and LinkedIn credentials.")
            
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scraper())