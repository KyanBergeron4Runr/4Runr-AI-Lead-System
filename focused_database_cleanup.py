#!/usr/bin/env python3
"""
🧹 FOCUSED DATABASE CLEANUP 🧹
==============================
Clean internal database completely and prepare for new system deployment.
Handle all duplicates and data quality issues.
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from intelligent_lead_cleaner import IntelligentLeadCleaner

class FocusedDatabaseCleanup:
    """Focused cleanup for internal database"""
    
    def __init__(self):
        self.db_path = "data/unified_leads.db"
        self.lead_cleaner = IntelligentLeadCleaner(self.db_path)
        
        print("🧹 Focused Database Cleanup initialized")
        print("🎯 Ready to clean internal database completely")
    
    def create_backup(self):
        """Create backup before cleanup"""
        print("\n💾 Creating backup...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"database_backup_{timestamp}.db"
        
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_file)
                print(f"✅ Database backed up to: {backup_file}")
                return backup_file
            else:
                print("❌ Database file not found")
                return None
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def analyze_database_state(self):
        """Analyze current database state"""
        print("\n🔍 Analyzing database state...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT COUNT(*) as total FROM leads")
            total_count = cursor.fetchone()['total']
            
            # Get leads with data
            cursor = conn.execute("""
                SELECT COUNT(*) as with_data FROM leads 
                WHERE full_name IS NOT NULL AND full_name != ''
            """)
            with_data_count = cursor.fetchone()['with_data']
            
            # Check for obvious duplicates (same name + company)
            cursor = conn.execute("""
                SELECT full_name, company, COUNT(*) as count
                FROM leads 
                WHERE full_name IS NOT NULL AND company IS NOT NULL
                GROUP BY LOWER(TRIM(full_name)), LOWER(TRIM(company))
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)
            obvious_duplicates = cursor.fetchall()
            
            conn.close()
            
            analysis = {
                'total_leads': total_count,
                'leads_with_data': with_data_count,
                'obvious_duplicate_groups': len(obvious_duplicates),
                'total_obvious_duplicates': sum(row['count'] - 1 for row in obvious_duplicates)
            }
            
            print(f"📊 DATABASE ANALYSIS:")
            print(f"   Total leads: {analysis['total_leads']}")
            print(f"   Leads with data: {analysis['leads_with_data']}")
            print(f"   Obvious duplicate groups: {analysis['obvious_duplicate_groups']}")
            print(f"   Total obvious duplicates: {analysis['total_obvious_duplicates']}")
            
            if obvious_duplicates:
                print(f"\n🔍 Sample duplicates:")
                for i, dup in enumerate(obvious_duplicates[:5], 1):
                    print(f"   {i}. {dup['full_name']} at {dup['company']} ({dup['count']} copies)")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None
    
    def fix_database_schema(self):
        """Fix database schema issues"""
        print("\n🔧 Fixing database schema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Add missing columns that our new system needs
            schema_fixes = [
                "ALTER TABLE leads ADD COLUMN merged_from TEXT",
                "ALTER TABLE leads ADD COLUMN lead_quality_score INTEGER",
                "ALTER TABLE leads ADD COLUMN domain_discovery_method TEXT",
                "ALTER TABLE leads ADD COLUMN domain_confidence TEXT",
                "ALTER TABLE leads ADD COLUMN email_pattern_used TEXT",
                "ALTER TABLE leads ADD COLUMN email_validation_score INTEGER",
                "ALTER TABLE leads ADD COLUMN alternative_emails TEXT",
                "ALTER TABLE leads ADD COLUMN email_confidence_distribution TEXT",
                "ALTER TABLE leads ADD COLUMN enrichment_timestamp TEXT",
                "ALTER TABLE leads ADD COLUMN enrichment_version TEXT"
            ]
            
            for fix in schema_fixes:
                try:
                    conn.execute(fix)
                    print(f"✅ Added column: {fix.split()[-2]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"⚠️ Schema fix issue: {e}")
            
            conn.commit()
            conn.close()
            
            print("✅ Database schema updated")
            
        except Exception as e:
            print(f"❌ Schema fix failed: {e}")
    
    def remove_obvious_duplicates(self):
        """Remove obvious duplicates manually"""
        print("\n🗑️ Removing obvious duplicates...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Find and remove exact duplicates (same name, company, email)
            duplicates_removed = 0
            
            # Get groups of duplicates
            cursor = conn.execute("""
                SELECT full_name, company, email, COUNT(*) as count, 
                       GROUP_CONCAT(rowid) as ids
                FROM leads 
                WHERE full_name IS NOT NULL AND company IS NOT NULL
                GROUP BY LOWER(TRIM(full_name)), LOWER(TRIM(company)), LOWER(TRIM(COALESCE(email, '')))
                HAVING COUNT(*) > 1
            """)
            
            duplicate_groups = cursor.fetchall()
            
            for group in duplicate_groups:
                ids = group['ids'].split(',')
                # Keep the first one, delete the rest
                ids_to_delete = ids[1:]
                
                for id_to_delete in ids_to_delete:
                    conn.execute("DELETE FROM leads WHERE rowid = ?", (id_to_delete,))
                    duplicates_removed += 1
            
            conn.commit()
            conn.close()
            
            print(f"✅ Removed {duplicates_removed} obvious duplicates")
            return duplicates_removed
            
        except Exception as e:
            print(f"❌ Duplicate removal failed: {e}")
            return 0
    
    def clean_data_quality(self):
        """Clean data quality issues"""
        print("\n🧼 Cleaning data quality...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Remove leads with no useful data
            cursor = conn.execute("""
                DELETE FROM leads 
                WHERE (full_name IS NULL OR full_name = '')
                AND (company IS NULL OR company = '')
                AND (email IS NULL OR email = '')
            """)
            empty_removed = cursor.rowcount
            
            # Clean up whitespace and normalize data
            conn.execute("""
                UPDATE leads 
                SET full_name = TRIM(full_name),
                    company = TRIM(company),
                    email = LOWER(TRIM(email))
                WHERE full_name IS NOT NULL OR company IS NOT NULL OR email IS NOT NULL
            """)
            
            # Set default values for important fields
            conn.execute("""
                UPDATE leads 
                SET created_at = datetime('now')
                WHERE created_at IS NULL
            """)
            
            conn.execute("""
                UPDATE leads 
                SET source = 'Legacy_Data'
                WHERE source IS NULL OR source = ''
            """)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Removed {empty_removed} empty records")
            print(f"✅ Normalized data formatting")
            
            return empty_removed
            
        except Exception as e:
            print(f"❌ Data quality cleanup failed: {e}")
            return 0
    
    def run_advanced_deduplication(self):
        """Run our advanced deduplication system"""
        print("\n🔬 Running advanced deduplication...")
        
        try:
            # Use our intelligent lead cleaner
            results = self.lead_cleaner.clean_leads_database()
            
            print(f"✅ Advanced deduplication completed")
            print(f"   Leads merged: {results.get('leads_merged', 0)}")
            print(f"   Leads deleted: {results.get('leads_deleted', 0)}")
            print(f"   Final count: {results.get('final_lead_count', 0)}")
            
            return results
            
        except Exception as e:
            print(f"❌ Advanced deduplication failed: {e}")
            return None
    
    def final_verification(self):
        """Final verification of cleanup"""
        print("\n✅ Final verification...")
        
        analysis = self.analyze_database_state()
        
        if analysis:
            print(f"\n🎯 CLEANUP RESULTS:")
            print(f"   Final lead count: {analysis['total_leads']}")
            print(f"   Leads with data: {analysis['leads_with_data']}")
            print(f"   Remaining duplicates: {analysis['total_obvious_duplicates']}")
            
            if analysis['total_obvious_duplicates'] == 0:
                print(f"🎉 DATABASE IS CLEAN! Zero duplicates remaining!")
                return True
            else:
                print(f"⚠️ Still has {analysis['total_obvious_duplicates']} duplicates")
                return False
        
        return False
    
    def run_complete_cleanup(self):
        """Run complete database cleanup"""
        print("🧹 FOCUSED DATABASE CLEANUP STARTING")
        print("=" * 60)
        
        # Step 1: Backup
        backup_file = self.create_backup()
        if not backup_file:
            print("❌ Cannot proceed without backup")
            return
        
        # Step 2: Initial analysis
        initial_analysis = self.analyze_database_state()
        
        # Step 3: Fix schema
        self.fix_database_schema()
        
        # Step 4: Remove obvious duplicates
        obvious_removed = self.remove_obvious_duplicates()
        
        # Step 5: Clean data quality
        empty_removed = self.clean_data_quality()
        
        # Step 6: Advanced deduplication
        advanced_results = self.run_advanced_deduplication()
        
        # Step 7: Final verification
        is_clean = self.final_verification()
        
        # Summary
        print(f"\n🏆 CLEANUP COMPLETED")
        print(f"=" * 60)
        print(f"✅ Backup created: {backup_file}")
        print(f"✅ Schema updated with new fields")
        print(f"✅ Obvious duplicates removed: {obvious_removed}")
        print(f"✅ Empty records removed: {empty_removed}")
        if advanced_results:
            print(f"✅ Advanced dedup removed: {advanced_results.get('leads_deleted', 0)}")
        print(f"🎯 Database is clean: {'YES' if is_clean else 'NEEDS MORE WORK'}")
        
        if is_clean:
            print(f"\n🚀 READY FOR NEW SYSTEM DEPLOYMENT!")
        
        return {
            'backup_file': backup_file,
            'initial_analysis': initial_analysis,
            'obvious_removed': obvious_removed,
            'empty_removed': empty_removed,
            'advanced_results': advanced_results,
            'is_clean': is_clean
        }

def main():
    """Run focused database cleanup"""
    cleanup = FocusedDatabaseCleanup()
    results = cleanup.run_complete_cleanup()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"database_cleanup_results_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: database_cleanup_results_{timestamp}.json")

if __name__ == "__main__":
    main()
