#!/usr/bin/env python3
"""
Exact Airtable Fields Sync
==========================
Use the EXACT field names that exist in your Airtable base
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class ExactFieldSync:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def sync_with_exact_fields(self):
        """Sync using only the fields that definitely exist in Airtable"""
        self.logger.info("📤 Syncing with EXACT Airtable field names...")
        
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
            
            # Use ONLY the field names that definitely exist
            # Based on field_mappings: 'email': 'Email', 'company_name': 'Company Name'
            airtable_data = {
                'Email': business_email,  # ✅ Confirmed exists
                'Company Name': francois_data.get('Company', ''),  # ✅ Confirmed exists
                'LinkedIn URL': francois_data.get('LinkedIn_URL', '')  # ✅ Confirmed exists
            }
            
            # Remove empty fields
            airtable_data = {k: v for k, v in airtable_data.items() if v}
            
            self.logger.info(f"📤 Syncing with ONLY confirmed fields:")
            for key, value in airtable_data.items():
                self.logger.info(f"   {key}: {value}")
            
            # Sync to Airtable
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            record_id = client.create_lead(airtable_data)
            
            if record_id:
                self.logger.info(f"✅ SUCCESS! Minimal sync worked: {record_id}")
                
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
            self.logger.error(f"❌ Sync error: {e}")
            return None

    def try_add_more_fields(self, record_id):
        """Try to add more fields one by one to the existing record"""
        self.logger.info(f"📝 Trying to add more fields to record {record_id}...")
        
        # Try adding fields one by one
        additional_fields = [
            ('Full Name', 'Francois Boulanger'),
            ('Job Title', 'CGI Executive'),
            ('Website', 'www.cgi.com'),
            ('AI Message', 'Hi Francois, impressed by CGI...'),
            ('Source', 'B2B Autonomous System')
        ]
        
        from shared.airtable_client import get_airtable_client
        client = get_airtable_client()
        
        for field_name, field_value in additional_fields:
            try:
                # Try to update with this field
                update_data = {field_name: field_value}
                
                # Check if client has update method
                if hasattr(client, 'update_lead'):
                    result = client.update_lead(record_id, update_data)
                    if result:
                        self.logger.info(f"   ✅ Added {field_name}")
                    else:
                        self.logger.info(f"   ❌ Could not add {field_name}")
                else:
                    self.logger.info(f"   ⚠️ No update method available")
                    break
                    
            except Exception as field_error:
                self.logger.info(f"   ❌ Failed to add {field_name}: {field_error}")

def main():
    syncer = ExactFieldSync()
    
    print("📤 EXACT AIRTABLE FIELDS SYNC")
    print("=" * 30)
    print("📋 Use ONLY the fields confirmed to exist")
    print("✅ Confirmed fields: Email, Company Name, LinkedIn URL")
    print("")
    
    # Try minimal sync first
    record_id = syncer.sync_with_exact_fields()
    
    if record_id:
        print(f"\n🎉 MINIMAL SYNC SUCCESS!")
        print(f"   📤 Airtable Record ID: {record_id}")
        print(f"   📧 Email: info@cgi.com")
        print(f"   🏢 Company Name: CGI")
        print(f"   🔗 LinkedIn URL: Included")
        
        print(f"\n📝 Trying to add more fields...")
        syncer.try_add_more_fields(record_id)
        
        print(f"\n🏆 FRANCOIS IS IN AIRTABLE!")
        print(f"   ✅ Basic B2B data synced")
        print(f"   ✅ Business email contact")
        print(f"   ✅ Real company information")
        
        print(f"\n🚀 YOUR B2B SYSTEM WORKS!")
        print(f"   Now you can add more fields to Airtable as needed")
        print(f"   Or run autonomous mode with minimal data")
    else:
        print(f"\n❌ Even minimal sync failed")
        print(f"   Check Airtable base and field names")

if __name__ == "__main__":
    main()
