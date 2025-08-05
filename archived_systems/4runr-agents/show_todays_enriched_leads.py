#!/usr/bin/env python3
"""
Show today's enriched leads
"""

import json
from pathlib import Path
from datetime import datetime

def show_todays_leads():
    """Show leads enriched today"""
    shared_dir = Path(__file__).parent / "shared"
    enriched_file = shared_dir / "enriched_leads.json"
    
    if not enriched_file.exists():
        print("❌ No enriched_leads.json found")
        return
    
    try:
        with open(enriched_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        today = "2025-07-31"
        todays_leads = []
        
        for lead in leads:
            enriched_at = lead.get('enriched_at', '')
            if today in enriched_at and lead.get('enrichment_method') == 'comprehensive_serpapi_enricher':
                todays_leads.append(lead)
        
        print(f"📋 Today's Enriched Leads ({len(todays_leads)}):")
        print("=" * 50)
        
        for i, lead in enumerate(todays_leads, 1):
            name = lead.get('full_name') or lead.get('name', 'Unknown')
            title = lead.get('title', 'No title')
            company = lead.get('company', 'No company')
            email = lead.get('email', 'No email')
            website = lead.get('company_website', 'No website')
            
            print(f"\n{i}. {name}")
            print(f"   📋 Title: {title}")
            print(f"   🏢 Company: {company}")
            print(f"   🌐 Website: {website}")
            print(f"   📧 Email: {email}")
            print(f"   🔗 LinkedIn: {lead.get('linkedin_url', 'No LinkedIn')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    show_todays_leads()