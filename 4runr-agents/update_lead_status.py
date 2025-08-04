#!/usr/bin/env python3
"""
Update a lead status for testing
"""

from database.lead_database import get_lead_database

def main():
    db = get_lead_database()
    leads = db.search_leads({'enriched': True})
    
    if leads:
        lead_id = leads[0]['id']
        lead_name = leads[0].get('full_name', 'Unknown')
        
        # Update to Ready for Outreach status
        success = db.update_lead(lead_id, {'status': 'Ready for Outreach'})
        
        if success:
            print(f'✅ Updated lead {lead_name} (ID: {lead_id[:8]}...) to Ready for Outreach status')
        else:
            print(f'❌ Failed to update lead {lead_id}')
    else:
        print('No enriched leads found')

if __name__ == '__main__':
    main()