#!/usr/bin/env python3
"""
Google Enricher Agent for the 4Runr Autonomous Outreach System.

This agent uses Google search to enrich leads with missing company information
and website URLs when we only have a person's name and LinkedIn profile.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import re

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.config import config
from website_scraper.scraping_engine import WebScrapingEngine


class GoogleEnricherAgent:
    """Google Enricher Agent for enriching leads with missing company/website information."""
    
    def __init__(self):
        """Initialize the Google Enricher Agent."""
        self.logger = get_logger('google_enricher')
        self.airtable_client = get_airtable_client()
        self.system_config = config.get_system_config()
    
    async def process_leads(self, limit: int = None) -> Dict[str, int]:
        """
        Process leads that need Google-based enrichment.
        
        Args:
            limit: Maximum number of leads to process
            
        Returns:
            Dictionary with processing statistics
        """
        # Get leads that need enrichment (missing company or website)
        batch_size = limit or self.system_config['batch_size']
        leads = self._get_leads_needing_enrichment(batch_size)
        
        if not leads:
            self.logger.log_module_activity('google_enricher', 'system', 'info', 
                                           {'message': 'No leads found that need Google enrichment'})
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
    
    def _get_leads_needing_enrichment(self, limit: int) -> List[Dict[str, Any]]:
        """Get leads that need Google enrichment (missing company or website info)."""
        try:
            # Get leads with names but missing company info or website
            formula = "AND(NOT({Full Name} = ''), OR({Company} = '', {Website} = ''))"
            
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
            self.logger.log_error(e, {'action': 'get_leads_needing_enrichment'})
            return []
    
    async def _process_single_lead(self, lead: Dict[str, Any], scraping_engine: WebScrapingEngine) -> bool:
        """
        Process a single lead to enrich with Google search.
        
        Args:
            lead: Lead data dictionary
            scraping_engine: Initialized scraping engine
            
        Returns:
            True if successful, False otherwise
        """
        lead_id = lead.get('id', 'unknown')
        full_name = lead.get('Full Name', '')
        current_company = lead.get('Company', '')
        current_website = lead.get('Website', '')
        linkedin_url = lead.get('LinkedIn URL', '')
        
        self.logger.log_module_activity('google_enricher', lead_id, 'start', 
                                       {'message': f'Processing {full_name}', 
                                        'current_company': current_company,
                                        'current_website': current_website})
        
        # Validate we have a name to search with
        if not full_name or len(full_name.strip()) < 3:
            self.logger.log_module_activity('google_enricher', lead_id, 'skip', 
                                           {'message': 'Invalid or missing full name'})
            return False
        
        try:
            # Build Google search queries
            search_queries = self._build_google_search_queries(full_name, current_company, linkedin_url)
            
            enrichment_data = {}
            
            # Try each search query until we find useful information
            for query in search_queries:
                try:
                    # Use Google search to find company/website information
                    search_results = await self._google_search_for_lead_info(query, scraping_engine, lead_id)
                    
                    if search_results:
                        # Extract company and website information from search results
                        extracted_info = self._extract_company_website_info(search_results, full_name)
                        
                        if extracted_info:
                            enrichment_data.update(extracted_info)
                            break  # Found useful info, stop searching
                    
                    # Rate limiting between searches
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self.logger.log_error(e, {
                        'action': 'google_search',
                        'query': query,
                        'lead_id': lead_id
                    })
                    continue
            
            # Update Airtable if we found new information
            if enrichment_data:
                # Only update fields that are currently empty
                airtable_fields = {}
                
                if not current_company and enrichment_data.get('company'):
                    airtable_fields['Company'] = enrichment_data['company']
                
                if not current_website and enrichment_data.get('website'):
                    airtable_fields['Website'] = enrichment_data['website']
                
                if airtable_fields:
                    update_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
                    
                    if update_success:
                        self.logger.log_module_activity('google_enricher', lead_id, 'success', 
                                                       {'message': f'Successfully enriched {full_name}',
                                                        'enriched_fields': list(airtable_fields.keys()),
                                                        'company': airtable_fields.get('Company'),
                                                        'website': airtable_fields.get('Website')})
                        return True
                    else:
                        self.logger.log_module_activity('google_enricher', lead_id, 'error', 
                                                       {'message': 'Failed to update Airtable'})
                        return False
                else:
                    self.logger.log_module_activity('google_enricher', lead_id, 'skip', 
                                                   {'message': 'No new information found to update'})
                    return False
            else:
                self.logger.log_module_activity('google_enricher', lead_id, 'skip', 
                                               {'message': 'No company/website information found via Google search'})
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'process_single_lead',
                'lead_id': lead_id,
                'full_name': full_name
            })
            return False
    
    def _build_google_search_queries(self, full_name: str, current_company: str, linkedin_url: str) -> List[str]:
        """
        Build Google search queries to find company and website information.
        
        Args:
            full_name: Person's full name
            current_company: Current company (if any)
            linkedin_url: LinkedIn URL (if any)
            
        Returns:
            List of search queries to try
        """
        queries = []
        
        # Clean up the name for searching
        clean_name = full_name.strip()
        
        # Query 1: Name + CEO/Founder + Montreal (location-based)
        queries.append(f'"{clean_name}" CEO Montreal company website')
        queries.append(f'"{clean_name}" Founder Montreal company website')
        queries.append(f'"{clean_name}" President Montreal company website')
        
        # Query 2: Name + company (if we have partial company info)
        if current_company and current_company != 'Unknown Company':
            queries.append(f'"{clean_name}" "{current_company}" website')
            queries.append(f'"{clean_name}" {current_company} CEO website')
        
        # Query 3: Name + professional context
        queries.append(f'"{clean_name}" Montreal executive company')
        queries.append(f'"{clean_name}" Montreal business owner website')
        queries.append(f'"{clean_name}" Montreal entrepreneur company')
        
        # Query 4: Name + LinkedIn context (if available)
        if linkedin_url:
            queries.append(f'"{clean_name}" LinkedIn Montreal company website')
        
        # Query 5: Broader search
        queries.append(f'"{clean_name}" Montreal company')
        queries.append(f'"{clean_name}" CEO company website')
        
        return queries[:5]  # Limit to 5 queries to avoid excessive API calls
    
    async def _google_search_for_lead_info(self, query: str, scraping_engine: WebScrapingEngine, lead_id: str) -> str:
        """
        Perform Google search and extract search results content.
        
        Args:
            query: Search query
            scraping_engine: Initialized scraping engine
            lead_id: Lead ID for logging
            
        Returns:
            Search results content if successful, None otherwise
        """
        try:
            # Build Google search URL
            google_search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            # Create new page for direct Google search scraping
            page = await scraping_engine.browser.new_page()
            
            try:
                # Set user agent and viewport
                await page.set_extra_http_headers({'User-Agent': scraping_engine.config['user_agent']})
                await page.set_viewport_size({'width': 1920, 'height': 1080})
                
                # Navigate directly to Google search results
                response = await page.goto(google_search_url, timeout=30000, wait_until='domcontentloaded')
                
                if response and response.status == 200:
                    # Wait for search results to load
                    await page.wait_for_timeout(3000)
                    
                    # Extract search results content
                    content = await page.evaluate('''() => {
                        // Extract search result snippets and titles
                        const results = [];
                        
                        // Get search result containers
                        const searchResults = document.querySelectorAll('div[data-ved] h3, div.g h3, div.rc h3');
                        const snippets = document.querySelectorAll('div[data-ved] span, div.g .VwiC3b, div.rc .VwiC3b');
                        
                        // Extract titles and snippets
                        searchResults.forEach((title, index) => {
                            const titleText = title.textContent || '';
                            const snippet = snippets[index] ? snippets[index].textContent || '' : '';
                            if (titleText.length > 0) {
                                results.push(titleText + ' ' + snippet);
                            }
                        });
                        
                        // Also get any visible text that might contain company info
                        const allText = document.body.innerText || '';
                        
                        return results.join(' ') + ' ' + allText;
                    }''')
                    
                    if content and len(content.strip()) > 50:
                        self.logger.log_module_activity('google_enricher', lead_id, 'info', 
                                                       {'message': f'Google search successful for: {query}',
                                                        'content_length': len(content)})
                        return content
                    else:
                        self.logger.log_module_activity('google_enricher', lead_id, 'warning', 
                                                       {'message': f'No useful content found in Google search for: {query}'})
                        return None
                else:
                    self.logger.log_module_activity('google_enricher', lead_id, 'warning', 
                                                   {'message': f'Failed to load Google search for: {query}'})
                    return None
                    
            finally:
                await page.close()
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'google_search_for_lead_info',
                'query': query,
                'lead_id': lead_id
            })
            return None
    
    def _extract_company_website_info(self, search_content: str, full_name: str) -> Dict[str, str]:
        """
        Extract company and website information from Google search results.
        
        Args:
            search_content: HTML content from Google search
            full_name: Person's name to validate relevance
            
        Returns:
            Dictionary with extracted company and website info
        """
        extracted_info = {}
        
        try:
            # Extract company names from search results
            company = self._extract_company_from_search(search_content, full_name)
            if company:
                extracted_info['company'] = company
            
            # Extract website URLs from search results
            website = self._extract_website_from_search(search_content, full_name)
            if website:
                extracted_info['website'] = website
            
            return extracted_info
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'extract_company_website_info',
                'full_name': full_name
            })
            return {}
    
    def _extract_company_from_search(self, content: str, full_name: str) -> str:
        """Extract company name from Google search results."""
        # Patterns to find company names in search results
        patterns = [
            # "John Smith - CEO at Company Name"
            rf'{re.escape(full_name)}.*?(?:CEO|President|Founder).*?(?:at|of)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International)?)',
            
            # "John Smith, CEO of Company Name"
            rf'{re.escape(full_name)}.*?(?:CEO|President|Founder).*?(?:of|at)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International)?)',
            
            # Company Name - John Smith (CEO)
            r'([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International)?)\s*[-–]\s*' + re.escape(full_name),
            
            # Look for company indicators near the name
            rf'{re.escape(full_name)}.*?(?:works at|employed at|CEO of|President of|Founder of)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                company = match.strip()
                # Clean up the company name
                company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
                company = company.strip(' ,-.')  # Remove trailing punctuation
                
                # Validate company name
                if self._is_valid_company_name(company):
                    return company
        
        return None
    
    def _extract_website_from_search(self, content: str, full_name: str) -> str:
        """Extract website URL from Google search results."""
        # Look for website URLs in search results
        patterns = [
            # Direct website URLs
            r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # URLs in search result snippets
            r'(?:Visit|Website|Site):\s*https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # Company domain patterns
            r'([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))(?:\s|$|\.|\)|,)',
        ]
        
        found_websites = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                website = match.strip().lower()
                
                # Skip common non-company domains
                skip_domains = [
                    'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
                    'youtube.com', 'google.com', 'gmail.com', 'outlook.com',
                    'yahoo.com', 'hotmail.com', 'example.com', 'wikipedia.org'
                ]
                
                if any(skip_domain in website for skip_domain in skip_domains):
                    continue
                
                # Add protocol if missing
                if not website.startswith('http'):
                    website = f"https://{website}"
                
                if self._is_valid_website_url(website):
                    found_websites.append(website)
        
        # Return the first valid website found
        if found_websites:
            # Prefer .com domains
            com_domains = [w for w in found_websites if '.com' in w]
            return com_domains[0] if com_domains else found_websites[0]
        
        return None
    
    def _is_valid_company_name(self, company: str) -> bool:
        """Validate if a string looks like a valid company name."""
        if not company or len(company) < 3:
            return False
        
        # Skip common false positives
        skip_terms = [
            'linkedin', 'facebook', 'twitter', 'google', 'montreal', 'quebec',
            'canada', 'ceo', 'president', 'founder', 'executive', 'manager',
            'director', 'officer', 'unknown', 'company', 'inc', 'corp'
        ]
        
        company_lower = company.lower()
        if any(term in company_lower for term in skip_terms):
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', company):
            return False
        
        return True
    
    def _is_valid_website_url(self, url: str) -> bool:
        """Validate if a URL looks like a valid website."""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


async def main():
    """Main entry point for the Google Enricher Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Google Enricher Agent')
    parser.add_argument('--limit', type=int, help='Maximum number of leads to process')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    
    args = parser.parse_args()
    
    agent = GoogleEnricherAgent()
    
    if args.stats:
        leads = agent._get_leads_needing_enrichment(1000)
        print(f"Google Enricher Statistics:")
        print(f"  Leads needing enrichment: {len(leads)}")
        return True
    
    # Process leads in batch
    results = await agent.process_leads(limit=args.limit)
    
    print(f"Google Enricher Results:")
    print(f"  Processed: {results['processed']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Errors: {results['errors']}")
    
    return results['successful'] > 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)