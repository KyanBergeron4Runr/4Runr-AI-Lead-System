#!/usr/bin/env python3
"""
SerpAPI Lead Scraper

Consolidated SerpAPI-based LinkedIn lead scraping for the 4runr-lead-scraper system.
Uses SerpAPI to search for Montreal CEOs and LinkedIn profiles.
"""

import os
import json
import time
import logging
import requests
import random
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('serpapi-scraper')

class SerpAPILeadScraper:
    """
    SerpAPI-based lead scraper for LinkedIn profiles.
    Focuses on Montreal-based executives and business leaders.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SerpAPI scraper.
        
        Args:
            api_key: SerpAPI key. If None, reads from environment.
        """
        self.serpapi_key = api_key or os.getenv('SERPAPI_KEY')
        
        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")
        
        # Get configuration from environment
        self.max_leads_per_run = int(os.getenv('MAX_LEADS_PER_RUN', '10'))
        self.search_location = os.getenv('SEARCH_LOCATION', 'Montreal, Quebec, Canada')
        
        # Parse search queries from environment
        search_queries_str = os.getenv('SEARCH_QUERIES', 'CEO,Founder,President')
        self.search_queries = [q.strip() for q in search_queries_str.split(',')]
        
        logger.info("🔍 SerpAPI Lead Scraper initialized")
        logger.info(f"✅ SerpAPI key configured")
        logger.info(f"📍 Search location: {self.search_location}")
        logger.info(f"🎯 Search queries: {', '.join(self.search_queries)}")
    
    def search_montreal_ceos(self, max_results: int = 10) -> List[Dict]:
        """
        Search for Montreal CEOs using SerpAPI.
        
        Args:
            max_results: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries
        """
        all_leads = []
        processed_urls = set()
        
        # Build search queries
        queries = self._build_search_queries()
        
        # Limit queries to conserve API calls
        queries_to_use = queries[:3]  # Use first 3 queries
        
        for i, query in enumerate(queries_to_use, 1):
            if len(all_leads) >= max_results:
                break
                
            logger.info(f"🔍 SerpAPI Search {i}/{len(queries_to_use)}: {query}")
            
            try:
                results = self._execute_serpapi_search(query)
                
                if results:
                    logger.info(f"✅ Found {len(results)} search results")
                    
                    # Extract LinkedIn profiles from results
                    for result in results:
                        lead = self._extract_linkedin_lead(result)
                        
                        if lead and lead['linkedin_url'] not in processed_urls:
                            processed_urls.add(lead['linkedin_url'])
                            all_leads.append(lead)
                            logger.info(f"📋 Found: {lead['name']} - {lead['title']} at {lead['company']}")
                        
                        if len(all_leads) >= max_results:
                            break
                
                # Rate limiting between searches
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ SerpAPI search error: {str(e)}")
                continue
        
        logger.info(f"✅ SerpAPI scraping completed: {len(all_leads)} leads found")
        return all_leads
    
    def search_by_company_type(self, company_type: str, location: str = None) -> List[Dict]:
        """
        Search for leads by company type.
        
        Args:
            company_type: Type of company (e.g., "tech startups", "consulting firms")
            location: Search location (defaults to configured location)
            
        Returns:
            List of lead dictionaries
        """
        location = location or self.search_location
        
        # Build targeted queries for company type
        queries = [
            f"{location} {company_type} CEO LinkedIn site:linkedin.com/in",
            f"{location} {company_type} founder LinkedIn site:linkedin.com/in",
            f"{location} {company_type} president LinkedIn site:linkedin.com/in"
        ]
        
        all_leads = []
        processed_urls = set()
        
        for query in queries:
            try:
                results = self._execute_serpapi_search(query)
                
                if results:
                    for result in results:
                        lead = self._extract_linkedin_lead(result)
                        
                        if lead and lead['linkedin_url'] not in processed_urls:
                            processed_urls.add(lead['linkedin_url'])
                            all_leads.append(lead)
                
                # Rate limiting
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ Company type search error: {str(e)}")
                continue
        
        logger.info(f"✅ Company type search completed: {len(all_leads)} leads found for {company_type}")
        return all_leads
    
    def validate_linkedin_profiles(self, leads: List[Dict]) -> List[Dict]:
        """
        Validate LinkedIn profiles by checking if URLs are accessible.
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of validated leads
        """
        validated_leads = []
        
        for lead in leads:
            linkedin_url = lead.get('linkedin_url')
            if not linkedin_url:
                continue
            
            try:
                # Simple HEAD request to check if profile exists
                response = requests.head(linkedin_url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    lead['verified'] = True
                    validated_leads.append(lead)
                    logger.debug(f"✅ Validated: {lead['name']}")
                else:
                    logger.debug(f"❌ Invalid profile: {lead['name']} ({response.status_code})")
                
                # Rate limiting for validation requests
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.warning(f"⚠️ Validation failed for {lead['name']}: {str(e)}")
                # Include unvalidated leads but mark them
                lead['verified'] = False
                validated_leads.append(lead)
        
        logger.info(f"✅ Profile validation completed: {len(validated_leads)} leads validated")
        return validated_leads
    
    def _build_search_queries(self) -> List[str]:
        """Build search queries based on configuration."""
        queries = []
        
        for query_term in self.search_queries:
            queries.extend([
                f"{self.search_location} {query_term} LinkedIn site:linkedin.com/in",
                f"{self.search_location} Chief {query_term} LinkedIn site:linkedin.com/in",
                f"{self.search_location} {query_term} LinkedIn site:linkedin.com/in -Shopify -CGI -Lightspeed",
                f"{self.search_location} startup {query_term} LinkedIn site:linkedin.com/in",
                f"{self.search_location} company {query_term} LinkedIn site:linkedin.com/in"
            ])
        
        return queries
    
    def _execute_serpapi_search(self, query: str) -> List[Dict]:
        """
        Execute a single SerpAPI search.
        
        Args:
            query: Search query string
            
        Returns:
            List of search results
        """
        url = "https://serpapi.com/search"
        params = {
            'q': query,
            'api_key': self.serpapi_key,
            'engine': 'google',
            'num': 5,  # 5 results per query
            'safe': 'active',
            'location': self.search_location,
            'gl': 'ca',  # Canada
            'hl': 'en'   # English
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('organic_results', [])
        elif response.status_code == 429:
            logger.warning("⚠️ SerpAPI rate limit reached - waiting...")
            time.sleep(60)
            return []
        else:
            logger.warning(f"⚠️ SerpAPI request failed: {response.status_code}")
            return []
    
    def _extract_linkedin_lead(self, result: Dict) -> Optional[Dict]:
        """
        Extract lead information from SerpAPI search result.
        
        Args:
            result: SerpAPI search result dictionary
            
        Returns:
            Lead dictionary or None if extraction fails
        """
        try:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            
            # Must be a LinkedIn profile
            if 'linkedin.com/in/' not in link:
                return None
            
            # Extract name from title (usually "Name - Title - Company | LinkedIn")
            name = ""
            job_title = ""
            company = ""
            
            if ' - ' in title:
                parts = title.split(' - ')
                if len(parts) >= 1:
                    name = parts[0].strip()
                if len(parts) >= 2:
                    job_title = parts[1].strip()
                if len(parts) >= 3:
                    company_part = parts[2].strip()
                    # Remove "| LinkedIn" if present
                    if '|' in company_part:
                        company = company_part.split('|')[0].strip()
                    else:
                        company = company_part
            
            # If name extraction failed, try alternative parsing
            if not name and title:
                # Sometimes format is "Name | LinkedIn"
                if '|' in title:
                    name = title.split('|')[0].strip()
                else:
                    name = title.strip()
            
            # Extract additional info from snippet
            if not job_title and snippet:
                # Look for job titles in snippet
                ceo_indicators = ['CEO', 'Chief Executive Officer', 'President', 'Founder', 'Owner', 'Director']
                for indicator in ceo_indicators:
                    if indicator.lower() in snippet.lower():
                        job_title = indicator
                        break
            
            # Extract company from snippet if not found in title
            if not company and snippet:
                company = self._extract_company_from_snippet(snippet)
            
            # Validate we have minimum required info
            if not name or not link:
                return None
            
            # Check if this looks like a location-based person
            location_indicators = self._get_location_indicators()
            is_target_location = any(indicator in (title + ' ' + snippet).lower() 
                                   for indicator in location_indicators)
            
            if not is_target_location:
                logger.debug(f"⚠️ Skipping non-target location profile: {name}")
                return None
            
            # Create lead object
            lead = {
                "name": name,
                "title": job_title or "Executive",
                "company": company or "Unknown Company",
                "linkedin_url": link,
                "location": self.search_location,
                "email": None,
                "verified": False,
                "enriched": False,
                "scraped_at": datetime.now().isoformat(),
                "scraping_source": "serpapi",
                "search_query": result.get('query', ''),
                "search_context": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                "status": "scraped"
            }
            
            return lead
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract lead from result: {str(e)}")
            return None
    
    def _extract_company_from_snippet(self, snippet: str) -> str:
        """Extract company name from search result snippet."""
        lines = snippet.split('.')
        for line in lines:
            line = line.strip()
            # Look for patterns like "at Company Name" or "chez Company"
            if ' at ' in line.lower():
                parts = line.lower().split(' at ')
                if len(parts) > 1:
                    return parts[1].strip().title()
            elif ' chez ' in line.lower():
                parts = line.lower().split(' chez ')
                if len(parts) > 1:
                    return parts[1].strip().title()
            elif any(word in line.lower() for word in ['company', 'inc', 'corp', 'ltd', 'llc', 'international']):
                return line.strip()
        
        return ""
    
    def _get_location_indicators(self) -> List[str]:
        """Get location indicators based on configured search location."""
        location_lower = self.search_location.lower()
        indicators = []
        
        if 'montreal' in location_lower:
            indicators.extend(['montreal', 'québec', 'quebec', 'canada', 'qc'])
        elif 'toronto' in location_lower:
            indicators.extend(['toronto', 'ontario', 'canada', 'on'])
        elif 'vancouver' in location_lower:
            indicators.extend(['vancouver', 'british columbia', 'canada', 'bc'])
        else:
            # Generic Canada indicators
            indicators.extend(['canada', 'canadian'])
        
        return indicators


# Async wrapper for compatibility
async def scrape_linkedin_leads_serpapi(max_results: int = 10) -> List[Dict]:
    """
    Async wrapper for SerpAPI LinkedIn scraping.
    
    Args:
        max_results: Maximum number of leads to return
        
    Returns:
        List of lead dictionaries
    """
    try:
        scraper = SerpAPILeadScraper()
        
        logger.info(f"🚀 Starting SerpAPI LinkedIn scraping for {max_results} leads")
        
        # Search for leads
        leads = scraper.search_montreal_ceos(max_results=max_results)
        
        if not leads:
            logger.warning("⚠️ No leads found via SerpAPI")
            return []
        
        logger.info(f"✅ SerpAPI LinkedIn scraping completed: {len(leads)} leads found")
        
        # Log sample results
        for i, lead in enumerate(leads[:3], 1):
            logger.info(f"   📋 {i}. {lead['name']} - {lead['title']} at {lead['company']}")
            logger.info(f"      🔗 {lead['linkedin_url']}")
        
        return leads
        
    except Exception as e:
        logger.error(f"❌ SerpAPI LinkedIn scraping failed: {str(e)}")
        return []


# Synchronous wrapper
def scrape_linkedin_leads_serpapi_sync(max_results: int = 10) -> List[Dict]:
    """
    Synchronous wrapper for SerpAPI scraping.
    
    Args:
        max_results: Maximum number of leads to return
        
    Returns:
        List of lead dictionaries
    """
    import asyncio
    return asyncio.run(scrape_linkedin_leads_serpapi(max_results))


if __name__ == "__main__":
    # Test the SerpAPI scraper
    leads = scrape_linkedin_leads_serpapi_sync(5)
    print(f"\n✅ Found {len(leads)} leads via SerpAPI:")
    for lead in leads:
        print(f"- {lead['name']} ({lead['title']}) at {lead['company']}")
        print(f"  LinkedIn: {lead['linkedin_url']}")
        print()