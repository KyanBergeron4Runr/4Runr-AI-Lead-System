#!/usr/bin/env python3
"""
Simple Scraper Test

Test the scraper with proper environment loading
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment from parent directory
parent_dir = Path(__file__).parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

print("🧪 Testing Scraper with Environment Variables")
print("=" * 50)

# Check environment variables
required_vars = ['LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'SEARCH_URL']
print("Environment Variables:")
for var in required_vars:
    value = os.getenv(var)
    has_value = bool(value and value.strip())
    print(f"  {var}: {'✅ Set' if has_value else '❌ Missing'}")

print()

if all(os.getenv(var) for var in required_vars):
    print("🚀 All required variables present. Testing scraper...")
    
    # Import and test the scraper
    sys.path.append(str(parent_dir / 'scraper'))
    
    try:
        from linkedin_scraper import scrape_linkedin_leads
        
        print("📡 Running LinkedIn scraper...")
        leads = asyncio.run(scrape_linkedin_leads())
        
        print(f"✅ Scraper completed successfully!")
        print(f"📊 Results: {len(leads)} leads scraped")
        
        if leads:
            print("\n📋 Sample leads:")
            for i, lead in enumerate(leads[:3], 1):
                print(f"  {i}. {lead.get('name', 'Unknown')} - {lead.get('company', 'Unknown Company')}")
        
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("❌ Missing required environment variables. Cannot test scraper.")
    print("Please check your .env file.")