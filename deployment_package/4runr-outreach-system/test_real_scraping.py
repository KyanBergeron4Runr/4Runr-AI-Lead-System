#!/usr/bin/env python3
"""
Test real website scraping with a reliable site.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.website_scraper_service import WebsiteScraperService


def test_real_scraping():
    """Test scraping with a real, reliable website."""
    print("🧪 Testing real website scraping...")
    
    scraper = WebsiteScraperService()
    
    # Test with example.com (very reliable)
    print("\n1. Testing with example.com...")
    try:
        result = scraper.scrape_company_website("https://example.com", "Example Company")
        print(f"   Success: {result['success']}")
        print(f"   Summary: {result['summary']}")
        if result['raw_content']:
            print(f"   Content preview: {result['raw_content'][:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test URL validation fix
    print("\n2. Testing improved URL validation...")
    test_cases = [
        ("invalid-url", None),
        ("google.com", "https://google.com"),
        ("just-text", None)
    ]
    
    for input_url, expected in test_cases:
        result = scraper._validate_and_normalize_url(input_url)
        expected_result = expected is not None
        actual_result = result is not None
        status = "✅" if expected_result == actual_result else "❌"
        print(f"   {status} '{input_url}' -> valid: {actual_result} (expected: {expected_result})")


if __name__ == '__main__':
    test_real_scraping()