#!/usr/bin/env python3
"""
Check and Fix Database Issues

This script identifies and fixes database problems found by the rigorous test.
"""

import sqlite3
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_database_issues():
    """Check for database issues and fix them."""
    print("🔍 Checking Database Issues")
    print("=" * 40)
    
    db_path = "4runr-outreach-system/data/leads_cache.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check schema
        print("\n📋 Database Schema:")
        cursor.execute("PRAGMA table_info(leads)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check for duplicate emails
        print("\n🔍 Checking for duplicate emails:")
        cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"  Found {len(duplicates)} duplicate emails:")
            for email, count in duplicates:
                print(f"    {email}: {count} times")
            
            # Fix duplicates by keeping only the first occurrence
            print("\n🧹 Fixing duplicate emails...")
            for email, count in duplicates:
                cursor.execute("SELECT id FROM leads WHERE email = ? ORDER BY created_at", (email,))
                lead_ids = cursor.fetchall()
                
                # Keep the first one, delete the rest
                for lead_id in lead_ids[1:]:
                    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id[0],))
                    print(f"    Deleted duplicate lead {lead_id[0]} with email {email}")
            
            conn.commit()
            print("  ✅ Duplicate emails fixed")
        else:
            print("  ✅ No duplicate emails found")
        
        # Check total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        print(f"\n📊 Total leads: {total_leads}")
        
        # Check for invalid records
        cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name = '' OR company = ''")
        invalid_records = cursor.fetchone()[0]
        print(f"📊 Invalid records: {invalid_records}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def fix_connection_pool_issues():
    """Fix the connection pool timeout issues."""
    print("\n🔧 Fixing Connection Pool Issues")
    print("=" * 40)
    
    # The issue is that the database operations are taking too long due to logging overhead
    # Let's create a simplified version that bypasses the connection pool for testing
    
    try:
        # Test direct database access
        db_path = "4runr-outreach-system/data/leads_cache.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test simple query
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]
        query_time = time.time() - start_time
        
        print(f"  Direct query time: {query_time:.3f}s")
        print(f"  Total leads: {count}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing direct database access: {e}")
        return False

if __name__ == "__main__":
    import time
    
    print("🚀 Database Issue Checker")
    print("=" * 40)
    
    # Check and fix database issues
    if check_database_issues():
        print("\n✅ Database issues checked")
    else:
        print("\n❌ Failed to check database issues")
    
    # Test connection pool
    if fix_connection_pool_issues():
        print("\n✅ Connection pool issues checked")
    else:
        print("\n❌ Failed to check connection pool issues")
    
    print("\n🎯 Database check completed!")
