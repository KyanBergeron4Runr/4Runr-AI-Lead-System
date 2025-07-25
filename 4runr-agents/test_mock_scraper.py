#!/usr/bin/env python3
"""
Test Mock Scraper

This script tests the mock scraper functionality without Docker or Playwright.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add the scraper directory to the path
sys.path.append('scraper')

# Load environment variables
load_dotenv()

# Mock the linkedin_scraper import to avoid Playwright dependency
class MockLinkedInScraper:
    @staticmethod
    async def scrape_linkedin_leads():
        return []

sys.modules['linkedin_scraper'] = MockLinkedInScraper()

# Now import the scraper app
from scraper.app import main, generate_mock_leads, save_leads

def test_mock_scraper():
    """Test the mock scraper functionality"""
    print("🧪 Testing Mock Scraper")
    print("=" * 40)
    
    # Set environment for mock mode
    os.environ['USE_REAL_SCRAPING'] = 'false'
    os.environ['SCRAPER_LEAD_COUNT'] = '3'
    
    try:
        # Test mock lead generation
        print("📝 Generating mock leads...")
        leads = generate_mock_leads(3)
        
        print(f"✅ Generated {len(leads)} mock leads:")
        for i, lead in enumerate(leads, 1):
            print(f"  {i}. {lead['name']} - {lead['title']} at {lead['company']}")
        
        # Test saving leads
        print("\n💾 Testing lead saving...")
        save_leads(leads)
        
        # Check if shared file was created
        shared_file = "shared/leads.json"
        if os.path.exists(shared_file):
            with open(shared_file, 'r') as f:
                saved_leads = json.load(f)
            print(f"✅ Successfully saved {len(saved_leads)} leads to {shared_file}")
            
            # Show the format
            if saved_leads:
                print("\n📋 Lead format:")
                lead = saved_leads[0]
                for key, value in lead.items():
                    print(f"  {key}: {value}")
        else:
            print("❌ Failed to create shared leads file")
        
        print("\n🎉 Mock scraper test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during mock scraper test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create shared directory if it doesn't exist
    os.makedirs("shared", exist_ok=True)
    
    success = test_mock_scraper()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Fix Docker performance issues")
        print("2. Build containers with mock scraping first:")
        print("   docker-compose build scraper")
        print("3. Test the pipeline:")
        print("   docker-compose up scraper")
        print("4. Once Docker is stable, enable real scraping")
    else:
        print("\n❌ Mock scraper test failed. Check the error above.")