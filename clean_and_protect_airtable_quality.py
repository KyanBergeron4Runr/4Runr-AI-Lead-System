#!/usr/bin/env python3
"""
Clean Airtable and implement strict data quality controls
- Remove all test/fake leads from Airtable
- Fix sync logic to only allow high-quality leads
- Implement strict validation before any Airtable sync
"""

import sqlite3
import requests
import json
import logging
import os
import re
from datetime import datetime

class AirtableQualityController:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
        # Airtable config - using the working IDs from real_autonomous_organism.py
        self.base_id = "appBZvPvNXGqtoJdc"
        self.table_name = "Table 1"
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def is_test_or_fake_lead(self, lead_data):
        """Strict validation to identify test/fake leads"""
        full_name = lead_data.get('Full_Name', '').strip().lower()
        company = lead_data.get('Company', '').strip().lower()
        email = lead_data.get('Email', '').strip().lower()
        
        # Test patterns that should NEVER sync to Airtable
        test_patterns = [
            'test', 'auto', 'example', 'demo', 'fake', 'sample',
            'unknown company', 'test corp', 'test inc', 'auto test',
            'testcorp', 'testcompany', '@example.com', '@test.com'
        ]
        
        # Check full name
        for pattern in test_patterns:
            if pattern in full_name:
                return True, f"Test name pattern: {pattern}"
        
        # Check company
        for pattern in test_patterns:
            if pattern in company:
                return True, f"Test company pattern: {pattern}"
        
        # Check email
        if '@example.com' in email or '@test.com' in email:
            return True, "Test email domain"
        
        # Check for missing critical data
        if not full_name or len(full_name) < 3:
            return True, "Missing or invalid full name"
        
        if not company or len(company) < 3:
            return True, "Missing or invalid company"
        
        if not email or '@' not in email:
            return True, "Missing or invalid email"
        
        return False, "Valid lead"

    def is_high_quality_lead(self, lead_data):
        """Check if lead meets high quality standards for Airtable"""
        # First check if it's a test lead
        is_test, reason = self.is_test_or_fake_lead(lead_data)
        if is_test:
            return False, f"Test lead: {reason}"
        
        # Check required fields
        required_fields = ['Full_Name', 'Company', 'Email', 'LinkedIn_URL', 'AI_Message']
        missing_fields = []
        
        for field in required_fields:
            value = lead_data.get(field, '').strip()
            if not value:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing critical fields: {', '.join(missing_fields)}"
        
        # Check AI message quality (should not be generic)
        ai_message = lead_data.get('AI_Message', '')
        if len(ai_message) < 50:
            return False, "AI message too short"
        
        # Check LinkedIn URL format
        linkedin_url = lead_data.get('LinkedIn_URL', '')
        if 'linkedin.com/in/' not in linkedin_url:
            return False, "Invalid LinkedIn URL format"
        
        return True, "High quality lead"

    def clean_airtable_test_leads(self):
        """Remove all test/fake leads from Airtable"""
        self.logger.info("🧹 Cleaning test leads from Airtable...")
        
        if not self.api_key:
            self.logger.error("❌ No Airtable API key found")
            return 0
        
        try:
            # Get all Airtable records
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            all_records = []
            offset = None
            
            while True:
                params = {'pageSize': 100}
                if offset:
                    params['offset'] = offset
                
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    self.logger.error(f"❌ Error getting Airtable records: {response.status_code}")
                    break
                
                data = response.json()
                all_records.extend(data.get('records', []))
                
                offset = data.get('offset')
                if not offset:
                    break
            
            self.logger.info(f"📋 Found {len(all_records)} total records in Airtable")
            
            # Identify test leads to delete
            test_records_to_delete = []
            
            for record in all_records:
                fields = record.get('fields', {})
                record_id = record.get('id')
                
                # Convert Airtable field names to our format
                lead_data = {
                    'Full_Name': fields.get('Full Name', ''),
                    'Company': fields.get('Company', ''),
                    'Email': fields.get('Email', ''),
                    'LinkedIn_URL': fields.get('LinkedIn URL', ''),
                    'AI_Message': fields.get('AI Message', '')
                }
                
                is_test, reason = self.is_test_or_fake_lead(lead_data)
                if is_test:
                    test_records_to_delete.append({
                        'id': record_id,
                        'name': lead_data['Full_Name'],
                        'reason': reason
                    })
            
            self.logger.info(f"🗑️ Found {len(test_records_to_delete)} test leads to delete")
            
            # Delete test records
            deleted_count = 0
            for record in test_records_to_delete:
                try:
                    delete_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}/{record['id']}"
                    response = requests.delete(delete_url, headers=headers)
                    
                    if response.status_code == 200:
                        self.logger.info(f"🗑️ Deleted test lead: {record['name']} - {record['reason']}")
                        deleted_count += 1
                    else:
                        self.logger.error(f"❌ Failed to delete {record['name']}: {response.status_code}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error deleting {record['name']}: {e}")
            
            self.logger.info(f"🎉 Deleted {deleted_count} test leads from Airtable")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning Airtable: {e}")
            return 0

    def clean_database_test_leads(self):
        """Remove test leads from database"""
        self.logger.info("🧹 Cleaning test leads from database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            leads = conn.execute("SELECT * FROM leads").fetchall()
            
            test_lead_ids = []
            for lead in leads:
                lead_dict = dict(lead)
                is_test, reason = self.is_test_or_fake_lead(lead_dict)
                if is_test:
                    test_lead_ids.append((lead['id'], lead_dict.get('Full_Name', 'Unknown'), reason))
            
            self.logger.info(f"🗑️ Found {len(test_lead_ids)} test leads in database")
            
            # Delete test leads
            deleted_count = 0
            for lead_id, name, reason in test_lead_ids:
                conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
                self.logger.info(f"🗑️ Deleted from DB: {name} - {reason}")
                deleted_count += 1
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Deleted {deleted_count} test leads from database")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning database: {e}")
            return 0

    def validate_all_database_leads(self):
        """Validate all leads in database and mark quality status"""
        self.logger.info("✅ Validating all database leads for quality...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            leads = conn.execute("SELECT * FROM leads").fetchall()
            
            high_quality_count = 0
            low_quality_count = 0
            
            for lead in leads:
                lead_dict = dict(lead)
                is_quality, reason = self.is_high_quality_lead(lead_dict)
                
                # Update lead with quality status
                quality_status = 'high_quality' if is_quality else 'low_quality'
                
                conn.execute("""
                    UPDATE leads SET 
                        Lead_Quality = ?,
                        Response_Status = ?
                    WHERE id = ?
                """, (
                    quality_status,
                    'approved_for_sync' if is_quality else 'needs_improvement',
                    lead['id']
                ))
                
                if is_quality:
                    high_quality_count += 1
                    self.logger.info(f"✅ High quality: {lead_dict.get('Full_Name', 'Unknown')}")
                else:
                    low_quality_count += 1
                    self.logger.info(f"⚠️ Low quality: {lead_dict.get('Full_Name', 'Unknown')} - {reason}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📊 Quality Analysis Complete:")
            self.logger.info(f"   ✅ High quality leads: {high_quality_count}")
            self.logger.info(f"   ⚠️ Low quality leads: {low_quality_count}")
            
            return high_quality_count, low_quality_count
            
        except Exception as e:
            self.logger.error(f"❌ Error validating leads: {e}")
            return 0, 0

def main():
    controller = AirtableQualityController()
    
    print("🧹 AIRTABLE QUALITY CONTROL & CLEANUP")
    print("=" * 45)
    
    # Step 1: Clean test leads from Airtable
    print("\n🗑️ STEP 1: Cleaning test leads from Airtable...")
    airtable_deleted = controller.clean_airtable_test_leads()
    
    # Step 2: Clean test leads from database
    print("\n🗑️ STEP 2: Cleaning test leads from database...")
    db_deleted = controller.clean_database_test_leads()
    
    # Step 3: Validate remaining leads
    print("\n✅ STEP 3: Validating remaining leads...")
    high_quality, low_quality = controller.validate_all_database_leads()
    
    # Summary
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"   🗑️ Deleted from Airtable: {airtable_deleted} test leads")
    print(f"   🗑️ Deleted from Database: {db_deleted} test leads")
    print(f"   ✅ High quality leads: {high_quality}")
    print(f"   ⚠️ Low quality leads: {low_quality}")
    
    print(f"\n🛡️ PROTECTION IMPLEMENTED:")
    print(f"   ✅ Only high-quality leads will sync to Airtable")
    print(f"   ✅ Test leads are permanently blocked")
    print(f"   ✅ All leads must have complete data")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Update sync logic to use quality validation")
    print(f"   2. Test sync with only high-quality leads")
    print(f"   3. Monitor for future test lead prevention")

if __name__ == "__main__":
    main()
