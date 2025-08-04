#!/usr/bin/env python3
"""
Debug database search
"""

from database.lead_database import get_lead_database

def main():
    db = get_lead_database()
    
    # Check all leads
    all_leads = db.get_all_leads(limit=10)
    print(f'Total leads in database: {len(all_leads)}')
    
    for lead in all_leads:
        print(f'  - {lead.get("full_name")} (status: "{lead.get("status")}", enriched: {lead.get("enriched")})')
    
    print('\n--- Testing searches ---')
    
    # Test exact status search
    ready_leads = db.search_leads({'status': 'Ready for Outreach'})
    print(f'Ready for Outreach leads: {len(ready_leads)}')
    
    # Test enriched search
    enriched_leads = db.search_leads({'enriched': True})
    print(f'Enriched leads: {len(enriched_leads)}')
    
    # Test enriched search with boolean value
    enriched_leads2 = db.search_leads({'enriched': 1})
    print(f'Enriched leads (with 1): {len(enriched_leads2)}')

if __name__ == '__main__':
    main()