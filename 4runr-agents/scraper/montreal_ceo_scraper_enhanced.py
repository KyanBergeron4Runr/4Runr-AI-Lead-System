#!/usr/bin/env python3
"""
Enhanced Montreal CEO Scraper

Scrapes fresh Montreal-based CEOs, Founders, Presidents with:
- Stealth techniques
- Real company validation
- Decision-maker filtering
- De-duplication
"""

import os
import json
import time
import logging
import asyncio
import random
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# Add shared modules to path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))
from linkedin_url_validator import validate_linkedin_url, clean_linkedin_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('montreal-ceo-scraper')

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for scraper")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

# Load environment
load_dotenv()

class MontrealCEOScraper:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        self.use_proxy = os.getenv('PROXY_SERVER', '') != ''
        
        # Montreal-specific search parameters
        self.montreal_region_id = "101449429"  # Montreal region ID
        self.target_titles = [
            "CEO", "Chief Executive Officer", "Founder", "Co-Founder", 
            "President", "Managing Director", "Executive Director", 
            "Managing Partner", "Owner"
        ]
        
        # Company validation criteria
        self.min_company_name_length = 4
        self.excluded_keywords = [
            "student", "freelancer", "assistant", "recruiter", "consultant",
            "intern", "volunteer", "unemployed", "seeking", "looking for"
        ]
        
        self.browser = None
        self.page = None
        self.is_logged_in = False
        
        # Load cookies if available
        self.cookies_file = Path(__file__).parent / 'cookies.json'
        
    async def start_browser(self):
        """Start browser with stealth configuration"""
        playwright = await async_playwright().start()
        
        # Enhanced stealth configuration
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-features=TranslateUI',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--metrics-recording-only',
            '--no-default-browser-check',
            '--safebrowsing-disable-auto-update',
            '--enable-automation',
            '--password-store=basic',
            '--use-mock-keychain'
        ]
        
        # Add proxy if configured
        proxy_config = None
        if self.use_proxy:
            proxy_server = os.getenv('PROXY_SERVER')
            proxy_username = os.getenv('PROXY_USERNAME')
            proxy_password = os.getenv('PROXY_PASSWORD')
            
            proxy_config = {
                'server': proxy_server,
                'username': proxy_username,
                'password': proxy_password
            }
            logger.info(f"🔒 Using proxy: {proxy_server}")
        
        try:
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args,
                proxy=proxy_config
            )
        except Exception as e:
            logger.error(f"❌ Browser launch failed: {e}")
            raise
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Montreal',
            geolocation={'latitude': 45.5017, 'longitude': -73.5673},  # Montreal coordinates
            permissions=['geolocation']
        )
        
        self.page = await context.new_page()
        
        # Set realistic timeouts
        self.page.set_default_timeout(30000)
        
        # Load cookies if available
        await self.load_cookies()
        
        logger.info("🚀 Enhanced browser started with stealth configuration")
    
    async def load_cookies(self):
        """Load saved cookies to maintain session"""
        if self.cookies_file.exists():
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                await self.page.context.add_cookies(cookies)
                logger.info("🍪 Loaded saved cookies")
                
                # Test if we're already logged in
                await self.page.goto('https://www.linkedin.com/feed/')
                await asyncio.sleep(2)
                
                if 'feed' in self.page.url:
                    self.is_logged_in = True
                    logger.info("✅ Already logged in via cookies")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not load cookies: {e}")
    
    async def save_cookies(self):
        """Save cookies for future sessions"""
        try:
            cookies = await self.page.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info("🍪 Cookies saved")
        except Exception as e:
            logger.warning(f"⚠️ Could not save cookies: {e}")
    
    async def login(self):
        """Login to LinkedIn with enhanced stealth"""
        if self.is_logged_in:
            return True
            
        try:
            logger.info("🔐 Logging into LinkedIn...")
            await self.page.goto('https://www.linkedin.com/login')
            
            # Random delay to appear human
            await asyncio.sleep(random.uniform(2, 4))
            
            # Wait for login form
            await self.page.wait_for_selector('#username', timeout=10000)
            
            # Human-like typing
            await self.page.type('#username', self.email, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            await self.page.type('#password', self.password, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Click login button
            await self.page.click('button[type="submit"]')
            
            # Wait for login to complete
            try:
                await self.page.wait_for_selector('main', timeout=15000)
                
                current_url = self.page.url
                
                # Check for security challenge
                if 'challenge' in current_url or 'checkpoint' in current_url:
                    logger.error("🚨 LinkedIn security challenge detected")
                    return False
                
                # Check for successful login
                if 'feed' in current_url or 'mynetwork' in current_url:
                    self.is_logged_in = True
                    await self.save_cookies()
                    logger.info("✅ Successfully logged into LinkedIn")
                    return True
                
                # Navigate to feed to confirm login
                await self.page.goto('https://www.linkedin.com/feed/')
                await self.page.wait_for_selector('main', timeout=10000)
                
                self.is_logged_in = True
                await self.save_cookies()
                logger.info("✅ Successfully logged into LinkedIn")
                return True
                
            except PlaywrightTimeoutError:
                logger.error("❌ Login timeout - possible security challenge")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False
    
    def build_search_url(self, title_keywords: List[str], page: int = 1) -> str:
        """Build LinkedIn search URL for Montreal CEOs"""
        # Base search URL for people in Montreal
        base_url = "https://www.linkedin.com/search/results/people/"
        
        # Build title query
        title_query = " OR ".join([f'"{title}"' for title in title_keywords])
        
        # Search parameters
        params = {
            'keywords': title_query,
            'geoUrn': f'["urn:li:fs_geo:{self.montreal_region_id}"]',  # Montreal region
            'origin': 'FACETED_SEARCH',
            'page': page
        }
        
        # Build query string
        query_parts = []
        for key, value in params.items():
            if key == 'geoUrn':
                query_parts.append(f"{key}={value}")
            else:
                query_parts.append(f"{key}={value}")
        
        search_url = f"{base_url}?{'&'.join(query_parts)}"
        logger.info(f"🔍 Search URL: {search_url}")
        
        return search_url
    
    async def navigate_to_search(self, title_keywords: List[str], page: int = 1):
        """Navigate to Montreal CEO search results"""
        try:
            search_url = self.build_search_url(title_keywords, page)
            
            logger.info(f"🔍 Searching for Montreal {'/'.join(title_keywords)} (page {page})")
            await self.page.goto(search_url)
            
            # Wait for results to load
            await self.page.wait_for_selector('.search-results-container, .reusable-search__result-container', timeout=15000)
            
            # Random delay
            await asyncio.sleep(random.uniform(3, 6))
            
            logger.info("✅ Search results loaded")
            return True
            
        except PlaywrightTimeoutError:
            logger.error("❌ Search results failed to load")
            return False
        except Exception as e:
            logger.error(f"❌ Search navigation failed: {str(e)}")
            return False
    
    def validate_company(self, company: str) -> bool:
        """Validate if company appears legitimate"""
        if not company or len(company.strip()) < self.min_company_name_length:
            return False
        
        company_lower = company.lower().strip()
        
        # Check for excluded keywords
        if any(keyword in company_lower for keyword in self.excluded_keywords):
            return False
        
        # Check for common fake company indicators
        fake_indicators = [
            "n/a", "none", "self", "freelance", "independent", 
            "unemployed", "seeking", "looking", "available"
        ]
        
        if any(indicator in company_lower for indicator in fake_indicators):
            return False
        
        return True
    
    def validate_title(self, title: str) -> bool:
        """Validate if title indicates decision-making authority"""
        if not title:
            return False
        
        title_lower = title.lower().strip()
        
        # Check for excluded keywords
        if any(keyword in title_lower for keyword in self.excluded_keywords):
            return False
        
        # Check if title contains decision-maker keywords
        decision_maker_keywords = [
            "ceo", "chief executive", "founder", "co-founder", "president", 
            "managing director", "executive director", "managing partner", 
            "owner", "principal", "head of", "director"
        ]
        
        return any(keyword in title_lower for keyword in decision_maker_keywords)
    
    async def extract_leads_from_page(self) -> List[Dict]:
        """Extract validated leads from current search page"""
        leads = []
        
        try:
            # Wait for results to be fully loaded
            await asyncio.sleep(random.uniform(2, 4))
            
            # Find result containers
            result_containers = await self.page.query_selector_all('.reusable-search__result-container')
            
            if not result_containers:
                logger.warning("⚠️ No result containers found")
                return leads
            
            logger.info(f"🔍 Found {len(result_containers)} potential leads")
            
            for i, container in enumerate(result_containers):
                try:
                    lead_data = await self.extract_lead_from_container(container)
                    
                    if lead_data and self.validate_lead(lead_data):
                        leads.append(lead_data)
                        logger.info(f"✅ Extracted: {lead_data['name']} - {lead_data['title']} at {lead_data['company']}")
                    
                    # Random delay between extractions
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract lead {i+1}: {str(e)}")
                    continue
            
            logger.info(f"📊 Successfully extracted {len(leads)} validated leads")
            return leads
            
        except Exception as e:
            logger.error(f"❌ Failed to extract leads: {str(e)}")
            return leads
    
    async def extract_lead_from_container(self, container) -> Optional[Dict]:
        """Extract lead data from a result container"""
        try:
            # Extract name
            name_element = await container.query_selector('.entity-result__title-text a span[aria-hidden="true"]')
            if not name_element:
                name_element = await container.query_selector('.entity-result__title-text a')
            
            name = await name_element.inner_text() if name_element else None
            if not name:
                return None
            
            # Extract LinkedIn URL
            url_element = await container.query_selector('.entity-result__title-text a')
            linkedin_url = await url_element.get_attribute('href') if url_element else None
            
            # Clean and validate LinkedIn URL
            if linkedin_url:
                cleaned_url = clean_linkedin_url(linkedin_url)
                if cleaned_url:
                    # Validate the URL format (don't test accessibility during scraping for speed)
                    validation_result = validate_linkedin_url(cleaned_url, test_accessibility=False)
                    if validation_result['format_valid']:
                        linkedin_url = validation_result['cleaned_url']
                    else:
                        logger.debug(f"Invalid LinkedIn URL format: {linkedin_url}")
                        return None
                else:
                    return None
            else:
                return None
            
            # Extract title
            title_element = await container.query_selector('.entity-result__primary-subtitle')
            title = await title_element.inner_text() if title_element else ""
            
            # Extract company
            company_element = await container.query_selector('.entity-result__secondary-subtitle')
            company = await company_element.inner_text() if company_element else ""
            
            # Extract location (should be Montreal area)
            location_element = await container.query_selector('.entity-result__secondary-subtitle')
            location = await location_element.inner_text() if location_element else "Montreal, Quebec, Canada"
            
            # Clean extracted data
            name = self.clean_text(name)
            title = self.clean_text(title)
            company = self.clean_text(company)
            location = self.clean_text(location)
            
            # Create lead object
            lead = {
                "uuid": str(uuid.uuid4()),
                "name": name,
                "full_name": name,
                "title": title,
                "company": company,
                "location": location,
                "linkedin_url": linkedin_url,
                "email": None,  # To be enriched later
                "verified": False,  # To be verified later
                "enriched": False,
                "scraped_at": datetime.now().isoformat(),
                "source": "Montreal CEO Search",
                "needs_enrichment": True,
                "status": "scraped"
            }
            
            return lead
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract lead data: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        
        # Remove LinkedIn artifacts
        text = text.replace('LinkedIn Member', '').strip()
        
        return text
    
    def validate_lead(self, lead: Dict) -> bool:
        """Validate if lead meets our criteria"""
        # Check required fields
        if not all([lead.get('name'), lead.get('linkedin_url'), lead.get('title')]):
            return False
        
        # Validate title (decision-maker)
        if not self.validate_title(lead['title']):
            logger.debug(f"❌ Invalid title: {lead['title']}")
            return False
        
        # Validate company
        if not self.validate_company(lead.get('company', '')):
            logger.debug(f"❌ Invalid company: {lead.get('company', 'N/A')}")
            return False
        
        # Check for Montreal location (basic check)
        location = lead.get('location', '').lower()
        montreal_indicators = ['montreal', 'québec', 'quebec', 'canada']
        if not any(indicator in location for indicator in montreal_indicators):
            logger.debug(f"❌ Not Montreal-based: {location}")
            return False
        
        return True
    
    async def scrape_montreal_ceos(self, max_leads: int = 10, max_pages: int = 3) -> List[Dict]:
        """Main method to scrape Montreal CEOs"""
        all_leads = []
        scraping_start_time = datetime.now()
        
        try:
            if not self.is_logged_in:
                logger.error("❌ Not logged in to LinkedIn")
                return all_leads
            
            # Define title groups to search
            title_groups = [
                ["CEO", "Chief Executive Officer"],
                ["Founder", "Co-Founder"],
                ["President", "Managing Director"],
                ["Executive Director", "Managing Partner"]
            ]
            
            for title_group in title_groups:
                if len(all_leads) >= max_leads:
                    break
                
                logger.info(f"🔍 Searching for {'/'.join(title_group)} in Montreal")
                
                for page in range(1, max_pages + 1):
                    if len(all_leads) >= max_leads:
                        break
                    
                    # Navigate to search
                    if not await self.navigate_to_search(title_group, page):
                        break
                    
                    # Extract leads from current page
                    page_leads = await self.extract_leads_from_page()
                    
                    # Add unique leads only
                    for lead in page_leads:
                        if len(all_leads) >= max_leads:
                            break
                        
                        # Check for duplicates by LinkedIn URL
                        linkedin_url = lead.get('linkedin_url')
                        if not any(existing['linkedin_url'] == linkedin_url for existing in all_leads):
                            all_leads.append(lead)
                    
                    logger.info(f"📊 Total leads collected: {len(all_leads)}")
                    
                    # Random delay between pages
                    await asyncio.sleep(random.uniform(5, 10))
                
                # Delay between title groups
                await asyncio.sleep(random.uniform(10, 15))
            
            logger.info(f"🎉 Scraping completed! Total leads: {len(all_leads)}")
            
            # Log production data - scraping complete
            if PRODUCTION_LOGGING_ENABLED:
                try:
                    scraping_results = {
                        "total_leads_found": len(all_leads),
                        "scraping_duration": (datetime.now() - scraping_start_time).total_seconds(),
                        "pages_scraped": max_pages,
                        "title_groups_searched": len([["CEO", "Chief Executive Officer"], ["Founder", "Co-Founder"], ["President", "Managing Director"], ["Executive Director", "Managing Partner"]]),
                        "success_rate": len(all_leads) / max_leads if max_leads > 0 else 0,
                        "leads_data": all_leads[:5]  # Sample of leads for training
                    }
                    
                    scraping_decisions = {
                        "target_region": "Montreal",
                        "max_leads_requested": max_leads,
                        "max_pages_per_search": max_pages,
                        "stealth_enabled": True,
                        "deduplication_applied": True
                    }
                    
                    log_production_event(
                        "website_analysis",  # Using website_analysis for scraping
                        {"scraping_target": "Montreal CEOs", "max_leads": max_leads},
                        scraping_results,
                        {"decisions": scraping_decisions}
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Production logging failed: {e}")
            
            return all_leads[:max_leads]  # Ensure we don't exceed max_leads
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")
            return all_leads
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("🔒 Browser closed")

async def scrape_fresh_montreal_ceos(max_leads: int = 10) -> List[Dict]:
    """Main function to scrape fresh Montreal CEOs"""
    scraper = None
    
    try:
        scraper = MontrealCEOScraper()
        
        # Start browser
        await scraper.start_browser()
        
        # Login
        if not await scraper.login():
            logger.error("❌ Failed to login to LinkedIn")
            return []
        
        # Scrape leads
        leads = await scraper.scrape_montreal_ceos(max_leads=max_leads, max_pages=3)
        
        logger.info(f"✅ Successfully scraped {len(leads)} Montreal CEO leads")
        return leads
        
    except Exception as e:
        logger.error(f"❌ Error in Montreal CEO scraping: {str(e)}")
        return []
        
    finally:
        if scraper:
            await scraper.close()

if __name__ == "__main__":
    # Test the scraper
    leads = asyncio.run(scrape_fresh_montreal_ceos(max_leads=5))
    print(f"\n🎯 Scraped {len(leads)} Montreal CEO leads:")
    for lead in leads:
        print(f"  - {lead['name']} ({lead['title']}) at {lead['company']}")