#!/usr/bin/env python3
"""
Simple CLI for 4runr-lead-scraper

A simplified command-line interface that works without complex imports.
"""
import sqlite3
import sys
import os
from pathlib import Path

def get_database_path():
    """Get the database path"""
    return Path(__file__).parent / "data" / "leads.db"

def show_stats():
    """Show database statistics"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print("❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
        with_email = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Ready for Outreach'")
        ready_for_outreach = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE enriched = 1")
        enriched = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        status_counts = cursor.fetchall()
        
        print("📊 4Runr Lead Scraper Statistics")
        print("=" * 40)
        print(f"Total Leads: {total_leads}")
        print(f"With Email: {with_email} ({with_email/total_leads*100:.1f}%)")
        print(f"Enriched: {enriched} ({enriched/total_leads*100:.1f}%)")
        print(f"Ready for Outreach: {ready_for_outreach}")
        
        print("\nStatus Breakdown:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_leads(limit=10):
    """List leads"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print("❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT full_name, email, company, status, enriched 
            FROM leads 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        leads = cursor.fetchall()
        
        print(f"📋 Recent Leads (showing {len(leads)} of {limit})")
        print("=" * 60)
        
        for name, email, company, status, enriched in leads:
            enriched_status = "✅" if enriched else "⏳"
            print(f"{enriched_status} {name}")
            print(f"   📧 {email or 'No email'}")
            print(f"   🏢 {company or 'No company'}")
            print(f"   📊 {status}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_help():
    """Show help information"""
    print("🚀 4Runr Lead Scraper - Simple CLI")
    print("=" * 40)
    print("Available commands:")
    print("  stats          - Show database statistics")
    print("  list [N]       - List recent leads (default: 10)")
    print("  help           - Show this help")
    print()
    print("Examples:")
    print("  python simple_cli.py stats")
    print("  python simple_cli.py list 20")

def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_stats()
    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_leads(limit)
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()