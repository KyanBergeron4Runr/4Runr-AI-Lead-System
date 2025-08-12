#!/usr/bin/env python3
"""
Simple test for the Website Scraper components without complex dependencies.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration():
    """Test configuration loading."""
    print("⚙️  Testing Configuration...")
    
    try:
        import sys
        sys.path.append('4runr-outreach-system')
        from shared.config import config
        
        # Test configuration access
        airtable_config = config.get_airtable_config()
        scraping_config = config.get_scraping_config()
        
        print(f"✅ Airtable configured: {bool(airtable_config.get('api_key'))}")
        print(f"✅ Scraping delay: {scraping_config['delay']}s")
        print(f"✅ Max retries: {scraping_config['max_retries']}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return False


def test_content_analyzer():
    """Test the content analyzer with sample content."""
    print("\n🧠 Testing Content Analyzer...")
    
    try:
        import sys
        sys.path.append('4runr-outreach-system')
        from website_scraper.content_analyzer import ContentAnalyzer
        
        # Sample scraped data
        sample_data = {
            'success': True,
            'raw_content': """
            About Us
            
            We are a leading technology consulting company that helps businesses transform 
            their operations through innovative digital solutions. Founded in 2015, our 
            team of experienced professionals specializes in software development, 
            cloud migration, and digital strategy.
            
            Our Services
            
            • Custom Software Development
            • Cloud Infrastructure Setup
            • Digital Transformation Consulting
            • Data Analytics Solutions
            • Cybersecurity Assessment
            
            We provide comprehensive, professional solutions that drive real business results.
            Our innovative approach combines cutting-edge technology with strategic thinking
            to deliver exceptional value to our clients.
            """,
            'website_insights': {
                '/about': 'We are a leading technology consulting company...',
                '/services': 'Custom Software Development, Cloud Infrastructure...'
            }
        }
        
        analyzer = ContentAnalyzer()
        result = analyzer.analyze_content(sample_data, 'test_lead')
        
        print(f"✅ Company Description: {result['company_description'][:100]}...")
        print(f"✅ Top Services: {result['top_services']}")
        print(f"✅ Detected Tone: {result['tone']}")
        print(f"✅ Website Insights: {len(result['website_insights'])} characters")
        return True
        
    except Exception as e:
        print(f"❌ Content analyzer error: {str(e)}")
        return False


def test_validation():
    """Test validation functions."""
    print("\n🔍 Testing Validation...")
    
    try:
        import sys
        sys.path.append('4runr-outreach-system')
        from shared.validation import validate_email_format, validate_website_url, classify_email_confidence
        
        # Test email validation
        test_emails = [
            'test@example.com',
            'invalid-email',
            'john.doe@company.com',
            'admin@4runr.com'
        ]
        
        for email in test_emails:
            valid = validate_email_format(email)
            confidence = classify_email_confidence(email, 'pattern_generation')
            print(f"  Email: {email} - Valid: {valid}, Confidence: {confidence}")
        
        # Test URL validation
        test_urls = [
            'https://example.com',
            'example.com',
            'invalid-url',
            'https://4runr.com'
        ]
        
        for url in test_urls:
            valid = validate_website_url(url)
            print(f"  URL: {url} - Valid: {valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False


def test_airtable_connection():
    """Test Airtable connection."""
    print("\n📊 Testing Airtable Connection...")
    
    try:
        import sys
        sys.path.append('4runr-outreach-system')
        from shared.airtable_client import get_airtable_client
        
        client = get_airtable_client()
        
        # Try to get leads (this will test the connection)
        leads = client.get_leads_for_outreach(limit=1)
        
        print(f"✅ Airtable connection successful")
        print(f"✅ Found {len(leads)} leads ready for processing")
        
        if leads:
            lead = leads[0]
            print(f"  Sample lead: {lead.get('Name', 'Unknown')} at {lead.get('Company', 'Unknown Company')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Airtable connection error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🧪 4Runr Website Scraper Agent - Simple Test Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Content Analyzer", test_content_analyzer),
        ("Validation", test_validation),
        ("Airtable Connection", test_airtable_connection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🏁 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The Website Scraper Agent is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)