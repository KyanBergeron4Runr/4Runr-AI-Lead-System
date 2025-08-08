#!/usr/bin/env python3
"""
Message Generator Agent for the 4Runr Autonomous Outreach System.

This agent creates personalized outreach messages using AI while maintaining
4Runr's helpful, strategic brand voice.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from outreach.shared.airtable_client import get_airtable_client
from outreach.shared.logging_utils import get_logger
from outreach.shared.validation import validate_message_quality, validate_airtable_fields
from outreach.shared.config import config

from outreach.message_generator.ai_generator import AIMessageGenerator


class MessageGeneratorAgent:
    """Main Message Generator Agent class."""
    
    def __init__(self):
        """Initialize the Message Generator Agent."""
        self.logger = get_logger('message_generator')
        self.airtable_client = get_airtable_client()
        self.ai_generator = AIMessageGenerator()
        self.system_config = config.get_system_config()
    
    def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need message generation.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads that need message generation
        batch_size = limit or self.system_config['batch_size']
        leads = self.airtable_client.get_leads_for_message_generation(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('message_generator', 'system', 'info', 
                                           {'message': 'No leads found that need message generation'})
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
    
    def _process_single_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Process a single lead for message generation.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        company_name = lead.get('Company', 'Unknown Company')
        
        self.logger.log_module_activity('message_generator', lead_id, 'start', 
                                       {'message': f'Processing {lead_name} at {company_name}'})
        
        # Check if we have required company data
        if not lead.get('Company_Description'):
            self.logger.log_module_activity('message_generator', lead_id, 'skip', 
                                           {'message': 'Missing company description - website scraping needed first'})
            return False
        
        try:
            # Prepare lead data
            lead_data = {
                'Name': lead.get('Name', ''),
                'Company': lead.get('Company', ''),
                'Job Title': lead.get('Job Title', ''),
                'Email': lead.get('Email', ''),
                'Email_Confidence_Level': lead.get('Email_Confidence_Level', 'Guess')
            }
            
            # Prepare company data
            company_data = {
                'company_description': lead.get('Company_Description', ''),
                'top_services': lead.get('Top_Services', ''),
                'tone': lead.get('Tone', 'Professional'),
                'website_insights': lead.get('Website_Insights', '')
            }
            
            # Generate message
            message_result = self.ai_generator.generate_message(lead_data, company_data, lead_id)
            generated_message = message_result['message']
            
            # Validate message quality
            quality_result = validate_message_quality(generated_message, lead_data)
            
            # Determine engagement status
            engagement_status = self._determine_engagement_status(
                lead_data.get('Email_Confidence_Level', 'Guess'),
                quality_result
            )
            
            # Prepare Airtable update
            airtable_fields = {
                'Custom_Message': generated_message,
                'Engagement_Status': engagement_status
            }
            
            # Validate fields before update
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('message_generator', lead_id, 'error', 
                                               {'message': 'Field validation failed', 
                                                'errors': validation_result['errors']})
                return False
            
            # Update Airtable
            update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
            if update_success:
                self.logger.log_module_activity('message_generator', lead_id, 'success', 
                                               {'message': f'Generated message for {lead_name}',
                                                'message_length': len(generated_message),
                                                'engagement_status': engagement_status,
                                                'quality_score': quality_result.get('score', 0),
                                                'generation_method': message_result.get('method', 'unknown')})
                return True
            else:
                self.logger.log_module_activity('message_generator', lead_id, 'error', 
                                               {'message': 'Failed to update Airtable'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'company': company_name
            })
            return False
    
    def _determine_engagement_status(self, email_confidence: str, quality_result: Dict[str, Any]) -> str:
        """
        Determine engagement status based on email confidence and message quality.
        
        Args:
            email_confidence: Email confidence level (Real/Pattern/Guess)
            quality_result: Message quality validation result
            
        Returns:
            Engagement status (Auto-Send/Skip/Needs Review)
        """
        # Skip if email confidence is Guess or empty
        if not email_confidence or email_confidence == 'Guess':
            return 'Skip'
        
        # Skip if email confidence is not Real or Pattern
        if email_confidence not in ['Real', 'Pattern']:
            return 'Skip'
        
        # Check message quality
        if not quality_result.get('valid', False):
            return 'Needs Review'
        
        # If quality score is low, needs review
        if quality_result.get('score', 0) < 80:
            return 'Needs Review'
        
        # All checks passed - ready for auto-send
        return 'Auto-Send'
    
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
            self.logger.log_module_activity('message_generator', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return False
        
        return self._process_single_lead(lead)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads ready for processing.
        
        Returns:
            Dictionary with processing statistics
        """
        leads = self.airtable_client.get_leads_for_message_generation(limit=1000)  # Get more for stats
        
        stats = {
            'total_leads_ready': len(leads),
            'leads_with_company_data': 0,
            'leads_without_company_data': 0
        }
        
        for lead in leads:
            if lead.get('Company_Description'):
                stats['leads_with_company_data'] += 1
            else:
                stats['leads_without_company_data'] += 1
        
        return stats


def main():
    """Main entry point for the Message Generator Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Message Generator Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = MessageGeneratorAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with company data: {stats['leads_with_company_data']}")
        print(f"  Leads without company data: {stats['leads_without_company_data']}")
        return True
    
    if args.lead_id:
        success = agent.process_specific_lead(args.lead_id)
        return success
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Message Generator Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)