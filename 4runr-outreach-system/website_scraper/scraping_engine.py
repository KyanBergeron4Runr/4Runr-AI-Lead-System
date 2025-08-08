"""
Web scraping engine for the Website Scraper Agent.

Uses Playwright for dynamic website scraping with browser automation,
implements page prioritization logic, and includes content cleaning algorithms.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

from outreach.shared.config import config
from outreach.shared.logging_utils import get_logger


class WebScrapingEngine:
    """Web scraping engine using Playwright for dynamic content extraction."""
    
    def __init__(self):
        """Initialize the web scraping engine."""
        self.logger = get_logger('website_scraper')
        self.config = config.get_scraping_config()
        self.browser: Optional[Browser] = None
        
        # Priority pages to scrape
        self.priority_paths = [
            '/about',
            '/about-us',
            '/services',
            '/what-we-do',
            '/home',
            '/',
            '/contact',
            '/contact-us'
        ]
        
        # Content selectors to try
        self.content_selectors = [
            'main',
            '.main-content',
            '#main-content',
            '.content',
            '#content',
            'article',
            '.page-content',
            'body'
        ]
        
        # Elements to remove (navigation, footer, etc.)
        self.cleanup_selectors = [
            'nav',
            'header',
            'footer',
            '.navigation',
            '.nav',
            '.menu',
            '.sidebar',
            '.cookie-banner',
            '.cookie-notice',
            '.popup',
            '.modal',
            '.advertisement',
            '.ads',
            'script',
            'style',
            'noscript'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
    
    async def start_browser(self) -> None:
        """Start the Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            self.logger.log_module_activity('scraping_engine', 'system', 'info', 
                                           {'message': 'Browser started successfully'})
        except Exception as e:
            self.logger.log_error(e, {'action': 'start_browser', 'lead_id': 'system'})
            raise
    
    async def close_browser(self) -> None:
        """Close the Playwright browser."""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            self.logger.log_module_activity('scraping_engine', 'system', 'info', 
                                           {'message': 'Browser closed successfully'})
        except Exception as e:
            self.logger.log_error(e, {'action': 'close_browser', 'lead_id': 'system'})
    
    async def scrape_website(self, website_url: str, lead_id: str) -> Dict[str, any]:
        """
        Scrape a website and extract key information.
        
        Args:
            website_url: URL of the website to scrape
            lead_id: Lead ID for logging purposes
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        self.logger.log_module_activity('scraping_engine', lead_id, 'start', 
                                       {'message': f'Starting website scrape for {website_url}'})
        
        # Normalize URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        try:
            # Create new page
            page = await self.browser.new_page()
            
            # Set user agent and viewport
            await page.set_user_agent(self.config['user_agent'])
            await page.set_viewport_size({'width': 1920, 'height': 1080})
            
            # Get priority pages content
            scraped_pages = await self._scrape_priority_pages(page, website_url, lead_id)
            
            await page.close()
            
            if not scraped_pages:
                self.logger.log_module_activity('scraping_engine', lead_id, 'error', 
                                               {'message': 'No content could be scraped from any pages'})
                return self._create_empty_result(website_url)
            
            # Process and clean content
            processed_content = self._process_scraped_content(scraped_pages, lead_id)
            
            self.logger.log_module_activity('scraping_engine', lead_id, 'success', 
                                           {'message': f'Successfully scraped {len(scraped_pages)} pages'})
            
            return processed_content
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'scrape_website', 'lead_id': lead_id, 'url': website_url})
            return self._create_empty_result(website_url)
    
    async def _scrape_priority_pages(self, page: Page, base_url: str, lead_id: str) -> Dict[str, str]:
        """
        Scrape priority pages from the website.
        
        Args:
            page: Playwright page object
            base_url: Base URL of the website
            lead_id: Lead ID for logging
            
        Returns:
            Dictionary mapping page paths to their content
        """
        scraped_pages = {}
        
        for path in self.priority_paths:
            try:
                # Construct full URL
                if path == '/':
                    url = base_url
                else:
                    url = urljoin(base_url, path)
                
                self.logger.log_module_activity('scraping_engine', lead_id, 'info', 
                                               {'message': f'Attempting to scrape {url}'})
                
                # Navigate to page with timeout
                response = await page.goto(url, timeout=self.config['timeout'] * 1000, wait_until='domcontentloaded')
                
                if response and response.status == 200:
                    # Wait for content to load
                    await page.wait_for_timeout(self.config['delay'] * 1000)
                    
                    # Extract content
                    content = await self._extract_page_content(page, lead_id)
                    
                    if content and len(content.strip()) > 100:  # Minimum content threshold
                        scraped_pages[path] = content
                        self.logger.log_module_activity('scraping_engine', lead_id, 'success', 
                                                       {'message': f'Successfully scraped {path}', 'content_length': len(content)})
                    else:
                        self.logger.log_module_activity('scraping_engine', lead_id, 'warning', 
                                                       {'message': f'Insufficient content from {path}'})
                else:
                    status = response.status if response else 'no_response'
                    self.logger.log_module_activity('scraping_engine', lead_id, 'warning', 
                                                   {'message': f'Failed to load {path}', 'status': status})
                
            except PlaywrightTimeoutError:
                self.logger.log_module_activity('scraping_engine', lead_id, 'warning', 
                                               {'message': f'Timeout loading {path}'})
            except Exception as e:
                self.logger.log_module_activity('scraping_engine', lead_id, 'warning', 
                                               {'message': f'Error scraping {path}: {str(e)}'})
            
            # Rate limiting delay
            await asyncio.sleep(self.config['delay'])
        
        return scraped_pages
    
    async def _extract_page_content(self, page: Page, lead_id: str) -> str:
        """
        Extract meaningful content from a page.
        
        Args:
            page: Playwright page object
            lead_id: Lead ID for logging
            
        Returns:
            Cleaned text content
        """
        try:
            # Remove unwanted elements first
            for selector in self.cleanup_selectors:
                try:
                    await page.evaluate(f'''
                        document.querySelectorAll("{selector}").forEach(el => el.remove());
                    ''')
                except:
                    pass  # Continue if selector fails
            
            # Try content selectors in order of preference
            for selector in self.content_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        content = await element.inner_text()
                        if content and len(content.strip()) > 50:
                            return self._clean_text_content(content)
                except:
                    continue
            
            # Fallback: get body text
            try:
                body_content = await page.evaluate('document.body.innerText')
                if body_content:
                    return self._clean_text_content(body_content)
            except:
                pass
            
            self.logger.log_module_activity('scraping_engine', lead_id, 'warning', 
                                           {'message': 'Could not extract content using any selector'})
            return ""
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'extract_page_content', 'lead_id': lead_id})
            return ""
    
    def _clean_text_content(self, content: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            content: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not content:
            return ""
        
        # Remove extra whitespace and normalize
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and len(line) > 3:  # Filter out very short lines
                lines.append(line)
        
        # Join lines and remove excessive spacing
        cleaned = ' '.join(lines)
        
        # Remove multiple spaces
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove common unwanted phrases
        unwanted_phrases = [
            'Cookie Policy',
            'Privacy Policy',
            'Terms of Service',
            'Accept Cookies',
            'This website uses cookies',
            'Subscribe to newsletter',
            'Follow us on',
            'Copyright ©'
        ]
        
        for phrase in unwanted_phrases:
            cleaned = cleaned.replace(phrase, '')
        
        return cleaned.strip()
    
    def _process_scraped_content(self, scraped_pages: Dict[str, str], lead_id: str) -> Dict[str, any]:
        """
        Process scraped content to extract structured information.
        
        Args:
            scraped_pages: Dictionary of scraped page content
            lead_id: Lead ID for logging
            
        Returns:
            Processed content dictionary
        """
        # Combine all content for analysis
        all_content = ' '.join(scraped_pages.values())
        
        # Store raw insights
        website_insights = {}
        for path, content in scraped_pages.items():
            if content:
                website_insights[path] = content[:1000]  # Truncate for storage
        
        result = {
            'success': True,
            'scraped_pages': list(scraped_pages.keys()),
            'total_content_length': len(all_content),
            'raw_content': all_content,
            'website_insights': website_insights,
            'scrape_timestamp': time.time()
        }
        
        self.logger.log_module_activity('scraping_engine', lead_id, 'success', 
                                       {'message': 'Content processing completed', 
                                        'pages_scraped': len(scraped_pages),
                                        'total_length': len(all_content)})
        
        return result
    
    def _create_empty_result(self, website_url: str) -> Dict[str, any]:
        """
        Create an empty result for failed scraping attempts.
        
        Args:
            website_url: URL that failed to scrape
            
        Returns:
            Empty result dictionary
        """
        return {
            'success': False,
            'scraped_pages': [],
            'total_content_length': 0,
            'raw_content': '',
            'website_insights': {},
            'scrape_timestamp': time.time(),
            'error': f'Failed to scrape content from {website_url}'
        }