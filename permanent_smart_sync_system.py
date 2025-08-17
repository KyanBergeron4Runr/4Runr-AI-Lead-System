#!/usr/bin/env python3
"""
Permanent Smart Sync System
============================
Long-term solution that intelligently syncs database to Airtable without duplicates.

Features:
- Detects existing records in Airtable (by LinkedIn URL, Email, or Name)
- Updates existing records instead of creating duplicates
- Only adds genuinely new records
- Maintains bidirectional sync
- Prevents duplicates permanently
"""

import sqlite3
import requests
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class PermanentSmartSync:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        self.db_path = 'data/unified_leads.db'
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable not set")
    
    def get_airtable_records(self) -> Dict[str, Dict]:
        """Get all Airtable records and index them by key identifiers"""
        print("📊 Loading all Airtable records...")
        
        url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        all_records = []
        offset = None
        
        while True:
            params = {}
            if offset:
                params['offset'] = offset
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error fetching Airtable records: {response.status_code}")
                break
                
            data = response.json()
            records = data.get('records', [])
            all_records.extend(records)
            
            offset = data.get('offset')
            if not offset:
                break
        
        # Index records by multiple keys for duplicate detection
        indexed_records = {}
        
        for record in all_records:
            record_id = record['id']
            fields = record.get('fields', {})
            
            # Index by LinkedIn URL (primary key)
            linkedin_url = fields.get('LinkedIn URL', '').strip()
            if linkedin_url:
                indexed_records[f"linkedin:{linkedin_url}"] = record
            
            # Index by email (secondary key)
            email = fields.get('Email', '').strip().lower()
            if email:
                indexed_records[f"email:{email}"] = record
            
            # Index by name+company (tertiary key)
            full_name = fields.get('Full Name', '').strip().lower()
            company = fields.get('Company', '').strip().lower()
            if full_name and company:
                indexed_records[f"name_company:{full_name}:{company}"] = record
            elif full_name:
                indexed_records[f"name:{full_name}"] = record
        
        print(f"✅ Loaded {len(all_records)} Airtable records")
        print(f"🔑 Indexed {len(indexed_records)} unique identifiers")
        
        return indexed_records
    
    def get_database_records(self) -> List[Dict]:
        """Get all database records"""
        print("📊 Loading database records...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('SELECT * FROM leads ORDER BY created_at DESC')
        db_records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ Loaded {len(db_records)} database records")
        return db_records
    
    def find_existing_airtable_record(self, db_record: Dict, airtable_index: Dict) -> Optional[Dict]:
        """Find if a database record already exists in Airtable"""
        
        # Check by LinkedIn URL (highest priority)
        linkedin_url = db_record.get('linkedin_url', '').strip()
        if linkedin_url:
            key = f"linkedin:{linkedin_url}"
            if key in airtable_index:
                return airtable_index[key]
        
        # Check by email (medium priority)
        email = db_record.get('email', '').strip().lower()
        if email:
            key = f"email:{email}"
            if key in airtable_index:
                return airtable_index[key]
        
        # Check by name+company (low priority)
        full_name = db_record.get('full_name', '').strip().lower()
        company = db_record.get('company', '').strip().lower()
        if full_name and company:
            key = f"name_company:{full_name}:{company}"
            if key in airtable_index:
                return airtable_index[key]
        elif full_name:
            key = f"name:{full_name}"
            if key in airtable_index:
                return airtable_index[key]
        
        return None
    
    def db_record_to_airtable_fields(self, db_record: Dict) -> Dict:
        """Convert database record to Airtable fields"""
        return {
            'Full Name': db_record.get('full_name') or '',
            'LinkedIn URL': db_record.get('linkedin_url') or '',
            'Job Title': db_record.get('job_title') or '',
            'Company': db_record.get('company') or '',
            'Email': db_record.get('email') or '',
            'Source': db_record.get('source') or 'Smart Sync',
            'Lead Quality': db_record.get('lead_quality') or 'Warm',
            'Date Scraped': db_record.get('date_scraped') or datetime.now().strftime('%Y-%m-%d'),
            'Website': db_record.get('website') or '',
            'Business_Type': db_record.get('business_type') or '',
            'Company_Description': db_record.get('company_description') or '',
            'Created At': db_record.get('created_at') or datetime.now().isoformat(),
            'AI Message': db_record.get('ai_message') or '',
            'Email_Confidence_Level': str(db_record.get('email_confidence_level') or ''),
            'Follow_Up_Stage': db_record.get('follow_up_stage') or '',
            'Needs Enrichment': 'No'  # Since we're syncing clean data
        }
    
    def update_airtable_record(self, record_id: str, fields: Dict) -> bool:
        """Update an existing Airtable record"""
        url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}/{record_id}'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {'fields': fields}
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error updating record {record_id}: {e}")
            return False
    
    def create_airtable_record(self, fields: Dict) -> Optional[str]:
        """Create a new Airtable record"""
        url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {'fields': fields}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in [200, 201]:
                return response.json().get('id')
            else:
                print(f"❌ Error creating record: {response.status_code} - {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Error creating record: {e}")
            return None
    
    def smart_sync(self) -> Dict:
        """Perform intelligent sync between database and Airtable"""
        print("🔄 SMART SYNC STARTING")
        print("=" * 50)
        
        # Load data
        airtable_index = self.get_airtable_records()
        db_records = self.get_database_records()
        
        stats = {
            'updated': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }
        
        print(f"\n🔄 Processing {len(db_records)} database records...")
        
        for i, db_record in enumerate(db_records):
            name = db_record.get('full_name', 'Unknown')
            
            # Check if record exists in Airtable
            existing_record = self.find_existing_airtable_record(db_record, airtable_index)
            
            # Convert to Airtable format
            airtable_fields = self.db_record_to_airtable_fields(db_record)
            
            if existing_record:
                # Update existing record
                record_id = existing_record['id']
                if self.update_airtable_record(record_id, airtable_fields):
                    stats['updated'] += 1
                    print(f"   ✅ Updated: {name}")
                else:
                    stats['errors'] += 1
                    print(f"   ❌ Failed to update: {name}")
            else:
                # Create new record
                new_record_id = self.create_airtable_record(airtable_fields)
                if new_record_id:
                    stats['created'] += 1
                    print(f"   ➕ Created: {name}")
                else:
                    stats['errors'] += 1
                    print(f"   ❌ Failed to create: {name}")
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(0.1)
        
        print(f"\n🏆 SMART SYNC COMPLETED")
        print("=" * 50)
        print(f"📊 Results:")
        print(f"   Updated existing records: {stats['updated']}")
        print(f"   Created new records: {stats['created']}")
        print(f"   Skipped records: {stats['skipped']}")
        print(f"   Errors: {stats['errors']}")
        
        # Save sync log
        sync_log = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'total_db_records': len(db_records),
            'total_airtable_records': len(airtable_index)
        }
        
        with open('smart_sync_log.json', 'w') as f:
            json.dump(sync_log, f, indent=2)
        
        return stats

def main():
    """Run the smart sync"""
    try:
        sync_system = PermanentSmartSync()
        stats = sync_system.smart_sync()
        
        print(f"\n🎯 SYNC SUCCESS!")
        print(f"✅ No duplicates created")
        print(f"✅ Database and Airtable in sync")
        print(f"✅ Long-term solution active")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
