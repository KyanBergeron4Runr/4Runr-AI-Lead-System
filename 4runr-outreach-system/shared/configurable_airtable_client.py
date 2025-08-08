"""
Configurable Airtable client for the 4Runr Autonomous Outreach System.

Provides a robust Airtable integration with configurable field names,
defensive error handling, and fallback mechanisms for 422 INVALID_FILTER_BY_FORMULA errors.
"""

import os
import time
import logging
import urllib.parse as up
from typing import List, Dict, Any, Optional
from pyairtable import Api
from pyairtable.formulas import match

from outreach.shared.config import get_airtable_config
from outreach.shared.logging_utils import get_logger


class ConfigurableAirtableClient:
    """Configurable Airtable client with defensive error handling."""
    
    def __init__(self):
        """Initialize the configurable Airtable client."""
        self.logger = get_logger('airtable_client')
        self.config = get_airtable_config()
        
        # Initialize API connection
        self.api = Api(self.config['api_key'])
        self.base_id = self.config['base_id']
        self.table_name = self.config['table_name']
        self.table = self.api.table(self.base_id, self.table_name)
        
        # Load configurable field names from environment
        self.field_website = os.getenv("AIRTABLE_FIELD_WEBSITE", "Website")
        self.field_company_description = os.getenv("AIRTABLE_FIELD_COMPANY_DESCRIPTION", "Company Description")
        self.field_email = os.getenv("AIRTABLE_FIELD_EMAIL", "Email")
        self.field_company_name = os.getenv("AIRTABLE_FIELD_COMPANY_NAME", "Company Name")
        self.field_name = os.getenv("AIRTABLE_FIELD_NAME", "Name")
        self.field_job_title = os.getenv("AIRTABLE_FIELD_JOB_TITLE", "Job Title")
        self.field_email_confidence_level = os.getenv("AIRTABLE_FIELD_EMAIL_CONFIDENCE_LEVEL", "Email_Confidence_Level")
        self.field_custom_message = os.getenv("AIRTABLE_FIELD_CUSTOM_MESSAGE", "Custom_Message")
        self.field_engagement_status = os.getenv("AIRTABLE_FIELD_ENGAGEMENT_STATUS", "Engagement_Status")
        self.field_date_messaged = os.getenv("AIRTABLE_FIELD_DATE_MESSAGED", "Date Messaged")
        
        self.logger.log_module_activity('airtable_client', 'system', 'info', {
            'message': 'Configurable Airtable client initialized',
            'base_id': self.base_id,
            'table_name': self.table_name,
            'field_mappings': {
                'website': self.field_website,
                'company_description': self.field_company_description,
                'email': self.field_email,
                'company_name': self.field_company_name
            }
        })
    
    def get_leads_for_processing(self, max_records: int = 20) -> List[Dict[str, Any]]:
        """
        Get leads that need website scraping with defensive error handling.
        
        Args:
            max_records: Maximum number of records to retrieve
            
        Returns:
            List of lead records
        """
        try:
            # Primary filter - leads with websites but no company description
            formula = f"AND({{{self.field_website}}} != '', {{{self.field_company_description}}} = '')"
            
            records = self.table.all(
                formula=formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            if leads:
                self.logger.log_module_activity('airtable_client', 'system', 'success', {
                    'message': f'Retrieved {len(leads)} leads with primary filter',
                    'formula': formula
                })
                return leads
                
        except Exception as e:
            self.logger.log_module_activity('airtable_client', 'system', 'warning', {
                'message': f'Primary filter failed: {str(e)}',
                'formula': formula if 'formula' in locals() else 'unknown'
            })
            
            # Log available field names for debugging
            available_fields = self._get_available_field_names()
            self.logger.log_module_activity('airtable_client', 'system', 'info', {
                'message': 'Available field names for debugging',
                'available_fields': available_fields
            })
        
        # Fallback filter - looser criteria
        try:
            fallback_formula = f"{{{self.field_website}}} != ''"
            
            records = self.table.all(
                formula=fallback_formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            self.logger.log_module_activity('airtable_client', 'system', 'info', {
                'message': f'Retrieved {len(leads)} leads with fallback filter',
                'formula': fallback_formula
            })
            
            return leads
            
        except Exception as fallback_error:
            self.logger.log_module_activity('airtable_client', 'system', 'error', {
                'message': f'Both primary and fallback filters failed',
                'primary_error': str(e) if 'e' in locals() else 'unknown',
                'fallback_error': str(fallback_error),
                'available_fields': self._get_available_field_names()
            })
            return []
    
    def get_leads_for_message_generation(self, max_records: int = 20) -> List[Dict[str, Any]]:
        """
        Get leads ready for message generation with defensive error handling.
        
        Args:
            max_records: Maximum number of records to retrieve
            
        Returns:
            List of lead records
        """
        try:
            # Primary filter - leads with company data but no custom message
            formula = f"AND({{{self.field_company_description}}} != '', {{{self.field_custom_message}}} = '')"
            
            records = self.table.all(
                formula=formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            if leads:
                self.logger.log_module_activity('airtable_client', 'system', 'success', {
                    'message': f'Retrieved {len(leads)} leads for message generation',
                    'formula': formula
                })
                return leads
                
        except Exception as e:
            self.logger.log_module_activity('airtable_client', 'system', 'warning', {
                'message': f'Message generation filter failed: {str(e)}',
                'available_fields': self._get_available_field_names()
            })
        
        # Fallback - get leads with company descriptions
        try:
            fallback_formula = f"{{{self.field_company_description}}} != ''"
            
            records = self.table.all(
                formula=fallback_formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            self.logger.log_module_activity('airtable_client', 'system', 'info', {
                'message': f'Retrieved {len(leads)} leads with fallback filter for message generation'
            })
            
            return leads
            
        except Exception as fallback_error:
            self.logger.log_module_activity('airtable_client', 'system', 'error', {
                'message': 'All message generation filters failed',
                'fallback_error': str(fallback_error)
            })
            return []
    
    def get_leads_for_engagement(self, max_records: int = 20) -> List[Dict[str, Any]]:
        """
        Get leads ready for engagement with defensive error handling.
        
        Args:
            max_records: Maximum number of records to retrieve
            
        Returns:
            List of lead records
        """
        try:
            # Primary filter - leads with Auto-Send status
            formula = f"AND({{{self.field_email}}} != '', {{{self.field_engagement_status}}} = 'Auto-Send')"
            
            records = self.table.all(
                formula=formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            if leads:
                self.logger.log_module_activity('airtable_client', 'system', 'success', {
                    'message': f'Retrieved {len(leads)} leads for engagement',
                    'formula': formula
                })
                return leads
                
        except Exception as e:
            self.logger.log_module_activity('airtable_client', 'system', 'warning', {
                'message': f'Engagement filter failed: {str(e)}',
                'available_fields': self._get_available_field_names()
            })
        
        # Fallback - get leads with emails
        try:
            fallback_formula = f"{{{self.field_email}}} != ''"
            
            records = self.table.all(
                formula=fallback_formula,
                max_records=max_records
            )
            
            leads = self._convert_records_to_leads(records)
            
            self.logger.log_module_activity('airtable_client', 'system', 'info', {
                'message': f'Retrieved {len(leads)} leads with fallback filter for engagement'
            })
            
            return leads
            
        except Exception as fallback_error:
            self.logger.log_module_activity('airtable_client', 'system', 'error', {
                'message': 'All engagement filters failed',
                'fallback_error': str(fallback_error)
            })
            return []
    
    def update_lead_fields(self, lead_id: str, fields: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Update specific fields for a lead record with retry logic.
        
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
                
                self.logger.log_module_activity('airtable_client', lead_id, 'success', {
                    'message': f'Updated lead fields: {list(fields.keys())}',
                    'attempt': attempt + 1
                })
                
                return True
                
            except Exception as e:
                self.logger.log_module_activity('airtable_client', lead_id, 'warning', {
                    'message': f'Update attempt {attempt + 1} failed: {str(e)}',
                    'fields': list(fields.keys())
                })
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.log_module_activity('airtable_client', lead_id, 'error', {
                        'message': f'Failed to update lead after {max_retries} attempts',
                        'final_error': str(e)
                    })
        
        return False
    
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
            lead_data = {
                'id': record['id'],
                **record['fields']
            }
            
            self.logger.log_module_activity('airtable_client', lead_id, 'success', {
                'message': 'Retrieved lead by ID'
            })
            
            return lead_data
            
        except Exception as e:
            self.logger.log_module_activity('airtable_client', lead_id, 'error', {
                'message': f'Error retrieving lead: {str(e)}'
            })
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
            record_id = record['id']
            
            self.logger.log_module_activity('airtable_client', record_id, 'success', {
                'message': 'Created new lead record',
                'fields': list(fields.keys())
            })
            
            return record_id
            
        except Exception as e:
            self.logger.log_module_activity('airtable_client', 'system', 'error', {
                'message': f'Error creating lead record: {str(e)}',
                'fields': list(fields.keys())
            })
            return None
    
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
                    
                    self.logger.log_module_activity('airtable_client', 'system', 'success', {
                        'message': f'Batch updated {len(batch)} leads',
                        'attempt': attempt + 1
                    })
                    
                    break
                    
                except Exception as e:
                    self.logger.log_module_activity('airtable_client', 'system', 'warning', {
                        'message': f'Batch update attempt {attempt + 1} failed: {str(e)}',
                        'batch_size': len(batch)
                    })
                    
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        self.logger.log_module_activity('airtable_client', 'system', 'error', {
                            'message': f'Failed to batch update {len(batch)} leads after {max_retries} attempts'
                        })
        
        self.logger.log_module_activity('airtable_client', 'system', 'info', {
            'message': f'Batch update completed: {successful_updates}/{len(updates)} successful'
        })
        
        return successful_updates
    
    def test_connection(self) -> bool:
        """
        Test the Airtable connection and field configuration.
        
        Returns:
            True if connection and configuration are working, False otherwise
        """
        try:
            # Try to get a small sample of records
            records = self.table.all(max_records=1)
            records_list = list(records)
            
            if records_list:
                sample_record = records_list[0]
                available_fields = list(sample_record['fields'].keys())
                
                self.logger.log_module_activity('airtable_client', 'system', 'success', {
                    'message': 'Airtable connection test successful',
                    'available_fields': available_fields,
                    'configured_fields': {
                        'website': self.field_website,
                        'company_description': self.field_company_description,
                        'email': self.field_email
                    }
                })
                
                return True
            else:
                self.logger.log_module_activity('airtable_client', 'system', 'warning', {
                    'message': 'Airtable connection successful but no records found'
                })
                return True
                
        except Exception as e:
            self.logger.log_module_activity('airtable_client', 'system', 'error', {
                'message': f'Airtable connection test failed: {str(e)}'
            })
            return False
    
    def _convert_records_to_leads(self, records) -> List[Dict[str, Any]]:
        """
        Convert Airtable records to lead dictionaries.
        
        Args:
            records: Airtable records (generator or list)
            
        Returns:
            List of lead dictionaries
        """
        leads = []
        
        # Convert generator to list if needed
        if hasattr(records, '__iter__') and not isinstance(records, list):
            records = list(records)
        
        for record in records:
            lead_data = {
                'id': record['id'],
                **record['fields']
            }
            leads.append(lead_data)
        
        return leads
    
    def _get_available_field_names(self) -> List[str]:
        """
        Get available field names from a sample record for debugging.
        
        Returns:
            List of available field names or error message
        """
        try:
            records = self.table.all(max_records=1)
            records_list = list(records)
            
            if records_list:
                return list(records_list[0]['fields'].keys())
            else:
                return ["No records available to determine field names"]
                
        except Exception as e:
            return [f"Unable to retrieve field names: {str(e)}"]
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        Get the current field mapping configuration.
        
        Returns:
            Dictionary of logical field names to Airtable field names
        """
        return {
            'website': self.field_website,
            'company_description': self.field_company_description,
            'email': self.field_email,
            'company_name': self.field_company_name,
            'name': self.field_name,
            'job_title': self.field_job_title,
            'email_confidence_level': self.field_email_confidence_level,
            'custom_message': self.field_custom_message,
            'engagement_status': self.field_engagement_status,
            'date_messaged': self.field_date_messaged
        }


# Global client instance
_configurable_client = None


def get_configurable_airtable_client() -> ConfigurableAirtableClient:
    """Get the global configurable Airtable client instance."""
    global _configurable_client
    if _configurable_client is None:
        _configurable_client = ConfigurableAirtableClient()
    return _configurable_client


# Backward compatibility - update the original function to use configurable client
def get_airtable_client() -> ConfigurableAirtableClient:
    """Get the Airtable client instance (now uses configurable client)."""
    return get_configurable_airtable_client()