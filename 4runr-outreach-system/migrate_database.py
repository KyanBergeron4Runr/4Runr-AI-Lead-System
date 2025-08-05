#!/usr/bin/env python3
"""
Database Migration Script for 4Runr Enhanced Engager.

Migrates existing database to new schema with engagement tracking fields.
"""

import sys
import sqlite3
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def migrate_database():
    """Migrate database to new schema."""
    print("🔄 Database Migration for Enhanced Engager")
    print("=" * 50)
    
    # Check both possible database locations
    db_paths = [
        "data/leads_cache.db",
        "../data/leads_cache.db",
        "leads_cache.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"📁 Found database: {db_path}")
            migrate_single_db(db_path)
        else:
            print(f"📭 No database at: {db_path}")
    
    # Create new database with proper schema
    print(f"\n🆕 Creating new database with proper schema...")
    create_new_database("data/leads_cache.db")


def migrate_single_db(db_path):
    """Migrate a single database file."""
    print(f"\n🔄 Migrating: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check existing schema
        cursor.execute("PRAGMA table_info(leads)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"   📋 Existing columns: {list(columns.keys())}")
        
        # Add missing columns
        new_columns = {
            'engagement_stage': 'TEXT DEFAULT "1st degree"',
            'last_contacted': 'TIMESTAMP',
            'engagement_history': 'TEXT'
        }
        
        for column_name, column_def in new_columns.items():
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_def}")
                    print(f"   ✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️  Column {column_name} already exists or error: {e}")
        
        # Create engagement_tracking table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                engagement_level TEXT NOT NULL,
                previous_level TEXT,
                contacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_sent TEXT,
                company_summary TEXT,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                airtable_synced BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)
        print(f"   ✅ Created engagement_tracking table")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_leads_engagement_stage ON leads(engagement_stage)",
            "CREATE INDEX IF NOT EXISTS idx_leads_last_contacted ON leads(last_contacted)",
            "CREATE INDEX IF NOT EXISTS idx_engagement_tracking_lead_id ON engagement_tracking(lead_id)",
            "CREATE INDEX IF NOT EXISTS idx_engagement_tracking_contacted_at ON engagement_tracking(contacted_at)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"   ✅ Created index")
            except sqlite3.OperationalError as e:
                print(f"   ⚠️  Index error: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Migration completed for {db_path}")
        
    except Exception as e:
        print(f"   ❌ Migration failed for {db_path}: {e}")


def create_new_database(db_path):
    """Create new database with proper schema."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create leads table with all columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                company TEXT,
                company_website TEXT,
                engagement_stage TEXT DEFAULT '1st degree',
                last_contacted TIMESTAMP,
                engagement_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create engagement_tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                engagement_level TEXT NOT NULL,
                previous_level TEXT,
                contacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_sent TEXT,
                company_summary TEXT,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                airtable_synced BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_engagement_stage ON leads(engagement_stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_last_contacted ON leads(last_contacted)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_tracking_lead_id ON engagement_tracking(lead_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_tracking_contacted_at ON engagement_tracking(contacted_at)")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ New database created: {db_path}")
        
    except Exception as e:
        print(f"   ❌ Failed to create new database: {e}")


def verify_database():
    """Verify the database schema is correct."""
    print(f"\n🔍 Verifying database schema...")
    
    db_path = "data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check leads table
        cursor.execute("PRAGMA table_info(leads)")
        leads_columns = [row[1] for row in cursor.fetchall()]
        print(f"   📋 Leads table columns: {leads_columns}")
        
        # Check engagement_tracking table
        cursor.execute("PRAGMA table_info(engagement_tracking)")
        tracking_columns = [row[1] for row in cursor.fetchall()]
        print(f"   📋 Tracking table columns: {tracking_columns}")
        
        # Check for required columns
        required_leads_columns = ['id', 'name', 'email', 'company', 'company_website', 'engagement_stage']
        missing_columns = [col for col in required_leads_columns if col not in leads_columns]
        
        if missing_columns:
            print(f"   ❌ Missing columns: {missing_columns}")
            return False
        else:
            print(f"   ✅ All required columns present")
            return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


if __name__ == '__main__':
    migrate_database()
    
    if verify_database():
        print(f"\n🎉 Database migration completed successfully!")
        print(f"   You can now use: python view_lead_db.py leads")
    else:
        print(f"\n❌ Database migration failed!")
        sys.exit(1)