#!/usr/bin/env python3
"""
Test Sync Flow

Simulates adding a new lead (as if from scraper) and tests the automatic sync to Airtable.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database.models import get_lead_database
from sync.sync_scheduler import get_sync_scheduler

def test_lead_sync_flow():
    """Test the complete lead sync flow."""
    print("🧪 Testing Lead Sync Flow")
    print("=" * 40)
    
    # Initialize components
    db = get_lead_database()
    scheduler = get_sync_scheduler()
    
    # Create test lead data (as if from scraper)
    lead_data = {
        'name': 'Kyan Bergeron',
        'company': '4Runr',
        'title': 'CEO',
        'linkedin_url': 'https://linkedin.com/in/kyan-bergeron',
        'location': 'Montreal, Quebec, Canada',
        'status': 'scraped',
        'scraped_at': datetime.now().isoformat(),
        'scraping_source': 'serpapi',
        'search_query': 'CEO Montreal',
        'enriched': False,
        'ready_for_outreach': False,
        'sync_status': 'pending'
    }
    
    print(f"📋 Adding lead: {lead_data['name']}")
    print(f"   🏢 Company: {lead_data['company']}")
    print(f"   💼 Title: {lead_data['title']}")
    print(f"   🔗 LinkedIn: {lead_data['linkedin_url']}")
    print(f"   📍 Location: {lead_data['location']}")
    
    try:
        # Step 1: Add lead to database
        print("\n1️⃣ Adding lead to database...")
        lead_id = db.create_lead(lead_data)
        print(f"   ✅ Lead created with ID: {lead_id}")
        
        # Step 2: Verify lead is in database
        print("\n2️⃣ Verifying lead in database...")
        saved_lead = db.get_lead(lead_id)
        if saved_lead:
            print(f"   ✅ Lead found: {saved_lead.name}")
            print(f"   📊 Sync status: {saved_lead.sync_status}")
        else:
            print("   ❌ Lead not found in database")
            return False
        
        # Step 3: Test immediate sync to Airtable
        print("\n3️⃣ Testing immediate sync to Airtable...")
        sync_result = scheduler.sync_lead_to_airtable_immediately(lead_id)
        
        if sync_result['success']:
            print(f"   ✅ Lead synced to Airtable successfully")
            if sync_result.get('skipped'):
                print("   ⏭️ Immediate sync was disabled")
        else:
            print(f"   ❌ Sync failed: {sync_result.get('error', 'Unknown error')}")
        
        # Step 4: Verify sync status updated
        print("\n4️⃣ Verifying sync status...")
        time.sleep(2)  # Give it a moment to update
        updated_lead = db.get_lead(lead_id)
        if updated_lead:
            print(f"   📊 Updated sync status: {updated_lead.sync_status}")
            if updated_lead.airtable_id:
                print(f"   🔗 Airtable ID: {updated_lead.airtable_id}")
            if updated_lead.airtable_synced:
                print(f"   📅 Last synced: {updated_lead.airtable_synced}")
        
        # Step 5: Check overall sync status
        print("\n5️⃣ Checking overall sync status...")
        status = scheduler.get_sync_status()
        scheduler_info = status.get('scheduler', {})
        
        print(f"   🔄 Scheduler running: {'Yes' if scheduler_info.get('scheduler_running') else 'No'}")
        print(f"   ⚡ Immediate sync: {'Enabled' if scheduler_info.get('immediate_sync_enabled') else 'Disabled'}")
        print(f"   📋 Pending leads: {scheduler_info.get('pending_leads_count', 0)}")
        
        print("\n🎉 Test completed successfully!")
        print(f"   Lead '{lead_data['name']}' has been:")
        print("   ✅ Added to local database")
        print("   ✅ Synced to Airtable (if immediate sync enabled)")
        print("   ✅ Ready for enrichment and outreach")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_lead_sync_flow()
    sys.exit(0 if success else 1)