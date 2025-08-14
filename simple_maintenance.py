#!/usr/bin/env python3
"""
Simple Database Maintenance Script

A lightweight maintenance script that works with the existing database connection.
"""

import sys
import os
from pathlib import Path

# Add the lead scraper to path
sys.path.insert(0, '4runr-lead-scraper')

try:
    from database.connection import get_database_connection
    from database.models import get_lead_database
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)

def check_database_health():
    """Check basic database health and statistics."""
    print("\n🔍 Database Health Check")
    print("=" * 40)
    
    try:
        # Test connection
        db_conn = get_database_connection()
        print("✅ Database connection established")
        
        # Get basic stats
        cursor = db_conn.execute_query("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        print(f"📊 Total leads: {total_leads}")
        
        # Check for duplicates by email
        cursor = db_conn.execute_query("""
            SELECT email, COUNT(*) as count 
            FROM leads 
            WHERE email IS NOT NULL AND email != ''
            GROUP BY LOWER(email) 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} email duplicates:")
            for email, count in duplicates:
                print(f"   - {email}: {count} records")
        else:
            print("✅ No email duplicates found")
        
        # Check engagement status distribution
        cursor = db_conn.execute_query("""
            SELECT engagement_status, COUNT(*) as count
            FROM leads
            GROUP BY engagement_status
            ORDER BY count DESC
        """)
        statuses = cursor.fetchall()
        
        print("\n📈 Engagement Status Distribution:")
        for status, count in statuses:
            status_display = status if status else "NULL/Empty"
            print(f"   - {status_display}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False

def fix_engagement_status():
    """Fix NULL or empty engagement status values."""
    print("\n🔧 Fixing Engagement Status")
    print("=" * 40)
    
    try:
        db_conn = get_database_connection()
        
        # Find records with NULL or empty engagement status
        cursor = db_conn.execute_query("""
            SELECT COUNT(*) FROM leads 
            WHERE engagement_status IS NULL OR engagement_status = ''
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✅ All records have engagement status set")
            return True
        
        print(f"📝 Found {null_count} records with missing engagement status")
        
        # Update them to 'auto_send'
        cursor = db_conn.execute_query("""
            UPDATE leads 
            SET engagement_status = 'auto_send'
            WHERE engagement_status IS NULL OR engagement_status = ''
        """)
        
        # Commit the changes
        db_conn.connection.commit()
        
        print(f"✅ Updated {null_count} records to 'auto_send' status")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix engagement status: {e}")
        return False

def remove_email_duplicates():
    """Remove duplicate records based on email address."""
    print("\n🗑️  Removing Email Duplicates")
    print("=" * 40)
    
    try:
        db_conn = get_database_connection()
        
        # Find duplicates (keep the most recent one)
        cursor = db_conn.execute_query("""
            WITH duplicates AS (
                SELECT id, email, created_at,
                       ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY created_at DESC) as rn
                FROM leads
                WHERE email IS NOT NULL AND email != ''
            )
            SELECT COUNT(*) FROM duplicates WHERE rn > 1
        """)
        
        duplicate_count = cursor.fetchone()[0]
        
        if duplicate_count == 0:
            print("✅ No email duplicates found")
            return True
        
        print(f"📝 Found {duplicate_count} duplicate records to remove")
        
        # Remove duplicates (keep most recent)
        cursor = db_conn.execute_query("""
            DELETE FROM leads 
            WHERE id IN (
                WITH duplicates AS (
                    SELECT id, email, created_at,
                           ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY created_at DESC) as rn
                    FROM leads
                    WHERE email IS NOT NULL AND email != ''
                )
                SELECT id FROM duplicates WHERE rn > 1
            )
        """)
        
        # Commit the changes
        db_conn.connection.commit()
        
        print(f"✅ Removed {duplicate_count} duplicate records")
        return True
        
    except Exception as e:
        print(f"❌ Failed to remove duplicates: {e}")
        return False

def clean_email_formats():
    """Clean and standardize email formats."""
    print("\n📧 Cleaning Email Formats")
    print("=" * 40)
    
    try:
        db_conn = get_database_connection()
        
        # Find emails that need cleaning
        cursor = db_conn.execute_query("""
            SELECT COUNT(*) FROM leads 
            WHERE email IS NOT NULL 
            AND email != ''
            AND (email != LOWER(TRIM(email)) OR email LIKE '% %')
        """)
        
        dirty_count = cursor.fetchone()[0]
        
        if dirty_count == 0:
            print("✅ All email formats are clean")
            return True
        
        print(f"📝 Found {dirty_count} emails that need cleaning")
        
        # Clean email formats
        cursor = db_conn.execute_query("""
            UPDATE leads 
            SET email = LOWER(TRIM(email))
            WHERE email IS NOT NULL 
            AND email != ''
            AND (email != LOWER(TRIM(email)) OR email LIKE '% %')
        """)
        
        # Commit the changes
        db_conn.connection.commit()
        
        print(f"✅ Cleaned {dirty_count} email formats")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clean email formats: {e}")
        return False

def main():
    """Main maintenance function."""
    print("🔧 Simple Database Maintenance")
    print("=" * 50)
    
    success_count = 0
    total_operations = 4
    
    # Run maintenance operations
    if check_database_health():
        success_count += 1
    
    if fix_engagement_status():
        success_count += 1
    
    if clean_email_formats():
        success_count += 1
    
    if remove_email_duplicates():
        success_count += 1
    
    # Final summary
    print("\n" + "=" * 50)
    print(f"🎉 Maintenance Complete: {success_count}/{total_operations} operations successful")
    
    if success_count == total_operations:
        print("✅ All maintenance operations completed successfully!")
    else:
        print("⚠️  Some operations failed. Check the logs above.")
    
    # Final health check
    print("\n🔍 Final Database Status:")
    check_database_health()

if __name__ == "__main__":
    main()