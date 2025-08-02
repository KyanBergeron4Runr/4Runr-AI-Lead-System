#!/usr/bin/env python3
"""
Enhanced website scraper that extracts rich context for dynamic message generation.

Extracts headers, hero sections, features, meta data, and tech mentions for
deeper personalization and ICP matching.
"""

import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.logging_utils import get_logger
from shared.config import config


class EnhancedWebsiteScraper:
    """Enhanced website scraper for rich context extraction."""
    
    def __init__(self):
        """Initialize the enhanced scraper."""
        self.logger = get_logger('enhanced_scraper')
        self.scraping_config = config.get_scraping_config()
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.scraping_config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Tech keywords to look for
        self.tech_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'automation',
            'personalization', 'booking flow', 'search algorithm', 'optimization',
            'analytics', 'data science', 'api', 'integration', 'platform',
            'saas', 'cloud', 'scalable', 'real-time', 'dashboard'
        ]
        
        # Feature selectors to try
        self.feature_selectors = [
            '.features li', '.feature-list li', '.services li',
            '.benefits li', '.capabilities li', 'ul.features li',
            '.feature-item', '.service-item', '.benefit-item'
        ]
        
        # Hero section selectors
        self.hero_selectors = [
            '.hero', '.hero-section', '.banner', '.jumbotron',
            '.main-banner', '.header-content', '.intro-section'
        ]
    
    def scrape_enhanced_data(self, website_url: str, lead_id: str) -> Dict[str, any]:
        """
        Scrape enhanced data from website for dynamic message generation.
        
        Args:
            website_url: URL to scrape
            lead_id: Lead ID for logging
            
        Returns:
            Enhanced data dictionary with rich context
        """
        self.logger.log_module_activity('enhanced_scraper', lead_id, 'start', 
                                       {'message': f'Enhanced scraping for {website_url}'})
        
        # Normalize URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        try:
            # Get homepage content
            response = self.session.get(website_url, timeout=self.scraping_config['timeout'])
            
            if response.status_code != 200:
                self.logger.log_module_activity('enhanced_scraper', lead_id, 'error', 
                                               {'message': f'Failed to load {website_url}: {response.status_code}'})
                return self._create_empty_result(website_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract enhanced data
            enhanced_data = {
                'url': website_url,
                'headline': self._extract_headline(soup),
                'hero_copy': self._extract_hero_copy(soup),
                'features': self._extract_features(soup),
                'meta_description': self._extract_meta_description(soup),
                'page_title': self._extract_page_title(soup),
                'headers': self._extract_headers(soup),
                'mentions_ai_or_tech': self._check_tech_mentions(soup),
                'tech_keywords_found': self._find_tech_keywords(soup),
                'testimonials': self._extract_testimonials(soup),
                'partner_logos': self._extract_partner_info(soup),
                'cta_buttons': self._extract_cta_buttons(soup),
                'tone_indicators': self._analyze_tone_indicators(soup),
                'scrape_timestamp': response.headers.get('date', ''),
                'success': True
            }
            
            self.logger.log_module_activity('enhanced_scraper', lead_id, 'success', 
                                           {'message': f'Enhanced scraping completed',
                                            'features_found': len(enhanced_data['features']),
                                            'tech_mentions': enhanced_data['mentions_ai_or_tech'],
                                            'headers_found': len(enhanced_data['headers'])})
            
            return enhanced_data
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'scrape_enhanced_data', 'lead_id': lead_id, 'url': website_url})
            return self._create_empty_result(website_url)
    
    def _extract_headline(self, soup: BeautifulSoup) -> str:
        """Extract main headline from h1 tags."""
        h1_tags = soup.find_all('h1')
        
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            if text and len(text) > 10 and len(text) < 200:
                return text
        
        return ""
    
    def _extract_hero_copy(self, soup: BeautifulSoup) -> str:
        """Extract hero section copy or tagline."""
        # Try hero selectors
        for selector in self.hero_selectors:
            hero_section = soup.select_one(selector)
            if hero_section:
                text = hero_section.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    return text[:500]  # Limit length
        
        # Fallback: look for large text near top
        for tag in ['p', 'div']:
            elements = soup.find_all(tag, class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['hero', 'intro', 'tagline', 'subtitle']
            ))
            
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 300:
                    return text
        
        return ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract features/services from lists and structured content."""
        features = []
        
        # Try feature selectors
        for selector in self.feature_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5 and len(text) < 100:
                    features.append(text)
        
        # Look for feature-related sections
        feature_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['feature', 'service', 'benefit', 'capability']
        ))
        
        for section in feature_sections:
            # Look for lists within these sections
            lists = section.find_all(['ul', 'ol'])
            for ul in lists:
                items = ul.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 5 and len(text) < 100:
                        features.append(text)
        
        # Remove duplicates and limit
        unique_features = list(dict.fromkeys(features))
        return unique_features[:10]  # Limit to top 10
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        return ""
    
    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""
    
    def _extract_headers(self, soup: BeautifulSoup) -> List[str]:
        """Extract h1 and h2 headers."""
        headers = []
        
        for tag in ['h1', 'h2']:
            elements = soup.find_all(tag)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5 and len(text) < 150:
                    headers.append(text)
        
        return headers[:8]  # Limit to top 8
    
    def _check_tech_mentions(self, soup: BeautifulSoup) -> bool:
        """Check if page mentions AI, automation, or tech keywords."""
        page_text = soup.get_text().lower()
        
        return any(keyword in page_text for keyword in self.tech_keywords)
    
    def _find_tech_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Find specific tech keywords mentioned on the page."""
        page_text = soup.get_text().lower()
        found_keywords = []
        
        for keyword in self.tech_keywords:
            if keyword in page_text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_testimonials(self, soup: BeautifulSoup) -> List[str]:
        """Extract testimonials or customer quotes."""
        testimonials = []
        
        # Look for testimonial sections
        testimonial_selectors = [
            '.testimonial', '.review', '.quote', '.customer-quote',
            '[class*="testimonial"]', '[class*="review"]'
        ]
        
        for selector in testimonial_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 20 and len(text) < 300:
                    testimonials.append(text)
        
        return testimonials[:3]  # Limit to top 3
    
    def _extract_partner_info(self, soup: BeautifulSoup) -> List[str]:
        """Extract partner logos or company mentions."""
        partners = []
        
        # Look for partner/client sections
        partner_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['partner', 'client', 'customer', 'logo']
        ))
        
        for section in partner_sections:
            # Look for alt text in images (often contains company names)
            images = section.find_all('img')
            for img in images:
                alt_text = img.get('alt', '')
                if alt_text and len(alt_text) > 2 and len(alt_text) < 50:
                    partners.append(alt_text)
        
        return partners[:5]  # Limit to top 5
    
    def _extract_cta_buttons(self, soup: BeautifulSoup) -> List[str]:
        """Extract call-to-action button text."""
        cta_buttons = []
        
        # Look for buttons and links with CTA-like classes
        cta_selectors = [
            'button', '.btn', '.button', '.cta', '.call-to-action',
            'a[class*="btn"]', 'a[class*="button"]', 'a[class*="cta"]'
        ]
        
        for selector in cta_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 50:
                    cta_buttons.append(text)
        
        # Remove duplicates
        unique_ctas = list(dict.fromkeys(cta_buttons))
        return unique_ctas[:8]  # Limit to top 8
    
    def _analyze_tone_indicators(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Analyze tone indicators from the website."""
        page_text = soup.get_text().lower()
        
        tone_analysis = {
            'formal_indicators': 0,
            'casual_indicators': 0,
            'technical_indicators': 0,
            'friendly_indicators': 0
        }
        
        # Formal indicators
        formal_words = ['enterprise', 'professional', 'solution', 'comprehensive', 'strategic']
        tone_analysis['formal_indicators'] = sum(1 for word in formal_words if word in page_text)
        
        # Casual indicators
        casual_words = ['easy', 'simple', 'quick', 'hassle-free', 'no-brainer']
        tone_analysis['casual_indicators'] = sum(1 for word in casual_words if word in page_text)
        
        # Technical indicators
        technical_words = ['api', 'integration', 'algorithm', 'optimization', 'analytics']
        tone_analysis['technical_indicators'] = sum(1 for word in technical_words if word in page_text)
        
        # Friendly indicators
        friendly_words = ['love', 'enjoy', 'excited', 'passionate', 'community']
        tone_analysis['friendly_indicators'] = sum(1 for word in friendly_words if word in page_text)
        
        # Determine primary tone
        max_score = max(tone_analysis.values())
        if max_score > 0:
            primary_tone = max(tone_analysis, key=tone_analysis.get).replace('_indicators', '')
            tone_analysis['primary_tone'] = primary_tone
        else:
            tone_analysis['primary_tone'] = 'professional'
        
        return tone_analysis
    
    def _create_empty_result(self, website_url: str) -> Dict[str, any]:
        """Create empty result for failed scraping."""
        return {
            'url': website_url,
            'headline': '',
            'hero_copy': '',
            'features': [],
            'meta_description': '',
            'page_title': '',
            'headers': [],
            'mentions_ai_or_tech': False,
            'tech_keywords_found': [],
            'testimonials': [],
            'partner_logos': [],
            'cta_buttons': [],
            'tone_indicators': {'primary_tone': 'professional'},
            'scrape_timestamp': '',
            'success': False,
            'error': f'Failed to scrape {website_url}'
        }


def main():
    """Test the enhanced scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Website Scraper')
    parser.add_argument('url', help='Website URL to scrape')
    parser.add_argument('--output', help='Output JSON file path')
    
    args = parser.parse_args()
    
    scraper = EnhancedWebsiteScraper()
    result = scraper.scrape_enhanced_data(args.url, 'test')
    
    # Pretty print result
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {args.output}")


if __name__ == '__main__':
    main()