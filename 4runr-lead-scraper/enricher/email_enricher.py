#!/usr/bin/env python3
"""
Email Enricher

Consolidated email enrichment system for finding and validating email addresses.
Uses web scraping, pattern generation, and email verification.
"""

import os
import re
import time
import random
import logging
import requests
import dns.resolver
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger('email-enricher')

class EmailEnricher:
    """
    Email enrichment system using web scraping and pattern generation.
    Includes anti-detection measures and email verification.
    """
    
    def __init__(self):
        """Initialize the email enricher."""
        self.session = requests.Session()
        
        # Anti-detection: Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
        ]
        
        # Base headers for requests
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay_between_domains = 3  # Minimum seconds between requests to same domain
        
        # Configuration from environment
        self.max_email_attempts = int(os.getenv('MAX_EMAIL_ATTEMPTS', '2'))
        self.max_website_attempts = int(os.getenv('MAX_WEBSITE_ATTEMPTS', '2'))
        self.enrichment_timeout = int(os.getenv('ENRICHMENT_TIMEOUT_SECONDS', '30'))
        self.use_pattern_emails = os.getenv('USE_PATTERN_EMAILS', 'true').lower() == 'true'
        
        logger.info("📧 Email Enricher initialized")
        logger.info(f"⚙️ Max email attempts: {self.max_email_attempts}")
        logger.info(f"⚙️ Max website attempts: {self.max_website_attempts}")
        logger.info(f"⚙️ Use pattern emails: {self.use_pattern_emails}")
    
    def enrich_lead_email(self, lead: Dict) -> Dict:
        """
        Enrich a lead with email information.
        
        Args:
            lead: Lead dictionary with name, company, etc.
            
        Returns:
            Dictionary with enrichment results
        """
        name = lead.get('name', '')
        company = lead.get('company', '')
        
        logger.info(f"📧 Enriching email for: {name} at {company}")
        
        enrichment_result = {
            'success': False,
            'email': None,
            'confidence': 'none',
            'method': None,
            'found_emails': [],
            'attempts': 0,
            'enriched_at': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            # Step 1: Discover company domain
            domain = self._discover_company_domain(company)
            if not domain:
                enrichment_result['error'] = 'Could not discover company domain'
                return enrichment_result
            
            enrichment_result['company_website'] = domain
            
            # Step 2: Scrape website for emails
            found_emails = self._scrape_website_for_emails(domain, name)
            enrichment_result['found_emails'] = found_emails
            enrichment_result['attempts'] += 1
            
            if found_emails:
                # Verify emails
                verified_emails = []
                for email in found_emails:
                    if self._verify_email_deliverability(email):
                        verified_emails.append(email)
                
                if verified_emails:
                    enrichment_result['success'] = True
                    enrichment_result['email'] = verified_emails[0]
                    enrichment_result['confidence'] = 'high'
                    enrichment_result['method'] = 'website_scraping'
                    return enrichment_result
            
            # Step 3: Generate email patterns if enabled
            if self.use_pattern_emails and enrichment_result['attempts'] < self.max_email_attempts:
                patterns = self._generate_email_patterns(name, domain)
                enrichment_result['attempts'] += 1
                
                verified_patterns = []
                for pattern in patterns:
                    if self._verify_email_deliverability(pattern):
                        verified_patterns.append(pattern)
                
                if verified_patterns:
                    enrichment_result['success'] = True
                    enrichment_result['email'] = verified_patterns[0]
                    enrichment_result['confidence'] = 'medium'
                    enrichment_result['method'] = 'pattern_generation'
                    enrichment_result['found_emails'].extend(verified_patterns)
                    return enrichment_result
            
            # No email found
            enrichment_result['error'] = 'No valid email found'
            return enrichment_result
            
        except Exception as e:
            logger.error(f"❌ Email enrichment failed for {name}: {str(e)}")
            enrichment_result['error'] = str(e)
            return enrichment_result
    
    def _discover_company_domain(self, company: str) -> Optional[str]:
        """
        Discover company domain through search.
        
        Args:
            company: Company name
            
        Returns:
            Domain string or None
        """
        try:
            # Clean company name
            clean_company = re.sub(r'\b(inc|corp|ltd|llc|company|co)\b', '', company.lower()).strip()
            
            # Try common patterns first
            potential_domains = [
                f"{clean_company.replace(' ', '')}.com",
                f"{clean_company.replace(' ', '')}.ca",
                f"{clean_company.replace(' ', '-')}.com",
                f"{clean_company.replace(' ', '-')}.ca"
            ]
            
            for domain in potential_domains:
                if self._test_domain_exists(domain):
                    logger.info(f"🌐 Found domain: {domain}")
                    return domain
            
            # If no direct match, try web search (simplified)
            search_domain = self._search_company_domain(company)
            if search_domain:
                return search_domain
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Domain discovery failed for {company}: {str(e)}")
            return None
    
    def _test_domain_exists(self, domain: str) -> bool:
        """Test if a domain exists and is accessible."""
        try:
            # Add rate limiting
            self._apply_rate_limiting(domain)
            
            headers = self.base_headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            response = self.session.head(
                f"https://{domain}",
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            
            return response.status_code < 400
            
        except Exception:
            return False
    
    def _search_company_domain(self, company: str) -> Optional[str]:
        """
        Search for company domain using web search.
        
        Args:
            company: Company name
            
        Returns:
            Domain string or None
        """
        try:
            # Simple search approach - look for company website
            search_query = f"{company} official website"
            
            # This is a simplified implementation
            # In production, you might use a search API or more sophisticated methods
            
            return None  # Placeholder - implement based on your search strategy
            
        except Exception as e:
            logger.warning(f"⚠️ Company domain search failed: {str(e)}")
            return None
    
    def _scrape_website_for_emails(self, domain: str, name: str) -> List[str]:
        """
        Scrape website for email addresses.
        
        Args:
            domain: Company domain
            name: Person's name to look for
            
        Returns:
            List of found email addresses
        """
        found_emails = []
        
        try:
            # Pages to check
            pages_to_check = [
                f"https://{domain}",
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}/team",
                f"https://{domain}/staff"
            ]
            
            name_parts = name.lower().split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            for page_url in pages_to_check:
                try:
                    # Rate limiting
                    self._apply_rate_limiting(domain)
                    
                    headers = self.base_headers.copy()
                    headers['User-Agent'] = random.choice(self.user_agents)
                    
                    response = self.session.get(
                        page_url,
                        headers=headers,
                        timeout=self.enrichment_timeout,
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        # Parse HTML
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text_content = soup.get_text().lower()
                        
                        # Find email addresses
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, response.text, re.IGNORECASE)
                        
                        for email in emails:
                            email = email.lower()
                            
                            # Filter relevant emails
                            if (domain.replace('www.', '') in email and 
                                not any(skip in email for skip in ['noreply', 'no-reply', 'info@', 'contact@', 'support@'])):
                                
                                # Check if email might belong to the person
                                if (first_name in email or last_name in email or
                                    any(part in email for part in name_parts if len(part) > 2)):
                                    found_emails.append(email)
                                    logger.info(f"📧 Found potential email: {email}")
                
                except Exception as e:
                    logger.debug(f"⚠️ Failed to scrape {page_url}: {str(e)}")
                    continue
            
            # Remove duplicates
            found_emails = list(set(found_emails))
            
            logger.info(f"📧 Found {len(found_emails)} potential emails for {name}")
            return found_emails
            
        except Exception as e:
            logger.error(f"❌ Website scraping failed: {str(e)}")
            return []
    
    def _generate_email_patterns(self, name: str, domain: str) -> List[str]:
        """
        Generate common email patterns for a person.
        
        Args:
            name: Person's name
            domain: Company domain
            
        Returns:
            List of email patterns
        """
        patterns = []
        
        try:
            name_parts = name.lower().split()
            if not name_parts:
                return patterns
            
            first_name = name_parts[0]
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            # Clean domain
            clean_domain = domain.replace('www.', '')
            
            # Common patterns
            if last_name:
                patterns.extend([
                    f"{first_name}.{last_name}@{clean_domain}",
                    f"{first_name}_{last_name}@{clean_domain}",
                    f"{first_name}{last_name}@{clean_domain}",
                    f"{first_name[0]}{last_name}@{clean_domain}",
                    f"{first_name}.{last_name[0]}@{clean_domain}",
                    f"{last_name}.{first_name}@{clean_domain}",
                    f"{last_name}@{clean_domain}"
                ])
            else:
                patterns.extend([
                    f"{first_name}@{clean_domain}",
                    f"{first_name}.admin@{clean_domain}"
                ])
            
            logger.info(f"📧 Generated {len(patterns)} email patterns for {name}")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Pattern generation failed: {str(e)}")
            return []
    
    def _verify_email_deliverability(self, email: str) -> bool:
        """
        Verify if an email address is deliverable.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if email appears deliverable
        """
        try:
            # Basic format validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return False
            
            # Extract domain
            domain = email.split('@')[1]
            
            # Check MX record
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if not mx_records:
                    return False
            except Exception:
                return False
            
            # Additional checks could be added here
            # (SMTP verification, etc.)
            
            return True
            
        except Exception as e:
            logger.debug(f"⚠️ Email verification failed for {email}: {str(e)}")
            return False
    
    def _apply_rate_limiting(self, domain: str):
        """Apply rate limiting for domain requests."""
        now = time.time()
        
        if domain in self.last_request_time:
            time_since_last = now - self.last_request_time[domain]
            if time_since_last < self.min_delay_between_domains:
                sleep_time = self.min_delay_between_domains - time_since_last
                logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def batch_enrich_emails(self, leads: List[Dict], max_leads: int = None) -> List[Dict]:
        """
        Enrich multiple leads with email information.
        
        Args:
            leads: List of lead dictionaries
            max_leads: Maximum number of leads to process
            
        Returns:
            List of enrichment results
        """
        if max_leads:
            leads = leads[:max_leads]
        
        logger.info(f"📧 Starting batch email enrichment for {len(leads)} leads")
        
        results = []
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"📧 Processing lead {i}/{len(leads)}: {lead.get('name', 'Unknown')}")
            
            try:
                result = self.enrich_lead_email(lead)
                result['lead_id'] = lead.get('id')
                results.append(result)
                
                # Anti-detection delay between leads
                if i < len(leads):
                    delay = random.uniform(5, 10)
                    logger.debug(f"⏱️ Anti-detection delay: {delay:.1f}s")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Batch enrichment failed for lead {i}: {str(e)}")
                results.append({
                    'lead_id': lead.get('id'),
                    'success': False,
                    'error': str(e),
                    'enriched_at': datetime.now().isoformat()
                })
        
        successful = sum(1 for r in results if r.get('success'))
        logger.info(f"✅ Batch email enrichment completed: {successful}/{len(results)} successful")
        
        return results


# Convenience function
def enrich_lead_email(lead: Dict) -> Dict:
    """
    Enrich a single lead with email (convenience function).
    
    Args:
        lead: Lead dictionary
        
    Returns:
        Enrichment result dictionary
    """
    enricher = EmailEnricher()
    return enricher.enrich_lead_email(lead)


if __name__ == "__main__":
    # Test the email enricher
    enricher = EmailEnricher()
    
    print("🧪 Testing Email Enricher...")
    
    # Test lead
    test_lead = {
        'name': 'John Smith',
        'company': 'Test Company Inc',
        'id': 'test_123'
    }
    
    result = enricher.enrich_lead_email(test_lead)
    print(f"Enrichment result: {result}")
    
    print("✅ Email enricher test completed")