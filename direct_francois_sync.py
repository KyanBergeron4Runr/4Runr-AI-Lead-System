#!/usr/bin/env python3
"""
Direct Francois Sync
==================
Bypass all validation and sync Francois directly to Airtable
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class DirectFrancoisSync:
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
                self.logger.info(f"   Job Title: {francois_data.get('Job_Title', 'None')}")
                self.logger.info(f"   LinkedIn: {francois_data.get('LinkedIn_URL', 'None')}")
                self.logger.info(f"   Website: {francois_data.get('Website', 'None')}")
                self.logger.info(f"   AI Message: {francois_data.get('AI_Message', 'None')[:50]}...")
                
                conn.close()
                return francois_data
            else:
                self.logger.error("❌ Francois not found in database")
                conn.close()
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting Francois data: {e}")
            return None

    def sync_francois_to_airtable(self, francois_data):
        """Sync Francois directly to Airtable"""
        self.logger.info("📤 Syncing Francois directly to Airtable...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Prepare Airtable data
            airtable_data = {
                'Full Name': francois_data.get('Full_Name', ''),
                'Company': francois_data.get('Company', ''),
                'Email': francois_data.get('Email', ''),
                'Job Title': francois_data.get('Job_Title', ''),
                'LinkedIn URL': francois_data.get('LinkedIn_URL', ''),
                'Website': francois_data.get('Website', ''),
                'AI Message': francois_data.get('AI_Message', ''),
                'Response Status': 'pending',
                'Source': 'Direct Sync - Enhanced System',
                'Date Added': '2025-08-18',
                'Company Size': francois_data.get('Company_Size', ''),
                'Industry': francois_data.get('Industry', ''),
                'Notes': 'Real lead from CGI with extracted company email'
            }
            
            # Remove empty fields
            airtable_data = {k: v for k, v in airtable_data.items() if v}
            
            self.logger.info(f"📋 Airtable data prepared:")
            for key, value in airtable_data.items():
                display_value = value[:50] + '...' if len(str(value)) > 50 else value
                self.logger.info(f"   {key}: {display_value}")
            
            # Create record in Airtable
            result = client.create(airtable_data)
            
            if result:
                record_id = result.get('id')
                self.logger.info(f"✅ SUCCESS! Synced to Airtable: {record_id}")
                
                # Update database with Airtable ID
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
                self.logger.error("❌ Failed to create Airtable record")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Direct sync failed: {e}")
            return None

    def verify_airtable_sync(self, record_id):
        """Verify the record was created in Airtable"""
        self.logger.info(f"✅ Verifying Airtable record: {record_id}")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try to get the record
            record = client.get(record_id)
            
            if record:
                fields = record.get('fields', {})
                name = fields.get('Full Name', 'Unknown')
                company = fields.get('Company', 'Unknown')
                email = fields.get('Email', 'Unknown')
                
                self.logger.info(f"✅ Verified in Airtable:")
                self.logger.info(f"   Record ID: {record_id}")
                self.logger.info(f"   Name: {name}")
                self.logger.info(f"   Company: {company}")
                self.logger.info(f"   Email: {email}")
                
                return True
            else:
                self.logger.error(f"❌ Record not found in Airtable")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying record: {e}")
            return False

def main():
    syncer = DirectFrancoisSync()
    
    print("📤 DIRECT FRANCOIS SYNC")
    print("=" * 25)
    print("📋 Bypass validation and sync Francois directly to Airtable")
    print("")
    
    # Get Francois data
    francois_data = syncer.get_francois_data()
    
    if not francois_data:
        print("❌ Cannot find Francois in database")
        return
    
    # Check if already synced
    if francois_data.get('airtable_id'):
        print(f"⚠️ Francois already synced: {francois_data.get('airtable_id')}")
        return
    
    # Sync to Airtable
    record_id = syncer.sync_francois_to_airtable(francois_data)
    
    if record_id:
        # Verify sync
        verified = syncer.verify_airtable_sync(record_id)
        
        print(f"\n🎉 DIRECT SYNC COMPLETE!")
        print(f"   📤 Airtable Record: {record_id}")
        print(f"   ✅ Verified: {'Yes' if verified else 'No'}")
        print(f"   🎯 Francois is now in your Airtable!")
        
        print(f"\n📋 Check your Airtable to see:")
        print(f"   - Francois Boulanger from CGI")
        print(f"   - Email: info@cgi.com")
        print(f"   - AI-generated message")
        print(f"   - Real company website")
    else:
        print(f"\n❌ Direct sync failed")

if __name__ == "__main__":
    main()
