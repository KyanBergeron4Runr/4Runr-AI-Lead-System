#!/usr/bin/env python3
"""Test SerpAPI website extraction functionality"""

import sys
sys.path.append('4runr-lead-scraper')

from scraper.serpapi_scraper import SerpAPILeadScraper

def test_serpapi_website_extraction():
    """Test the SerpAPI scraper with website extraction"""
    try:
        scraper = SerpAPILeadScraper()
        print('✅ SerpAPI scraper initialized')
        
        # Test with a small search
        leads = scraper.search_montreal_ceos(max_results=2)
        
        print(f'📊 Found {len(leads)} leads')
        for i, lead in enumerate(leads, 1):
            print(f'\n{i}. {lead["name"]} - {lead["title"]}')
            print(f'   Company: {lead["company"]}')
            print(f'   LinkedIn: {lead["linkedin_url"]}')
            website = lead.get('website', 'None - will trigger Google fallback')
            print(f'   Website: {website}')
            
        return leads
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return []

if __name__ == "__main__":
    test_serpapi_website_extraction()