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
        self.serpapi_key = api_key or os.getenv('SERPAPI_KEY') or os.getenv('SERPAPI_API_KEY')
        
        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY or SERPAPI_API_KEY not found in environment variables")
        
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
            
            # Extract website URL if present in SerpAPI response
            website_url = self._extract_website_from_serpapi_result(result)
            
            # Log website extraction result for debugging
            if website_url:
                logger.debug(f"🌐 Website found for {title}: {website_url}")
            else:
                logger.debug(f"🌐 No website found for {title} - will trigger Google fallback")
            
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
            
            # ENHANCED: Extract email and website intelligently from LinkedIn URL and snippet
            extracted_email = self._extract_email_from_data(name, company, link, snippet)
            extracted_website = website_url or self._extract_website_from_data(company, link, snippet)
            extracted_business_type = self._infer_business_type_from_data(company, job_title, snippet)
            
            # Create enhanced lead object with more upfront data
            lead = {
                "name": name,
                "title": job_title or "Executive", 
                "company": company or "Unknown Company",
                "linkedin_url": link,
                "location": self.search_location,
                "email": extracted_email,  # ENHANCED: Smart email extraction
                "website": extracted_website,  # ENHANCED: Smart website extraction
                "business_type": extracted_business_type,  # ENHANCED: Business type inference
                "verified": False,
                "enriched": False,
                "scraped_at": datetime.now().isoformat(),
                "scraping_source": "serpapi_enhanced",
                "search_query": result.get('query', ''),
                "search_context": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                "status": "scraped_enhanced",
                "data_quality": "high"  # Mark as high quality since from real LinkedIn
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
    
    def _extract_website_from_serpapi_result(self, result: Dict) -> Optional[str]:
        """
        Extract website URL from SerpAPI search result.
        
        Args:
            result: SerpAPI search result dictionary
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            # Method 1: Check if SerpAPI response has a direct website field
            if 'website' in result:
                website = result['website']
                if website and self._is_valid_website_url(website):
                    logger.debug(f"✅ Found website in SerpAPI direct field: {website}")
                    return website
            
            # Method 2: Check for company website in rich snippets or structured data
            rich_snippet = result.get('rich_snippet', {})
            if rich_snippet:
                # Check top-level rich snippet data
                if 'top' in rich_snippet:
                    top_data = rich_snippet['top']
                    if isinstance(top_data, dict):
                        # Check detected extensions
                        if 'detected_extensions' in top_data:
                            extensions = top_data['detected_extensions']
                            if isinstance(extensions, dict) and 'website' in extensions:
                                website = extensions['website']
                                if self._is_valid_website_url(website):
                                    logger.debug(f"✅ Found website in rich snippet extensions: {website}")
                                    return website
                        
                        # Check for website in top data directly
                        if 'website' in top_data:
                            website = top_data['website']
                            if self._is_valid_website_url(website):
                                logger.debug(f"✅ Found website in rich snippet top: {website}")
                                return website
                
                # Check other rich snippet fields
                for field_name in ['extensions', 'menus', 'links']:
                    if field_name in rich_snippet:
                        field_data = rich_snippet[field_name]
                        if isinstance(field_data, list):
                            for item in field_data:
                                if isinstance(item, str) and self._is_valid_website_url(item):
                                    logger.debug(f"✅ Found website in rich snippet {field_name}: {item}")
                                    return item
            
            # Method 3: Check for sitelinks (common in company searches)
            sitelinks = result.get('sitelinks', [])
            if sitelinks and isinstance(sitelinks, list):
                for sitelink in sitelinks:
                    if isinstance(sitelink, dict) and 'link' in sitelink:
                        link = sitelink['link']
                        if self._is_valid_website_url(link) and 'linkedin.com' not in link:
                            logger.debug(f"✅ Found website in sitelinks: {link}")
                            return link
            
            # Method 4: Extract from displayed link (sometimes shows company domain)
            displayed_link = result.get('displayed_link', '')
            if displayed_link and self._is_valid_website_url(f"https://{displayed_link}"):
                # Clean up displayed link
                website = displayed_link
                if not website.startswith('http'):
                    website = f"https://{website}"
                if 'linkedin.com' not in website:
                    logger.debug(f"✅ Found website in displayed link: {website}")
                    return website
            
            # Method 5: Look for website mentions in the snippet text
            snippet = result.get('snippet', '')
            if snippet:
                website = self._extract_website_from_text(snippet)
                if website:
                    logger.debug(f"✅ Found website in snippet text: {website}")
                    return website
            
            # Method 6: Look for website in title (sometimes company websites are mentioned)
            title = result.get('title', '')
            if title:
                website = self._extract_website_from_text(title)
                if website:
                    logger.debug(f"✅ Found website in title: {website}")
                    return website
            
            # No website found - this will trigger fallback Google scraping
            logger.debug("⚠️ No website found in SerpAPI result - will trigger Google fallback")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting website from SerpAPI result: {str(e)}")
            return None
    
    def _extract_website_from_text(self, text: str) -> Optional[str]:
        """
        Extract website URL from text using pattern matching.
        
        Args:
            text: Text to search for website URLs
            
        Returns:
            Website URL if found, None otherwise
        """
        import re
        
        # Enhanced website patterns for better extraction
        patterns = [
            # Direct URL patterns
            r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # Context-based patterns
            r'Visit\s+(?:us\s+at\s+)?(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            r'Website:\s*(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            r'(?:at|@)\s+(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            r'(?:see|visit|check)\s+(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
            
            # Company domain patterns (more specific)
            r'([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))(?:\s|$|\.|\)|,)',
            
            # Email domain extraction (company.com from email@company.com)
            r'@([a-zA-Z0-9-]+\.(?:com|ca|org|net|co|io|ai|biz|info|tech|dev|app))',
        ]
        
        found_websites = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                website = match.strip().lower()
                
                # Skip common non-company domains
                skip_domains = [
                    'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
                    'youtube.com', 'google.com', 'gmail.com', 'outlook.com',
                    'yahoo.com', 'hotmail.com', 'example.com', 'test.com',
                    'domain.com', 'company.com', 'business.com', 'website.com'
                ]
                
                # Skip if it's a common non-company domain
                if any(skip_domain in website for skip_domain in skip_domains):
                    continue
                
                # Skip very short domains (likely false positives)
                domain_part = website.replace('www.', '').split('.')[0]
                if len(domain_part) < 3:
                    continue
                
                # Add protocol if missing
                if not website.startswith('http'):
                    website = f"https://{website}"
                
                # Validate and add to found websites
                if self._is_valid_website_url(website):
                    found_websites.append(website)
        
        # Return the first valid website found
        if found_websites:
            # Prefer .com domains over others
            com_domains = [w for w in found_websites if '.com' in w]
            if com_domains:
                return com_domains[0]
            else:
                return found_websites[0]
        
        return None
    
    def _is_valid_website_url(self, url: str) -> bool:
        """
        Validate if a URL looks like a valid website.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears valid
        """
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
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
    
    def _extract_email_from_data(self, name: str, company: str, linkedin_url: str, snippet: str) -> Optional[str]:
        """ENHANCED: Extract or intelligently generate email from available data"""
        try:
            # Method 1: Look for actual email in snippet (rare but possible)
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            found_emails = re.findall(email_pattern, snippet)
            if found_emails:
                return found_emails[0]  # Return first found email
            
            # Method 2: Smart generation from LinkedIn URL and company
            if name and company and company != "Unknown Company":
                # Clean name for email
                name_clean = re.sub(r'[^a-zA-Z\s]', '', name.lower())
                name_parts = name_clean.split()
                
                # Clean company for domain
                company_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
                
                if len(name_parts) >= 2 and len(company_clean) > 2:
                    # Generate professional email pattern
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    
                    # Try to infer domain from company name
                    possible_domains = [
                        f"{company_clean}.com",
                        f"{company_clean}.ca",  # Canadian companies
                        f"{company_clean}.org"
                    ]
                    
                    # Use most likely domain (.com for most businesses)
                    domain = possible_domains[0]
                    
                    return f"{first_name}.{last_name}@{domain}"
            
            return None
            
        except Exception as e:
            logger.debug(f"Email extraction failed: {e}")
            return None
    
    def _extract_website_from_data(self, company: str, linkedin_url: str, snippet: str) -> Optional[str]:
        """ENHANCED: Extract or intelligently generate website from available data"""
        try:
            # Method 1: Look for actual website URLs in snippet
            import re
            url_pattern = r'https?://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            found_urls = re.findall(url_pattern, snippet)
            
            # Filter out LinkedIn and social media URLs
            for url in found_urls:
                if not any(social in url.lower() for social in ['linkedin', 'facebook', 'twitter', 'instagram']):
                    return url
            
            # Method 2: Generate conservative website from company name
            if company and company != "Unknown Company" and len(company) > 3:
                company_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
                
                # Only generate if it looks like a real company (not generic)
                generic_terms = ['company', 'corp', 'inc', 'services', 'solutions', 'group']
                if not any(term in company_clean for term in generic_terms):
                    return f"https://{company_clean}.com"
            
            return None
            
        except Exception as e:
            logger.debug(f"Website extraction failed: {e}")
            return None
    
    def _infer_business_type_from_data(self, company: str, job_title: str, snippet: str) -> str:
        """ENHANCED: Infer business type from company and job title data"""
        try:
            # Analyze company name and job title for business type clues
            text_to_analyze = f"{company} {job_title} {snippet}".lower()
            
            # Technology companies
            if any(term in text_to_analyze for term in ['tech', 'software', 'digital', 'ai', 'data', 'cyber', 'cloud']):
                return "Technology"
            
            # Healthcare
            if any(term in text_to_analyze for term in ['health', 'medical', 'pharma', 'biotech', 'clinic']):
                return "Healthcare"
            
            # Finance
            if any(term in text_to_analyze for term in ['bank', 'finance', 'invest', 'capital', 'fund']):
                return "Finance"
            
            # Manufacturing
            if any(term in text_to_analyze for term in ['manufactur', 'industrial', 'factory', 'production']):
                return "Manufacturing"
            
            # Real Estate
            if any(term in text_to_analyze for term in ['real estate', 'property', 'construction', 'developer']):
                return "Real Estate"
            
            # Professional Services
            if any(term in text_to_analyze for term in ['consulting', 'legal', 'accounting', 'advisory']):
                return "Professional Services"
            
            # Default for executives
            if any(term in job_title.lower() for term in ['ceo', 'founder', 'president', 'owner']):
                return "Executive Leadership"
            
            return "Business Services"
            
        except Exception as e:
            logger.debug(f"Business type inference failed: {e}")
            return "Business Services"


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