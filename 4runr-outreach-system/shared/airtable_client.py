"""
Airtable client module for the 4Runr Autonomous Outreach System.

Provides an abstraction layer for interacting with the Airtable API,
handling authentication, error handling, and data transformation.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from pyairtable import Api
from pyairtable.formulas import match
from .config import get_airtable_config


logger = logging.getLogger(__name__)


class AirtableClient:
    """Client for interacting with Airtable API."""
    
    def __init__(self):
        """Initialize the Airtable client."""
        self.config = get_airtable_config()
        self.api = Api(self.config['api_key'])
        self.table = self.api.table(self.config['base_id'], self.config['table_name'])
    
    def get_leads_for_outreach(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve enriched leads ready for outreach processing.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of lead records with their fields
        """
        try:
            # Get leads that have company_website_url but haven't been processed yet
            formula = "AND({company_website_url} != '', {Company_Description} = '')"
            
            records = self.table.all(
                formula=formula,
                max_records=limit
            )
            
            # Convert generator to list to avoid subscriptable errors
            records_list = list(records)
            
            leads = []
            for record in records_list:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            logger.info(f"Retrieved {len(leads)} leads for outreach processing")
            return leads
            
        except Exception as e:
            logger.error(f"Error retrieving leads from Airtable: {str(e)}")
            return []
    
    def get_leads_for_message_generation(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve leads ready for message generation.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of lead records ready for message generation
        """
        try:
            # Get leads that have company data but no custom message yet
            formula = "AND({Company_Description} != '', {Custom_Message} = '')"
            
            records = self.table.all(
                formula=formula,
                max_records=limit
            )
            
            # Convert generator to list to avoid subscriptable errors
            records_list = list(records)
            
            leads = []
            for record in records_list:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            logger.info(f"Retrieved {len(leads)} leads for message generation")
            return leads
            
        except Exception as e:
            logger.error(f"Error retrieving leads for message generation: {str(e)}")
            return []
    
    def get_leads_for_engagement(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve leads ready for engagement.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of lead records ready for engagement
        """
        try:
            # Get leads with Auto-Send status and Real/Pattern email confidence
            formula = "AND({Engagement_Status} = 'Auto-Send', OR({Email_Confidence_Level} = 'Real', {Email_Confidence_Level} = 'Pattern'))"
            
            records = self.table.all(
                formula=formula,
                max_records=limit
            )
            
            # Convert generator to list to avoid subscriptable errors
            records_list = list(records)
            
            leads = []
            for record in records_list:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            logger.info(f"Retrieved {len(leads)} leads for engagement")
            return leads
            
        except Exception as e:
            logger.error(f"Error retrieving leads for engagement: {str(e)}")
            return []
    
    def update_lead_fields(self, lead_id: str, fields: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Update specific fields for a lead record.
        
        Args:
            lead_id: Airtable record ID
            fields: Dictionary of fields to update
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                self.table.update(lead_id, fields)
                logger.debug(f"Updated lead {lead_id} with fields: {list(fields.keys())}")
                return True
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to update lead {lead_id}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to update lead {lead_id} after {max_retries} attempts")
                    return False
        
        return False
    
    def batch_update_leads(self, updates: List[Dict[str, Any]], max_retries: int = 3) -> int:
        """
        Perform bulk updates for multiple leads.
        
        Args:
            updates: List of update dictionaries with 'id' and 'fields' keys
            max_retries: Maximum number of retry attempts
            
        Returns:
            Number of successfully updated records
        """
        successful_updates = 0
        
        # Process in batches of 10 (Airtable API limit)
        batch_size = 10
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    # Format for batch update
                    batch_records = [
                        {'id': update['id'], 'fields': update['fields']}
                        for update in batch
                    ]
                    
                    self.table.batch_update(batch_records)
                    successful_updates += len(batch)
                    logger.debug(f"Batch updated {len(batch)} leads")
                    break
                    
                except Exception as e:
                    logger.warning(f"Batch update attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to batch update {len(batch)} leads after {max_retries} attempts")
        
        logger.info(f"Successfully updated {successful_updates} out of {len(updates)} leads")
        return successful_updates
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific lead by ID.
        
        Args:
            lead_id: Airtable record ID
            
        Returns:
            Lead record data or None if not found
        """
        try:
            record = self.table.get(lead_id)
            return {
                'id': record['id'],
                **record['fields']
            }
        except Exception as e:
            logger.error(f"Error retrieving lead {lead_id}: {str(e)}")
            return None
    
    def create_lead(self, fields: Dict[str, Any]) -> Optional[str]:
        """
        Create a new lead record.
        
        Args:
            fields: Dictionary of field values
            
        Returns:
            Record ID if successful, None otherwise
        """
        try:
            record = self.table.create(fields)
            logger.info(f"Created new lead record: {record['id']}")
            return record['id']
        except Exception as e:
            logger.error(f"Error creating lead record: {str(e)}")
            return None


# Global client instance
_client = None


def get_airtable_client() -> AirtableClient:
    """Get the global Airtable client instance."""
    global _client
    if _client is None:
        _client = AirtableClient()
    return _client