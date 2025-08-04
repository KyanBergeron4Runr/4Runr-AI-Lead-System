#!/usr/bin/env python3
"""
Check leads ready for outreach
"""

from database.lead_database import get_lead_database

def main():
    db = get_lead_database()
    
    # Check Ready for Outreach leads
    ready_leads = db.search_leads({'status': 'Ready for Outreach'})
    print(f'Ready for Outreach leads: {len(ready_leads)}')
    for lead in ready_leads:
        print(f'  - {lead.get("full_name")} (enriched: {lead.get("enriched")})')
    
    # Check enriched leads
    enriched_leads = db.search_leads({'enriched': True})
    print(f'\nEnriched leads: {len(enriched_leads)}')
    for lead in enriched_leads:
        print(f'  - {lead.get("full_name")} (status: {lead.get("status")})')

if __name__ == '__main__':
    main()