#!/usr/bin/env python3
"""
Update existing Airtable records with complete enriched data
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-complete-update')

def update_existing_records():
    """Update existing Airtable records with complete enriched data"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
    
    if not all([api_key, base_id]):
        logger.error("❌ Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
        return False
    
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    if not raw_leads_file.exists():
        logger.error("❌ No raw_leads.json found")
        return False
    
    try:
        # Read enriched raw leads
        with open(raw_leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        logger.info(f"📋 Found {len(leads)} leads to update")
        
        # Update each lead in Airtable
        updated_count = 0
        
        for lead in leads:
            airtable_id = lead.get('airtable_id')
            name = lead.get('full_name', '')
            
            if not airtable_id:
                logger.info(f"⚠️ No Airtable ID for {name} - skipping")
                continue
            
            # Prepare comprehensive update data
            update_fields = {}
            
            # Basic info
            if lead.get('title'):
                update_fields['Job Title'] = lead['title']
            
            if lead.get('company'):
                update_fields['Company'] = lead['company']
            
            if lead.get('email'):
                update_fields['Email'] = lead['email']
            
            # Enrichment status
            if lead.get('enriched'):
                update_fields['Needs Enrichment'] = False
                if lead.get('enriched_at'):
                    update_fields['Date Enriched'] = lead['enriched_at'][:10]
            
            # Skip Lead Quality for now to avoid validation errors
            # We'll add this info to Response Notes instead
            
            # Create comprehensive Response Notes
            response_notes = []
            
            if lead.get('company_website'):
                response_notes.append(f"🌐 Website: {lead['company_website']}")
            
            if lead.get('email_confidence'):
                response_notes.append(f"📧 Email Confidence: {lead['email_confidence']}")
            
            if lead.get('email_source'):
                response_notes.append(f"📧 Email Source: {lead['email_source']}")
            
            if lead.get('enrichment_method'):
                response_notes.append(f"🔧 Enriched via: {lead['enrichment_method']}")
            
            if lead.get('email_patterns'):
                patterns = ', '.join(lead['email_patterns'][:3])
                response_notes.append(f"📧 Alternative Emails: {patterns}")
            
            if lead.get('found_emails') and len(lead['found_emails']) > 1:
                other_emails = ', '.join(lead['found_emails'][1:3])  # Show other found emails
                response_notes.append(f"📧 Other Found Emails: {other_emails}")
            
            if lead.get('enrichment_quality'):
                response_notes.append(f"⭐ Enrichment Quality: {lead['enrichment_quality']}")
            
            # Add lead quality info to notes
            if lead.get('ready_for_engagement'):
                response_notes.append(f"🎯 Lead Quality: High (Ready for engagement)")
            elif lead.get('email') or lead.get('company_website'):
                response_notes.append(f"🎯 Lead Quality: Medium (Partial contact info)")
            
            if response_notes:
                update_fields['Response Notes'] = '\n'.join(response_notes)
            
            if not update_fields:
                logger.info(f"⚠️ No updates needed for {name}")
                continue
            
            # Update Airtable record
            encoded_table_name = quote(table_name)
            url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}/{airtable_id}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {'fields': update_fields}
            response = requests.patch(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Updated {name} with complete enriched data")
                updated_count += 1
                
                # Log what was updated
                logger.info(f"   📋 Job Title: {update_fields.get('Job Title', 'Not updated')}")
                logger.info(f"   🏢 Company: {update_fields.get('Company', 'Not updated')}")
                logger.info(f"   📧 Email: {update_fields.get('Email', 'Not updated')}")
                logger.info(f"   🌐 Website: {'Yes' if 'Website:' in update_fields.get('Response Notes', '') else 'Not found'}")
                
            else:
                logger.error(f"❌ Failed to update {name}: {response.status_code}")
                logger.error(f"Response: {response.text}")
            
            # Rate limiting
            import time
            time.sleep(1)
        
        logger.info(f"🎯 Updated {updated_count} records in Airtable with complete data")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Airtable: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting complete Airtable update with all enriched data...")
    success = update_existing_records()
    
    if success:
        logger.info("✅ Complete Airtable update finished successfully")
    else:
        logger.error("❌ Complete Airtable update failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())