#!/usr/bin/env python3
"""
Google Enricher

Uses Google search to enrich leads with missing company information
and website URLs when we only have a person's name and LinkedIn profile.
"""

import os
import re
import time
import random
import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger('google-enricher')

class GoogleEnricher:
    """
    Google-based enrichment system for finding missing company and website data.
    """
    
    def __init__(self):
        """Initialize the Google enricher."""
        self.session = requests.Session()
        
        # User agents for web scraping
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        
        # Base headers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 3  # Minimum 3 seconds between Google requests
        
        # Configuration
        self.search_timeout = int(os.getenv('GOOGLE_SEARCH_TIMEOUT', '15'))
        self.max_search_queries = int(os.getenv('MAX_GOOGLE_QUERIES_PER_LEAD', '3'))
        
        logger.info("🔍 Google Enricher initialized")
    
    def enrich_lead_with_google(self, lead: Dict) -> Dict:
        """
        Enrich a lead with Google search data.
        
        Args:
            lead: Lead dictionary with name, company, etc.
            
        Returns:
            Dictionary with enrichment results
        """
        name = lead.get('name', '')
        current_company = lead.get('company', '')
        current_website = lead.get('website', '')
        linkedin_url = lead.get('linkedin_url', '')
        
        logger.info(f"🔍 Google enriching: {name} at {current_company}")
        
        enrichment_result = {
            'success': False,
            'found_company': None,
            'found_website': None,
            'search_queries_used': [],
            'enriched_at': datetime.now().isoformat(),
            'error': None
        }
        
        # Skip if we already have both company and website
        if current_company and current_company != 'Unknown Company' and current_website:
            enrichment_result['error'] = 'Lead already has company and website data'
            logger.info(f"⏭️ Skipping {name} - already has complete data")
            return enrichment_result
        
        # Validate we have a name to search with
        if not name or len(name.strip()) < 3:
            enrichment_result['error'] = 'Invalid or missing name for Google search'
            logger.warning(f"⚠️ Skipping {name} - invalid name")
            return enrichment_result
        
        try:
            # Build Google search queries
            search_queries = self._build_google_search_queries(name, current_company, linkedin_url)
            
            # Try each search query until we find useful information
            for query in search_queries[:self.max_search_queries]:
                try:
                    logger.info(f"🔍 Google searching: {query}")
                    enrichment_result['search_queries_used'].append(query)
                    
                    # Perform Google search
                    search_results = self._perform_google_search(query)
                    
                    if search_results:
                        # Extract company and website information
                        extracted_info = self._extract_company_website_from_results(search_results, name)
                        
                        if extracted_info:
                            # Update enrichment result with found data
                            if extracted_info.get('company') and not enrichment_result['found_company']:
                                enrichment_result['found_company'] = extracted_info['company']
                            
                            if extracted_info.get('website') and not enrichment_result['found_website']:
                                enrichment_result['found_website'] = extracted_info['website']
                            
                            # If we found both or what we were looking for, stop searching
                            if (enrichment_result['found_company'] and enrichment_result['found_website']) or \
                               (current_company and enrichment_result['found_website']) or \
                               (current_website and enrichment_result['found_company']):
                                break
                    
                    # Rate limiting between searches
                    self._apply_rate_limiting()
                    
                except Exception as e:
                    logger.warning(f"⚠️ Google search failed for query '{query}': {str(e)}")
                    continue
            
            # Determine success
            enrichment_result['success'] = bool(
                enrichment_result['found_company'] or enrichment_result['found_website']
            )
            
            if enrichment_result['success']:
                logger.info(f"✅ Google enrichment successful for {name}")
                if enrichment_result['found_company']:
                    logger.info(f"   🏢 Found company: {enrichment_result['found_company']}")
                if enrichment_result['found_website']:
                    logger.info(f"   🌐 Found website: {enrichment_result['found_website']}")
            else:
                enrichment_result['error'] = 'No additional company/website data found via Google'
                logger.info(f"📭 No additional data found for {name}")
            
            return enrichment_result
            
        except Exception as e:
            logger.error(f"❌ Google enrichment failed for {name}: {str(e)}")
            enrichment_result['error'] = str(e)
            return enrichment_result
    
    def _build_google_search_queries(self, name: str, current_company: str, linkedin_url: str) -> List[str]:
        """
        Build Google search queries to find company and website information.
        
        Args:
            name: Person's full name
            current_company: Current company (if any)
            linkedin_url: LinkedIn URL (if any)
            
        Returns:
            List of search queries to try
        """
        queries = []
        clean_name = name.strip()
        
        # Query 1: Name + CEO/Executive + Montreal (location-based)
        queries.append(f'"{clean_name}" CEO Montreal company website')
        queries.append(f'"{clean_name}" Founder Montreal company website')
        queries.append(f'"{clean_name}" President Montreal executive')
        
        # Query 2: Name + company (if we have partial company info)
        if current_company and current_company not in ['Unknown Company', 'Unknown', '']:
            queries.append(f'"{clean_name}" "{current_company}" website')
            queries.append(f'"{clean_name}" {current_company} CEO')
        
        # Query 3: Name + professional context
        queries.append(f'"{clean_name}" Montreal business owner')
        queries.append(f'"{clean_name}" Montreal entrepreneur company')
        queries.append(f'"{clean_name}" executive Montreal')
        
        # Query 4: Name + LinkedIn context (if available)
        if linkedin_url:
            queries.append(f'"{clean_name}" LinkedIn Montreal company')
        
        # Query 5: Broader searches
        queries.append(f'"{clean_name}" Montreal company')
        queries.append(f'"{clean_name}" CEO company')
        
        return queries
    
    def _perform_google_search(self, query: str) -> Optional[str]:
        """
        Perform Google search and return HTML content.
        
        Args:
            query: Search query string
            
        Returns:
            HTML content if successful, None otherwise
        """
        try:
            # Build Google search URL
            encoded_query = quote_plus(query)
            google_url = f"https://www.google.com/search?q={encoded_query}&num=10"
            
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Set headers
            headers = self.base_headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            # Perform request
            response = self.session.get(
                google_url,
                headers=headers,
                timeout=self.search_timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"⚠️ Google search returned status {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Google search request failed: {str(e)}")
            return None
    
    def _extract_company_website_from_results(self, html_content: str, name: str) -> Dict[str, str]:
        """
        Extract company and website information from Google search results.
        
        Args:
            html_content: HTML content from Google search
            name: Person's name to validate relevance
            
        Returns:
            Dictionary with extracted company and website info
        """
        extracted_info = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get all search result text
            search_text = soup.get_text()
            
            # Extract company names
            company = self._extract_company_from_search_text(search_text, name)
            if company:
                extracted_info['company'] = company
            
            # Extract website URLs
            website = self._extract_website_from_search_results(soup, search_text, name)
            if website:
                extracted_info['website'] = website
            
            return extracted_info
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract data from search results: {str(e)}")
            return {}
    
    def _extract_company_from_search_text(self, search_text: str, name: str) -> Optional[str]:
        """Extract company name from Google search results text."""
        try:
            # Patterns to find company names in search results
            patterns = [
                # "John Smith - CEO at Company Name"
                rf'{re.escape(name)}.*?(?:CEO|President|Founder|Director).*?(?:at|of)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Solutions|Group|Company)?)',
                
                # "John Smith, CEO of Company Name"
                rf'{re.escape(name)}.*?(?:CEO|President|Founder|Director).*?(?:of|at)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Solutions|Group|Company)?)',
                
                # Company Name - John Smith (CEO)
                r'([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Solutions|Group|Company)?)\s*[-–]\s*' + re.escape(name),
                
                # Look for company indicators near the name
                rf'{re.escape(name)}.*?(?:works at|employed at|CEO of|President of|Founder of)\s+([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Solutions|Group|Company)?)',
                
                # Montreal company patterns
                rf'{re.escape(name)}.*?Montreal.*?([A-Z][A-Za-z\s&,.-]+(?:Inc|Corp|Ltd|LLC|International|Solutions|Group|Company)?)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    company = match.strip()
                    # Clean up the company name
                    company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
                    company = company.strip(' ,-.')  # Remove trailing punctuation
                    
                    # Validate company name
                    if self._is_valid_company_name(company):
                        logger.info(f"🏢 Found company via pattern matching: {company}")
                        return company
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Company extraction failed: {str(e)}")
            return None
    
    def _extract_website_from_search_results(self, soup: BeautifulSoup, search_text: str, name: str) -> Optional[str]:
        """Extract website URL from Google search results."""
        try:
            found_websites = []
            
            # Method 1: Extract from search result links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    if self._is_valid_website_url(actual_url):
                        found_websites.append(actual_url)
                elif href.startswith('http') and self._is_valid_website_url(href):
                    found_websites.append(href)
            
            # Method 2: Extract from search result text using patterns
            website_patterns = [
                # Direct website URLs
                r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
                
                # Company domain patterns
                r'([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))(?:\s|$|\.|\)|,)',
            ]
            
            for pattern in website_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    website = match.strip().lower()
                    
                    # Add protocol if missing
                    if not website.startswith('http'):
                        website = f"https://{website}"
                    
                    if self._is_valid_website_url(website):
                        found_websites.append(website)
            
            # Filter and return best website
            if found_websites:
                # Remove duplicates and filter out unwanted domains
                unique_websites = list(set(found_websites))
                valid_websites = [w for w in unique_websites if self._is_company_website(w)]
                
                if valid_websites:
                    # Prefer .com domains
                    com_domains = [w for w in valid_websites if '.com' in w]
                    selected_website = com_domains[0] if com_domains else valid_websites[0]
                    logger.info(f"🌐 Found website via search results: {selected_website}")
                    return selected_website
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Website extraction failed: {str(e)}")
            return None
    
    def _is_valid_company_name(self, company: str) -> bool:
        """Validate if a string looks like a valid company name."""
        if not company or len(company) < 3:
            return False
        
        # Skip common false positives
        skip_terms = [
            'linkedin', 'facebook', 'twitter', 'google', 'montreal', 'quebec',
            'canada', 'ceo', 'president', 'founder', 'executive', 'manager',
            'director', 'officer', 'unknown', 'company', 'search', 'results'
        ]
        
        company_lower = company.lower()
        if any(term in company_lower for term in skip_terms):
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', company):
            return False
        
        # Skip very short or very long names
        if len(company) < 3 or len(company) > 100:
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
    
    def _is_company_website(self, url: str) -> bool:
        """Check if URL looks like a company website (not social media, etc.)."""
        if not url:
            return False
        
        # Skip common non-company domains
        skip_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'google.com', 'gmail.com', 'outlook.com',
            'yahoo.com', 'hotmail.com', 'wikipedia.org', 'github.com'
        ]
        
        url_lower = url.lower()
        return not any(domain in url_lower for domain in skip_domains)
    
    def _apply_rate_limiting(self):
        """Apply rate limiting for Google requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def batch_enrich_with_google(self, leads: List[Dict], max_leads: int = None) -> List[Dict]:
        """
        Enrich multiple leads with Google search data.
        
        Args:
            leads: List of lead dictionaries
            max_leads: Maximum number of leads to process
            
        Returns:
            List of enrichment results
        """
        if max_leads:
            leads = leads[:max_leads]
        
        logger.info(f"🔍 Starting batch Google enrichment for {len(leads)} leads")
        
        results = []
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"🔍 Processing lead {i}/{len(leads)}: {lead.get('name', 'Unknown')}")
            
            try:
                result = self.enrich_lead_with_google(lead)
                result['lead_id'] = lead.get('id')
                results.append(result)
                
                # Rate limiting between leads (longer delay)
                if i < len(leads):
                    delay = random.uniform(5, 8)  # 5-8 seconds between leads
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Batch Google enrichment failed for lead {i}: {str(e)}")
                results.append({
                    'lead_id': lead.get('id'),
                    'success': False,
                    'error': str(e),
                    'enriched_at': datetime.now().isoformat()
                })
        
        successful = sum(1 for r in results if r.get('success'))
        logger.info(f"✅ Batch Google enrichment completed: {successful}/{len(results)} successful")
        
        return results


# Convenience function
def enrich_lead_with_google(lead: Dict) -> Dict:
    """
    Enrich a single lead with Google search data (convenience function).
    
    Args:
        lead: Lead dictionary
        
    Returns:
        Enrichment result dictionary
    """
    enricher = GoogleEnricher()
    return enricher.enrich_lead_with_google(lead)


if __name__ == "__main__":
    # Test the Google enricher
    enricher = GoogleEnricher()
    
    print("🧪 Testing Google Enricher...")
    
    # Test lead
    test_lead = {
        'name': 'John Smith',
        'company': '',  # Missing company
        'website': '',  # Missing website
        'linkedin_url': 'https://linkedin.com/in/johnsmith',
        'id': 'test_123'
    }
    
    result = enricher.enrich_lead_with_google(test_lead)
    print(f"Google enrichment result: {result}")
    
    print("✅ Google enricher test completed")