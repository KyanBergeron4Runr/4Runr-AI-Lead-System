#!/usr/bin/env python3
"""
Test Airtable Sync with just the new leads
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test-airtable')

def test_sync_new_leads():
    """Test syncing just the 5 new leads"""
    
    # Get the 5 new enriched leads
    shared_dir = Path(__file__).parent / "shared"
    enriched_file = shared_dir / "enriched_leads.json"
    
    if not enriched_file.exists():
        logger.error("❌ No enriched_leads.json found")
        return
    
    with open(enriched_file, 'r', encoding='utf-8') as f:
        all_leads = json.load(f)
    
    # Get just the last 5 leads (the new ones)
    new_leads = all_leads[-5:]
    
    logger.info(f"📋 Testing sync with {len(new_leads)} new leads")
    
    # Airtable config
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
    
    encoded_table_name = quote(table_name)
    url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Format leads for Airtable
    records = []
    for lead in new_leads:
        record = {
            'fields': {
                'Full Name': lead.get('full_name', ''),
                'LinkedIn URL': lead.get('linkedin_url', ''),
                'Job Title': lead.get('title', 'Executive'),
                'Company': lead.get('company', 'Unknown'),
                'Email': lead.get('email', ''),
                'Source': 'Manual',  # Use existing option
                'Needs Enrichment': not lead.get('enriched', False),
                'Date Scraped': datetime.now().strftime('%Y-%m-%d'),
                'Response Notes': f"Scraped via SerpAPI on {datetime.now().strftime('%Y-%m-%d')}"
            }
        }
        
        # Remove empty fields
        record['fields'] = {k: v for k, v in record['fields'].items() if v}
        records.append(record)
    
    # Send to Airtable
    try:
        data = {'records': records}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            created_records = result.get('records', [])
            logger.info(f"✅ Successfully synced {len(created_records)} leads to Airtable!")
            
            for i, record in enumerate(created_records):
                lead_name = new_leads[i].get('full_name', 'Unknown')
                logger.info(f"   📋 {lead_name} -> Airtable ID: {record['id']}")
        else:
            logger.error(f"❌ Airtable sync failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_sync_new_leads()