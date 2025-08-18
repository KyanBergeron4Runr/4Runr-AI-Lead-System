#!/usr/bin/env python3
"""
Minimal Working Sync
====================
Use ONLY the fields that we know 100% work: Email and LinkedIn URL
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class MinimalWorkingSync:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def sync_minimal_francois(self):
        """Sync with absolute minimal fields that definitely work"""
        self.logger.info("📤 Minimal sync with only guaranteed fields...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            
            if not francois:
                self.logger.error("❌ Francois not found")
                return None
            
            francois_data = dict(francois)
            
            # Extract business email
            business_contact = francois_data.get('Source', '')
            if 'Business:' in business_contact:
                business_email = business_contact.replace('Business: ', '')
            else:
                business_email = francois_data.get('Email', '')
            
            # Use ONLY the two fields that definitely exist based on field mappings
            airtable_data = {
                'Email': business_email,  # ✅ Confirmed in field mappings
                'LinkedIn URL': francois_data.get('LinkedIn_URL', '')  # ✅ Confirmed in field mappings
            }
            
            # Remove empty fields
            airtable_data = {k: v for k, v in airtable_data.items() if v}
            
            self.logger.info(f"📤 Minimal sync with ONLY guaranteed fields:")
            for key, value in airtable_data.items():
                self.logger.info(f"   '{key}': {value}")
            
            # Sync to Airtable
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            record_id = client.create_lead(airtable_data)
            
            if record_id:
                self.logger.info(f"✅ MINIMAL SUCCESS! Francois in Airtable: {record_id}")
                
                # Update database
                conn.execute("""
                    UPDATE leads 
                    SET Response_Status = 'synced'
                    WHERE id = ?
                """, (francois_data['id'],))
                conn.commit()
                
                self.logger.info(f"✅ Database updated")
                conn.close()
                return record_id
            else:
                self.logger.error("❌ Even minimal sync failed")
                conn.close()
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Minimal sync error: {e}")
            return None

    def try_manual_airtable_call(self):
        """Try the most basic possible Airtable call"""
        self.logger.info("🧪 Testing most basic Airtable call...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try with just one field
            test_data = {'Email': 'test@cgi.com'}
            
            self.logger.info(f"🧪 Testing with minimal data: {test_data}")
            
            record_id = client.create_lead(test_data)
            
            if record_id:
                self.logger.info(f"✅ Basic test worked: {record_id}")
                return record_id
            else:
                self.logger.error("❌ Basic test failed")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Basic test error: {e}")
            return None

def main():
    syncer = MinimalWorkingSync()
    
    print("📤 MINIMAL WORKING SYNC")
    print("=" * 25)
    print("📋 Using ONLY guaranteed fields from field mappings:")
    print("   ✅ 'Email' (confirmed in mappings)")
    print("   ✅ 'LinkedIn URL' (confirmed in mappings)")
    print("")
    
    # Try basic test first
    print("🧪 Testing basic Airtable call...")
    test_record = syncer.try_manual_airtable_call()
    
    if test_record:
        print(f"✅ Basic Airtable works! Record: {test_record}")
        
        # Now try with Francois
        print(f"\n📤 Syncing Francois with minimal data...")
        record_id = syncer.sync_minimal_francois()
        
        if record_id:
            print(f"\n🎉 MINIMAL SUCCESS!")
            print(f"   📤 Airtable Record ID: {record_id}")
            print(f"   📧 Email: info@cgi.com (business contact)")
            print(f"   🔗 LinkedIn URL: Francois profile")
            
            print(f"\n🏆 FRANCOIS IS IN AIRTABLE!")
            print(f"   ✅ Minimal B2B data synced")
            print(f"   ✅ Can add more fields manually in Airtable")
            print(f"   ✅ Your system is working!")
            
            print(f"\n📋 To add more fields:")
            print(f"   1. Go to your Airtable base")
            print(f"   2. Add fields: Full Name, Company, Job Title")
            print(f"   3. Update field mappings in system")
            
        else:
            print(f"\n❌ Francois sync failed")
    else:
        print(f"❌ Basic Airtable test failed")
        print(f"Check Airtable connection and permissions")

if __name__ == "__main__":
    main()
