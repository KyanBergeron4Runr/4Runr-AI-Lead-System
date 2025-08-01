#!/usr/bin/env python3
"""
Engager Agent for the 4Runr Autonomous Outreach System.

This agent executes outreach campaigns while maintaining strict validation
gates to ensure only validated leads receive personalized messages.
"""

import sys
import datetime
import requests
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.validation import validate_email_format, validate_airtable_fields
from shared.config import config


class EngagerAgent:
    """Main Engager Agent class."""
    
    def __init__(self):
        """Initialize the Engager Agent."""
        self.logger = get_logger('engager')
        self.airtable_client = get_airtable_client()
        self.email_config = config.get_email_config()
        self.system_config = config.get_system_config()
    
    def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that are ready for engagement.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads ready for engagement
        batch_size = limit or self.system_config['batch_size']
        leads = self.airtable_client.get_leads_for_engagement(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('engager', 'system', 'info', 
                                           {'message': 'No leads found ready for engagement'})
            return {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead
                result = self._process_single_lead(lead)
                
                stats['processed'] += 1
                if result == 'success':
                    stats['successful'] += 1
                elif result == 'skip':
                    stats['skipped'] += 1
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
    
    def _process_single_lead(self, lead: Dict[str, Any]) -> str:
        """
        Process a single lead for engagement.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        email_confidence = lead.get('Email_Confidence_Level', '')
        custom_message = lead.get('Custom_Message', '')
        
        self.logger.log_module_activity('engager', lead_id, 'start', 
                                       {'message': f'Processing engagement for {lead_name}: {email}'})
        
        # Validation gates
        if not self._should_engage_lead(lead):
            return 'skip'
        
        try:
            # Send the email
            send_success = self._send_email(lead, custom_message)
            
            if send_success:
                # Update Airtable with engagement results
                update_success = self._update_engagement_status(lead, 'Sent', custom_message)
                
                if update_success:
                    # Log engagement for analysis
                    self._log_engagement(lead, 'Sent', 'Email')
                    
                    self.logger.log_module_activity('engager', lead_id, 'success', 
                                                   {'message': f'Successfully sent message to {lead_name}',
                                                    'email': email,
                                                    'message_length': len(custom_message)})
                    return 'success'
                else:
                    self.logger.log_module_activity('engager', lead_id, 'error', 
                                                   {'message': 'Email sent but failed to update Airtable'})
                    return 'error'
            else:
                # Update status as error
                self._update_engagement_status(lead, 'Error', custom_message)
                return 'error'
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'email': email
            })
            
            # Try to update status as error
            try:
                self._update_engagement_status(lead, 'Error', custom_message)
            except:
                pass  # Don't fail if we can't update status
            
            return 'error'
    
    def _should_engage_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Determine if a lead should be engaged based on validation gates.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if lead should be engaged, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        email = lead.get('Email', '')
        email_confidence = lead.get('Email_Confidence_Level', '')
        custom_message = lead.get('Custom_Message', '')
        engagement_status = lead.get('Engagement_Status', '')
        
        # Must have email
        if not email:
            self.logger.log_module_activity('engager', lead_id, 'skip', 
                                           {'message': 'No email address'})
            return False
        
        # Email must be valid format
        if not validate_email_format(email):
            self.logger.log_module_activity('engager', lead_id, 'skip', 
                                           {'message': 'Invalid email format'})
            return False
        
        # Email confidence must be Real or Pattern
        if email_confidence not in ['Real', 'Pattern']:
            self.logger.log_module_activity('engager', lead_id, 'skip', 
                                           {'message': f'Email confidence level is {email_confidence}, not Real or Pattern'})
            return False
        
        # Must have custom message
        if not custom_message:
            self.logger.log_module_activity('engager', lead_id, 'skip', 
                                           {'message': 'No custom message available'})
            return False
        
        # Engagement status must be Auto-Send
        if engagement_status != 'Auto-Send':
            self.logger.log_module_activity('engager', lead_id, 'skip', 
                                           {'message': f'Engagement status is {engagement_status}, not Auto-Send'})
            return False
        
        # All validation gates passed
        return True
    
    def _send_email(self, lead: Dict[str, Any], message: str) -> bool:
        """
        Send email to the lead using Microsoft Graph API.
        
        Args:
            lead: Lead data dictionary
            message: Custom message to send
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        company = lead.get('Company', 'Unknown Company')
        
        try:
            # Get Microsoft Graph configuration
            graph_config = {
                'client_id': config.get('MS_GRAPH_CLIENT_ID'),
                'client_secret': config.get('MS_GRAPH_CLIENT_SECRET'),
                'tenant_id': config.get('MS_GRAPH_TENANT_ID'),
                'sender_email': config.get('MS_GRAPH_SENDER_EMAIL')
            }
            
            # Check if Graph configuration is available
            if not all(graph_config.values()):
                self.logger.log_module_activity('engager', lead_id, 'error', 
                                               {'message': 'Microsoft Graph configuration not available'})
                return False
            
            # Get access token
            access_token = self._get_graph_access_token(graph_config)
            if not access_token:
                return False
            
            # Send email via Microsoft Graph
            success = self._send_via_graph(access_token, graph_config['sender_email'], email, company, message, lead_id)
            
            if success:
                self.logger.log_module_activity('engager', lead_id, 'success', 
                                               {'message': f'Email sent successfully to {email} via Microsoft Graph'})
            
            return success
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'send_email',
                'lead_id': lead_id,
                'email': email,
                'lead_name': lead_name
            })
            return False
    
    def _get_graph_access_token(self, graph_config: Dict[str, str]) -> str:
        """Get Microsoft Graph access token."""
        try:
            import requests
            
            url = f"https://login.microsoftonline.com/{graph_config['tenant_id']}/oauth2/v2.0/token"
            
            data = {
                'client_id': graph_config['client_id'],
                'client_secret': graph_config['client_secret'],
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                self.logger.log_module_activity('engager', 'system', 'error', 
                                               {'message': f'Failed to get access token: {response.text}'})
                return None
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_graph_access_token', 'lead_id': 'system'})
            return None
    
    def _send_via_graph(self, access_token: str, sender_email: str, recipient_email: str, 
                       company: str, message: str, lead_id: str) -> bool:
        """Send email using Microsoft Graph API."""
        try:
            import requests
            
            url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                "message": {
                    "subject": f"Strategic Partnership Opportunity - {company}",
                    "body": {
                        "contentType": "Text",
                        "content": message
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=email_data)
            
            if response.status_code == 202:
                self.logger.log_module_activity('engager', lead_id, 'success', 
                                               {'message': f'Microsoft Graph API returned 202 Accepted'})
                return True
            else:
                self.logger.log_module_activity('engager', lead_id, 'error', 
                                               {'message': f'Microsoft Graph API error: {response.status_code} - {response.text}'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'send_via_graph', 'lead_id': lead_id})
            return False
    
    def _update_engagement_status(self, lead: Dict[str, Any], status: str, message: str) -> bool:
        """
        Update engagement status in Airtable.
        
        Args:
            lead: Lead data dictionary
            status: Engagement status (Sent/Skipped/Error)
            message: Message that was sent
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        
        try:
            # Prepare update fields
            airtable_fields = {
                'Engagement_Status': status,
                'Message_Preview': message[:500] + "..." if len(message) > 500 else message,  # Truncate if too long
                'Last_Contacted_Date': datetime.date.today().isoformat(),
                'Delivery_Method': 'Email' if status == 'Sent' else 'Skipped'
            }
            
            # Validate fields
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('engager', lead_id, 'error', 
                                               {'message': 'Field validation failed', 
                                                'errors': validation_result['errors']})
                return False
            
            # Update Airtable
            return self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'update_engagement_status',
                'lead_id': lead_id,
                'status': status
            })
            return False
    
    def _log_engagement(self, lead: Dict[str, Any], status: str, method: str) -> None:
        """
        Log engagement for detailed analysis.
        
        Args:
            lead: Lead data dictionary
            status: Engagement status
            method: Delivery method
        """
        engagement_data = {
            'lead_id': lead.get('id', 'unknown'),
            'lead_name': lead.get('Name', 'Unknown'),
            'company': lead.get('Company', 'Unknown Company'),
            'email': lead.get('Email', ''),
            'email_confidence': lead.get('Email_Confidence_Level', ''),
            'status': status,
            'delivery_method': method,
            'message_length': len(lead.get('Custom_Message', '')),
            'engagement_date': datetime.datetime.now().isoformat()
        }
        
        self.logger.save_engagement_log(engagement_data)
    
    def process_specific_lead(self, lead_id: str) -> str:
        """
        Process a specific lead by ID.
        
        Args:
            lead_id: Airtable record ID
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead = self.airtable_client.get_lead_by_id(lead_id)
        if not lead:
            self.logger.log_module_activity('engager', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return 'error'
        
        return self._process_single_lead(lead)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads ready for processing.
        
        Returns:
            Dictionary with processing statistics
        """
        leads = self.airtable_client.get_leads_for_engagement(limit=1000)  # Get more for stats
        
        stats = {
            'total_leads_ready': len(leads),
            'leads_with_real_emails': 0,
            'leads_with_pattern_emails': 0,
            'leads_with_guess_emails': 0,
            'leads_with_messages': 0
        }
        
        for lead in leads:
            confidence = lead.get('Email_Confidence_Level', '')
            if confidence == 'Real':
                stats['leads_with_real_emails'] += 1
            elif confidence == 'Pattern':
                stats['leads_with_pattern_emails'] += 1
            elif confidence == 'Guess':
                stats['leads_with_guess_emails'] += 1
            
            if lead.get('Custom_Message'):
                stats['leads_with_messages'] += 1
        
        return stats


def main():
    """Main entry point for the Engager Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Engager Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--dry-run', action='store_true', help='Simulate sending without actually sending emails')
    
    args = parser.parse_args()
    
    agent = EngagerAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with Real emails: {stats['leads_with_real_emails']}")
        print(f"  Leads with Pattern emails: {stats['leads_with_pattern_emails']}")
        print(f"  Leads with Guess emails: {stats['leads_with_guess_emails']}")
        print(f"  Leads with messages: {stats['leads_with_messages']}")
        return True
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No emails will actually be sent")
    
    if args.lead_id:
        result = agent.process_specific_lead(args.lead_id)
        print(f"Result: {result}")
        return result == 'success'
    
    # Process leads in batch
    results = agent.process_leads(limit=args.limit)
    
    print(f"Engager Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)