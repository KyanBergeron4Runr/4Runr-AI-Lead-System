#!/usr/bin/env python3
"""
Unit Test for Website Extraction Logic

Test the website extraction methods with mock SerpAPI responses to verify
the logic works correctly when website data is present.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.serpapi_scraper import SerpAPILeadScraper

def test_website_extraction_logic():
    """Test website extraction logic with mock data."""
    print("🧪 Testing Website Extraction Logic")
    print("=" * 40)
    
    # Create scraper instance (without API key for unit testing)
    scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
    scraper.search_location = "Montreal, Quebec, Canada"
    
    # Test 1: Direct website field in SerpAPI response
    print("\n📋 Test 1: Direct website field")
    mock_result_1 = {
        'title': 'John Doe - CEO - Tech Company | LinkedIn',
        'snippet': 'CEO at Tech Company in Montreal',
        'link': 'https://linkedin.com/in/johndoe',
        'website': 'https://techcompany.com'
    }
    
    website = scraper._extract_website_from_serpapi_result(mock_result_1)
    print(f"   Result: {website}")
    assert website == 'https://techcompany.com', f"Expected https://techcompany.com, got {website}"
    print("   ✅ Direct website field extraction works")
    
    # Test 2: Website in rich snippet
    print("\n📋 Test 2: Website in rich snippet")
    mock_result_2 = {
        'title': 'Jane Smith - Founder - StartupCo | LinkedIn',
        'snippet': 'Founder at StartupCo',
        'link': 'https://linkedin.com/in/janesmith',
        'rich_snippet': {
            'top': {
                'detected_extensions': {
                    'website': 'https://startupco.ca'
                }
            }
        }
    }
    
    website = scraper._extract_website_from_serpapi_result(mock_result_2)
    print(f"   Result: {website}")
    assert website == 'https://startupco.ca', f"Expected https://startupco.ca, got {website}"
    print("   ✅ Rich snippet website extraction works")
    
    # Test 3: Website in snippet text
    print("\n📋 Test 3: Website in snippet text")
    mock_result_3 = {
        'title': 'Bob Wilson - President - InnovateInc | LinkedIn',
        'snippet': 'President at InnovateInc. Visit us at innovateinc.com for more information.',
        'link': 'https://linkedin.com/in/bobwilson'
    }
    
    website = scraper._extract_website_from_serpapi_result(mock_result_3)
    print(f"   Result: {website}")
    assert website == 'https://innovateinc.com', f"Expected https://innovateinc.com, got {website}"
    print("   ✅ Snippet text website extraction works")
    
    # Test 4: No website found
    print("\n📋 Test 4: No website found")
    mock_result_4 = {
        'title': 'Alice Brown - Director - LocalBiz | LinkedIn',
        'snippet': 'Director at LocalBiz in Montreal',
        'link': 'https://linkedin.com/in/alicebrown'
    }
    
    website = scraper._extract_website_from_serpapi_result(mock_result_4)
    print(f"   Result: {website}")
    assert website is None, f"Expected None, got {website}"
    print("   ✅ No website case handled correctly")
    
    # Test 5: Test full lead extraction with website
    print("\n📋 Test 5: Full lead extraction with website")
    mock_result_5 = {
        'title': 'Sarah Johnson - CEO - TechSolutions | LinkedIn',
        'snippet': 'CEO at TechSolutions in Montreal, Quebec, Canada. Leading innovation in tech.',
        'link': 'https://linkedin.com/in/sarahjohnson',
        'website': 'https://techsolutions.ca'
    }
    
    lead = scraper._extract_linkedin_lead(mock_result_5)
    print(f"   Lead: {lead['name']} - {lead['title']} at {lead['company']}")
    print(f"   Website: {lead['website']}")
    assert lead['website'] == 'https://techsolutions.ca', f"Expected https://techsolutions.ca, got {lead['website']}"
    print("   ✅ Full lead extraction with website works")
    
    print("\n🎉 All website extraction tests passed!")
    return True

def test_website_validation():
    """Test website URL validation logic."""
    print("\n🔍 Testing Website URL Validation")
    print("=" * 40)
    
    scraper = SerpAPILeadScraper.__new__(SerpAPILeadScraper)
    
    # Valid URLs
    valid_urls = [
        'https://example.com',
        'http://test.ca',
        'https://www.company.org',
        'https://startup.io'
    ]
    
    for url in valid_urls:
        result = scraper._is_valid_website_url(url)
        print(f"   {url}: {'✅' if result else '❌'}")
        assert result, f"Expected {url} to be valid"
    
    # Invalid URLs
    invalid_urls = [
        '',
        None,
        'not-a-url',
        'ftp://example.com',
        'javascript:alert(1)'
    ]
    
    for url in invalid_urls:
        result = scraper._is_valid_website_url(url)
        print(f"   {url}: {'❌' if not result else '✅'}")
        assert not result, f"Expected {url} to be invalid"
    
    print("   ✅ Website URL validation works correctly")
    return True

def main():
    """Run all unit tests."""
    print("🚀 Starting Website Extraction Unit Tests")
    print("=" * 50)
    
    try:
        test_website_extraction_logic()
        test_website_validation()
        
        print("\n" + "=" * 50)
        print("✅ All unit tests passed!")
        print("\n📋 Summary:")
        print("- Website extraction from direct field works")
        print("- Website extraction from rich snippets works")
        print("- Website extraction from snippet text works")
        print("- No website case handled correctly")
        print("- Full lead extraction with website works")
        print("- Website URL validation works correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Unit test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)