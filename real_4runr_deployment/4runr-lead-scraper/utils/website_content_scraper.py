#!/usr/bin/env python3
"""
Website Content Scraper Agent

Advanced website content scraper that extracts company information from discovered websites.
Uses Playwright for dynamic content scraping with intelligent page prioritization and content cleaning.
"""

import os
import re
import time
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    from bs4 import BeautifulSoup
except ImportError:
    async_playwright = None
    Browser = None
    Page = None
    PlaywrightTimeoutError = Exception
    BeautifulSoup = None

logger = logging.getLogger('website-content-scraper')

class WebsiteContentScraper:
    """
    Advanced website content scraper for extracting company information.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize website content scraper.
        
        Args:
            headless: Run browser in headless mode
            timeout: Timeout for page operations in milliseconds
        """
        if async_playwright is None:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")
        
        if BeautifulSoup is None:
            raise ImportError("BeautifulSoup not installed. Run: pip install beautifulsoup4")
        
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None
        
        # Page prioritization configuration
        self.priority_pages = [
            '/about',
            '/about-us',
            '/services',
            '/what-we-do',
            '/home',
            '/',
            '/contact',
            '/contact-us',
            '/company',
            '/our-story',
            '/mission'
        ]
        
        # Content cleaning configuration
        self.content_selectors_to_remove = [
            'nav', 'header', 'footer', 'aside',
            '.navigation', '.nav', '.menu',
            '.header', '.footer', '.sidebar',
            '.cookie-banner', '.cookie-notice',
            '.popup', '.modal', '.overlay',
            '.advertisement', '.ads', '.ad',
            '.social-media', '.social-links',
            '.breadcrumb', '.breadcrumbs',
            'script', 'style', 'noscript'
        ]
        
        # Content extraction selectors
        self.content_selectors = [
            'main', '.main', '#main',
            '.content', '#content', '.main-content',
            'article', '.article',
            '.page-content', '.entry-content',
            '.container', '.wrapper'
        ]
        
        logger.info("🌐 Website Content Scraper initialized")
        logger.info(f"⚙️ Headless mode: {headless}, Timeout: {timeout}ms")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
    
    async def start_browser(self):
        """Start the Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create a new page with realistic user agent
            self.page = await self.browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Set viewport
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            logger.info("✅ Browser started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser: {str(e)}")
            raise
    
    async def close_browser(self):
        """Close the browser and cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            logger.info("✅ Browser closed successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Error closing browser: {str(e)}")
    
    async def scrape_website_content(self, website_url: str) -> Dict[str, Any]:
        """
        Scrape comprehensive content from a website.
        
        Args:
            website_url: Website URL to scrape
            
        Returns:
            Dictionary with scraped content and metadata
        """
        if not self.page:
            raise RuntimeError("Browser not started. Use async context manager or call start_browser()")
        
        logger.info(f"🌐 Scraping website content: {website_url}")
        
        result = {
            'website_url': website_url,
            'scraped_at': datetime.now().isoformat(),
            'success': False,
            'pages_scraped': [],
            'content': {},
            'raw_content': {},
            'errors': []
        }
        
        try:
            # Get prioritized pages to scrape
            pages_to_scrape = await self._get_pages_to_scrape(website_url)
            
            if not pages_to_scrape:
                logger.warning(f"⚠️ No pages found to scrape for {website_url}")
                result['errors'].append('No accessible pages found')
                return result
            
            logger.info(f"📋 Found {len(pages_to_scrape)} pages to scrape")
            
            # Scrape each page
            for page_url, page_type in pages_to_scrape:
                try:
                    logger.info(f"📄 Scraping {page_type} page: {page_url}")
                    
                    page_content = await self._scrape_single_page(page_url, page_type)
                    
                    if page_content['success']:
                        result['pages_scraped'].append({
                            'url': page_url,
                            'type': page_type,
                            'content_length': len(page_content['cleaned_content'])
                        })
                        
                        result['content'][page_type] = page_content['cleaned_content']
                        result['raw_content'][page_type] = page_content['raw_content']
                        
                        logger.info(f"✅ Successfully scraped {page_type} page ({len(page_content['cleaned_content'])} chars)")
                    else:
                        logger.warning(f"⚠️ Failed to scrape {page_type} page: {page_content['error']}")
                        result['errors'].append(f"{page_type}: {page_content['error']}")
                    
                    # Delay between pages to be respectful
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Failed to scrape {page_type} page: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    continue
            
            # Mark as successful if we scraped at least one page
            result['success'] = len(result['pages_scraped']) > 0
            
            if result['success']:
                logger.info(f"✅ Website scraping completed: {len(result['pages_scraped'])} pages scraped")
            else:
                logger.error(f"❌ Website scraping failed: no pages successfully scraped")
            
            return result
            
        except Exception as e:
            error_msg = f"Website scraping failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            return result
    
    async def _get_pages_to_scrape(self, website_url: str) -> List[Tuple[str, str]]:
        """
        Get prioritized list of pages to scrape.
        
        Args:
            website_url: Base website URL
            
        Returns:
            List of (page_url, page_type) tuples
        """
        pages_to_scrape = []
        
        try:
            # Parse base URL
            parsed_url = urlparse(website_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Test homepage first
            try:
                await self.page.goto(base_url, timeout=self.timeout)
                await self.page.wait_for_load_state('networkidle', timeout=10000)
                
                pages_to_scrape.append((base_url, 'home'))
                logger.info(f"✅ Homepage accessible: {base_url}")
                
            except Exception as e:
                logger.warning(f"⚠️ Homepage not accessible: {str(e)}")
                return []
            
            # Test priority pages
            for priority_path in self.priority_pages[1:]:  # Skip '/' as we already tested homepage
                try:
                    page_url = urljoin(base_url, priority_path)
                    
                    # Quick check if page exists
                    response = await self.page.goto(page_url, timeout=15000)
                    
                    if response and response.status == 200:
                        page_type = self._get_page_type_from_path(priority_path)
                        pages_to_scrape.append((page_url, page_type))
                        logger.debug(f"✅ Found {page_type} page: {page_url}")
                    else:
                        logger.debug(f"⚠️ Page not found: {page_url} (status: {response.status if response else 'no response'})")
                
                except Exception as e:
                    logger.debug(f"⚠️ Page not accessible: {priority_path} - {str(e)}")
                    continue
            
            # Fallback: if we only have homepage, try to find other pages from navigation
            if len(pages_to_scrape) == 1:
                logger.info("🔍 Only homepage found, attempting to discover other pages")
                discovered_pages = await self._discover_pages_from_navigation(base_url)
                pages_to_scrape.extend(discovered_pages)
            
            return pages_to_scrape
            
        except Exception as e:
            logger.error(f"❌ Failed to get pages to scrape: {str(e)}")
            return []
    
    async def _scrape_single_page(self, page_url: str, page_type: str) -> Dict[str, Any]:
        """
        Scrape content from a single page.
        
        Args:
            page_url: URL of the page to scrape
            page_type: Type of page (home, about, services, etc.)
            
        Returns:
            Dictionary with page content and metadata
        """
        result = {
            'url': page_url,
            'type': page_type,
            'success': False,
            'raw_content': '',
            'cleaned_content': '',
            'error': None
        }
        
        try:
            # Navigate to page
            response = await self.page.goto(page_url, timeout=self.timeout)
            
            if not response or response.status != 200:
                result['error'] = f"HTTP {response.status if response else 'no response'}"
                return result
            
            # Wait for content to load
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Get page content
            raw_html = await self.page.content()
            result['raw_content'] = raw_html
            
            # Clean and extract content
            cleaned_content = self._clean_and_extract_content(raw_html, page_type)
            result['cleaned_content'] = cleaned_content
            
            if cleaned_content.strip():
                result['success'] = True
                logger.debug(f"✅ Extracted {len(cleaned_content)} characters from {page_type} page")
            else:
                result['error'] = "No meaningful content extracted"
                logger.warning(f"⚠️ No meaningful content extracted from {page_type} page")
            
            return result
            
        except PlaywrightTimeoutError:
            result['error'] = "Page load timeout"
            logger.warning(f"⚠️ Page load timeout: {page_url}")
            return result
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Failed to scrape page {page_url}: {str(e)}")
            return result
    
    def _clean_and_extract_content(self, html_content: str, page_type: str) -> str:
        """
        Clean HTML content and extract meaningful text.
        
        Args:
            html_content: Raw HTML content
            page_type: Type of page for context-aware cleaning
            
        Returns:
            Cleaned text content
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for selector in self.content_selectors_to_remove:
                for element in soup.select(selector):
                    element.decompose()
            
            # Find main content area
            main_content = None
            
            # Try to find main content using selectors
            for selector in self.content_selectors:
                elements = soup.select(selector)
                if elements:
                    main_content = elements[0]
                    break
            
            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                main_content = soup
            
            # Extract text content
            text_content = main_content.get_text(separator=' ', strip=True)
            
            # Clean up text
            cleaned_text = self._clean_text_content(text_content)
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"❌ Content cleaning failed: {str(e)}")
            return ""
    
    def _clean_text_content(self, text: str) -> str:
        """
        Clean extracted text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise patterns
        noise_patterns = [
            r'Cookie\s+(?:Policy|Notice|Settings|Preferences)',
            r'Accept\s+(?:All\s+)?Cookies',
            r'Privacy\s+Policy',
            r'Terms\s+(?:of\s+)?(?:Service|Use)',
            r'Subscribe\s+to\s+(?:our\s+)?newsletter',
            r'Follow\s+us\s+on',
            r'Copyright\s+©?\s*\d{4}',
            r'All\s+rights\s+reserved',
            r'Skip\s+to\s+(?:main\s+)?content',
            r'Menu\s+Toggle',
            r'Search\s+for:?',
            r'Loading\.\.\.?',
            r'Please\s+enable\s+JavaScript'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        
        # Clean up spacing again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _get_page_type_from_path(self, path: str) -> str:
        """
        Determine page type from URL path.
        
        Args:
            path: URL path
            
        Returns:
            Page type string
        """
        path_lower = path.lower().strip('/')
        
        if 'about' in path_lower:
            return 'about'
        elif 'service' in path_lower or 'what-we-do' in path_lower:
            return 'services'
        elif 'contact' in path_lower:
            return 'contact'
        elif 'company' in path_lower or 'our-story' in path_lower:
            return 'company'
        elif 'mission' in path_lower:
            return 'mission'
        elif path_lower in ['', 'home', 'index']:
            return 'home'
        else:
            return 'other'
    
    async def _discover_pages_from_navigation(self, base_url: str) -> List[Tuple[str, str]]:
        """
        Discover additional pages from website navigation.
        
        Args:
            base_url: Base website URL
            
        Returns:
            List of discovered (page_url, page_type) tuples
        """
        discovered_pages = []
        
        try:
            # Go to homepage
            await self.page.goto(base_url, timeout=self.timeout)
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Look for navigation links
            nav_selectors = [
                'nav a', '.nav a', '.navigation a',
                '.menu a', '.main-menu a',
                'header a', '.header a'
            ]
            
            found_links = set()
            
            for selector in nav_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    
                    for link in links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if href and text:
                            # Clean and validate link
                            href = href.strip()
                            text = text.strip().lower()
                            
                            # Skip external links, anchors, and irrelevant links
                            if (href.startswith('http') and not href.startswith(base_url)) or \
                               href.startswith('#') or href.startswith('mailto:') or \
                               href.startswith('tel:'):
                                continue
                            
                            # Convert relative URLs to absolute
                            if href.startswith('/'):
                                full_url = base_url + href
                            elif not href.startswith('http'):
                                full_url = urljoin(base_url, href)
                            else:
                                full_url = href
                            
                            # Determine page type from link text
                            page_type = self._get_page_type_from_text(text)
                            
                            if page_type != 'other' and full_url not in found_links:
                                found_links.add(full_url)
                                discovered_pages.append((full_url, page_type))
                                logger.debug(f"🔍 Discovered {page_type} page: {full_url}")
                
                except Exception as e:
                    logger.debug(f"⚠️ Error discovering links with selector {selector}: {str(e)}")
                    continue
            
            return discovered_pages[:5]  # Limit to 5 discovered pages
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to discover pages from navigation: {str(e)}")
            return []
    
    def _get_page_type_from_text(self, text: str) -> str:
        """
        Determine page type from link text.
        
        Args:
            text: Link text
            
        Returns:
            Page type string
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['about', 'who we are', 'our story', 'company']):
            return 'about'
        elif any(word in text_lower for word in ['service', 'what we do', 'solutions', 'offerings']):
            return 'services'
        elif any(word in text_lower for word in ['contact', 'get in touch', 'reach us']):
            return 'contact'
        elif any(word in text_lower for word in ['home', 'homepage']):
            return 'home'
        else:
            return 'other'


# Convenience functions for synchronous usage
def scrape_website_content_sync(website_url: str, headless: bool = True, timeout: int = 30000) -> Dict[str, Any]:
    """
    Synchronous wrapper for website content scraping.
    
    Args:
        website_url: Website URL to scrape
        headless: Run browser in headless mode
        timeout: Timeout in milliseconds
        
    Returns:
        Scraped content dictionary
    """
    async def _scrape():
        async with WebsiteContentScraper(headless=headless, timeout=timeout) as scraper:
            return await scraper.scrape_website_content(website_url)
    
    return asyncio.run(_scrape())

def scrape_multiple_websites_sync(website_urls: List[str], headless: bool = True, 
                                 timeout: int = 30000) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for multiple website content scraping.
    
    Args:
        website_urls: List of website URLs to scrape
        headless: Run browser in headless mode
        timeout: Timeout in milliseconds
        
    Returns:
        List of scraped content dictionaries
    """
    async def _scrape():
        results = []
        async with WebsiteContentScraper(headless=headless, timeout=timeout) as scraper:
            for url in website_urls:
                result = await scraper.scrape_website_content(url)
                results.append(result)
                # Delay between websites
                await asyncio.sleep(2)
        return results
    
    return asyncio.run(_scrape())


if __name__ == "__main__":
    # Test the website content scraper
    import sys
    
    async def test_website_scraper():
        """Test the website content scraper."""
        print("🧪 Testing Website Content Scraper")
        print("=" * 40)
        
        test_websites = [
            'https://microsoft.com',
            'https://apple.com'
        ]
        
        try:
            async with WebsiteContentScraper(headless=True) as scraper:
                for website in test_websites:
                    print(f"\n🌐 Testing: {website}")
                    
                    result = await scraper.scrape_website_content(website)
                    
                    if result['success']:
                        print(f"   ✅ Success: {len(result['pages_scraped'])} pages scraped")
                        for page in result['pages_scraped']:
                            print(f"      📄 {page['type']}: {page['content_length']} chars")
                    else:
                        print(f"   ❌ Failed: {result['errors']}")
            
            print("\n✅ Website content scraper test completed")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            return False
        
        return True
    
    # Run test
    success = asyncio.run(test_website_scraper())
    sys.exit(0 if success else 1)