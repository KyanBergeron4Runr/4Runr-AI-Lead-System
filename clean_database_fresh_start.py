#!/usr/bin/env python3
"""
Clean Database Fresh Start
==========================
Remove all contaminated leads for a completely fresh start
"""

import sqlite3
import json
import logging
from datetime import datetime

class DatabaseCleaner:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def backup_all_leads(self):
        """Backup all current leads before cleaning"""
        self.logger.info("💾 Backing up all current leads...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Create backup file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backups/full_database_backup_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(leads, f, indent=2, default=str)
            
            self.logger.info(f"💾 Backed up {len(leads)} leads to: {backup_file}")
            return backup_file, len(leads)
            
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            return None, 0

    def get_database_stats(self):
        """Get current database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get total leads
            cursor = conn.execute("SELECT COUNT(*) as total FROM leads")
            total = cursor.fetchone()['total']
            
            # Get leads by status
            cursor = conn.execute("""
                SELECT Response_Status, COUNT(*) as count 
                FROM leads 
                GROUP BY Response_Status
            """)
            status_counts = {row['Response_Status']: row['count'] for row in cursor.fetchall()}
            
            # Get leads with/without contact info
            cursor = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN Email IS NOT NULL AND Email != '' THEN 1 END) as with_email,
                    COUNT(CASE WHEN LinkedIn_URL IS NOT NULL AND LinkedIn_URL != '' THEN 1 END) as with_linkedin,
                    COUNT(CASE WHEN (Email IS NULL OR Email = '') AND (LinkedIn_URL IS NULL OR LinkedIn_URL = '') THEN 1 END) as no_contact
                FROM leads
            """)
            contact_stats = dict(cursor.fetchone())
            
            conn.close()
            
            return {
                'total': total,
                'status_counts': status_counts,
                'contact_stats': contact_stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting stats: {e}")
            return None

    def clean_all_leads(self):
        """Remove ALL leads for fresh start"""
        self.logger.info("🧹 Cleaning ALL leads from database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Delete all leads
            cursor = conn.execute("DELETE FROM leads")
            deleted_count = cursor.rowcount
            
            # Reset auto-increment
            conn.execute("DELETE FROM sqlite_sequence WHERE name='leads'")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🧹 Deleted {deleted_count} leads from database")
            self.logger.info(f"✅ Database is now completely clean")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning database: {e}")
            return 0

    def verify_clean_database(self):
        """Verify database is empty"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) as count FROM leads")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                self.logger.info("✅ Database verified: completely clean")
                return True
            else:
                self.logger.warning(f"⚠️ Database not clean: {count} leads remaining")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying database: {e}")
            return False

    def show_database_schema(self):
        """Show current database schema for field planning"""
        self.logger.info("📋 Current database schema:")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = cursor.fetchall()
            conn.close()
            
            self.logger.info("📊 Available columns:")
            for column in columns:
                col_name = column[1]
                col_type = column[2]
                self.logger.info(f"   {col_name} ({col_type})")
            
            return [col[1] for col in columns]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting schema: {e}")
            return []

def main():
    cleaner = DatabaseCleaner()
    
    print("🧹 DATABASE FRESH START CLEANER")
    print("=" * 35)
    print("📋 This will remove ALL leads for a completely fresh start")
    print("")
    
    # Show current stats
    print("📊 Current database status:")
    stats = cleaner.get_database_stats()
    if stats:
        print(f"   📋 Total leads: {stats['total']}")
        print(f"   📊 Status breakdown:")
        for status, count in stats['status_counts'].items():
            print(f"      {status}: {count}")
        print(f"   📧 Contact info:")
        print(f"      With email: {stats['contact_stats']['with_email']}")
        print(f"      With LinkedIn: {stats['contact_stats']['with_linkedin']}")
        print(f"      No contact: {stats['contact_stats']['no_contact']}")
    
    print(f"\n💾 Step 1: Backing up all data...")
    backup_file, backup_count = cleaner.backup_all_leads()
    
    if backup_file:
        print(f"✅ Backup created: {backup_file}")
        print(f"   💾 Backed up: {backup_count} leads")
        
        print(f"\n🧹 Step 2: Cleaning database...")
        deleted_count = cleaner.clean_all_leads()
        
        if deleted_count > 0:
            print(f"✅ Deleted: {deleted_count} leads")
            
            print(f"\n✅ Step 3: Verifying clean state...")
            if cleaner.verify_clean_database():
                print(f"🎉 DATABASE COMPLETELY CLEAN!")
                
                print(f"\n📋 Step 4: Database schema for field planning...")
                columns = cleaner.show_database_schema()
                
                print(f"\n🚀 NEXT STEPS:")
                print(f"   1. ✅ Database is clean and ready")
                print(f"   2. 🔧 Add missing field population logic")
                print(f"   3. 🧪 Test autonomous system with enhanced fields")
                print(f"   4. 🚀 Run continuous mode for fresh, high-quality leads")
                
                print(f"\n💾 BACKUP SAVED:")
                print(f"   📁 File: {backup_file}")
                print(f"   📊 Contains: {backup_count} leads (if needed for recovery)")
                
            else:
                print(f"❌ Database not properly cleaned")
        else:
            print(f"❌ No leads deleted - check database")
    else:
        print(f"❌ Backup failed - aborting clean operation")

if __name__ == "__main__":
    main()
