#!/usr/bin/env python3
"""
Sync only today's fresh leads to Airtable
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
logger = logging.getLogger('fresh-leads-sync')

def sync_fresh_leads():
    """Sync only today's fresh leads"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
    
    if not all([api_key, base_id]):
        logger.error("❌ Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
        return False
    
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    # Get today's fresh leads
    if not raw_leads_file.exists():
        logger.error("❌ No raw_leads.json file found")
        return False
    
    try:
        with open(raw_leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        logger.info(f"📋 Found {len(leads)} fresh leads to sync")
        
        # Format leads for Airtable
        records = []
        for lead in leads:
            if lead.get('airtable_synced'):
                continue  # Skip already synced leads
            
            # Create comprehensive Response Notes with all enriched data
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
                patterns = ', '.join(lead['email_patterns'][:3])  # Show first 3 patterns
                response_notes.append(f"📧 Email Patterns: {patterns}")
            
            response_notes_text = '\n'.join(response_notes) if response_notes else ''
            
            record = {
                'fields': {
                    'Full Name': lead.get('full_name', ''),
                    'Company': lead.get('company', ''),
                    'Job Title': lead.get('title') or lead.get('job_title', ''),
                    'Email': lead.get('email', ''),
                    'LinkedIn URL': lead.get('linkedin_url', ''),
                    'Source': 'SerpAPI Scraper',  # Set a valid source
                    'Needs Enrichment': not lead.get('enriched', False),
                    'Date Scraped': lead.get('scraped_at', '')[:10] if lead.get('scraped_at') else None,
                    'Date Enriched': lead.get('enriched_at', '')[:10] if lead.get('enriched_at') else None,
                    'Response Notes': response_notes_text,
                    # 'Lead Quality': Skip this field to avoid validation errors
                }
            }
            
            # Remove None values
            record['fields'] = {k: v for k, v in record['fields'].items() if v is not None}
            records.append(record)
        
        if not records:
            logger.info("✅ No new leads to sync")
            return True
        
        # Sync to Airtable
        encoded_table_name = quote(table_name)
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {'records': records}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            created_records = result.get('records', [])
            logger.info(f"✅ Successfully synced {len(created_records)} fresh leads to Airtable")
            
            # Mark leads as synced
            for i, lead in enumerate(leads):
                if i < len(created_records):
                    lead['airtable_synced'] = True
                    lead['airtable_id'] = created_records[i]['id']
                    lead['synced_at'] = datetime.now().isoformat()
            
            # Save updated leads
            with open(raw_leads_file, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            return True
        else:
            logger.error(f"❌ Airtable sync failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error syncing fresh leads: {str(e)}")
        return False

if __name__ == "__main__":
    success = sync_fresh_leads()
    exit(0 if success else 1)