#!/usr/bin/env python3
"""
Check Database Status - Quick diagnostic script
"""

import sqlite3
from pathlib import Path

def check_database_status():
    """Check the current status of the unified database"""
    
    db_path = Path("data/unified_leads.db")
    
    if not db_path.exists():
        print("❌ Unified database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN ai_message IS NOT NULL AND ai_message != '' THEN 1 END) as with_ai_messages,
                COUNT(CASE WHEN enriched = 1 THEN 1 END) as enriched_leads,
                COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_emails,
                COUNT(CASE WHEN company IS NOT NULL AND company != '' THEN 1 END) as with_companies
            FROM leads
        """)
        
        result = cursor.fetchone()
        total_leads, with_ai_messages, enriched_leads, with_emails, with_companies = result
        
        print("📊 Database Status Report")
        print("=" * 50)
        print(f"Total leads: {total_leads}")
        print(f"Leads with AI messages: {with_ai_messages} ({with_ai_messages/total_leads*100:.1f}%)")
        print(f"Enriched leads: {enriched_leads} ({enriched_leads/total_leads*100:.1f}%)")
        print(f"Leads with emails: {with_emails} ({with_emails/total_leads*100:.1f}%)")
        print(f"Leads with companies: {with_companies} ({with_companies/total_leads*100:.1f}%)")
        
        # Check for leads missing AI messages
        cursor.execute("""
            SELECT id, full_name, company, email 
            FROM leads 
            WHERE (ai_message IS NULL OR ai_message = '') 
            AND company IS NOT NULL 
            AND company != ''
            LIMIT 5
        """)
        
        missing_ai = cursor.fetchall()
        
        print(f"\n🔍 Sample leads missing AI messages:")
        for lead in missing_ai:
            print(f"  - ID {lead[0]}: {lead[1]} at {lead[2]} ({lead[3]})")
        
        # Check recent activity
        cursor.execute("""
            SELECT created_at, COUNT(*) 
            FROM leads 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY created_at DESC
        """)
        
        recent_activity = cursor.fetchall()
        
        print(f"\n📅 Recent activity (last 7 days):")
        for date, count in recent_activity:
            print(f"  - {date}: {count} leads added")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database_status()
