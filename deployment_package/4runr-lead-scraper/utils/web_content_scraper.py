#!/usr/bin/env python3
"""
Website Content Scraper Agent

Comprehensive web scraping engine for extracting meaningful business signals
from company websites. Uses Playwright with BeautifulSoup fallback for
reliable content extraction.
"""

import os
import sys
import time
import logging
import asyncio
import requests
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

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    BeautifulSoup = None

logger = logging.getLogger('web-content-scraper')

class WebContentScraper:
    """
    Website content scraper for extracting business information from company websites.
    Uses Playwright as primary method with BeautifulSoup fallback.
    """
    
    def __init__(self):
        """Initialize the web content scraper."""
        # Configuration
        self.timeout = 30000  # 30 seconds
        self.navigation_timeout = 15000  # 15 seconds
        self.max_retries = 3
        self.retry_delay = 2
        
        # Content filtering
        self.min_content_length = 100
        self.max_content_length = 50000
        
        # User agents for requests fallback
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        logger.info("🌐 Web Content Scraper initialized")
        logger.info(f"📊 Playwright available: {PLAYWRIGHT_AVAILABLE}")
        logger.info(f"📊 BeautifulSoup available: {BEAUTIFULSOUP_AVAILABLE}")
    
    async def scrape_website(self, website_url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape website content using Playwright with fallback to requests.
        
        Args:
            website_url: URL to scrape
            lead_context: Optional context (lead name, email domain, etc.)
            
        Returns:
            Dictionary with scraped content and metadata
        """
        logger.info(f"🌐 Scraping website: {website_url}")
        
        # Validate and clean URL
        clean_url = self._clean_url(website_url)
        if not clean_url:
            return self._create_error_result("Invalid URL format", website_url)
        
        # Try Playwright first
        if PLAYWRIGHT_AVAILABLE:
            result = await self._scrape_with_playwright(clean_url, lead_context)
            if result['success']:
                return result
            else:
                logger.warning(f"⚠️ Playwright scraping failed: {result.get('error')}")
        
        # Fallback to requests + BeautifulSoup
        if BEAUTIFULSOUP_AVAILABLE:
            result = await self._scrape_with_requests(clean_url, lead_context)
            if result['success']:
                return result
            else:
                logger.warning(f"⚠️ Requests scraping failed: {result.get('error')}")
        
        # Both methods failed
        return self._create_error_result("All scraping methods failed", clean_url)
    
    def scrape_website_sync(self, website_url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for website scraping.
        
        Args:
            website_url: URL to scrape
            lead_context: Optional context
            
        Returns:
            Dictionary with scraped content and metadata
        """
        try:
            return asyncio.run(self.scrape_website(website_url, lead_context))
        except Exception as e:
            logger.error(f"❌ Sync scraping failed: {str(e)}")
            return self._create_error_result(str(e), website_url)
    
    async def _scrape_with_playwright(self, url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape website using Playwright.
        
        Args:
            url: URL to scrape
            lead_context: Optional context
            
        Returns:
            Scraping result dictionary
        """
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-extensions',
                        '--disable-plugins',
                    ]
                )
                
                try:
                    # Create page
                    page = await browser.new_page()
                    
                    # Set timeout
                    page.set_default_timeout(self.timeout)
                    page.set_default_navigation_timeout(self.navigation_timeout)
                    
                    # Set user agent
                    await page.set_extra_http_headers({
                        'User-Agent': self.user_agents[0]
                    })
                    
                    # Navigate to page
                    response = await page.goto(url, wait_until='domcontentloaded')
                    
                    if not response or response.status >= 400:
                        return self._create_error_result(f"HTTP {response.status if response else 'No response'}", url)
                    
                    # Wait for content to load
                    await asyncio.sleep(2)
                    
                    # Extract content
                    content = await self._extract_content_playwright(page, url)
                    
                    return content
                
                finally:
                    await browser.close()
        
        except Exception as e:
            logger.error(f"❌ Playwright scraping error: {str(e)}")
            return self._create_error_result(str(e), url)
    
    async def _scrape_with_requests(self, url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape website using requests + BeautifulSoup fallback.
        
        Args:
            url: URL to scrape
            lead_context: Optional context
            
        Returns:
            Scraping result dictionary
        """
        try:
            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            
            if response.status_code >= 400:
                return self._create_error_result(f"HTTP {response.status_code}", url)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            content = self._extract_content_beautifulsoup(soup, url)
            
            return content
        
        except Exception as e:
            logger.error(f"❌ Requests scraping error: {str(e)}")
            return self._create_error_result(str(e), url)
    
    async def _extract_content_playwright(self, page: Page, url: str) -> Dict[str, Any]:
        """
        Extract content from Playwright page.
        
        Args:
            page: Playwright page instance
            url: Original URL
            
        Returns:
            Extracted content dictionary
        """
        try:
            # Get page title
            title = await page.title()
            
            # Get meta description
            meta_desc_element = await page.query_selector('meta[name="description"]')
            meta_description = ""
            if meta_desc_element:
                meta_description = await meta_desc_element.get_attribute('content') or ""
            
            # Remove unwanted elements
            await self._remove_unwanted_elements_playwright(page)
            
            # Get main content
            text_content = await self._extract_main_content_playwright(page)
            
            # Validate content
            if not self._is_valid_content(text_content, url):
                return self._create_error_result("Content appears to be empty or invalid", url)
            
            # Create result
            result = {
                'text': text_content,
                'meta_description': meta_description.strip(),
                'page_title': title.strip(),
                'success': True,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'method': 'playwright',
                'content_length': len(text_content)
            }
            
            logger.info(f"✅ Playwright scraping successful: {len(text_content)} chars")
            return result
        
        except Exception as e:
            logger.error(f"❌ Playwright content extraction error: {str(e)}")
            return self._create_error_result(str(e), url)
    
    def _extract_content_beautifulsoup(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract content from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Original URL
            
        Returns:
            Extracted content dictionary
        """
        try:
            # Get page title
            title_element = soup.find('title')
            title = title_element.get_text().strip() if title_element else ""
            
            # Get meta description
            meta_desc_element = soup.find('meta', attrs={'name': 'description'})
            meta_description = ""
            if meta_desc_element:
                meta_description = meta_desc_element.get('content', '').strip()
            
            # Remove unwanted elements
            self._remove_unwanted_elements_beautifulsoup(soup)
            
            # Get main content
            text_content = self._extract_main_content_beautifulsoup(soup)
            
            # Validate content
            if not self._is_valid_content(text_content, url):
                return self._create_error_result("Content appears to be empty or invalid", url)
            
            # Create result
            result = {
                'text': text_content,
                'meta_description': meta_description,
                'page_title': title,
                'success': True,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'method': 'requests+beautifulsoup',
                'content_length': len(text_content)
            }
            
            logger.info(f"✅ BeautifulSoup scraping successful: {len(text_content)} chars")
            return result
        
        except Exception as e:
            logger.error(f"❌ BeautifulSoup content extraction error: {str(e)}")
            return self._create_error_result(str(e), url)
    
    async def _remove_unwanted_elements_playwright(self, page: Page):
        """Remove unwanted elements from Playwright page."""
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.nav', '.navbar', '.navigation', '.menu',
            '.header', '.footer', '.sidebar', '.aside',
            '.cookie', '.popup', '.modal', '.overlay',
            '.advertisement', '.ad', '.ads',
            'script', 'style', 'noscript',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
        ]
        
        for selector in unwanted_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    await element.evaluate('element => element.remove()')
            except:
                continue
    
    def _remove_unwanted_elements_beautifulsoup(self, soup: BeautifulSoup):
        """Remove unwanted elements from BeautifulSoup object."""
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside',
            'script', 'style', 'noscript'
        ]
        
        unwanted_classes = [
            'nav', 'navbar', 'navigation', 'menu',
            'header', 'footer', 'sidebar', 'aside',
            'cookie', 'popup', 'modal', 'overlay',
            'advertisement', 'ad', 'ads'
        ]
        
        # Remove by tag
        for selector in unwanted_selectors:
            for element in soup.find_all(selector):
                element.decompose()
        
        # Remove by class
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=re.compile(class_name, re.I)):
                element.decompose()
        
        # Remove by role
        for element in soup.find_all(attrs={'role': ['navigation', 'banner', 'contentinfo']}):
            element.decompose()
    
    async def _extract_main_content_playwright(self, page: Page) -> str:
        """Extract main content from Playwright page."""
        # Try to find main content area
        main_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '.page-content',
            '#main',
            '#content',
            'article',
            '.container'
        ]
        
        for selector in main_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > self.min_content_length:
                        return self._clean_text(text)
            except:
                continue
        
        # Fallback to body
        try:
            body = await page.query_selector('body')
            if body:
                text = await body.inner_text()
                return self._clean_text(text)
        except:
            pass
        
        return ""
    
    def _extract_main_content_beautifulsoup(self, soup: BeautifulSoup) -> str:
        """Extract main content from BeautifulSoup object."""
        # Try to find main content area
        main_selectors = [
            'main',
            '[role="main"]',
            {'class': re.compile(r'main|content', re.I)},
            {'id': re.compile(r'main|content', re.I)},
            'article'
        ]
        
        for selector in main_selectors:
            if isinstance(selector, dict):
                element = soup.find(attrs=selector)
            else:
                element = soup.find(selector)
            
            if element:
                text = element.get_text()
                if text and len(text.strip()) > self.min_content_length:
                    return self._clean_text(text)
        
        # Fallback to body
        body = soup.find('body')
        if body:
            text = body.get_text()
            return self._clean_text(text)
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise
        noise_patterns = [
            r'Cookie Policy.*?Accept',
            r'This website uses cookies.*?(?:Accept|OK|Continue)',
            r'We use cookies.*?(?:Accept|OK|Continue)',
            r'Subscribe to.*?newsletter',
            r'Follow us on.*?(?:Facebook|Twitter|LinkedIn|Instagram)',
            r'Copyright.*?\d{4}',
            r'All rights reserved',
            r'Privacy Policy.*?Terms',
            r'Terms.*?Privacy',
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Trim and limit length
        text = text.strip()
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."
        
        return text
    
    def _is_valid_content(self, text: str, url: str) -> bool:
        """Validate if extracted content is meaningful."""
        if not text or len(text.strip()) < self.min_content_length:
            logger.warning(f"⚠️ Content too short for {url}: {len(text) if text else 0} chars")
            return False
        
        # Check for error page indicators
        error_indicators = [
            '404', 'not found', 'page not found',
            'error', 'oops', 'something went wrong',
            'under construction', 'coming soon',
            'maintenance', 'temporarily unavailable'
        ]
        
        text_lower = text.lower()
        error_count = sum(1 for indicator in error_indicators if indicator in text_lower)
        
        if error_count >= 2:
            logger.warning(f"⚠️ Content appears to be error page for {url}")
            return False
        
        return True
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate URL."""
        if not url or not isinstance(url, str):
            return None
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                return url
        except Exception:
            pass
        
        return None
    
    def _create_error_result(self, error: str, url: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            'text': '',
            'meta_description': '',
            'page_title': '',
            'success': False,
            'error': error,
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'method': 'failed',
            'content_length': 0
        }


# Convenience functions
async def scrape_website_content(website_url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Async function to scrape website content.
    
    Args:
        website_url: URL to scrape
        lead_context: Optional context
        
    Returns:
        Scraping result dictionary
    """
    try:
        scraper = WebContentScraper()
        return await scraper.scrape_website(website_url, lead_context)
    except Exception as e:
        logger.error(f"❌ Website scraping failed: {str(e)}")
        return {
            'text': '',
            'meta_description': '',
            'page_title': '',
            'success': False,
            'error': str(e),
            'url': website_url,
            'scraped_at': datetime.now().isoformat(),
            'method': 'failed',
            'content_length': 0
        }


def scrape_website_content_sync(website_url: str, lead_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Synchronous function to scrape website content.
    
    Args:
        website_url: URL to scrape
        lead_context: Optional context
        
    Returns:
        Scraping result dictionary
    """
    try:
        scraper = WebContentScraper()
        return scraper.scrape_website_sync(website_url, lead_context)
    except Exception as e:
        logger.error(f"❌ Sync website scraping failed: {str(e)}")
        return {
            'text': '',
            'meta_description': '',
            'page_title': '',
            'success': False,
            'error': str(e),
            'url': website_url,
            'scraped_at': datetime.now().isoformat(),
            'method': 'failed',
            'content_length': 0
        }


if __name__ == "__main__":
    # Test the web content scraper
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Web Content Scraper')
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('--sync', action='store_true', help='Use synchronous scraping')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.sync:
        # Synchronous scraping
        result = scrape_website_content_sync(args.url)
    else:
        # Asynchronous scraping
        result = asyncio.run(scrape_website_content(args.url))
    
    # Display results
    print(f"\n🌐 Scraping Results for: {args.url}")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Method: {result['method']}")
    print(f"Title: {result['page_title']}")
    print(f"Meta Description: {result['meta_description']}")
    print(f"Content Length: {result['content_length']} chars")
    
    if result['success']:
        print(f"\nContent Preview:")
        print("-" * 40)
        print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
    else:
        print(f"Error: {result['error']}")