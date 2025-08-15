#!/usr/bin/env python3
"""
Debug Lead Retrieval Issue

This script specifically debugs the lead retrieval problem.
"""

import sqlite3
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def debug_retrieval():
    """Debug the lead retrieval issue."""
    print("🔍 Debugging Lead Retrieval")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert a test lead
        test_uuid = "debug-retrieval-uuid"
        print(f"\n📝 Inserting test lead with UUID: {test_uuid}")
        
        cursor.execute("""
            INSERT INTO leads (
                id, uuid, full_name, email, company, title, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (test_uuid, test_uuid, "Debug Retrieval User", "debug@retrieval.com", "Debug Retrieval Company", "Debug Retrieval Title"))
        
        print("  ✅ Lead inserted")
        
        # Check what's in the database
        print(f"\n🔍 Checking database for lead with ID: {test_uuid}")
        cursor.execute("SELECT id, uuid, full_name FROM leads WHERE id = ?", (test_uuid,))
        result = cursor.fetchone()
        
        if result:
            print(f"  ✅ Found lead: ID={result[0]}, UUID={result[1]}, Name={result[2]}")
        else:
            print(f"  ❌ No lead found with ID: {test_uuid}")
        
        # Check with UUID
        print(f"\n🔍 Checking database for lead with UUID: {test_uuid}")
        cursor.execute("SELECT id, uuid, full_name FROM leads WHERE uuid = ?", (test_uuid,))
        result = cursor.fetchone()
        
        if result:
            print(f"  ✅ Found lead: ID={result[0]}, UUID={result[1]}, Name={result[2]}")
        else:
            print(f"  ❌ No lead found with UUID: {test_uuid}")
        
        # List all leads to see what's there
        print(f"\n📋 All leads in database:")
        cursor.execute("SELECT id, uuid, full_name FROM leads")
        all_leads = cursor.fetchall()
        
        for lead in all_leads:
            print(f"  ID: {lead[0]}, UUID: {lead[1]}, Name: {lead[2]}")
        
        # Clean up
        cursor.execute("DELETE FROM leads WHERE uuid = ?", (test_uuid,))
        conn.commit()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error debugging retrieval: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_retrieval()
