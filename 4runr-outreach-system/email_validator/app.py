#!/usr/bin/env python3
"""
Email Validation Upgrade for the 4Runr Autonomous Outreach System.

This module classifies email addresses by confidence level to ensure
outreach quality and prevent sending to invalid addresses.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.validation import validate_email_format, classify_email_confidence, validate_airtable_fields
from shared.config import config


class EmailValidatorAgent:
    """Main Email Validator Agent class."""
    
    def __init__(self):
        """Initialize the Email Validator Agent."""
        self.logger = get_logger('email_validator')
        self.airtable_client = get_airtable_client()
        self.system_config = config.get_system_config()
    
    def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need email validation.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get all leads to check their email confidence levels
        batch_size = limit or self.system_config['batch_size'] * 2  # Process more for validation
        leads = self._get_leads_needing_validation(batch_size)
        
        if not leads:
            self.logger.log_module_activity('email_validator', 'system', 'info', 
                                           {'message': 'No leads found that need email validation'})
            return {'processed': 0, 'successful': 0, 'errors': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead
                success = self._process_single_lead(lead)
                
                stats['processed'] += 1
                if success:
                    stats['successful'] += 1
                else:
                    stats['errors'] += 1
                
                # Rate limiting
                import time
                if i < len(leads) - 1:  # Don't delay after the last lead
                    time.sleep(self.system_config['rate_limit_delay'])
                    
            except Exception as e:
                self.logger.log_error(e, {
                    'action': 'process_leads',
                    'lead_id': lead.get('id', 'unknown'),
                    'lead_index': i
                })
                stats['processed'] += 1
                stats['errors'] += 1
        
        self.logger.log_pipeline_complete(stats['processed'], stats['successful'], stats['errors'])
        return stats
    
    def _get_leads_needing_validation(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads that need email validation."""
        try:
            # Get leads that have emails but no confidence level set
            # This is a simplified approach - in practice, you'd want a more specific filter
            leads = self.airtable_client.get_leads_for_outreach(limit=limit)
            
            # Filter for leads that need validation
            needs_validation = []
            for lead in leads:
                email = lead.get('Email')
                confidence = lead.get('Email_Confidence_Level')
                
                # Need validation if has email but no confidence level
                if email and not confidence:
                    needs_validation.append(lead)
            
            return needs_validation
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_leads_needing_validation'})
            return []
    
    def _process_single_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Process a single lead for email validation.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        
        self.logger.log_module_activity('email_validator', lead_id, 'start', 
                                       {'message': f'Validating email for {lead_name}: {email}'})
        
        if not email:
            self.logger.log_module_activity('email_validator', lead_id, 'skip', 
                                           {'message': 'No email address to validate'})
            return False
        
        try:
            # Validate email format
            is_valid_format = validate_email_format(email)
            
            if not is_valid_format:
                self.logger.log_module_activity('email_validator', lead_id, 'warning', 
                                               {'message': f'Invalid email format: {email}'})
                confidence_level = 'Guess'
            else:
                # Classify email confidence based on source method
                # For now, we'll infer the source method from the email pattern
                source_method = self._infer_source_method(email, lead)
                confidence_level = classify_email_confidence(email, source_method)
            
            # Prepare Airtable update
            airtable_fields = {
                'Email_Confidence_Level': confidence_level
            }
            
            # Validate fields before update
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('email_validator', lead_id, 'error', 
                                               {'message': 'Field validation failed', 
                                                'errors': validation_result['errors']})
                return False
            
            # Update Airtable
            update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
            if update_success:
                self.logger.log_module_activity('email_validator', lead_id, 'success', 
                                               {'message': f'Email validated for {lead_name}',
                                                'email': email,
                                                'confidence_level': confidence_level,
                                                'valid_format': is_valid_format})
                return True
            else:
                self.logger.log_module_activity('email_validator', lead_id, 'error', 
                                               {'message': 'Failed to update Airtable'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'email': email
            })
            return False
    
    def _infer_source_method(self, email: str, lead: Dict[str, Any]) -> str:
        """
        Infer the source method for email classification.
        
        Args:
            email: Email address
            lead: Lead data
            
        Returns:
            Inferred source method
        """
        email_lower = email.lower()
        company = lead.get('Company', '').lower()
        
        # Check if email domain matches company name (rough heuristic)
        if company:
            company_words = company.replace(' ', '').replace('-', '').replace('.', '')
            if any(word in email_lower for word in [company_words[:10]]):  # First 10 chars of company
                # Looks like a company email
                if any(pattern in email_lower for pattern in ['info@', 'contact@', 'hello@', 'admin@']):
                    return 'direct_scrape'  # Likely from contact page
                else:
                    return 'pattern_generation'  # Likely generated pattern
        
        # Check for common patterns
        if '.' in email_lower.split('@')[0]:  # firstname.lastname pattern
            return 'pattern_generation'
        
        # Default to guess for uncertain cases
        return 'fallback_logic'
    
    def process_specific_lead(self, lead_id: str) -> bool:
        """
        Process a specific lead by ID.
        
        Args:
            lead_id: Airtable record ID
            
        Returns:
            True if successful, False otherwise
        """
        lead = self.airtable_client.get_lead_by_id(lead_id)
        if not lead:
            self.logger.log_module_activity('email_validator', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return False
        
        return self._process_single_lead(lead)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads ready for processing.
        
        Returns:
            Dictionary with processing statistics
        """
        leads = self._get_leads_needing_validation(1000)  # Get more for stats
        
        stats = {
            'total_leads_needing_validation': len(leads),
            'leads_with_valid_emails': 0,
            'leads_with_invalid_emails': 0
        }
        
        for lead in leads:
            email = lead.get('Email', '')
            if email and validate_email_format(email):
                stats['leads_with_valid_emails'] += 1
            else:
                stats['leads_with_invalid_emails'] += 1
        
        return stats


def main():
    """Main entry point for the Email Validator Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Email Validator Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = EmailValidatorAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads needing validation: {stats['total_leads_needing_validation']}")
        print(f"  Leads with valid emails: {stats['leads_with_valid_emails']}")
        print(f"  Leads with invalid emails: {stats['leads_with_invalid_emails']}")
        return True
    
    if args.lead_id:
        success = agent.process_specific_lead(args.lead_id)
        return success
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Email Validator Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)