#!/usr/bin/env python3
"""
Enhanced Daily Automation Script with Google Website Scraper

Enhanced daily lead scraping, enrichment, and synchronization that includes
Google website scraper fallback for leads without website information.
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
from utils.google_scraper_integration import GoogleScraperPipeline
from config.settings import get_settings
from utils.logging import get_logger, StructuredLogger, PerformanceLogger, LoggedOperation
from utils.validators import LeadDataValidator, clean_lead_data

class EnhancedDailyScraperAgent:
    """
    Enhanced daily automation agent with Google website scraper integration.
    """
    
    def __init__(self, max_leads: int = None, dry_run: bool = False, enable_google_scraper: bool = True):
        """
        Initialize the enhanced daily scraper agent.
        
        Args:
            max_leads: Maximum leads to process (overrides config)
            dry_run: Run in dry-run mode (no database changes)
            enable_google_scraper: Enable Google website scraper fallback
        """
        self.settings = get_settings()
        self.db = get_lead_database()
        self.sync_manager = get_sync_manager()
        
        # Configuration
        self.max_leads = max_leads or self.settings.scraper.max_leads_per_run
        self.dry_run = dry_run
        self.enable_google_scraper = enable_google_scraper
        
        # Initialize Google scraper pipeline
        if self.enable_google_scraper:
            self.google_scraper = GoogleScraperPipeline(headless=True, timeout=30000)
        
        # Logging
        self.logger = get_logger('enhanced-daily-scraper')
        self.struct_logger = StructuredLogger('enhanced-daily-scraper')
        self.perf_logger = PerformanceLogger('enhanced-daily-scraper')
        
        # Statistics tracking
        self.stats = {
            'leads_scraped': 0,
            'leads_enriched': 0,
            'leads_synced': 0,
            'websites_discovered': 0,
            'google_searches_performed': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'operations': []
        }
        
        self.logger.info("🤖 Enhanced Daily Scraper Agent initialized")
        self.logger.info(f"⚙️ Max leads: {self.max_leads}")
        self.logger.info(f"⚙️ Dry run: {self.dry_run}")
        self.logger.info(f"⚙️ Google scraper: {'Enabled' if self.enable_google_scraper else 'Disabled'}")
    
    def run_enhanced_daily_pipeline(self) -> Dict[str, Any]:
        """
        Run the enhanced daily pipeline: scrape → google_fallback → enrich → sync.
        
        Returns:
            Dictionary with pipeline results
        """
        self.logger.info("🚀 Starting enhanced daily lead pipeline")
        
        with LoggedOperation(self.struct_logger, 'enhanced_daily_pipeline', max_leads=self.max_leads):
            try:
                # Step 1: Scrape new leads (with SerpAPI website extraction)
                scraping_result = self._run_scraping_phase()
                
                # Step 2: Google website scraper fallback
                google_scraper_result = self._run_google_scraper_phase()
                
                # Step 3: Enrich existing leads
                enrichment_result = self._run_enrichment_phase()
                
                # Step 4: Sync to Airtable
                sync_result = self._run_sync_phase()
                
                # Generate summary
                summary = self._generate_enhanced_summary(
                    scraping_result, google_scraper_result, enrichment_result, sync_result
                )
                
                self.logger.info("✅ Enhanced daily pipeline completed successfully")
                return summary
                
            except Exception as e:
                self.logger.error(f"❌ Enhanced daily pipeline failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_scraping_phase(self) -> Dict[str, Any]:
        """
        Run the lead scraping phase with enhanced website extraction.
        
        Returns:
            Scraping results
        """
        self.logger.info("🔍 Starting enhanced scraping phase")
        
        with LoggedOperation(self.struct_logger, 'enhanced_scraping_phase'):
            try:
                # Initialize lead finder
                lead_finder = LeadFinder()
                
                # Scrape new leads (SerpAPI already enhanced with website extraction)
                self.perf_logger.start_timer('scraping')
                leads = lead_finder.find_montreal_executives(max_leads=self.max_leads)
                scraping_duration = self.perf_logger.end_timer('scraping', {'leads_found': len(leads)})
                
                if not leads:
                    self.logger.info("📭 No new leads found")
                    return {
                        'leads_found': 0, 
                        'leads_saved': 0, 
                        'leads_with_websites': 0,
                        'leads_without_websites': 0,
                        'duration': scraping_duration
                    }
                
                self.logger.info(f"📋 Found {len(leads)} potential leads")
                
                # Count leads with/without websites from SerpAPI
                leads_with_websites = sum(1 for lead in leads if lead.get('website'))
                leads_without_websites = len(leads) - leads_with_websites
                
                self.logger.info(f"🌐 SerpAPI website extraction: {leads_with_websites} with websites, {leads_without_websites} without")
                
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
                            self.logger.warning(f"⚠️ Invalid lead data for {lead.get('name', 'Unknown')}: {validation_result.errors}")
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to process lead: {str(e)}")
                        continue
                
                self.logger.info(f"✅ Validated {len(valid_leads)}/{len(leads)} leads")
                
                # Save leads to database
                saved_count = 0
                if not self.dry_run:
                    for lead in valid_leads:
                        try:
                            lead_id = self.db.create_lead(lead)
                            saved_count += 1
                            self.logger.debug(f"💾 Saved lead: {lead['name']} ({lead_id})")
                        
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to save lead {lead.get('name', 'Unknown')}: {str(e)}")
                            self.stats['errors'] += 1
                else:
                    saved_count = len(valid_leads)  # Simulate for dry run
                
                self.stats['leads_scraped'] = saved_count
                self.stats['operations'].append('scraping')
                
                result = {
                    'leads_found': len(leads),
                    'leads_validated': len(valid_leads),
                    'leads_saved': saved_count,
                    'leads_with_websites': leads_with_websites,
                    'leads_without_websites': leads_without_websites,
                    'duration': scraping_duration
                }
                
                self.struct_logger.log_scraping('success', leads_count=saved_count, source='serpapi')
                self.logger.info(f"✅ Enhanced scraping phase completed: {saved_count} leads saved")
                
                return result
                
            except Exception as e:
                self.struct_logger.log_scraping('failed', error=str(e))
                self.logger.error(f"❌ Enhanced scraping phase failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_google_scraper_phase(self) -> Dict[str, Any]:
        """
        Run the Google website scraper fallback phase.
        
        Returns:
            Google scraper results
        """
        if not self.enable_google_scraper:
            self.logger.info("⏭️ Google scraper disabled, skipping phase")
            return {
                'enabled': False,
                'leads_processed': 0,
                'websites_found': 0,
                'websites_not_found': 0,
                'duration': 0
            }
        
        self.logger.info("🔍 Starting Google website scraper fallback phase")
        
        with LoggedOperation(self.struct_logger, 'google_scraper_phase'):
            try:
                self.perf_logger.start_timer('google_scraper')
                
                # Process leads without websites using Google scraper
                google_result = self.google_scraper.process_leads_without_websites(limit=self.max_leads)
                
                google_duration = self.perf_logger.end_timer('google_scraper', {
                    'leads_processed': google_result['processed_count'],
                    'websites_found': google_result['websites_found']
                })
                
                # Update statistics
                self.stats['websites_discovered'] = google_result['websites_found']
                self.stats['google_searches_performed'] = google_result['processed_count']
                self.stats['operations'].append('google_scraper')
                
                # Log results
                if google_result['success']:
                    self.struct_logger.log_module_activity(
                        'enhanced_daily_scraper', 
                        'google_scraper', 
                        'success', 
                        {
                            'leads_processed': google_result['processed_count'],
                            'websites_found': google_result['websites_found'],
                            'websites_not_found': google_result['websites_not_found']
                        }
                    )
                    
                    self.logger.info(f"✅ Google scraper phase completed: {google_result['websites_found']}/{google_result['processed_count']} websites found")
                else:
                    self.logger.error(f"❌ Google scraper phase had errors: {google_result['errors']}")
                    self.stats['errors'] += len(google_result['errors'])
                
                result = {
                    'enabled': True,
                    'leads_processed': google_result['processed_count'],
                    'websites_found': google_result['websites_found'],
                    'websites_not_found': google_result['websites_not_found'],
                    'database_updates': google_result['database_updates'],
                    'airtable_updates': google_result['airtable_updates'],
                    'errors': google_result['errors'],
                    'duration': google_duration
                }
                
                return result
                
            except Exception as e:
                self.struct_logger.log_module_activity('enhanced_daily_scraper', 'google_scraper', 'failed', {'error': str(e)})
                self.logger.error(f"❌ Google scraper phase failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_enrichment_phase(self) -> Dict[str, Any]:
        """
        Run the lead enrichment phase (same as original but with enhanced logging).
        
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
                        
                        # Profile enrichment (now enhanced with website data if available)
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
                                self.logger.warning(f"⚠️ Failed to update database for {lead.name}")
                        elif enrichment_data and self.dry_run:
                            enriched_count += 1  # Simulate for dry run
                        
                        # Anti-detection delay
                        if i < len(leads_to_enrich):
                            delay = random.uniform(5, 10)
                            self.logger.debug(f"⏱️ Anti-detection delay: {delay:.1f}s")
                            time.sleep(delay)
                    
                    except Exception as e:
                        self.logger.error(f"❌ Enrichment failed for {lead.name}: {str(e)}")
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
                
                self.logger.info(f"✅ Enrichment phase completed: {enriched_count}/{len(leads_to_enrich)} leads enriched")
                
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Enrichment phase failed: {str(e)}")
                self.stats['errors'] += 1
                raise
    
    def _run_sync_phase(self) -> Dict[str, Any]:
        """
        Run the Airtable synchronization phase (same as original).
        
        Returns:
            Sync results
        """
        self.logger.info("🔄 Starting sync phase")
        
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
                
                # Sync to Airtable (now includes website data)
                self.perf_logger.start_timer('sync')
                sync_result = self.sync_manager.sync_to_airtable()
                sync_duration = self.perf_logger.end_timer('sync', {'leads_synced': sync_result.get('synced_count', 0)})
                
                synced_count = sync_result.get('synced_count', 0)
                sync_success = sync_result.get('success', False)
                
                if sync_success:
                    self.struct_logger.log_sync('success', direction='to_airtable', count=synced_count)
                    self.logger.info(f"✅ Sync completed: {synced_count} leads synced to Airtable")
                    
                    # Log engagement defaults results
                    if 'defaults_applied' in sync_result:
                        defaults = sync_result['defaults_applied']
                        defaults_count = defaults.get('count', 0)
                        if defaults_count > 0:
                            fields_updated = defaults.get('fields_updated', [])
                            self.logger.info(f"🎯 Engagement defaults applied: {defaults_count} leads updated with fields {fields_updated}")
                else:
                    self.struct_logger.log_sync('failed', direction='to_airtable', error=sync_result.get('errors', []))
                    self.logger.error(f"❌ Sync failed: {sync_result.get('failed_count', 0)} failures")
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
                self.logger.error(f"❌ Sync phase failed: {str(e)}")
                self.struct_logger.log_sync('failed', direction='to_airtable', error=str(e))
                self.stats['errors'] += 1
                raise
    
    def _generate_enhanced_summary(self, scraping_result: Dict, google_result: Dict, 
                                 enrichment_result: Dict, sync_result: Dict) -> Dict[str, Any]:
        """
        Generate enhanced pipeline execution summary.
        
        Args:
            scraping_result: Results from scraping phase
            google_result: Results from Google scraper phase
            enrichment_result: Results from enrichment phase
            sync_result: Results from sync phase
            
        Returns:
            Enhanced summary dictionary
        """
        end_time = datetime.now()
        total_duration = (end_time - self.stats['start_time']).total_seconds()
        
        summary = {
            'execution_id': f"enhanced_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': self.stats['start_time'].isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': total_duration,
            'dry_run': self.dry_run,
            'google_scraper_enabled': self.enable_google_scraper,
            'success': self.stats['errors'] == 0,
            'statistics': {
                'leads_scraped': self.stats['leads_scraped'],
                'leads_enriched': self.stats['leads_enriched'],
                'leads_synced': self.stats['leads_synced'],
                'websites_discovered': self.stats['websites_discovered'],
                'google_searches_performed': self.stats['google_searches_performed'],
                'defaults_applied': sync_result.get('defaults_applied', 0),
                'total_errors': self.stats['errors'],
                'operations_completed': self.stats['operations']
            },
            'phase_results': {
                'scraping': scraping_result,
                'google_scraper': google_result,
                'enrichment': enrichment_result,
                'sync': sync_result
            }
        }
        
        # Enhanced performance metrics
        self.perf_logger.log_performance_metrics({
            'total_duration': total_duration,
            'leads_per_minute': (self.stats['leads_scraped'] / (total_duration / 60)) if total_duration > 0 else 0,
            'enrichment_rate': (self.stats['leads_enriched'] / self.stats['leads_scraped']) if self.stats['leads_scraped'] > 0 else 0,
            'sync_rate': (self.stats['leads_synced'] / self.stats['leads_scraped']) if self.stats['leads_scraped'] > 0 else 0,
            'website_discovery_rate': (self.stats['websites_discovered'] / self.stats['google_searches_performed']) if self.stats['google_searches_performed'] > 0 else 0,
            'error_rate': (self.stats['errors'] / max(1, sum([self.stats['leads_scraped'], self.stats['leads_enriched'], self.stats['leads_synced'], self.stats['google_searches_performed']])))
        })
        
        return summary


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="4Runr Enhanced Lead Scraper Daily Automation")
    parser.add_argument('--max-leads', type=int, help='Maximum leads to process')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no database changes)')
    parser.add_argument('--disable-google-scraper', action='store_true', help='Disable Google website scraper fallback')
    parser.add_argument('--scrape-only', action='store_true', help='Only run scraping phase')
    parser.add_argument('--google-only', action='store_true', help='Only run Google scraper phase')
    parser.add_argument('--enrich-only', action='store_true', help='Only run enrichment phase')
    parser.add_argument('--sync-only', action='store_true', help='Only run sync phase')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--save-report', action='store_true', help='Save execution report to file')
    
    args = parser.parse_args()
    
    try:
        # Initialize enhanced agent
        agent = EnhancedDailyScraperAgent(
            max_leads=args.max_leads, 
            dry_run=args.dry_run,
            enable_google_scraper=not args.disable_google_scraper
        )
        
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Run specific phases or full pipeline
        if args.scrape_only:
            result = agent._run_scraping_phase()
            print(f"🔍 Scraping Results: {result}")
        elif args.google_only:
            result = agent._run_google_scraper_phase()
            print(f"🔍 Google Scraper Results: {result}")
        elif args.enrich_only:
            result = agent._run_enrichment_phase()
            print(f"💎 Enrichment Results: {result}")
        elif args.sync_only:
            result = agent._run_sync_phase()
            print(f"🔄 Sync Results: {result}")
        else:
            # Run full enhanced pipeline
            summary = agent.run_enhanced_daily_pipeline()
            
            # Display enhanced summary
            print(f"\n🎯 Enhanced Daily Pipeline Summary:")
            print(f"  Execution ID: {summary['execution_id']}")
            print(f"  Duration: {summary['total_duration_seconds']:.1f}s")
            print(f"  Success: {'✅' if summary['success'] else '❌'}")
            print(f"  Leads Scraped: {summary['statistics']['leads_scraped']}")
            print(f"  Websites Discovered: {summary['statistics']['websites_discovered']}")
            print(f"  Google Searches: {summary['statistics']['google_searches_performed']}")
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
        print("\n⚠️ Enhanced daily automation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Enhanced daily automation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())