#!/usr/bin/env python3
"""
Diagnose Airtable Sync Issues
============================
Check what's preventing leads from syncing to Airtable
"""

import sqlite3
import sys
import logging

# Add paths
sys.path.insert(0, './4runr-outreach-system')

class AirtableSyncDiagnostic:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_database_leads(self):
        """Check what leads are in the database and their status"""
        self.logger.info("🔍 Checking database leads...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads ORDER BY created_at DESC")
            all_leads = [dict(row) for row in cursor.fetchall()]
            
            if not all_leads:
                self.logger.info("📋 No leads found in database")
                return []
            
            self.logger.info(f"📋 Found {len(all_leads)} leads in database:")
            
            for i, lead in enumerate(all_leads, 1):
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                email = lead.get('Email', 'None')
                status = lead.get('Response_Status', 'Unknown')
                airtable_id = lead.get('airtable_id', 'None')
                ai_message = lead.get('AI_Message', 'None')
                
                self.logger.info(f"   {i}. {name} - {company}")
                self.logger.info(f"      Email: {email}")
                self.logger.info(f"      Status: {status}")
                self.logger.info(f"      Airtable ID: {airtable_id}")
                self.logger.info(f"      AI Message: {'✅ Yes' if ai_message and ai_message != 'None' else '❌ No'}")
                self.logger.info("")
            
            conn.close()
            return all_leads
            
        except Exception as e:
            self.logger.error(f"❌ Error checking database: {e}")
            return []

    def check_airtable_connection(self):
        """Test Airtable connection"""
        self.logger.info("🔗 Testing Airtable connection...")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Try to get records
            records = client.get_all()
            
            self.logger.info(f"✅ Airtable connection working")
            self.logger.info(f"📊 Found {len(records)} records in Airtable")
            
            # Show recent records
            if records:
                self.logger.info("📋 Recent Airtable records:")
                for i, record in enumerate(records[-3:], 1):  # Last 3
                    fields = record.get('fields', {})
                    name = fields.get('Full Name', 'Unknown')
                    company = fields.get('Company', 'Unknown')
                    self.logger.info(f"   {i}. {name} - {company}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Airtable connection failed: {e}")
            return False

    def check_sync_validation(self, leads):
        """Check what's blocking leads from syncing"""
        self.logger.info("🔍 Checking sync validation logic...")
        
        if not leads:
            self.logger.info("📋 No leads to validate")
            return
        
        for lead in leads:
            name = lead.get('Full_Name', 'Unknown')
            company = lead.get('Company', 'Unknown')
            email = lead.get('Email', '')
            
            self.logger.info(f"🧪 Validating: {name}")
            
            # Check validation criteria
            validation_issues = []
            
            # Check company
            if not company or company.lower() in ['unknown company', 'unknown', '']:
                validation_issues.append("❌ Generic/missing company name")
            else:
                self.logger.info(f"   ✅ Company: {company}")
            
            # Check email domain vs company
            if email and '@' in email:
                domain = email.split('@')[1].lower()
                if any(fake in domain for fake in ['a0b00267.com', '27b69170.com', 'test.com']):
                    validation_issues.append("❌ Fake email domain")
                else:
                    self.logger.info(f"   ✅ Email: {email}")
            else:
                validation_issues.append("❌ Missing/invalid email")
            
            # Check if already synced
            airtable_id = lead.get('airtable_id')
            if airtable_id:
                validation_issues.append(f"⚠️ Already synced: {airtable_id}")
            
            # Check AI message
            ai_message = lead.get('AI_Message')
            if not ai_message or ai_message == 'None':
                validation_issues.append("❌ Missing AI message")
            else:
                self.logger.info(f"   ✅ AI Message present")
            
            # Report results
            if validation_issues:
                self.logger.info(f"   🚫 BLOCKED from sync:")
                for issue in validation_issues:
                    self.logger.info(f"      {issue}")
            else:
                self.logger.info(f"   ✅ READY for sync")
            
            self.logger.info("")

    def manual_sync_test(self, leads):
        """Try to manually sync a lead to test the process"""
        self.logger.info("🧪 Testing manual sync...")
        
        # Find a lead that should be syncable
        syncable_leads = []
        for lead in leads:
            company = lead.get('Company', '')
            email = lead.get('Email', '')
            ai_message = lead.get('AI_Message', '')
            airtable_id = lead.get('airtable_id')
            
            if (company and company.lower() not in ['unknown company', 'unknown'] and
                email and '@' in email and 
                not any(fake in email.lower() for fake in ['a0b00267.com', '27b69170.com']) and
                ai_message and ai_message != 'None' and
                not airtable_id):
                syncable_leads.append(lead)
        
        if not syncable_leads:
            self.logger.info("❌ No leads found that meet sync criteria")
            return
        
        test_lead = syncable_leads[0]
        name = test_lead.get('Full_Name', 'Unknown')
        
        self.logger.info(f"🧪 Testing sync for: {name}")
        
        try:
            from shared.airtable_client import get_airtable_client
            
            client = get_airtable_client()
            
            # Prepare data for Airtable
            airtable_data = {
                'Full Name': test_lead.get('Full_Name', ''),
                'Company': test_lead.get('Company', ''),
                'Email': test_lead.get('Email', ''),
                'Job Title': test_lead.get('Job_Title', ''),
                'LinkedIn URL': test_lead.get('LinkedIn_URL', ''),
                'AI Message': test_lead.get('AI_Message', ''),
                'Response Status': test_lead.get('Response_Status', 'pending'),
                'Source': 'Manual Sync Test'
            }
            
            # Create record
            result = client.create(airtable_data)
            
            if result:
                record_id = result.get('id')
                self.logger.info(f"✅ Successfully synced to Airtable: {record_id}")
                
                # Update database with Airtable ID
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE leads SET airtable_id = ? WHERE id = ?", 
                           (record_id, test_lead['id']))
                conn.commit()
                conn.close()
                
                self.logger.info(f"✅ Updated database with Airtable ID")
                return True
            else:
                self.logger.error("❌ Failed to create Airtable record")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Manual sync failed: {e}")
            return False

def main():
    diagnostic = AirtableSyncDiagnostic()
    
    print("🔍 AIRTABLE SYNC DIAGNOSTIC")
    print("=" * 30)
    
    # Step 1: Check database leads
    print("\n📋 STEP 1: Check database leads")
    leads = diagnostic.check_database_leads()
    
    # Step 2: Test Airtable connection
    print("\n🔗 STEP 2: Test Airtable connection")
    airtable_ok = diagnostic.check_airtable_connection()
    
    # Step 3: Check validation logic
    print("\n🔍 STEP 3: Check sync validation")
    diagnostic.check_sync_validation(leads)
    
    # Step 4: Try manual sync
    if airtable_ok and leads:
        print("\n🧪 STEP 4: Test manual sync")
        sync_success = diagnostic.manual_sync_test(leads)
        
        if sync_success:
            print("\n✅ MANUAL SYNC SUCCESSFUL!")
            print("The issue might be in the autonomous organism's sync logic")
        else:
            print("\n❌ MANUAL SYNC FAILED!")
            print("There's an issue with the sync process itself")
    
    print(f"\n📊 DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()
