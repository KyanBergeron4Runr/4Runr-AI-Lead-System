#!/usr/bin/env python3
"""
Simple Airtable Sync - Working version to sync fixed data to Airtable
"""
import os
import sys
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_airtable_config():
    """Get Airtable configuration from environment"""
    return {
        'api_key': os.getenv('AIRTABLE_API_KEY'),
        'base_id': os.getenv('AIRTABLE_BASE_ID'),
        'table_name': os.getenv('AIRTABLE_TABLE_NAME', 'Leads')
    }

def get_unified_database():
    """Get connection to unified database"""
    db_path = project_root / 'data' / 'unified_leads.db'
    if not db_path.exists():
        print("❌ Unified database not found!")
        return None
    return sqlite3.connect(db_path)

def get_leads_from_db():
    """Get all leads from unified database"""
    conn = get_unified_database()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, email, company, ai_message, industry, 
               company_size, linkedin_url, created_at, updated_at
        FROM leads
        ORDER BY id
    """)
    
    leads = []
    for row in cursor.fetchall():
        leads.append({
            'id': row[0],
            'full_name': row[1] or '',
            'email': row[2] or '',
            'company': row[3] or '',
            'ai_message': row[4] or '',
            'industry': row[5] or '',
            'company_size': row[6] or '',
            'linkedin_url': row[7] or '',
            'created_at': row[8] or '',
            'updated_at': row[9] or ''
        })
    
    conn.close()
    return leads

def sync_to_airtable(leads):
    """Sync leads to Airtable"""
    config = get_airtable_config()
    
    if not config['api_key'] or not config['base_id']:
        print("❌ Missing Airtable configuration!")
        print("   Please set AIRTABLE_API_KEY, AIRTABLE_BASE_ID, and AIRTABLE_TABLE_NAME")
        return False
    
    url = f"https://api.airtable.com/v0/{config['base_id']}/{config['table_name']}"
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔄 Syncing {len(leads)} leads to Airtable...")
    
    success_count = 0
    error_count = 0
    
    for lead in leads:
        # Prepare record for Airtable
        record = {
            'fields': {
                'Full Name': lead['full_name'],
                'Email': lead['email'],
                'Company': lead['company'],
                'AI Message': lead['ai_message'],
                'LinkedIn URL': lead['linkedin_url']
            }
        }
        
        try:
            # Try to create new record
            response = requests.post(url, headers=headers, json={'records': [record]})
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Synced: {lead['full_name']} at {lead['company']}")
            else:
                error_count += 1
                print(f"❌ Failed to sync {lead['full_name']}: {response.status_code}")
                print(f"   Error response: {response.text}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Error syncing {lead['full_name']}: {str(e)}")
    
    print(f"\n📊 Sync Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    print(f"   📈 Total: {len(leads)}")
    
    return success_count > 0

def main():
    """Main sync function"""
    print("🔄 Simple Airtable Sync")
    print("=" * 50)
    
    # Get leads from database
    leads = get_leads_from_db()
    if not leads:
        print("❌ No leads found in database!")
        return
    
    print(f"📊 Found {len(leads)} leads in database")
    
    # Sync to Airtable
    success = sync_to_airtable(leads)
    
    if success:
        print("\n🎉 Sync completed successfully!")
    else:
        print("\n❌ Sync failed!")

if __name__ == "__main__":
    main()
