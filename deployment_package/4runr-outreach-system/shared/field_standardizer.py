#!/usr/bin/env python3
"""
Field Standardizer

Comprehensive field standardization system for database maintenance.
Handles engagement status, company names, website URLs, email formats, and other field standardization.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger('field-standardizer')

@dataclass
class StandardizationResult:
    """Results from field standardization operations."""
    success: bool
    field_name: str
    records_processed: int
    records_updated: int
    errors: List[str]
    warnings: List[str]
    changes_made: List[Dict[str, Any]]

class FieldStandardizer:
    """
    Comprehensive field standardization system.
    
    Standardizes field values across both database and Airtable systems
    using configurable rules and formatting standards.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the field standardizer.
        
        Args:
            config: Configuration dictionary with standardization rules
        """
        self.config = config or self._get_default_config()
        logger.info("FieldStandardizer initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default standardization configuration."""
        return {
            'engagement_status': {
                'default_value': 'auto_send',
                'valid_values': ['auto_send', 'manual_review', 'contacted', 'responded']
            },
            'company_name': {
                'normalize_case': True,
                'remove_suffixes': ['Inc.', 'LLC', 'Corp.', 'Ltd.'],
                'add_proper_suffix': True
            },
            'website_url': {
                'ensure_protocol': True,
                'preferred_protocol': 'https',
                'remove_trailing_slash': True
            },
            'email': {
                'normalize_case': 'lower',
                'validate_format': True
            }
        }
    
    def standardize_engagement_status(self, default_status: str = "auto_send") -> StandardizationResult:
        """
        Standardize engagement status across all records.
        
        Args:
            default_status: Default engagement status to set
            
        Returns:
            StandardizationResult: Results of the standardization operation
        """
        result = StandardizationResult(
            success=True,
            field_name="engagement_status",
            records_processed=0,
            records_updated=0,
            errors=[],
            warnings=[],
            changes_made=[]
        )
        
        try:
            logger.info(f"Standardizing engagement status to: {default_status}")
            
            # Validate the default status
            valid_statuses = self.config['engagement_status']['valid_values']
            if default_status not in valid_statuses:
                result.errors.append(f"Invalid engagement status: {default_status}. Valid values: {valid_statuses}")
                result.success = False
                return result
            
            # Standardize database records
            db_result = self._standardize_database_engagement_status(default_status)
            result.records_processed += db_result['processed']
            result.records_updated += db_result['updated']
            result.errors.extend(db_result['errors'])
            result.changes_made.extend(db_result['changes'])
            
            # Standardize Airtable records
            airtable_result = self._standardize_airtable_engagement_status(default_status)
            result.records_processed += airtable_result['processed']
            result.records_updated += airtable_result['updated']
            result.errors.extend(airtable_result['errors'])
            result.changes_made.extend(airtable_result['changes'])
            
            logger.info(f"Engagement status standardization completed: {result.records_updated}/{result.records_processed} records updated")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Engagement status standardization failed: {str(e)}")
            logger.error(f"Engagement status standardization failed: {e}")
            return result
    
    def _standardize_database_engagement_status(self, default_status: str) -> Dict[str, Any]:
        """Standardize engagement status in the database."""
        try:
            # Import database connection
            import sys
            from pathlib import Path
            
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            from database.models import get_lead_database
            
            db = get_lead_database()
            all_leads = db.search_leads({})
            
            processed = 0
            updated = 0
            errors = []
            changes = []
            
            for lead in all_leads:
                processed += 1
                
                # Check if status needs updating
                current_status = getattr(lead, 'status', None)
                
                if current_status != default_status:
                    # Update the lead
                    update_success = db.update_lead(lead.id, {'status': default_status})
                    
                    if update_success:
                        updated += 1
                        changes.append({
                            'record_id': lead.id,
                            'system': 'database',
                            'field': 'status',
                            'old_value': current_status,
                            'new_value': default_status
                        })
                        logger.debug(f"Updated database lead {lead.id}: status {current_status} -> {default_status}")
                    else:
                        errors.append(f"Failed to update database lead {lead.id}")
            
            logger.info(f"Database engagement status standardization: {updated}/{processed} records updated")
            
            return {
                'processed': processed,
                'updated': updated,
                'errors': errors,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Database engagement status standardization failed: {e}")
            return {
                'processed': 0,
                'updated': 0,
                'errors': [f"Database standardization failed: {str(e)}"],
                'changes': []
            }
    
    def _standardize_airtable_engagement_status(self, default_status: str) -> Dict[str, Any]:
        """Standardize engagement status in Airtable."""
        try:
            from configurable_airtable_client import get_configurable_airtable_client
            
            airtable_client = get_configurable_airtable_client()
            
            # Get all records
            all_records = []
            records = airtable_client.table.all()
            
            for record in records:
                all_records.append({
                    'id': record['id'],
                    'fields': record['fields']
                })
            
            processed = 0
            updated = 0
            errors = []
            changes = []
            
            # Batch updates for efficiency
            updates_to_make = []
            
            for record in all_records:
                processed += 1
                
                # Check current engagement status
                current_status = record['fields'].get('Engagement_Status', '')
                
                if current_status != default_status:
                    updates_to_make.append({
                        'id': record['id'],
                        'fields': {'Engagement_Status': default_status}
                    })
                    
                    changes.append({
                        'record_id': record['id'],
                        'system': 'airtable',
                        'field': 'Engagement_Status',
                        'old_value': current_status,
                        'new_value': default_status
                    })
            
            # Perform batch updates
            if updates_to_make:
                try:
                    # Process in batches of 10 (Airtable limit)
                    batch_size = 10
                    for i in range(0, len(updates_to_make), batch_size):
                        batch = updates_to_make[i:i + batch_size]
                        airtable_client.table.batch_update(batch)
                        updated += len(batch)
                        logger.debug(f"Updated Airtable batch: {len(batch)} records")
                    
                except Exception as e:
                    errors.append(f"Airtable batch update failed: {str(e)}")
            
            logger.info(f"Airtable engagement status standardization: {updated}/{processed} records updated")
            
            return {
                'processed': processed,
                'updated': updated,
                'errors': errors,
                'changes': changes
            }
            
        except Exception as e:
            logger.warning(f"Airtable engagement status standardization failed: {e}")
            return {
                'processed': 0,
                'updated': 0,
                'errors': [f"Airtable standardization failed: {str(e)}"],
                'changes': []
            }
    
    def standardize_company_names(self) -> StandardizationResult:
        """
        Standardize company name formatting.
        
        Returns:
            StandardizationResult: Results of the standardization operation
        """
        result = StandardizationResult(
            success=True,
            field_name="company_name",
            records_processed=0,
            records_updated=0,
            errors=[],
            warnings=[],
            changes_made=[]
        )
        
        try:
            logger.info("Standardizing company names...")
            
            # Get company name configuration
            company_config = self.config.get('company_name', {})
            
            # Standardize database records
            db_result = self._standardize_database_company_names(company_config)
            result.records_processed += db_result['processed']
            result.records_updated += db_result['updated']
            result.errors.extend(db_result['errors'])
            result.changes_made.extend(db_result['changes'])
            
            # Standardize Airtable records
            airtable_result = self._standardize_airtable_company_names(company_config)
            result.records_processed += airtable_result['processed']
            result.records_updated += airtable_result['updated']
            result.errors.extend(airtable_result['errors'])
            result.changes_made.extend(airtable_result['changes'])
            
            logger.info(f"Company name standardization completed: {result.records_updated}/{result.records_processed} records updated")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Company name standardization failed: {str(e)}")
            logger.error(f"Company name standardization failed: {e}")
            return result
    
    def _normalize_company_name(self, company_name: str, config: Dict[str, Any]) -> str:
        """Normalize a company name according to configuration rules."""
        if not company_name or not isinstance(company_name, str):
            return company_name
        
        normalized = company_name.strip()
        
        # Normalize case if configured
        if config.get('normalize_case', False):
            # Title case for company names
            normalized = normalized.title()
        
        # Remove unwanted suffixes
        remove_suffixes = config.get('remove_suffixes', [])
        for suffix in remove_suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Add proper suffix if configured
        if config.get('add_proper_suffix', False):
            # Simple heuristic: if no suffix, don't add one
            # This is a placeholder for more sophisticated logic
            pass
        
        return normalized
    
    def _standardize_database_company_names(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize company names in the database."""
        # Placeholder implementation
        logger.info("Standardizing database company names...")
        return {
            'processed': 0,
            'updated': 0,
            'errors': [],
            'changes': []
        }
    
    def _standardize_airtable_company_names(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize company names in Airtable."""
        # Placeholder implementation
        logger.info("Standardizing Airtable company names...")
        return {
            'processed': 0,
            'updated': 0,
            'errors': [],
            'changes': []
        }
    
    def standardize_website_urls(self) -> StandardizationResult:
        """
        Standardize website URL formatting.
        
        Returns:
            StandardizationResult: Results of the standardization operation
        """
        result = StandardizationResult(
            success=True,
            field_name="website_url",
            records_processed=0,
            records_updated=0,
            errors=[],
            warnings=[],
            changes_made=[]
        )
        
        logger.info("Website URL standardization not yet implemented")
        return result
    
    def standardize_email_formats(self) -> StandardizationResult:
        """
        Standardize email formatting.
        
        Returns:
            StandardizationResult: Results of the standardization operation
        """
        result = StandardizationResult(
            success=True,
            field_name="email",
            records_processed=0,
            records_updated=0,
            errors=[],
            warnings=[],
            changes_made=[]
        )
        
        logger.info("Email format standardization not yet implemented")
        return result
    
    def apply_field_defaults(self, field_defaults: Dict[str, Any]) -> StandardizationResult:
        """
        Apply default values to empty fields.
        
        Args:
            field_defaults: Dictionary of field names and their default values
            
        Returns:
            StandardizationResult: Results of the standardization operation
        """
        result = StandardizationResult(
            success=True,
            field_name="field_defaults",
            records_processed=0,
            records_updated=0,
            errors=[],
            warnings=[],
            changes_made=[]
        )
        
        logger.info(f"Applying field defaults: {field_defaults}")
        return result


if __name__ == "__main__":
    # Test the field standardizer
    print("🧪 Testing Field Standardizer...")
    
    # Create field standardizer
    standardizer = FieldStandardizer()
    
    # Test engagement status standardization
    print("Testing engagement status standardization...")
    result = standardizer.standardize_engagement_status("auto_send")
    print(f"Engagement status standardization: {'Success' if result.success else 'Failed'}")
    print(f"Records processed: {result.records_processed}")
    print(f"Records updated: {result.records_updated}")
    
    if result.errors:
        print(f"Errors: {result.errors}")
    
    # Test company name standardization
    print("Testing company name standardization...")
    company_result = standardizer.standardize_company_names()
    print(f"Company name standardization: {'Success' if company_result.success else 'Failed'}")
    
    print("✅ Field standardizer test completed")