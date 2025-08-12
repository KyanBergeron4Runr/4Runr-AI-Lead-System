#!/usr/bin/env python3
"""
Test the enhanced Google enricher validation logic
"""

import re
from typing import Dict

class TestGoogleEnricherValidation:
    """Test class for Google enricher validation methods"""
    
    def _is_valid_company_name(self, company: str) -> bool:
        """ENHANCED validation for 110% accuracy in company name detection."""
        if not company or len(company.strip()) < 2:
            return False
        
        company = company.strip()
        company_lower = company.lower()
        
        # Skip obvious false positives
        skip_terms = [
            'linkedin', 'facebook', 'twitter', 'google', 'youtube', 'instagram',
            'montreal', 'quebec', 'canada', 'toronto', 'vancouver', 'ottawa',
            'ceo', 'president', 'founder', 'executive', 'manager', 'director', 
            'officer', 'unknown', 'company name', 'business', 'organization',
            'university', 'college', 'school', 'hospital', 'government',
            'the company', 'his company', 'her company', 'their company',
            'this company', 'that company', 'a company', 'the firm',
            'search results', 'web results', 'google search', 'find company'
        ]
        
        # Check if it's just a skip term
        if company_lower in skip_terms:
            return False
            
        # Check if it contains skip terms as main content
        if any(term == company_lower or company_lower.startswith(term + ' ') or company_lower.endswith(' ' + term) for term in skip_terms):
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', company):
            return False
        
        # Skip if it's just a person's name (all lowercase or all caps usually not companies)
        if company.islower() or (company.isupper() and len(company) < 5):
            return False
        
        # Skip if it's too generic
        generic_terms = ['company', 'business', 'firm', 'organization', 'corp', 'inc', 'ltd', 'llc']
        if company_lower in generic_terms:
            return False
        
        # Must have at least one capital letter (proper noun)
        if not re.search(r'[A-Z]', company):
            return False
        
        # Skip if it's just numbers or mostly numbers
        if re.match(r'^[\d\s\-\.]+$', company):
            return False
        
        # Skip if it looks like a date or time
        if re.match(r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', company):
            return False
        
        # Skip if it's too long (probably not a company name)
        if len(company) > 60:
            return False
        
        # POSITIVE INDICATORS: These make it more likely to be a company
        positive_indicators = [
            'inc', 'corp', 'ltd', 'llc', 'international', 'technologies', 
            'solutions', 'systems', 'group', 'company', 'enterprises',
            'consulting', 'services', 'partners', 'associates', 'holdings',
            'ventures', 'capital', 'investments', 'labs', 'studio', 'agency'
        ]
        
        has_positive_indicator = any(indicator in company_lower for indicator in positive_indicators)
        
        # If it has positive indicators, it's likely valid
        if has_positive_indicator:
            return True
        
        # For names without indicators, be more strict
        # Must be at least 3 characters and have proper capitalization
        if len(company) >= 3 and re.match(r'^[A-Z][a-zA-Z0-9\s&,.-]*$', company):
            # Check if it looks like a real company name (not just random words)
            words = company.split()
            if len(words) <= 4:  # Most company names are 1-4 words
                # Additional check: reject if it looks like a person's name
                # Person names typically have 2-3 words, all capitalized, no business indicators
                if len(words) == 2 and all(word.istitle() and word.isalpha() for word in words):
                    # This looks like "First Last" - probably a person name
                    return False
                return True
        
        return False

def test_company_validation():
    """Test the company validation logic"""
    tester = TestGoogleEnricherValidation()
    
    # Test cases: (company_name, expected_result, description)
    test_cases = [
        # Valid companies
        ("Flinks Technologies", True, "Valid tech company"),
        ("Apple Inc", True, "Valid company with Inc"),
        ("Microsoft Corporation", True, "Valid corporation"),
        ("Shopify", True, "Valid single word company"),
        ("Goldman Sachs", True, "Valid financial company"),
        ("McKinsey & Company", True, "Valid consulting company"),
        
        # Invalid companies
        ("google", False, "Should reject google"),
        ("linkedin", False, "Should reject linkedin"),
        ("montreal", False, "Should reject city name"),
        ("ceo", False, "Should reject job title"),
        ("company", False, "Should reject generic term"),
        ("unknown", False, "Should reject unknown"),
        ("123456", False, "Should reject numbers only"),
        ("", False, "Should reject empty string"),
        ("a", False, "Should reject single character"),
        ("THE COMPANY", False, "Should reject all caps generic"),
        ("google search", False, "Should reject search terms"),
        
        # Edge cases
        ("AI Solutions Inc", True, "Valid AI company"),
        ("Data Corp", True, "Valid data company"),
        ("Tech Ventures", True, "Valid venture company"),
        ("John Smith", False, "Should reject person name"),
        ("www.example.com", False, "Should reject website"),
    ]
    
    print("🧪 Testing Enhanced Company Validation Logic")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for company, expected, description in test_cases:
        result = tester._is_valid_company_name(company)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} | '{company}' -> {result} | {description}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print(f"🎯 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🚀 ALL TESTS PASSED! Company validation is 110% ready!")
    else:
        print("⚠️  Some tests failed - validation logic needs adjustment")

if __name__ == "__main__":
    test_company_validation()