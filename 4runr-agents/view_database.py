#!/usr/bin/env python3
"""
Database Viewer - View and explore the leads database
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database

def view_database_stats():
    """Show database statistics"""
    db = get_lead_database()
    stats = db.get_database_stats()
    
    print("=" * 60)
    print("📊 DATABASE STATISTICS")
    print("=" * 60)
    print(f"📍 Database Path: {stats.get('database_path', 'Unknown')}")
    print(f"💾 Database Size: {stats.get('database_size_mb', 0)} MB")
    print(f"📈 Total Leads: {stats.get('total_leads', 0)}")
    print(f"🔄 Pending Sync: {stats.get('pending_sync', 0)}")
    print(f"✅ Synced to Airtable: {stats.get('synced_to_airtable', 0)}")
    print(f"🔍 Enriched Leads: {stats.get('enriched_leads', 0)}")
    print(f"⏳ Needs Enrichment: {stats.get('needs_enrichment', 0)}")
    
    print("\n📊 Status Breakdown:")
    status_counts = stats.get('status_counts', {})
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    
    print(f"\n📅 Added Today: {stats.get('leads_added_today', 0)}")
    print(f"🔄 Updated Today: {stats.get('leads_updated_today', 0)}")

def view_recent_leads(limit=10):
    """Show recent leads"""
    db = get_lead_database()
    leads = db.get_recent_leads(days=30, limit=limit)
    
    print("\n" + "=" * 60)
    print(f"📅 RECENT LEADS (Last 30 days, showing {len(leads)})")
    print("=" * 60)
    
    for lead in leads:
        status_emoji = {
            'Ready for Outreach': '🎯',
            'Campaign Generated': '✅',
            'contacted': '📧',
            'new': '🆕',
            'Enriched': '🔍',
            'Processed': '✅'
        }.get(lead.get('status', ''), '❓')
        
        enriched_emoji = '🔍' if lead.get('enriched') else '⏳'
        verified_emoji = '✅' if lead.get('verified') else '❓'
        
        print(f"{status_emoji} {lead.get('full_name', 'Unknown')}")
        print(f"   🏢 {lead.get('company', 'No company')}")
        print(f"   💼 {lead.get('title', 'No title')}")
        print(f"   📧 {lead.get('email', 'No email')}")
        print(f"   📊 Status: {lead.get('status', 'unknown')}")
        print(f"   {enriched_emoji} Enriched: {lead.get('enriched', False)}")
        print(f"   {verified_emoji} Verified: {lead.get('verified', False)}")
        print(f"   📅 Created: {lead.get('created_at', 'Unknown')[:10]}")
        print()

def view_ready_for_outreach():
    """Show leads ready for campaign brain"""
    db = get_lead_database()
    leads = db.search_leads({'status': 'Ready for Outreach'})
    
    print("\n" + "=" * 60)
    print(f"🎯 LEADS READY FOR CAMPAIGN BRAIN ({len(leads)})")
    print("=" * 60)
    
    for lead in leads:
        raw_data = lead.get('raw_data', {})
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        # Check if already processed by brain
        brain_status = raw_data.get('brain_status', 'Not processed')
        brain_emoji = '🧠' if brain_status != 'Not processed' else '⏳'
        
        print(f"🎯 {lead.get('full_name', 'Unknown')}")
        print(f"   🏢 {lead.get('company', 'No company')}")
        print(f"   💼 {lead.get('title', 'No title')}")
        print(f"   📧 {lead.get('email', 'No email')}")
        print(f"   🔗 {lead.get('linkedin_url', 'No LinkedIn')}")
        print(f"   {brain_emoji} Brain Status: {brain_status}")
        
        # Show enrichment data if available
        if raw_data.get('enrichment_data'):
            enrichment = raw_data['enrichment_data'][:100] + "..." if len(raw_data['enrichment_data']) > 100 else raw_data['enrichment_data']
            print(f"   🔍 Enrichment: {enrichment}")
        
        print()

def search_leads_interactive():
    """Interactive lead search"""
    db = get_lead_database()
    
    print("\n" + "=" * 60)
    print("🔍 INTERACTIVE LEAD SEARCH")
    print("=" * 60)
    
    while True:
        print("\nSearch options:")
        print("1. Search by name")
        print("2. Search by company")
        print("3. Search by status")
        print("4. Search by email")
        print("5. Back to main menu")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            name = input("Enter name to search: ").strip()
            leads = db.quick_search(name, limit=10)
        elif choice == '2':
            company = input("Enter company to search: ").strip()
            leads = db.search_by_company(company)
        elif choice == '3':
            status = input("Enter status to search: ").strip()
            leads = db.get_leads_by_status(status)
        elif choice == '4':
            email = input("Enter email to search: ").strip()
            leads = db.search_leads({'email': email})
        elif choice == '5':
            break
        else:
            print("Invalid choice!")
            continue
        
        print(f"\n📊 Found {len(leads)} leads:")
        for lead in leads[:5]:  # Show first 5
            print(f"   • {lead.get('full_name')} at {lead.get('company')} ({lead.get('status')})")
        
        if len(leads) > 5:
            print(f"   ... and {len(leads) - 5} more")

def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 60)
        print("🗄️  LEADS DATABASE VIEWER")
        print("=" * 60)
        print("1. View Database Statistics")
        print("2. View Recent Leads")
        print("3. View Leads Ready for Campaign Brain")
        print("4. Search Leads")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            view_database_stats()
        elif choice == '2':
            limit = input("How many recent leads to show? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            view_recent_leads(limit)
        elif choice == '3':
            view_ready_for_outreach()
        elif choice == '4':
            search_leads_interactive()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice! Please enter 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")