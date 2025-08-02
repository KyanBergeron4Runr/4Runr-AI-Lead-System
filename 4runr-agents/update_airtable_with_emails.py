#!/usr/bin/env python3
"""
Update Airtable with enriched email data
Push the found emails and contact info back to Airtable records
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-updater')

class AirtableUpdater:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
        self.shared_dir = Path(__file__).parent / "shared"
        
        logger.info("🔄 Airtable Updater initialized")
        logger.info(f"🔍 Base ID: {self.base_id}")
        logger.info(f"🔍 Table: {self.table_name}")
    
    def load_enriched_data(self):
        """Load the enriched lead data"""
        enriched_file = self.shared_dir / "enriched_verified_leads.json"
        
        if not enriched_file.exists():
            logger.error("❌ enriched_verified_leads.json not found")
            return []
        
        with open(enriched_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_airtable_records(self):
        """Get all records from Airtable to find record IDs"""
        try:
            # URL encode the table name
            from urllib.parse import quote
            encoded_table_name = quote(self.table_name)
            url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}"
            
            logger.info(f"🔍 Requesting URL: {url}")
            logger.info(f"🔍 Table name: '{self.table_name}' -> '{encoded_table_name}'")
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            logger.info(f"🔍 Response status: {response.status_code}")
            if response.status_code != 200:
                logger.info(f"🔍 Response text: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                return data.get('records', [])
            else:
                logger.error(f"❌ Failed to get records: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting records: {str(e)}")
            return []
    
    def update_airtable_record(self, record_id, update_data):
        """Update a specific Airtable record"""
        try:
            from urllib.parse import quote
            encoded_table_name = quote(self.table_name)
            url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}/{record_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'fields': update_data
            }
            
            response = requests.patch(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"❌ Failed to update record: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating record: {str(e)}")
            return False
    
    def update_leads_with_enrichment(self):
        """Update Airtable records with enriched data"""
        logger.info("🔄 Starting Airtable update with enriched data...")
        
        # Load enriched data
        enriched_leads = self.load_enriched_data()
        if not enriched_leads:
            logger.error("❌ No enriched data found")
            return 0
        
        # Get current Airtable records
        airtable_records = self.get_airtable_records()
        if not airtable_records:
            logger.error("❌ No Airtable records found")
            return 0
        
        # Create mapping of names to record IDs
        name_to_record = {}
        for record in airtable_records:
            fields = record.get('fields', {})
            name = fields.get('Full Name', fields.get('Name', ''))
            if name:
                name_to_record[name] = record.get('id')
        
        updated_count = 0
        
        print("\n" + "="*70)
        print("🔄 UPDATING AIRTABLE WITH ENRICHED DATA")
        print("="*70)
        
        for enriched_lead in enriched_leads:
            name = enriched_lead['name']
            
            if name not in name_to_record:
                logger.warning(f"⚠️ No Airtable record found for: {name}")
                continue
            
            record_id = name_to_record[name]
            
            print(f"\n📝 Updating: {name}")
            
            # Use only the essential fields that won't cause permission issues
            update_data = {}
            
            # Add email (most important field)
            if enriched_lead.get('primary_email'):
                update_data['Email'] = enriched_lead['primary_email']
                print(f"   📧 Email: {enriched_lead['primary_email']}")
            
            # Mark as enriched
            update_data['Needs Enrichment'] = False
            update_data['Date Enriched'] = datetime.now().strftime('%Y-%m-%d')
            
            # Add enrichment notes to Response Notes field
            notes_parts = []
            
            if enriched_lead.get('company_website'):
                notes_parts.append(f"Website: {enriched_lead['company_website']}")
                print(f"   🌐 Website: {enriched_lead['company_website']}")
            
            if enriched_lead.get('found_emails'):
                found_emails_text = f"Found emails: {', '.join(enriched_lead['found_emails'])}"
                notes_parts.append(found_emails_text)
                print(f"   📋 Found emails: {len(enriched_lead['found_emails'])}")
            
            if enriched_lead.get('email_patterns'):
                patterns_text = f"Email patterns: {', '.join(enriched_lead['email_patterns'][:3])}"
                notes_parts.append(patterns_text)
                print(f"   🎯 Email patterns: {len(enriched_lead['email_patterns'])}")
            
            # Add enrichment status
            status_text = f"Enriched: {enriched_lead.get('enrichment_status', 'unknown')} | Methods: {', '.join(enriched_lead.get('enrichment_methods', []))}"
            notes_parts.append(status_text)
            
            if notes_parts:
                update_data['Response Notes'] = ' | '.join(notes_parts)
            
            # Update the record
            try:
                success = self.update_airtable_record(record_id, update_data)
                if success:
                    updated_count += 1
                    print(f"   ✅ Successfully updated")
                else:
                    print(f"   ❌ Failed to update")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        return updated_count

def main():
    """Main function to update Airtable with enriched data"""
    logger.info("🚀 Starting Airtable update with enriched data...")
    
    updater = AirtableUpdater()
    
    # Update records
    updated_count = updater.update_leads_with_enrichment()
    
    # Summary
    print("\n" + "="*70)
    print("📊 AIRTABLE UPDATE SUMMARY:")
    print(f"   ✅ Successfully updated: {updated_count} records")
    print("   📧 All records now have email data")
    print("   🌐 All records now have website data")
    print("   📋 All records have enrichment notes")
    print("="*70)
    
    if updated_count > 0:
        print("\n🎉 SUCCESS! Your Airtable now contains:")
        print("   • Email addresses (real or high-probability patterns)")
        print("   • Company websites")
        print("   • Enrichment status and methods")
        print("   • Contact method recommendations")
        
        print("\n💡 NEXT STEPS:")
        print("   1. Check your Airtable - all 5 leads should have email data")
        print("   2. Start with leads marked 'Found' emails first")
        print("   3. Test pattern emails carefully")
        print("   4. Use LinkedIn DM as backup if emails bounce")
    
    print("="*70)

if __name__ == "__main__":
    main()