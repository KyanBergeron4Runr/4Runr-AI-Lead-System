#!/usr/bin/env python3
"""
Show summary of what data is now in Airtable
"""

import json
from pathlib import Path

def show_airtable_summary():
    """Show what enriched data is now in Airtable"""
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    if not raw_leads_file.exists():
        print("❌ No raw_leads.json found")
        return
    
    try:
        with open(raw_leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        print("🎯 AIRTABLE DATA SUMMARY - Today's Enriched Leads")
        print("=" * 60)
        
        for i, lead in enumerate(leads, 1):
            name = lead.get('full_name', 'Unknown')
            title = lead.get('title', 'No title')
            company = lead.get('company', 'No company')
            email = lead.get('email', 'No email')
            website = lead.get('company_website', 'No website')
            linkedin = lead.get('linkedin_url', 'No LinkedIn')
            
            print(f"\n{i}. {name}")
            print(f"   📋 Job Title: {title}")
            print(f"   🏢 Company: {company}")
            print(f"   📧 Email: {email}")
            print(f"   🌐 Website: {website}")
            print(f"   🔗 LinkedIn: {linkedin}")
            print(f"   ✅ Synced to Airtable: {'Yes' if lead.get('airtable_synced') else 'No'}")
            
            # Show what's in Response Notes
            response_notes = []
            if website != 'No website':
                response_notes.append(f"Website: {website}")
            if lead.get('email_confidence'):
                response_notes.append(f"Email Confidence: {lead['email_confidence']}")
            if lead.get('enrichment_method'):
                response_notes.append(f"Enriched via: {lead['enrichment_method']}")
            
            if response_notes:
                print(f"   📝 Response Notes: {' | '.join(response_notes)}")
        
        # Summary stats
        total_leads = len(leads)
        with_emails = len([l for l in leads if l.get('email')])
        with_websites = len([l for l in leads if l.get('company_website')])
        with_titles = len([l for l in leads if l.get('title')])
        with_companies = len([l for l in leads if l.get('company')])
        synced = len([l for l in leads if l.get('airtable_synced')])
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Leads: {total_leads}")
        print(f"   ✅ Synced to Airtable: {synced}")
        print(f"   📧 With Emails: {with_emails}")
        print(f"   🌐 With Websites: {with_websites}")
        print(f"   📋 With Job Titles: {with_titles}")
        print(f"   🏢 With Companies: {with_companies}")
        
        completion_rate = ((with_emails + with_websites + with_titles + with_companies) / (total_leads * 4)) * 100
        print(f"   🎯 Data Completion: {completion_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    show_airtable_summary()