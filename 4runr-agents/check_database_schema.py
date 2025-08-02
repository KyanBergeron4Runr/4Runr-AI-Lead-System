#!/usr/bin/env python3
"""
Check Database Schema

Examine the actual database schema to understand the structure.
"""

import sqlite3
from pathlib import Path

def check_schema():
    """Check the database schema"""
    print("🔍 Checking Database Schema")
    print("=" * 50)
    
    # Database path
    outreach_dir = Path(__file__).parent.parent / "4runr-outreach-system"
    queue_db = outreach_dir / "campaign_system" / "campaigns.db"
    
    if not queue_db.exists():
        print(f"❌ Database not found: {queue_db}")
        return
        
    try:
        conn = sqlite3.connect(str(queue_db))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Tables: {[table[0] for table in tables]}")
        
        # Check each table schema
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            print("-" * 30)
            
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
            
            # Show sample data
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  📊 Records: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
                sample_rows = cursor.fetchall()
                
                if sample_rows:
                    print(f"  📄 Sample data:")
                    column_names = [col[1] for col in columns]
                    for row in sample_rows:
                        row_dict = dict(zip(column_names, row))
                        for key, value in row_dict.items():
                            if value and len(str(value)) > 50:
                                value = str(value)[:50] + "..."
                            print(f"    {key}: {value}")
                        print("    " + "-" * 20)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")

if __name__ == "__main__":
    check_schema()