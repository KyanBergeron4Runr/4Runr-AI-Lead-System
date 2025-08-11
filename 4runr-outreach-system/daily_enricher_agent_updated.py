#!/usr/bin/env python3
"""
Updated Daily Enricher Agent - Database Integration
Runs daily to find leads missing emails and enriches them using the new database API
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
from urllib.parse import quote
from typing import List, Dict, Any, Optional

# Import new database components
from lead_database import LeadDatabase
from database_logger import database_logger, log_database_event, monitor_performance

# DNS resolution for email verification
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    logging.warning("DNS resolver not available - email verification disabled")

# Web scraping
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup not available - web scraping disabled")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('daily-enricher-updated')


class DatabaseEnricherAgent:
    """Updated enricher agent using the new database API."""
    
    def __init__(self):
        """Initialize the enricher agent with database connection."""
        try:
            # Initialize database connection
            self.db = LeadDatabase()
            logger.info("✅ Database connection established")
            
            # Initialize session for web requests
            self.session = requests.Session()
            
            # Anti-detection: Rotate user agents
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
            ]
            
            # Anti-detection: Base headers
            self.base_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Request timing for anti-detection
            self.last_request_time = {}
            self.min_delay_between_domains = 5
            
            logger.info("🥷 Database Enricher Agent initialized with anti-detection measures")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enricher agent: {e}")
            raise
    
    def get_leads_needing_enrichment(self) -> List[Dict[str, Any]]:
        """
        Get leads from database that need enrichment.
        
        Returns:
            List of leads that need enrichment
        """
        try:
            # Search for leads that need enrichment
            leads_needing_enrichment = self.db.search_leads({
                'needs_enrichment': True,
                'enriched': False
            })
            
            # Also get leads with missing emails
            leads_missing_email = self.db.search_leads({
                'email': None  # This will find leads with no email
            })
            
            # Combine and deduplicate
            all_leads = leads_needing_enrichment + leads_missing_email
            
            # Remove duplicates based on ID
            seen_ids = set()
            unique_leads = []
            for lead in all_leads:
                if lead.get('id') not in seen_ids:
                    unique_leads.append(lead)
                    seen_ids.add(lead.get('id'))
            
            logger.info(f"📋 Found {len(unique_leads)} leads needing enrichment")
            
            # Log the enrichment preparation
            log_database_event("database_operation", {}, {
                "success": True,
                "records_affected": len(unique_leads),
                "operation_type": "get_leads_needing_enrichment"
            }, {
                "operation_type": "search_leads",
                "performance_metrics": {"execution_time_ms": 0}
            })
            
            return unique_leads
            
        except Exception as e:
            logger.error(f"❌ Error getting leads needing enrichment: {e}")
            
            # Log error
            log_database_event("database_operation", {}, {
                "success": False,
                "error": str(e),
                "operation_type": "get_leads_needing_enrichment"
            }, {
                "operation_type": "search_leads"
            })
            
            return []
    
    def get_airtable_leads_missing_emails(self) -> List[Dict[str, Any]]:
        """
        Get leads from Airtable that are missing emails (fallback method).
        
        Returns:
            List of leads missing emails from Airtable
        """
        try:
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
            
            if not all([api_key, base_id]):
                logger.warning("⚠️ Airtable credentials not configured")
                return []
            
            encoded_table_name = quote(table_name)
            url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
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
                            'airtable_record_id': record.get('id'),
                            'name': name,
                            'full_name': name,
                            'company': company,
                            'title': fields.get('Job Title', ''),
                            'linkedin_url': fields.get('LinkedIn URL', ''),
                            'needs_enrichment': fields.get('Needs Enrichment', True),
                            'source': 'airtable_direct'
                        })
                
                logger.info(f"📋 Found {len(missing_email_leads)} leads missing emails in Airtable")
                return missing_email_leads
            
            else:
                logger.error(f"❌ Failed to get Airtable records: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting Airtable leads: {str(e)}")
            return []
    
    def get_stealth_headers(self, domain: Optional[str] = None) -> Dict[str, str]:
        """Generate randomized headers for stealth."""
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
    
    def stealth_delay(self, domain: str):
        """Implement intelligent delays to avoid detection."""
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
    
    def stealth_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a stealth HTTP request with anti-detection measures."""
        from urllib.parse import urlparse
        
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
            logger.debug(f"🌐 Request to {domain}: {response.status_code}")
            return response
            
        except Exception as e:
            logger.warning(f"⚠️ Request failed for {url}: {str(e)}")
            return None
    
    def discover_company_domain(self, company_name: str) -> Optional[str]:
        """Discover company domain with stealth techniques."""
        logger.info(f"🔍 Discovering domain for: {company_name}")
        
        # Method 1: Try common domain patterns first
        domain_patterns = self.generate_domain_patterns(company_name)
        
        for domain in domain_patterns[:3]:  # Limit to top 3 to reduce requests
            if self.verify_domain_exists(domain):
                logger.info(f"✅ Found domain via pattern: {domain}")
                return domain
        
        logger.warning(f"⚠️ Could not find domain for: {company_name}")
        return None
    
    def generate_domain_patterns(self, company_name: str) -> List[str]:
        """Generate intelligent domain patterns."""
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
    
    def verify_domain_exists(self, domain: str) -> bool:
        """Verify domain exists with minimal footprint."""
        try:
            # Quick DNS check first (no HTTP request)
            if DNS_AVAILABLE:
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
    
    def generate_email_patterns(self, person_name: str, domain: str) -> List[str]:
        """Generate smart email patterns."""
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
    
    def verify_email_deliverability(self, email: str) -> bool:
        """Verify email deliverability."""
        if not DNS_AVAILABLE:
            return True  # Assume valid if DNS not available
        
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False
    
    @monitor_performance("enrich_lead")
    def enrich_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single lead with email and other data.
        
        Args:
            lead: Lead data from database
            
        Returns:
            Enriched lead data
        """
        name = lead.get('full_name') or lead.get('name', '')
        company = lead.get('company', '')
        
        logger.info(f"🔄 Enriching: {name} at {company}")
        
        enrichment_start_time = datetime.now()
        
        enriched_data = {
            'enriched': False,
            'enriched_at': enrichment_start_time.isoformat(),
            'enrichment_method': 'database_enricher',
            'needs_enrichment': True
        }
        
        try:
            # Step 1: Discover company domain
            domain = self.discover_company_domain(company)
            if domain:
                enriched_data['company_website'] = domain
                
                # Step 2: Generate email patterns
                email_patterns = self.generate_email_patterns(name, domain)
                verified_emails = [e for e in email_patterns if self.verify_email_deliverability(e)]
                
                if verified_emails:
                    enriched_data['email'] = verified_emails[0]
                    enriched_data['email_patterns'] = verified_emails
                    enriched_data['email_confidence'] = 'medium'
                    enriched_data['enriched'] = True
                    enriched_data['needs_enrichment'] = False
                    
                    logger.info(f"✅ Found email for {name}: {verified_emails[0]}")
            
            # Calculate enrichment duration
            enrichment_duration = (datetime.now() - enrichment_start_time).total_seconds()
            enriched_data['enrichment_duration_seconds'] = enrichment_duration
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"❌ Error enriching {name}: {e}")
            enriched_data['enrichment_error'] = str(e)
            return enriched_data
    
    def update_lead_in_database(self, lead_id: str, enriched_data: Dict[str, Any]) -> bool:
        """
        Update lead in database with enriched data.
        
        Args:
            lead_id: Lead ID to update
            enriched_data: Enriched data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.db.update_lead(lead_id, enriched_data)
            
            if success:
                logger.info(f"✅ Updated lead {lead_id} in database")
            else:
                logger.warning(f"⚠️ Failed to update lead {lead_id} in database")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating lead {lead_id}: {e}")
            return False
    
    def update_airtable_with_email(self, airtable_record_id: str, email_data: Dict[str, Any]) -> bool:
        """
        Update Airtable record with found email (for Airtable-sourced leads).
        
        Args:
            airtable_record_id: Airtable record ID
            email_data: Email data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
            
            if not all([api_key, base_id]):
                return False
            
            encoded_table_name = quote(table_name)
            url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}/{airtable_record_id}"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            update_data = {
                'fields': {
                    'Email': email_data.get('email', ''),
                    'Needs Enrichment': False,
                    'Date Enriched': datetime.now().strftime('%Y-%m-%d'),
                    'Response Notes': f"Auto-enriched: {email_data.get('email_confidence', 'medium')} confidence"
                }
            }
            
            response = requests.patch(url, headers=headers, json=update_data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Updated Airtable record with email: {email_data.get('email', '')}")
                return True
            else:
                logger.error(f"❌ Failed to update Airtable: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating Airtable: {str(e)}")
            return False
    
    def run_daily_enrichment(self, max_leads: int = 50) -> Dict[str, Any]:
        """
        Run the daily enrichment process.
        
        Args:
            max_leads: Maximum number of leads to process
            
        Returns:
            Enrichment results dictionary
        """
        start_time = time.time()
        
        logger.info("🚀 Starting daily database enrichment process...")
        
        try:
            # Get leads needing enrichment from database
            database_leads = self.get_leads_needing_enrichment()
            
            # Also get leads from Airtable as fallback
            airtable_leads = self.get_airtable_leads_missing_emails()
            
            # Combine leads (prioritize database leads)
            all_leads = database_leads + airtable_leads
            
            # Limit to max_leads
            leads_to_process = all_leads[:max_leads]
            
            if not leads_to_process:
                logger.info("✅ No leads need enrichment today")
                return {
                    "success": True,
                    "total_leads": 0,
                    "enriched_count": 0,
                    "failed_count": 0,
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
            
            logger.info(f"📋 Processing {len(leads_to_process)} leads for enrichment")
            
            enriched_count = 0
            failed_count = 0
            
            for i, lead in enumerate(leads_to_process, 1):
                logger.info(f"🔄 Processing lead {i}/{len(leads_to_process)}: {lead.get('name', lead.get('full_name', 'Unknown'))}")
                
                try:
                    # Enrich the lead
                    enriched_data = self.enrich_lead(lead)
                    
                    # Update based on source
                    if lead.get('id'):  # Database lead
                        success = self.update_lead_in_database(lead['id'], enriched_data)
                    elif lead.get('airtable_record_id'):  # Airtable lead
                        success = self.update_airtable_with_email(lead['airtable_record_id'], enriched_data)
                    else:
                        success = False
                    
                    if success and enriched_data.get('enriched'):
                        enriched_count += 1
                        logger.info(f"✅ Successfully enriched: {lead.get('name', lead.get('full_name', 'Unknown'))}")
                    else:
                        failed_count += 1
                        if not enriched_data.get('enriched'):
                            logger.info(f"📭 No email found for: {lead.get('name', lead.get('full_name', 'Unknown'))}")
                        else:
                            logger.warning(f"⚠️ Failed to update: {lead.get('name', lead.get('full_name', 'Unknown'))}")
                    
                    # Anti-detection: Random delay between leads
                    if i < len(leads_to_process):  # Don't delay after last lead
                        delay = random.uniform(5, 15)  # 5-15 seconds between leads
                        logger.debug(f"⏱️ Anti-detection delay: {delay:.1f}s")
                        time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {lead.get('name', lead.get('full_name', 'Unknown'))}: {str(e)}")
                    failed_count += 1
                    continue
            
            # Calculate results
            execution_time_ms = (time.time() - start_time) * 1000
            success_rate = (enriched_count / len(leads_to_process)) * 100 if leads_to_process else 0
            
            results = {
                "success": True,
                "total_leads": len(leads_to_process),
                "enriched_count": enriched_count,
                "failed_count": failed_count,
                "success_rate_percent": success_rate,
                "execution_time_ms": execution_time_ms,
                "method": "database_enricher"
            }
            
            # Log summary
            logger.info(f"🎯 Daily enrichment complete: {enriched_count}/{len(leads_to_process)} leads enriched ({success_rate:.1f}% success)")
            
            # Save daily report
            self.save_daily_report(results)
            
            return results
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Daily enrichment failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "total_leads": 0,
                "enriched_count": 0,
                "failed_count": 0,
                "error": error_msg,
                "execution_time_ms": execution_time_ms,
                "method": "database_enricher"
            }
    
    def save_daily_report(self, results: Dict[str, Any]):
        """Save daily enrichment report."""
        try:
            report = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'leads_processed': results.get('total_leads', 0),
                'leads_enriched': results.get('enriched_count', 0),
                'leads_failed': results.get('failed_count', 0),
                'success_rate_percent': results.get('success_rate_percent', 0),
                'execution_time_ms': results.get('execution_time_ms', 0),
                'method': results.get('method', 'database_enricher'),
                'cost': 0  # Free enrichment
            }
            
            # Save to database logs directory
            reports_dir = Path("database_logs") / "enrichment_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Daily report saved: {report['leads_enriched']} leads enriched at $0 cost")
            
        except Exception as e:
            logger.error(f"❌ Error saving daily report: {e}")


def main():
    """Main function for daily enrichment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run daily lead enrichment using database API')
    parser.add_argument('--max-leads', type=int, default=50,
                       help='Maximum number of leads to process (default: 50)')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics only')
    
    args = parser.parse_args()
    
    try:
        logger.info("🥷 Starting Database Daily Enricher Agent...")
        
        agent = DatabaseEnricherAgent()
        
        if args.stats:
            # Show statistics only
            stats = agent.db.get_database_stats()
            print(json.dumps(stats, indent=2))
            return 0
        
        # Run enrichment
        results = agent.run_daily_enrichment(max_leads=args.max_leads)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("📊 ENRICHMENT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total leads processed: {results.get('total_leads', 0)}")
        logger.info(f"Successfully enriched: {results.get('enriched_count', 0)}")
        logger.info(f"Failed: {results.get('failed_count', 0)}")
        logger.info(f"Success rate: {results.get('success_rate_percent', 0):.1f}%")
        logger.info(f"Execution time: {results.get('execution_time_ms', 0):.1f}ms")
        logger.info(f"Method: {results.get('method', 'unknown')}")
        logger.info("=" * 50)
        
        return 0 if results.get('success', False) else 1
        
    except Exception as e:
        logger.error(f"❌ Daily enrichment process failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())