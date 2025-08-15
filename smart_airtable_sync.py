#!/usr/bin/env python3
"""
Smart Airtable Sync - Detects existing fields and maps accordingly
"""

import os
import sqlite3
import requests
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartAirtableSync:
    """Smart Airtable sync that detects existing fields."""
    
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME')
        self.db_path = 'data/unified_leads.db'
        
        if not all([self.api_key, self.base_id, self.table_name]):
            raise ValueError("Missing required Airtable environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_name}'
        self.existing_fields = None
        
    def detect_airtable_fields(self):
        """Detect existing fields in Airtable."""
        try:
            # Get existing records to see field structure
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                if records:
                    # Get field names from first record
                    self.existing_fields = list(records[0].get('fields', {}).keys())
                    logger.info(f"Detected Airtable fields: {self.existing_fields}")
                else:
                    # Default field set if no records exist
                    self.existing_fields = ['Full Name', 'Email', 'Company', 'LinkedIn URL']
                    logger.info("No existing records, using default fields")
                
                return True
            else:
                logger.error(f"Failed to detect fields: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Field detection failed: {e}")
            return False
    
    def sync_leads_to_airtable(self):
        """Sync all leads to Airtable with field detection."""
        logger.info("SMART AIRTABLE SYNC")
        logger.info("=" * 40)
        
        try:
            # First detect existing fields
            if not self.detect_airtable_fields():
                logger.error("Failed to detect Airtable fields")
                return False
            
            # Clear existing records first
            self.clear_existing_records()
            
            # Get leads from database
            leads = self.get_leads_from_database()
            logger.info(f"Found {len(leads)} leads in database")
            
            if not leads:
                logger.warning("No leads found in database")
                return True
            
            # Sync to Airtable
            success_count = 0
            fail_count = 0
            
            logger.info(f"Syncing {len(leads)} leads to Airtable...")
            
            for lead in leads:
                try:
                    self.sync_single_lead(lead)
                    success_count += 1
                    logger.info(f"Synced: {lead['full_name']} at {lead['company']}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to sync {lead['full_name']}: {e}")
            
            # Report results
            logger.info(f"\nSync Summary:")
            logger.info(f"   Successful: {success_count}")
            logger.info(f"   Failed: {fail_count}")
            logger.info(f"   Total: {len(leads)}")
            
            if fail_count == 0:
                logger.info("Sync completed successfully!")
                return True
            else:
                logger.warning(f"Sync completed with {fail_count} failures")
                return False
                
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False
    
    def clear_existing_records(self):
        """Clear existing records from Airtable."""
        try:
            logger.info("Clearing existing Airtable records...")
            
            # Get all existing records
            response = requests.get(self.base_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                # Delete in batches of 10 (Airtable limit)
                for i in range(0, len(records), 10):
                    batch = records[i:i+10]
                    record_ids = [record['id'] for record in batch]
                    
                    if record_ids:
                        delete_params = '&'.join([f'records[]={rid}' for rid in record_ids])
                        delete_url = f"{self.base_url}?{delete_params}"
                        
                        delete_response = requests.delete(delete_url, headers=self.headers)
                        
                        if delete_response.status_code != 200:
                            logger.warning(f"Failed to delete batch: {delete_response.status_code}")
                
                logger.info(f"Cleared {len(records)} existing records")
            else:
                logger.warning(f"Failed to get existing records: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Failed to clear existing records: {e}")
    
    def get_leads_from_database(self):
        """Get all leads from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads ORDER BY id")
            leads = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return leads
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []
    
    def sync_single_lead(self, lead):
        """Sync a single lead to Airtable using detected fields."""
        # Create field mapping based on detected fields
        field_mapping = {
            'Full Name': lead.get('full_name', ''),
            'Email': lead.get('email', ''),
            'Company': lead.get('company', ''),
            'LinkedIn URL': lead.get('linkedin_url', ''),
            'Website': lead.get('company_website', ''),
            'Created At': lead.get('created_at', ''),
            'Source': lead.get('source', 'Database'),
            'Level Engaged': 'Needs Review',  # Default status
            'Engagement_Status': 'Needs Review',
            'Email_Confidence_Level': 'Medium',
            'Business_Type': lead.get('business_type', 'Business'),
            'Follow_Up_Stage': 'Initial Contact',
            'Response_Status': 'No Response',
            'Company_Description': lead.get('company_description', ''),
            'AI_Message': lead.get('ai_message', '')[:1000] if lead.get('ai_message') else ''  # Truncate for Airtable
        }
        
        # Only include fields that exist in Airtable
        airtable_fields = {}
        for field_name, value in field_mapping.items():
            if field_name in self.existing_fields:
                airtable_fields[field_name] = value
            else:
                # Try alternative field names
                alternatives = {
                    'Business_Type': ['Business Type', 'Type', 'Industry'],
                    'Company_Description': ['Company Description', 'Description'],
                    'AI_Message': ['AI Message', 'Message', 'Notes'],
                    'LinkedIn URL': ['LinkedIn', 'LinkedIn Profile']
                }
                
                if field_name in alternatives:
                    for alt_name in alternatives[field_name]:
                        if alt_name in self.existing_fields:
                            airtable_fields[alt_name] = value
                            break
        
        # Prepare data for Airtable
        airtable_data = {
            'fields': airtable_fields
        }
        
        # Post to Airtable
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps(airtable_data),
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Airtable API error: {response.status_code} - {response.text}")
        
        return response.json()

def main():
    """Main sync function."""
    try:
        syncer = SmartAirtableSync()
        success = syncer.sync_leads_to_airtable()
        
        if success:
            print("SMART SYNC SUCCESSFUL")
            return 0
        else:
            print("SMART SYNC COMPLETED WITH WARNINGS")
            return 1
            
    except Exception as e:
        print(f"SMART SYNC FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
