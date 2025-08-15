#!/usr/bin/env python3
"""
Test script for the Website Scraper Service functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.website_scraper_service import WebsiteScraperService


def test_website_scraper():
    """Test the Website Scraper Service functionality."""
    print("🧪 Testing Website Scraper Service...")
    
    # Test 1: Initialize scraper
    print("\n1. Testing scraper initialization...")
    try:
        scraper = WebsiteScraperService()
        print("   ✅ Scraper initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize scraper: {e}")
        return False
    
    # Test 2: Test basic capability
    print("\n2. Testing basic scraping capability...")
    try:
        can_scrape = scraper.test_scraping_capability()
        print(f"   {'✅' if can_scrape else '❌'} Basic scraping capability: {can_scrape}")
    except Exception as e:
        print(f"   ❌ Capability test failed: {e}")
    
    # Test 3: URL validation
    print("\n3. Testing URL validation...")
    test_urls = [
        ("google.com", "https://google.com"),
        ("https://example.com", "https://example.com"),
        ("http://test.com/path", "http://test.com/path"),
        ("invalid-url", None),
        ("", None)
    ]
    
    for input_url, expected in test_urls:
        result = scraper._validate_and_normalize_url(input_url)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{input_url}' -> '{result}' (expected: '{expected}')")
    
    # Test 4: Test with a simple website (using httpbin for reliable testing)
    print("\n4. Testing website scraping with httpbin...")
    try:
        result = scraper.scrape_company_website("https://httpbin.org/html", "HTTPBin Test Company")
        print(f"   ✅ Scraping completed: success={result['success']}")
        if result['success']:
            print(f"   📄 Summary: {result['summary'][:100]}...")
        else:
            print(f"   ⚠️  Error: {result['error']}")
    except Exception as e:
        print(f"   ❌ Scraping test failed: {e}")
    
    # Test 5: Test fallback functionality
    print("\n5. Testing fallback functionality...")
    try:
        fallback_result = scraper.scrape_company_website("https://invalid-domain-that-does-not-exist.com", "Test Company")
        print(f"   ✅ Fallback completed: {fallback_result['summary']}")
    except Exception as e:
        print(f"   ❌ Fallback test failed: {e}")
    
    # Test 6: Test convenience method
    print("\n6. Testing convenience method...")
    try:
        summary = scraper.scrape_with_fallback("https://httpbin.org/html", "HTTPBin")
        print(f"   ✅ Convenience method works: {summary[:100]}...")
    except Exception as e:
        print(f"   ❌ Convenience method failed: {e}")
    
    print("\n🎉 Website Scraper Service tests completed!")
    return True


if __name__ == '__main__':
    success = test_website_scraper()
    sys.exit(0 if success else 1)