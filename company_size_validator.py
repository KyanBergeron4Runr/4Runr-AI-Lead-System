#!/usr/bin/env python3
"""
Company Size Validator

Validates company size to ensure leads are from appropriately sized companies.
Filters out massive corporations that won't respond to outreach.
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CompanySizeValidator:
    """Validate company size for lead qualification."""
    
    def __init__(self):
        self.massive_companies = {
            # Technology Giants
            'apple', 'microsoft', 'google', 'amazon', 'facebook', 'meta',
            'netflix', 'tesla', 'nvidia', 'adobe', 'salesforce', 'oracle',
            
            # Canadian Giants  
            'shopify', 'rbc', 'td bank', 'scotia bank', 'bmo', 'hydro-quebec',
            'cgi group', 'bombardier', 'suncor', 'canadian tire', 'loblaws',
            'rogers', 'bell canada', 'telus', 'power corporation',
            
            # Other Large Corporations
            'walmart', 'coca-cola', 'pepsi', 'mcdonalds', 'starbucks',
            'jp morgan', 'goldman sachs', 'blackrock', 'berkshire hathaway'
        }
    
    def is_company_too_large(self, company_name: str, company_website: str = "") -> bool:
        """Check if company is too large for outreach."""
        if not company_name:
            return False
        
        company_lower = company_name.lower()
        
        # Check against known massive companies
        for massive_company in self.massive_companies:
            if massive_company in company_lower:
                logger.info(f"[SIZE] Company too large: {company_name}")
                return True
        
        # Check for corporate indicators
        corporate_indicators = [
            'corporation', 'corp', 'inc.', 'ltd.', 'limited',
            'international', 'global', 'worldwide', 'group'
        ]
        
        indicator_count = sum(1 for indicator in corporate_indicators if indicator in company_lower)
        
        # If multiple corporate indicators, likely too large
        if indicator_count >= 2:
            logger.info(f"[SIZE] Multiple corporate indicators: {company_name}")
            return True
        
        return False
    
    def estimate_company_size(self, website_content: str, company_name: str = "") -> Dict[str, Any]:
        """Estimate company size from website content."""
        if not website_content:
            return {'size': 'Unknown', 'confidence': 'Low', 'employee_estimate': None}
        
        content_lower = website_content.lower()
        
        # Look for employee count indicators
        employee_indicators = [
            ('startup', 'Small', 1, 10),
            ('small team', 'Small', 1, 10),
            ('boutique', 'Small', 1, 15),
            ('growing team', 'Medium', 10, 50),
            ('established', 'Medium', 20, 100),
            ('enterprise', 'Large', 100, 500),
            ('fortune', 'Enterprise', 500, 10000),
            ('multinational', 'Enterprise', 1000, 50000)
        ]
        
        for indicator, size, min_emp, max_emp in employee_indicators:
            if indicator in content_lower:
                return {
                    'size': size,
                    'confidence': 'Medium',
                    'employee_estimate': f"{min_emp}-{max_emp}",
                    'indicator': indicator
                }
        
        # Estimate based on content complexity
        word_count = len(content_lower.split())
        
        if word_count > 5000:
            return {'size': 'Large', 'confidence': 'Low', 'employee_estimate': '50+'}
        elif word_count > 2000:
            return {'size': 'Medium', 'confidence': 'Low', 'employee_estimate': '10-50'}
        else:
            return {'size': 'Small', 'confidence': 'Low', 'employee_estimate': '1-10'}
    
    def is_good_outreach_target(self, company_name: str, website_content: str = "") -> Dict[str, Any]:
        """Determine if company is a good outreach target."""
        
        # Check if too large
        if self.is_company_too_large(company_name):
            return {
                'is_good_target': False,
                'reason': 'Company too large',
                'size_estimate': 'Enterprise'
            }
        
        # Get size estimate
        size_info = self.estimate_company_size(website_content, company_name)
        
        # Good targets: Small to Medium companies
        good_sizes = ['Small', 'Medium']
        is_good = size_info['size'] in good_sizes
        
        return {
            'is_good_target': is_good,
            'reason': f"Size: {size_info['size']}" + (" - Good target" if is_good else " - Too large"),
            'size_estimate': size_info['size'],
            'employee_estimate': size_info.get('employee_estimate'),
            'confidence': size_info['confidence']
        }

# Global instance
company_validator = CompanySizeValidator()
