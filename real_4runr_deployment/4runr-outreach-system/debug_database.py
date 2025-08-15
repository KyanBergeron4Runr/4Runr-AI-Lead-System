#!/usr/bin/env python3
"""
Debug Database Issues

This script investigates the specific database problems we're seeing.
"""

import sqlite3
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def debug_database():
    """Debug the database issues."""
    print("🔍 Debugging Database Issues")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check the ID column type and values
        print("\n📋 ID Column Analysis:")
        cursor.execute("SELECT id, full_name, email FROM leads LIMIT 5")
        sample_leads = cursor.fetchall()
        
        for lead in sample_leads:
            print(f"  ID: {lead[0]} (type: {type(lead[0])}) - Name: {lead[1]} - Email: {lead[2]}")
        
        # Check for duplicate emails with more detail
        print("\n🔍 Duplicate Email Analysis:")
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        
        for email, count in duplicates:
            print(f"\n  Email: {email} (appears {count} times)")
            cursor.execute("SELECT id, full_name, company, created_at FROM leads WHERE email = ?", (email,))
            duplicate_leads = cursor.fetchall()
            
            for lead in duplicate_leads:
                print(f"    ID: {lead[0]} - Name: {lead[1]} - Company: {lead[2]} - Created: {lead[3]}")
        
        # Test lead insertion and retrieval
        print("\n🧪 Testing Lead Insertion/Retrieval:")
        
        # Insert a test lead
        test_uuid = "debug-test-uuid"
        cursor.execute("""
            INSERT INTO leads (
                uuid, full_name, email, company, title, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (test_uuid, "Debug User", "debug@test.com", "Debug Company", "Debug Title"))
        
        # Get the inserted ID
        inserted_id = cursor.lastrowid
        print(f"  Inserted lead with ID: {inserted_id} (type: {type(inserted_id)})")
        
        # Try to retrieve it
        cursor.execute("SELECT * FROM leads WHERE id = ?", (inserted_id,))
        retrieved = cursor.fetchone()
        print(f"  Retrieved lead: {retrieved is not None}")
        
        if retrieved:
            print(f"  Retrieved data: ID={retrieved[0]}, Name={retrieved[14] if len(retrieved) > 14 else 'N/A'}")
        
        # Clean up test lead
        cursor.execute("DELETE FROM leads WHERE uuid = ?", (test_uuid,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error debugging database: {e}")
        import traceback
        traceback.print_exc()

def fix_duplicates_properly():
    """Fix duplicate emails properly."""
    print("\n🧹 Fixing Duplicates Properly")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all duplicate emails
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        
        for email, count in duplicates:
            print(f"\n  Processing email: {email} ({count} duplicates)")
            
            # Get all leads with this email, ordered by creation time
            cursor.execute("""
                SELECT id, full_name, company, created_at 
                FROM leads 
                WHERE email = ? 
                ORDER BY created_at
            """, (email,))
            
            leads = cursor.fetchall()
            
            # Keep the first one, delete the rest
            for i, lead in enumerate(leads):
                if i == 0:
                    print(f"    Keeping: ID={lead[0]} - {lead[1]} at {lead[2]}")
                else:
                    print(f"    Deleting: ID={lead[0]} - {lead[1]} at {lead[2]}")
                    cursor.execute("DELETE FROM leads WHERE id = ?", (lead[0],))
        
        conn.commit()
        
        # Verify duplicates are gone
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        remaining_duplicates = cursor.fetchall()
        
        if remaining_duplicates:
            print(f"\n❌ Still have {len(remaining_duplicates)} duplicate emails")
        else:
            print("\n✅ All duplicates removed")
        
        # Check total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        print(f"📊 Total leads after cleanup: {total_leads}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing duplicates: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Database Debug Tool")
    print("=" * 40)
    
    debug_database()
    fix_duplicates_properly()
    
    print("\n🎯 Debug completed!")
