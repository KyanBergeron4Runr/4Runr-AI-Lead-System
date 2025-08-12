#!/usr/bin/env python3
"""
Profile Enricher

Additional lead data enrichment for company information, social profiles,
and other relevant business data.
"""

import os
import re
import time
import random
import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger('profile-enricher')

class ProfileEnricher:
    """
    Profile enrichment system for gathering additional lead and company data.
    """
    
    def __init__(self):
        """Initialize the profile enricher."""
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
        self.last_request_time = {}
        self.min_delay = 2
        
        # Configuration
        self.enrichment_timeout = int(os.getenv('ENRICHMENT_TIMEOUT_SECONDS', '30'))
        
        logger.info("👤 Profile Enricher initialized")
    
    def enrich_lead_profile(self, lead: Dict) -> Dict:
        """
        Enrich a lead with additional profile and company data.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Dictionary with enrichment results
        """
        name = lead.get('name', '')
        company = lead.get('company', '')
        linkedin_url = lead.get('linkedin_url', '')
        
        logger.info(f"👤 Enriching profile for: {name} at {company}")
        
        enrichment_result = {
            'success': False,
            'company_data': {},
            'profile_data': {},
            'social_profiles': {},
            'enriched_at': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            # Enrich company data
            if company:
                company_data = self._enrich_company_data(company, lead.get('company_website'))
                enrichment_result['company_data'] = company_data
            
            # Enrich profile data from LinkedIn
            if linkedin_url:
                profile_data = self._enrich_linkedin_profile(linkedin_url, name)
                enrichment_result['profile_data'] = profile_data
            
            # Find additional social profiles
            social_profiles = self._find_social_profiles(name, company)
            enrichment_result['social_profiles'] = social_profiles
            
            # Determine success
            has_data = (
                bool(enrichment_result['company_data']) or
                bool(enrichment_result['profile_data']) or
                bool(enrichment_result['social_profiles'])
            )
            
            enrichment_result['success'] = has_data
            
            if has_data:
                logger.info(f"✅ Profile enrichment successful for {name}")
            else:
                enrichment_result['error'] = 'No additional profile data found'
                logger.info(f"📭 No additional profile data found for {name}")
            
            return enrichment_result
            
        except Exception as e:
            logger.error(f"❌ Profile enrichment failed for {name}: {str(e)}")
            enrichment_result['error'] = str(e)
            return enrichment_result
    
    def _enrich_company_data(self, company: str, company_website: str = None) -> Dict:
        """
        Enrich company data from website and other sources.
        
        Args:
            company: Company name
            company_website: Optional company website URL
            
        Returns:
            Dictionary with company data
        """
        company_data = {}
        
        try:
            # If no website provided, try to find it
            if not company_website:
                company_website = self._find_company_website(company)
            
            if company_website:
                # Scrape company website
                website_data = self._scrape_company_website(company_website)
                company_data.update(website_data)
                
                # Estimate company size
                company_size = self._estimate_company_size(website_data)
                if company_size:
                    company_data['estimated_size'] = company_size
                
                # Determine industry
                industry = self._determine_industry(website_data, company)
                if industry:
                    company_data['industry'] = industry
            
            logger.info(f"🏢 Enriched company data for {company}: {len(company_data)} fields")
            return company_data
            
        except Exception as e:
            logger.warning(f"⚠️ Company data enrichment failed for {company}: {str(e)}")
            return {}
    
    def _find_company_website(self, company: str) -> Optional[str]:
        """Find company website URL."""
        try:
            # Clean company name
            clean_company = re.sub(r'\b(inc|corp|ltd|llc|company|co)\b', '', company.lower()).strip()
            
            # Try common domain patterns
            potential_domains = [
                f"{clean_company.replace(' ', '')}.com",
                f"{clean_company.replace(' ', '')}.ca",
                f"{clean_company.replace(' ', '-')}.com",
                f"{clean_company.replace(' ', '-')}.ca"
            ]
            
            for domain in potential_domains:
                if self._test_website_accessible(f"https://{domain}"):
                    logger.info(f"🌐 Found company website: {domain}")
                    return f"https://{domain}"
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Website finding failed for {company}: {str(e)}")
            return None
    
    def _test_website_accessible(self, url: str) -> bool:
        """Test if a website is accessible."""
        try:
            self._apply_rate_limiting(url)
            
            headers = self.base_headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            response = self.session.head(url, headers=headers, timeout=10, allow_redirects=True)
            return response.status_code < 400
            
        except Exception:
            return False
    
    def _scrape_company_website(self, website_url: str) -> Dict:
        """
        Scrape company website for relevant information.
        
        Args:
            website_url: Company website URL
            
        Returns:
            Dictionary with scraped data
        """
        website_data = {}
        
        try:
            self._apply_rate_limiting(website_url)
            
            headers = self.base_headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            response = self.session.get(
                website_url,
                headers=headers,
                timeout=self.enrichment_timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic information
                website_data['website_url'] = website_url
                
                # Get page title
                title = soup.find('title')
                if title:
                    website_data['page_title'] = title.get_text().strip()
                
                # Get meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    website_data['description'] = meta_desc.get('content', '').strip()
                
                # Extract text content for analysis
                text_content = soup.get_text()
                website_data['content_length'] = len(text_content)
                
                # Look for specific business information
                business_info = self._extract_business_info(soup, text_content)
                website_data.update(business_info)
                
                # Look for contact information
                contact_info = self._extract_contact_info(soup, text_content)
                website_data.update(contact_info)
                
                logger.info(f"🌐 Scraped website data: {len(website_data)} fields")
            
            return website_data
            
        except Exception as e:
            logger.warning(f"⚠️ Website scraping failed for {website_url}: {str(e)}")
            return {}
    
    def _extract_business_info(self, soup: BeautifulSoup, text_content: str) -> Dict:
        """Extract business information from website content."""
        business_info = {}
        
        try:
            text_lower = text_content.lower()
            
            # Look for services/products
            service_keywords = [
                'services', 'solutions', 'products', 'offerings',
                'consulting', 'development', 'design', 'marketing'
            ]
            
            found_services = []
            for keyword in service_keywords:
                if keyword in text_lower:
                    # Extract context around the keyword
                    pattern = rf'.{{0,50}}{keyword}.{{0,50}}'
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        found_services.extend(matches[:2])  # Limit to 2 matches per keyword
            
            if found_services:
                business_info['services_mentioned'] = found_services[:5]  # Top 5
            
            # Look for company size indicators
            size_indicators = [
                'employees', 'team members', 'staff', 'founded',
                'established', 'years of experience'
            ]
            
            for indicator in size_indicators:
                if indicator in text_lower:
                    # Try to extract numbers near these indicators
                    pattern = rf'\d+\s*{indicator}|\b{indicator}\s*\d+'
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        business_info[f'{indicator}_mentions'] = matches[:2]
            
            return business_info
            
        except Exception as e:
            logger.debug(f"⚠️ Business info extraction failed: {str(e)}")
            return {}
    
    def _extract_contact_info(self, soup: BeautifulSoup, text_content: str) -> Dict:
        """Extract contact information from website."""
        contact_info = {}
        
        try:
            # Look for phone numbers
            phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
            phones = re.findall(phone_pattern, text_content)
            if phones:
                contact_info['phone_numbers'] = list(set(phones[:3]))  # Unique, max 3
            
            # Look for addresses
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)',
                r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'  # City, State ZIP
            ]
            
            addresses = []
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                addresses.extend(matches)
            
            if addresses:
                contact_info['addresses'] = list(set(addresses[:2]))  # Unique, max 2
            
            return contact_info
            
        except Exception as e:
            logger.debug(f"⚠️ Contact info extraction failed: {str(e)}")
            return {}
    
    def _estimate_company_size(self, website_data: Dict) -> Optional[str]:
        """Estimate company size based on website data."""
        try:
            content_length = website_data.get('content_length', 0)
            services_count = len(website_data.get('services_mentioned', []))
            
            # Simple heuristic based on website complexity
            if content_length > 50000 or services_count > 10:
                return 'Large (50+ employees)'
            elif content_length > 20000 or services_count > 5:
                return 'Medium (10-50 employees)'
            else:
                return 'Small (1-10 employees)'
                
        except Exception:
            return None
    
    def _determine_industry(self, website_data: Dict, company_name: str) -> Optional[str]:
        """Determine company industry based on available data."""
        try:
            # Combine text sources
            text_sources = [
                website_data.get('description', ''),
                website_data.get('page_title', ''),
                company_name,
                ' '.join(website_data.get('services_mentioned', []))
            ]
            
            combined_text = ' '.join(text_sources).lower()
            
            # Industry keywords mapping
            industry_keywords = {
                'Technology': ['software', 'tech', 'development', 'programming', 'digital', 'app', 'platform'],
                'Consulting': ['consulting', 'advisory', 'strategy', 'management', 'business'],
                'Marketing': ['marketing', 'advertising', 'branding', 'social media', 'seo'],
                'Healthcare': ['health', 'medical', 'healthcare', 'clinic', 'hospital'],
                'Finance': ['finance', 'financial', 'banking', 'investment', 'accounting'],
                'Real Estate': ['real estate', 'property', 'realty', 'housing'],
                'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial'],
                'Retail': ['retail', 'store', 'shop', 'e-commerce', 'sales']
            }
            
            # Score each industry
            industry_scores = {}
            for industry, keywords in industry_keywords.items():
                score = sum(1 for keyword in keywords if keyword in combined_text)
                if score > 0:
                    industry_scores[industry] = score
            
            # Return highest scoring industry
            if industry_scores:
                return max(industry_scores, key=industry_scores.get)
            
            return None
            
        except Exception:
            return None
    
    def _enrich_linkedin_profile(self, linkedin_url: str, name: str) -> Dict:
        """
        Enrich data from LinkedIn profile (limited due to LinkedIn's restrictions).
        
        Args:
            linkedin_url: LinkedIn profile URL
            name: Person's name
            
        Returns:
            Dictionary with profile data
        """
        profile_data = {}
        
        try:
            # Basic validation and cleanup of LinkedIn URL
            if 'linkedin.com/in/' in linkedin_url:
                profile_data['linkedin_url'] = linkedin_url
                profile_data['profile_verified'] = True
                
                # Extract username from URL
                username_match = re.search(r'linkedin\.com/in/([^/?]+)', linkedin_url)
                if username_match:
                    profile_data['linkedin_username'] = username_match.group(1)
                
                logger.info(f"🔗 LinkedIn profile validated for {name}")
            
            return profile_data
            
        except Exception as e:
            logger.debug(f"⚠️ LinkedIn profile enrichment failed: {str(e)}")
            return {}
    
    def _find_social_profiles(self, name: str, company: str) -> Dict:
        """
        Find additional social media profiles.
        
        Args:
            name: Person's name
            company: Company name
            
        Returns:
            Dictionary with social profiles
        """
        social_profiles = {}
        
        try:
            # This is a placeholder for social profile discovery
            # In a full implementation, you might search for:
            # - Twitter profiles
            # - Company social media accounts
            # - Professional associations
            # - Speaking engagements
            
            # For now, just return empty dict
            # Real implementation would require careful consideration of privacy and ToS
            
            return social_profiles
            
        except Exception as e:
            logger.debug(f"⚠️ Social profile search failed: {str(e)}")
            return {}
    
    def _apply_rate_limiting(self, url: str):
        """Apply rate limiting for requests."""
        domain = urlparse(url).netloc
        now = time.time()
        
        if domain in self.last_request_time:
            time_since_last = now - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def batch_enrich_profiles(self, leads: List[Dict], max_leads: int = None) -> List[Dict]:
        """
        Enrich multiple leads with profile data.
        
        Args:
            leads: List of lead dictionaries
            max_leads: Maximum number of leads to process
            
        Returns:
            List of enrichment results
        """
        if max_leads:
            leads = leads[:max_leads]
        
        logger.info(f"👤 Starting batch profile enrichment for {len(leads)} leads")
        
        results = []
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"👤 Processing lead {i}/{len(leads)}: {lead.get('name', 'Unknown')}")
            
            try:
                result = self.enrich_lead_profile(lead)
                result['lead_id'] = lead.get('id')
                results.append(result)
                
                # Rate limiting between leads
                if i < len(leads):
                    delay = random.uniform(3, 6)
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Batch profile enrichment failed for lead {i}: {str(e)}")
                results.append({
                    'lead_id': lead.get('id'),
                    'success': False,
                    'error': str(e),
                    'enriched_at': datetime.now().isoformat()
                })
        
        successful = sum(1 for r in results if r.get('success'))
        logger.info(f"✅ Batch profile enrichment completed: {successful}/{len(results)} successful")
        
        return results


# Convenience function
def enrich_lead_profile(lead: Dict) -> Dict:
    """
    Enrich a single lead with profile data (convenience function).
    
    Args:
        lead: Lead dictionary
        
    Returns:
        Enrichment result dictionary
    """
    enricher = ProfileEnricher()
    return enricher.enrich_lead_profile(lead)


if __name__ == "__main__":
    # Test the profile enricher
    enricher = ProfileEnricher()
    
    print("🧪 Testing Profile Enricher...")
    
    # Test lead
    test_lead = {
        'name': 'John Smith',
        'company': 'Test Company Inc',
        'linkedin_url': 'https://linkedin.com/in/johnsmith',
        'id': 'test_123'
    }
    
    result = enricher.enrich_lead_profile(test_lead)
    print(f"Profile enrichment result: {result}")
    
    print("✅ Profile enricher test completed")