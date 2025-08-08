"""
Simplified web scraping engine for testing without Playwright.

Uses requests and BeautifulSoup for basic website scraping.
This is a fallback implementation for testing purposes.
"""

import time
import requests
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from outreach.shared.config import config
from outreach.shared.logging_utils import get_logger


class SimpleScrapingEngine:
    """Simple web scraping engine using requests and BeautifulSoup."""
    
    def __init__(self):
        """Initialize the simple scraping engine."""
        self.logger = get_logger('website_scraper')
        self.config = config.get_scraping_config()
        
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
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.session.close()
    
    async def scrape_website(self, website_url: str, lead_id: str) -> Dict[str, any]:
        """
        Scrape a website and extract key information.
        
        Args:
            website_url: URL of the website to scrape
            lead_id: Lead ID for logging purposes
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        self.logger.log_module_activity('simple_scraper', lead_id, 'start', 
                                       {'message': f'Starting website scrape for {website_url}'})
        
        # Normalize URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        try:
            # Get priority pages content
            scraped_pages = await self._scrape_priority_pages(website_url, lead_id)
            
            if not scraped_pages:
                self.logger.log_module_activity('simple_scraper', lead_id, 'error', 
                                               {'message': 'No content could be scraped from any pages'})
                return self._create_empty_result(website_url)
            
            # Process and clean content
            processed_content = self._process_scraped_content(scraped_pages, lead_id)
            
            self.logger.log_module_activity('simple_scraper', lead_id, 'success', 
                                           {'message': f'Successfully scraped {len(scraped_pages)} pages'})
            
            return processed_content
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'scrape_website', 'lead_id': lead_id, 'url': website_url})
            return self._create_empty_result(website_url)
    
    async def _scrape_priority_pages(self, base_url: str, lead_id: str) -> Dict[str, str]:
        """
        Scrape priority pages from the website.
        
        Args:
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
                
                self.logger.log_module_activity('simple_scraper', lead_id, 'info', 
                                               {'message': f'Attempting to scrape {url}'})
                
                # Make request with timeout
                response = self.session.get(url, timeout=self.config['timeout'])
                
                if response.status_code == 200:
                    # Extract content
                    content = self._extract_page_content(response.text, lead_id)
                    
                    if content and len(content.strip()) > 100:  # Minimum content threshold
                        scraped_pages[path] = content
                        self.logger.log_module_activity('simple_scraper', lead_id, 'success', 
                                                       {'message': f'Successfully scraped {path}', 'content_length': len(content)})
                    else:
                        self.logger.log_module_activity('simple_scraper', lead_id, 'warning', 
                                                       {'message': f'Insufficient content from {path}'})
                else:
                    self.logger.log_module_activity('simple_scraper', lead_id, 'warning', 
                                                   {'message': f'Failed to load {path}', 'status': response.status_code})
                
            except requests.exceptions.Timeout:
                self.logger.log_module_activity('simple_scraper', lead_id, 'warning', 
                                               {'message': f'Timeout loading {path}'})
            except Exception as e:
                self.logger.log_module_activity('simple_scraper', lead_id, 'warning', 
                                               {'message': f'Error scraping {path}: {str(e)}'})
            
            # Rate limiting delay
            time.sleep(self.config['delay'])
        
        return scraped_pages
    
    def _extract_page_content(self, html_content: str, lead_id: str) -> str:
        """
        Extract meaningful content from HTML.
        
        Args:
            html_content: Raw HTML content
            lead_id: Lead ID for logging
            
        Returns:
            Cleaned text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            unwanted_tags = ['nav', 'header', 'footer', 'script', 'style', 'noscript']
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove elements with unwanted classes/ids
            unwanted_selectors = [
                '.navigation', '.nav', '.menu', '.sidebar',
                '.cookie-banner', '.cookie-notice', '.popup', '.modal',
                '.advertisement', '.ads', '#navigation', '#nav', '#menu'
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Try content selectors in order of preference
            content_selectors = ['main', '.main-content', '#main-content', '.content', '#content', 'article', '.page-content']
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    if content and len(content.strip()) > 50:
                        return self._clean_text_content(content)
            
            # Fallback: get body text
            body = soup.find('body')
            if body:
                content = body.get_text(separator=' ', strip=True)
                if content:
                    return self._clean_text_content(content)
            
            # Last resort: get all text
            content = soup.get_text(separator=' ', strip=True)
            return self._clean_text_content(content) if content else ""
            
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
        
        self.logger.log_module_activity('simple_scraper', lead_id, 'success', 
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