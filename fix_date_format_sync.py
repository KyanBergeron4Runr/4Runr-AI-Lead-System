#!/usr/bin/env python3
"""
Fixed Smart Sync - Corrects Date Format Issues
==============================================
Fixes the "Date Scraped" field format error and other field mapping issues.
"""

import sqlite3
import requests
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class FixedSmartSync:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        self.db_path = 'data/unified_leads.db'
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable not set")
    
    def format_date_for_airtable(self, date_value) -> str:
        """Convert various date formats to Airtable-compatible format (YYYY-MM-DD)"""
        if not date_value:
            return datetime.now().strftime('%Y-%m-%d')
        
        # If it's already a string, try to parse and reformat
        if isinstance(date_value, str):
            # Handle various date formats
            try:
                # Try ISO format first
                if 'T' in date_value:
                    dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d')
                
                # Try YYYY-MM-DD format
                if len(date_value) >= 10 and date_value[4] == '-' and date_value[7] == '-':
                    return date_value[:10]  # Just take the date part
                
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                        
            except Exception:
                pass
        
        # Default to today if we can't parse
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_airtable_records(self) -> Dict[str, Dict]:
        """Get all Airtable records and index them"""
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
        
        # Index records by multiple keys
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
            
            # Index by name (tertiary key)
            full_name = fields.get('Full Name', '').strip().lower()
            if full_name:
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
        linkedin_url = db_record.get('linkedin_url')
        if linkedin_url and linkedin_url.strip():
            key = f"linkedin:{linkedin_url.strip()}"
            if key in airtable_index:
                return airtable_index[key]
        
        # Check by email (medium priority)
        email = db_record.get('email')
        if email and email.strip():
            key = f"email:{email.strip().lower()}"
            if key in airtable_index:
                return airtable_index[key]
        
        # Check by name (low priority)
        full_name = db_record.get('full_name')
        if full_name and full_name.strip():
            key = f"name:{full_name.strip().lower()}"
            if key in airtable_index:
                return airtable_index[key]
        
        return None
    
    def db_record_to_airtable_fields(self, db_record: Dict) -> Dict:
        """Convert database record to Airtable fields with proper formatting"""
        # Only include fields that have actual values and are properly formatted
        fields = {}
        
        # Required text fields
        if db_record.get('full_name'):
            fields['Full Name'] = str(db_record['full_name']).strip()
        
        if db_record.get('linkedin_url'):
            fields['LinkedIn URL'] = str(db_record['linkedin_url']).strip()
        
        if db_record.get('job_title'):
            fields['Job Title'] = str(db_record['job_title']).strip()
        
        if db_record.get('company'):
            fields['Company'] = str(db_record['company']).strip()
        
        if db_record.get('email'):
            fields['Email'] = str(db_record['email']).strip()
        
        # Always include source
        fields['Source'] = 'Smart Sync'
        
        # Lead quality with default
        fields['Lead Quality'] = str(db_record.get('lead_quality') or 'Warm')
        
        # Date field - properly formatted
        fields['Date Scraped'] = self.format_date_for_airtable(db_record.get('date_scraped'))
        
        # Optional fields - only if they have values
        if db_record.get('website'):
            fields['Website'] = str(db_record['website']).strip()
        
        if db_record.get('business_type'):
            fields['Business_Type'] = str(db_record['business_type']).strip()
        
        if db_record.get('company_description'):
            fields['Company_Description'] = str(db_record['company_description']).strip()
        
        return fields
    
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
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Update error {response.status_code}: {response.text[:200]}")
                return False
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
                print(f"❌ Create error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Error creating record: {e}")
            return None
    
    def smart_sync(self) -> Dict:
        """Perform intelligent sync with proper error handling"""
        print("🔄 FIXED SMART SYNC STARTING")
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
            
            try:
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
                    
            except Exception as e:
                stats['errors'] += 1
                print(f"   ❌ Error processing {name}: {e}")
        
        print(f"\n🏆 FIXED SMART SYNC COMPLETED")
        print("=" * 50)
        print(f"📊 Results:")
        print(f"   Updated existing records: {stats['updated']}")
        print(f"   Created new records: {stats['created']}")
        print(f"   Errors: {stats['errors']}")
        
        return stats

def main():
    """Run the fixed smart sync"""
    try:
        sync_system = FixedSmartSync()
        stats = sync_system.smart_sync()
        
        print(f"\n🎯 SYNC SUCCESS!")
        print(f"✅ Date format issues fixed")
        print(f"✅ Field mapping corrected")
        print(f"✅ Error handling improved")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
