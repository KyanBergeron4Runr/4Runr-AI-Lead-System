"""
Website Scraper Service for the 4Runr Email Engager Upgrade.

Handles company website scraping and AI-powered summarization for 
company-focused personalization in outreach messages.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, Optional
import os
import httpx
from openai import OpenAI

from outreach.shared.logging_utils import get_logger
from outreach.shared.config import config


class WebsiteScraperService:
    """Handles company website scraping and summarization."""
    
    def __init__(self):
        """Initialize the Website Scraper Service."""
        self.scraping_config = config.get_scraping_config()
        self.ai_config = config.get_ai_config()
        
        # Initialize OpenAI client with proxy support
        try:
            proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
            
            if proxy:
                http_client = httpx.Client(proxies=proxy, timeout=60)
                self.openai_client = OpenAI(api_key=self.ai_config['api_key'], http_client=http_client)
            else:
                self.openai_client = OpenAI(api_key=self.ai_config['api_key'])
            
            self.logger = get_logger('engager')
            self.logger.log_module_activity('website_scraper_service', 'system', 'info', 
                                           {'message': 'OpenAI API connection established'})
        except Exception as e:
            self.logger = get_logger('engager')
            self.logger.log_error(e, {'action': 'initialize_openai_client'})
            self.openai_client = None
        
        # Request session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.scraping_config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        })
    
    def scrape_company_website(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """
        Scrape and summarize company website content.
        
        Args:
            website_url: Company website URL
            company_name: Company name for context
            
        Returns:
            Dictionary with scraping results and summary
        """
        result = {
            'success': False,
            'url': website_url,
            'company_name': company_name,
            'summary': '',
            'raw_content': '',
            'error': None
        }
        
        try:
            # Validate and normalize URL
            normalized_url = self._validate_and_normalize_url(website_url)
            if not normalized_url:
                result['error'] = f"Invalid URL format: {website_url}"
                return self._fallback_company_info(company_name, result)
            
            result['url'] = normalized_url
            
            # Extract website content
            raw_content = self._extract_website_content(normalized_url)
            if not raw_content:
                result['error'] = "Failed to extract website content"
                return self._fallback_company_info(company_name, result)
            
            result['raw_content'] = raw_content[:2000]  # Limit stored content
            
            # Generate AI summary
            summary = self._summarize_company_info(raw_content, company_name)
            if summary:
                result['summary'] = summary
                result['success'] = True
                
                self.logger.log_module_activity('engager', 'system', 'success', {
                    'message': f'Successfully scraped and summarized {company_name} website',
                    'url': normalized_url,
                    'content_length': len(raw_content),
                    'summary_length': len(summary)
                })
            else:
                result['error'] = "Failed to generate AI summary"
                return self._fallback_company_info(company_name, result)
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'scrape_company_website',
                'url': website_url,
                'company': company_name
            })
            result['error'] = str(e)
            return self._fallback_company_info(company_name, result)
        
        return result
    
    def _validate_and_normalize_url(self, url: str) -> Optional[str]:
        """
        Validate and normalize website URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Normalized URL or None if invalid
        """
        if not url or not isinstance(url, str):
            return None
        
        # Clean up the URL
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc or '.' not in parsed.netloc:
                return None
            
            # Reconstruct clean URL
            clean_url = f"{parsed.scheme}://{parsed.netloc}"
            if parsed.path and parsed.path != '/':
                clean_url += parsed.path
                
            return clean_url
            
        except Exception:
            return None
    
    def _extract_website_content(self, url: str) -> Optional[str]:
        """
        Extract clean text content from website.
        
        Args:
            url: Website URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Add delay for rate limiting
            time.sleep(self.scraping_config.get('delay', 2))
            
            # Make request with timeout
            response = self.session.get(
                url, 
                timeout=self.scraping_config.get('timeout', 30),
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text from key sections
            content_sections = []
            
            # Try to find main content areas
            main_selectors = [
                'main', '[role="main"]', '.main-content', '#main-content',
                '.content', '#content', '.page-content', '.entry-content'
            ]
            
            main_content = None
            for selector in main_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                content_sections.append(main_content.get_text())
            else:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    content_sections.append(body.get_text())
            
            # Also extract key meta information
            title = soup.find('title')
            if title:
                content_sections.insert(0, f"Title: {title.get_text().strip()}")
            
            description = soup.find('meta', attrs={'name': 'description'})
            if description and description.get('content'):
                content_sections.insert(1, f"Description: {description.get('content').strip()}")
            
            # Combine and clean content
            raw_text = '\n'.join(content_sections)
            cleaned_text = self._clean_extracted_text(raw_text)
            
            # Limit content length for AI processing
            if len(cleaned_text) > 4000:
                cleaned_text = cleaned_text[:4000] + "..."
            
            return cleaned_text if cleaned_text.strip() else None
            
        except requests.RequestException as e:
            self.logger.log_module_activity('engager', 'system', 'warning', {
                'message': f'Request failed for {url}: {str(e)}'
            })
            return None
        except Exception as e:
            self.logger.log_error(e, {'action': 'extract_website_content', 'url': url})
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text content.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text content
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common navigation/footer text patterns
        noise_patterns = [
            r'cookie policy.*?accept',
            r'privacy policy.*?terms',
            r'subscribe.*?newsletter',
            r'follow us.*?social',
            r'copyright.*?\d{4}',
            r'all rights reserved',
            r'terms of service',
            r'privacy policy'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces again
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _summarize_company_info(self, content: str, company_name: str) -> Optional[str]:
        """
        Use AI to summarize company information for personalization.
        
        Args:
            content: Website content to summarize
            company_name: Company name for context
            
        Returns:
            AI-generated company summary or None if failed
        """
        try:
            prompt = f"""Analyze the following website content for {company_name} and create a concise business summary for B2B outreach personalization.

Focus on:
- What the company does (core business/products/services)
- Industry and market focus
- Key value propositions or differentiators
- Business model or approach
- Any technology or infrastructure mentions

Website content:
{content}

Provide a 2-3 sentence summary that would help personalize a B2B outreach message. Focus on business operations and value proposition, not marketing fluff."""

            response = self.openai_client.chat.completions.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are a business analyst creating concise company summaries for B2B outreach personalization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            if summary and len(summary) > 20:
                return summary
            else:
                return None
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'summarize_company_info',
                'company': company_name
            })
            return None
    
    def _fallback_company_info(self, company_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback company information when scraping fails.
        
        Args:
            company_name: Company name
            result: Current result dictionary to update
            
        Returns:
            Updated result with fallback information
        """
        fallback_summary = f"Company: {company_name} (website content unavailable for detailed analysis)"
        
        result['summary'] = fallback_summary
        result['success'] = False  # Keep as False since scraping failed
        
        self.logger.log_module_activity('engager', 'system', 'info', {
            'message': f'Using fallback company info for {company_name}',
            'reason': result.get('error', 'Unknown error')
        })
        
        return result
    
    def scrape_with_fallback(self, website_url: str, company_name: str) -> str:
        """
        Scrape website with fallback to company name only.
        
        Args:
            website_url: Company website URL
            company_name: Company name
            
        Returns:
            Company summary string (either scraped or fallback)
        """
        result = self.scrape_company_website(website_url, company_name)
        return result['summary']
    
    def test_scraping_capability(self) -> bool:
        """
        Test basic scraping capability with a simple request.
        
        Returns:
            True if scraping is working, False otherwise
        """
        try:
            test_url = "https://httpbin.org/html"
            response = self.session.get(test_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.log_error(e, {'action': 'test_scraping_capability'})
            return False