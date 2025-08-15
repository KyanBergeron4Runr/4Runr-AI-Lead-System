#!/usr/bin/env python3
"""
4Runr Data Cleaner
=================
Removes duplicates and leads without full names from both local database and Airtable
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import json

# Import Airtable client
import sys
sys.path.append('4runr-outreach-system')
from shared.airtable_client import AirtableClient

class DataCleaner:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        self.airtable = AirtableClient()
        
        # Backup directory
        self.backup_dir = f"data/cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/data_cleaner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('data_cleaner')
        
    def backup_database(self):
        """Create a backup before cleaning"""
        try:
            import shutil
            backup_path = os.path.join(self.backup_dir, 'unified_leads_backup.db')
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"✅ Database backed up to: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            return False
            
    def get_local_leads(self) -> List[Dict[str, Any]]:
        """Get all leads from local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📊 Found {len(leads)} leads in local database")
            return leads
        except Exception as e:
            self.logger.error(f"❌ Error reading local database: {e}")
            return []
            
    def get_airtable_leads(self) -> List[Dict[str, Any]]:
        """Get all leads from Airtable"""
        try:
            leads = self.airtable.get_all_leads()
            self.logger.info(f"📊 Found {len(leads)} leads in Airtable")
            return leads
        except Exception as e:
            self.logger.error(f"❌ Error reading Airtable: {e}")
            return []
            
    def identify_duplicates(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify duplicate leads based on email and LinkedIn URL"""
        seen_emails = {}
        seen_linkedin = {}
        duplicates = []
        
        for lead in leads:
            lead_id = lead.get('id') or lead.get('record_id')
            email = lead.get('email', '').strip().lower()
            linkedin = lead.get('linkedin_url', '').strip().lower()
            
            # Check email duplicates
            if email and email != '':
                if email in seen_emails:
                    duplicates.append({
                        'id': lead_id,
                        'reason': 'duplicate_email',
                        'email': email,
                        'first_seen': seen_emails[email],
                        'lead': lead
                    })
                else:
                    seen_emails[email] = lead_id
                    
            # Check LinkedIn URL duplicates
            if linkedin and linkedin != '':
                if linkedin in seen_linkedin:
                    duplicates.append({
                        'id': lead_id,
                        'reason': 'duplicate_linkedin',
                        'linkedin_url': linkedin,
                        'first_seen': seen_linkedin[linkedin],
                        'lead': lead
                    })
                else:
                    seen_linkedin[linkedin] = lead_id
                    
        return duplicates
        
    def identify_incomplete_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify leads without full names or other critical data"""
        incomplete = []
        
        for lead in leads:
            lead_id = lead.get('id') or lead.get('record_id')
            full_name = lead.get('full_name', '').strip()
            
            reasons = []
            
            # Check for missing or incomplete full name
            if not full_name or len(full_name) < 3:
                reasons.append('missing_full_name')
            elif ' ' not in full_name:
                reasons.append('incomplete_name')  # Only first or last name
                
            # Check for missing email
            email = lead.get('email', '').strip()
            if not email or '@' not in email:
                reasons.append('missing_email')
                
            # Check for missing company
            company = lead.get('company', '').strip()
            if not company:
                reasons.append('missing_company')
                
            if reasons:
                incomplete.append({
                    'id': lead_id,
                    'reasons': reasons,
                    'full_name': full_name,
                    'email': email,
                    'company': company,
                    'lead': lead
                })
                
        return incomplete
        
    def clean_local_database(self, to_remove: List[str]) -> int:
        """Remove leads from local database"""
        if not to_remove:
            return 0
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join(['?' for _ in to_remove])
            cursor.execute(f"DELETE FROM leads WHERE id IN ({placeholders})", to_remove)
            
            removed_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Removed {removed_count} leads from local database")
            return removed_count
        except Exception as e:
            self.logger.error(f"❌ Error cleaning local database: {e}")
            return 0
            
    def clean_airtable(self, to_remove: List[str]) -> int:
        """Remove leads from Airtable"""
        if not to_remove:
            return 0
            
        try:
            removed_count = 0
            for record_id in to_remove:
                try:
                    self.airtable.delete_record(record_id)
                    removed_count += 1
                    self.logger.info(f"✅ Removed Airtable record: {record_id}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to remove {record_id}: {e}")
                    
            return removed_count
        except Exception as e:
            self.logger.error(f"❌ Error cleaning Airtable: {e}")
            return 0
            
    def save_cleanup_report(self, duplicates: List[Dict], incomplete: List[Dict], 
                          local_removed: int, airtable_removed: int):
        """Save a detailed cleanup report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'duplicates_found': len(duplicates),
                'incomplete_leads_found': len(incomplete),
                'local_database_cleaned': local_removed,
                'airtable_cleaned': airtable_removed
            },
            'duplicates': duplicates,
            'incomplete_leads': incomplete
        }
        
        report_path = os.path.join(self.backup_dir, 'cleanup_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        self.logger.info(f"📋 Cleanup report saved: {report_path}")
        
    def run_cleanup(self, dry_run: bool = False):
        """Run the complete data cleanup process"""
        self.logger.info("🧹 Starting Data Cleanup Process")
        
        if not dry_run:
            if not self.backup_database():
                self.logger.error("❌ Backup failed, aborting cleanup")
                return
                
        # Get all leads
        local_leads = self.get_local_leads()
        airtable_leads = self.get_airtable_leads()
        
        # Identify issues
        local_duplicates = self.identify_duplicates(local_leads)
        local_incomplete = self.identify_incomplete_leads(local_leads)
        
        airtable_duplicates = self.identify_duplicates(airtable_leads)
        airtable_incomplete = self.identify_incomplete_leads(airtable_leads)
        
        # Report findings
        self.logger.info(f"📊 LOCAL DATABASE ISSUES:")
        self.logger.info(f"   - Duplicates: {len(local_duplicates)}")
        self.logger.info(f"   - Incomplete: {len(local_incomplete)}")
        
        self.logger.info(f"📊 AIRTABLE ISSUES:")
        self.logger.info(f"   - Duplicates: {len(airtable_duplicates)}")
        self.logger.info(f"   - Incomplete: {len(airtable_incomplete)}")
        
        if dry_run:
            self.logger.info("🔍 DRY RUN - No changes made")
            self.save_cleanup_report(
                local_duplicates + airtable_duplicates,
                local_incomplete + airtable_incomplete,
                0, 0
            )
            return
            
        # Clean local database
        local_to_remove = [item['id'] for item in local_duplicates + local_incomplete]
        local_removed = self.clean_local_database(local_to_remove)
        
        # Clean Airtable
        airtable_to_remove = [item['id'] for item in airtable_duplicates + airtable_incomplete]
        airtable_removed = self.clean_airtable(airtable_to_remove)
        
        # Save report
        self.save_cleanup_report(
            local_duplicates + airtable_duplicates,
            local_incomplete + airtable_incomplete,
            local_removed, airtable_removed
        )
        
        self.logger.info("✅ DATA CLEANUP COMPLETE!")
        self.logger.info(f"   - Local database: {local_removed} leads removed")
        self.logger.info(f"   - Airtable: {airtable_removed} leads removed")
        self.logger.info(f"   - Backup saved: {self.backup_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean duplicate and incomplete leads')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    cleaner = DataCleaner()
    
    if not args.dry_run and not args.force:
        print("⚠️  This will permanently remove duplicate and incomplete leads!")
        print("📋 A backup will be created before cleaning.")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cleanup cancelled")
            exit(0)
    
    cleaner.run_cleanup(dry_run=args.dry_run)
