#!/usr/bin/env python3
"""
Campaign Brain Production Service

Production-ready service that integrates the LangGraph Campaign Brain
with the existing 4Runr lead pipeline and message queue system.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "4runr-outreach-system"))

# Import Campaign Brain
from campaign_brain import CampaignBrainGraph, CampaignBrainConfig, CampaignStatus

# Import existing 4Runr system components
try:
    from shared.airtable_client import get_airtable_client
    from shared.config import config as outreach_config
    from shared.logging_utils import get_logger
    from campaign_system.campaign_injector import CampaignInjector
except ImportError as e:
    print(f"Warning: Could not import 4Runr system components: {e}")
    print("Running in standalone mode...")


class CampaignBrainService:
    """Production service for the Campaign Brain"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the service"""
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self.brain = CampaignBrainGraph(self.config)
        
        # Initialize integrations
        try:
            self.airtable_client = get_airtable_client()
            self.campaign_injector = CampaignInjector()
            self.integrated_mode = True
            self.logger.info("Initialized in integrated mode with 4Runr systems")
        except:
            self.airtable_client = None
            self.campaign_injector = None
            self.integrated_mode = False
            self.logger.warning("Running in standalone mode - no 4Runr system integration")
        
        # Performance tracking
        self.stats = {
            'processed': 0,
            'approved': 0,
            'manual_review': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def _load_config(self, config_file: Optional[str]) -> CampaignBrainConfig:
        """Load configuration from file or environment"""
        
        # Load from config file if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Set environment variables from config file
            for key, value in config_data.items():
                os.environ[key] = str(value)
        
        # Load Campaign Brain config
        brain_config = CampaignBrainConfig()
        
        # Validate configuration
        validation_issues = brain_config.validate()
        if validation_issues:
            print("❌ Configuration Issues:")
            for issue in validation_issues:
                print(f"  • {issue}")
            sys.exit(1)
        
        return brain_config
    
    def _setup_logging(self) -> logging.Logger:
        """Set up production logging"""
        logger = logging.getLogger('campaign_brain_service')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "campaign_brain_service.log")
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    async def process_lead_by_id(self, lead_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Process a specific lead by ID"""
        
        self.logger.info(f"Processing lead ID: {lead_id}")
        
        try:
            # Get lead data
            if self.integrated_mode:
                lead_data = self.airtable_client.get_lead_by_id(lead_id)
                if not lead_data:
                    raise ValueError(f"Lead {lead_id} not found in Airtable")
            else:
                # Standalone mode - load from file
                lead_file = Path(f"leads/{lead_id}.json")
                if not lead_file.exists():
                    raise ValueError(f"Lead file not found: {lead_file}")
                
                with open(lead_file, 'r') as f:
                    lead_data = json.load(f)
            
            # Process through Campaign Brain
            result = await self._process_single_lead(lead_data, dry_run)
            
            # Update statistics
            self.stats['processed'] += 1
            if result['final_status'] == 'approved':
                self.stats['approved'] += 1
            elif result['final_status'] == 'manual_review':
                self.stats['manual_review'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing lead {lead_id}: {str(e)}")
            self.stats['errors'] += 1
            return {
                'lead_id': lead_id,
                'final_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_batch(self, batch_size: int = 10, dry_run: bool = False) -> Dict[str, Any]:
        """Process a batch of leads ready for campaign brain"""
        
        self.logger.info(f"Processing batch of {batch_size} leads")
        
        try:
            # Get leads ready for campaign brain
            if self.integrated_mode:
                leads = self._get_leads_for_brain_processing(batch_size)
            else:
                # Standalone mode - get from leads directory
                leads = self._get_leads_from_directory(batch_size)
            
            if not leads:
                self.logger.info("No leads found ready for processing")
                return {
                    'processed': 0,
                    'results': [],
                    'message': 'No leads ready for processing'
                }
            
            self.logger.info(f"Found {len(leads)} leads ready for processing")
            
            # Process leads concurrently (with limit)
            semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
            
            async def process_with_semaphore(lead):
                async with semaphore:
                    return await self._process_single_lead(lead, dry_run)
            
            # Process all leads
            results = await asyncio.gather(*[
                process_with_semaphore(lead) for lead in leads
            ], return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Lead {i} failed: {str(result)}")
                    self.stats['errors'] += 1
                    processed_results.append({
                        'lead_id': leads[i].get('id', f'lead_{i}'),
                        'final_status': 'error',
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
                    self.stats['processed'] += 1
                    
                    if result['final_status'] == 'approved':
                        self.stats['approved'] += 1
                    elif result['final_status'] == 'manual_review':
                        self.stats['manual_review'] += 1
            
            return {
                'processed': len(processed_results),
                'results': processed_results,
                'stats': self.get_stats(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")
            return {
                'processed': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _process_single_lead(self, lead_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Process a single lead through the Campaign Brain"""
        
        lead_id = lead_data.get('id', 'unknown')
        lead_name = lead_data.get('Name', 'Unknown')
        
        try:
            # Prepare lead data for Campaign Brain
            brain_input = self._prepare_brain_input(lead_data)
            
            # Execute Campaign Brain
            start_time = time.time()
            brain_result = await self.brain.execute(brain_input)
            execution_time = time.time() - start_time
            
            # Prepare result
            result = {
                'lead_id': lead_id,
                'lead_name': lead_name,
                'final_status': brain_result.final_status.value,
                'execution_time': execution_time,
                'traits': brain_result.traits,
                'messaging_angle': brain_result.messaging_angle,
                'campaign_tone': brain_result.campaign_tone,
                'overall_quality_score': brain_result.overall_quality_score,
                'messages_generated': len(brain_result.messages),
                'retry_count': brain_result.retry_count,
                'timestamp': datetime.now().isoformat()
            }
            
            # Handle approved campaigns
            if brain_result.final_status == CampaignStatus.APPROVED and not dry_run:
                injection_result = await self._inject_campaign(brain_result, lead_data)
                result['injection_result'] = injection_result
                
                # Update Airtable if integrated
                if self.integrated_mode:
                    await self._update_airtable_status(lead_data, brain_result, injection_result)
            
            # Save trace log
            if self.config.trace_logs_enabled:
                await self._save_trace_log(brain_result)
            
            self.logger.info(f"Processed {lead_name}: {brain_result.final_status.value} "
                           f"(score: {brain_result.overall_quality_score:.1f}, time: {execution_time:.2f}s)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing lead {lead_name}: {str(e)}")
            return {
                'lead_id': lead_id,
                'lead_name': lead_name,
                'final_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_brain_input(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare lead data for Campaign Brain input"""
        
        # Extract company data
        company_data = {
            'description': lead_data.get('Company_Description', ''),
            'services': lead_data.get('Top_Services', ''),
            'tone': lead_data.get('Tone', 'Professional')
        }
        
        # Extract scraped content
        scraped_content = {
            'homepage_text': lead_data.get('Homepage_Content', ''),
            'about_page': lead_data.get('About_Page_Content', ''),
            'website_url': lead_data.get('company_website_url', '')
        }
        
        return {
            'id': lead_data.get('id'),
            'Name': lead_data.get('Name'),
            'Title': lead_data.get('Title'),
            'Company': lead_data.get('Company'),
            'Email': lead_data.get('Email'),
            'company_data': company_data,
            'scraped_content': scraped_content
        }
    
    def _get_leads_for_brain_processing(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads ready for Campaign Brain processing from Airtable"""
        
        try:
            # Custom query for leads ready for brain processing
            # These should be leads that have been enriched but not yet processed by brain
            formula = "AND({Company_Description} != '', {Custom_Message} = '', {Brain_Status} != 'Processed')"
            
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit,
                sort=['-Created At']
            )
            
            leads = []
            for record in records:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            return leads
            
        except Exception as e:
            self.logger.error(f"Error getting leads from Airtable: {str(e)}")
            return []
    
    def _get_leads_from_directory(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads from local directory (standalone mode)"""
        
        leads_dir = Path("leads")
        if not leads_dir.exists():
            return []
        
        leads = []
        for lead_file in leads_dir.glob("*.json")[:limit]:
            try:
                with open(lead_file, 'r') as f:
                    lead_data = json.load(f)
                    leads.append(lead_data)
            except Exception as e:
                self.logger.warning(f"Error loading lead file {lead_file}: {str(e)}")
        
        return leads
    
    async def _inject_campaign(self, brain_result, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inject approved campaign into message queue"""
        
        try:
            if self.integrated_mode and self.campaign_injector:
                # Use existing campaign injector
                campaign_data = {
                    'ready_to_send': True,
                    'overall_quality_score': brain_result.overall_quality_score,
                    'messages': [
                        {
                            'type': msg.message_type,
                            'subject': msg.subject,
                            'body': msg.body,
                            'quality_score': msg.quality_score,
                            'issues_detected': msg.quality_issues
                        }
                        for msg in brain_result.messages
                    ],
                    'company_insights': {
                        'traits': brain_result.traits,
                        'messaging_angle': brain_result.messaging_angle,
                        'campaign_tone': brain_result.campaign_tone
                    }
                }
                
                success = self.campaign_injector.inject_campaign(campaign_data, lead_data)
                
                return {
                    'success': success,
                    'method': 'integrated_injector',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Standalone mode - save to queue directory
                queue_dir = Path("queue")
                queue_dir.mkdir(exist_ok=True)
                
                queue_file = queue_dir / f"campaign_{brain_result.execution_id}.json"
                
                queue_data = {
                    'campaign_id': brain_result.execution_id,
                    'lead_data': lead_data,
                    'brain_result': brain_result.to_dict(),
                    'created_at': datetime.now().isoformat()
                }
                
                with open(queue_file, 'w') as f:
                    json.dump(queue_data, f, indent=2, default=str)
                
                return {
                    'success': True,
                    'method': 'file_queue',
                    'queue_file': str(queue_file),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error injecting campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _update_airtable_status(self, lead_data: Dict[str, Any], brain_result, injection_result: Dict[str, Any]):
        """Update Airtable with Campaign Brain results"""
        
        try:
            if not self.integrated_mode:
                return
            
            update_fields = {
                'Brain_Status': 'Processed',
                'Brain_Execution_Date': datetime.now().date().isoformat(),
                'Brain_Quality_Score': brain_result.overall_quality_score,
                'Brain_Final_Status': brain_result.final_status.value,
                'Detected_Traits': ', '.join(brain_result.traits[:5]),  # Top 5 traits
                'Messaging_Angle': brain_result.messaging_angle,
                'Campaign_Tone': brain_result.campaign_tone
            }
            
            if injection_result.get('success'):
                update_fields['Campaign_Injected'] = True
                update_fields['Campaign_Injection_Date'] = datetime.now().date().isoformat()
            
            # Add first message as Custom_Message for compatibility
            if brain_result.messages:
                first_message = brain_result.messages[0]
                update_fields['Custom_Message'] = first_message.body
                update_fields['Message_Subject'] = first_message.subject
            
            success = self.airtable_client.update_lead_fields(lead_data['id'], update_fields)
            
            if success:
                self.logger.debug(f"Updated Airtable for lead {lead_data.get('Name')}")
            else:
                self.logger.warning(f"Failed to update Airtable for lead {lead_data.get('Name')}")
                
        except Exception as e:
            self.logger.error(f"Error updating Airtable: {str(e)}")
    
    async def _save_trace_log(self, brain_result):
        """Save detailed trace log"""
        
        try:
            trace_dir = Path("trace_logs")
            trace_dir.mkdir(exist_ok=True)
            
            trace_file = trace_dir / f"{brain_result.execution_id}.json"
            
            with open(trace_file, 'w') as f:
                json.dump(brain_result.to_dict(), f, indent=2, default=str)
            
            self.logger.debug(f"Saved trace log: {trace_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save trace log: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'runtime_seconds': runtime.total_seconds(),
            'processed': self.stats['processed'],
            'approved': self.stats['approved'],
            'manual_review': self.stats['manual_review'],
            'errors': self.stats['errors'],
            'approval_rate': (self.stats['approved'] / max(1, self.stats['processed'])) * 100,
            'integrated_mode': self.integrated_mode,
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'config_valid': True,
            'integrations': {
                'airtable': self.airtable_client is not None,
                'campaign_injector': self.campaign_injector is not None,
                'openai': bool(self.config.openai_api_key)
            },
            'stats': self.get_stats()
        }
        
        # Check for issues
        issues = []
        
        if not self.config.openai_api_key:
            issues.append("OpenAI API key not configured")
        
        if not self.integrated_mode:
            issues.append("Running in standalone mode - no 4Runr integration")
        
        if issues:
            health['status'] = 'degraded'
            health['issues'] = issues
        
        return health


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Campaign Brain Production Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process specific lead
  python serve_campaign_brain.py --lead-id rec123456789

  # Process batch of leads
  python serve_campaign_brain.py --batch-size 10

  # Dry run (no injection)
  python serve_campaign_brain.py --batch-size 5 --dry-run

  # Health check
  python serve_campaign_brain.py --health-check

  # Use custom config
  python serve_campaign_brain.py --config config.json --batch-size 10
        """
    )
    
    parser.add_argument('--lead-id', help='Process specific lead by ID')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of leads to process in batch')
    parser.add_argument('--dry-run', action='store_true', help='Simulate processing without injection')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--health-check', action='store_true', help='Perform health check and exit')
    parser.add_argument('--stats', action='store_true', help='Show service statistics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Initialize service
        service = CampaignBrainService(args.config)
        
        # Health check
        if args.health_check:
            health = service.health_check()
            print(json.dumps(health, indent=2))
            return health['status'] == 'healthy'
        
        # Statistics
        if args.stats:
            stats = service.get_stats()
            print(json.dumps(stats, indent=2))
            return True
        
        # Process specific lead
        if args.lead_id:
            print(f"Processing lead: {args.lead_id}")
            result = await service.process_lead_by_id(args.lead_id, args.dry_run)
            
            if args.verbose:
                print(json.dumps(result, indent=2))
            else:
                print(f"Result: {result['final_status']} "
                      f"(score: {result.get('overall_quality_score', 0):.1f})")
            
            return result['final_status'] in ['approved', 'manual_review']
        
        # Process batch
        print(f"Processing batch of {args.batch_size} leads...")
        if args.dry_run:
            print("🧪 DRY RUN MODE - No campaigns will be injected")
        
        result = await service.process_batch(args.batch_size, args.dry_run)
        
        if args.verbose:
            print(json.dumps(result, indent=2))
        else:
            print(f"Processed: {result['processed']} leads")
            if 'stats' in result:
                stats = result['stats']
                print(f"Approved: {stats['approved']}")
                print(f"Manual Review: {stats['manual_review']}")
                print(f"Errors: {stats['errors']}")
                print(f"Approval Rate: {stats['approval_rate']:.1f}%")
        
        return result['processed'] > 0
        
    except KeyboardInterrupt:
        print("\n\nService interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Service error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)