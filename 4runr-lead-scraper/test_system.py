#!/usr/bin/env python3
"""
System Test Script

Quick test to verify the 4runr-lead-scraper system is working correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration():
    """Test configuration loading."""
    print("🧪 Testing Configuration...")
    try:
        from config.settings import get_settings
        settings = get_settings()
        print("✅ Configuration loaded successfully")
        print(f"   Max leads: {settings.scraper.max_leads_per_run}")
        print(f"   Search location: {settings.scraper.search_location}")
        print(f"   SerpAPI key configured: {'Yes' if settings.scraper.serpapi_key else 'No'}")
        print(f"   Airtable configured: {'Yes' if settings.airtable.api_key else 'No'}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database():
    """Test database connection."""
    print("\n🧪 Testing Database...")
    try:
        from database.models import get_lead_database
        db = get_lead_database()
        
        # Health check
        health = db.db.health_check()
        print(f"✅ Database connection: {health['status']}")
        print(f"   Database path: {health['database_path']}")
        
        # Statistics
        stats = db.get_lead_statistics()
        print(f"   Total leads: {stats.get('total_leads', 0)}")
        print(f"   Enriched leads: {stats.get('enriched_leads', 0)}")
        
        return health['status'] == 'healthy'
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_scraper():
    """Test SerpAPI scraper (dry run)."""
    print("\n🧪 Testing SerpAPI Scraper...")
    try:
        from scraper.serpapi_scraper import SerpAPILeadScraper
        scraper = SerpAPILeadScraper()
        print("✅ SerpAPI scraper initialized")
        print(f"   API key configured: {'Yes' if scraper.serpapi_key else 'No'}")
        print(f"   Search location: {scraper.search_location}")
        
        # Note: We won't actually scrape to avoid using API credits
        print("   (Skipping actual scraping to preserve API credits)")
        return True
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def test_enricher():
    """Test enrichment system."""
    print("\n🧪 Testing Enrichment System...")
    try:
        from enricher.email_enricher import EmailEnricher
        from enricher.profile_enricher import ProfileEnricher
        
        email_enricher = EmailEnricher()
        profile_enricher = ProfileEnricher()
        
        print("✅ Email enricher initialized")
        print("✅ Profile enricher initialized")
        print(f"   Max email attempts: {email_enricher.max_email_attempts}")
        print(f"   Use pattern emails: {email_enricher.use_pattern_emails}")
        
        return True
    except Exception as e:
        print(f"❌ Enricher test failed: {e}")
        return False

def test_sync():
    """Test Airtable sync system."""
    print("\n🧪 Testing Airtable Sync...")
    try:
        from sync.airtable_sync import AirtableSync
        sync = AirtableSync()
        
        print("✅ Airtable sync initialized")
        print(f"   Base ID: {sync.base_id}")
        print(f"   Table name: {sync.table_name}")
        
        # Note: We won't actually sync to avoid modifying Airtable
        print("   (Skipping actual sync to avoid modifying Airtable)")
        return True
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        return False

def test_cli():
    """Test CLI system."""
    print("\n🧪 Testing CLI System...")
    try:
        # Test importing CLI components
        from cli.cli import cli
        print("✅ CLI system imported successfully")
        
        # Test help command
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        if result.exit_code == 0:
            print("✅ CLI help command works")
            return True
        else:
            print(f"❌ CLI help failed: {result.output}")
            return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 4Runr Lead Scraper - System Test")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_database,
        test_scraper,
        test_enricher,
        test_sync,
        test_cli
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! System is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())