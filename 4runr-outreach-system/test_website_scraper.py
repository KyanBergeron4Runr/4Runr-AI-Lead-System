#!/usr/bin/env python3
"""
Test script for the Website Scraper Agent.

This script tests the website scraping functionality with sample data
before running on real Airtable leads.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from website_scraper.simple_scraper import SimpleScrapingEngine as WebScrapingEngine
from website_scraper.content_analyzer import ContentAnalyzer
from shared.logging_utils import get_logger


async def test_scraping_engine():
    """Test the web scraping engine with sample websites."""
    logger = get_logger('test')
    
    # Test websites
    test_sites = [
        'https://example.com',
        'https://4runr.com',  # If available
        'https://openai.com'
    ]
    
    print("🔍 Testing Web Scraping Engine...")
    
    async with WebScrapingEngine() as engine:
        for site in test_sites:
            print(f"\n📄 Testing: {site}")
            try:
                result = await engine.scrape_website(site, 'test_lead')
                
                if result['success']:
                    print(f"✅ Success: Scraped {len(result['scraped_pages'])} pages")
                    print(f"   Content length: {result['total_content_length']} characters")
                    print(f"   Pages: {', '.join(result['scraped_pages'])}")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")


def test_content_analyzer():
    """Test the content analyzer with sample content."""
    print("\n🧠 Testing Content Analyzer...")
    
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


def test_configuration():
    """Test configuration loading."""
    print("\n⚙️  Testing Configuration...")
    
    try:
        from shared.config import config
        
        # Test configuration access
        airtable_config = config.get_airtable_config()
        scraping_config = config.get_scraping_config()
        
        print(f"✅ Airtable configured: {bool(airtable_config.get('api_key'))}")
        print(f"✅ Scraping delay: {scraping_config['delay']}s")
        print(f"✅ Max retries: {scraping_config['max_retries']}")
        
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")


async def test_full_workflow():
    """Test the complete workflow with a sample website."""
    print("\n🔄 Testing Full Workflow...")
    
    test_url = "https://example.com"
    
    try:
        # Step 1: Scrape website
        async with WebScrapingEngine() as engine:
            scraped_data = await engine.scrape_website(test_url, 'workflow_test')
        
        if not scraped_data['success']:
            print(f"❌ Scraping failed: {scraped_data.get('error')}")
            return
        
        print(f"✅ Step 1: Scraped {len(scraped_data['scraped_pages'])} pages")
        
        # Step 2: Analyze content
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze_content(scraped_data, 'workflow_test')
        
        print(f"✅ Step 2: Content analyzed")
        print(f"   Description: {len(analysis['company_description'])} chars")
        print(f"   Services: {len(analysis['top_services'])} chars")
        print(f"   Tone: {analysis['tone']}")
        
        # Step 3: Validate for Airtable
        from shared.validation import validate_airtable_fields
        
        fields = {
            'Company_Description': analysis['company_description'],
            'Top_Services': analysis['top_services'],
            'Tone': analysis['tone'],
            'Website_Insights': analysis['website_insights']
        }
        
        validation = validate_airtable_fields(fields)
        
        if validation['valid']:
            print("✅ Step 3: Fields validated for Airtable")
        else:
            print(f"❌ Step 3: Validation failed: {validation['errors']}")
        
        print("\n🎉 Full workflow test completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")


async def main():
    """Run all tests."""
    print("🧪 4Runr Website Scraper Agent - Test Suite")
    print("=" * 50)
    
    # Test configuration first
    test_configuration()
    
    # Test content analyzer (doesn't require network)
    test_content_analyzer()
    
    # Test scraping engine (requires network)
    await test_scraping_engine()
    
    # Test full workflow
    await test_full_workflow()
    
    print("\n" + "=" * 50)
    print("🏁 Test suite completed!")


if __name__ == '__main__':
    asyncio.run(main())