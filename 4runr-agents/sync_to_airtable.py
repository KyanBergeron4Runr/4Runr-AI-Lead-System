#!/usr/bin/env python3
"""
Sync Leads to Airtable
Syncs scraped and enriched leads to Airtable
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote

# Import database components
try:
    from database.lead_database import get_lead_database
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import database components: {e}")
    DATABASE_AVAILABLE = False


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-sync')

class AirtableSync:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
        
        if not all([self.api_key, self.base_id]):
            raise ValueError("Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID")
        
        self.shared_dir = Path(__file__).parent / "shared"
        
        logger.info("📊 Airtable sync initialized")
        logger.info(f"📋 Target table: {self.table_name}")
    
    def get_leads_to_sync(self):
        """Get leads that need to be synced to Airtable"""
        leads_files = [
            'raw_leads.json',
            'enriched_leads.json',
            'custom_enriched_leads.json'
        ]
        
        all_leads = []
        
        for filename in leads_files:
            file_path = self.shared_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        leads = json.load(f)
                    
                    if isinstance(leads, list):
                        for lead in leads:
                            # Check if already synced
                            if not lead.get('airtable_synced', False):
                                all_leads.append(lead)
                        
                        logger.info(f"📋 Found {len([l for l in leads if not l.get('airtable_synced', False)])} unsynced leads in {filename}")
                    
                except Exception as e:
                    logger.error(f"❌ Error reading {filename}: {str(e)}")
        
        logger.info(f"📊 Total leads to sync: {len(all_leads)}")
        return all_leads
    
    def format_lead_for_airtable(self, lead):
        """Format lead data for Airtable using correct field names"""
        # Map lead fields to exact Airtable field names
        airtable_record = {
            'Full Name': lead.get('name') or lead.get('full_name', ''),
            'Company': lead.get('company', ''),
            'Job Title': lead.get('title') or lead.get('job_title', ''),
            'Email': lead.get('email', ''),
            'LinkedIn URL': lead.get('linkedin_url', ''),
            # 'Source': 'Manual',  # Skip Source field for now to avoid validation errors
            'Needs Enrichment': not lead.get('enriched', False),  # Checkbox - True if NOT enriched
            'Date Scraped': self.format_date_for_airtable(lead.get('scraped_at')),
            'Date Enriched': self.format_date_for_airtable(lead.get('enriched_at')) if lead.get('enriched') else None
        }
        
        # Remove empty/None fields
        return {k: v for k, v in airtable_record.items() if v is not None and v != ''}
    
    def format_date_for_airtable(self, date_string):
        """Format ISO date string to YYYY-MM-DD for Airtable"""
        if not date_string:
            return None
        
        try:
            # Parse ISO format and return just the date part
            from datetime import datetime
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    
    def generate_response_notes(self, lead):
        """Generate response notes with enrichment details"""
        notes = []
        
        if lead.get('enriched'):
            notes.append(f"Enriched via {lead.get('enrichment_method', 'unknown method')}")
            
            if lead.get('email'):
                email_source = lead.get('email_source', 'unknown')
                email_confidence = lead.get('email_confidence', 'unknown')
                notes.append(f"Email found via {email_source} (confidence: {email_confidence})")
            
            if lead.get('company_domain'):
                notes.append(f"Company domain: {lead.get('company_domain')}")
        
        if lead.get('search_snippet'):
            notes.append(f"Search context: {lead.get('search_snippet')[:100]}...")
        
        return ' | '.join(notes) if notes else 'Scraped from SerpAPI'
    
    def sync_leads_to_airtable(self, leads):
        """Sync leads to Airtable in batches"""
        if not leads:
            logger.info("✅ No leads to sync")
            return True
        
        # Airtable API endpoint
        encoded_table_name = quote(self.table_name)
        url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Process in batches of 10 (Airtable limit)
        batch_size = 10
        synced_count = 0
        failed_count = 0
        
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            
            # Format records for Airtable
            records = []
            for lead in batch:
                formatted_lead = self.format_lead_for_airtable(lead)
                records.append({'fields': formatted_lead})
            
            # Send to Airtable
            try:
                data = {'records': records}
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    created_records = result.get('records', [])
                    synced_count += len(created_records)
                    
                    logger.info(f"✅ Synced batch {i//batch_size + 1}: {len(created_records)} records")
                    
                    # Mark leads as synced
                    for j, lead in enumerate(batch):
                        if j < len(created_records):
                            lead['airtable_synced'] = True
                            lead['airtable_id'] = created_records[j]['id']
                            lead['synced_at'] = datetime.now().isoformat()
                
                else:
                    logger.error(f"❌ Airtable sync failed for batch {i//batch_size + 1}: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    failed_count += len(batch)
                
            except Exception as e:
                logger.error(f"❌ Error syncing batch {i//batch_size + 1}: {str(e)}")
                failed_count += len(batch)
            
            # Rate limiting
            import time
            time.sleep(1)
        
        logger.info(f"📊 Sync complete: {synced_count} synced, {failed_count} failed")
        return failed_count == 0
    
    def update_lead_files(self, leads):
        """Update lead files with sync status"""
        # Group leads by source file
        files_to_update = {}
        
        for lead in leads:
            source_file = 'raw_leads.json'  # Default
            
            if lead.get('enriched'):
                source_file = 'enriched_leads.json'
            if lead.get('enrichment_method') == 'custom_system':
                source_file = 'custom_enriched_leads.json'
            
            if source_file not in files_to_update:
                files_to_update[source_file] = []
            files_to_update[source_file].append(lead)
        
        # Update each file
        for filename, file_leads in files_to_update.items():
            file_path = self.shared_dir / filename
            
            if file_path.exists():
                try:
                    # Read current file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_leads = json.load(f)
                    
                    # Update synced leads
                    for updated_lead in file_leads:
                        for i, existing_lead in enumerate(all_leads):
                            if (existing_lead.get('linkedin_url') == updated_lead.get('linkedin_url') or
                                existing_lead.get('name') == updated_lead.get('name')):
                                all_leads[i] = updated_lead
                                break
                    
                    # Write back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(all_leads, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"📁 Updated {filename} with sync status")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating {filename}: {str(e)}")

def sync_leads_to_airtable():
    """Main function to sync leads to Airtable"""
    try:
        logger.info("📊 Starting Airtable sync process...")
        
        # Initialize sync
        sync = AirtableSync()
        
        # Get leads to sync
        leads = sync.get_leads_to_sync()
        
        if not leads:
            logger.info("✅ No leads to sync - all up to date")
            return True
        
        # Sync to Airtable
        success = sync.sync_leads_to_airtable(leads)
        
        if success:
            # Update lead files with sync status
            sync.update_lead_files(leads)
            logger.info("✅ Airtable sync completed successfully")
        else:
            logger.error("❌ Some leads failed to sync to Airtable")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Airtable sync failed: {str(e)}")
        return False

def main():
    """Main function"""
    success = sync_leads_to_airtable()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())