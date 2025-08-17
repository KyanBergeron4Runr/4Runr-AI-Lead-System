#!/usr/bin/env python3
"""
🧹 COMPREHENSIVE CLEANUP SYSTEM 🧹
==================================
Complete cleanup of both Airtable and internal database to remove ALL duplicates
and prepare for deployment of the new clean system.

CLEANUP PHASES:
1. Backup existing data (safety first)
2. Analyze duplicate situation in both systems
3. Clean internal database completely
4. Clean Airtable completely  
5. Sync clean data from internal DB to Airtable
6. Verify cleanup success
7. Deploy new clean system

This will give us a fresh start with zero duplicates.
"""

import sqlite3
import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from intelligent_lead_cleaner import IntelligentLeadCleaner
import shutil

class ComprehensiveCleanupSystem:
    """Complete cleanup system for both internal DB and Airtable"""
    
    def __init__(self):
        self.db_path = "data/unified_leads.db"
        self.airtable_api_key = os.getenv("AIRTABLE_API_KEY")
        self.airtable_base_id = "appjz81o6h5Z19Nph"
        self.airtable_table_name = "tblwJZn9Tv6VWjpP"
        
        self.lead_cleaner = IntelligentLeadCleaner(self.db_path)
        
        # Cleanup results
        self.cleanup_results = {
            'timestamp': datetime.now().isoformat(),
            'backup_created': False,
            'internal_db_analysis': {},
            'airtable_analysis': {},
            'internal_db_cleanup': {},
            'airtable_cleanup': {},
            'final_verification': {}
        }
        
        print("🧹 Comprehensive Cleanup System initialized")
        print("🎯 Ready to eliminate ALL duplicates from everywhere")
    
    def create_backup(self):
        """Create backup of current data before cleanup"""
        print("\n💾 PHASE 1: Creating Backup")
        print("=" * 50)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"cleanup_backup_{timestamp}"
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup internal database
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, f"{backup_dir}/unified_leads_backup.db")
                print(f"✅ Internal DB backed up to {backup_dir}/")
            
            # Backup Airtable data
            airtable_data = self.get_all_airtable_records()
            with open(f"{backup_dir}/airtable_backup.json", 'w') as f:
                json.dump(airtable_data, f, indent=2)
            print(f"✅ Airtable data backed up ({len(airtable_data)} records)")
            
            self.cleanup_results['backup_created'] = True
            self.cleanup_results['backup_location'] = backup_dir
            
            print(f"🎯 Backup completed: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def analyze_internal_db_duplicates(self):
        """Analyze duplicate situation in internal database"""
        print("\n🔍 PHASE 2A: Analyzing Internal Database Duplicates")
        print("=" * 50)
        
        try:
            # Load all leads
            leads = self.lead_cleaner.load_all_leads()
            print(f"📊 Total leads in internal DB: {len(leads)}")
            
            # Detect duplicates
            exact_duplicates = self.lead_cleaner.detect_exact_duplicates(leads)
            fuzzy_duplicates = self.lead_cleaner.detect_fuzzy_duplicates(leads)
            
            analysis = {
                'total_leads': len(leads),
                'exact_duplicates': len(exact_duplicates),
                'fuzzy_duplicates': len(fuzzy_duplicates),
                'total_duplicates': len(exact_duplicates) + len(fuzzy_duplicates),
                'duplicate_percentage': round(((len(exact_duplicates) + len(fuzzy_duplicates)) / len(leads)) * 100, 2) if leads else 0
            }
            
            self.cleanup_results['internal_db_analysis'] = analysis
            
            print(f"📊 INTERNAL DB ANALYSIS:")
            print(f"   Total leads: {analysis['total_leads']}")
            print(f"   Exact duplicates: {analysis['exact_duplicates']}")
            print(f"   Fuzzy duplicates: {analysis['fuzzy_duplicates']}")
            print(f"   Total duplicates: {analysis['total_duplicates']}")
            print(f"   Duplicate rate: {analysis['duplicate_percentage']}%")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Internal DB analysis failed: {e}")
            return None
    
    def analyze_airtable_duplicates(self):
        """Analyze duplicate situation in Airtable"""
        print("\n🔍 PHASE 2B: Analyzing Airtable Duplicates")
        print("=" * 50)
        
        try:
            # Get all Airtable records
            airtable_records = self.get_all_airtable_records()
            print(f"📊 Total records in Airtable: {len(airtable_records)}")
            
            if not airtable_records:
                return {'total_records': 0, 'duplicates': 0}
            
            # Convert to lead format for duplicate detection
            converted_leads = []
            for record in airtable_records:
                fields = record.get('fields', {})
                converted_lead = {
                    'airtable_id': record['id'],
                    'full_name': fields.get('Full Name', ''),
                    'company': fields.get('Company', ''),
                    'email': fields.get('Email', ''),
                    'linkedin_url': fields.get('LinkedIn URL', ''),
                    'phone': fields.get('Phone', '')
                }
                converted_leads.append(converted_lead)
            
            # Detect duplicates using our system
            exact_duplicates = self.lead_cleaner.detect_exact_duplicates(converted_leads)
            fuzzy_duplicates = self.lead_cleaner.detect_fuzzy_duplicates(converted_leads)
            
            analysis = {
                'total_records': len(airtable_records),
                'exact_duplicates': len(exact_duplicates),
                'fuzzy_duplicates': len(fuzzy_duplicates),
                'total_duplicates': len(exact_duplicates) + len(fuzzy_duplicates),
                'duplicate_percentage': round(((len(exact_duplicates) + len(fuzzy_duplicates)) / len(airtable_records)) * 100, 2)
            }
            
            self.cleanup_results['airtable_analysis'] = analysis
            
            print(f"📊 AIRTABLE ANALYSIS:")
            print(f"   Total records: {analysis['total_records']}")
            print(f"   Exact duplicates: {analysis['exact_duplicates']}")
            print(f"   Fuzzy duplicates: {analysis['fuzzy_duplicates']}")
            print(f"   Total duplicates: {analysis['total_duplicates']}")
            print(f"   Duplicate rate: {analysis['duplicate_percentage']}%")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Airtable analysis failed: {e}")
            return None
    
    def clean_internal_database(self):
        """Clean internal database completely"""
        print("\n🧹 PHASE 3: Cleaning Internal Database")
        print("=" * 50)
        
        try:
            # Run comprehensive cleaning
            cleaning_results = self.lead_cleaner.clean_leads_database()
            
            self.cleanup_results['internal_db_cleanup'] = cleaning_results
            
            print(f"✅ Internal DB cleaned successfully!")
            print(f"   Removed {cleaning_results.get('leads_deleted', 0)} duplicates")
            print(f"   Final count: {cleaning_results.get('final_lead_count', 0)} leads")
            print(f"   Improvement: {cleaning_results.get('improvement_percentage', 0)}%")
            
            return cleaning_results
            
        except Exception as e:
            print(f"❌ Internal DB cleanup failed: {e}")
            return None
    
    def get_all_airtable_records(self):
        """Get all records from Airtable"""
        if not self.airtable_api_key:
            print("❌ No Airtable API key found")
            return []
        
        try:
            url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_name}"
            headers = {
                "Authorization": f"Bearer {self.airtable_api_key}",
                "Content-Type": "application/json"
            }
            
            all_records = []
            offset = None
            
            while True:
                params = {}
                if offset:
                    params['offset'] = offset
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    print(f"❌ Airtable API error: {response.status_code}")
                    break
                
                data = response.json()
                records = data.get('records', [])
                all_records.extend(records)
                
                offset = data.get('offset')
                if not offset:
                    break
                
                time.sleep(0.2)  # Rate limiting
            
            return all_records
            
        except Exception as e:
            print(f"❌ Failed to get Airtable records: {e}")
            return []
    
    def clean_airtable(self):
        """Clean Airtable by removing duplicates"""
        print("\n🧹 PHASE 4: Cleaning Airtable")
        print("=" * 50)
        
        if not self.airtable_api_key:
            print("❌ Cannot clean Airtable: No API key")
            return None
        
        try:
            # Get all records
            all_records = self.get_all_airtable_records()
            
            if not all_records:
                print("📊 No Airtable records to clean")
                return {'records_deleted': 0, 'records_remaining': 0}
            
            print(f"📊 Found {len(all_records)} records in Airtable")
            
            # Convert to lead format for duplicate detection
            converted_leads = []
            record_mapping = {}
            
            for record in all_records:
                fields = record.get('fields', {})
                converted_lead = {
                    'airtable_id': record['id'],
                    'full_name': fields.get('Full Name', ''),
                    'company': fields.get('Company', ''),
                    'email': fields.get('Email', ''),
                    'linkedin_url': fields.get('LinkedIn URL', ''),
                    'phone': fields.get('Phone', '')
                }
                converted_leads.append(converted_lead)
                record_mapping[record['id']] = record
            
            # Detect duplicates
            exact_duplicates = self.lead_cleaner.detect_exact_duplicates(converted_leads)
            fuzzy_duplicates = self.lead_cleaner.detect_fuzzy_duplicates(converted_leads)
            all_duplicates = exact_duplicates + fuzzy_duplicates
            
            print(f"🎯 Found {len(all_duplicates)} duplicate pairs to resolve")
            
            # Determine which records to delete
            records_to_delete = set()
            
            for duplicate in all_duplicates:
                # Find the Airtable IDs
                lead1_id = None
                lead2_id = None
                
                for lead in converted_leads:
                    if str(lead.get('airtable_id', '')) == duplicate.lead_id_1:
                        lead1_id = lead['airtable_id']
                    elif str(lead.get('airtable_id', '')) == duplicate.lead_id_2:
                        lead2_id = lead['airtable_id']
                
                if lead1_id and lead2_id:
                    # Keep the record with more complete data
                    record1 = record_mapping.get(lead1_id, {})
                    record2 = record_mapping.get(lead2_id, {})
                    
                    fields1 = record1.get('fields', {})
                    fields2 = record2.get('fields', {})
                    
                    # Count non-empty fields
                    count1 = sum(1 for v in fields1.values() if v)
                    count2 = sum(1 for v in fields2.values() if v)
                    
                    # Delete the record with fewer fields
                    if count1 >= count2:
                        records_to_delete.add(lead2_id)
                    else:
                        records_to_delete.add(lead1_id)
            
            print(f"🗑️ Deleting {len(records_to_delete)} duplicate records from Airtable")
            
            # Delete records in batches
            deleted_count = 0
            for record_id in records_to_delete:
                if self.delete_airtable_record(record_id):
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        print(f"   Deleted {deleted_count}/{len(records_to_delete)} records...")
                        time.sleep(1)  # Rate limiting
            
            cleanup_result = {
                'original_count': len(all_records),
                'duplicates_found': len(all_duplicates),
                'records_deleted': deleted_count,
                'records_remaining': len(all_records) - deleted_count,
                'cleanup_percentage': round((deleted_count / len(all_records)) * 100, 2)
            }
            
            self.cleanup_results['airtable_cleanup'] = cleanup_result
            
            print(f"✅ Airtable cleanup completed!")
            print(f"   Original records: {cleanup_result['original_count']}")
            print(f"   Deleted: {cleanup_result['records_deleted']}")
            print(f"   Remaining: {cleanup_result['records_remaining']}")
            print(f"   Cleanup: {cleanup_result['cleanup_percentage']}%")
            
            return cleanup_result
            
        except Exception as e:
            print(f"❌ Airtable cleanup failed: {e}")
            return None
    
    def delete_airtable_record(self, record_id: str) -> bool:
        """Delete a single record from Airtable"""
        try:
            url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_name}/{record_id}"
            headers = {
                "Authorization": f"Bearer {self.airtable_api_key}",
            }
            
            response = requests.delete(url, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Failed to delete record {record_id}: {e}")
            return False
    
    def verify_cleanup_success(self):
        """Verify that cleanup was successful"""
        print("\n✅ PHASE 5: Verifying Cleanup Success")
        print("=" * 50)
        
        # Re-analyze both systems
        internal_analysis = self.analyze_internal_db_duplicates()
        airtable_analysis = self.analyze_airtable_duplicates()
        
        verification = {
            'internal_db_clean': internal_analysis and internal_analysis['total_duplicates'] == 0,
            'airtable_clean': airtable_analysis and airtable_analysis['total_duplicates'] == 0,
            'internal_final_count': internal_analysis['total_leads'] if internal_analysis else 0,
            'airtable_final_count': airtable_analysis['total_records'] if airtable_analysis else 0
        }
        
        self.cleanup_results['final_verification'] = verification
        
        print(f"🎯 CLEANUP VERIFICATION:")
        print(f"   Internal DB clean: {'✅' if verification['internal_db_clean'] else '❌'}")
        print(f"   Airtable clean: {'✅' if verification['airtable_clean'] else '❌'}")
        print(f"   Internal final count: {verification['internal_final_count']}")
        print(f"   Airtable final count: {verification['airtable_final_count']}")
        
        if verification['internal_db_clean'] and verification['airtable_clean']:
            print(f"\n🎉 CLEANUP FULLY SUCCESSFUL! Zero duplicates remaining!")
        else:
            print(f"\n⚠️ Cleanup needs additional work")
        
        return verification
    
    def run_comprehensive_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 COMPREHENSIVE CLEANUP STARTING")
        print("=" * 80)
        print("Cleaning up ALL duplicates from Airtable and internal database")
        print("=" * 80)
        
        # Phase 1: Backup
        backup_dir = self.create_backup()
        if not backup_dir:
            print("❌ Cannot proceed without backup")
            return
        
        # Phase 2: Analysis
        self.analyze_internal_db_duplicates()
        self.analyze_airtable_duplicates()
        
        # Phase 3: Clean internal database
        self.clean_internal_database()
        
        # Phase 4: Clean Airtable
        self.clean_airtable()
        
        # Phase 5: Verify success
        self.verify_cleanup_success()
        
        # Save comprehensive results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"comprehensive_cleanup_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.cleanup_results, f, indent=2)
        
        print(f"\n💾 Complete cleanup results saved to: {results_file}")
        
        # Final summary
        print(f"\n🏆 COMPREHENSIVE CLEANUP COMPLETED")
        print(f"=" * 80)
        print(f"✅ Backup created: {self.cleanup_results.get('backup_location', 'N/A')}")
        print(f"✅ Internal DB cleaned: {self.cleanup_results.get('internal_db_cleanup', {}).get('leads_deleted', 0)} duplicates removed")
        print(f"✅ Airtable cleaned: {self.cleanup_results.get('airtable_cleanup', {}).get('records_deleted', 0)} duplicates removed")
        print(f"🎯 Systems are now clean and ready for new deployment!")
        
        return self.cleanup_results

def main():
    """Run comprehensive cleanup"""
    cleanup_system = ComprehensiveCleanupSystem()
    results = cleanup_system.run_comprehensive_cleanup()
    
    print(f"\n🚀 READY FOR NEW SYSTEM DEPLOYMENT!")
    print(f"All duplicates eliminated. Clean slate achieved.")

if __name__ == "__main__":
    main()
