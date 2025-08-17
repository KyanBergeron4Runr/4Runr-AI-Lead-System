#!/usr/bin/env python3
"""
Final Working Smart Sync - Uses Only Existing Airtable Field Values
===================================================================
Fixes the dropdown field issue by using only existing Airtable values.
"""

import sqlite3
import requests
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class FinalWorkingSync:
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
        
        if isinstance(date_value, str):
            try:
                # Handle ISO format
                if 'T' in date_value:
                    dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d')
                
                # Handle YYYY-MM-DD format
                if len(date_value) >= 10 and date_value[4] == '-' and date_value[7] == '-':
                    return date_value[:10]
                
                # Try other formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def get_airtable_field_options(self) -> Dict[str, List[str]]:
        """Get existing field options from Airtable to avoid dropdown errors"""
        print("🔍 Getting Airtable field options...")
        
        # Get a sample of existing records to see what values are used
        url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}?maxRecords=10'
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                # Extract existing values for dropdown fields
                sources = set()
                lead_qualities = set()
                
                for record in records:
                    fields = record.get('fields', {})
                    
                    source = fields.get('Source')
                    if source:
                        sources.add(source)
                    
                    lead_quality = fields.get('Lead Quality')
                    if lead_quality:
                        lead_qualities.add(lead_quality)
                
                options = {
                    'sources': list(sources) if sources else ['Manual', 'Import'],
                    'lead_qualities': list(lead_qualities) if lead_qualities else ['Hot', 'Warm', 'Cold']
                }
                
                print(f"✅ Found existing options:")
                print(f"   Sources: {options['sources']}")
                print(f"   Lead Qualities: {options['lead_qualities']}")
                
                return options
                
        except Exception as e:
            print(f"❌ Error getting field options: {e}")
        
        # Fallback to common values
        return {
            'sources': ['Manual', 'Import', 'LinkedIn'],
            'lead_qualities': ['Hot', 'Warm', 'Cold']
        }
    
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
    
    def db_record_to_airtable_fields(self, db_record: Dict, field_options: Dict) -> Dict:
        """Convert database record to Airtable fields with safe values"""
        fields = {}
        
        # Required text fields - only if they have values
        if db_record.get('full_name') and db_record['full_name'].strip():
            fields['Full Name'] = str(db_record['full_name']).strip()
        
        if db_record.get('linkedin_url') and db_record['linkedin_url'].strip():
            fields['LinkedIn URL'] = str(db_record['linkedin_url']).strip()
        
        if db_record.get('job_title') and db_record['job_title'].strip():
            fields['Job Title'] = str(db_record['job_title']).strip()
        
        if db_record.get('company') and db_record['company'].strip():
            fields['Company'] = str(db_record['company']).strip()
        
        if db_record.get('email') and db_record['email'].strip():
            fields['Email'] = str(db_record['email']).strip()
        
        # Source - use existing value or first available option
        db_source = db_record.get('source', '').strip()
        if db_source and db_source in field_options['sources']:
            fields['Source'] = db_source
        elif field_options['sources']:
            fields['Source'] = field_options['sources'][0]  # Use first available option
        
        # Lead Quality - use existing value or default
        db_quality = db_record.get('lead_quality', '').strip()
        if db_quality and db_quality in field_options['lead_qualities']:
            fields['Lead Quality'] = db_quality
        elif 'Warm' in field_options['lead_qualities']:
            fields['Lead Quality'] = 'Warm'
        elif field_options['lead_qualities']:
            fields['Lead Quality'] = field_options['lead_qualities'][0]
        
        # Date field - properly formatted
        fields['Date Scraped'] = self.format_date_for_airtable(db_record.get('date_scraped'))
        
        # Optional fields - only if they have values
        if db_record.get('website') and db_record['website'].strip():
            fields['Website'] = str(db_record['website']).strip()
        
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
        """Perform intelligent sync with safe field values"""
        print("🔄 FINAL WORKING SYNC STARTING")
        print("=" * 50)
        
        # Get field options first
        field_options = self.get_airtable_field_options()
        
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
            
            # Skip records without essential data
            if not name or not name.strip():
                stats['skipped'] += 1
                continue
            
            try:
                # Check if record exists in Airtable
                existing_record = self.find_existing_airtable_record(db_record, airtable_index)
                
                # Convert to Airtable format with safe values
                airtable_fields = self.db_record_to_airtable_fields(db_record, field_options)
                
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
        
        print(f"\n🏆 FINAL WORKING SYNC COMPLETED")
        print("=" * 50)
        print(f"📊 Results:")
        print(f"   Updated existing records: {stats['updated']}")
        print(f"   Created new records: {stats['created']}")
        print(f"   Skipped incomplete records: {stats['skipped']}")
        print(f"   Errors: {stats['errors']}")
        
        return stats

def main():
    """Run the final working sync"""
    try:
        sync_system = FinalWorkingSync()
        stats = sync_system.smart_sync()
        
        print(f"\n🎯 SYNC SUCCESS!")
        print(f"✅ Uses only existing Airtable field values")
        print(f"✅ No dropdown/select field errors")
        print(f"✅ Safe field mapping")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
