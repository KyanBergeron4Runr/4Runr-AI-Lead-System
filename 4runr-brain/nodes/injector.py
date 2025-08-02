"""
Injector Node

Manages approved campaign delivery to the message queue system.
Handles injection success/failure and coordinates with existing delivery infrastructure.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_node import CampaignNode, RetryableError
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / "4runr-outreach-system"))
from campaign_state import CampaignState, CampaignStatus

# Import Airtable client
try:
    from shared.airtable_client import get_airtable_client
    AIRTABLE_AVAILABLE = True
except ImportError:
    AIRTABLE_AVAILABLE = False


class InjectorNode(CampaignNode):
    """Injects approved campaigns into the delivery queue"""
    
    def __init__(self, config):
        super().__init__(config)
        self.injection_retry_limit = 3
        
        # Initialize Airtable client if available
        if AIRTABLE_AVAILABLE:
            try:
                self.airtable_client = get_airtable_client()
                self.logger.info("Airtable client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Airtable client: {e}")
                self.airtable_client = None
        else:
            self.airtable_client = None
            self.logger.warning("Airtable client not available - LinkedIn campaigns will be saved to file only")
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute campaign injection logic"""
        
        # Only inject if campaign is approved
        if state.final_status != CampaignStatus.APPROVED:
            self.logger.info(f"Skipping injection - campaign status: {state.final_status.value}")
            state.injection_status = "skipped"
            return state
        
        try:
            # Determine delivery method based on lead data
            delivery_method = self._classify_lead_delivery_method(state.lead_data)
            state.delivery_method = delivery_method
            
            # Always save AI message to Airtable first
            await self._save_ai_message_to_airtable(state)
            
            if delivery_method == "email_automated":
                # Handle automated email delivery
                await self._handle_email_automated(state)
            elif delivery_method == "manual_linkedin":
                # Handle manual LinkedIn (save to Airtable for operator)
                await self._handle_manual_linkedin(state)
            else:
                # Insufficient contact info
                state.injection_status = "failed"
                state.status_reason = "Insufficient contact information"
                state.final_status = CampaignStatus.MANUAL_REVIEW
                
        except Exception as e:
            self.logger.error(f"Injection error: {str(e)}")
            state.injection_status = "error"
            state.final_status = CampaignStatus.ERROR
            state.status_reason = f"Injection error: {str(e)}"
            state.add_error("injector", e)
        
        return state
    
    def _classify_lead_delivery_method(self, lead_data: Dict[str, Any]) -> str:
        """
        Determine delivery method:
        - Valid email = automated email delivery
        - No valid email = manual LinkedIn (stored in Airtable for operator)
        
        Returns: "email_automated", "manual_linkedin", or "insufficient_contact_info"
        """
        has_valid_email = lead_data.get('Email') and self._validate_email(lead_data['Email'])
        has_contact_info = (lead_data.get('LinkedIn_URL') and self._validate_linkedin_url(lead_data['LinkedIn_URL'])) or lead_data.get('Name')
        
        if has_valid_email:
            return "email_automated"  # Automated email delivery
        elif has_contact_info:
            return "manual_linkedin"  # Manual LinkedIn (saved to Airtable)
        else:
            return "insufficient_contact_info"
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_linkedin_url(self, linkedin_url: str) -> bool:
        """Basic LinkedIn URL validation"""
        return linkedin_url and 'linkedin.com' in linkedin_url.lower()
    
    async def _handle_email_delivery(self, state: CampaignState):
        """Handle email delivery through queue system"""
        # Prepare campaign for injection
        campaign_payload = self._prepare_campaign_payload(state)
        
        # Attempt injection
        injection_result = await self._inject_to_queue(campaign_payload, state)
        
        if injection_result['success']:
            state.injection_status = "success"
            state.queue_id = injection_result['queue_id']
            state.delivery_schedule = injection_result['delivery_schedule']
            
            self.log_decision(
                state,
                "Successfully injected to email queue",
                f"Queue ID: {state.queue_id}"
            )
            
            self.logger.info(f"Email campaign injected successfully: {state.queue_id}")
            
        else:
            state.injection_status = "failed"
            state.status_reason = f"Email injection failed: {injection_result['error']}"
            
            self.log_decision(
                state,
                "Email injection failed",
                injection_result['error']
            )
            
            # If injection fails, mark for manual review
            state.final_status = CampaignStatus.MANUAL_REVIEW
    
    async def _handle_email_automated(self, state: CampaignState):
        """Handle automated email delivery"""
        try:
            # Prepare campaign for injection
            campaign_payload = self._prepare_campaign_payload(state)
            
            # Attempt injection
            injection_result = await self._inject_to_queue(campaign_payload, state)
            
            if injection_result['success']:
                state.injection_status = "success"
                state.queue_id = injection_result['queue_id']
                state.delivery_schedule = injection_result['delivery_schedule']
                
                self.log_decision(
                    state,
                    "Successfully injected to email queue",
                    f"Queue ID: {state.queue_id}"
                )
                
                self.logger.info(f"Email campaign injected successfully: {state.queue_id}")
                
            else:
                state.injection_status = "failed"
                state.status_reason = f"Email injection failed: {injection_result['error']}"
                state.final_status = CampaignStatus.MANUAL_REVIEW
                
        except Exception as e:
            self.logger.error(f"Email automation error: {str(e)}")
            state.injection_status = "error"
            state.final_status = CampaignStatus.ERROR
            state.status_reason = f"Email automation error: {str(e)}"
            state.add_error("email_automation", e)
    
    async def _handle_manual_linkedin(self, state: CampaignState):
        """Handle manual LinkedIn (save to Airtable for operator to send manually)"""
        try:
            # Format campaign for manual LinkedIn sending
            formatted_campaign = self._format_manual_campaign(state.messages, state.lead_data)
            state.formatted_linkedin_campaign = formatted_campaign
            
            # Update Airtable with manual LinkedIn fields
            airtable_success = await self._update_airtable_ai_message(state, formatted_campaign)
            
            if airtable_success:
                state.injection_status = "success"
                state.airtable_update_status = "success"
                
                self.log_decision(
                    state,
                    "Successfully saved manual LinkedIn campaign",
                    f"Campaign saved to Airtable for manual sending"
                )
                
                self.logger.info(f"Manual LinkedIn campaign saved for {state.lead_data.get('Name')}")
                
            else:
                state.injection_status = "failed"
                state.airtable_update_status = "failed"
                state.status_reason = "Failed to update Airtable with manual LinkedIn campaign"
                state.final_status = CampaignStatus.MANUAL_REVIEW
                
        except Exception as e:
            self.logger.error(f"Manual LinkedIn delivery error: {str(e)}")
            state.injection_status = "error"
            state.airtable_update_status = "error"
            state.status_reason = f"Manual LinkedIn error: {str(e)}"
            state.add_error("manual_linkedin_delivery", e)
    
    def _format_manual_campaign(self, messages, lead_data: Dict[str, Any]) -> str:
        """
        Format 3-message campaign for manual sending
        
        Format: HOOK: [message]  PROOF: [message]  FOMO: [message]
        """
        formatted_sections = []
        
        for message in messages:
            message_type = message.message_type.upper()
            content = self._personalize_for_manual_sending(message.body, lead_data)
            formatted_sections.append(f"{message_type}: {content}")
        
        return "  ".join(formatted_sections)
    
    def _personalize_for_manual_sending(self, content: str, lead_data: Dict[str, Any]) -> str:
        """
        Replace specific names with placeholders for manual customization
        """
        # Replace actual names with placeholders for manual customization
        first_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else ''
        company = lead_data.get('Company', '')
        
        if first_name:
            content = content.replace(first_name, '{{first_name}}')
        if company:
            content = content.replace(company, '{{company}}')
            
        return content
    
    async def _save_ai_message_to_airtable(self, state: CampaignState):
        """Save AI message to Airtable regardless of delivery method"""
        try:
            # Format campaign for AI message field
            formatted_campaign = self._format_manual_campaign(state.messages, state.lead_data)
            
            # Update Airtable with AI message and metadata
            airtable_success = await self._update_airtable_ai_message(state, formatted_campaign)
            
            if airtable_success:
                self.logger.info(f"✅ AI message saved to Airtable for {state.lead_data.get('Name')}")
            else:
                self.logger.warning(f"⚠️ Failed to save AI message to Airtable for {state.lead_data.get('Name')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error saving AI message to Airtable: {str(e)}")

    
    async def _update_airtable_ai_message(self, state: CampaignState, formatted_campaign: str) -> bool:
        """
        Update Airtable AI Message field for manual sending
        
        Updates:
        - AI Message: formatted campaign content for manual sending
        """
        try:
            lead_id = state.lead_data.get('id')
            if not lead_id:
                self.logger.error("No lead ID provided for Airtable update")
                return False
            
            # Determine message type and metadata
            used_fallback = state.fallback_mode
            fallback_reason = state.data_quality.get('fallback_reason', '') if used_fallback else ''
            quality_score = state.overall_quality_score
            
            # Determine message tone based on generation
            message_tone = 'bold' if used_fallback else 'consultative'
            if used_fallback:
                if 'no_website_data' in fallback_reason:
                    message_tone = 'curious'
                elif 'low_signal_website' in fallback_reason:
                    message_tone = 'bold'
                elif 'insufficient_enrichment' in fallback_reason:
                    message_tone = 'strategic'
            
            # Create extra info with metadata
            extra_info_parts = []
            extra_info_parts.append(f"Quality Score: {quality_score:.1f}/100")
            extra_info_parts.append(f"Used Fallback: {'Yes' if used_fallback else 'No'}")
            if used_fallback:
                extra_info_parts.append(f"Fallback Reason: {fallback_reason}")
            extra_info_parts.append(f"Message Tone: {message_tone}")
            extra_info_parts.append(f"Data Quality: {state.data_quality.get('quality_score', 0)}/10")
            
            # Add website quality info if available
            website_quality = state.data_quality.get('website_quality', {})
            if website_quality:
                extra_info_parts.append(f"Website Insights: {website_quality.get('concrete_insights', 0)}")
                if website_quality.get('low_signal'):
                    extra_info_parts.append("Website: Low Signal Content")
            
            extra_info = " | ".join(extra_info_parts)
            
            # Prepare update data with all required fields
            update_data = {
                'AI Message': formatted_campaign,
                'Messaging Method': 'Manual LinkedIn',
                'Manual Message Sent': False,
                'AI Message Type': 'fallback' if used_fallback else 'personalized',
                'Extra Info': extra_info
            }
            
            # Try to update Airtable if client is available
            airtable_success = False
            is_test_lead = lead_id.startswith(('test_', 'linkedin_test_', 'email_test_'))
            
            if self.airtable_client and not is_test_lead:
                try:
                    airtable_success = self.airtable_client.update_lead_fields(lead_id, update_data)
                    if airtable_success:
                        self.logger.info(f"Successfully updated Airtable for lead {lead_id}")
                    else:
                        self.logger.error(f"Failed to update Airtable for lead {lead_id}")
                except Exception as e:
                    self.logger.error(f"Airtable update error for lead {lead_id}: {str(e)}")
                    airtable_success = False
            elif is_test_lead:
                self.logger.info(f"Test lead detected ({lead_id}) - skipping Airtable update")
                airtable_success = True  # Consider test leads as successful
            else:
                self.logger.warning("Airtable client not available - saving to file only")
                airtable_success = True  # Consider file-only mode as successful
            
            # Always save to file for backup/testing purposes
            self._save_linkedin_campaign_to_file(state, formatted_campaign, update_data)
            
            return airtable_success
            
        except Exception as e:
            self.logger.error(f"LinkedIn Airtable update failed: {str(e)}")
            return False
    
    def _save_linkedin_campaign_to_file(self, state: CampaignState, formatted_campaign: str, update_data: Dict):
        """Save LinkedIn campaign to file for testing purposes"""
        try:
            # Create LinkedIn campaigns directory
            linkedin_dir = self.config.__dict__.get('linkedin_dir', 'linkedin_campaigns')
            import os
            os.makedirs(linkedin_dir, exist_ok=True)
            
            # Save campaign file
            lead_name = state.lead_data.get('Name', 'unknown').replace(' ', '_')
            campaign_file = os.path.join(linkedin_dir, f"linkedin_{lead_name}_{state.execution_id[:8]}.json")
            
            campaign_data = {
                'execution_id': state.execution_id,
                'lead_data': {
                    'name': state.lead_data.get('Name'),
                    'company': state.lead_data.get('Company'),
                    'linkedin_url': state.lead_data.get('LinkedIn_URL')
                },
                'formatted_campaign': formatted_campaign,
                'airtable_updates': update_data,
                'campaign_metadata': {
                    'traits': state.traits,
                    'messaging_angle': state.messaging_angle,
                    'campaign_tone': state.campaign_tone,
                    'overall_quality_score': state.overall_quality_score
                },
                'created_at': datetime.now().isoformat()
            }
            
            with open(campaign_file, 'w') as f:
                json.dump(campaign_data, f, indent=2, default=str)
            
            self.logger.info(f"LinkedIn campaign saved to: {campaign_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save LinkedIn campaign to file: {str(e)}")

    def _prepare_campaign_payload(self, state: CampaignState) -> Dict[str, Any]:
        """Prepare campaign data for queue injection"""
        
        # Generate unique campaign ID
        campaign_id = f"brain_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Prepare messages for delivery
        messages = []
        for i, message in enumerate(state.messages):
            message_data = {
                'message_number': i + 1,
                'message_type': message.message_type,
                'subject': message.subject,
                'body': message.body,
                'quality_score': message.quality_score,
                'generation_attempt': message.generation_attempt,
                'scheduled_date': self._calculate_send_date(i),
                'status': 'scheduled'
            }
            messages.append(message_data)
        
        # Prepare full campaign payload
        payload = {
            'campaign_id': campaign_id,
            'lead_id': state.lead_data.get('id', 'unknown'),
            'lead_data': {
                'name': state.lead_data.get('Name', ''),
                'email': state.lead_data.get('Email', ''),
                'title': state.lead_data.get('Title', ''),
                'company': state.lead_data.get('Company', '')
            },
            'campaign_metadata': {
                'traits': state.traits,
                'primary_trait': state.primary_trait,
                'messaging_angle': state.messaging_angle,
                'campaign_tone': state.campaign_tone,
                'overall_quality_score': state.overall_quality_score,
                'generated_by': 'campaign_brain',
                'execution_id': state.execution_id
            },
            'messages': messages,
            'created_at': datetime.now().isoformat(),
            'campaign_status': 'active'
        }
        
        return payload
    
    def _calculate_send_date(self, message_index: int) -> str:
        """Calculate when each message should be sent"""
        
        # Standard schedule: Day 0, Day 3, Day 7
        send_delays = [0, 3, 7]
        
        if message_index < len(send_delays):
            delay_days = send_delays[message_index]
        else:
            # For additional messages, add 3 days each
            delay_days = 7 + (message_index - 2) * 3
        
        send_date = datetime.now() + timedelta(days=delay_days)
        
        # Adjust for business days (skip weekends)
        while send_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            send_date += timedelta(days=1)
        
        return send_date.isoformat()
    
    async def _inject_to_queue(self, payload: Dict[str, Any], state: CampaignState) -> Dict[str, Any]:
        """Inject campaign to message queue system"""
        
        try:
            # For now, simulate queue injection
            # In production, this would integrate with actual queue system
            queue_id = f"queue_{uuid.uuid4().hex[:12]}"
            
            # Simulate queue injection logic
            injection_success = await self._simulate_queue_injection(payload)
            
            if injection_success:
                # Calculate delivery schedule
                delivery_schedule = {}
                for message in payload['messages']:
                    delivery_schedule[message['message_type']] = datetime.fromisoformat(message['scheduled_date'])
                
                return {
                    'success': True,
                    'queue_id': queue_id,
                    'delivery_schedule': delivery_schedule,
                    'message': 'Campaign successfully queued for delivery'
                }
            else:
                return {
                    'success': False,
                    'error': 'Queue injection failed - simulated failure',
                    'queue_id': None
                }
                
        except Exception as e:
            self.logger.error(f"Queue injection error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'queue_id': None
            }
    
    async def _simulate_queue_injection(self, payload: Dict[str, Any]) -> bool:
        """Simulate queue injection for testing purposes"""
        
        # Simulate validation checks
        required_fields = ['campaign_id', 'lead_data', 'messages']
        for field in required_fields:
            if field not in payload:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate lead data
        lead_data = payload['lead_data']
        if not lead_data.get('email'):
            self.logger.error("No email address in lead data")
            return False
        
        # Validate messages
        messages = payload['messages']
        if not messages:
            self.logger.error("No messages in campaign")
            return False
        
        for message in messages:
            if not message.get('subject') or not message.get('body'):
                self.logger.error(f"Incomplete message: {message.get('message_type')}")
                return False
        
        # Simulate queue storage
        self._save_to_simulated_queue(payload)
        
        self.logger.debug(f"Simulated queue injection successful for campaign: {payload['campaign_id']}")
        return True
    
    def _save_to_simulated_queue(self, payload: Dict[str, Any]):
        """Save campaign to simulated queue file for testing"""
        
        try:
            # Create queue directory
            queue_dir = self.config.__dict__.get('queue_dir', 'queue_simulation')
            import os
            os.makedirs(queue_dir, exist_ok=True)
            
            # Save campaign file
            campaign_file = os.path.join(queue_dir, f"{payload['campaign_id']}.json")
            with open(campaign_file, 'w') as f:
                json.dump(payload, f, indent=2, default=str)
            
            self.logger.debug(f"Campaign saved to simulated queue: {campaign_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save to simulated queue: {str(e)}")
    
    def _update_airtable_status(self, state: CampaignState) -> bool:
        """Update Airtable with campaign status (placeholder)"""
        
        try:
            # This would integrate with existing Airtable client
            # For now, just log the update
            
            lead_id = state.lead_data.get('id')
            update_data = {
                'Campaign_ID': state.queue_id,
                'Campaign_Status': 'Active',
                'Campaign_Started_Date': datetime.now().date().isoformat(),
                'Overall_Quality_Score': state.overall_quality_score,
                'Messaging_Angle': state.messaging_angle,
                'Campaign_Tone': state.campaign_tone
            }
            
            self.logger.info(f"Would update Airtable for lead {lead_id}: {update_data}")
            return True
            
        except Exception as e:
            self.logger.error(f"Airtable update failed: {str(e)}")
            return False
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for injection"""
        if not super().validate_input(state):
            return False
        
        # Check if we have messages to inject
        if not state.messages:
            self.logger.error("No messages to inject")
            return False
        
        # Check if lead has either email or LinkedIn URL
        has_email = bool(state.lead_data.get('Email'))
        has_linkedin = bool(state.lead_data.get('LinkedIn_URL'))
        
        if not has_email and not has_linkedin:
            self.logger.error("No email address or LinkedIn URL for lead")
            return False
        
        return True
    
    def get_injection_summary(self, state: CampaignState) -> Dict[str, Any]:
        """Get summary of injection results"""
        summary = {
            'injection_status': state.injection_status,
            'delivery_method': getattr(state, 'delivery_method', 'unknown'),
            'campaign_status': state.final_status.value,
            'message_count': len(state.messages),
            'overall_quality_score': state.overall_quality_score
        }
        
        # Add delivery-method specific info
        if getattr(state, 'delivery_method', None) == 'email_queue':
            summary.update({
                'queue_id': state.queue_id,
                'delivery_schedule': state.delivery_schedule,
                'lead_email': state.lead_data.get('Email')
            })
        elif getattr(state, 'delivery_method', None) == 'linkedin_manual':
            summary.update({
                'airtable_update_status': getattr(state, 'airtable_update_status', None),
                'linkedin_url': state.lead_data.get('LinkedIn_URL'),
                'formatted_campaign_preview': getattr(state, 'formatted_linkedin_campaign', '')[:100] + '...' if getattr(state, 'formatted_linkedin_campaign', '') else None
            })
        
        return summary