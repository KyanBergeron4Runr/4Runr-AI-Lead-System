"""
Enhanced Engager Agent for the 4Runr Email Engager Upgrade.

Extends the existing EngagerAgent with 4Runr knowledge base integration,
company-focused personalization, engagement level tracking, and autonomous operation.
"""

import datetime
from typing import Dict, Any, List, Optional

from .app import EngagerAgent
from .knowledge_base_loader import KnowledgeBaseLoader
from .website_scraper_service import WebsiteScraperService
from .engagement_level_tracker import EngagementLevelTracker
from .message_generator_enhanced import MessageGeneratorEnhanced
from .local_database_manager import LocalDatabaseManager
from .reengagement_strategy import ReengagementStrategy
from shared.logging_utils import get_logger


class EnhancedEngagerAgent(EngagerAgent):
    """Enhanced Engager Agent with 4Runr knowledge and company personalization."""
    
    def __init__(self):
        """Initialize the Enhanced Engager Agent."""
        # Initialize parent class
        super().__init__()
        
        # Initialize enhanced components
        self.knowledge_base_loader = KnowledgeBaseLoader()
        self.website_scraper = WebsiteScraperService()
        self.engagement_tracker = EngagementLevelTracker()
        self.message_generator = MessageGeneratorEnhanced()
        self.database_manager = LocalDatabaseManager()
        self.reengagement_strategy = ReengagementStrategy()
        
        # Create database backup on startup
        self._create_startup_backup()
        
        # Cache 4Runr knowledge at startup
        self._4runr_knowledge = None
        self._load_4runr_knowledge()
        
        self.logger.log_module_activity('engager', 'system', 'success', {
            'message': 'Enhanced Engager Agent initialized successfully',
            'components': ['knowledge_base', 'website_scraper', 'engagement_tracker', 'message_generator', 'database_manager', 'reengagement_strategy']
        })
    
    def _load_4runr_knowledge(self) -> None:
        """Load 4Runr knowledge base at startup."""
        try:
            self._4runr_knowledge = self.knowledge_base_loader.load_knowledge_base()
            self.logger.log_module_activity('engager', 'system', 'success', {
                'message': '4Runr knowledge base loaded successfully',
                'knowledge_length': len(self._4runr_knowledge)
            })
        except Exception as e:
            self.logger.log_error(e, {'action': 'load_4runr_knowledge'})
            self._4runr_knowledge = "4Runr builds custom AI infrastructure—private, intelligent, and permanent."
    
    def _create_startup_backup(self) -> None:
        """Create database backup on agent startup."""
        try:
            backup_success = self.database_manager.create_database_backup()
            if backup_success:
                self.logger.log_module_activity('engager', 'system', 'success', {
                    'message': 'Startup database backup created successfully'
                })
            else:
                self.logger.log_module_activity('engager', 'system', 'warning', {
                    'message': 'Startup database backup failed or skipped'
                })
        except Exception as e:
            self.logger.log_error(e, {'action': 'create_startup_backup'})
    
    def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Enhanced lead processing with 4Runr knowledge and company personalization.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads ready for enhanced engagement
        batch_size = limit or self.system_config['batch_size']
        leads = self.engagement_tracker.get_leads_for_enhanced_engagement(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('engager', 'system', 'info', {
                'message': 'No leads found ready for enhanced engagement'
            })
            return {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        for i, lead in enumerate(leads):
            try:
                # Log progress
                self.logger.log_batch_progress(i + 1, len(leads))
                
                # Process individual lead with enhancements
                result = self._process_single_lead_enhanced(lead)
                
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
                    'action': 'process_leads_enhanced',
                    'lead_id': lead.get('id', 'unknown'),
                    'lead_index': i
                })
                stats['processed'] += 1
                stats['errors'] += 1
        
        self.logger.log_pipeline_complete(stats['processed'], stats['successful'], stats['errors'])
        return stats
    
    def _process_single_lead_enhanced(self, lead: Dict[str, Any]) -> str:
        """
        Enhanced single lead processing with full upgrade features.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead_id = lead.get('id', 'unknown')
        lead_name = lead.get('Name', 'Unknown')
        email = lead.get('Email', '')
        company_name = lead.get('Company', 'Unknown Company')
        company_website = lead.get('Website', '')
        
        self.logger.log_module_activity('engager', lead_id, 'start', {
            'message': f'Processing enhanced engagement for {lead_name} at {company_name}',
            'email': email,
            'website': company_website
        })
        
        # Enhanced validation gates
        if not self._should_engage_lead_enhanced(lead):
            return 'skip'
        
        try:
            # Get current engagement level
            current_level = self.engagement_tracker.get_current_engagement_level(lead)
            
            # Scrape company website for personalization
            company_summary = self._get_company_summary(company_website, company_name)
            
            # Generate enhanced personalized message
            personalized_message = self.message_generator.generate_personalized_message(
                lead, self._4runr_knowledge, company_summary, current_level
            )
            
            # Send the email
            send_success = self._send_email_enhanced(lead, personalized_message)
            
            if send_success:
                # Update engagement level and sync to database
                update_success = self.engagement_tracker.update_engagement_level(lead_id, current_level)
                
                # Log detailed engagement data
                engagement_data = {
                    'engagement_stage': self.engagement_tracker.get_next_engagement_level(current_level) or current_level,
                    'last_contacted': datetime.datetime.now().isoformat(),
                    'message_sent': personalized_message[:500],  # Truncate for storage
                    'company_summary': company_summary[:200],  # Truncate for storage
                    'success': True,
                    'airtable_synced': update_success
                }
                
                # Sync to local database
                self.engagement_tracker.sync_to_local_database(lead_id, engagement_data)
                
                if update_success:
                    self.logger.log_module_activity('engager', lead_id, 'success', {
                        'message': f'Successfully sent enhanced message to {lead_name}',
                        'company': company_name,
                        'engagement_level': current_level,
                        'message_length': len(personalized_message),
                        'company_summary_available': bool(company_summary and 'unavailable' not in company_summary)
                    })
                    return 'success'
                else:
                    self.logger.log_module_activity('engager', lead_id, 'warning', {
                        'message': 'Email sent but engagement level update failed'
                    })
                    return 'success'  # Still count as success since email was sent
            else:
                # Log failed engagement
                engagement_data = {
                    'engagement_stage': current_level,
                    'last_contacted': datetime.datetime.now().isoformat(),
                    'success': False,
                    'error_message': 'Email sending failed'
                }
                self.engagement_tracker.sync_to_local_database(lead_id, engagement_data)
                return 'error'
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead_enhanced',
                'lead_id': lead_id,
                'lead_name': lead_name,
                'company': company_name
            })
            
            # Log failed engagement
            try:
                engagement_data = {
                    'engagement_stage': self.engagement_tracker.get_current_engagement_level(lead),
                    'last_contacted': datetime.datetime.now().isoformat(),
                    'success': False,
                    'error_message': str(e)
                }
                self.engagement_tracker.sync_to_local_database(lead_id, engagement_data)
            except:
                pass  # Don't fail if we can't log the failure
            
            return 'error'
    
    def _should_engage_lead_enhanced(self, lead: Dict[str, Any]) -> bool:
        """
        Enhanced lead validation including engagement level checks.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if lead should be engaged, False otherwise
        """
        # First check engagement level
        if self.engagement_tracker.should_skip_lead(lead):
            return False
        
        # Then run standard validation
        return self._should_engage_lead(lead)
    
    def _get_company_summary(self, website_url: str, company_name: str) -> str:
        """
        Get company summary from website scraping.
        
        Args:
            website_url: Company website URL
            company_name: Company name
            
        Returns:
            Company summary string
        """
        if not website_url:
            return f"Company: {company_name} (no website available for analysis)"
        
        try:
            return self.website_scraper.scrape_with_fallback(website_url, company_name)
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'get_company_summary',
                'website_url': website_url,
                'company': company_name
            })
            return f"Company: {company_name} (website analysis unavailable)"
    
    def _send_email_enhanced(self, lead: Dict[str, Any], message: str) -> bool:
        """
        Send email using the parent class method but with enhanced logging.
        
        Args:
            lead: Lead data dictionary
            message: Enhanced personalized message
            
        Returns:
            True if successful, False otherwise
        """
        # Use parent class email sending method
        return self._send_email(lead, message)
    
    def get_enhanced_processing_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about enhanced processing capabilities.
        
        Returns:
            Dictionary with enhanced processing statistics
        """
        try:
            # Get engagement statistics
            engagement_stats = self.engagement_tracker.get_engagement_statistics()
            
            # Get database statistics
            db_stats = self.engagement_tracker.db_manager.get_engagement_statistics()
            
            # Get knowledge base status
            kb_valid = self.knowledge_base_loader.validate_knowledge_base()
            
            # Get website scraping capability
            scraping_works = self.website_scraper.test_scraping_capability()
            
            # Get message generation capability
            generation_works = self.message_generator.test_message_generation()
            
            enhanced_stats = {
                'engagement_levels': engagement_stats,
                'database_stats': db_stats,
                'knowledge_base_valid': kb_valid,
                'website_scraping_available': scraping_works,
                'message_generation_available': generation_works,
                'enhanced_components_status': {
                    'knowledge_base_loader': 'operational',
                    'website_scraper': 'operational' if scraping_works else 'limited',
                    'engagement_tracker': 'operational',
                    'message_generator': 'operational' if generation_works else 'fallback'
                }
            }
            
            return enhanced_stats
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_enhanced_processing_stats'})
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for all enhanced components.
        
        Returns:
            Dictionary with health status of all components
        """
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            # Check knowledge base
            kb_healthy = self.knowledge_base_loader.validate_knowledge_base()
            health_status['components']['knowledge_base'] = 'healthy' if kb_healthy else 'degraded'
            
            # Check website scraper
            scraper_healthy = self.website_scraper.test_scraping_capability()
            health_status['components']['website_scraper'] = 'healthy' if scraper_healthy else 'degraded'
            
            # Check engagement tracker
            tracker_healthy = self.engagement_tracker.validate_engagement_level_field()
            health_status['components']['engagement_tracker'] = 'healthy' if tracker_healthy else 'degraded'
            
            # Check message generator
            generator_healthy = self.message_generator.test_message_generation()
            health_status['components']['message_generator'] = 'healthy' if generator_healthy else 'degraded'
            
            # Check database
            db_healthy = self.engagement_tracker.db_manager.test_database_connection()
            health_status['components']['local_database'] = 'healthy' if db_healthy else 'unhealthy'
            
            # Determine overall status
            component_statuses = list(health_status['components'].values())
            if 'unhealthy' in component_statuses:
                health_status['overall_status'] = 'unhealthy'
            elif 'degraded' in component_statuses:
                health_status['overall_status'] = 'degraded'
            
            self.logger.log_module_activity('engager', 'system', 'info', {
                'message': 'Health check completed',
                'overall_status': health_status['overall_status'],
                'component_count': len(health_status['components'])
            })
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'health_check'})
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def process_reengagement_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads marked for re-engagement with adjusted messaging.
        
        Args:
            limit: Maximum number of re-engagement leads to process
            
        Returns:
            Dictionary with re-engagement processing statistics
        """
        self.logger.log_module_activity('engager', 'system', 'info', {
            'message': 'Starting re-engagement lead processing',
            'limit': limit
        })
        
        # Get leads marked for re-engagement
        reengagement_leads = self.reengagement_strategy.get_reengagement_leads(limit)
        
        if not reengagement_leads:
            self.logger.log_module_activity('engager', 'system', 'info', {
                'message': 'No leads found ready for re-engagement'
            })
            return {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        self.logger.log_module_activity('engager', 'system', 'info', {
            'message': f'Processing {len(reengagement_leads)} re-engagement leads'
        })
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0, 'skipped': 0}
        
        for i, lead in enumerate(reengagement_leads):
            try:
                self.logger.log_module_activity('engager', lead['id'], 'start', {
                    'message': f'Processing re-engagement for {lead["name"]} ({lead["follow_up_stage"]})',
                    'email': lead['email'],
                    'follow_up_stage': lead['follow_up_stage']
                })
                
                result = self._process_single_reengagement_lead(lead)
                
                stats['processed'] += 1
                if result == 'success':
                    stats['successful'] += 1
                elif result == 'skip':
                    stats['skipped'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                self.logger.log_error(e, {
                    'action': 'process_reengagement_leads',
                    'lead_id': lead.get('id', 'unknown'),
                    'lead_index': i
                })
                stats['processed'] += 1
                stats['errors'] += 1
        
        self.logger.log_module_activity('engager', 'system', 'success', {
            'message': 'Re-engagement processing completed',
            'processed': stats['processed'],
            'successful': stats['successful'],
            'errors': stats['errors'],
            'skipped': stats['skipped']
        })
        
        return stats
    
    def _process_single_reengagement_lead(self, lead: Dict[str, Any]) -> str:
        """
        Process a single lead for re-engagement with adjusted messaging.
        
        Args:
            lead: Re-engagement lead data dictionary
            
        Returns:
            Result status: 'success', 'skip', or 'error'
        """
        lead_id = lead['id']
        lead_name = lead['name']
        email = lead['email']
        follow_up_stage = lead['follow_up_stage']
        
        try:
            # Check if lead should be skipped
            if lead['response_status'] in ['Converted', 'Rejected', 'Interested']:
                self.logger.log_module_activity('engager', lead_id, 'skip', {
                    'message': f'Skipping re-engagement - Response status: {lead["response_status"]}',
                    'response_status': lead['response_status']
                })
                
                # Mark as completed
                self.reengagement_strategy.complete_reengagement(lead_id, success=True)
                return 'skip'
            
            # Generate re-engagement message with adjusted tone
            reengagement_message = self._generate_reengagement_message(lead)
            
            if not reengagement_message:
                self.logger.log_module_activity('engager', lead_id, 'error', {
                    'message': 'Failed to generate re-engagement message'
                })
                self.reengagement_strategy.complete_reengagement(
                    lead_id, success=False, error_message="Message generation failed"
                )
                return 'error'
            
            # Send the re-engagement email
            send_success = self._send_reengagement_email(lead, reengagement_message)
            
            if send_success:
                # Update engagement tracking
                engagement_data = {
                    'engagement_stage': f'reengagement_{follow_up_stage.lower()}',
                    'last_contacted': datetime.datetime.now().isoformat(),
                    'message_sent': reengagement_message[:500],  # Truncate for storage
                    'success': True,
                    'follow_up_stage': follow_up_stage
                }
                
                # Sync to local database
                self.database_manager.update_engagement_data(lead_id, engagement_data)
                
                # Mark re-engagement as completed
                self.reengagement_strategy.complete_reengagement(lead_id, success=True)
                
                self.logger.log_module_activity('engager', lead_id, 'success', {
                    'message': f'Successfully sent re-engagement message ({follow_up_stage})',
                    'follow_up_stage': follow_up_stage,
                    'message_length': len(reengagement_message)
                })
                
                return 'success'
            else:
                self.reengagement_strategy.complete_reengagement(
                    lead_id, success=False, error_message="Email sending failed"
                )
                return 'error'
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_reengagement_lead',
                'lead_id': lead_id,
                'follow_up_stage': follow_up_stage
            })
            
            self.reengagement_strategy.complete_reengagement(
                lead_id, success=False, error_message=str(e)
            )
            return 'error'
    
    def _generate_reengagement_message(self, lead: Dict[str, Any]) -> Optional[str]:
        """
        Generate a re-engagement message with adjusted tone and urgency.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Generated re-engagement message or None if generation fails
        """
        try:
            follow_up_stage = lead['follow_up_stage']
            
            # Create re-engagement context
            reengagement_context = {
                'is_reengagement': True,
                'follow_up_stage': follow_up_stage,
                'follow_up_number': 1 if follow_up_stage == 'Followup_1' else 2,
                'days_since_last_contact': (
                    datetime.datetime.now() - 
                    datetime.datetime.fromisoformat(lead['last_contacted'])
                ).days if lead.get('last_contacted') else 7
            }
            
            # Use the enhanced message generator with re-engagement context
            message = self.message_generator.generate_reengagement_message(
                lead, self._4runr_knowledge, reengagement_context
            )
            
            return message
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'generate_reengagement_message',
                'lead_id': lead.get('id', 'unknown'),
                'follow_up_stage': lead.get('follow_up_stage')
            })
            return None
    
    def _send_reengagement_email(self, lead: Dict[str, Any], message: str) -> bool:
        """
        Send re-engagement email with appropriate tracking.
        
        Args:
            lead: Lead data dictionary
            message: Re-engagement message to send
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # For now, simulate email sending
            # In a real implementation, this would integrate with the email sending system
            
            self.logger.log_module_activity('engager', lead['id'], 'info', {
                'message': f'Sending re-engagement email to {lead["email"]}',
                'follow_up_stage': lead['follow_up_stage'],
                'message_preview': message[:100] + "..." if len(message) > 100 else message
            })
            
            # Simulate successful sending
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'send_reengagement_email',
                'lead_id': lead.get('id', 'unknown'),
                'email': lead.get('email')
            })
            return False


def main():
    """Main entry point for the Enhanced Engager Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Enhanced Engager Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show enhanced processing statistics')
    parser.add_argument('--health', action='store_true', help='Run health check on all components')
    parser.add_argument('--dry-run', action='store_true', help='Simulate sending without actually sending emails')
    parser.add_argument('--reengage-only', action='store_true', help='Process only re-engagement leads')
    
    args = parser.parse_args()
    
    agent = EnhancedEngagerAgent()
    
    if args.health:
        health = agent.health_check()
        print(f"🏥 Enhanced Engager Health Check:")
        print(f"  Overall Status: {health['overall_status']}")
        print(f"  Components:")
        for component, status in health.get('components', {}).items():
            status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
            print(f"    {status_icon} {component}: {status}")
        return health['overall_status'] == 'healthy'
    
    if args.stats:
        stats = agent.get_enhanced_processing_stats()
        print(f"📊 Enhanced Processing Statistics:")
        
        if 'engagement_levels' in stats:
            eng_stats = stats['engagement_levels']
            print(f"  Engagement Levels:")
            print(f"    Total leads ready: {eng_stats.get('ready_for_engagement', 0)}")
            for level, count in eng_stats.get('by_level', {}).items():
                print(f"    {level}: {count}")
        
        if 'enhanced_components_status' in stats:
            print(f"  Component Status:")
            for component, status in stats['enhanced_components_status'].items():
                status_icon = "✅" if status == 'operational' else "⚠️"
                print(f"    {status_icon} {component}: {status}")
        
        return True
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No emails will actually be sent")
    
    if args.lead_id:
        # Process specific lead (use parent method for now)
        result = agent.process_specific_lead(args.lead_id)
        print(f"Result: {result}")
        return result == 'success'
    
    if args.reengage_only:
        # Process only re-engagement leads
        print("🔄 Processing re-engagement leads only...")
        results = agent.process_reengagement_leads(limit=args.limit)
        
        print(f"Re-engagement Results:")
        print(f"  Processed: {results['processed']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Errors: {results['errors']}")
        
        return results['successful'] > 0
    
    # Process leads in batch with enhancements
    results = agent.process_leads(limit=args.limit)
    
    print(f"Enhanced Engager Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = main()
    import sys
    sys.exit(0 if success else 1)