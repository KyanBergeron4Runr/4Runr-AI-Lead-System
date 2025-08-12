#!/usr/bin/env python3
"""
Google Website Scraper (Playwright Agent)

Fallback Google search agent for discovering company websites when SerpAPI
doesn't provide them. Uses Playwright for automated Google search with
anti-detection measures.
"""

import os
import sys
import time
import logging
import random
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re

# Add the project root to the path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None

logger = logging.getLogger('google-scraper')

class GoogleWebsiteScraper:
    """
    Google search fallback agent for website discovery using Playwright.
    Designed to find company websites when SerpAPI doesn't provide them.
    """
    
    def __init__(self):
        """Initialize the Google Website Scraper."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install with: pip install playwright && playwright install"
            )
        
        # Configuration
        self.search_domains = ['.com', '.ca', '.org', '.net', '.co', '.io']
        self.max_retries = 3
        self.retry_delay = 2
        self.page_timeout = 30000  # 30 seconds
        self.navigation_timeout = 15000  # 15 seconds
        
        # Anti-detection settings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        logger.info("🔍 Google Website Scraper initialized")
        logger.info(f"📍 Search domains: {', '.join(self.search_domains)}")
    
    async def search_company_website(self, full_name: str, company_name: str = None) -> Optional[str]:
        """
        Search for company website using Google search.
        
        Args:
            full_name: Full name of the person
            company_name: Company name (optional)
            
        Returns:
            Website URL if found, None otherwise
        """
        if not full_name:
            logger.warning("⚠️ No full name provided for Google search")
            return None
        
        # Build search query
        query = self._build_search_query(full_name, company_name)
        logger.info(f"🔍 Google search query: {query}")
        
        try:
            async with async_playwright() as p:
                # Launch browser with anti-detection settings
                browser = await self._launch_browser(p)
                
                try:
                    # Create new page
                    page = await browser.new_page()
                    
                    # Set random user agent
                    await page.set_extra_http_headers({
                        'User-Agent': random.choice(self.user_agents)
                    })
                    
                    # Perform Google search
                    website_url = await self._perform_google_search(page, query)
                    
                    if website_url:
                        logger.info(f"✅ Website found via Google search: {website_url}")
                        return website_url
                    else:
                        logger.info("⚠️ No website found via Google search")
                        return None
                
                finally:
                    await browser.close()
        
        except Exception as e:
            logger.error(f"❌ Google search failed: {str(e)}")
            return None
    
    def search_company_website_sync(self, full_name: str, company_name: str = None) -> Optional[str]:
        """
        Synchronous wrapper for Google website search.
        
        Args:
            full_name: Full name of the person
            company_name: Company name (optional)
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            return asyncio.run(self.search_company_website(full_name, company_name))
        except Exception as e:
            logger.error(f"❌ Sync Google search failed: {str(e)}")
            return None
    
    def _build_search_query(self, full_name: str, company_name: str = None) -> str:
        """
        Build Google search query for website discovery.
        
        Args:
            full_name: Full name of the person
            company_name: Company name (optional)
            
        Returns:
            Formatted search query
        """
        # Clean and format names
        full_name = full_name.strip().replace('"', '')
        
        if company_name:
            company_name = company_name.strip().replace('"', '')
            # Build query with both name and company
            base_query = f'"{full_name}" "{company_name}"'
        else:
            # Build query with just name
            base_query = f'"{full_name}"'
        
        # Add site restrictions for common business domains
        site_restrictions = ' OR '.join([f'site:{domain}' for domain in self.search_domains])
        
        # Final query format
        query = f'{base_query} ({site_restrictions})'
        
        return query
    
    async def _launch_browser(self, playwright) -> Browser:
        """
        Launch browser with anti-detection settings.
        
        Args:
            playwright: Playwright instance
            
        Returns:
            Browser instance
        """
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
                '--disable-javascript',  # We don't need JS for basic search
            ]
        )
        
        return browser
    
    async def _perform_google_search(self, page: Page, query: str) -> Optional[str]:
        """
        Perform Google search and extract website URL.
        
        Args:
            page: Playwright page instance
            query: Search query
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            # Navigate to Google
            await page.goto('https://www.google.com', timeout=self.navigation_timeout)
            
            # Wait for search box and enter query
            await page.wait_for_selector('input[name="q"]', timeout=5000)
            await page.fill('input[name="q"]', query)
            
            # Submit search
            await page.press('input[name="q"]', 'Enter')
            
            # Wait for results
            await page.wait_for_selector('#search', timeout=10000)
            
            # Add random delay to appear more human-like
            await asyncio.sleep(random.uniform(1, 3))
            
            # Extract website URL from first organic result
            website_url = await self._extract_website_from_results(page)
            
            return website_url
        
        except Exception as e:
            logger.error(f"❌ Google search execution failed: {str(e)}")
            return None
    
    async def _extract_website_from_results(self, page: Page) -> Optional[str]:
        """
        Extract website URL from Google search results.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            # Wait for search results
            await page.wait_for_selector('#search', timeout=5000)
            
            # Get all organic search result links (exclude ads)
            # Google search results are typically in divs with data-ved attribute
            result_selectors = [
                '#search .g h3 a',  # Standard result links
                '#search .yuRUbf a',  # Alternative result structure
                '#search [data-ved] h3 a',  # Results with data-ved
            ]
            
            for selector in result_selectors:
                try:
                    # Get all links matching this selector
                    links = await page.query_selector_all(selector)
                    
                    for link in links:
                        href = await link.get_attribute('href')
                        
                        if href and self._is_valid_company_website(href):
                            # Clean and validate the URL
                            clean_url = self._clean_url(href)
                            if clean_url:
                                logger.debug(f"✅ Found potential website: {clean_url}")
                                return clean_url
                
                except Exception as e:
                    logger.debug(f"⚠️ Selector {selector} failed: {str(e)}")
                    continue
            
            # If no results found with standard selectors, try alternative approach
            logger.debug("🔍 Trying alternative result extraction")
            return await self._extract_website_alternative(page)
        
        except Exception as e:
            logger.error(f"❌ Website extraction from results failed: {str(e)}")
            return None
    
    async def _extract_website_alternative(self, page: Page) -> Optional[str]:
        """
        Alternative method to extract website from search results.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Website URL if found, None otherwise
        """
        try:
            # Get all links on the page
            all_links = await page.query_selector_all('a[href]')
            
            for link in all_links:
                href = await link.get_attribute('href')
                
                if href and self._is_valid_company_website(href):
                    # Check if this looks like a search result (not Google internal link)
                    if not self._is_google_internal_link(href):
                        clean_url = self._clean_url(href)
                        if clean_url:
                            logger.debug(f"✅ Found website via alternative method: {clean_url}")
                            return clean_url
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Alternative website extraction failed: {str(e)}")
            return None
    
    def _is_valid_company_website(self, url: str) -> bool:
        """
        Check if URL looks like a valid company website.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears to be a valid company website
        """
        if not url or not isinstance(url, str):
            return False
        
        # Skip Google internal links
        if self._is_google_internal_link(url):
            return False
        
        # Skip common non-company domains
        skip_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'wikipedia.org', 'crunchbase.com', 'bloomberg.com',
            'reuters.com', 'forbes.com', 'techcrunch.com', 'businesswire.com'
        ]
        
        url_lower = url.lower()
        if any(domain in url_lower for domain in skip_domains):
            return False
        
        # Check if URL has a valid business domain extension
        parsed = urlparse(url)
        if parsed.netloc:
            domain = parsed.netloc.lower()
            if any(domain.endswith(ext) for ext in self.search_domains):
                return True
        
        return False
    
    def _is_google_internal_link(self, url: str) -> bool:
        """
        Check if URL is a Google internal link.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is Google internal
        """
        google_domains = [
            'google.com', 'google.ca', 'google.co.uk', 'google.fr',
            'googleusercontent.com', 'googlesyndication.com', 'googleadservices.com'
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in google_domains)
    
    def _clean_url(self, url: str) -> Optional[str]:
        """
        Clean and validate URL.
        
        Args:
            url: Raw URL from search results
            
        Returns:
            Cleaned URL or None if invalid
        """
        if not url:
            return None
        
        # Handle Google redirect URLs
        if '/url?q=' in url:
            # Extract actual URL from Google redirect
            import urllib.parse
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if 'q' in parsed:
                url = parsed['q'][0]
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                # Additional validation: check if domain has valid extension
                domain = parsed.netloc.lower()
                if any(domain.endswith(ext) for ext in self.search_domains):
                    return url
        except Exception:
            pass
        
        return None


# Convenience functions for integration
async def search_company_website_google(full_name: str, company_name: str = None) -> Optional[str]:
    """
    Async function to search for company website using Google.
    
    Args:
        full_name: Full name of the person
        company_name: Company name (optional)
        
    Returns:
        Website URL if found, None otherwise
    """
    try:
        scraper = GoogleWebsiteScraper()
        return await scraper.search_company_website(full_name, company_name)
    except Exception as e:
        logger.error(f"❌ Google website search failed: {str(e)}")
        return None


def search_company_website_google_sync(full_name: str, company_name: str = None) -> Optional[str]:
    """
    Synchronous function to search for company website using Google.
    
    Args:
        full_name: Full name of the person
        company_name: Company name (optional)
        
    Returns:
        Website URL if found, None otherwise
    """
    try:
        scraper = GoogleWebsiteScraper()
        return scraper.search_company_website_sync(full_name, company_name)
    except Exception as e:
        logger.error(f"❌ Sync Google website search failed: {str(e)}")
        return None


if __name__ == "__main__":
    # Test the Google scraper
    import asyncio
    
    async def test_google_scraper():
        """Test the Google website scraper."""
        test_cases = [
            ("John Smith", "TechCorp"),
            ("Jane Doe", "StartupXYZ"),
            ("Mike Johnson", None),  # No company name
        ]
        
        scraper = GoogleWebsiteScraper()
        
        for full_name, company_name in test_cases:
            print(f"\n🧪 Testing: {full_name}" + (f" at {company_name}" if company_name else ""))
            
            website = await scraper.search_company_website(full_name, company_name)
            
            if website:
                print(f"✅ Found website: {website}")
            else:
                print("⚠️ No website found")
    
    # Run test if Playwright is available
    if PLAYWRIGHT_AVAILABLE:
        asyncio.run(test_google_scraper())
    else:
        print("❌ Playwright not available. Install with: pip install playwright && playwright install")