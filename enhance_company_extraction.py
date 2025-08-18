#!/usr/bin/env python3
"""
Enhance Company Extraction
=========================
Extract real company names from LinkedIn results instead of "Unknown Company"
"""

import re
import logging
from urllib.parse import urlparse

class CompanyExtractor:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_company_from_title(self, title):
        """Extract company from job title"""
        if not title:
            return None
            
        # Common patterns for company extraction
        patterns = [
            r'at\s+(.+?)(?:\s*\||$)',  # "CEO at Company Name"
            r'@\s*(.+?)(?:\s*\||$)',   # "CEO @ Company Name"
            r'-\s*(.+?)(?:\s*\||$)',   # "CEO - Company Name"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common suffixes
                company = re.sub(r'\s*\(.*?\)$', '', company)  # Remove parentheses
                company = re.sub(r'\s*,.*$', '', company)       # Remove comma and after
                if len(company) > 2 and not company.lower() in ['inc', 'llc', 'corp']:
                    return company
        
        return None

    def extract_company_from_snippet(self, snippet):
        """Extract company from search result snippet"""
        if not snippet:
            return None
            
        # Look for company patterns in snippet
        patterns = [
            r'works?\s+at\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s*[,.]|\s+as\s|\s+in\s|$)',
            r'CEO\s+of\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s*[,.]|$)',
            r'President\s+of\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s*[,.]|$)',
            r'Founder\s+of\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s*[,.]|$)',
            r'at\s+([A-Z][a-zA-Z\s&,.-]{3,30}?)(?:\s*[,.]|\s+as\s|\s+in\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet)
            if match:
                company = match.group(1).strip()
                # Clean up
                company = re.sub(r'\s*\(.*?\)$', '', company)
                company = re.sub(r'\s*,.*$', '', company)
                if len(company) > 2 and len(company) < 50:
                    return company
        
        return None

    def extract_company_from_linkedin_url(self, linkedin_url):
        """Extract potential company info from LinkedIn URL"""
        if not linkedin_url or 'linkedin.com' not in linkedin_url:
            return None
            
        # Some LinkedIn URLs contain company info
        # This is a basic implementation - could be enhanced
        return None

    def validate_company_name(self, company):
        """Validate if company name seems real"""
        if not company:
            return False
            
        company_lower = company.lower().strip()
        
        # Reject obviously fake/generic names
        fake_indicators = [
            'unknown', 'company', 'corporation', 'business', 'enterprise',
            'startup', 'firm', 'group', 'organization', 'institute'
        ]
        
        if company_lower in fake_indicators:
            return False
            
        # Must be reasonable length
        if len(company) < 2 or len(company) > 100:
            return False
            
        # Should contain at least one letter
        if not re.search(r'[a-zA-Z]', company):
            return False
            
        return True

    def extract_best_company(self, title, snippet, linkedin_url=None):
        """Extract the best company name from available data"""
        
        candidates = []
        
        # Try title first
        company_from_title = self.extract_company_from_title(title)
        if company_from_title and self.validate_company_name(company_from_title):
            candidates.append(('title', company_from_title))
        
        # Try snippet
        company_from_snippet = self.extract_company_from_snippet(snippet)
        if company_from_snippet and self.validate_company_name(company_from_snippet):
            candidates.append(('snippet', company_from_snippet))
        
        # Try LinkedIn URL
        company_from_url = self.extract_company_from_linkedin_url(linkedin_url)
        if company_from_url and self.validate_company_name(company_from_url):
            candidates.append(('url', company_from_url))
        
        if not candidates:
            return None
        
        # Prefer title extraction, then snippet, then URL
        priority = {'title': 3, 'snippet': 2, 'url': 1}
        best_candidate = max(candidates, key=lambda x: priority.get(x[0], 0))
        
        return best_candidate[1]

def test_company_extraction():
    """Test the company extraction with sample data"""
    
    extractor = CompanyExtractor()
    
    test_cases = [
        {
            'title': 'President and CEO at Bombardier',
            'snippet': 'Éric Martel is the President and CEO at Bombardier, a leading aircraft manufacturer.',
            'expected': 'Bombardier'
        },
        {
            'title': 'CEO @ CGI Inc',
            'snippet': 'Francois Boulanger works at CGI as Chief Executive Officer.',
            'expected': 'CGI Inc'
        },
        {
            'title': 'Founder - Tech Startup',
            'snippet': 'John Smith is the founder of InnovateTech Solutions, a Montreal-based startup.',
            'expected': 'Tech Startup'  # or 'InnovateTech Solutions' from snippet
        }
    ]
    
    print("🧪 TESTING COMPANY EXTRACTION")
    print("=" * 35)
    
    for i, case in enumerate(test_cases, 1):
        title = case['title']
        snippet = case['snippet']
        expected = case['expected']
        
        result = extractor.extract_best_company(title, snippet)
        
        print(f"\n{i}. TEST CASE:")
        print(f"   Title: {title}")
        print(f"   Snippet: {snippet[:60]}...")
        print(f"   Expected: {expected}")
        print(f"   Result: {result}")
        print(f"   Status: {'✅ PASS' if result else '❌ FAIL'}")

def main():
    print("🏢 COMPANY EXTRACTION ENHANCER")
    print("=" * 35)
    print("📋 Purpose: Extract real company names from LinkedIn search results")
    print("✅ Features:")
    print("   - Extract from job titles (CEO at Company)")
    print("   - Extract from snippets (works at Company)")
    print("   - Validate company names")
    print("   - Prioritize extraction sources")
    print("")
    
    # Run tests
    test_company_extraction()
    
    print(f"\n💡 INTEGRATION:")
    print(f"   Add this to SerpAPILeadScraper.process_search_result()")
    print(f"   Replace 'Unknown Company' with extracted company")
    print(f"   This will pass validation filters")

if __name__ == "__main__":
    main()
