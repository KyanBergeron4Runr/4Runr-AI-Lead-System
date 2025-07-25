#!/usr/bin/env python3
"""
Real LinkedIn Scraper using Playwright

This module handles actual LinkedIn scraping using Playwright with proper
authentication and search functionality.
"""

import os
import json
import time
import logging
import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('linkedin-scraper')

class LinkedInScraper:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.search_url = os.getenv('SEARCH_URL')
        
        if not all([self.email, self.password, self.search_url]):
            raise ValueError("Missing required environment variables: LINKEDIN_EMAIL, LINKEDIN_PASSWORD, SEARCH_URL")
        
        self.browser = None
        self.page = None
        self.is_logged_in = False
        
    async def start_browser(self):
        """Start the browser and create a new page"""
        playwright = await async_playwright().start()
        
        # Use headless mode for production, set to False for debugging
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        # Create a new context with realistic user agent
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        
        # Set realistic timeouts
        self.page.set_default_timeout(30000)  # 30 seconds
        
        logger.info("Browser started successfully")
    
    async def login(self):
        """Login to LinkedIn"""
        try:
            logger.info("Navigating to LinkedIn login page")
            await self.page.goto('https://www.linkedin.com/login')
            
            # Wait for login form to load
            await self.page.wait_for_selector('#username', timeout=10000)
            
            # Fill in credentials
            await self.page.fill('#username', self.email)
            await self.page.fill('#password', self.password)
            
            logger.info("Submitting login form")
            await self.page.click('button[type="submit"]')
            
            # Wait for login to complete - check for feed or challenge
            try:
                # Wait for either the feed (successful login) or challenge page
                await self.page.wait_for_selector('main', timeout=15000)
                
                # Check if we're on a challenge page
                current_url = self.page.url
                if 'challenge' in current_url or 'checkpoint' in current_url:
                    logger.error("LinkedIn security challenge detected. Manual intervention required.")
                    return False
                
                # Check if we're on the feed (successful login)
                if 'feed' in current_url or 'mynetwork' in current_url:
                    logger.info("Successfully logged into LinkedIn")
                    self.is_logged_in = True
                    return True
                
                # If we're somewhere else, try to navigate to feed to verify login
                await self.page.goto('https://www.linkedin.com/feed/')
                await self.page.wait_for_selector('main', timeout=10000)
                
                logger.info("Successfully logged into LinkedIn")
                self.is_logged_in = True
                return True
                
            except PlaywrightTimeoutError:
                logger.error("Login failed - timeout waiting for main content")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    async def navigate_to_search(self):
        """Navigate to the specified search URL"""
        try:
            logger.info(f"Navigating to search URL: {self.search_url}")
            await self.page.goto(self.search_url)
            
            # Wait for search results to load
            await self.page.wait_for_selector('.search-results-container, .search-results__list, .reusable-search__result-container', timeout=15000)
            
            # Add random delay to appear more human-like
            await asyncio.sleep(random.uniform(2, 4))
            
            logger.info("Successfully navigated to search results")
            return True
            
        except PlaywrightTimeoutError:
            logger.error("Failed to load search results - timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to search: {str(e)}")
            return False
    
    async def extract_leads_from_page(self):
        """Extract lead data from the current search results page"""
        leads = []
        
        try:
            # Different selectors for different LinkedIn search types
            selectors = [
                '.reusable-search__result-container',  # Standard search
                '.search-results__list .search-result',  # Alternative search
                '.search-results-container .search-result__wrapper',  # Sales Navigator
                '.artdeco-entity-lockup'  # Another common pattern
            ]
            
            result_containers = None
            for selector in selectors:
                try:
                    result_containers = await self.page.query_selector_all(selector)
                    if result_containers:
                        logger.info(f"Found {len(result_containers)} results using selector: {selector}")
                        break
                except:
                    continue
            
            if not result_containers:
                logger.warning("No search result containers found")
                return leads
            
            for container in result_containers:
                try:
                    lead_data = await self.extract_lead_from_container(container)
                    if lead_data:
                        leads.append(lead_data)
                        logger.info(f"Extracted lead: {lead_data['name']} from {lead_data['company']}")
                    
                    # Add small delay between extractions
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.warning(f"Failed to extract lead from container: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(leads)} leads from current page")
            return leads
            
        except Exception as e:
            logger.error(f"Failed to extract leads from page: {str(e)}")
            return leads
    
    async def extract_lead_from_container(self, container):
        """Extract lead data from a single result container"""
        try:
            # Extract name
            name_selectors = [
                '.entity-result__title-text a span[aria-hidden="true"]',
                '.search-result__title a',
                '.actor-name',
                '.name a',
                'h3 a span[aria-hidden="true"]',
                '.artdeco-entity-lockup__title a'
            ]
            
            name = await self.get_text_from_selectors(container, name_selectors)
            if not name:
                return None
            
            # Extract LinkedIn URL
            linkedin_url = await self.get_linkedin_url(container)
            if not linkedin_url:
                return None
            
            # Extract title
            title_selectors = [
                '.entity-result__primary-subtitle',
                '.search-result__snippets',
                '.subline-level-1',
                '.artdeco-entity-lockup__subtitle'
            ]
            
            title = await self.get_text_from_selectors(container, title_selectors)
            
            # Extract company
            company_selectors = [
                '.entity-result__secondary-subtitle',
                '.search-result__snippets .search-result__snippet-text',
                '.subline-level-2',
                '.artdeco-entity-lockup__caption'
            ]
            
            company = await self.get_text_from_selectors(container, company_selectors)
            
            # Clean up extracted data
            name = self.clean_text(name)
            title = self.clean_text(title) if title else ""
            company = self.clean_text(company) if company else ""
            
            # Create lead object in the required format
            lead = {
                "name": name,
                "title": title,
                "company": company,
                "linkedin_url": linkedin_url,
                "email": "",  # Left blank for enricher
                "Needs Enrichment": True,
                "Status": "New",
                "Created At": datetime.now().isoformat(),
                "Updated At": datetime.now().isoformat()
            }
            
            return lead
            
        except Exception as e:
            logger.warning(f"Failed to extract lead data: {str(e)}")
            return None
    
    async def get_text_from_selectors(self, container, selectors):
        """Try multiple selectors to get text content"""
        for selector in selectors:
            try:
                element = await container.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return None
    
    async def get_linkedin_url(self, container):
        """Extract LinkedIn profile URL from container"""
        url_selectors = [
            '.entity-result__title-text a',
            '.search-result__title a',
            '.actor-name a',
            '.name a',
            'h3 a',
            '.artdeco-entity-lockup__title a'
        ]
        
        for selector in url_selectors:
            try:
                element = await container.query_selector(selector)
                if element:
                    href = await element.get_attribute('href')
                    if href and 'linkedin.com/in/' in href:
                        # Clean up the URL (remove tracking parameters)
                        if '?' in href:
                            href = href.split('?')[0]
                        return href
            except:
                continue
        return None
    
    def clean_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        
        # Remove common LinkedIn artifacts
        text = text.replace('LinkedIn Member', '').strip()
        
        return text
    
    async def scrape_leads(self, max_pages=3, max_leads=50):
        """Main method to scrape leads from LinkedIn search"""
        all_leads = []
        
        try:
            if not self.is_logged_in:
                logger.error("Not logged in to LinkedIn")
                return all_leads
            
            # Navigate to search results
            if not await self.navigate_to_search():
                return all_leads
            
            page_count = 0
            
            while page_count < max_pages and len(all_leads) < max_leads:
                logger.info(f"Scraping page {page_count + 1}")
                
                # Extract leads from current page
                page_leads = await self.extract_leads_from_page()
                all_leads.extend(page_leads)
                
                logger.info(f"Total leads collected: {len(all_leads)}")
                
                # Check if we have enough leads
                if len(all_leads) >= max_leads:
                    all_leads = all_leads[:max_leads]
                    break
                
                # Try to go to next page
                page_count += 1
                if page_count < max_pages:
                    if not await self.go_to_next_page():
                        logger.info("No more pages available")
                        break
                    
                    # Wait between pages
                    await asyncio.sleep(random.uniform(3, 6))
            
            logger.info(f"Scraping completed. Total leads: {len(all_leads)}")
            return all_leads
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return all_leads
    
    async def go_to_next_page(self):
        """Navigate to the next page of search results"""
        try:
            # Look for next page button
            next_selectors = [
                'button[aria-label="Next"]',
                '.artdeco-pagination__button--next',
                '.search-results__pagination-next-button'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = await self.page.query_selector(selector)
                    if next_button:
                        # Check if button is enabled
                        is_disabled = await next_button.get_attribute('disabled')
                        if not is_disabled:
                            await next_button.click()
                            
                            # Wait for new results to load
                            await asyncio.sleep(random.uniform(2, 4))
                            await self.page.wait_for_load_state('networkidle', timeout=10000)
                            
                            logger.info("Successfully navigated to next page")
                            return True
                except:
                    continue
            
            logger.info("No next page button found or available")
            return False
            
        except Exception as e:
            logger.warning(f"Failed to navigate to next page: {str(e)}")
            return False
    
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

async def scrape_linkedin_leads():
    """Main function to scrape LinkedIn leads"""
    scraper = None
    
    try:
        # Initialize scraper
        scraper = LinkedInScraper()
        
        # Start browser
        await scraper.start_browser()
        
        # Login to LinkedIn
        if not await scraper.login():
            logger.error("Failed to login to LinkedIn")
            return []
        
        # Scrape leads
        max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '20'))
        max_pages = int(os.getenv('MAX_PAGES_PER_RUN', '3'))
        
        leads = await scraper.scrape_leads(max_pages=max_pages, max_leads=max_leads)
        
        logger.info(f"Successfully scraped {len(leads)} leads")
        return leads
        
    except Exception as e:
        logger.error(f"Error in LinkedIn scraping: {str(e)}")
        return []
        
    finally:
        if scraper:
            await scraper.close()

if __name__ == "__main__":
    # Run the scraper
    leads = asyncio.run(scrape_linkedin_leads())
    print(f"Scraped {len(leads)} leads")
    for lead in leads:
        print(f"- {lead['name']} ({lead['title']}) at {lead['company']}")