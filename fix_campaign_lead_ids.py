#!/usr/bin/env python3
"""Fix campaign lead IDs to match real leads"""

import sqlite3

def main():
    # Connect to both databases
    campaign_conn = sqlite3.connect('4runr-outreach-system/campaign_system/campaigns.db')
    leads_conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
    
    # Get real lead IDs with emails
    leads_cursor = leads_conn.execute("SELECT id, email, company FROM leads WHERE email IS NOT NULL LIMIT 5")
    real_leads = leads_cursor.fetchall()
    
    print("Real leads available:")
    for lead in real_leads:
        print(f"  {lead[0][:8]}... - {lead[1]} ({lead[2]})")
    
    # Update campaigns with real lead IDs
    campaign_cursor = campaign_conn.execute("SELECT campaign_id, lead_id, company FROM campaigns")
    campaigns = campaign_cursor.fetchall()
    
    print(f"\nUpdating {len(campaigns)} campaigns with real lead IDs...")
    
    for i, (campaign_id, old_lead_id, company) in enumerate(campaigns):
        if i < len(real_leads):
            new_lead_id = real_leads[i][0]
            
            # Update campaign
            campaign_conn.execute("""
                UPDATE campaigns 
                SET lead_id = ? 
                WHERE campaign_id = ?
            """, (new_lead_id, campaign_id))
            
            print(f"  ✅ Updated campaign {campaign_id[:8]}... to use lead {new_lead_id[:8]}...")
    
    campaign_conn.commit()
    
    # Verify the update
    cursor = campaign_conn.execute("SELECT campaign_id, lead_id FROM campaigns")
    updated_campaigns = cursor.fetchall()
    
    print(f"\n✅ Updated {len(updated_campaigns)} campaigns")
    print("Updated campaign-lead mappings:")
    for campaign_id, lead_id in updated_campaigns:
        print(f"  {campaign_id[:8]}... → {lead_id[:8]}...")
    
    campaign_conn.close()
    leads_conn.close()

if __name__ == "__main__":
    main()