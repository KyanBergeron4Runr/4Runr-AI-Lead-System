#!/usr/bin/env python3
"""
Improved Email Finder

More practical email discovery that includes common business emails.
Focuses on finding ANY valid business email, not just personal ones.
"""

import re
import requests
import logging
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ImprovedEmailFinder:
    """Find business emails more effectively."""
    
    def __init__(self):
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_business_emails(self, company_website: str, company_name: str = "") -> List[str]:
        """Find business emails from company website."""
        emails = []
        
        try:
            logger.info(f"[EMAIL] Searching for emails on {company_website}")
            
            # Get domain from website
            domain = self._extract_domain(company_website)
            if not domain:
                return emails
            
            # Try multiple pages
            pages_to_check = [
                company_website,
                f"{company_website}/contact",
                f"{company_website}/about",
                f"{company_website}/team",
                f"{company_website}/contact-us"
            ]
            
            for page_url in pages_to_check:
                try:
                    response = requests.get(page_url, headers=self.headers, timeout=self.timeout)
                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_page(response.text, domain)
                        emails.extend(page_emails)
                except:
                    continue
            
            # Remove duplicates and filter
            emails = list(set(emails))
            emails = self._filter_valid_business_emails(emails, domain)
            
            logger.info(f"[EMAIL] Found {len(emails)} valid emails")
            return emails[:3]  # Return top 3 emails
            
        except Exception as e:
            logger.error(f"[EMAIL] Email search failed: {e}")
            return emails
    
    def _extract_domain(self, website: str) -> Optional[str]:
        """Extract domain from website URL."""
        try:
            if '://' not in website:
                website = 'https://' + website
            
            from urllib.parse import urlparse
            parsed = urlparse(website)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return None
    
    def _extract_emails_from_page(self, html_content: str, domain: str) -> List[str]:
        """Extract emails from HTML content."""
        emails = []
        
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, html_content, re.IGNORECASE)
        
        # Filter emails from the same domain
        for email in found_emails:
            email = email.lower()
            if domain.lower() in email:
                emails.append(email)
        
        return emails
    
    def _filter_valid_business_emails(self, emails: List[str], domain: str) -> List[str]:
        """Filter and prioritize business emails."""
        valid_emails = []
        
        # Skip obvious spam/invalid emails
        skip_patterns = [
            'noreply', 'no-reply', 'donotreply', 'test@', 'example@',
            'webmaster@', 'admin@', 'postmaster@'
        ]
        
        # Prioritize business emails
        priority_patterns = [
            'info@', 'contact@', 'hello@', 'sales@', 'business@',
            'office@', 'support@'  # Include support emails
        ]
        
        priority_emails = []
        other_emails = []
        
        for email in emails:
            email = email.strip().lower()
            
            # Skip invalid emails
            if any(skip in email for skip in skip_patterns):
                continue
            
            # Basic email validation
            if '@' not in email or '.' not in email.split('@')[1]:
                continue
            
            # Categorize emails
            if any(pattern in email for pattern in priority_patterns):
                priority_emails.append(email)
            else:
                other_emails.append(email)
        
        # Return priority emails first, then others
        valid_emails = priority_emails + other_emails
        return valid_emails[:5]  # Limit to 5 emails max

# Global instance
email_finder = ImprovedEmailFinder()
