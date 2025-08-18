#!/usr/bin/env python3
"""
Fix Direct Sync Method
=====================
Fix the Airtable client method call for Francois sync
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class FixedFrancoisSync:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def get_francois_data(self):
        """Get Francois data from database"""
        self.logger.info("📋 Getting Francois data...")
        
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
                
                self.logger.info(f"✅ Found Francois:")
                self.logger.info(f"   Name: {francois_data.get('Full_Name', 'Unknown')}")
                self.logger.info(f"   Company: {francois_data.get('Company', 'Unknown')}")
                self.logger.info(f"   Email: {francois_data.get('Email', 'None')}")
                self.logger.info(f"   AI Message: {'✅ Present' if francois_data.get('AI_Message') else '❌ Missing'}")
                
                conn.close()
                return francois_data
            else:
                self.logger.error("❌ Francois not found in database")
                conn.close()
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting Francois data: {e}")
            return None

    def sync_francois_fixed(self, francois_data):
        """Sync Francois using correct Airtable client method"""
        self.logger.info("📤 Syncing Francois with correct method...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Prepare data using client's expected field mapping
            airtable_fields = {
                'Full Name': francois_data.get('Full_Name', ''),
                'Company': francois_data.get('Company', ''),
                'Email': francois_data.get('Email', ''),
                'Job Title': francois_data.get('Job_Title', ''),
                'LinkedIn URL': francois_data.get('LinkedIn_URL', ''),
                'Website': francois_data.get('Website', ''),
                'AI Message': francois_data.get('AI_Message', ''),
                'Response Status': 'pending',
                'Source': 'Enhanced System - Direct Sync',
                'Notes': 'Real CGI lead with extracted company email'
            }
            
            # Remove empty fields
            airtable_fields = {k: v for k, v in airtable_fields.items() if v}
            
            self.logger.info(f"📋 Syncing with fields:")
            for key, value in airtable_fields.items():
                display_value = str(value)[:50] + '...' if len(str(value)) > 50 else value
                self.logger.info(f"   {key}: {display_value}")
            
            # Use the correct method name
            record_id = client.create_lead(airtable_fields)
            
            if record_id:
                self.logger.info(f"✅ SUCCESS! Created Airtable record: {record_id}")
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    UPDATE leads 
                    SET airtable_id = ?, Response_Status = 'synced'
                    WHERE id = ?
                """, (record_id, francois_data['id']))
                conn.commit()
                conn.close()
                
                self.logger.info(f"✅ Updated database with Airtable ID")
                return record_id
            else:
                self.logger.error("❌ create_lead returned None")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Sync failed: {e}")
            
            # Try to inspect the client methods
            try:
                from shared.airtable_client import get_airtable_client
                client = get_airtable_client()
                
                self.logger.info(f"🔍 Available client methods:")
                methods = [method for method in dir(client) if not method.startswith('_')]
                for method in methods:
                    self.logger.info(f"   - {method}")
                    
            except Exception as inspect_error:
                self.logger.error(f"❌ Could not inspect client: {inspect_error}")
            
            return None

    def check_if_already_synced(self, francois_data):
        """Check if Francois is already in Airtable"""
        airtable_id = francois_data.get('airtable_id')
        
        if airtable_id:
            self.logger.info(f"⚠️ Francois already synced to: {airtable_id}")
            return True
        
        return False

def main():
    syncer = FixedFrancoisSync()
    
    print("🔧 FIXED FRANCOIS SYNC")
    print("=" * 22)
    print("📋 Use correct Airtable client method")
    print("")
    
    # Get Francois data
    francois_data = syncer.get_francois_data()
    
    if not francois_data:
        print("❌ Cannot find Francois in database")
        return
    
    # Check if already synced
    if syncer.check_if_already_synced(francois_data):
        print("✅ Francois already synced to Airtable!")
        return
    
    # Sync with correct method
    record_id = syncer.sync_francois_fixed(francois_data)
    
    if record_id:
        print(f"\n🎉 SYNC SUCCESSFUL!")
        print(f"   📤 Airtable Record ID: {record_id}")
        print(f"   🎯 Check your Airtable for Francois Boulanger!")
        print(f"   📧 Email: info@cgi.com")
        print(f"   🏢 Company: CGI")
    else:
        print(f"\n❌ Sync failed - check logs for details")

if __name__ == "__main__":
    main()
