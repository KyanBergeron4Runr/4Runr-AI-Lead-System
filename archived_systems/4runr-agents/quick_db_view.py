#!/usr/bin/env python3
"""Quick database view - shows key info at a glance"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.lead_database import get_lead_database

def main():
    db = get_lead_database()
    
    print("🗄️  LEADS DATABASE QUICK VIEW")
    print("=" * 50)
    
    # Stats
    stats = db.get_database_stats()
    print(f"📊 Total Leads: {stats.get('total_leads', 0)}")
    print(f"💾 Database Size: {stats.get('database_size_mb', 0)} MB")
    
    # Status breakdown
    print("\n📈 Status Breakdown:")
    for status, count in stats.get('status_counts', {}).items():
        emoji = {'Ready for Outreach': '🎯', 'contacted': '📧', 'new': '🆕', 'Enriched': '🔍'}.get(status, '❓')
        print(f"   {emoji} {status}: {count}")
    
    # Ready for campaign brain
    ready_leads = db.search_leads({'status': 'Ready for Outreach'})
    print(f"\n🎯 Ready for Campaign Brain: {len(ready_leads)}")
    
    # Show first 5 ready leads
    print("\n📋 Next leads to process:")
    for i, lead in enumerate(ready_leads[:5], 1):
        print(f"   {i}. {lead.get('full_name')} at {lead.get('company')}")
    
    if len(ready_leads) > 5:
        print(f"   ... and {len(ready_leads) - 5} more")
    
    print(f"\n💡 To view full database: python view_database.py")
    print(f"🚀 To process leads: cd ../4runr-brain && python serve_campaign_brain.py --batch-size 3")

if __name__ == '__main__':
    main()