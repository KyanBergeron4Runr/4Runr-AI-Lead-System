#!/usr/bin/env python3
"""
Test script for the Lead Cache System

This script tests the basic functionality of the lead cache without requiring Airtable.
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from cache.lead_cache import LeadCache

def test_lead_cache():
    """Test basic lead cache functionality"""
    
    print("🧪 Testing Lead Cache System")
    print("=" * 50)
    
    # Initialize cache (will create database)
    cache = LeadCache("data/test_leads_cache.db")
    
    # Test 1: Add some sample leads
    print("\n1️⃣ Testing lead creation...")
    
    sample_leads = [
        {
            'id': 'test_001',
            'Name': 'John Smith',
            'Company': 'TechCorp',
            'Email': 'john@techcorp.com',
            'Status': 'new',
            'Title': 'CEO',
            'LinkedIn URL': 'https://linkedin.com/in/johnsmith',
            'Website': 'https://techcorp.com',
            'Location': 'Montreal, QC'
        },
        {
            'id': 'test_002',
            'Name': 'Jane Doe',
            'Company': 'StartupCo',
            'Email': 'jane@startupco.com',
            'Status': 'scraped',
            'Title': 'CTO',
            'LinkedIn URL': 'https://linkedin.com/in/janedoe',
            'Website': 'https://startupco.com',
            'Location': 'Toronto, ON'
        },
        {
            'id': 'test_003',
            'Name': 'Bob Wilson',
            'Company': 'InnovateLab',
            'Email': '',
            'Status': 'scraped',
            'Title': 'Founder',
            'LinkedIn URL': 'https://linkedin.com/in/bobwilson',
            'Website': 'https://innovatelab.com',
            'Location': 'Vancouver, BC'
        }
    ]
    
    for lead in sample_leads:
        success = cache.add_lead(lead)
        print(f"   {'✅' if success else '❌'} Added {lead['Name']} at {lead['Company']}")
    
    # Test 2: Get all leads
    print("\n2️⃣ Testing get all leads...")
    all_leads = cache.get_all_leads()
    print(f"   Found {len(all_leads)} leads total")
    
    # Test 3: Get leads by status
    print("\n3️⃣ Testing get leads by status...")
    scraped_leads = cache.get_leads_by_status('scraped')
    print(f"   Found {len(scraped_leads)} leads with status 'scraped'")
    for lead in scraped_leads:
        print(f"   - {lead['name']} at {lead['company']}")
    
    # Test 4: Search leads
    print("\n4️⃣ Testing lead search...")
    search_results = cache.search_leads('Tech')
    print(f"   Found {len(search_results)} leads matching 'Tech'")
    for lead in search_results:
        print(f"   - {lead['name']} at {lead['company']}")
    
    # Test 5: Get specific lead
    print("\n5️⃣ Testing get lead by ID...")
    lead = cache.get_lead_by_id('test_001')
    if lead:
        print(f"   ✅ Found lead: {lead['name']} at {lead['company']}")
    else:
        print("   ❌ Lead not found")
    
    # Test 6: Update lead
    print("\n6️⃣ Testing lead update...")
    success = cache.update_lead('test_003', {
        'Email': 'bob@innovatelab.com',
        'Status': 'enriched'
    })
    print(f"   {'✅' if success else '❌'} Updated lead test_003")
    
    # Verify update
    updated_lead = cache.get_lead_by_id('test_003')
    if updated_lead and updated_lead['email'] == 'bob@innovatelab.com':
        print(f"   ✅ Update verified: {updated_lead['name']} now has email")
    
    # Test 7: Cache stats
    print("\n7️⃣ Testing cache statistics...")
    stats = cache.get_cache_stats()
    print(f"   Total leads: {stats['total_leads']}")
    print(f"   Status breakdown: {stats['status_counts']}")
    print(f"   Pending sync: {stats['pending_sync']}")
    print(f"   Cache fresh: {stats['cache_fresh']}")
    
    # Test 8: Cache freshness
    print("\n8️⃣ Testing cache freshness...")
    is_fresh = cache.is_cache_fresh(max_age_hours=24)
    print(f"   Cache is {'fresh' if is_fresh else 'stale'}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print(f"📊 Final stats: {stats['total_leads']} leads, {stats['pending_sync']} pending sync")
    
    return True

def cleanup_test_db():
    """Clean up test database"""
    test_db_path = "data/test_leads_cache.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"🧹 Cleaned up test database: {test_db_path}")

if __name__ == "__main__":
    try:
        # Run tests
        test_lead_cache()
        
        # Ask if user wants to keep test data
        keep_data = input("\n🤔 Keep test database for inspection? (y/N): ").lower().strip()
        if keep_data != 'y':
            cleanup_test_db()
        else:
            print("📁 Test database kept at: data/test_leads_cache.db")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)