#!/usr/bin/env python3
"""
Daily Automation Script

Automated daily lead scraping, enrichment, and synchronization for the 4runr-lead-scraper system.
Designed to run as a scheduled task (cron job) for continuous lead generation.
"""

import os
import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import get_lead_database
from scraper.lead_finder import LeadFinder
from enricher.email_enricher import EmailEnricher
from enricher.profile_enricher import ProfileEnricher
from sync.sync_manager import get_sync_manager
from config.settings import get_settings
from utils.logging import get_logger, StructuredLogger, PerformanceLogger, LoggedOperation
from utils.validators import LeadDataValidator, clean_lead_data

class DailyScraperAgent:
    """
    Daily automation agent for lead scraping, enrichment, and sync operations.
    """
    
    def __init__(self, max_leads: int = None, dry_run: bool = False):
        """
        Initialize the daily scraper agent.
        
        Args:
            max_leads: Maximum leads to process (overrides config)
            dry_run: Run in dry-run mode (no database changes)
        """
        self.settings = get_settings()
        self.db = get_lead_database()
        self.sync_manager = get_sync_manager()
        
        # Configuration
        self.max_leads = max_leads or self.settings.scraper.max_leads_per_run
        self.dry_run = dry_run
        
        # Logging
        self.logger = get_logger('daily-scraper')
        self.struct_logger = StructuredLogger('daily-scraper')
        self.perf_logger = PerformanceLogger('daily-scraper')
        
        # Statistics tracking
        self.stats = {
            'leads_scraped': 0,
            'leads_enriched': 0,
            'leads_synced': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'operations': []
        }
        
        self.logger.info("[BOT] Daily Scraper Agent initialized")
        self.logger.info(f"⚙️ Max leads: {self.max_leads}")
        self.logger.info(f"⚙️ Dry run: {self.dry_run}")
    
    def run_daily_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete daily pipeline: scrape → enrich → sync.
        
        Returns:
            Dictionary with pipeline results
        """
        self.logger.info("[LAUNCH] Starting daily lead pipeline")
        
        with LoggedOperation(self.struct_logger, 'daily_pipeline', max_leads=self.max_leads):
            try:
                # Step 1: Scrape new leads
                scraping_result = self._run_scraping_phase()
                
                # Step 2: Enrich existing leads
                enrichment_result = self._run_enrichment_phase()
                
                # Step 3: Sync to Airtable
                sync_result = self._run_sync_phase()
                
                # Generate summary
                summary = self._generate_summary(scraping_result, enrichment_result, sync_result)
                
                self.logger.info("[OK] Daily pipeline completed successfully")
                return summary
                
            except Exception as e:
                self.logger.error(f"[ERROR] Daily pipeline failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_scraping_phase(self) -> Dict[str, Any]:
        """
        Run the lead scraping phase.
        
        Returns:
            Scraping results
        """
        self.logger.info("[SEARCH] Starting scraping phase")
        
        with LoggedOperation(self.struct_logger, 'scraping_phase'):
            try:
                # Initialize lead finder
                lead_finder = LeadFinder()
                
                # Scrape new leads
                self.perf_logger.start_timer('scraping')
                leads = lead_finder.find_montreal_executives(max_leads=self.max_leads)
                scraping_duration = self.perf_logger.end_timer('scraping', {'leads_found': len(leads)})
                
                if not leads:
                    self.logger.info("📭 No new leads found")
                    return {'leads_found': 0, 'leads_saved': 0, 'duration': scraping_duration}
                
                self.logger.info(f"📋 Found {len(leads)} potential leads")
                
                # Validate and clean leads
                valid_leads = []
                for lead in leads:
                    try:
                        # Clean the lead data
                        cleaned_lead = clean_lead_data(lead)
                        
                        # Validate the lead
                        validation_result = LeadDataValidator.validate_lead_data(cleaned_lead)
                        
                        if validation_result.is_valid:
                            valid_leads.append(cleaned_lead)
                        else:
                            self.logger.warning(f"[WARNING] Invalid lead data for {lead.get('name', 'Unknown')}: {validation_result.errors}")
                    
                    except Exception as e:
                        self.logger.warning(f"[WARNING] Failed to process lead: {str(e)}")
                        continue
                
                self.logger.info(f"[OK] Validated {len(valid_leads)}/{len(leads)} leads")
                
                # Save leads to database
                saved_count = 0
                if not self.dry_run:
                    for lead in valid_leads:
                        try:
                            lead_id = self.db.create_lead(lead)
                            saved_count += 1
                            self.logger.debug(f"[SAVE] Saved lead: {lead['name']} ({lead_id})")
                        
                        except Exception as e:
                            self.logger.warning(f"[WARNING] Failed to save lead {lead.get('name', 'Unknown')}: {str(e)}")
                            self.stats['errors'] += 1
                else:
                    saved_count = len(valid_leads)  # Simulate for dry run
                
                self.stats['leads_scraped'] = saved_count
                self.stats['operations'].append('scraping')
                
                result = {
                    'leads_found': len(leads),
                    'leads_validated': len(valid_leads),
                    'leads_saved': saved_count,
                    'duration': scraping_duration
                }
                
                self.struct_logger.log_scraping('success', leads_count=saved_count, source='serpapi')
                self.logger.info(f"[OK] Scraping phase completed: {saved_count} leads saved")
                
                return result
                
            except Exception as e:
                self.struct_logger.log_scraping('failed', error=str(e))
                self.logger.error(f"[ERROR] Scraping phase failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_enrichment_phase(self) -> Dict[str, Any]:
        """
        Run the lead enrichment phase.
        
        Returns:
            Enrichment results
        """
        self.logger.info("💎 Starting enrichment phase")
        
        with LoggedOperation(self.struct_logger, 'enrichment_phase'):
            try:
                # Get leads that need enrichment
                leads_to_enrich = self.db.get_leads_needing_enrichment(limit=self.max_leads)
                
                if not leads_to_enrich:
                    self.logger.info("📭 No leads need enrichment")
                    return {'leads_processed': 0, 'leads_enriched': 0, 'duration': 0}
                
                self.logger.info(f"📋 Found {len(leads_to_enrich)} leads needing enrichment")
                
                # Initialize enrichers
                email_enricher = EmailEnricher()
                profile_enricher = ProfileEnricher()
                
                enriched_count = 0
                self.perf_logger.start_timer('enrichment')
                
                for i, lead in enumerate(leads_to_enrich, 1):
                    self.logger.info(f"💎 Enriching {i}/{len(leads_to_enrich)}: {lead.name}")
                    
                    try:
                        enrichment_data = {}
                        
                        # Email enrichment
                        if not lead.email:
                            email_result = email_enricher.enrich_lead_email(lead.to_dict())
                            
                            if email_result.get('success'):
                                enrichment_data['email'] = email_result['email']
                                enrichment_data['enrichment_method'] = email_result['method']
                                self.logger.info(f"  📧 Found email: {email_result['email']}")
                        
                        # Profile enrichment
                        profile_result = profile_enricher.enrich_lead_profile(lead.to_dict())
                        
                        if profile_result.get('success'):
                            company_data = profile_result.get('company_data', {})
                            if company_data.get('industry'):
                                enrichment_data['industry'] = company_data['industry']
                            if company_data.get('estimated_size'):
                                enrichment_data['company_size'] = company_data['estimated_size']
                            if company_data.get('website_url'):
                                enrichment_data['company_website'] = company_data['website_url']
                        
                        # Update database
                        if enrichment_data and not self.dry_run:
                            success = self.db.mark_lead_enriched(lead.id, enrichment_data)
                            if success:
                                enriched_count += 1
                                self.struct_logger.log_enrichment('success', lead_name=lead.name, method=enrichment_data.get('enrichment_method', 'profile'))
                            else:
                                self.logger.warning(f"[WARNING] Failed to update database for {lead.name}")
                        elif enrichment_data and self.dry_run:
                            enriched_count += 1  # Simulate for dry run
                        
                        # Anti-detection delay
                        if i < len(leads_to_enrich):
                            delay = random.uniform(5, 10)
                            self.logger.debug(f"⏱️ Anti-detection delay: {delay:.1f}s")
                            time.sleep(delay)
                    
                    except Exception as e:
                        self.logger.error(f"[ERROR] Enrichment failed for {lead.name}: {str(e)}")
                        self.struct_logger.log_enrichment('failed', lead_name=lead.name, error=str(e))
                        self.stats['errors'] += 1
                        continue
                
                enrichment_duration = self.perf_logger.end_timer('enrichment', {'leads_enriched': enriched_count})
                
                self.stats['leads_enriched'] = enriched_count
                self.stats['operations'].append('enrichment')
                
                result = {
                    'leads_processed': len(leads_to_enrich),
                    'leads_enriched': enriched_count,
                    'duration': enrichment_duration
                }
                
                self.logger.info(f"[OK] Enrichment phase completed: {enriched_count}/{len(leads_to_enrich)} leads enriched")
                
                return result
                
            except Exception as e:
                self.logger.error(f"[ERROR] Enrichment phase failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_sync_phase(self) -> Dict[str, Any]:
        """
        Run the Airtable synchronization phase.
        
        Returns:
            Sync results
        """
        self.logger.info("[SYNC] Starting sync phase")
        
        with LoggedOperation(self.struct_logger, 'sync_phase'):
            try:
                if self.dry_run:
                    self.logger.info("🧪 Dry run mode - skipping actual sync")
                    return {
                        'leads_synced': 0, 
                        'sync_success': True, 
                        'duration': 0,
                        'errors': [],
                        'defaults_applied': 0,
                        'defaults_fields': [],
                        'defaults_errors': []
                    }
                
                # Sync to Airtable
                self.perf_logger.start_timer('sync')
                sync_result = self.sync_manager.sync_to_airtable()
                sync_duration = self.perf_logger.end_timer('sync', {'leads_synced': sync_result.get('synced_count', 0)})
                
                synced_count = sync_result.get('synced_count', 0)
                sync_success = sync_result.get('success', False)
                
                if sync_success:
                    self.struct_logger.log_sync('success', direction='to_airtable', count=synced_count)
                    self.logger.info(f"[OK] Sync completed: {synced_count} leads synced to Airtable")
                    
                    # Log engagement defaults results
                    if 'defaults_applied' in sync_result:
                        defaults = sync_result['defaults_applied']
                        defaults_count = defaults.get('count', 0)
                        if defaults_count > 0:
                            fields_updated = defaults.get('fields_updated', [])
                            self.logger.info(f"[TARGET] Engagement defaults applied: {defaults_count} leads updated with fields {fields_updated}")
                            
                            # Add to structured logging
                            self.struct_logger.log_module_activity('daily_scraper', 'engagement_defaults', 'success', {
                                'leads_updated': defaults_count,
                                'fields_updated': fields_updated,
                                'skipped_count': defaults.get('skipped_count', 0),
                                'failed_count': defaults.get('failed_count', 0)
                            })
                        elif defaults.get('errors'):
                            self.logger.warning(f"[WARNING] Engagement defaults had errors: {defaults['errors']}")
                            self.struct_logger.log_module_activity('daily_scraper', 'engagement_defaults', 'warning', {
                                'errors': defaults['errors']
                            })
                        else:
                            self.logger.debug("[TARGET] No engagement defaults needed (all leads already have values)")
                else:
                    self.struct_logger.log_sync('failed', direction='to_airtable', error=sync_result.get('errors', []))
                    self.logger.error(f"[ERROR] Sync failed: {sync_result.get('failed_count', 0)} failures")
                    self.stats['errors'] += 1
                
                self.stats['leads_synced'] = synced_count
                self.stats['operations'].append('sync')
                
                # Extract defaults information
                defaults_applied = sync_result.get('defaults_applied', {})
                defaults_count = defaults_applied.get('count', 0)
                
                return {
                    'leads_synced': synced_count,
                    'sync_success': sync_success,
                    'duration': sync_duration,
                    'errors': sync_result.get('errors', []),
                    'defaults_applied': defaults_count,
                    'defaults_fields': defaults_applied.get('fields_updated', []),
                    'defaults_errors': defaults_applied.get('errors', [])
                }
                
            except Exception as e:
                self.logger.error(f"[ERROR] Sync phase failed: {str(e)}")
                self.struct_logger.log_sync('failed', direction='to_airtable', error=str(e))
                self.stats['errors'] += 1
                raise
    
    def _generate_summary(self, scraping_result: Dict, enrichment_result: Dict, sync_result: Dict) -> Dict[str, Any]:
        """
        Generate pipeline execution summary.
        
        Args:
            scraping_result: Results from scraping phase
            enrichment_result: Results from enrichment phase
            sync_result: Results from sync phase
            
        Returns:
            Summary dictionary
        """
        end_time = datetime.now()
        total_duration = (end_time - self.stats['start_time']).total_seconds()
        
        summary = {
            'execution_id': f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': self.stats['start_time'].isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': total_duration,
            'dry_run': self.dry_run,
            'success': self.stats['errors'] == 0,
            'statistics': {
                'leads_scraped': self.stats['leads_scraped'],
                'leads_enriched': self.stats['leads_enriched'],
                'leads_synced': self.stats['leads_synced'],
                'defaults_applied': sync_result.get('defaults_applied', 0),
                'total_errors': self.stats['errors'],
                'operations_completed': self.stats['operations']
            },
            'phase_results': {
                'scraping': scraping_result,
                'enrichment': enrichment_result,
                'sync': sync_result
            }
        }
        
        # Log performance metrics
        self.perf_logger.log_performance_metrics({
            'total_duration': total_duration,
            'leads_per_minute': (self.stats['leads_scraped'] / (total_duration / 60)) if total_duration > 0 else 0,
            'enrichment_rate': (self.stats['leads_enriched'] / self.stats['leads_scraped']) if self.stats['leads_scraped'] > 0 else 0,
            'sync_rate': (self.stats['leads_synced'] / self.stats['leads_scraped']) if self.stats['leads_scraped'] > 0 else 0,
            'error_rate': (self.stats['errors'] / max(1, sum([self.stats['leads_scraped'], self.stats['leads_enriched'], self.stats['leads_synced']])))
        })
        
        return summary
    
    def save_execution_report(self, summary: Dict[str, Any]) -> str:
        """
        Save execution report to file.
        
        Args:
            summary: Execution summary
            
        Returns:
            Path to saved report
        """
        try:
            # Create reports directory
            reports_dir = Path("logs/daily")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate report filename
            report_filename = f"daily_report_{summary['execution_id']}.json"
            report_path = reports_dir / report_filename
            
            # Save report
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"[FILE] Execution report saved: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to save execution report: {str(e)}")
            return ""


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="4Runr Lead Scraper Daily Automation")
    parser.add_argument('--max-leads', type=int, help='Maximum leads to process')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no database changes)')
    parser.add_argument('--scrape-only', action='store_true', help='Only run scraping phase')
    parser.add_argument('--enrich-only', action='store_true', help='Only run enrichment phase')
    parser.add_argument('--sync-only', action='store_true', help='Only run sync phase')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--save-report', action='store_true', help='Save execution report to file')
    
    args = parser.parse_args()
    
    try:
        # Initialize agent
        agent = DailyScraperAgent(max_leads=args.max_leads, dry_run=args.dry_run)
        
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Run specific phases or full pipeline
        if args.scrape_only:
            result = agent._run_scraping_phase()
            print(f"[SEARCH] Scraping Results: {result}")
        elif args.enrich_only:
            result = agent._run_enrichment_phase()
            print(f"💎 Enrichment Results: {result}")
        elif args.sync_only:
            result = agent._run_sync_phase()
            print(f"[SYNC] Sync Results: {result}")
        else:
            # Run full pipeline
            summary = agent.run_daily_pipeline()
            
            # Display summary
            print(f"\n[TARGET] Daily Pipeline Summary:")
            print(f"  Execution ID: {summary['execution_id']}")
            print(f"  Duration: {summary['total_duration_seconds']:.1f}s")
            print(f"  Success: {'[OK]' if summary['success'] else '[ERROR]'}")
            print(f"  Leads Scraped: {summary['statistics']['leads_scraped']}")
            print(f"  Leads Enriched: {summary['statistics']['leads_enriched']}")
            print(f"  Leads Synced: {summary['statistics']['leads_synced']}")
            print(f"  Errors: {summary['statistics']['total_errors']}")
            
            # Save report if requested
            if args.save_report:
                report_path = agent.save_execution_report(summary)
                if report_path:
                    print(f"  Report: {report_path}")
            
            result = summary
        
        return 0 if result.get('success', True) else 1
        
    except KeyboardInterrupt:
        print("\n[WARNING] Daily automation interrupted by user")
        return 1
    except Exception as e:
        print(f"[ERROR] Daily automation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())