#!/usr/bin/env python3
"""
Fix Database Schema Missing Columns
===================================
Add missing columns that are preventing lead saving
"""

import sqlite3
import logging

class DatabaseSchemaFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_current_schema(self):
        """Check current database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📊 Current columns: {len(columns)}")
            for col in columns:
                self.logger.info(f"   ✅ {col}")
            
            return columns
            
        except Exception as e:
            self.logger.error(f"❌ Error checking schema: {e}")
            return []

    def add_missing_columns(self):
        """Add missing columns that are causing save errors"""
        
        # List of columns that might be missing
        potential_missing = [
            ('industry', 'TEXT'),
            ('location', 'TEXT'), 
            ('company_size', 'TEXT'),
            ('phone', 'TEXT'),
            ('business_type', 'TEXT'),
            ('verified', 'INTEGER'),
            ('enriched', 'INTEGER'),
            ('score', 'REAL'),
            ('engagement_level', 'INTEGER'),
            ('contact_attempts', 'INTEGER'),
            ('follow_up_count', 'INTEGER'),
            ('last_engagement_date', 'TEXT'),
            ('engagement_notes', 'TEXT'),
            ('notes', 'TEXT'),
            ('airtable_id', 'TEXT'),
            ('sync_status', 'TEXT'),
            ('updated_at', 'TIMESTAMP'),
            ('scraped_at', 'TIMESTAMP'),
            ('message_generated_at', 'TIMESTAMP'),
            ('response_received', 'INTEGER')
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get current columns
            cursor = conn.execute("PRAGMA table_info(leads)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            added_count = 0
            
            for column_name, column_type in potential_missing:
                if column_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}")
                        self.logger.info(f"✅ Added column: {column_name} ({column_type})")
                        added_count += 1
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not add {column_name}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Added {added_count} missing columns")
            return added_count
            
        except Exception as e:
            self.logger.error(f"❌ Error adding columns: {e}")
            return 0

    def verify_schema_fix(self):
        """Verify schema is now compatible"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            required_columns = ['industry', 'location', 'phone', 'verified', 'enriched']
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                self.logger.warning(f"⚠️ Still missing: {missing}")
                return False
            else:
                self.logger.info(f"✅ All required columns present")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying schema: {e}")
            return False

def main():
    fixer = DatabaseSchemaFixer()
    
    print("🔧 DATABASE SCHEMA FIXER")
    print("=" * 25)
    print("📋 Adding missing columns that prevent lead saving")
    print("")
    
    # Check current schema
    print("📊 Checking current schema...")
    current_columns = fixer.check_current_schema()
    
    # Add missing columns
    print(f"\n🔧 Adding missing columns...")
    added_count = fixer.add_missing_columns()
    
    if added_count > 0:
        print(f"✅ Added {added_count} missing columns")
        
        # Verify fix
        print(f"\n✅ Verifying schema fix...")
        if fixer.verify_schema_fix():
            print(f"🎉 SCHEMA FIXED SUCCESSFULLY!")
            print(f"   ✅ All required columns now present")
            print(f"   🧪 Test: python3 real_autonomous_organism.py --test")
            print(f"   🎯 Sarah-Eden Dadoun should now save successfully!")
        else:
            print(f"⚠️ Some columns still missing - may need manual investigation")
    else:
        print(f"📋 No columns needed to be added")
    
    print(f"\n🚀 EXPECTED RESULT:")
    print(f"   📋 NEW lead found: Sarah-Eden Dadoun")
    print(f"   💾 Successfully saved to database")
    print(f"   📤 Synced to Airtable")
    print(f"   🎉 Diverse search system fully operational!")

if __name__ == "__main__":
    main()
