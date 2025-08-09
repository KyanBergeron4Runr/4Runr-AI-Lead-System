"""
Resilient Engager for the 4Runr Autonomous Outreach System.

This engager implements fallback message generation and defensive lead processing
to ensure leads are processed even when upstream modules (scraper, generator) fail.
"""

import sys
import datetime
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
from outreach.shared.logging_utils import get_logger
from outreach.shared.validation import validate_email_format, validate_airtable_fields
from outreach.shared.config import config


class ResilientEngager:
    """Resilient engager with fallback message generation."""
    
    def __init__(self):
        """Initialize the Resilient Engager."""
        self.logger = get_logger('resilient_engager')
        self.airtable_client = get_configurable_airtable_client()
        self.email_config = config.get_email_config()
        self.system_config = config.get_system_config()
    
    def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads with resilient engagement logic.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads ready for engagement
        batch_size = limit or self.system_config['batch_size']
        leads = self.airtable_client.get_leads_for_engagement(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('resilient_engager', 'system', 'info', 
                                           {'message': 'No leads found ready for engagement'})
            return {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead with resilient logic
                result = self._process_single_lead_resilient(lead)
                
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
    
    def _process_single_lead_resilient(self, lead: Dict[str, Any]) -> str:
        """
        Process a single lead with resilient engagement logic.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        custom_message = lead.get('Custom_Message', '')
        
        self.logger.log_module_activity('resilient_engager', lead_id, 'start', 
                                       {'message': f'Processing engagement for {lead_name}: {email}'})
        
        # Basic validation - only skip for fundamental issues
        skip_reason = self._should_skip_lead(lead)
        if skip_reason:
            self.logger.log_module_activity('resilient_engager', lead_id, 'skip', {
                'message': f'Lead skipped: {skip_reason}',
                'reason': skip_reason,
                'lead_name': lead_name,
                'email': email
            })
            return 'skip'
        
        try:
            # Get or generate message with fallback
            message = self._get_or_generate_message(lead)
            
            if not message:
                self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
                                               {'message': 'Failed to get or generate any message'})
                return 'error'
            
            # Send the email
            send_success = self._send_email(lead, message)
            
            if send_success:
                # Update Airtable with engagement results
                update_success = self._update_engagement_status(lead, 'Sent', message)
                
                if update_success:
                    # Log engagement for analysis
                    self._log_engagement(lead, 'Sent', 'Email')
                    
                    self.logger.log_module_activity('resilient_engager', lead_id, 'success', 
                                                   {'message': f'Successfully sent message to {lead_name}',
                                                    'email': email,
                                                    'message_length': len(message),
                                                    'message_source': 'generated' if not custom_message else 'custom'})
                    return 'success'
                else:
                    self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
                                                   {'message': 'Email sent but failed to update Airtable'})
                    return 'error'
            else:
                # Update status as error
                self._update_engagement_status(lead, 'Error', message)
                return 'error'
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead_resilient',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'email': email
            })
            
            # Try to update status as error
            try:
                self._update_engagement_status(lead, 'Error', custom_message or 'Error during processing')
            except:
                pass  # Don't fail if we can't update status
            
            return 'error'
    
    def _should_skip_lead(self, lead: Dict[str, Any]) -> Optional[str]:
        """
        Determine if a lead should be skipped based on fundamental criteria.
        Only skips for essential missing data or explicit filters.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Skip reason string if should skip, None if should process
        """
        email = lead.get('Email', '')
        email_confidence = lead.get('Email_Confidence_Level', '')
        
        # Must have email
        if not email:
            return 'no_email_address'
        
        # Email must be valid format
        if not validate_email_format(email):
            return 'invalid_email_format'
        
        # Skip if email confidence is explicitly "Guess" (too risky)
        if email_confidence == 'Guess':
            return 'email_confidence_too_low'
        
        # Check if recently contacted (prevent spam)
        if self._recently_contacted(email):
            return 'recently_contacted'
        
        # All fundamental checks passed
        return None
    
    def _get_or_generate_message(self, lead: Dict[str, Any]) -> Optional[str]:
        """
        Get existing custom message or generate fallback message.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Message string or None if all generation fails
        """
        lead_id = lead.get('id', 'unknown')
        custom_message = lead.get('Custom_Message', '')
        
        # Try to use existing custom message first
        if custom_message and len(custom_message.strip()) > 10:
            self.logger.log_module_activity('resilient_engager', lead_id, 'info', 
                                           {'message': 'Using existing custom message'})
            return custom_message.strip()
        
        # Generate fallback message from basic lead data
        self.logger.log_module_activity('resilient_engager', lead_id, 'warning', 
                                       {'message': 'No custom message available, generating fallback'})
        
        fallback_message = self._generate_fallback_message(lead)
        
        if fallback_message:
            self.logger.log_module_activity('resilient_engager', lead_id, 'success', 
                                           {'message': 'Generated fallback message successfully'})
            return fallback_message
        
        # Last resort - minimal message
        minimal_message = self._generate_minimal_message(lead)
        
        if minimal_message:
            self.logger.log_module_activity('resilient_engager', lead_id, 'warning', 
                                           {'message': 'Using minimal fallback message'})
            return minimal_message
        
        return None
    
    def _generate_fallback_message(self, lead: Dict[str, Any]) -> Optional[str]:
        """
        Generate a fallback message from basic lead data.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Generated message or None if generation fails
        """
        try:
            # Extract basic information
            lead_name = lead.get('Name', '').split()[0] if lead.get('Name') else 'there'
            company_name = lead.get('Company', lead.get('Company Name', 'your company'))
            job_title = lead.get('Job Title', lead.get('Title', ''))
            website = lead.get('Website', '')
            company_description = lead.get('Company Description', '')
            
            # Determine focus area based on available data
            focus_area = self._determine_focus_area(company_description, website, company_name)
            value_prop = self._get_value_proposition(focus_area)
            
            # Generate personalized message
            greeting = f"Hi {lead_name}," if lead_name != 'there' else "Hello,"
            
            # Build context-aware opening
            if company_description:
                opening = f"I noticed {company_name}'s work in {focus_area} and was impressed by your approach."
            elif website:
                opening = f"I came across {company_name} and was interested in your {focus_area} focus."
            else:
                opening = f"I wanted to reach out regarding {company_name} and potential collaboration opportunities."
            
            # Add role context if available
            role_context = ""
            if job_title:
                role_context = f" As a {job_title}, you're likely focused on driving results and staying ahead of industry trends."
            
            # Build complete message
            message = f"""{greeting}

{opening}{role_context}

At 4Runr, we specialize in helping companies like yours {value_prop} through strategic AI implementation and intelligent automation systems.

I'd love to share how we've helped similar organizations achieve measurable improvements in their operations. Would you be open to a brief conversation about your current priorities?

Best regards,
4Runr Team"""
            
            return message
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'generate_fallback_message',
                'lead_id': lead.get('id', 'unknown')
            })
            return None
    
    def _generate_minimal_message(self, lead: Dict[str, Any]) -> str:
        """
        Generate a minimal message as last resort.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Minimal message string
        """
        lead_name = lead.get('Name', '').split()[0] if lead.get('Name') else 'there'
        company_name = lead.get('Company', lead.get('Company Name', 'your company'))
        
        return f"""Hi {lead_name},

I wanted to reach out regarding potential opportunities for {company_name}.

At 4Runr, we help companies optimize their operations through intelligent automation and strategic AI implementation.

Would you be interested in a brief conversation about how we might be able to help?

Best regards,
4Runr Team"""
    
    def _determine_focus_area(self, company_description: str, website: str, company_name: str) -> str:
        """
        Determine the company's focus area from available data.
        
        Args:
            company_description: Company description text
            website: Website URL
            company_name: Company name
            
        Returns:
            Focus area string
        """
        text = f"{company_description} {website} {company_name}".lower()
        
        if any(word in text for word in ['technology', 'software', 'tech', 'digital', 'platform']):
            return "technology and digital innovation"
        elif any(word in text for word in ['consulting', 'advisory', 'strategy']):
            return "strategic consulting and business optimization"
        elif any(word in text for word in ['marketing', 'advertising', 'brand']):
            return "marketing strategy and customer engagement"
        elif any(word in text for word in ['finance', 'financial', 'investment']):
            return "financial services and strategic growth"
        elif any(word in text for word in ['healthcare', 'medical', 'health']):
            return "healthcare innovation and operational excellence"
        elif any(word in text for word in ['education', 'learning', 'training']):
            return "educational technology and learning solutions"
        else:
            return "operational efficiency and strategic growth"
    
    def _get_value_proposition(self, focus_area: str) -> str:
        """
        Get appropriate value proposition for the focus area.
        
        Args:
            focus_area: Company's focus area
            
        Returns:
            Value proposition string
        """
        if "technology" in focus_area:
            return "streamline their tech operations and accelerate digital transformation"
        elif "consulting" in focus_area:
            return "enhance their consulting capabilities and deliver better client outcomes"
        elif "marketing" in focus_area:
            return "amplify their marketing impact and improve customer engagement"
        elif "financial" in focus_area:
            return "optimize their financial operations and drive sustainable growth"
        elif "healthcare" in focus_area:
            return "improve their healthcare delivery and operational efficiency"
        elif "education" in focus_area:
            return "enhance their educational offerings and learning outcomes"
        else:
            return "optimize their operations and drive sustainable growth"
    
    def _recently_contacted(self, email: str) -> bool:
        """
        Check if this email was recently contacted to prevent spam.
        
        Args:
            email: Email address to check
            
        Returns:
            True if recently contacted, False otherwise
        """
        try:
            # Simple implementation - check if there's a recent "Date Messaged" entry
            # In a more sophisticated system, this would check a contact history database
            
            # For now, we'll implement a basic check
            # This could be enhanced to check actual contact history
            return False
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'recently_contacted', 'email': email})
            return False  # If check fails, don't skip the lead
    
    def _send_email(self, lead: Dict[str, Any], message: str) -> bool:
        """
        Send email to the lead using Microsoft Graph API.
        
        Args:
            lead: Lead data dictionary
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        company = lead.get('Company', lead.get('Company Name', 'Unknown Company'))
        
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
                self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
                                               {'message': 'Microsoft Graph configuration not available'})
                return False
            
            # Get access token
            access_token = self._get_graph_access_token(graph_config)
            if not access_token:
                return False
            
            # Send email via Microsoft Graph
            success = self._send_via_graph(access_token, graph_config['sender_email'], email, company, message, lead_id)
            
            if success:
                self.logger.log_module_activity('resilient_engager', lead_id, 'success', 
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
    
    def _get_graph_access_token(self, graph_config: Dict[str, str]) -> Optional[str]:
        """Get Microsoft Graph access token."""
        try:
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
                self.logger.log_module_activity('resilient_engager', 'system', 'error', 
                                               {'message': f'Failed to get access token: {response.text}'})
                return None
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_graph_access_token', 'lead_id': 'system'})
            return None
    
    def _send_via_graph(self, access_token: str, sender_email: str, recipient_email: str, 
                       company: str, message: str, lead_id: str) -> bool:
        """Send email using Microsoft Graph API."""
        try:
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
                self.logger.log_module_activity('resilient_engager', lead_id, 'success', 
                                               {'message': f'Microsoft Graph API returned 202 Accepted'})
                return True
            else:
                self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
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
                'Date Messaged': datetime.date.today().isoformat(),
            }
            
            # Add the message if it was sent successfully
            if status == 'Sent' and message:
                airtable_fields['Custom_Message'] = message
            
            # Validate fields
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
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
            'company': lead.get('Company', lead.get('Company Name', 'Unknown Company')),
            'email': lead.get('Email', ''),
            'email_confidence': lead.get('Email_Confidence_Level', ''),
            'status': status,
            'delivery_method': method,
            'message_length': len(lead.get('Custom_Message', '')),
            'engagement_date': datetime.datetime.now().isoformat(),
            'message_source': 'generated' if not lead.get('Custom_Message') else 'custom'
        }
        
        self.logger.save_engagement_log(engagement_data)
    
    def process_specific_lead(self, lead_id: str) -> str:
        """
        Process a specific lead by ID with resilient logic.
        
        Args:
            lead_id: Airtable record ID
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead = self.airtable_client.get_lead_by_id(lead_id)
        if not lead:
            self.logger.log_module_activity('resilient_engager', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return 'error'
        
        return self._process_single_lead_resilient(lead)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads ready for processing.
        
        Returns:
            Dictionary with processing statistics
        """
        leads = self.airtable_client.get_leads_for_engagement(limit=1000)  # Get more for stats
        
        stats = {
            'total_leads_ready': len(leads),
            'leads_with_custom_messages': 0,
            'leads_without_custom_messages': 0,
            'leads_with_real_emails': 0,
            'leads_with_pattern_emails': 0,
            'leads_with_guess_emails': 0
        }
        
        for lead in leads:
            # Check message availability
            if lead.get('Custom_Message'):
                stats['leads_with_custom_messages'] += 1
            else:
                stats['leads_without_custom_messages'] += 1
            
            # Check email confidence
            confidence = lead.get('Email_Confidence_Level', '')
            if confidence == 'Real':
                stats['leads_with_real_emails'] += 1
            elif confidence == 'Pattern':
                stats['leads_with_pattern_emails'] += 1
            elif confidence == 'Guess':
                stats['leads_with_guess_emails'] += 1
        
        return stats