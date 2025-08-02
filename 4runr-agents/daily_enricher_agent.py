#!/usr/bin/env python3
"""
Daily Enricher Agent - Anti-Detection Version
Runs daily to find leads missing emails in Airtable and enriches them
Uses advanced stealth techniques to avoid detection and blocking
"""

import os
import sys
import json
import time
import random
import logging
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
import dns.resolver
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from urllib.parse import quote
import hashlib

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('daily-enricher')

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for daily enricher")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

class StealthEnricherAgent:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / "shared"
        self.session = requests.Session()
        
        # Initialize encoding fixer
        try:
            from encoding_fixer import EncodingFixer
            self.encoding_fixer = EncodingFixer()
            logger.info("🔧 Encoding fixer initialized for enricher")
        except ImportError:
            logger.warning("⚠️ Encoding fixer not available")
            self.encoding_fixer = None
        
        # Anti-detection: Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
        ]
        
        # Anti-detection: Randomize headers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Anti-detection: Track request timing
        self.last_request_time = {}
        self.min_delay_between_domains = 5  # Minimum seconds between requests to same domain
        
        # Anti-detection: Proxy rotation (can be extended)
        self.proxies = []  # Add proxy list if needed
        
        logger.info("🥷 Stealth Enricher Agent initialized with anti-detection measures")
    
    def get_airtable_leads_missing_emails(self):
        """Get leads from Airtable that are missing emails"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
            
            encoded_table_name = quote(table_name)
            url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                # Filter leads missing emails
                missing_email_leads = []
                
                for record in records:
                    fields = record.get('fields', {})
                    email = fields.get('Email', '').strip()
                    name = fields.get('Full Name', '').strip()
                    company = fields.get('Company', '').strip()
                    
                    # Check if email is missing or empty
                    if not email and name and company:
                        missing_email_leads.append({
                            'record_id': record.get('id'),
                            'name': name,
                            'company': company,
                            'title': fields.get('Job Title', ''),
                            'linkedin_url': fields.get('LinkedIn URL', ''),
                            'needs_enrichment': fields.get('Needs Enrichment', True)
                        })
                
                logger.info(f"📋 Found {len(missing_email_leads)} leads missing emails")
                return missing_email_leads
            
            else:
                logger.error(f"❌ Failed to get Airtable records: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting Airtable leads: {str(e)}")
            return []
    
    def update_airtable_with_email(self, record_id, email_data):
        """Update Airtable record with found email"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
            
            encoded_table_name = quote(table_name)
            url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}/{record_id}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            update_data = {
                'fields': {
                    'Email': email_data['primary_email'],
                    'Needs Enrichment': False,
                    'Date Enriched': datetime.now().strftime('%Y-%m-%d'),
                    'Response Notes': f"Auto-enriched: {email_data.get('confidence', 'medium')} confidence | Methods: {', '.join(email_data.get('methods', []))}"
                }
            }
            
            response = requests.patch(url, headers=headers, json=update_data)
            
            if response.status_code == 200:
                logger.info(f"✅ Updated Airtable record with email: {email_data['primary_email']}")
                return True
            else:
                logger.error(f"❌ Failed to update Airtable: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating Airtable: {str(e)}")
            return False
    
    def get_stealth_headers(self, domain=None):
        """Generate randomized headers for stealth"""
        headers = self.base_headers.copy()
        
        # Randomize user agent
        headers['User-Agent'] = random.choice(self.user_agents)
        
        # Add domain-specific headers
        if domain:
            headers['Referer'] = f"https://www.google.com/search?q={domain}"
            
        # Randomize some header values
        if random.random() > 0.5:
            headers['DNT'] = '1'
        
        return headers
    
    def stealth_delay(self, domain):
        """Implement intelligent delays to avoid detection"""
        current_time = time.time()
        
        # Check last request time for this domain
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            
            if time_since_last < self.min_delay_between_domains:
                sleep_time = self.min_delay_between_domains - time_since_last
                # Add random jitter
                sleep_time += random.uniform(1, 3)
                logger.debug(f"⏱️ Stealth delay: {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        # Update last request time
        self.last_request_time[domain] = time.time()
        
        # Random additional delay
        if random.random() > 0.7:  # 30% chance
            extra_delay = random.uniform(2, 5)
            logger.debug(f"⏱️ Random extra delay: {extra_delay:.1f}s")
            time.sleep(extra_delay)
    
    def stealth_request(self, url, **kwargs):
        """Make a stealth HTTP request with anti-detection measures"""
        domain = urlparse(url).netloc
        
        # Apply stealth delay
        self.stealth_delay(domain)
        
        # Get stealth headers
        headers = self.get_stealth_headers(domain)
        kwargs['headers'] = headers
        
        # Set timeout
        kwargs.setdefault('timeout', 10)
        kwargs.setdefault('allow_redirects', True)
        
        try:
            response = self.session.get(url, **kwargs)
            
            # Log for monitoring
            logger.debug(f"🌐 Request to {domain}: {response.status_code}")
            
            return response
            
        except Exception as e:
            logger.warning(f"⚠️ Request failed for {url}: {str(e)}")
            return None
    
    def discover_company_domain_stealth(self, company_name):
        """Discover company domain with stealth techniques"""
        logger.info(f"🔍 Stealthily discovering domain for: {company_name}")
        
        # Method 1: Try common domain patterns first (no web requests)
        domain_patterns = self.generate_domain_patterns(company_name)
        
        for domain in domain_patterns[:5]:  # Limit to top 5 to reduce requests
            if self.verify_domain_exists_stealth(domain):
                logger.info(f"✅ Found domain via pattern: {domain}")
                return domain
        
        # Method 2: Use DuckDuckGo search with stealth
        search_domain = self.search_company_domain_stealth(company_name)
        if search_domain:
            return search_domain
        
        logger.warning(f"⚠️ Could not find domain for: {company_name}")
        return None
    
    def generate_domain_patterns(self, company_name):
        """Generate intelligent domain patterns"""
        clean_name = company_name.lower()
        clean_name = re.sub(r'[^a-z0-9\s]', '', clean_name)
        clean_name = clean_name.replace(' inc', '').replace(' corp', '').replace(' ltd', '')
        clean_name = clean_name.replace(' company', '').replace(' group', '').replace(' partners', '')
        clean_name = clean_name.replace(' consulting', '').replace(' consultants', '')
        
        words = [w for w in clean_name.split() if len(w) > 2]
        
        patterns = []
        
        if len(words) == 1:
            word = words[0]
            patterns.extend([
                f"{word}.com",
                f"{word}.ca",
                f"www.{word}.com"
            ])
        elif len(words) >= 2:
            word1, word2 = words[0], words[1]
            patterns.extend([
                f"{word1}{word2}.com",
                f"{word1}-{word2}.com",
                f"{word1}.com",
                f"{word1}{word2}.ca",
                f"{word1}-{word2}.ca"
            ])
        
        return patterns
    
    def verify_domain_exists_stealth(self, domain):
        """Verify domain exists with minimal footprint"""
        try:
            # Quick DNS check first (no HTTP request)
            dns.resolver.resolve(domain, 'A')
            
            # Then try HTTP with stealth
            response = self.stealth_request(f"https://{domain}")
            if response and response.status_code == 200:
                return True
                
            # Fallback to HTTP
            response = self.stealth_request(f"http://{domain}")
            if response and response.status_code == 200:
                return True
                
        except Exception:
            pass
        
        return False
    
    def search_company_domain_stealth(self, company_name):
        """Search for company domain using stealth techniques"""
        try:
            # Use DuckDuckGo (more privacy-friendly)
            query = f"{company_name} Montreal official website"
            search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            response = self.stealth_request(search_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract domains from search results
                links = soup.find_all('a', href=True)
                
                for link in links[:10]:  # Limit to first 10 results
                    href = link.get('href', '')
                    if 'http' in href:
                        domain = urlparse(href).netloc
                        if domain and self.is_company_domain(domain, company_name):
                            if self.verify_domain_exists_stealth(domain):
                                logger.info(f"🔍 Found domain via search: {domain}")
                                return domain
            
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}")
        
        return None
    
    def is_company_domain(self, domain, company_name):
        """Check if domain likely belongs to the company"""
        domain_lower = domain.lower().replace('www.', '')
        company_lower = company_name.lower()
        
        company_words = re.sub(r'[^a-z0-9\s]', '', company_lower).split()
        
        for word in company_words:
            if len(word) > 3 and word in domain_lower:
                return True
        
        return False
    
    def scrape_website_for_emails_stealth(self, domain, person_name):
        """Scrape website for emails with advanced stealth"""
        logger.info(f"🕷️ Stealthily scraping {domain} for emails...")
        
        found_emails = []
        
        # Pages to check (prioritized)
        pages_to_check = [
            '',  # Homepage
            '/contact',
            '/about',
            '/team'
        ]
        
        for i, page in enumerate(pages_to_check):
            try:
                url = f"https://{domain}{page}"
                response = self.stealth_request(url)
                
                if response and response.status_code == 200:
                    emails = self.extract_emails_from_content(response.text, person_name)
                    found_emails.extend(emails)
                    
                    # If we found emails, we can stop early
                    if found_emails:
                        break
                
                # Progressive delay increase
                time.sleep(2 + i)  # Increase delay with each page
                
            except Exception as e:
                logger.debug(f"Could not scrape {url}: {str(e)}")
                continue
        
        # Remove duplicates
        unique_emails = list(set(found_emails))
        
        if unique_emails:
            logger.info(f"📧 Found {len(unique_emails)} emails via stealth scraping")
        
        return unique_emails
    
    def extract_emails_from_content(self, content, person_name=None):
        """Extract emails from content with person name prioritization"""
        import re
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        valid_emails = []
        
        for email in emails:
            email_lower = email.lower()
            
            # Filter out common non-personal emails
            if any(skip in email_lower for skip in ['noreply', 'no-reply', 'donotreply', 'example.com']):
                continue
            
            # Prioritize emails that might match the person
            if person_name:
                name_parts = person_name.lower().split()
                for part in name_parts:
                    if len(part) > 2 and part in email_lower:
                        valid_emails.insert(0, email)  # Prioritize
                        break
                else:
                    valid_emails.append(email)
            else:
                valid_emails.append(email)
        
        return valid_emails
    
    def generate_email_patterns_smart(self, person_name, domain):
        """Generate smart email patterns with verification"""
        if not domain or not person_name:
            return []
        
        name_parts = person_name.lower().replace('.', '').replace('-', '').split()
        if len(name_parts) < 2:
            return []
        
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Generate patterns in order of likelihood
        patterns = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}"
        ]
        
        return patterns
    
    def verify_email_deliverability(self, email):
        """Verify email deliverability"""
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False
    
    def enrich_lead_stealth(self, lead):
        """Enrich a single lead with stealth techniques"""
        name = lead['name']
        company = lead['company']
        
        logger.info(f"🥷 Stealthily enriching: {name} at {company}")
        
        # Log production data - enrichment start
        enrichment_start_time = datetime.now()
        
        enriched_data = {
            'name': name,
            'company': company,
            'enriched_at': enrichment_start_time.isoformat(),
            'methods': ['stealth_system'],
            'cost': 0
        }
        
        # Step 1: Discover domain with stealth
        domain = self.discover_company_domain_stealth(company)
        if domain:
            enriched_data['company_website'] = domain
            enriched_data['methods'].append('stealth_domain_discovery')
            
            # Step 2: Scrape for emails with stealth
            found_emails = self.scrape_website_for_emails_stealth(domain, name)
            if found_emails:
                verified_emails = [e for e in found_emails if self.verify_email_deliverability(e)]
                
                if verified_emails:
                    enriched_data['found_emails'] = verified_emails
                    enriched_data['primary_email'] = verified_emails[0]
                    enriched_data['confidence'] = 'high'
                    enriched_data['methods'].append('stealth_website_scraping')
            
            # Step 3: Generate patterns if no emails found
            if 'primary_email' not in enriched_data:
                patterns = self.generate_email_patterns_smart(name, domain)
                verified_patterns = [p for p in patterns if self.verify_email_deliverability(p)]
                
                if verified_patterns:
                    enriched_data['email_patterns'] = verified_patterns
                    enriched_data['primary_email'] = verified_patterns[0]
                    enriched_data['confidence'] = 'medium'
                    enriched_data['methods'].append('stealth_pattern_generation')
        
        # Log production data - enrichment complete
        if PRODUCTION_LOGGING_ENABLED:
            try:
                enrichment_reasoning = {
                    "domain_discovery": f"Found domain: {enriched_data.get('company_website', 'None')}",
                    "email_methods": enriched_data.get('methods', []),
                    "confidence_level": enriched_data.get('confidence', 'none'),
                    "enrichment_duration": (datetime.now() - enrichment_start_time).total_seconds(),
                    "success": 'primary_email' in enriched_data
                }
                
                log_production_event(
                    "enrichment",
                    lead,
                    enriched_data,
                    {"reasoning": enrichment_reasoning}
                )
            except Exception as e:
                logger.warning(f"⚠️ Production logging failed: {e}")
        
        return enriched_data
    
    def run_daily_enrichment(self):
        """Run the daily enrichment process"""
        logger.info("🚀 Starting daily stealth enrichment process...")
        
        # Get leads missing emails from Airtable
        leads_to_enrich = self.get_airtable_leads_missing_emails()
        
        if not leads_to_enrich:
            logger.info("✅ No leads need enrichment today")
            return
        
        logger.info(f"📋 Found {len(leads_to_enrich)} leads to enrich")
        
        enriched_count = 0
        
        for i, lead in enumerate(leads_to_enrich, 1):
            logger.info(f"🔄 Processing lead {i}/{len(leads_to_enrich)}: {lead['name']}")
            
            try:
                # Enrich the lead
                enriched_data = self.enrich_lead_stealth(lead)
                
                # Update Airtable if we found an email
                if enriched_data.get('primary_email'):
                    success = self.update_airtable_with_email(lead['record_id'], enriched_data)
                    if success:
                        enriched_count += 1
                        logger.info(f"✅ Successfully enriched: {lead['name']}")
                    else:
                        logger.warning(f"⚠️ Failed to update Airtable for: {lead['name']}")
                else:
                    logger.info(f"📭 No email found for: {lead['name']}")
                
                # Anti-detection: Random delay between leads
                if i < len(leads_to_enrich):  # Don't delay after last lead
                    delay = random.uniform(10, 20)  # 10-20 seconds between leads
                    logger.info(f"⏱️ Anti-detection delay: {delay:.1f}s")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Error enriching {lead['name']}: {str(e)}")
                continue
        
        # Summary
        logger.info(f"🎯 Daily enrichment complete: {enriched_count}/{len(leads_to_enrich)} leads enriched")
        
        # Save daily report
        self.save_daily_report(leads_to_enrich, enriched_count)
    
    def save_daily_report(self, leads_processed, enriched_count):
        """Save daily enrichment report"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'leads_processed': len(leads_processed),
            'leads_enriched': enriched_count,
            'success_rate': f"{(enriched_count/len(leads_processed)*100):.1f}%" if leads_processed else "0%",
            'cost': 0,
            'method': 'stealth_custom_system'
        }
        
        # Save to daily reports file
        reports_file = self.shared_dir / "daily_enrichment_reports.json"
        
        if reports_file.exists():
            with open(reports_file, 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append(report)
        
        with open(reports_file, 'w') as f:
            json.dump(reports, f, indent=2)
        
        logger.info(f"📊 Daily report saved: {enriched_count} leads enriched at $0 cost")

def main():
    """Main function for daily enrichment"""
    logger.info("🥷 Starting Daily Stealth Enricher Agent...")
    
    agent = StealthEnricherAgent()
    agent.run_daily_enrichment()
    
    logger.info("✅ Daily enrichment process completed")

if __name__ == "__main__":
    main()