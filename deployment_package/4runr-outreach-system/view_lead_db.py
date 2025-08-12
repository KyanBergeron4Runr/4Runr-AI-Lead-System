#!/usr/bin/env python3
"""
Lead Database Viewer for 4Runr Enhanced Engager.

Provides easy access to view and query the internal SQLite lead database
with engagement tracking, history, and statistics.
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.local_database_manager import LocalDatabaseManager


def view_all_leads():
    """View all leads in the database."""
    print("📋 ALL LEADS IN DATABASE:")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, company, company_website, 
                       engagement_stage, last_contacted, created_at, updated_at
                FROM leads 
                ORDER BY updated_at DESC
            """)
            
            leads = cursor.fetchall()
            
            if not leads:
                print("   📭 No leads found in database")
                return
            
            for i, lead in enumerate(leads, 1):
                print(f"\n{i}. 👤 {lead['name'] or 'Unknown Name'}")
                print(f"   📧 Email: {lead['email'] or 'No email'}")
                print(f"   🏢 Company: {lead['company'] or 'Unknown Company'}")
                print(f"   🌐 Website: {lead['company_website'] or 'No website'}")
                print(f"   📊 Engagement: {lead['engagement_stage'] or 'Not set'}")
                print(f"   📅 Last Contact: {lead['last_contacted'] or 'Never'}")
                print(f"   🆔 ID: {lead['id']}")
                print(f"   📅 Created: {lead['created_at']}")
                print(f"   🔄 Updated: {lead['updated_at']}")
            
            print(f"\n📊 Total leads: {len(leads)}")
            
    except Exception as e:
        print(f"❌ Error viewing leads: {e}")


def view_engagement_history():
    """View engagement tracking history."""
    print("\n📈 ENGAGEMENT TRACKING HISTORY:")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT et.*, l.name, l.email, l.company
                FROM engagement_tracking et
                LEFT JOIN leads l ON et.lead_id = l.id
                ORDER BY et.contacted_at DESC
                LIMIT 20
            """)
            
            history = cursor.fetchall()
            
            if not history:
                print("   📭 No engagement history found")
                return
            
            for i, record in enumerate(history, 1):
                print(f"\n{i}. 📧 {record['name']} ({record['email']})")
                print(f"   🏢 Company: {record['company']}")
                print(f"   📊 Level: {record['previous_level']} → {record['engagement_level']}")
                print(f"   📅 Contacted: {record['contacted_at']}")
                print(f"   ✅ Success: {bool(record['success'])}")
                print(f"   🔄 Airtable Synced: {bool(record['airtable_synced'])}")
                if record['error_message']:
                    print(f"   ❌ Error: {record['error_message']}")
                if record['message_sent']:
                    print(f"   💬 Message: {record['message_sent'][:100]}...")
            
            print(f"\n📊 Showing last {len(history)} engagement records")
            
    except Exception as e:
        print(f"❌ Error viewing engagement history: {e}")


def view_database_stats():
    """View database statistics."""
    print("\n📊 DATABASE STATISTICS:")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        stats = db_manager.get_engagement_statistics()
        
        print(f"📋 Total Leads: {stats.get('total_leads', 0)}")
        print(f"📈 Recent Engagements (7 days): {stats.get('recent_engagements', 0)}")
        print(f"✅ Success Rate: {stats.get('success_rate', 0):.1%}")
        print(f"🔄 Airtable Sync Rate: {stats.get('airtable_sync_rate', 0):.1%}")
        
        print(f"\n📊 Leads by Engagement Stage:")
        for stage, count in stats.get('by_stage', {}).items():
            print(f"   {stage}: {count}")
            
    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def search_leads(search_term):
    """Search leads by name, email, or company."""
    print(f"\n🔍 SEARCHING FOR: '{search_term}'")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, company, company_website, 
                       engagement_stage, last_contacted
                FROM leads 
                WHERE name LIKE ? OR email LIKE ? OR company LIKE ?
                ORDER BY updated_at DESC
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            results = cursor.fetchall()
            
            if not results:
                print(f"   📭 No leads found matching '{search_term}'")
                return
            
            for i, lead in enumerate(results, 1):
                print(f"\n{i}. 👤 {lead['name']}")
                print(f"   📧 {lead['email']}")
                print(f"   🏢 {lead['company']}")
                print(f"   📊 Engagement: {lead['engagement_stage']}")
                print(f"   📅 Last Contact: {lead['last_contacted'] or 'Never'}")
                print(f"   🆔 ID: {lead['id']}")
            
            print(f"\n📊 Found {len(results)} matching leads")
            
    except Exception as e:
        print(f"❌ Error searching leads: {e}")


def view_lead_details(lead_id):
    """View detailed information for a specific lead."""
    print(f"\n👤 LEAD DETAILS: {lead_id}")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        # Get lead info
        lead_status = db_manager.get_lead_engagement_status(lead_id)
        
        if not lead_status:
            print(f"   ❌ Lead {lead_id} not found")
            return
        
        print(f"👤 Name: {lead_status['name'] or 'Unknown'}")
        print(f"📧 Email: {lead_status['email'] or 'No email'}")
        print(f"🏢 Company: {lead_status['company'] or 'Unknown'}")
        print(f"🌐 Website: {lead_status['company_website'] or 'No website'}")
        print(f"📊 Engagement Stage: {lead_status['engagement_stage']}")
        print(f"📅 Last Contacted: {lead_status['last_contacted'] or 'Never'}")
        print(f"📅 Created: {lead_status['created_at']}")
        print(f"🔄 Updated: {lead_status['updated_at']}")
        
        if lead_status['engagement_history']:
            print(f"📋 History: {lead_status['engagement_history']}")
        
        # Get engagement history
        history = db_manager.get_engagement_history(lead_id)
        
        if history:
            print(f"\n📈 ENGAGEMENT HISTORY ({len(history)} records):")
            for i, record in enumerate(history, 1):
                print(f"\n  {i}. 📅 {record['contacted_at']}")
                print(f"     📊 {record['previous_level']} → {record['engagement_level']}")
                print(f"     ✅ Success: {record['success']}")
                print(f"     🔄 Synced: {record['airtable_synced']}")
                if record['message_sent']:
                    print(f"     💬 Message: {record['message_sent'][:100]}...")
                if record['error_message']:
                    print(f"     ❌ Error: {record['error_message']}")
        
    except Exception as e:
        print(f"❌ Error viewing lead details: {e}")


def export_database():
    """Export database to JSON for analysis."""
    print("\n💾 EXPORTING DATABASE:")
    print("=" * 60)
    
    db_manager = LocalDatabaseManager()
    
    try:
        # Export engagement data
        export_data = db_manager.export_engagement_data()
        
        filename = f"lead_db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Database exported to: {filename}")
        print(f"📊 Exported {len(export_data)} engagement records")
        
    except Exception as e:
        print(f"❌ Error exporting database: {e}")


def main():
    """Main menu for database viewer."""
    print("🗄️  4Runr Lead Database Viewer")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'leads':
            view_all_leads()
        elif command == 'history':
            view_engagement_history()
        elif command == 'stats':
            view_database_stats()
        elif command == 'search' and len(sys.argv) > 2:
            search_leads(sys.argv[2])
        elif command == 'details' and len(sys.argv) > 2:
            view_lead_details(sys.argv[2])
        elif command == 'export':
            export_database()
        else:
            print("❌ Invalid command or missing parameter")
            show_help()
    else:
        # Interactive mode
        while True:
            print("\n🗄️  DATABASE VIEWER MENU:")
            print("1. View all leads")
            print("2. View engagement history")
            print("3. View database statistics")
            print("4. Search leads")
            print("5. View lead details")
            print("6. Export database")
            print("0. Exit")
            
            choice = input("\nSelect option (0-6): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                view_all_leads()
            elif choice == '2':
                view_engagement_history()
            elif choice == '3':
                view_database_stats()
            elif choice == '4':
                search_term = input("Enter search term: ").strip()
                if search_term:
                    search_leads(search_term)
            elif choice == '5':
                lead_id = input("Enter lead ID: ").strip()
                if lead_id:
                    view_lead_details(lead_id)
            elif choice == '6':
                export_database()
            else:
                print("❌ Invalid option")


def show_help():
    """Show command line help."""
    print("\n📖 USAGE:")
    print("python view_lead_db.py [command] [parameter]")
    print("\nCOMMANDS:")
    print("  leads                    - View all leads")
    print("  history                  - View engagement history")
    print("  stats                    - View database statistics")
    print("  search <term>            - Search leads")
    print("  details <lead_id>        - View lead details")
    print("  export                   - Export database to JSON")
    print("  (no command)             - Interactive menu")


if __name__ == '__main__':
    main()