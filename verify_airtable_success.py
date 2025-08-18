#!/usr/bin/env python3
"""
Verify Airtable Success
======================
Confirm Francois was successfully added to Airtable
"""

import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class AirtableVerifier:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_airtable_records(self):
        """Check what records are in Airtable"""
        self.logger.info("📋 Checking Airtable records...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try to get all records (or check if the method exists)
            if hasattr(client, 'get_all_leads'):
                records = client.get_all_leads()
            elif hasattr(client, 'table'):
                # Use the underlying table directly
                records = client.table.all()
            else:
                self.logger.error("❌ No method to get records found")
                return []
            
            self.logger.info(f"📊 Found {len(records)} records in Airtable:")
            
            francois_found = False
            for i, record in enumerate(records, 1):
                if hasattr(record, 'get'):
                    fields = record.get('fields', {})
                    record_id = record.get('id', 'Unknown')
                else:
                    fields = record
                    record_id = fields.get('id', 'Unknown')
                
                name = fields.get('Full Name', 'Unknown')
                email = fields.get('Email', 'Unknown')
                company = fields.get('Company', 'Unknown')
                
                self.logger.info(f"   {i}. {name}")
                self.logger.info(f"      ID: {record_id}")
                self.logger.info(f"      Email: {email}")
                self.logger.info(f"      Company: {company}")
                
                # Check if this is Francois
                if 'francois' in name.lower() and 'cgi' in company.lower():
                    francois_found = True
                    self.logger.info(f"      🎉 THIS IS FRANCOIS!")
                
                self.logger.info("")
            
            if francois_found:
                self.logger.info("✅ FRANCOIS CONFIRMED IN AIRTABLE!")
            else:
                self.logger.info("❌ Francois not found in Airtable")
            
            return francois_found
            
        except Exception as e:
            self.logger.error(f"❌ Error checking Airtable: {e}")
            return False

    def check_specific_record(self, record_id="reciamDUA1KZQli4V"):
        """Check the specific record that was created"""
        self.logger.info(f"🔍 Checking specific record: {record_id}")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try to get the specific record
            if hasattr(client, 'get_lead'):
                record = client.get_lead(record_id)
            elif hasattr(client, 'table'):
                record = client.table.get(record_id)
            else:
                self.logger.error("❌ No method to get specific record")
                return False
            
            if record:
                if hasattr(record, 'get'):
                    fields = record.get('fields', {})
                else:
                    fields = record
                
                name = fields.get('Full Name', 'Unknown')
                email = fields.get('Email', 'Unknown')
                company = fields.get('Company', 'Unknown')
                
                self.logger.info(f"✅ Record found:")
                self.logger.info(f"   ID: {record_id}")
                self.logger.info(f"   Name: {name}")
                self.logger.info(f"   Email: {email}")
                self.logger.info(f"   Company: {company}")
                
                if 'francois' in name.lower():
                    self.logger.info(f"🎉 CONFIRMED: This is Francois in Airtable!")
                    return True
                else:
                    self.logger.info(f"⚠️ This doesn't appear to be Francois")
                    return False
            else:
                self.logger.info(f"❌ Record {record_id} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error checking record: {e}")
            return False

def main():
    verifier = AirtableVerifier()
    
    print("✅ AIRTABLE SUCCESS VERIFICATION")
    print("=" * 35)
    print("📋 Checking if Francois was successfully added to Airtable")
    print("")
    
    # Check the specific record that was created
    print("🔍 Checking the created record...")
    specific_success = verifier.check_specific_record("reciamDUA1KZQli4V")
    
    print("\n📊 Checking all Airtable records...")
    general_success = verifier.check_airtable_records()
    
    print(f"\n🎉 VERIFICATION COMPLETE!")
    print(f"   📤 Specific record check: {'✅ SUCCESS' if specific_success else '❌ Failed'}")
    print(f"   📊 General records check: {'✅ Found Francois' if general_success else '❌ Not found'}")
    
    if specific_success or general_success:
        print(f"\n🏆 MISSION ACCOMPLISHED!")
        print(f"   ✅ Francois Boulanger is in your Airtable")
        print(f"   📧 Email: info@cgi.com")
        print(f"   🏢 Company: CGI")
        print(f"   🎯 Your AI lead generation system is working!")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Check your Airtable base to see Francois")
        print(f"   2. System can now generate more leads")
        print(f"   3. Autonomous mode will continue finding leads")
    else:
        print(f"\n❌ Verification failed - may need more debugging")

if __name__ == "__main__":
    main()
