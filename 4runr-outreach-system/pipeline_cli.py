#!/usr/bin/env python3
"""
Enhanced pipeline CLI for the 4Runr Autonomous Outreach System.

Integrates enhanced website scraping, trait inference, modular message generation,
and email sending with comprehensive logging and feedback collection.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.logging_utils import get_logger
from shared.airtable_client import get_airtable_client
from shared.validation import validate_email_format, validate_airtable_fields
from shared.config import config

# Import enhanced modules
from scraper.scrape_site import EnhancedWebsiteScraper
from enricher.infer_traits import ICPTraitInference
from generator.generate_message import ModularMessageGenerator
from sender.send_via_graph import GraphEmailSender


class EnhancedOutreachPipeline:
    """Enhanced autonomous outreach pipeline with modular components."""
    
    def __init__(self):
        """Initialize the enhanced pipeline."""
        self.logger = get_logger('enhanced_pipeline')
        self.airtable_client = get_airtable_client()
        
        # Initialize components
        self.scraper = EnhancedWebsiteScraper()
        self.trait_inference = ICPTraitInference()
        self.message_generator = ModularMessageGenerator()
        self.email_sender = GraphEmailSender()
        
        self.system_config = config.get_system_config()
    
    async def process_leads_enhanced(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads using the enhanced pipeline.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Processing statistics
        """
        # Get leads for processing
        batch_size = limit or self.system_config['batch_size']
        leads = self.airtable_client.get_leads_for_outreach(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('enhanced_pipeline', 'system', 'info', 
                                           {'message': 'No leads found for enhanced processing'})
            return {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead through enhanced pipeline
                result = await self._process_single_lead_enhanced(lead)
                
                stats['processed'] += 1
                if result == 'success':
                    stats['successful'] += 1
                elif result == 'skip':
                    stats['skipped'] += 1
                else:
                    stats['errors'] += 1
                
                # Rate limiting
                if i < len(leads) - 1:
                    await asyncio.sleep(self.system_config['rate_limit_delay'])
                    
            except Exception as e:
                self.logger.log_error(e, {
                    'action': 'process_leads_enhanced',
                    'lead_id': lead.get('id', 'unknown'),
                    'lead_index': i
                })
                stats['processed'] += 1
                stats['errors'] += 1
        
        self.logger.log_pipeline_complete(stats['processed'], stats['successful'], stats['errors'])
        return stats
    
    async def _process_single_lead_enhanced(self, lead: Dict[str, Any]) -> str:
        """
        Process a single lead through the enhanced pipeline.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        company = lead.get('Company', 'Unknown Company')
        website_url = lead.get('company_website_url', '')
        email = lead.get('Email', '')
        
        self.logger.log_module_activity('enhanced_pipeline', lead_id, 'start', 
                                       {'message': f'Enhanced processing for {lead_name} at {company}'})
        
        # Validation checks
        if not website_url:
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'skip', 
                                           {'message': 'No website URL provided'})
            return 'skip'
        
        if not email or not validate_email_format(email):
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'skip', 
                                           {'message': 'Invalid or missing email address'})
            return 'skip'
        
        try:
            # Step 1: Enhanced website scraping
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'info', 
                                           {'message': 'Step 1: Enhanced website scraping'})
            
            scraped_data = self.scraper.scrape_enhanced_data(website_url, lead_id)
            
            if not scraped_data.get('success'):
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                               {'message': 'Website scraping failed'})
                return 'error'
            
            # Step 2: Trait inference
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'info', 
                                           {'message': 'Step 2: ICP trait inference'})
            
            traits_data = self.trait_inference.infer_traits(scraped_data, lead)
            
            if not traits_data.get('success'):
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                               {'message': 'Trait inference failed'})
                return 'error'
            
            # Step 3: Enhanced message generation
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'info', 
                                           {'message': 'Step 3: Modular message generation'})
            
            message_result = self.message_generator.generate_enhanced_message(
                lead, scraped_data, traits_data
            )
            
            if not message_result.get('success'):
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                               {'message': 'Message generation failed'})
                return 'error'
            
            generated_message = message_result['message']
            
            # Step 4: Email sending
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'info', 
                                           {'message': 'Step 4: Email sending via Microsoft Graph'})
            
            send_success = await self.email_sender.send_enhanced_email(
                lead, generated_message, lead_id
            )
            
            if not send_success:
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                               {'message': 'Email sending failed'})
                return 'error'
            
            # Step 5: Update Airtable with enhanced data
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'info', 
                                           {'message': 'Step 5: Updating Airtable with enhanced data'})
            
            update_success = await self._update_airtable_enhanced(
                lead_id, scraped_data, traits_data, message_result
            )
            
            if update_success:
                # Step 6: Log engagement for feedback
                self._log_enhanced_engagement(lead, scraped_data, traits_data, message_result)
                
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'success', 
                                               {'message': f'Enhanced pipeline completed for {lead_name}',
                                                'industry': traits_data.get('traits', {}).get('industry'),
                                                'generation_method': message_result.get('generation_method'),
                                                'message_length': len(generated_message)})
                return 'success'
            else:
                return 'error'
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead_enhanced',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'company': company
            })
            return 'error'
    
    async def _update_airtable_enhanced(self, lead_id: str, scraped_data: Dict[str, Any], 
                                       traits_data: Dict[str, Any], message_result: Dict[str, Any]) -> bool:
        """Update Airtable with enhanced data from all pipeline stages."""
        try:
            # Prepare enhanced fields
            airtable_fields = {
                # Enhanced website data
                'Company_Description': scraped_data.get('meta_description', '')[:500],
                'Top_Services': ', '.join(scraped_data.get('features', [])[:5]),
                'Tone': traits_data.get('traits', {}).get('tone_preference', 'Professional').title(),
                'Website_Insights': json.dumps({
                    'headline': scraped_data.get('headline', ''),
                    'hero_copy': scraped_data.get('hero_copy', '')[:200],
                    'tech_keywords': scraped_data.get('tech_keywords_found', []),
                    'cta_buttons': scraped_data.get('cta_buttons', [])
                }, ensure_ascii=False)[:1000],
                
                # Enhanced message data
                'Custom_Message': message_result['message'],
                'Engagement_Status': 'Sent',
                'Message_Preview': message_result['message'][:500],
                'Last_Contacted_Date': datetime.now().date().isoformat(),
                'Delivery_Method': 'Email',
                
                # Enhanced analytics fields
                'Industry_Classification': traits_data.get('traits', {}).get('industry', ''),
                'Company_Size_Inferred': traits_data.get('traits', {}).get('company_size', ''),
                'Tech_Sophistication': traits_data.get('traits', {}).get('tech_sophistication', ''),
                'Generation_Method': message_result.get('generation_method', ''),
                'AI_Enhanced': message_result.get('ai_enhanced', False),
                'Confidence_Score': traits_data.get('confidence_score', 0.0),
                'Value_Props_Used': ', '.join(traits_data.get('value_props', [])[:3])
            }
            
            # Validate fields
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                               {'message': 'Enhanced field validation failed', 
                                                'errors': validation_result['errors']})
                return False
            
            # Update Airtable
            return self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'update_airtable_enhanced', 'lead_id': lead_id})
            return False
    
    def _log_enhanced_engagement(self, lead: Dict[str, Any], scraped_data: Dict[str, Any], 
                                traits_data: Dict[str, Any], message_result: Dict[str, Any]) -> None:
        """Log enhanced engagement data for feedback and improvement."""
        engagement_data = {
            'lead_id': lead.get('id', 'unknown'),
            'lead_name': lead.get('Name', 'Unknown'),
            'company': lead.get('Company', 'Unknown Company'),
            'email': lead.get('Email', ''),
            'website_url': lead.get('company_website_url', ''),
            
            # Enhanced scraping data
            'scraped_features_count': len(scraped_data.get('features', [])),
            'tech_keywords_found': scraped_data.get('tech_keywords_found', []),
            'mentions_ai_or_tech': scraped_data.get('mentions_ai_or_tech', False),
            'website_tone': scraped_data.get('tone_indicators', {}).get('primary_tone', ''),
            
            # Trait inference data
            'inferred_industry': traits_data.get('traits', {}).get('industry', ''),
            'company_size': traits_data.get('traits', {}).get('company_size', ''),
            'tech_sophistication': traits_data.get('traits', {}).get('tech_sophistication', ''),
            'confidence_score': traits_data.get('confidence_score', 0.0),
            'value_props_matched': len(traits_data.get('value_props', [])),
            
            # Message generation data
            'generation_method': message_result.get('generation_method', ''),
            'ai_enhanced': message_result.get('ai_enhanced', False),
            'message_length': len(message_result.get('message', '')),
            'template_blocks_used': message_result.get('template_blocks_used', []),
            
            # Engagement metadata
            'engagement_timestamp': datetime.now().isoformat(),
            'pipeline_version': 'enhanced_v1.0'
        }
        
        self.logger.save_engagement_log(engagement_data)
    
    async def process_specific_lead_enhanced(self, lead_id: str) -> str:
        """Process a specific lead through the enhanced pipeline."""
        lead = self.airtable_client.get_lead_by_id(lead_id)
        if not lead:
            self.logger.log_module_activity('enhanced_pipeline', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return 'error'
        
        return await self._process_single_lead_enhanced(lead)
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced processing statistics."""
        leads = self.airtable_client.get_leads_for_outreach(limit=1000)
        
        stats = {
            'total_leads_available': len(leads),
            'leads_with_websites': 0,
            'leads_without_websites': 0,
            'leads_with_valid_emails': 0,
            'leads_ready_for_enhanced_processing': 0
        }
        
        for lead in leads:
            if lead.get('company_website_url'):
                stats['leads_with_websites'] += 1
            else:
                stats['leads_without_websites'] += 1
            
            if lead.get('Email') and validate_email_format(lead['Email']):
                stats['leads_with_valid_emails'] += 1
            
            if (lead.get('company_website_url') and 
                lead.get('Email') and 
                validate_email_format(lead['Email'])):
                stats['leads_ready_for_enhanced_processing'] += 1
        
        return stats


# Create sender module
class GraphEmailSender:
    """Enhanced email sender using Microsoft Graph API."""
    
    def __init__(self):
        """Initialize the Graph email sender."""
        self.logger = get_logger('graph_sender')
    
    async def send_enhanced_email(self, lead: Dict[str, Any], message: str, lead_id: str) -> bool:
        """Send enhanced email via Microsoft Graph."""
        try:
            import requests
            
            # Get Graph configuration
            graph_config = {
                'client_id': config.get('MS_GRAPH_CLIENT_ID'),
                'client_secret': config.get('MS_GRAPH_CLIENT_SECRET'),
                'tenant_id': config.get('MS_GRAPH_TENANT_ID'),
                'sender_email': config.get('MS_GRAPH_SENDER_EMAIL')
            }
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{graph_config['tenant_id']}/oauth2/v2.0/token"
            token_data = {
                'client_id': graph_config['client_id'],
                'client_secret': graph_config['client_secret'],
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code != 200:
                return False
            
            access_token = token_response.json()['access_token']
            
            # Send email
            send_url = f"https://graph.microsoft.com/v1.0/users/{graph_config['sender_email']}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                "message": {
                    "subject": f"Strategic Partnership Opportunity - {lead.get('Company', '')}",
                    "body": {
                        "contentType": "Text",
                        "content": message
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": lead.get('Email', '')
                            }
                        }
                    ]
                }
            }
            
            send_response = requests.post(send_url, headers=headers, json=email_data)
            
            if send_response.status_code == 202:
                self.logger.log_module_activity('graph_sender', lead_id, 'success', 
                                               {'message': 'Email sent via Microsoft Graph'})
                return True
            else:
                self.logger.log_module_activity('graph_sender', lead_id, 'error', 
                                               {'message': f'Graph API error: {send_response.status_code}'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'send_enhanced_email', 'lead_id': lead_id})
            return False


async def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced 4Runr Outreach Pipeline')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show enhanced processing statistics')
    parser.add_argument('--test-components', action='store_true', help='Test individual components')
    
    args = parser.parse_args()
    
    pipeline = EnhancedOutreachPipeline()
    
    if args.stats:
        stats = pipeline.get_enhanced_stats()
        print("Enhanced Pipeline Statistics:")
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        return True
    
    if args.test_components:
        print("Testing enhanced pipeline components...")
        # Add component testing logic here
        return True
    
    if args.lead_id:
        result = await pipeline.process_specific_lead_enhanced(args.lead_id)
        print(f"Enhanced processing result: {result}")
        return result == 'success'
    
    # Process leads in batch
    results = await pipeline.process_leads_enhanced(limit=args.limit)
    
    print("Enhanced Pipeline Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)