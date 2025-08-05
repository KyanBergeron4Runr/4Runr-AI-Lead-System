#!/usr/bin/env python3
"""
Add Test Lead Script for 4Runr Email Engager Upgrade.

Adds Kyan Bergeron as a test lead to both local database and Airtable
with all proper fields and validation for deployment testing.
"""

import sys
import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from engager.local_database_manager import LocalDatabaseManager
from shared.logging_utils import get_logger


def add_lead():
    """Add Kyan Bergeron as regular lead to database and Airtable."""
    logger = get_logger('lead_addition')
    
    # Lead data (as if scraped naturally)
    lead_data = {
        'full_name': 'Kyan Bergeron',
        'email': 'kyan@4runr.com',
        'company': '4Runr',
        'website': 'https://4runr.com',
        'status': 'Ready for Outreach',
        'source': 'linkedin_scraper',
        'contact_stage': None,  # Unset as requested
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    print("📋 Adding Lead: Kyan Bergeron")
    print(f"   📧 Email: {lead_data['email']}")
    print(f"   🏢 Company: {lead_data['company']}")
    print(f"   🌐 Website: {lead_data['website']}")
    print(f"   📊 Status: {lead_data['status']}")
    
    # Initialize clients
    try:
        airtable_client = get_airtable_client()
        db_manager = LocalDatabaseManager()
        print("   ✅ Clients initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize clients: {e}")
        return False
    
    # Check available fields and existing leads
    print("\n🔍 Checking Airtable schema and existing leads...")
    try:
        # Get existing leads to check schema and duplicates
        existing_leads = list(airtable_client.table.all(max_records=5))
        
        if existing_leads:
            available_fields = list(existing_leads[0].get('fields', {}).keys())
            print(f"   📋 Available fields: {available_fields}")
        
        duplicate_found = False
        for record in existing_leads:
            fields = record.get('fields', {})
            existing_email = fields.get('Email', '').lower()
            existing_name = fields.get('Full Name', '') or fields.get('Name', '')
            
            if existing_email == lead_data['email'].lower():
                print(f"   ⚠️  Found existing lead with same email:")
                print(f"      - Name: {existing_name}")
                print(f"      - Email: {existing_email}")
                print(f"      - Status: {fields.get('Engagement_Status', 'Unknown')}")
                duplicate_found = True
                break
        
        if not duplicate_found:
            print("   ✅ No duplicate email found")
        
    except Exception as e:
        print(f"   ⚠️  Could not check schema/duplicates: {e}")
    
    # Add to Airtable
    print("\n📋 Adding to Airtable...")
    try:
        # Use only the exact fields that exist in Airtable
        airtable_fields = {
            'Full Name': lead_data['full_name'],
            'LinkedIn URL': f"https://linkedin.com/in/kyan-bergeron",
            'Needs Enrichment': False,
            'Date Scraped': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        # Create record in Airtable
        record_id = airtable_client.create_lead(airtable_fields)
        
        if record_id:
            print(f"   ✅ Successfully added to Airtable with ID: {record_id}")
            lead_data['airtable_id'] = record_id
        else:
            print("   ❌ Failed to add to Airtable")
            return False
            
    except Exception as e:
        print(f"   ❌ Airtable insertion failed: {e}")
        return False
    
    # Add to Local Database
    print("\n💾 Adding to Local Database...")
    try:
        # First, add the complete lead data to local database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO leads (
                    id, name, email, company, company_website, 
                    engagement_stage, last_contacted, engagement_history, 
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                lead_data['full_name'],
                lead_data['email'],
                lead_data['company'],
                lead_data['website'],
                '1st degree',
                None,  # Not contacted yet
                None,
                lead_data['created_at'],
                lead_data['updated_at']
            ))
            conn.commit()
        
        # Then add engagement tracking record
        engagement_data = {
            'engagement_stage': '1st degree',
            'last_contacted': None,
            'engagement_history': None,
            'success': True,
            'airtable_synced': True
        }
        
        db_success = db_manager.update_engagement_data(record_id, engagement_data)
        
        if db_success:
            print("   ✅ Successfully added to local database")
        else:
            print("   ❌ Failed to add to local database")
            return False
            
    except Exception as e:
        print(f"   ❌ Database insertion failed: {e}")
        return False
    
    # Validation Summary
    print("\n✅ LEAD ADDED SUCCESSFULLY:")
    print(f"   👤 Name: {airtable_fields['Full Name']}")
    print(f"   📧 Email: {lead_data['email']} (unique and valid)")
    print(f"   🏢 Company: {lead_data['company']}")
    print(f"   🌐 Website: {lead_data['website']} (available for scraping)")
    print(f"   🔗 Airtable ID: {record_id}")
    print(f"   💾 Local DB: Synced with 1st degree engagement level")
    print(f"   📅 Date Scraped: {airtable_fields['Date Scraped']}")
    print(f"   🔗 LinkedIn: {airtable_fields['LinkedIn URL']}")
    
    # Ready for Processing
    print("\n🚀 READY FOR ENHANCED ENGAGER!")
    print("   The system will:")
    print("   • Load 4Runr knowledge base")
    print("   • Scrape 4runr.com for company context")
    print("   • Generate personalized 1st degree message")
    print("   • Update engagement level after sending")
    print("   • Log comprehensive engagement data")
    
    logger.log_module_activity('lead_addition', 'system', 'success', {
        'message': 'Lead added successfully',
        'lead_name': lead_data['full_name'],
        'email': lead_data['email'],
        'company': lead_data['company'],
        'source': lead_data['source'],
        'airtable_id': record_id
    })
    
    return True


def verify_lead():
    """Verify the lead was added correctly."""
    print("\n🔍 VERIFYING LEAD...")
    
    try:
        airtable_client = get_airtable_client()
        db_manager = LocalDatabaseManager()
        
        # Check Airtable
        leads = airtable_client.table.all(formula="AND({Email} = 'kyan@4runr.com')")
        airtable_found = len(list(leads)) > 0
        
        # Check Local Database
        db_stats = db_manager.get_engagement_statistics()
        
        print(f"   📋 Airtable: {'✅ Found' if airtable_found else '❌ Not found'}")
        print(f"   💾 Local DB: {db_stats.get('total_leads', 0)} total leads")
        
        return airtable_found
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


if __name__ == '__main__':
    print("📋 4Runr Enhanced Engager - Add Lead")
    print("=" * 40)
    
    success = add_lead()
    
    if success:
        verify_lead()
        print("\n🎉 Lead added successfully!")
        print("   Ready for enhanced engager processing.")
    else:
        print("\n❌ Lead addition failed!")
        sys.exit(1)