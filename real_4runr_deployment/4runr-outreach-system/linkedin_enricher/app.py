#!/usr/bin/env python3
"""
LinkedIn Enricher Agent for the 4Runr Autonomous Outreach System.

This agent extracts website URLs from LinkedIn company profiles
to populate the Website field for downstream processing.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import re

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from outreach.shared.airtable_client import get_airtable_client
from outreach.shared.logging_utils import get_logger
from outreach.shared.config import config
from outreach.website_scraper.scraping_engine import WebScrapingEngine


class LinkedInEnricherAgent:
    """LinkedIn Enricher Agent for extracting website URLs from LinkedIn profiles."""
    
    def __init__(self):
        """Initialize the LinkedIn Enricher Agent."""
        self.logger = get_logger('linkedin_enricher')
        self.airtable_client = get_airtable_client()
        self.system_config = config.get_system_config()
    
    async def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need LinkedIn URL → Website URL extraction.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads with LinkedIn URLs but no Website URLs
        batch_size = limit or self.system_config['batch_size']
        leads = self._get_leads_needing_website_extraction(batch_size)
        
        if not leads:
            self.logger.log_module_activity('linkedin_enricher', 'system', 'info', 
                                           {'message': 'No leads found that need website extraction'})
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
    
    def _get_leads_needing_website_extraction(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads that have LinkedIn URLs but no Website URLs."""
        try:
            # Get leads with LinkedIn URL but no Website
            formula = "AND(NOT({LinkedIn URL} = ''), {Website} = '')"
            
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit
            )
            
            leads = []
            for record in records:
                lead_data = {
                    'id': record['id'],
                    **record['fields']
                }
                leads.append(lead_data)
            
            self.logger.log_module_activity('airtable_client', 'system', 'success', 
                                           {'message': f'Retrieved {len(leads)} records', 
                                            'formula': formula, 'max_records': limit})
            return leads
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_leads_needing_website_extraction'})
            return []
    
    async def _process_single_lead(self, lead: Dict[str, Any], scraping_engine: WebScrapingEngine) -> bool:
        """
        Process a single lead to extract website URL from LinkedIn.
        
        Args:
            lead: Lead data dictionary
            scraping_engine: Initialized scraping engine
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        company_name = lead.get('Company', 'Unknown Company')
        linkedin_url = lead.get('LinkedIn URL')
        
        self.logger.log_module_activity('linkedin_enricher', lead_id, 'start', 
                                       {'message': f'Processing {company_name}', 'linkedin_url': linkedin_url})
        
        # Validate LinkedIn URL
        if not linkedin_url or not self._is_valid_linkedin_url(linkedin_url):
            self.logger.log_module_activity('linkedin_enricher', lead_id, 'skip', 
                                           {'message': 'Invalid or missing LinkedIn URL'})
            return False
        
        try:
            # Extract website URL from LinkedIn profile
            website_url = await self._extract_website_from_linkedin(linkedin_url, scraping_engine, lead_id)
            
            if not website_url:
                self.logger.log_module_activity('linkedin_enricher', lead_id, 'skip', 
                                               {'message': 'No website URL found on LinkedIn profile'})
                return False
            
            # Update Airtable with the extracted website URL
            airtable_fields = {'Website': website_url}
            
            update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
            if update_success:
                self.logger.log_module_activity('linkedin_enricher', lead_id, 'success', 
                                               {'message': f'Successfully extracted website for {company_name}',
                                                'website_url': website_url})
                return True
            else:
                self.logger.log_module_activity('linkedin_enricher', lead_id, 'error', 
                                               {'message': 'Failed to update Airtable'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'company': company_name,
                'linkedin_url': linkedin_url
            })
            return False
    
    def _is_valid_linkedin_url(self, url: str) -> bool:
        """Check if the URL is a valid LinkedIn URL."""
        if not url:
            return False
        return 'linkedin.com' in url.lower()
    
    async def _extract_website_from_linkedin(self, linkedin_url: str, scraping_engine: WebScrapingEngine, lead_id: str) -> str:
        """
        Extract website URL from LinkedIn company profile.
        
        Args:
            linkedin_url: LinkedIn profile URL
            scraping_engine: Initialized scraping engine
            lead_id: Lead ID for logging
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            # Scrape the LinkedIn page
            scraped_data = await scraping_engine.scrape_website(linkedin_url, lead_id)
            
            if not scraped_data.get('success'):
                return None
            
            content = scraped_data.get('content', '')
            
            # Extract website URL using multiple patterns
            website_url = self._find_website_in_content(content)
            
            return website_url
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'extract_website_from_linkedin',
                'linkedin_url': linkedin_url,
                'lead_id': lead_id
            })
            return None
    
    def _find_website_in_content(self, content: str) -> str:
        """
        Find website URL in LinkedIn page content using various patterns.
        
        Args:
            content: HTML content from LinkedIn page
            
        Returns:
            Website URL if found, None otherwise
        """
        # Common patterns for website URLs on LinkedIn
        patterns = [
            # Direct website links
            r'href="(https?://(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/[^\s"]*)?)"',
            # Website field patterns
            r'"website"[^"]*"([^"]*)"',
            r'Website[^:]*:\s*([^\s<]+)',
            # Company website patterns
            r'company-website[^>]*>([^<]+)',
            r'org-top-card-summary-info-list__info-item[^>]*>\s*([^\s<]+\.[a-zA-Z]{2,})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean and validate the URL
                url = match.strip()
                if self._is_valid_website_url(url):
                    return url
        
        return None
    
    def _is_valid_website_url(self, url: str) -> bool:
        """
        Check if the extracted URL is a valid website URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        
        # Skip LinkedIn URLs and other social media
        skip_domains = ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']
        for domain in skip_domains:
            if domain in url.lower():
                return False
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        # Check if it looks like a valid domain
        domain_pattern = r'^https?://(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/.*)?$'
        return bool(re.match(domain_pattern, url))


async def main():
    """Main entry point for the LinkedIn Enricher Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr LinkedIn Enricher Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = LinkedInEnricherAgent()
    
    if args.stats:
        leads = agent._get_leads_needing_website_extraction(1000)
        print(f"LinkedIn Enricher Statistics:")
        print(f"  Leads needing website extraction: {len(leads)}")
        return True
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"LinkedIn Enricher Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)