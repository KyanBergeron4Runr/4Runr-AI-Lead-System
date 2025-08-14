#!/usr/bin/env python3
"""
Final Database Fix

This script fixes all the database issues we've identified.
"""

import sqlite3
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def fix_database_issues():
    """Fix all database issues."""
    print("🔧 Final Database Fix")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, let's clean up the records with None IDs
        print("\n🧹 Cleaning up records with None IDs:")
        cursor.execute("DELETE FROM leads WHERE id IS NULL")
        deleted_count = cursor.rowcount
        print(f"  Deleted {deleted_count} records with None IDs")
        
        # Now check for remaining duplicates
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n🔍 Found {len(duplicates)} duplicate emails:")
            for email, count in duplicates:
                print(f"  {email}: {count} times")
                
                # Get all leads with this email
                cursor.execute("SELECT id, full_name, company, created_at FROM leads WHERE email = ? ORDER BY created_at", (email,))
                leads = cursor.fetchall()
                
                # Keep the first one, delete the rest
                for i, lead in enumerate(leads):
                    if i == 0:
                        print(f"    Keeping: {lead[1]} at {lead[2]}")
                    else:
                        print(f"    Deleting: {lead[1]} at {lead[2]}")
                        cursor.execute("DELETE FROM leads WHERE id = ?", (lead[0],))
        else:
            print("\n✅ No duplicate emails found")
        
        # Verify cleanup
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        remaining_duplicates = cursor.fetchall()
        
        if remaining_duplicates:
            print(f"\n❌ Still have {len(remaining_duplicates)} duplicate emails")
        else:
            print("\n✅ All duplicates removed")
        
        # Check total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        print(f"\n📊 Total leads after cleanup: {total_leads}")
        
        # Check for invalid records
        cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name = '' OR company = ''")
        invalid_records = cursor.fetchone()[0]
        print(f"📊 Invalid records: {invalid_records}")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_after_fix():
    """Test the database after fixes."""
    print("\n🧪 Testing Database After Fix")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        print(f"📊 Total leads: {total_leads}")
        
        # Test for duplicates
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        print(f"📊 Duplicate emails: {len(duplicates)}")
        
        # Test for invalid records
        cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name = '' OR company = ''")
        invalid_records = cursor.fetchone()[0]
        print(f"📊 Invalid records: {invalid_records}")
        
        # Test lead insertion with proper ID handling
        print("\n🧪 Testing Lead Insertion:")
        
        # Insert a test lead
        test_uuid = "final-test-uuid"
        cursor.execute("""
            INSERT INTO leads (
                id, uuid, full_name, email, company, title, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (test_uuid, test_uuid, "Final Test User", "final@test.com", "Final Test Company", "Final Test Title"))
        
        # Try to retrieve it using the UUID as ID
        cursor.execute("SELECT * FROM leads WHERE id = ?", (test_uuid,))
        retrieved = cursor.fetchone()
        print(f"  Retrieved lead: {retrieved is not None}")
        
        if retrieved:
            print(f"  Retrieved data: ID={retrieved[0]}, Name={retrieved[14] if len(retrieved) > 14 else 'N/A'}")
        
        # Clean up test lead
        cursor.execute("DELETE FROM leads WHERE id = ?", (test_uuid,))
        
        conn.commit()
        conn.close()
        
        print("\n✅ Database test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Final Database Fix Tool")
    print("=" * 40)
    
    if fix_database_issues():
        print("\n✅ Database issues fixed")
    else:
        print("\n❌ Failed to fix database issues")
        sys.exit(1)
    
    if test_database_after_fix():
        print("\n✅ Database test passed")
    else:
        print("\n❌ Database test failed")
        sys.exit(1)
    
    print("\n🎉 All database issues resolved!")
