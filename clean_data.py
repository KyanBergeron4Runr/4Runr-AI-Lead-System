#!/usr/bin/env python3
"""
Simple Data Cleaner for 4Runr System
=====================================
Removes duplicates and leads without full names
"""

import sqlite3
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_database():
    """Clean the local database of duplicates and incomplete leads"""
    db_path = 'data/unified_leads.db'
    
    if not os.path.exists(db_path):
        # Try alternative path
        db_path = '4runr-outreach-system/data/unified_leads.db'
        if not os.path.exists(db_path):
            logger.error("❌ Database not found!")
            return
    
    logger.info("🧹 Starting database cleanup...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get initial count
        cursor.execute("SELECT COUNT(*) FROM leads")
        initial_count = cursor.fetchone()[0]
        logger.info(f"📊 Initial lead count: {initial_count}")
        
        # Remove leads without full names or with very short names
        cursor.execute("""
            DELETE FROM leads 
            WHERE full_name IS NULL 
               OR full_name = '' 
               OR LENGTH(TRIM(full_name)) < 3
               OR full_name NOT LIKE '% %'
        """)
        no_name_removed = cursor.rowcount
        logger.info(f"🗑️  Removed {no_name_removed} leads without proper full names")
        
        # Remove duplicates based on email
        cursor.execute("""
            DELETE FROM leads 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM leads 
                WHERE email IS NOT NULL AND email != ''
                GROUP BY LOWER(TRIM(email))
            ) AND email IS NOT NULL AND email != ''
        """)
        email_dups_removed = cursor.rowcount
        logger.info(f"🗑️  Removed {email_dups_removed} duplicate emails")
        
        # Remove duplicates based on LinkedIn URL
        cursor.execute("""
            DELETE FROM leads 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM leads 
                WHERE linkedin_url IS NOT NULL AND linkedin_url != ''
                GROUP BY LOWER(TRIM(linkedin_url))
            ) AND linkedin_url IS NOT NULL AND linkedin_url != ''
        """)
        linkedin_dups_removed = cursor.rowcount
        logger.info(f"🗑️  Removed {linkedin_dups_removed} duplicate LinkedIn URLs")
        
        # Remove leads without email AND without LinkedIn
        cursor.execute("""
            DELETE FROM leads 
            WHERE (email IS NULL OR email = '') 
              AND (linkedin_url IS NULL OR linkedin_url = '')
        """)
        no_contact_removed = cursor.rowcount
        logger.info(f"🗑️  Removed {no_contact_removed} leads without any contact info")
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM leads")
        final_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        total_removed = initial_count - final_count
        logger.info(f"✅ Cleanup complete!")
        logger.info(f"   - Initial leads: {initial_count}")
        logger.info(f"   - Final leads: {final_count}")
        logger.info(f"   - Total removed: {total_removed}")
        
        # Show breakdown
        logger.info(f"📋 Removal breakdown:")
        logger.info(f"   - No proper name: {no_name_removed}")
        logger.info(f"   - Duplicate emails: {email_dups_removed}")
        logger.info(f"   - Duplicate LinkedIn: {linkedin_dups_removed}")
        logger.info(f"   - No contact info: {no_contact_removed}")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        
def show_database_stats():
    """Show current database statistics"""
    db_path = 'data/unified_leads.db'
    
    if not os.path.exists(db_path):
        db_path = '4runr-outreach-system/data/unified_leads.db'
        if not os.path.exists(db_path):
            logger.error("❌ Database not found!")
            return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        
        # Leads without proper names
        cursor.execute("""
            SELECT COUNT(*) FROM leads 
            WHERE full_name IS NULL 
               OR full_name = '' 
               OR LENGTH(TRIM(full_name)) < 3
               OR full_name NOT LIKE '% %'
        """)
        no_name = cursor.fetchone()[0]
        
        # Leads without email
        cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NULL OR email = ''")
        no_email = cursor.fetchone()[0]
        
        # Leads without LinkedIn
        cursor.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url IS NULL OR linkedin_url = ''")
        no_linkedin = cursor.fetchone()[0]
        
        # Potential email duplicates
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT LOWER(TRIM(email))) 
            FROM leads 
            WHERE email IS NOT NULL AND email != ''
        """)
        email_dups = cursor.fetchone()[0] or 0
        
        # Potential LinkedIn duplicates
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT LOWER(TRIM(linkedin_url))) 
            FROM leads 
            WHERE linkedin_url IS NOT NULL AND linkedin_url != ''
        """)
        linkedin_dups = cursor.fetchone()[0] or 0
        
        conn.close()
        
        logger.info("📊 DATABASE STATISTICS")
        logger.info(f"   Total leads: {total}")
        logger.info(f"   Missing/invalid names: {no_name}")
        logger.info(f"   Missing email: {no_email}")
        logger.info(f"   Missing LinkedIn: {no_linkedin}")
        logger.info(f"   Potential email duplicates: {email_dups}")
        logger.info(f"   Potential LinkedIn duplicates: {linkedin_dups}")
        
        issues = no_name + email_dups + linkedin_dups
        if issues > 0:
            logger.info(f"⚠️  Total issues that can be cleaned: {issues}")
        else:
            logger.info("✅ Database looks clean!")
            
    except Exception as e:
        logger.error(f"❌ Error reading stats: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_database_stats()
    elif len(sys.argv) > 1 and sys.argv[1] == '--clean':
        print("⚠️  This will permanently remove duplicate and incomplete leads!")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            clean_database()
        else:
            print("❌ Cleanup cancelled")
    else:
        print("🧹 4Runr Data Cleaner")
        print("Usage:")
        print("  python clean_data.py --stats   # Show database statistics")
        print("  python clean_data.py --clean   # Clean the database")
        print()
        show_database_stats()
