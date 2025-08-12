#!/usr/bin/env python3
"""
Cleanup and Add Lead Script.

Removes duplicate/incomplete leads and adds Kyan Bergeron properly.
"""

import sys
import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from engager.local_database_manager import LocalDatabaseManager


def cleanup_leads():
    """Remove duplicate/incomplete leads."""
    print("🧹 CLEANING UP DUPLICATE LEADS...")
    
    try:
        airtable_client = get_airtable_client()
        db_manager = LocalDatabaseManager()
        
        # Get all Airtable records
        records = list(airtable_client.table.all())
        
        leads_to_delete = []
        for record in records:
            fields = record.get('fields', {})
            full_name = fields.get('Full Name', '')
            
            # Find Kyan Bergeron records (there might be duplicates)
            if 'kyan' in full_name.lower() and 'bergeron' in full_name.lower():
                leads_to_delete.append(record['id'])
                print(f"   🗑️  Found Kyan Bergeron record to delete: {record['id']}")
        
        # Delete from Airtable
        for record_id in leads_to_delete:
            try:
                airtable_client.table.delete(record_id)
                print(f"   ✅ Deleted from Airtable: {record_id}")
            except Exception as e:
                print(f"   ⚠️  Could not delete {record_id}: {e}")
        
        # Clean up local database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete the duplicate records
            for record_id in leads_to_delete:
                cursor.execute("DELETE FROM leads WHERE id = ?", (record_id,))
                cursor.execute("DELETE FROM engagement_tracking WHERE lead_id = ?", (record_id,))
            
            conn.commit()
            print(f"   ✅ Cleaned up local database")
        
        print(f"🧹 Cleanup complete: removed {len(leads_to_delete)} duplicate records")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


def add_clean_lead():
    """Add Kyan Bergeron with complete data."""
    print("\n📋 ADDING CLEAN LEAD: Kyan Bergeron")
    
    # Lead data
    lead_data = {
        'full_name': 'Kyan Bergeron',
        'email': 'kyan@4runr.com',
        'company': '4Runr',
        'website': 'https://4runr.com',
        'linkedin': 'https://linkedin.com/in/kyan-bergeron',
        'source': 'linkedin_scraper',
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    try:
        airtable_client = get_airtable_client()
        db_manager = LocalDatabaseManager()
        
        # Add to Airtable with only available fields
        airtable_fields = {
            'Full Name': lead_data['full_name'],
            'LinkedIn URL': lead_data['linkedin'],
            'Needs Enrichment': False,
            'Date Scraped': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        record_id = airtable_client.create_lead(airtable_fields)
        
        if not record_id:
            print("❌ Failed to create Airtable record")
            return False
        
        print(f"   ✅ Added to Airtable: {record_id}")
        
        # Add complete data to local database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert complete lead data
            cursor.execute("""
                INSERT INTO leads (
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
                None,
                None,
                lead_data['created_at'],
                lead_data['updated_at']
            ))
            
            # Add initial engagement tracking
            cursor.execute("""
                INSERT INTO engagement_tracking (
                    lead_id, engagement_level, previous_level, contacted_at,
                    message_sent, company_summary, success, airtable_synced
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                '1st degree',
                None,
                datetime.datetime.now().isoformat(),
                '',
                f'{lead_data["company"]} - ready for enhanced engager processing',
                True,
                True
            ))
            
            conn.commit()
        
        print(f"   ✅ Added to local database with complete data")
        
        # Verify the lead
        print(f"\n✅ LEAD ADDED SUCCESSFULLY:")
        print(f"   👤 Name: {lead_data['full_name']}")
        print(f"   📧 Email: {lead_data['email']}")
        print(f"   🏢 Company: {lead_data['company']}")
        print(f"   🌐 Website: {lead_data['website']}")
        print(f"   🔗 LinkedIn: {lead_data['linkedin']}")
        print(f"   🆔 Airtable ID: {record_id}")
        print(f"   📊 Engagement Level: 1st degree")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add clean lead: {e}")
        return False


if __name__ == '__main__':
    print("🧹 4Runr Lead Cleanup & Add")
    print("=" * 30)
    
    # Cleanup first
    cleanup_success = cleanup_leads()
    
    if cleanup_success:
        # Add clean lead
        add_success = add_clean_lead()
        
        if add_success:
            print(f"\n🎉 SUCCESS! Clean lead added.")
            print(f"   Use: python view_lead_db.py leads")
            print(f"   To view the internal database")
        else:
            print(f"\n❌ Failed to add clean lead")
    else:
        print(f"\n❌ Cleanup failed, skipping add")