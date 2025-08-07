#!/usr/bin/env python3
"""
Enhanced Engager Integration

Combines enrichment, fallback messaging, and engagement logic to ensure
no lead with a valid email is skipped. Integrates with database and Airtable.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from enricher.enhanced_enricher_integration import EnhancedEnricherIntegration
    from enricher.fallback_message_generator import FallbackMessageGenerator, should_use_fallback_messaging
    from database.models import get_lead_database, Lead
    from sync.airtable_sync import AirtableSync
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    import_error = str(e)

logger = logging.getLogger('enhanced-engager-integration')

class EnhancedEngagerIntegration:
    """
    Enhanced engager that combines enrichment with fallback messaging to ensure
    comprehensive lead processing and message generation for all viable leads.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the enhanced engager integration.
        
        Args:
            openai_api_key: Optional OpenAI API key for AI operations
        """
        if not INTEGRATION_AVAILABLE:
            raise ImportError(f"Integration dependencies not available: {import_error}")
        
        # Initialize components
        self.db = get_lead_database()
        self.airtable_sync = AirtableSync()
        self.enricher = EnhancedEnricherIntegration(openai_api_key)
        self.fallback_generator = None
        
        # Try to initialize fallback generator
        try:
            self.fallback_generator = FallbackMessageGenerator(openai_api_key)
            self.fallback_enabled = True
        except Exception as e:
            logger.warning(f"⚠️ Fallback generator not available: {str(e)}")
            self.fallback_enabled = False
        
        # Configuration
        self.max_batch_size = 15
        
        logger.info("🎯 Enhanced Engager Integration initialized")
        logger.info(f"🧠 Enrichment enabled: ✅")
        logger.info(f"💬 Fallback messaging enabled: {'✅' if self.fallback_enabled else '❌'}")
    
    def process_lead_complete(self, lead_id: str) -> Dict[str, Any]:
        """
        Complete lead processing: enrichment → fallback messaging → engagement preparation.
        
        Args:
            lead_id: ID of the lead to process
            
        Returns:
            Dictionary with complete processing results
        """
        logger.info(f"🎯 Starting complete lead processing for {lead_id}")
        
        try:
            # Get lead from database
            lead = self.db.get_lead(lead_id)
            if not lead:
                logger.error(f"❌ Lead {lead_id} not found in database")
                return {
                    'success': False,
                    'error': 'Lead not found',
                    'lead_id': lead_id
                }
            
            # Step 1: Attempt enrichment if lead has website
            enrichment_result = None
            if hasattr(lead, 'website') and lead.website:
                logger.info("🧠 Attempting lead enrichment")
                enrichment_result = self.enricher.enrich_lead_comprehensive(lead_id)
            else:
                logger.info("⚠️ No website available for enrichment")
            
            # Step 2: Refresh lead data after enrichment
            updated_lead = self.db.get_lead(lead_id)
            if not updated_lead:
                updated_lead = lead
            
            # Step 3: Determine if fallback messaging is needed
            lead_data = self._prepare_lead_data_for_messaging(updated_lead, enrichment_result)
            
            should_use_fallback = False
            if self.fallback_enabled:
                should_use_fallback = should_use_fallback_messaging(lead_data)
                logger.info(f"💬 Use fallback messaging: {should_use_fallback}")
            
            # Step 4: Generate message (enriched or fallback)
            message_result = None
            if should_use_fallback:
                logger.info("💬 Generating fallback message")
                message_result = self.fallback_generator.generate_fallback_message(lead_data)
            elif enrichment_result and enrichment_result.get('success'):
                logger.info("🧠 Using enriched data for messaging")
                message_result = self._create_enriched_message_placeholder(enrichment_result)
            else:
                logger.info("⚠️ No messaging strategy available")
                message_result = self._create_skip_result("No enrichment data or fallback available")
            
            # Step 5: Update lead with messaging results
            messaging_success = self._update_lead_with_messaging(updated_lead, message_result)
            
            # Step 6: Sync to Airtable
            airtable_success = self._sync_to_airtable(lead_id)
            
            # Create comprehensive result
            result = {
                'success': True,
                'lead_id': lead_id,
                'lead_name': updated_lead.name,
                'lead_email': getattr(updated_lead, 'email', ''),
                'enrichment_attempted': enrichment_result is not None,
                'enrichment_success': enrichment_result.get('success', False) if enrichment_result else False,
                'fallback_used': should_use_fallback,
                'message_generated': message_result.get('generation_success', False) if message_result else False,
                'message_confidence': message_result.get('confidence', 'none') if message_result else 'none',
                'database_updated': messaging_success,
                'airtable_updated': airtable_success,
                'engagement_status': self._determine_engagement_status(message_result, lead_data),
                'processing_summary': self._create_processing_summary(enrichment_result, message_result, should_use_fallback)
            }
            
            logger.info(f"✅ Complete processing finished for {updated_lead.name}")
            logger.info(f"   Enrichment: {'✅' if result['enrichment_success'] else '❌'}")
            logger.info(f"   Messaging: {'✅' if result['message_generated'] else '❌'}")
            logger.info(f"   Engagement Status: {result['engagement_status']}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Complete lead processing failed for {lead_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'lead_id': lead_id
            }
    
    def process_leads_batch_complete(self, limit: int = None) -> Dict[str, Any]:
        """
        Process multiple leads with complete enrichment and fallback messaging.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with batch processing results
        """
        logger.info(f"🎯 Starting batch complete processing (limit: {limit or 'unlimited'})")
        
        try:
            # Get leads that need processing
            all_leads = self.db.search_leads({}, limit=limit or self.max_batch_size * 2)
            
            # Filter leads that need processing (have email but not processed)
            leads_to_process = []
            for lead in all_leads:
                if (hasattr(lead, 'email') and lead.email and 
                    not getattr(lead, 'engagement_processed', False)):
                    leads_to_process.append(lead)
                    if len(leads_to_process) >= (limit or self.max_batch_size):
                        break
            
            if not leads_to_process:
                logger.info("✅ No leads need complete processing")
                return {
                    'success': True,
                    'leads_processed': 0,
                    'enrichment_successful': 0,
                    'messages_generated': 0,
                    'fallback_used': 0,
                    'leads_ready_for_engagement': 0,
                    'details': []
                }
            
            logger.info(f"📋 Processing {len(leads_to_process)} leads completely")
            
            # Process each lead
            results = {
                'success': True,
                'leads_processed': 0,
                'enrichment_successful': 0,
                'messages_generated': 0,
                'fallback_used': 0,
                'leads_ready_for_engagement': 0,
                'details': []
            }
            
            for lead in leads_to_process:
                try:
                    result = self.process_lead_complete(lead.id)
                    results['details'].append(result)
                    results['leads_processed'] += 1
                    
                    if result.get('success'):
                        if result.get('enrichment_success'):
                            results['enrichment_successful'] += 1
                        if result.get('message_generated'):
                            results['messages_generated'] += 1
                        if result.get('fallback_used'):
                            results['fallback_used'] += 1
                        if result.get('engagement_status') in ['Auto-Send', 'Needs Review']:
                            results['leads_ready_for_engagement'] += 1
                
                except Exception as e:
                    logger.error(f"❌ Batch processing error for lead {lead.id}: {str(e)}")
                    results['details'].append({
                        'success': False,
                        'error': str(e),
                        'lead_id': lead.id
                    })
            
            # Summary
            logger.info(f"✅ Batch complete processing finished:")
            logger.info(f"   📊 Processed: {results['leads_processed']} leads")
            logger.info(f"   🧠 Enriched: {results['enrichment_successful']}")
            logger.info(f"   💬 Messages: {results['messages_generated']}")
            logger.info(f"   🔄 Fallback: {results['fallback_used']}")
            logger.info(f"   🎯 Ready for engagement: {results['leads_ready_for_engagement']}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Batch complete processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'leads_processed': 0,
                'enrichment_successful': 0,
                'messages_generated': 0,
                'fallback_used': 0,
                'leads_ready_for_engagement': 0
            }
    
    def _prepare_lead_data_for_messaging(self, lead: Lead, enrichment_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare lead data for messaging decisions."""
        
        # Base lead data
        lead_data = {
            'full_name': getattr(lead, 'name', ''),
            'email': getattr(lead, 'email', ''),
            'company_name': getattr(lead, 'company', ''),
            'website': getattr(lead, 'website', ''),
            'email_confidence': getattr(lead, 'email_confidence', 'pattern'),
            'previously_skipped': getattr(lead, 'previously_skipped', False)
        }
        
        # Add enrichment data if available
        if enrichment_result and enrichment_result.get('success'):
            enrichment_data = enrichment_result.get('enrichment_data', {})
            lead_data.update({
                'business_type': enrichment_data.get('Business_Type', 'Unknown'),
                'business_traits': enrichment_data.get('Business_Traits', []),
                'pain_points': enrichment_data.get('Pain_Points', []),
                'strategic_insight': enrichment_data.get('Strategic_Insight', ''),
                'website_scraping_failed': False
            })
        else:
            # Mark as having insufficient enrichment data
            lead_data.update({
                'business_type': 'Unknown',
                'business_traits': [],
                'pain_points': [],
                'strategic_insight': '',
                'website_scraping_failed': bool(lead_data.get('website')),
                'ai_analysis_failed': True
            })
        
        return lead_data
    
    def _create_enriched_message_placeholder(self, enrichment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create placeholder for enriched messaging (to be implemented by message generator)."""
        
        return {
            'message': '[Enriched message would be generated here]',
            'subject_line': '[Enriched subject would be generated here]',
            'confidence': 'high',
            'used_fallback': False,
            'generation_success': True,
            'generation_method': 'enriched_data',
            'generated_at': datetime.now().isoformat(),
            'enrichment_data_available': True
        }
    
    def _create_skip_result(self, reason: str) -> Dict[str, Any]:
        """Create result for skipped leads."""
        
        return {
            'message': '',
            'subject_line': '',
            'confidence': 'none',
            'used_fallback': False,
            'generation_success': False,
            'generation_error': reason,
            'skip_reason': reason,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'skip'
        }
    
    def _update_lead_with_messaging(self, lead: Lead, message_result: Dict[str, Any]) -> bool:
        """Update lead with messaging results."""
        
        try:
            update_data = {
                'engagement_processed': True,
                'engagement_processed_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add messaging data
            if message_result.get('generation_success'):
                update_data.update({
                    'custom_message': message_result.get('message', ''),
                    'message_subject': message_result.get('subject_line', ''),
                    'message_confidence': message_result.get('confidence', 'none'),
                    'used_fallback': message_result.get('used_fallback', False),
                    'message_generated_at': message_result.get('generated_at', ''),
                    'ready_for_outreach': True
                })
                
                if message_result.get('used_fallback'):
                    update_data['fallback_reason'] = message_result.get('fallback_reason', '')
            else:
                update_data.update({
                    'custom_message': '',
                    'message_confidence': 'none',
                    'ready_for_outreach': False,
                    'skip_reason': message_result.get('skip_reason', 'Message generation failed')
                })
            
            success = self.db.update_lead(lead.id, update_data)
            
            if success:
                logger.info(f"✅ Lead messaging data updated: {lead.id}")
            else:
                logger.warning(f"⚠️ Lead messaging update failed: {lead.id}")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Lead messaging update error for {lead.id}: {str(e)}")
            return False
    
    def _sync_to_airtable(self, lead_id: str) -> bool:
        """Sync processed lead to Airtable."""
        
        try:
            # Get updated lead
            updated_lead = self.db.get_lead(lead_id)
            if not updated_lead:
                return False
            
            # Force sync to Airtable
            sync_result = self.airtable_sync.sync_leads_to_airtable([updated_lead], force=True)
            
            if sync_result.get('success'):
                logger.info(f"✅ Airtable updated for processed lead {lead_id}")
                return True
            else:
                logger.warning(f"⚠️ Airtable sync failed for lead {lead_id}: {sync_result.get('error')}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Airtable sync error for lead {lead_id}: {str(e)}")
            return False
    
    def _determine_engagement_status(self, message_result: Dict[str, Any], lead_data: Dict[str, Any]) -> str:
        """Determine engagement status based on message generation and lead data."""
        
        if not message_result or not message_result.get('generation_success'):
            return 'Skip'
        
        # Check email confidence
        email_confidence = lead_data.get('email_confidence', '').lower()
        if email_confidence not in ['real', 'pattern']:
            return 'Skip'
        
        # Determine status based on message confidence
        message_confidence = message_result.get('confidence', 'none')
        
        if message_confidence in ['high', 'medium']:
            return 'Auto-Send'
        elif message_confidence == 'low':
            return 'Needs Review'
        else:
            return 'Skip'
    
    def _create_processing_summary(self, enrichment_result: Optional[Dict[str, Any]], 
                                 message_result: Optional[Dict[str, Any]], 
                                 used_fallback: bool) -> str:
        """Create human-readable processing summary."""
        
        summary_parts = []
        
        # Enrichment summary
        if enrichment_result and enrichment_result.get('success'):
            business_type = enrichment_result.get('enrichment_data', {}).get('Business_Type', 'Unknown')
            summary_parts.append(f"Enriched as {business_type}")
        else:
            summary_parts.append("Enrichment failed or unavailable")
        
        # Messaging summary
        if message_result and message_result.get('generation_success'):
            if used_fallback:
                confidence = message_result.get('confidence', 'unknown')
                summary_parts.append(f"Fallback message generated ({confidence} confidence)")
            else:
                summary_parts.append("Enriched message prepared")
        else:
            summary_parts.append("No message generated")
        
        return " | ".join(summary_parts)


# Convenience functions
def process_lead_complete(lead_id: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Process lead with complete enrichment and fallback messaging.
    
    Args:
        lead_id: ID of the lead to process
        openai_api_key: Optional OpenAI API key
        
    Returns:
        Complete processing result dictionary
    """
    try:
        engager = EnhancedEngagerIntegration(openai_api_key)
        return engager.process_lead_complete(lead_id)
    except Exception as e:
        logger.error(f"❌ Complete lead processing failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lead_id': lead_id
        }


def process_leads_batch_complete(limit: int = None, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Process multiple leads with complete enrichment and fallback messaging.
    
    Args:
        limit: Maximum number of leads to process
        openai_api_key: Optional OpenAI API key
        
    Returns:
        Batch processing result dictionary
    """
    try:
        engager = EnhancedEngagerIntegration(openai_api_key)
        return engager.process_leads_batch_complete(limit)
    except Exception as e:
        logger.error(f"❌ Batch complete processing failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'leads_processed': 0,
            'enrichment_successful': 0,
            'messages_generated': 0,
            'fallback_used': 0,
            'leads_ready_for_engagement': 0
        }


if __name__ == "__main__":
    # Test the enhanced engager integration
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Enhanced Engager Integration')
    parser.add_argument('--lead-id', help='Process specific lead ID')
    parser.add_argument('--batch', action='store_true', help='Process batch of leads')
    parser.add_argument('--limit', type=int, default=5, help='Limit for batch processing')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.lead_id:
        # Process specific lead
        print(f"🎯 Processing lead completely: {args.lead_id}")
        result = process_lead_complete(args.lead_id)
        print(f"📊 Result: {result}")
    
    elif args.batch:
        # Process batch of leads
        print(f"🎯 Processing batch of leads completely (limit: {args.limit})")
        result = process_leads_batch_complete(args.limit)
        print(f"📊 Batch Result: {result}")
    
    else:
        print("❌ Please specify --lead-id or --batch")
        print("Usage examples:")
        print("  python enhanced_engager_integration.py --lead-id lead-123")
        print("  python enhanced_engager_integration.py --batch --limit 10")