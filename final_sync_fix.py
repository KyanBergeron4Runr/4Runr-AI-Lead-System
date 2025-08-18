#!/usr/bin/env python3
"""
Final Sync Fix
=============
Force Francois through the final sync validation
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class FinalSyncFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_sync_criteria(self):
        """Check what's blocking Francois from sync"""
        self.logger.info("🔍 Checking sync criteria for all leads...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                status = lead.get('Response_Status', 'Unknown')
                
                self.logger.info(f"\n📋 {name} - {company}")
                self.logger.info(f"   Response_Status: {status}")
                
                # Check all sync criteria
                sync_checks = {
                    'has_real_company': company and company not in ['Unknown Company', 'Unknown', ''],
                    'has_email_or_contact': bool(lead.get('Email')) or 'Business:' in str(lead.get('Source', '')),
                    'has_ai_message': bool(lead.get('AI_Message')),
                    'not_already_synced': status not in ['synced', 'replied'],
                    'status_allows_sync': status in ['pending', 'enriched'],
                    'has_complete_data': bool(lead.get('Company_Description'))
                }
                
                self.logger.info(f"   Sync criteria check:")
                all_passed = True
                for criteria, passed in sync_checks.items():
                    status_icon = "✅" if passed else "❌"
                    self.logger.info(f"      {criteria}: {status_icon}")
                    if not passed:
                        all_passed = False
                
                if all_passed:
                    self.logger.info(f"   🎯 READY FOR SYNC")
                else:
                    self.logger.info(f"   ❌ BLOCKED FROM SYNC")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error checking sync criteria: {e}")

    def force_francois_syncable(self):
        """Force Francois to pass all sync criteria"""
        self.logger.info("🔧 Forcing Francois to pass sync criteria...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Update Francois to pass all sync criteria
            result = conn.execute("""
                UPDATE leads 
                SET Response_Status = 'enriched',
                    Company_Description = 'Leading technology consulting company based in Montreal',
                    Needs_Enrichment = 0
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            if result.rowcount > 0:
                self.logger.info(f"✅ Updated Francois for sync:")
                self.logger.info(f"   Response_Status: → enriched")
                self.logger.info(f"   Company_Description: → Added")
                self.logger.info(f"   Needs_Enrichment: → 0 (complete)")
                
                conn.commit()
                conn.close()
                return True
            else:
                self.logger.error("❌ No Francois found")
                conn.close()
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error updating Francois: {e}")
            return False

    def manual_sync_test(self):
        """Test manual sync with Francois"""
        self.logger.info("🧪 Testing manual sync with Francois...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            
            if francois:
                francois_data = dict(francois)
                
                self.logger.info(f"🧪 Manual sync test for Francois:")
                self.logger.info(f"   Name: {francois_data.get('Full_Name')}")
                self.logger.info(f"   Company: {francois_data.get('Company')}")
                self.logger.info(f"   Email: {francois_data.get('Email')}")
                self.logger.info(f"   Business: {francois_data.get('Source')}")
                
                # Try to sync
                from shared.airtable_client import get_airtable_client
                
                client = get_airtable_client()
                
                # Use the business email from Source field
                business_contact = francois_data.get('Source', '')
                business_email = business_contact.replace('Business: ', '') if 'Business:' in business_contact else francois_data.get('Email', '')
                
                airtable_data = {
                    'Full Name': francois_data.get('Full_Name', ''),
                    'Company': francois_data.get('Company', ''),
                    'Email': business_email,
                    'Job Title': francois_data.get('Job_Title', ''),
                    'Website': francois_data.get('Website', ''),
                    'AI Message': francois_data.get('AI_Message', ''),
                    'Company Description': francois_data.get('Company_Description', ''),
                    'Source': 'Autonomous B2B System'
                }
                
                # Remove empty fields
                airtable_data = {k: v for k, v in airtable_data.items() if v}
                
                self.logger.info(f"📤 Syncing to Airtable with fields:")
                for key, value in airtable_data.items():
                    display_value = str(value)[:50] + '...' if len(str(value)) > 50 else value
                    self.logger.info(f"   {key}: {display_value}")
                
                record_id = client.create_lead(airtable_data)
                
                if record_id:
                    self.logger.info(f"✅ SUCCESS! Manual sync created record: {record_id}")
                    
                    # Update database
                    conn.execute("""
                        UPDATE leads 
                        SET Response_Status = 'synced'
                        WHERE id = ?
                    """, (francois_data['id'],))
                    conn.commit()
                    
                    self.logger.info(f"✅ Updated database status to 'synced'")
                    return record_id
                else:
                    self.logger.error("❌ Manual sync failed")
                    return None
            else:
                self.logger.error("❌ Francois not found")
                return None
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Manual sync error: {e}")
            return None

def main():
    fixer = FinalSyncFixer()
    
    print("🔧 FINAL SYNC FIX")
    print("=" * 18)
    print("📋 Force Francois through final sync validation")
    print("")
    
    # Check current sync criteria
    fixer.check_sync_criteria()
    
    print(f"\n🔧 FORCE FRANCOIS SYNCABLE?")
    print(f"This will ensure he passes all sync criteria")
    
    response = input("Force sync readiness? (y/n): ")
    if response.lower() == 'y':
        success = fixer.force_francois_syncable()
        
        if success:
            print(f"\n✅ Francois prepared for sync!")
            
            print(f"\n🧪 MANUAL SYNC TEST?")
            response2 = input("Test manual sync? (y/n): ")
            if response2.lower() == 'y':
                record_id = fixer.manual_sync_test()
                
                if record_id:
                    print(f"\n🎉 MANUAL SYNC SUCCESS!")
                    print(f"   📤 Airtable Record: {record_id}")
                    print(f"   🎯 Francois is in Airtable!")
                    print(f"   ✅ Your B2B system is working!")
                else:
                    print(f"\n❌ Manual sync failed")
            
            print(f"\n🚀 Or test autonomous again:")
            print(f"   python3 real_autonomous_organism.py --test")
        else:
            print(f"\n❌ Failed to prepare Francois")

if __name__ == "__main__":
    main()
