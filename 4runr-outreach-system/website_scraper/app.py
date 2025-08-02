#!/usr/bin/env python3
"""
Website Scraper Agent for the 4Runr Autonomous Outreach System.

This agent scrapes company websites to extract business information
for personalized outreach campaigns.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.validation import validate_website_url, validate_airtable_fields
from shared.config import config

from .scraping_engine import WebScrapingEngine
from .content_analyzer import ContentAnalyzer


class WebsiteScraperAgent:
    """Main Website Scraper Agent class."""
    
    def __init__(self):
        """Initialize the Website Scraper Agent."""
        self.logger = get_logger('website_scraper')
        self.airtable_client = get_airtable_client()
        self.content_analyzer = ContentAnalyzer()
        self.system_config = config.get_system_config()
    
    async def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need website scraping.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads that need website scraping
        batch_size = limit or self.system_config['batch_size']
        leads = self.airtable_client.get_leads_for_outreach(limit=batch_size)
        
        if not leads:
            self.logger.log_module_activity('website_scraper', 'system', 'info', 
                                           {'message': 'No leads found that need website scraping'})
            return {'processed': 0, 'successful': 0, 'errors': 0}
        
        self.logger.log_pipeline_start(len(leads))
        
        stats = {'processed': 0, 'successful': 0, 'errors': 0}
        
        # Initialize scraping engine
        async with WebScrapingEngine() as scraping_engine:
            for i, lead in enumerate(leads):
                try:
                    # Log progress
                    self.logger.log_batch_progress(i + 1, len(leads))
                    
                    # Process individual lead
                    success = await self._process_single_lead(lead, scraping_engine)
                    
                    stats['processed'] += 1
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['errors'] += 1
                    
                    # Rate limiting
                    if i < len(leads) - 1:  # Don't delay after the last lead
                        await asyncio.sleep(self.system_config['rate_limit_delay'])
                        
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
    
    async def _process_single_lead(self, lead: Dict[str, Any], scraping_engine: WebScrapingEngine) -> bool:
        """
        Process a single lead for website scraping.
        
        Args:
            lead: Lead data dictionary
            scraping_engine: Initialized scraping engine
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        company_name = lead.get('Company', 'Unknown Company')
        website_url = lead.get('company_website_url')
        
        self.logger.log_module_activity('website_scraper', lead_id, 'start', 
                                       {'message': f'Processing {company_name}', 'website_url': website_url})
        
        # Validate website URL
        if not website_url or not validate_website_url(website_url):
            self.logger.log_module_activity('website_scraper', lead_id, 'skip', 
                                           {'message': 'Invalid or missing website URL'})
            return False
        
        try:
            # Scrape the website
            scraped_data = await scraping_engine.scrape_website(website_url, lead_id)
            
            if not scraped_data.get('success'):
                self.logger.log_module_activity('website_scraper', lead_id, 'error', 
                                               {'message': 'Website scraping failed'})
                return False
            
            # Analyze the content
            analysis_result = self.content_analyzer.analyze_content(scraped_data, lead_id)
            
            # Prepare Airtable update
            airtable_fields = {
                'Company_Description': analysis_result['company_description'],
                'Top_Services': analysis_result['top_services'],
                'Tone': analysis_result['tone'],
                'Website_Insights': analysis_result['website_insights']
            }
            
            # Validate fields before update
            validation_result = validate_airtable_fields(airtable_fields)
            if not validation_result['valid']:
                self.logger.log_module_activity('website_scraper', lead_id, 'error', 
                                               {'message': 'Field validation failed', 
                                                'errors': validation_result['errors']})
                return False
            
            # Update Airtable
            update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
            if update_success:
                self.logger.log_module_activity('website_scraper', lead_id, 'success', 
                                               {'message': f'Successfully processed {company_name}',
                                                'description_length': len(analysis_result['company_description']),
                                                'services_length': len(analysis_result['top_services']),
                                                'tone': analysis_result['tone']})
                return True
            else:
                self.logger.log_module_activity('website_scraper', lead_id, 'error', 
                                               {'message': 'Failed to update Airtable'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'company': company_name,
                'website_url': website_url
            })
            return False
    
    async def process_specific_lead(self, lead_id: str) -> bool:
        """
        Process a specific lead by ID.
        
        Args:
            lead_id: Airtable record ID
            
        Returns:
            True if successful, False otherwise
        """
        lead = self.airtable_client.get_lead_by_id(lead_id)
        if not lead:
            self.logger.log_module_activity('website_scraper', lead_id, 'error', 
                                           {'message': 'Lead not found'})
            return False
        
        async with WebScrapingEngine() as scraping_engine:
            return await self._process_single_lead(lead, scraping_engine)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads ready for processing.
        
        Returns:
            Dictionary with processing statistics
        """
        leads = self.airtable_client.get_leads_for_outreach(limit=1000)  # Get more for stats
        
        stats = {
            'total_leads_ready': len(leads),
            'leads_with_websites': 0,
            'leads_without_websites': 0
        }
        
        for lead in leads:
            if lead.get('company_website_url'):
                stats['leads_with_websites'] += 1
            else:
                stats['leads_without_websites'] += 1
        
        return stats


async def main():
    """Main entry point for the Website Scraper Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Website Scraper Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--lead-id', help='Process a specific lead by ID')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = WebsiteScraperAgent()
    
    if args.stats:
        stats = agent.get_processing_stats()
        print(f"Processing Statistics:")
        print(f"  Total leads ready: {stats['total_leads_ready']}")
        print(f"  Leads with websites: {stats['leads_with_websites']}")
        print(f"  Leads without websites: {stats['leads_without_websites']}")
        return True
    
    if args.lead_id:
        success = await agent.process_specific_lead(args.lead_id)
        return success
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"Website Scraper Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)