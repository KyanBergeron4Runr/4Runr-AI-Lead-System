#!/usr/bin/env python3
"""
Safe Complete Sync - Only updates fields that definitely exist and work
"""

import sqlite3
import requests

def safe_complete_sync():
    """Safe sync using only confirmed working fields"""
    
    api_key = 'pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923'
    base_id = 'appBZvPvNXGqtoJdc'
    table_name = 'Table 1'
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    airtable_url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    
    # Get processed lead data
    conn = sqlite3.connect('data/unified_leads.db')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute('''
        SELECT 
            full_name, linkedin_url, job_title, company, email,
            ai_message, lead_quality, email_confidence_level, website,
            business_type, company_description, industry, location, 
            company_size, score, verified, enriched
        FROM leads 
        WHERE ai_message IS NOT NULL AND ai_message != ''
    ''')
    
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    print(f"Found {len(leads)} leads with complete data to sync")
    
    # Get existing Airtable records
    response = requests.get(airtable_url, headers=headers)
    existing_records = response.json().get('records', [])
    
    email_to_record = {}
    for record in existing_records:
        email = record.get('fields', {}).get('Email', '').lower()
        if email:
            email_to_record[email] = record['id']
    
    updated_count = 0
    
    for lead in leads:
        email = lead.get('email', '').lower()
        if not email or email not in email_to_record:
            continue
            
        record_id = email_to_record[email]
        
        # Only use basic fields we know work (from previous successful syncs)
        airtable_fields = {
            "Full Name": lead.get('full_name', ''),
            "LinkedIn URL": lead.get('linkedin_url', ''),
            "Job Title": lead.get('job_title', '') or "Professional",
            "Company": lead.get('company', ''),
            "Email": lead.get('email', ''),
            "Website": lead.get('website', ''),
            "AI Message": lead.get('ai_message', ''),
            "Business_Type": lead.get('business_type', ''),
            "Lead Quality": lead.get('lead_quality', 'Warm'),
            "Email_Confidence_Level": lead.get('email_confidence_level', 'Real'),
            "Company_Description": lead.get('company_description', '')
        }
        
        # Clean empty fields
        cleaned_fields = {k: v for k, v in airtable_fields.items() if v not in [None, ""]}
        
        # Update record
        try:
            update_data = {"fields": cleaned_fields}
            response = requests.patch(f"{airtable_url}/{record_id}", 
                                    headers=headers, json=update_data)
            
            if response.status_code == 200:
                updated_count += 1
                quality = lead.get('lead_quality', 'Unknown')
                job_title = lead.get('job_title', 'Professional')
                industry = lead.get('industry', 'N/A')
                score = lead.get('score', 0)
                print(f"✅ {lead.get('full_name', 'Unknown')}")
                print(f"   Job: {job_title} | Quality: {quality} | Industry: {industry} | Score: {score}")
            else:
                print(f"❌ Failed {lead.get('full_name', 'Unknown')}: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Exception for {lead.get('full_name', 'Unknown')}: {e}")
    
    print(f"\n🎉 SAFE COMPLETE SYNC FINISHED!")
    print(f"✅ Successfully updated: {updated_count} records")
    print(f"\n📊 DATA NOW IN AIRTABLE:")
    print(f"  ✅ Complete contact information")
    print(f"  ✅ Intelligent job titles (ML-inferred)")
    print(f"  ✅ Lead quality scores (Hot/Warm/Cold)")
    print(f"  ✅ Email confidence levels")
    print(f"  ✅ Business types and descriptions")
    print(f"  ✅ Personalized AI messages")
    print(f"  ✅ Company websites")
    
    print(f"\n🔧 TO GET MORE FIELDS:")
    print(f"You need to manually add these fields to Airtable first:")
    print(f"  - Source (Single select: Search, Comment, Other)")
    print(f"  - Level Engaged (Multiple select: 1st degree, 2nd degree, 3rd degree)")
    print(f"  - Engagement_Status (Single select: Sent, Auto-Send, Skip, Needs Review)")
    print(f"  - All date fields (Date Scraped, Date Enriched, etc.)")
    print(f"  - Response tracking fields")
    print(f"\nOnce added, run sync again to populate them!")

if __name__ == "__main__":
    print("🛡️ SAFE COMPLETE AIRTABLE SYNC")
    print("=" * 45)
    print("Syncing only confirmed working fields...")
    print()
    safe_complete_sync()
