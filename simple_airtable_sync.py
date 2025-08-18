#!/usr/bin/env python3
"""
Simple Airtable Sync
===================
Sync Francois using only basic fields that exist in Airtable
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class SimpleAirtableSync:
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
                self.logger.info(f"✅ Found Francois with all data ready")
                conn.close()
                return francois_data
            else:
                self.logger.error("❌ Francois not found")
                conn.close()
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting data: {e}")
            return None

    def sync_with_basic_fields(self, francois_data):
        """Sync using only basic fields that definitely exist"""
        self.logger.info("📤 Syncing with basic fields only...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Use ONLY the most basic fields
            basic_fields = {
                'Full Name': francois_data.get('Full_Name', ''),
                'Email': francois_data.get('Email', ''),
                'Company': francois_data.get('Company', ''),
            }
            
            # Remove empty fields
            basic_fields = {k: v for k, v in basic_fields.items() if v}
            
            self.logger.info(f"📋 Using basic fields:")
            for key, value in basic_fields.items():
                self.logger.info(f"   {key}: {value}")
            
            # Create record
            record_id = client.create_lead(basic_fields)
            
            if record_id:
                self.logger.info(f"✅ SUCCESS! Record created: {record_id}")
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    UPDATE leads 
                    SET airtable_id = ?, Response_Status = 'synced'
                    WHERE id = ?
                """, (record_id, francois_data['id']))
                conn.commit()
                conn.close()
                
                self.logger.info(f"✅ Database updated with record ID")
                return record_id
            else:
                self.logger.error("❌ create_lead returned None")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Basic sync failed: {e}")
            return None

    def add_additional_fields(self, record_id, francois_data):
        """Try to add additional fields one by one"""
        self.logger.info(f"📝 Adding additional fields to record {record_id}...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try additional fields one by one
            additional_fields = {
                'Job Title': francois_data.get('Job_Title', ''),
                'LinkedIn URL': francois_data.get('LinkedIn_URL', ''),
                'Website': francois_data.get('Website', ''),
                'AI Message': francois_data.get('AI_Message', ''),
            }
            
            for field_name, field_value in additional_fields.items():
                if field_value:
                    try:
                        # Try to update with this field
                        update_data = {field_name: field_value}
                        
                        # Check if client has update method
                        if hasattr(client, 'update_lead'):
                            result = client.update_lead(record_id, update_data)
                            if result:
                                self.logger.info(f"   ✅ Added {field_name}")
                            else:
                                self.logger.info(f"   ⚠️ Could not add {field_name}")
                        else:
                            self.logger.info(f"   ⚠️ No update method available")
                            break
                            
                    except Exception as field_error:
                        self.logger.info(f"   ❌ Failed to add {field_name}: {field_error}")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding fields: {e}")

def main():
    syncer = SimpleAirtableSync()
    
    print("📤 SIMPLE AIRTABLE SYNC")
    print("=" * 25)
    print("📋 Sync Francois with basic fields only")
    print("")
    
    # Get Francois data
    francois_data = syncer.get_francois_data()
    
    if not francois_data:
        print("❌ Cannot find Francois")
        return
    
    # Check if already synced
    if francois_data.get('airtable_id'):
        print(f"✅ Francois already synced: {francois_data.get('airtable_id')}")
        return
    
    # Sync with basic fields
    record_id = syncer.sync_with_basic_fields(francois_data)
    
    if record_id:
        print(f"\n🎉 BASIC SYNC SUCCESS!")
        print(f"   📤 Airtable Record: {record_id}")
        print(f"   📋 Name: {francois_data.get('Full_Name')}")
        print(f"   📧 Email: {francois_data.get('Email')}")
        print(f"   🏢 Company: {francois_data.get('Company')}")
        
        # Try to add additional fields
        print(f"\n📝 Trying to add additional fields...")
        syncer.add_additional_fields(record_id, francois_data)
        
        print(f"\n✅ FRANCOIS IS NOW IN AIRTABLE!")
        print(f"   Check your Airtable base for the new record")
    else:
        print(f"\n❌ Sync failed")

if __name__ == "__main__":
    main()