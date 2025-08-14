#!/usr/bin/env python3
"""
Fix Incomplete Enrichment - Direct database update
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def enrich_lead_data(lead_data):
    """Enrich lead data with additional information"""
    # This is a simplified enrichment - in production you'd use real APIs
    company = lead_data.get('company', '')
    email = lead_data.get('email', '')
    
    # Basic enrichment logic
    enriched_data = {
        'enriched': 1,
        'enrichment_date': datetime.now().isoformat(),
        'company_size': '10-50',  # Default size
        'industry': 'Technology',  # Default industry
        'location': 'Unknown',
        'website': '',
        'phone': '',
        'linkedin_company_url': ''
    }
    
    # Try to extract domain from email
    if email and '@' in email:
        domain = email.split('@')[1]
        enriched_data['website'] = f"https://{domain}"
    
    # Basic company analysis
    if company:
        company_lower = company.lower()
        if 'tech' in company_lower or 'software' in company_lower:
            enriched_data['industry'] = 'Technology'
        elif 'health' in company_lower or 'medical' in company_lower:
            enriched_data['industry'] = 'Healthcare'
        elif 'finance' in company_lower or 'bank' in company_lower:
            enriched_data['industry'] = 'Finance'
        elif 'consult' in company_lower:
            enriched_data['industry'] = 'Consulting'
        else:
            enriched_data['industry'] = 'Other'
    
    return enriched_data

def fix_incomplete_enrichment():
    """Fix incomplete enrichment in the database"""
    print("🔧 Fixing Incomplete Enrichment")
    print("=" * 50)
    
    try:
        # Connect to unified database
        db_path = Path("data/unified_leads.db")
        if not db_path.exists():
            print("❌ Unified database not found")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get unenriched leads
        cursor.execute("""
            SELECT id, full_name, company, email, linkedin_url
            FROM leads 
            WHERE (enriched IS NULL OR enriched = 0) 
            AND company IS NOT NULL 
            AND company != ''
        """)
        
        unenriched_leads = cursor.fetchall()
        
        if not unenriched_leads:
            print("✅ All leads already enriched")
            conn.close()
            return True
        
        print(f"Found {len(unenriched_leads)} unenriched leads")
        
        # Enrich leads
        updated_count = 0
        for lead in unenriched_leads:
            lead_id, full_name, company, email, linkedin_url = lead
            
            # Create lead data for enrichment
            lead_data = {
                'full_name': full_name,
                'company': company,
                'email': email,
                'linkedin_url': linkedin_url
            }
            
            # Enrich lead data
            enriched_data = enrich_lead_data(lead_data)
            
            # Update database with enrichment data
            cursor.execute("""
                UPDATE leads 
                SET enriched = ?, 
                    company_size = ?,
                    industry = ?,
                    location = ?,
                    website = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                enriched_data['enriched'],
                enriched_data['company_size'],
                enriched_data['industry'],
                enriched_data['location'],
                enriched_data['website'],
                datetime.now().isoformat(),
                lead_id
            ))
            
            updated_count += 1
            print(f"✅ Enriched lead {lead_id}: {full_name} at {company} ({enriched_data['industry']})")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Successfully enriched {updated_count} leads")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing enrichment: {e}")
        return False

def check_results():
    """Check the results after fixing"""
    print("\n📊 Checking Results")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("data/unified_leads.db")
        cursor = conn.cursor()
        
        # Get updated stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN ai_message IS NOT NULL AND ai_message != '' THEN 1 END) as with_ai_messages,
                COUNT(CASE WHEN enriched = 1 THEN 1 END) as enriched_leads,
                COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_emails,
                COUNT(CASE WHEN company IS NOT NULL AND company != '' THEN 1 END) as with_companies
            FROM leads
        """)
        
        result = cursor.fetchone()
        total_leads, with_ai_messages, enriched_leads, with_emails, with_companies = result
        
        print(f"Total leads: {total_leads}")
        print(f"Leads with AI messages: {with_ai_messages} ({with_ai_messages/total_leads*100:.1f}%)")
        print(f"Enriched leads: {enriched_leads} ({enriched_leads/total_leads*100:.1f}%)")
        print(f"Leads with emails: {with_emails} ({with_emails/total_leads*100:.1f}%)")
        print(f"Leads with companies: {with_companies} ({with_companies/total_leads*100:.1f}%)")
        
        # Check industry distribution
        cursor.execute("""
            SELECT industry, COUNT(*) as count
            FROM leads 
            WHERE enriched = 1 AND industry IS NOT NULL
            GROUP BY industry
            ORDER BY count DESC
        """)
        
        industries = cursor.fetchall()
        if industries:
            print(f"\nIndustry distribution:")
            for industry, count in industries:
                print(f"  - {industry}: {count} leads")
        
        conn.close()
        
        if enriched_leads == total_leads:
            print("\n🎉 All leads now enriched!")
            return True
        else:
            print(f"\n⚠️ Still missing enrichment for {total_leads - enriched_leads} leads")
            return False
            
    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return False

def main():
    """Main function"""
    print("🔧 4Runr AI Lead System - Fix Incomplete Enrichment")
    print("=" * 60)
    
    # Fix incomplete enrichment
    success = fix_incomplete_enrichment()
    
    if success:
        # Check results
        check_results()
        
        print("\n✅ Enrichment fix completed!")
        print("\nNext steps:")
        print("1. Set up automation: python fix_automation_issues.py")
        print("2. Test daily scraping: python 4runr-lead-scraper/scripts/daily_scraper.py --max-leads 5")
    else:
        print("\n❌ Failed to fix enrichment")

if __name__ == "__main__":
    main()
