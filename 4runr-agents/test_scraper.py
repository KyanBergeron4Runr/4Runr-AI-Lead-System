#!/usr/bin/env python3
"""
Test script for LinkedIn scraper
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test environment variables
print("Environment variables:")
print(f"LINKEDIN_EMAIL: {os.getenv('LINKEDIN_EMAIL')}")
print(f"LINKEDIN_PASSWORD: {'*' * len(os.getenv('LINKEDIN_PASSWORD', '')) if os.getenv('LINKEDIN_PASSWORD') else 'Not set'}")
print(f"SEARCH_URL: {os.getenv('SEARCH_URL')}")
print(f"APIFY_TOKEN: {'*' * 10 if os.getenv('APIFY_TOKEN') else 'Not set'}")

# Test the scraper
try:
    from scraper.linkedin_scraper import scrape_linkedin_leads
    print("\nTesting LinkedIn scraper...")
    leads = asyncio.run(scrape_linkedin_leads())
    print(f"Got {len(leads)} leads")
    for lead in leads[:3]:  # Show first 3
        print(f"- {lead['name']} from {lead['company']}")
except Exception as e:
    print(f"LinkedIn scraper failed: {e}")

# Test simple scraper as fallback
try:
    from scraper.simple_linkedin_scraper import scrape_linkedin_leads_simple
    print("\nTesting simple scraper...")
    leads = asyncio.run(scrape_linkedin_leads_simple())
    print(f"Got {len(leads)} leads")
    for lead in leads[:3]:  # Show first 3
        print(f"- {lead['name']} from {lead['company']}")
except Exception as e:
    print(f"Simple scraper failed: {e}")