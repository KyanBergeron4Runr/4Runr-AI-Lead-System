#!/usr/bin/env python3
"""
Database-Integrated Scraper Agent for Lead Database Integration.

This agent scrapes leads from various sources and stores them directly
in the database using the new LeadDatabase API with comprehensive logging.
"""

import os
import sys
import json
import time
import random
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

# Import new database components
from lead_database import LeadDatabase
from database_logger import database_logger, log_database_event, monitor_performance

# Web scraping
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup not available - web scraping disabled")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available - advanced scraping disabled")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scraper-agent-database')


class DatabaseScraperAgent:
    """Scraper agent that stores leads directly in the database."""
    
    def __init__(self):
        """Initialize the scraper agent with database connection."""
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
            self.min_delay_between_domains = 3
            
            # Selenium driver (lazy initialization)
            self.driver = None
            
            logger.info("🕷️ Database Scraper Agent initialized with anti-detection measures")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scraper agent: {e}")
            raise
    
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
                sleep_time += random.uniform(0.5, 2)
                logger.debug(f"⏱️ Stealth delay: {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        # Update last request time
        self.last_request_time[domain] = time.time()
        
        # Random additional delay
        if random.random() > 0.8:  # 20% chance
            extra_delay = random.uniform(1, 3)
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
        kwargs.setdefault('timeout', 15)
        kwargs.setdefault('allow_redirects', True)
        
        try:
            response = self.session.get(url, **kwargs)
            logger.debug(f"🌐 Request to {domain}: {response.status_code}")
            return response
            
        except Exception as e:
            logger.warning(f"⚠️ Request failed for {url}: {str(e)}")
            return None
    
    def init_selenium_driver(self) -> bool:
        """Initialize Selenium WebDriver for advanced scraping."""
        if not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium not available")
            return False
        
        try:
            if self.driver:
                return True
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium WebDriver initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            return False
    
    def cleanup_selenium(self):
        """Clean up Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("🧹 Selenium WebDriver cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up Selenium: {e}")
    
    def extract_contact_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract contact information from text using regex patterns."""
        contact_info = {}
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['emails'] = list(set(emails))  # Remove duplicates
        
        # Phone patterns
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phones'] = ['-'.join(phone[1:]) for phone in phones]
        
        # LinkedIn profile patterns
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9-]+'
        linkedin_urls = re.findall(linkedin_pattern, text)
        if linkedin_urls:
            contact_info['linkedin_urls'] = list(set(linkedin_urls))
        
        return contact_info
    
    def scrape_company_website(self, company_name: str, website_url: str) -> List[Dict[str, Any]]:
        """
        Scrape a company website for lead information.
        
        Args:
            company_name: Name of the company
            website_url: Company website URL
            
        Returns:
            List of lead dictionaries found on the website
        """
        leads = []
        
        try:
            logger.info(f"🕷️ Scraping {company_name} website: {website_url}")
            
            # Get main page
            response = self.stealth_request(website_url)
            if not response or response.status_code != 200:
                logger.warning(f"⚠️ Could not access {website_url}")
                return leads
            
            if not BS4_AVAILABLE:
                logger.warning("⚠️ BeautifulSoup not available for parsing")
                return leads
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract contact information from main page
            page_text = soup.get_text()
            contact_info = self.extract_contact_info_from_text(page_text)
            
            # Look for common contact/about/team pages
            contact_pages = []
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                link_text = link.get_text().lower()
                
                if any(keyword in href or keyword in link_text for keyword in 
                      ['contact', 'about', 'team', 'staff', 'people', 'leadership']):
                    full_url = urljoin(website_url, link['href'])
                    contact_pages.append(full_url)
            
            # Scrape contact pages
            for page_url in contact_pages[:3]:  # Limit to 3 pages
                try:
                    page_response = self.stealth_request(page_url)
                    if page_response and page_response.status_code == 200:
                        page_soup = BeautifulSoup(page_response.content, 'html.parser')
                        page_text = page_soup.get_text()
                        page_contact_info = self.extract_contact_info_from_text(page_text)
                        
                        # Merge contact info
                        for key, value in page_contact_info.items():
                            if key in contact_info:
                                contact_info[key].extend(value)
                            else:
                                contact_info[key] = value
                
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {page_url}: {e}")
                    continue
            
            # Create leads from found contact information
            if contact_info.get('emails'):
                for email in contact_info['emails'][:5]:  # Limit to 5 emails
                    lead = {
                        'email': email,
                        'company': company_name,
                        'company_website': website_url,
                        'source': 'website_scraper',
                        'scraped_at': datetime.now().isoformat(),
                        'needs_enrichment': True,
                        'verified': False,
                        'enriched': False
                    }
                    
                    # Try to extract name from email
                    email_parts = email.split('@')[0].split('.')
                    if len(email_parts) >= 2:
                        lead['full_name'] = ' '.join(part.capitalize() for part in email_parts)
                    
                    # Add LinkedIn if found
                    if contact_info.get('linkedin_urls'):
                        lead['linkedin_url'] = contact_info['linkedin_urls'][0]
                    
                    leads.append(lead)
            
            logger.info(f"✅ Found {len(leads)} potential leads from {company_name}")
            
        except Exception as e:
            logger.error(f"❌ Error scraping {company_name}: {e}")
        
        return leads
    
    def scrape_linkedin_company_page(self, company_name: str, linkedin_url: str) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn company page for employee information.
        
        Args:
            company_name: Name of the company
            linkedin_url: LinkedIn company page URL
            
        Returns:
            List of lead dictionaries found on LinkedIn
        """
        leads = []
        
        try:
            logger.info(f"🔗 Scraping LinkedIn for {company_name}: {linkedin_url}")
            
            # Initialize Selenium if needed
            if not self.init_selenium_driver():
                logger.warning("⚠️ Cannot scrape LinkedIn without Selenium")
                return leads
            
            # Navigate to LinkedIn company page
            self.driver.get(linkedin_url)
            time.sleep(random.uniform(3, 6))  # Random delay
            
            # Look for employee links
            try:
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Find employee links (this is a simplified approach)
                employee_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
                
                for link in employee_links[:10]:  # Limit to 10 employees
                    try:
                        profile_url = link.get_attribute('href')
                        profile_text = link.text.strip()
                        
                        if profile_text and len(profile_text.split()) >= 2:
                            lead = {
                                'full_name': profile_text,
                                'company': company_name,
                                'linkedin_url': profile_url,
                                'source': 'linkedin_scraper',
                                'scraped_at': datetime.now().isoformat(),
                                'needs_enrichment': True,
                                'verified': False,
                                'enriched': False
                            }
                            leads.append(lead)
                    
                    except Exception as e:
                        logger.debug(f"⚠️ Error processing employee link: {e}")
                        continue
                
                logger.info(f"✅ Found {len(leads)} potential leads from LinkedIn")
                
            except Exception as e:
                logger.warning(f"⚠️ Error scraping LinkedIn page: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error accessing LinkedIn: {e}")
        
        return leads
    
    @monitor_performance("store_leads_in_database")
    def store_leads_in_database(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store scraped leads in the database.
        
        Args:
            leads: List of lead dictionaries to store
            
        Returns:
            Storage results dictionary
        """
        if not leads:
            return {"success": True, "stored_count": 0, "duplicate_count": 0, "error_count": 0}
        
        stored_count = 0
        duplicate_count = 0
        error_count = 0
        errors = []
        
        logger.info(f"💾 Storing {len(leads)} leads in database...")
        
        for lead in leads:
            try:
                # Add lead to database (duplicate detection is automatic)
                lead_id = self.db.add_lead(lead)
                
                if lead_id:
                    stored_count += 1
                    logger.debug(f"✅ Stored lead: {lead.get('full_name', lead.get('email', 'Unknown'))}")
                else:
                    duplicate_count += 1
                    logger.debug(f"🔄 Duplicate lead: {lead.get('full_name', lead.get('email', 'Unknown'))}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"Error storing lead {lead.get('full_name', lead.get('email', 'Unknown'))}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
        
        results = {
            "success": error_count == 0,
            "total_leads": len(leads),
            "stored_count": stored_count,
            "duplicate_count": duplicate_count,
            "error_count": error_count,
            "errors": errors
        }
        
        logger.info(f"✅ Storage complete: {stored_count} stored, {duplicate_count} duplicates, {error_count} errors")
        
        return results
    
    def scrape_company_leads(self, company_name: str, website_url: Optional[str] = None, 
                           linkedin_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape leads from a company using multiple sources.
        
        Args:
            company_name: Name of the company
            website_url: Company website URL (optional)
            linkedin_url: LinkedIn company page URL (optional)
            
        Returns:
            Scraping results dictionary
        """
        start_time = time.time()
        all_leads = []
        
        try:
            logger.info(f"🎯 Starting lead scraping for: {company_name}")
            
            # Scrape website if provided
            if website_url:
                website_leads = self.scrape_company_website(company_name, website_url)
                all_leads.extend(website_leads)
                logger.info(f"🌐 Website scraping: {len(website_leads)} leads found")
            
            # Scrape LinkedIn if provided
            if linkedin_url:
                linkedin_leads = self.scrape_linkedin_company_page(company_name, linkedin_url)
                all_leads.extend(linkedin_leads)
                logger.info(f"🔗 LinkedIn scraping: {len(linkedin_leads)} leads found")
            
            # Store leads in database
            storage_results = self.store_leads_in_database(all_leads)
            
            # Calculate final results
            execution_time_ms = (time.time() - start_time) * 1000
            
            results = {
                "success": storage_results["success"],
                "company_name": company_name,
                "total_leads_found": len(all_leads),
                "leads_stored": storage_results["stored_count"],
                "duplicates_found": storage_results["duplicate_count"],
                "errors": storage_results["error_count"],
                "execution_time_ms": execution_time_ms,
                "sources_scraped": {
                    "website": website_url is not None,
                    "linkedin": linkedin_url is not None
                }
            }
            
            # Log scraping operation
            log_database_event("database_operation", {"company": company_name}, {
                "success": results["success"],
                "records_affected": results["leads_stored"],
                "operation_type": "scrape_company_leads"
            }, {
                "operation_type": "bulk_add_leads",
                "performance_metrics": {"execution_time_ms": execution_time_ms}
            })
            
            return results
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Company scraping failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "company_name": company_name,
                "total_leads_found": 0,
                "leads_stored": 0,
                "duplicates_found": 0,
                "errors": 1,
                "error_message": error_msg,
                "execution_time_ms": execution_time_ms
            }
    
    def run_batch_scraping(self, companies: List[Dict[str, str]], max_companies: int = 10) -> Dict[str, Any]:
        """
        Run batch scraping for multiple companies.
        
        Args:
            companies: List of company dictionaries with name, website, linkedin_url
            max_companies: Maximum number of companies to process
            
        Returns:
            Batch scraping results
        """
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting batch scraping for {len(companies)} companies...")
            
            # Limit companies
            companies_to_process = companies[:max_companies]
            
            total_leads_found = 0
            total_leads_stored = 0
            total_duplicates = 0
            total_errors = 0
            company_results = []
            
            for i, company in enumerate(companies_to_process, 1):
                company_name = company.get('name', 'Unknown')
                website_url = company.get('website')
                linkedin_url = company.get('linkedin_url')
                
                logger.info(f"🏢 Processing company {i}/{len(companies_to_process)}: {company_name}")
                
                try:
                    # Scrape company
                    results = self.scrape_company_leads(company_name, website_url, linkedin_url)
                    company_results.append(results)
                    
                    # Accumulate totals
                    total_leads_found += results.get("total_leads_found", 0)
                    total_leads_stored += results.get("leads_stored", 0)
                    total_duplicates += results.get("duplicates_found", 0)
                    total_errors += results.get("errors", 0)
                    
                    # Anti-detection delay between companies
                    if i < len(companies_to_process):
                        delay = random.uniform(10, 30)  # 10-30 seconds between companies
                        logger.info(f"⏱️ Anti-detection delay: {delay:.1f}s")
                        time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"❌ Error processing {company_name}: {e}")
                    total_errors += 1
                    continue
            
            # Calculate final results
            execution_time_ms = (time.time() - start_time) * 1000
            success_rate = (total_leads_stored / max(total_leads_found, 1)) * 100
            
            batch_results = {
                "success": total_errors == 0,
                "companies_processed": len(companies_to_process),
                "total_leads_found": total_leads_found,
                "total_leads_stored": total_leads_stored,
                "total_duplicates": total_duplicates,
                "total_errors": total_errors,
                "success_rate_percent": success_rate,
                "execution_time_ms": execution_time_ms,
                "company_results": company_results
            }
            
            logger.info(f"🎯 Batch scraping complete: {total_leads_stored} leads stored from {len(companies_to_process)} companies")
            
            return batch_results
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Batch scraping failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "companies_processed": 0,
                "total_leads_found": 0,
                "total_leads_stored": 0,
                "total_duplicates": 0,
                "total_errors": 1,
                "error_message": error_msg,
                "execution_time_ms": execution_time_ms
            }
        
        finally:
            # Clean up Selenium
            self.cleanup_selenium()
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics from the database."""
        try:
            db_stats = self.db.get_database_stats()
            
            # Get recent scraping activity
            recent_leads = self.db.search_leads({
                'source': 'website_scraper'
            })
            
            linkedin_leads = self.db.search_leads({
                'source': 'linkedin_scraper'
            })
            
            return {
                "database_stats": db_stats,
                "website_scraped_leads": len(recent_leads),
                "linkedin_scraped_leads": len(linkedin_leads),
                "total_scraped_leads": len(recent_leads) + len(linkedin_leads),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting scraping statistics: {e}")
            return {"error": str(e)}


def main():
    """Main function for scraper agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run lead scraping using database API')
    parser.add_argument('--company', type=str, help='Company name to scrape')
    parser.add_argument('--website', type=str, help='Company website URL')
    parser.add_argument('--linkedin', type=str, help='LinkedIn company page URL')
    parser.add_argument('--batch-file', type=str, help='JSON file with companies to scrape')
    parser.add_argument('--max-companies', type=int, default=10, help='Maximum companies to process')
    parser.add_argument('--stats', action='store_true', help='Show scraping statistics only')
    
    args = parser.parse_args()
    
    try:
        logger.info("🕷️ Starting Database Scraper Agent...")
        
        agent = DatabaseScraperAgent()
        
        if args.stats:
            # Show statistics only
            stats = agent.get_scraping_statistics()
            print(json.dumps(stats, indent=2))
            return 0
        
        if args.company:
            # Single company scraping
            results = agent.scrape_company_leads(args.company, args.website, args.linkedin)
            
            # Print results
            logger.info("=" * 50)
            logger.info("📊 SCRAPING SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Company: {results.get('company_name', 'Unknown')}")
            logger.info(f"Total leads found: {results.get('total_leads_found', 0)}")
            logger.info(f"Leads stored: {results.get('leads_stored', 0)}")
            logger.info(f"Duplicates: {results.get('duplicates_found', 0)}")
            logger.info(f"Errors: {results.get('errors', 0)}")
            logger.info(f"Execution time: {results.get('execution_time_ms', 0):.1f}ms")
            logger.info("=" * 50)
            
            return 0 if results.get('success', False) else 1
        
        elif args.batch_file:
            # Batch scraping from file
            try:
                with open(args.batch_file, 'r') as f:
                    companies = json.load(f)
                
                results = agent.run_batch_scraping(companies, args.max_companies)
                
                # Print results
                logger.info("=" * 50)
                logger.info("📊 BATCH SCRAPING SUMMARY")
                logger.info("=" * 50)
                logger.info(f"Companies processed: {results.get('companies_processed', 0)}")
                logger.info(f"Total leads found: {results.get('total_leads_found', 0)}")
                logger.info(f"Total leads stored: {results.get('total_leads_stored', 0)}")
                logger.info(f"Total duplicates: {results.get('total_duplicates', 0)}")
                logger.info(f"Total errors: {results.get('total_errors', 0)}")
                logger.info(f"Success rate: {results.get('success_rate_percent', 0):.1f}%")
                logger.info(f"Execution time: {results.get('execution_time_ms', 0):.1f}ms")
                logger.info("=" * 50)
                
                return 0 if results.get('success', False) else 1
                
            except Exception as e:
                logger.error(f"❌ Error reading batch file: {e}")
                return 1
        
        else:
            logger.error("❌ Please specify --company or --batch-file")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Scraper agent failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())