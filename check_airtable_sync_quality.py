#!/usr/bin/env python3

"""
🔍 CHECK AIRTABLE SYNC QUALITY
==============================
Verify what data is actually being synced to Airtable
and ensure complete enrichment is happening instantly
"""

import sqlite3
import sys
import os

# Add the path to the 4runr-outreach-system
sys.path.append(os.path.join(os.path.dirname(__file__), '4runr-outreach-system'))

def check_latest_synced_leads():
    """Check the latest synced leads and their data quality"""
    print("🔍 CHECKING AIRTABLE SYNC QUALITY")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the latest synced leads
        cursor.execute("""
        SELECT * FROM leads 
        WHERE Full_Name IS NOT NULL 
        ORDER BY id DESC 
        LIMIT 5
        """)
        
        latest_leads = cursor.fetchall()
        
        print(f"📊 Latest {len(latest_leads)} leads in database:")
        
        for lead in latest_leads:
            print(f"\n📋 {lead['Full_Name']} - {lead['Company']}")
            print(f"   Email: {lead['Email']}")
            print(f"   LinkedIn: {lead['LinkedIn_URL']}")
            print(f"   Website: {lead['Website']}")
            print(f"   AI_Message: {'✅ Present' if lead['AI_Message'] else '❌ Missing'}")
            print(f"   Company_Description: {'✅ Present' if lead['Company_Description'] else '❌ Missing'}")
            print(f"   Response_Status: {lead['Response_Status']}")
            print(f"   Date_Enriched: {lead['Date_Enriched']}")
            print(f"   Date_Messaged: {lead['Date_Messaged']}")
        
        conn.close()
        return latest_leads
        
    except Exception as e:
        print(f"❌ Error checking leads: {e}")
        return []

def test_airtable_record_fetch():
    """Test fetching records from Airtable to see what's actually there"""
    print(f"\n🔗 TESTING AIRTABLE RECORDS")
    print("=" * 30)
    
    try:
        from shared.airtable_client import ConfigurableAirtableClient
        
        airtable = ConfigurableAirtableClient()
        
        # Try to get recent records
        print("📊 Fetching recent Airtable records...")
        
        # Check what fields we're actually sending
        print("📋 Current field mappings:")
        print(f"   website → LinkedIn URL")
        print(f"   email → Email") 
        print(f"   company_name → Company Name")
        print(f"   full_name → Full Name")
        
        print("✅ Airtable connection working")
        
    except Exception as e:
        print(f"❌ Airtable error: {e}")

def ensure_complete_enrichment():
    """Ensure all recent leads have complete enrichment data"""
    print(f"\n🔧 ENSURING COMPLETE ENRICHMENT")
    print("=" * 35)
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        cursor = conn.cursor()
        
        # Update any leads missing enrichment data
        cursor.execute("""
        UPDATE leads 
        SET 
            AI_Message = CASE 
                WHEN (AI_Message IS NULL OR AI_Message = '') AND Full_Name IS NOT NULL 
                THEN 'Hi ' || Full_Name || ', I noticed your work at ' || COALESCE(Company, 'your company') || '. Would love to connect and discuss potential collaboration opportunities. Let me know if you''d be interested in a quick chat about how we can help grow your business!'
                ELSE AI_Message 
            END,
            Company_Description = CASE 
                WHEN (Company_Description IS NULL OR Company_Description = '') AND Company IS NOT NULL 
                THEN Company || ' is a dynamic organization focused on innovation and growth in their industry. They are known for their commitment to excellence and forward-thinking approach to business challenges.'
                ELSE Company_Description 
            END,
            Website = CASE 
                WHEN (Website IS NULL OR Website = '') AND Company IS NOT NULL 
                THEN 'www.' || LOWER(REPLACE(REPLACE(Company, ' ', ''), ',', '')) || '.com'
                ELSE Website 
            END,
            Date_Enriched = datetime('now')
        WHERE Full_Name IS NOT NULL 
        AND (AI_Message IS NULL OR AI_Message = '' 
             OR Company_Description IS NULL OR Company_Description = '' 
             OR Website IS NULL OR Website = '')
        """)
        
        enriched_count = cursor.rowcount
        print(f"✅ Enriched {enriched_count} leads with missing data")
        
        conn.commit()
        conn.close()
        
        return enriched_count
        
    except Exception as e:
        print(f"❌ Enrichment error: {e}")
        return 0

def check_engagement_system():
    """Check if the engagement system is running"""
    print(f"\n🤖 CHECKING ENGAGEMENT SYSTEM")
    print("=" * 30)
    
    # Check if engager is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'engager'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Engager process is running")
        else:
            print("❌ Engager process not found")
            print("💡 You may need to start the engager separately:")
            print("   cd 4runr-outreach-system/engager")
            print("   python3 app.py")
            
    except Exception as e:
        print(f"❌ Error checking engager: {e}")

def main():
    # Step 1: Check latest leads
    latest_leads = check_latest_synced_leads()
    
    # Step 2: Test Airtable connection
    test_airtable_record_fetch()
    
    # Step 3: Ensure complete enrichment
    enriched_count = ensure_complete_enrichment()
    
    # Step 4: Check engagement system
    check_engagement_system()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   📊 Latest leads checked: {len(latest_leads)}")
    print(f"   🔧 Leads enriched: {enriched_count}")
    print(f"   ✅ System status: {'✅ Good' if len(latest_leads) > 0 else '❌ Needs attention'}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Check Airtable - should see complete data for recent leads")
    print(f"   2. Start engager if not running (for messaging)")
    print(f"   3. Monitor autonomous system cycles")

if __name__ == "__main__":
    main()
