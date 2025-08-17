#!/usr/bin/env python3
"""
Comprehensive Duplicate Cleaner
===============================
Cleans both Airtable AND internal database of duplicates.
Fixes the issue where duplicate prevention rejects all leads.
"""

import sqlite3
import requests
import os
import json
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher
from typing import List, Dict, Tuple

class ComprehensiveDuplicateCleaner:
    def __init__(self, db_path='data/unified_leads.db'):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        self.db_path = db_path
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable not set")
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings"""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
    
    def get_all_airtable_records(self) -> List[Dict]:
        """Get all records from Airtable"""
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
                print(f"❌ Error: {response.status_code}")
                break
                
            data = response.json()
            records = data.get('records', [])
            all_records.extend(records)
            
            offset = data.get('offset')
            if not offset:
                break
        
        print(f"✅ Loaded {len(all_records)} Airtable records")
        return all_records
    
    def get_all_database_records(self) -> List[Dict]:
        """Get all records from database"""
        print("📊 Loading all database records...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('SELECT * FROM leads ORDER BY created_at DESC')
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ Loaded {len(records)} database records")
        return records
    
    def find_airtable_duplicates(self, records: List[Dict]) -> List[List[Dict]]:
        """Find duplicate groups in Airtable"""
        print("🔍 Finding Airtable duplicates...")
        
        # Group by exact matches first
        exact_groups = defaultdict(list)
        fuzzy_groups = []
        
        for record in records:
            fields = record.get('fields', {})
            name = str(fields.get('Full Name', '')).strip().lower()
            email = str(fields.get('Email', '')).strip().lower()
            linkedin = str(fields.get('LinkedIn URL', '')).strip().lower()
            
            # Create key for exact matching
            key = f"{name}|{email}|{linkedin}"
            exact_groups[key].append(record)
        
        # Find exact duplicates
        exact_duplicates = [group for group in exact_groups.values() if len(group) > 1]
        
        # Find fuzzy duplicates (similar names + companies)
        processed = set()
        for i, record1 in enumerate(records):
            if i in processed:
                continue
                
            fields1 = record1.get('fields', {})
            name1 = str(fields1.get('Full Name', '')).strip()
            company1 = str(fields1.get('Company', '')).strip()
            
            if not name1:
                continue
            
            fuzzy_group = [record1]
            processed.add(i)
            
            for j, record2 in enumerate(records[i+1:], i+1):
                if j in processed:
                    continue
                    
                fields2 = record2.get('fields', {})
                name2 = str(fields2.get('Full Name', '')).strip()
                company2 = str(fields2.get('Company', '')).strip()
                
                if not name2:
                    continue
                
                name_sim = self.similarity(name1, name2)
                company_sim = self.similarity(company1, company2)
                
                # Consider fuzzy duplicate if high similarity
                if name_sim > 0.8 and company_sim > 0.7:
                    fuzzy_group.append(record2)
                    processed.add(j)
            
            if len(fuzzy_group) > 1:
                fuzzy_groups.append(fuzzy_group)
        
        all_duplicates = exact_duplicates + fuzzy_groups
        
        print(f"🎯 Found {len(exact_duplicates)} exact duplicate groups")
        print(f"🎯 Found {len(fuzzy_groups)} fuzzy duplicate groups")
        print(f"🎯 Total duplicate groups: {len(all_duplicates)}")
        
        return all_duplicates
    
    def find_database_duplicates(self, records: List[Dict]) -> List[List[Dict]]:
        """Find duplicate groups in database"""
        print("🔍 Finding database duplicates...")
        
        # Group by exact matches
        exact_groups = defaultdict(list)
        fuzzy_groups = []
        
        for record in records:
            name = str(record.get('full_name', '')).strip().lower()
            email = str(record.get('email', '')).strip().lower()
            linkedin = str(record.get('linkedin_url', '')).strip().lower()
            
            key = f"{name}|{email}|{linkedin}"
            exact_groups[key].append(record)
        
        # Find exact duplicates
        exact_duplicates = [group for group in exact_groups.values() if len(group) > 1]
        
        # Find fuzzy duplicates
        processed = set()
        for i, record1 in enumerate(records):
            if i in processed:
                continue
                
            name1 = str(record1.get('full_name', '')).strip()
            company1 = str(record1.get('company', '')).strip()
            
            if not name1:
                continue
            
            fuzzy_group = [record1]
            processed.add(i)
            
            for j, record2 in enumerate(records[i+1:], i+1):
                if j in processed:
                    continue
                    
                name2 = str(record2.get('full_name', '')).strip()
                company2 = str(record2.get('company', '')).strip()
                
                if not name2:
                    continue
                
                name_sim = self.similarity(name1, name2)
                company_sim = self.similarity(company1, company2)
                
                if name_sim > 0.8 and company_sim > 0.7:
                    fuzzy_group.append(record2)
                    processed.add(j)
            
            if len(fuzzy_group) > 1:
                fuzzy_groups.append(fuzzy_group)
        
        all_duplicates = exact_duplicates + fuzzy_groups
        
        print(f"🎯 Found {len(exact_duplicates)} exact duplicate groups")
        print(f"🎯 Found {len(fuzzy_groups)} fuzzy duplicate groups")
        print(f"🎯 Total duplicate groups: {len(all_duplicates)}")
        
        return all_duplicates
    
    def clean_airtable_duplicates(self, duplicate_groups: List[List[Dict]]) -> int:
        """Clean duplicates from Airtable"""
        print("🧹 Cleaning Airtable duplicates...")
        
        deleted_count = 0
        
        for i, group in enumerate(duplicate_groups, 1):
            print(f"   Group {i}: {len(group)} duplicates")
            
            # Keep the first record, delete the rest
            keep_record = group[0]
            delete_records = group[1:]
            
            keep_name = keep_record.get('fields', {}).get('Full Name', 'Unknown')
            print(f"   📌 Keeping: {keep_name}")
            
            for delete_record in delete_records:
                record_id = delete_record['id']
                delete_name = delete_record.get('fields', {}).get('Full Name', 'Unknown')
                
                # Delete from Airtable
                url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}/{record_id}'
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                try:
                    response = requests.delete(url, headers=headers)
                    if response.status_code == 200:
                        deleted_count += 1
                        print(f"   ✅ Deleted: {delete_name}")
                    else:
                        print(f"   ❌ Failed to delete: {delete_name} ({response.status_code})")
                except Exception as e:
                    print(f"   ❌ Error deleting {delete_name}: {e}")
        
        print(f"✅ Deleted {deleted_count} duplicate records from Airtable")
        return deleted_count
    
    def clean_database_duplicates(self, duplicate_groups: List[List[Dict]]) -> int:
        """Clean duplicates from database"""
        print("🧹 Cleaning database duplicates...")
        
        conn = sqlite3.connect(self.db_path)
        deleted_count = 0
        
        for i, group in enumerate(duplicate_groups, 1):
            print(f"   Group {i}: {len(group)} duplicates")
            
            # Keep the newest record (highest ID), delete the rest
            group_sorted = sorted(group, key=lambda x: x.get('id', 0), reverse=True)
            keep_record = group_sorted[0]
            delete_records = group_sorted[1:]
            
            keep_name = keep_record.get('full_name', 'Unknown')
            print(f"   📌 Keeping: {keep_name} (ID: {keep_record.get('id')})")
            
            for delete_record in delete_records:
                record_id = delete_record['id']
                delete_name = delete_record.get('full_name', 'Unknown')
                
                try:
                    conn.execute('DELETE FROM leads WHERE id = ?', (record_id,))
                    deleted_count += 1
                    print(f"   ✅ Deleted: {delete_name} (ID: {record_id})")
                except Exception as e:
                    print(f"   ❌ Error deleting {delete_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Deleted {deleted_count} duplicate records from database")
        return deleted_count
    
    def comprehensive_cleanup(self) -> Dict:
        """Run comprehensive cleanup of both systems"""
        print("🧹 COMPREHENSIVE DUPLICATE CLEANUP")
        print("=" * 50)
        print("Cleaning both Airtable AND internal database")
        print("")
        
        # Step 1: Clean Airtable
        print("📊 STEP 1: AIRTABLE CLEANUP")
        print("-" * 30)
        
        airtable_records = self.get_all_airtable_records()
        airtable_duplicates = self.find_airtable_duplicates(airtable_records)
        
        airtable_deleted = 0
        if airtable_duplicates:
            airtable_deleted = self.clean_airtable_duplicates(airtable_duplicates)
        else:
            print("✅ No Airtable duplicates found")
        
        # Step 2: Clean Database
        print(f"\n📊 STEP 2: DATABASE CLEANUP")
        print("-" * 30)
        
        db_records = self.get_all_database_records()
        db_duplicates = self.find_database_duplicates(db_records)
        
        db_deleted = 0
        if db_duplicates:
            db_deleted = self.clean_database_duplicates(db_duplicates)
        else:
            print("✅ No database duplicates found")
        
        # Step 3: Final verification
        print(f"\n✅ CLEANUP COMPLETED")
        print("=" * 50)
        
        final_airtable = self.get_all_airtable_records()
        final_db = self.get_all_database_records()
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'airtable_before': len(airtable_records),
            'airtable_after': len(final_airtable),
            'airtable_deleted': airtable_deleted,
            'database_before': len(db_records),
            'database_after': len(final_db),
            'database_deleted': db_deleted,
            'total_deleted': airtable_deleted + db_deleted
        }
        
        print(f"📊 FINAL RESULTS:")
        print(f"   Airtable: {results['airtable_before']} → {results['airtable_after']} (-{results['airtable_deleted']})")
        print(f"   Database: {results['database_before']} → {results['database_after']} (-{results['database_deleted']})")
        print(f"   Total deleted: {results['total_deleted']}")
        
        # Save report
        report_file = f"comprehensive_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Report saved to: {report_file}")
        
        return results

def main():
    """Run comprehensive cleanup"""
    try:
        cleaner = ComprehensiveDuplicateCleaner()
        results = cleaner.comprehensive_cleanup()
        
        if results['total_deleted'] > 0:
            print(f"\n🎉 SUCCESS! Cleaned {results['total_deleted']} duplicates")
            print("✅ Both Airtable and database are now clean")
            print("✅ Duplicate prevention should work properly now")
        else:
            print("\n✅ No duplicates found - systems are already clean")
        
        return 0
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
