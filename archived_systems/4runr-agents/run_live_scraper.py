#!/usr/bin/env python3
"""
Live LinkedIn Scraper - Get fresh, accessible leads from LinkedIn search
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('live-scraper')

# Constants
SHARED_DIR = os.path.join(os.path.dirname(__file__), "shared")
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")

class LiveLinkedInScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.cookies_file = Path(__file__).parent / "scraper" / "cookies.json"
        
    async def start_browser(self):
        """Start browser with cookies"""
        playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        
        # Load cookies
        await self._load_cookies()
        
        logger.info("✅ Browser started with cookies loaded")
    
    async def _load_cookies(self):
        """Load LinkedIn cookies"""
        if self.cookies_file.exists():
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Convert to Playwright format
            playwright_cookies = []
            for cookie in cookies:
                playwright_cookie = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path'],
                    'expires': cookie.get('expirationDate', -1),
                    'httpOnly': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False),
                    'sameSite': self._convert_same_site(cookie.get('sameSite', 'Lax'))
                }
                playwright_cookies.append(playwright_cookie)
            
            await self.context.add_cookies(playwright_cookies)
            logger.info(f"✅ Loaded {len(playwright_cookies)} cookies")
    
    def _convert_same_site(self, same_site_value):
        """Convert Chrome cookie sameSite values to Playwright format"""
        if same_site_value in ['no_restriction', 'None']:
            return 'None'
        elif same_site_value in ['lax', 'Lax']:
            return 'Lax'
        elif same_site_value in ['strict', 'Strict']:
            return 'Strict'
        else:
            return 'Lax'
    
    async def search_linkedin_ceos(self, location="Montreal, Quebec, Canada", max_results=10):
        """Search for CEOs in Montreal area"""
        try:
            # Navigate to LinkedIn search
            search_url = f"https://www.linkedin.com/search/results/people/?keywords=CEO&origin=GLOBAL_SEARCH_HEADER&geoUrn=%5B%22101449429%22%5D"
            
            logger.info(f"🔍 Searching LinkedIn for CEOs in {location}")
            logger.info(f"🔗 Search URL: {search_url}")
            
            await self.page.goto(search_url, wait_until='networkidle', timeout=30000)
            
            # Wait for search results
            await asyncio.sleep(5)
            
            # Check if we're logged in
            current_url = self.page.url
            if 'login' in current_url or 'challenge' in current_url:
                logger.error("❌ Not logged in to LinkedIn - please check cookies")
                return []
            
            # Wait for search results to load
            try:
                await self.page.wait_for_selector('.reusable-search__result-container', timeout=15000)
            except:
                logger.warning("⚠️ Search results not found with primary selector, trying alternatives")
                try:
                    await self.page.wait_for_selector('.search-result__wrapper', timeout=10000)
                except:
                    logger.error("❌ No search results found")
                    return []
            
            # Extract profiles from search results
            leads = []
            result_containers = await self.page.query_selector_all('.reusable-search__result-container')
            
            if not result_containers:
                result_containers = await self.page.query_selector_all('.search-result__wrapper')
            
            logger.info(f"📋 Found {len(result_containers)} search result containers")
            
            for i, container in enumerate(result_containers[:max_results]):
                try:
                    lead_data = await self._extract_profile_data(container)
                    
                    if lead_data and lead_data.get('linkedin_url') and lead_data.get('name'):
                        # Quick validation - check if URL looks valid
                        if '/in/' in lead_data['linkedin_url']:
                            leads.append(lead_data)
                            logger.info(f"✅ Extracted: {lead_data['name']} - {lead_data.get('title', 'N/A')} at {lead_data.get('company', 'N/A')}")
                        else:
                            logger.warning(f"⚠️ Invalid LinkedIn URL: {lead_data.get('linkedin_url')}")
                    else:
                        logger.warning(f"⚠️ Incomplete profile data for result {i+1}")
                    
                    # Human-like delay
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract profile {i+1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Successfully extracted {len(leads)} LinkedIn profiles")
            return leads
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return []
    
    async def _extract_profile_data(self, container):
        """Extract profile data from search result container"""
        try:
            # Extract name
            name_element = await container.query_selector('.entity-result__title-text a span[aria-hidden="true"]')
            if not name_element:
                name_element = await container.query_selector('.actor-name a')
            if not name_element:
                name_element = await container.query_selector('a[data-control-name="search_srp_result"] span[aria-hidden="true"]')
            
            if not name_element:
                return None
            
            name = await name_element.inner_text()
            name = name.strip()
            
            # Extract LinkedIn URL
            url_element = await container.query_selector('.entity-result__title-text a')
            if not url_element:
                url_element = await container.query_selector('.actor-name a')
            if not url_element:
                url_element = await container.query_selector('a[data-control-name="search_srp_result"]')
            
            if not url_element:
                return None
            
            linkedin_url = await url_element.get_attribute('href')
            
            # Clean LinkedIn URL
            if linkedin_url:
                if linkedin_url.startswith('/'):
                    linkedin_url = f"https://www.linkedin.com{linkedin_url}"
                # Remove tracking parameters
                if '?' in linkedin_url:
                    linkedin_url = linkedin_url.split('?')[0]
            
            # Extract title/position
            title_element = await container.query_selector('.entity-result__primary-subtitle')
            title = ""
            if title_element:
                title = await title_element.inner_text()
                title = title.strip()
            
            # Extract company
            company_element = await container.query_selector('.entity-result__secondary-subtitle')
            company = ""
            if company_element:
                company = await company_element.inner_text()
                company = company.strip()
            
            # Extract location if available
            location_element = await container.query_selector('.entity-result__location')
            location = "Montreal, Quebec, Canada"  # Default
            if location_element:
                location_text = await location_element.inner_text()
                if location_text:
                    location = location_text.strip()
            
            # Validate we have minimum required data
            if not name or not linkedin_url:
                return None
            
            # Create lead object
            lead = {
                "name": name,
                "title": title,
                "company": company,
                "linkedin_url": linkedin_url,
                "location": location,
                "scraped_at": datetime.now().isoformat(),
                "source": "Live LinkedIn Search"
            }
            
            return lead
            
        except Exception as e:
            logger.warning(f"Failed to extract profile data: {str(e)}")
            return None
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()

def save_raw_leads(leads):
    """Save leads to raw_leads.json"""
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    formatted_leads = []
    for lead in leads:
        if not lead.get("linkedin_url") or not lead.get("name"):
            logger.warning(f"⚠️ Skipping person without LinkedIn URL: {lead.get('name', 'Unknown')}")
            continue
        
        lead_uuid = str(uuid.uuid4())
        
        formatted_lead = {
            "uuid": lead_uuid,
            "full_name": lead["name"],
            "linkedin_url": lead["linkedin_url"],
            "company": lead.get("company", ""),
            "title": lead.get("title", ""),
            "location": lead.get("location", "Montreal, Quebec, Canada"),
            "verified": False,
            "enriched": False,
            "email": None,
            "engagement_method": None,
            "scraped_at": datetime.now().isoformat(),
            "source": "Live LinkedIn Search - Real Profiles"
        }
        
        formatted_leads.append(formatted_lead)
    
    if not formatted_leads:
        logger.error("❌ No real people found with LinkedIn URLs")
        return []
    
    # Save to raw_leads.json
    raw_leads_file = os.path.join(SHARED_DIR, "raw_leads.json")
    
    with open(raw_leads_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_leads, f, indent=2, ensure_ascii=False)
    
    # Update control file
    with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_scrape": datetime.now().isoformat(),
            "lead_count": len(formatted_leads),
            "status": "ready_for_verification",
            "pipeline_stage": "raw_leads"
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved {len(formatted_leads)} real people to raw_leads.json")
    return formatted_leads

async def main():
    """Main function to run live LinkedIn scraper"""
    logger.info("🚀 Starting Live LinkedIn Scraper")
    
    scraper = LiveLinkedInScraper()
    
    try:
        # Start browser with cookies
        await scraper.start_browser()
        
        # Search for CEOs in Montreal
        max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '10'))
        logger.info(f"🎯 Searching for {max_leads} CEOs in Montreal...")
        
        leads = await scraper.search_linkedin_ceos(
            location="Montreal, Quebec, Canada",
            max_results=max_leads
        )
        
        if not leads:
            logger.error("❌ No leads found from LinkedIn search")
            return
        
        logger.info(f"✅ Successfully scraped {len(leads)} fresh LinkedIn profiles:")
        for lead in leads:
            logger.info(f"   📋 {lead['name']} - {lead.get('title', 'N/A')} at {lead.get('company', 'N/A')}")
            logger.info(f"   🔗 {lead['linkedin_url']}")
        
        # Save the leads
        saved_leads = save_raw_leads(leads)
        
        logger.info(f"✅ Live scraping completed successfully - {len(saved_leads)} leads ready for verification")
        
    except Exception as e:
        logger.error(f"❌ Error in live scraper: {str(e)}")
        raise
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())