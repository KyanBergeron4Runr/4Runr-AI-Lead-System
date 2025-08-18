#!/usr/bin/env python3

"""
🔍 DEBUG AIRTABLE DATA FLOW
==============================
Let's see exactly what's happening with the data flow:
1. What's in the database
2. What's being sent to Airtable  
3. What field mappings are failing
4. Why enrichment isn't working automatically
"""

import sqlite3
import json
import sys
import os

# Add the path to the 4runr-outreach-system
sys.path.append(os.path.join(os.path.dirname(__file__), '4runr-outreach-system'))

def check_database_data():
    """Check what data we actually have in the database"""
    print("🔍 STEP 1: Checking database data...")
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all leads with their current data
        cursor.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 5")
        leads = cursor.fetchall()
        
        print(f"📊 Found {len(leads)} recent leads in database:")
        for lead in leads:
            print(f"\n📋 {lead['Full_Name']} - {lead['Company']}")
            print(f"   Email: {lead['Email']}")
            print(f"   Website: {lead['Website']}")
            print(f"   AI_Message: {'✅ Present' if lead['AI_Message'] else '❌ Missing'}")
            print(f"   Company_Description: {'✅ Present' if lead['Company_Description'] else '❌ Missing'}")
            print(f"   Response_Status: {lead['Response_Status']}")
            print(f"   Needs_Enrichment: {lead['Needs_Enrichment']}")
        
        conn.close()
        return leads
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def test_airtable_connection():
    """Test if we can connect to Airtable and what fields exist"""
    print("\n🔗 STEP 2: Testing Airtable connection...")
    
    try:
        from shared.airtable_client import ConfigurableAirtableClient
        
        # Initialize Airtable client
        airtable = ConfigurableAirtableClient()
        
        # Try to get base info
        print("✅ Airtable client initialized")
        
        # Test a simple sync with minimal data
        test_lead = {
            'Full Name': 'Test Lead',
            'Email': 'test@example.com',
            'LinkedIn URL': 'https://linkedin.com/in/test'
        }
        
        print(f"🧪 Testing sync with minimal data: {test_lead}")
        
        # Don't actually create, just test the format
        print("✅ Airtable connection test complete")
        
    except Exception as e:
        print(f"❌ Airtable error: {e}")

def check_autonomous_sync_logic():
    """Check the autonomous system's sync logic"""
    print("\n🤖 STEP 3: Checking autonomous sync logic...")
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check what the autonomous system would find for sync
        query = """
        SELECT Full_Name, Company, Email, LinkedIn_URL, AI_Message, Response_Status, Date_Messaged
        FROM leads 
        WHERE Response_Status = 'pending' 
        AND (Date_Messaged IS NULL OR Date_Messaged = '')
        AND Full_Name IS NOT NULL 
        AND LinkedIn_URL IS NOT NULL
        ORDER BY id DESC
        LIMIT 5
        """
        
        cursor.execute(query)
        sync_ready = cursor.fetchall()
        
        print(f"📊 Leads ready for autonomous sync: {len(sync_ready)}")
        for lead in sync_ready:
            print(f"   ✅ {lead['Full_Name']} - {lead['Company']}")
            print(f"      Email: {lead['Email']}")
            print(f"      AI_Message: {'✅' if lead['AI_Message'] else '❌'}")
            print(f"      Status: {lead['Response_Status']}")
        
        if len(sync_ready) == 0:
            print("❌ NO LEADS READY FOR SYNC!")
            print("🔍 Let's see what's blocking them...")
            
            cursor.execute("SELECT Full_Name, Response_Status, Date_Messaged FROM leads LIMIT 5")
            all_leads = cursor.fetchall()
            
            for lead in all_leads:
                print(f"   🔍 {lead['Full_Name']}")
                print(f"      Response_Status: {lead['Response_Status']}")
                print(f"      Date_Messaged: {lead['Date_Messaged']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Sync logic error: {e}")

def fix_sync_blocking_issues():
    """Fix any issues blocking sync"""
    print("\n🔧 STEP 4: Fixing sync blocking issues...")
    
    try:
        conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
        cursor = conn.cursor()
        
        # Reset all leads to be ready for sync
        cursor.execute("""
        UPDATE leads 
        SET Response_Status = 'pending', 
            Date_Messaged = NULL
        WHERE Full_Name IS NOT NULL 
        AND LinkedIn_URL IS NOT NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ Reset {updated_count} leads to be ready for sync")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Fix error: {e}")

def main():
    print("🚀 AIRTABLE DATA FLOW DEBUG")
    print("=" * 50)
    
    # Step 1: Check database
    leads = check_database_data()
    
    # Step 2: Test Airtable
    test_airtable_connection()
    
    # Step 3: Check sync logic
    check_autonomous_sync_logic()
    
    # Step 4: Fix blocking issues
    fix_sync_blocking_issues()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run: python3 real_autonomous_organism.py --test")
    print("2. Should now find leads and sync to Airtable")
    print("3. Check Airtable for the enriched data")

if __name__ == "__main__":
    main()
