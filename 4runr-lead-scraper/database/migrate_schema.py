#!/usr/bin/env python3
"""
Database Schema Migration

Migrates the existing database schema to support the enhanced sync system.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

def migrate_database_schema(db_path: str):
    """
    Migrate database schema to support enhanced sync features.
    
    Args:
        db_path: Path to the database file
    """
    print(f"🔄 Migrating database schema: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(leads)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        print(f"📋 Found {len(existing_columns)} existing columns")
        
        # Define required columns with their SQL definitions
        required_columns = {
            'name': 'TEXT',
            'phone': 'TEXT',
            'company_website': 'TEXT',
            'ready_for_outreach': 'BOOLEAN DEFAULT FALSE',
            'lead_score': 'INTEGER',
            'qualification_criteria': 'TEXT',
            'enrichment_attempts': 'INTEGER DEFAULT 0',
            'enrichment_last_attempt': 'TEXT',
            'enrichment_method': 'TEXT',
            'sync_status': 'TEXT DEFAULT "pending"',
            'scraping_source': 'TEXT DEFAULT "serpapi"',
            'search_query': 'TEXT',
            'search_context': 'TEXT',
            'last_contacted': 'TEXT'
        }
        
        # Add missing columns
        added_columns = []
        for column_name, column_def in required_columns.items():
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE leads ADD COLUMN {column_name} {column_def}"
                    cursor.execute(alter_sql)
                    added_columns.append(column_name)
                    print(f"  ✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"  ⚠️ Failed to add column {column_name}: {e}")
        
        # Update existing data to use new column names if needed
        column_mappings = {
            'full_name': 'name',
            'sync_pending': 'sync_status'
        }
        
        for old_col, new_col in column_mappings.items():
            if old_col in existing_columns and new_col in added_columns:
                try:
                    # Copy data from old column to new column
                    cursor.execute(f"UPDATE leads SET {new_col} = {old_col} WHERE {old_col} IS NOT NULL")
                    print(f"  🔄 Migrated data from {old_col} to {new_col}")
                except sqlite3.Error as e:
                    print(f"  ⚠️ Failed to migrate data from {old_col} to {new_col}: {e}")
        
        # Update sync_status for existing records
        if 'sync_status' in added_columns:
            try:
                # Set sync_status based on existing sync_pending column
                cursor.execute("""
                    UPDATE leads 
                    SET sync_status = CASE 
                        WHEN sync_pending = 1 THEN 'pending'
                        WHEN airtable_synced = 1 THEN 'synced'
                        ELSE 'pending'
                    END
                """)
                print(f"  🔄 Updated sync_status for existing records")
            except sqlite3.Error as e:
                print(f"  ⚠️ Failed to update sync_status: {e}")
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_leads_sync_status ON leads(sync_status)",
            "CREATE INDEX IF NOT EXISTS idx_leads_ready_for_outreach ON leads(ready_for_outreach)",
            "CREATE INDEX IF NOT EXISTS idx_leads_enriched ON leads(enriched)",
            "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
            "CREATE INDEX IF NOT EXISTS idx_leads_scraped_at ON leads(scraped_at)",
            "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"  📊 Created index")
            except sqlite3.Error as e:
                print(f"  ⚠️ Index creation failed: {e}")
        
        # Create sync_log table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    sync_timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp ON sync_log(sync_timestamp)")
            print(f"  📋 Created sync_log table")
        except sqlite3.Error as e:
            print(f"  ⚠️ Failed to create sync_log table: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"✅ Database migration completed successfully")
        print(f"   Added {len(added_columns)} new columns")
        
        return True
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

def main():
    """Main function for CLI usage."""
    try:
        settings = get_settings()
        db_path = settings.database.db_path
        
        print("🔄 4Runr Lead Database Schema Migration")
        print("=" * 40)
        
        success = migrate_database_schema(db_path)
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("   Your database is now ready for the enhanced sync system.")
        else:
            print("\n❌ Migration failed!")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Migration script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())