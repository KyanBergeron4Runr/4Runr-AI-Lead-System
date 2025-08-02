#!/usr/bin/env python3
"""
Update Airtable records with enriched data
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
logger = logging.getLogger('airtable-update')

def update_airtable_with_enriched_data():
    """Update Airtable records with enriched data"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
    
    if not all([api_key, base_id]):
        logger.error("❌ Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
        return False
    
    shared_dir = Path(__file__).parent / "shared"
    
    # Read raw leads (with Airtable IDs) and enriched leads
    raw_leads_file = shared_dir / "raw_leads.json"
    enriched_leads_file = shared_dir / "enriched_leads.json"
    
    if not raw_leads_file.exists() or not enriched_leads_file.exists():
        logger.error("❌ Missing raw_leads.json or enriched_leads.json")
        return False
    
    try:
        # Read both files
        with open(raw_leads_file, 'r', encoding='utf-8') as f:
            raw_leads = json.load(f)
        
        with open(enriched_leads_file, 'r', encoding='utf-8') as f:
            enriched_leads = json.load(f)
        
        # Update Airtable records directly from raw leads (which now contain enriched data)
        updated_count = 0
        
        for raw_lead in raw_leads:
            airtable_id = raw_lead.get('airtable_id')
            name = raw_lead.get('full_name', '')
            
            if not airtable_id or not name:
                continue
            
            # Check if this lead has been enriched
            if not raw_lead.get('enriched'):
                logger.info(f"⚠️ {name} not enriched yet")
                continue
            
            # Prepare update data from raw lead (which now contains enriched data)
            update_fields = {}
            
            if raw_lead.get('title'):
                update_fields['Job Title'] = raw_lead['title']
            
            if raw_lead.get('company'):
                update_fields['Company'] = raw_lead['company']
            
            if raw_lead.get('email'):
                update_fields['Email'] = raw_lead['email']
            
            if raw_lead.get('enriched'):
                update_fields['Needs Enrichment'] = False
                update_fields['Date Enriched'] = raw_lead.get('enriched_at', '')[:10]
            
            if not update_fields:
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
                logger.info(f"✅ Updated {name} in Airtable")
                updated_count += 1
            else:
                logger.error(f"❌ Failed to update {name}: {response.status_code}")
                logger.error(f"Response: {response.text}")
        
        logger.info(f"🎯 Updated {updated_count} records in Airtable")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Airtable: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_airtable_with_enriched_data()
    exit(0 if success else 1)