#!/usr/bin/env python3
"""
Database migration script for cold lead recycling features

Adds the necessary columns to support recycling functionality.
"""

import sys
import os
from pathlib import Path

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from campaign_system.database.connection import get_database_connection


def migrate_campaigns_table():
    """Add recycling columns to campaigns table"""
    db = get_database_connection()
    
    # List of columns to add
    new_columns = [
        ('is_recycled', 'BOOLEAN DEFAULT FALSE'),
        ('original_campaign_id', 'TEXT'),
        ('recycle_type', 'TEXT'),
        ('recycle_attempt_count', 'INTEGER DEFAULT 0'),
        ('eligible_for_recycle', 'BOOLEAN DEFAULT FALSE'),
        ('last_message_sent_type', 'TEXT'),
        ('days_since_last_message', 'INTEGER DEFAULT 0')
    ]
    
    print("🔄 Migrating campaigns table for recycling support...")
    
    for column_name, column_def in new_columns:
        try:
            # Check if column exists
            check_query = "PRAGMA table_info(campaigns)"
            columns = db.execute_query(check_query)
            existing_columns = [col['name'] for col in columns]
            
            if column_name not in existing_columns:
                # Add the column
                alter_query = f"ALTER TABLE campaigns ADD COLUMN {column_name} {column_def}"
                db.execute_query(alter_query)
                print(f"  ✅ Added column: {column_name}")
            else:
                print(f"  ⚠️  Column already exists: {column_name}")
                
        except Exception as e:
            print(f"  ❌ Error adding column {column_name}: {e}")
    
    print("✅ Campaign table migration complete")


def main():
    """Run database migration"""
    print("🗄️  Database Migration for Cold Lead Recycling")
    print("=" * 50)
    
    try:
        migrate_campaigns_table()
        
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now use the cold lead recycling features:")
        print("  python retry_cold_campaigns.py --stats")
        print("  python retry_cold_campaigns.py --dry-run")
        print("  python test_cold_recycling.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)