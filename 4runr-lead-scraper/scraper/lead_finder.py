#!/usr/bin/env python3
"""
Lead Finder

High-level lead discovery logic that coordinates different scraping methods
and applies business rules for lead qualification.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .serpapi_scraper import SerpAPILeadScraper

logger = logging.getLogger('lead-finder')

class LeadFinder:
    """
    High-level lead discovery coordinator.
    Manages different scraping methods and applies business logic.
    """
    
    def __init__(self):
        """Initialize the lead finder."""
        self.serpapi_scraper = SerpAPILeadScraper()
        logger.info("🎯 Lead Finder initialized")
    
    def find_montreal_executives(self, max_leads: int = 10) -> List[Dict]:
        """
        Find Montreal-based executives and business leaders.
        
        Args:
            max_leads: Maximum number of leads to find
            
        Returns:
            List of qualified lead dictionaries
        """
        logger.info(f"🔍 Finding {max_leads} Montreal executives")
        
        try:
            # Use SerpAPI to find leads
            raw_leads = self.serpapi_scraper.search_montreal_ceos(max_results=max_leads)
            
            if not raw_leads:
                logger.warning("⚠️ No raw leads found")
                return []
            
            # Apply qualification filters
            qualified_leads = self._qualify_leads(raw_leads)
            
            # Validate LinkedIn profiles
            validated_leads = self.serpapi_scraper.validate_linkedin_profiles(qualified_leads)
            
            logger.info(f"✅ Found {len(validated_leads)} qualified Montreal executives")
            return validated_leads
            
        except Exception as e:
            logger.error(f"❌ Lead finding failed: {str(e)}")
            return []
    
    def find_leads_by_industry(self, industry: str, max_leads: int = 10) -> List[Dict]:
        """
        Find leads in a specific industry.
        
        Args:
            industry: Industry to target (e.g., "technology", "consulting")
            max_leads: Maximum number of leads to find
            
        Returns:
            List of qualified lead dictionaries
        """
        logger.info(f"🔍 Finding {max_leads} leads in {industry} industry")
        
        try:
            # Map industry to company types
            company_types = self._get_company_types_for_industry(industry)
            
            all_leads = []
            leads_per_type = max(1, max_leads // len(company_types))
            
            for company_type in company_types:
                if len(all_leads) >= max_leads:
                    break
                
                leads = self.serpapi_scraper.search_by_company_type(
                    company_type, 
                    location="Montreal, Quebec, Canada"
                )
                
                # Apply qualification and take only what we need
                qualified = self._qualify_leads(leads)
                all_leads.extend(qualified[:leads_per_type])
            
            # Remove duplicates and limit results
            unique_leads = self._remove_duplicates(all_leads)[:max_leads]
            
            logger.info(f"✅ Found {len(unique_leads)} qualified leads in {industry}")
            return unique_leads
            
        except Exception as e:
            logger.error(f"❌ Industry lead finding failed: {str(e)}")
            return []
    
    def find_startup_founders(self, max_leads: int = 10) -> List[Dict]:
        """
        Find startup founders and entrepreneurs.
        
        Args:
            max_leads: Maximum number of leads to find
            
        Returns:
            List of qualified startup founder leads
        """
        logger.info(f"🔍 Finding {max_leads} startup founders")
        
        try:
            startup_types = [
                "tech startups",
                "software startups", 
                "fintech startups",
                "healthtech startups",
                "startup founders",
                "entrepreneurs"
            ]
            
            all_leads = []
            leads_per_type = max(1, max_leads // len(startup_types))
            
            for startup_type in startup_types:
                if len(all_leads) >= max_leads:
                    break
                
                leads = self.serpapi_scraper.search_by_company_type(startup_type)
                
                # Apply startup-specific qualification
                qualified = self._qualify_startup_leads(leads)
                all_leads.extend(qualified[:leads_per_type])
            
            # Remove duplicates and limit results
            unique_leads = self._remove_duplicates(all_leads)[:max_leads]
            
            logger.info(f"✅ Found {len(unique_leads)} qualified startup founders")
            return unique_leads
            
        except Exception as e:
            logger.error(f"❌ Startup founder finding failed: {str(e)}")
            return []
    
    def _qualify_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Apply general qualification criteria to leads.
        
        Args:
            leads: Raw lead list
            
        Returns:
            Qualified leads
        """
        qualified = []
        
        for lead in leads:
            # Basic validation
            if not self._has_required_fields(lead):
                continue
            
            # Title qualification
            if not self._is_qualified_title(lead.get('title', '')):
                continue
            
            # Company qualification
            if not self._is_qualified_company(lead.get('company', '')):
                continue
            
            # Add qualification metadata
            lead['qualified'] = True
            lead['qualification_date'] = datetime.now().isoformat()
            lead['qualification_criteria'] = 'general_executive'
            
            qualified.append(lead)
        
        logger.info(f"📊 Qualified {len(qualified)}/{len(leads)} leads")
        return qualified
    
    def _qualify_startup_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Apply startup-specific qualification criteria.
        
        Args:
            leads: Raw lead list
            
        Returns:
            Qualified startup leads
        """
        qualified = []
        
        startup_titles = [
            'founder', 'co-founder', 'ceo', 'chief executive',
            'president', 'owner', 'entrepreneur', 'startup'
        ]
        
        for lead in leads:
            if not self._has_required_fields(lead):
                continue
            
            title = lead.get('title', '').lower()
            
            # Must have startup-relevant title
            if not any(startup_title in title for startup_title in startup_titles):
                continue
            
            # Exclude large corporations
            company = lead.get('company', '').lower()
            excluded_companies = [
                'shopify', 'cgi', 'lightspeed', 'bombardier', 'bell',
                'desjardins', 'hydro-quebec', 'sap', 'microsoft', 'google'
            ]
            
            if any(excluded in company for excluded in excluded_companies):
                continue
            
            # Add startup qualification metadata
            lead['qualified'] = True
            lead['qualification_date'] = datetime.now().isoformat()
            lead['qualification_criteria'] = 'startup_founder'
            
            qualified.append(lead)
        
        logger.info(f"📊 Qualified {len(qualified)}/{len(leads)} startup leads")
        return qualified
    
    def _has_required_fields(self, lead: Dict) -> bool:
        """Check if lead has required fields."""
        required_fields = ['name', 'linkedin_url']
        return all(lead.get(field) for field in required_fields)
    
    def _is_qualified_title(self, title: str) -> bool:
        """Check if title indicates a qualified lead."""
        if not title:
            return False
        
        title_lower = title.lower()
        
        # Qualified titles
        qualified_titles = [
            'ceo', 'chief executive', 'president', 'founder', 'co-founder',
            'owner', 'director', 'vice president', 'vp', 'managing director',
            'general manager', 'head of', 'lead', 'principal'
        ]
        
        return any(qual_title in title_lower for qual_title in qualified_titles)
    
    def _is_qualified_company(self, company: str) -> bool:
        """Check if company is qualified (not too large/corporate)."""
        if not company:
            return True  # Allow unknown companies
        
        company_lower = company.lower()
        
        # Exclude very large corporations
        excluded_companies = [
            'shopify', 'cgi group', 'lightspeed', 'bombardier', 'bell canada',
            'desjardins', 'hydro-quebec', 'sap', 'microsoft', 'google',
            'amazon', 'facebook', 'meta', 'apple', 'ibm'
        ]
        
        return not any(excluded in company_lower for excluded in excluded_companies)
    
    def _get_company_types_for_industry(self, industry: str) -> List[str]:
        """Map industry to company types for searching."""
        industry_mapping = {
            'technology': ['tech companies', 'software companies', 'IT services'],
            'consulting': ['consulting firms', 'advisory services', 'business consulting'],
            'finance': ['financial services', 'fintech', 'investment firms'],
            'healthcare': ['healthcare companies', 'medical services', 'healthtech'],
            'manufacturing': ['manufacturing companies', 'industrial companies'],
            'retail': ['retail companies', 'e-commerce', 'consumer goods'],
            'real_estate': ['real estate companies', 'property management'],
            'marketing': ['marketing agencies', 'advertising agencies', 'digital marketing']
        }
        
        return industry_mapping.get(industry.lower(), [f'{industry} companies'])
    
    def _remove_duplicates(self, leads: List[Dict]) -> List[Dict]:
        """Remove duplicate leads based on LinkedIn URL."""
        seen_urls = set()
        unique_leads = []
        
        for lead in leads:
            linkedin_url = lead.get('linkedin_url')
            if linkedin_url and linkedin_url not in seen_urls:
                seen_urls.add(linkedin_url)
                unique_leads.append(lead)
        
        return unique_leads


# Convenience functions for direct usage
def find_montreal_executives(max_leads: int = 10) -> List[Dict]:
    """Find Montreal executives (convenience function)."""
    finder = LeadFinder()
    return finder.find_montreal_executives(max_leads)

def find_startup_founders(max_leads: int = 10) -> List[Dict]:
    """Find startup founders (convenience function)."""
    finder = LeadFinder()
    return finder.find_startup_founders(max_leads)

def find_leads_by_industry(industry: str, max_leads: int = 10) -> List[Dict]:
    """Find leads by industry (convenience function)."""
    finder = LeadFinder()
    return finder.find_leads_by_industry(industry, max_leads)


if __name__ == "__main__":
    # Test the lead finder
    finder = LeadFinder()
    
    print("🧪 Testing Lead Finder...")
    
    # Test Montreal executives
    executives = finder.find_montreal_executives(3)
    print(f"\n✅ Found {len(executives)} Montreal executives:")
    for exec in executives:
        print(f"- {exec['name']} ({exec['title']}) at {exec['company']}")
    
    # Test startup founders
    founders = finder.find_startup_founders(3)
    print(f"\n✅ Found {len(founders)} startup founders:")
    for founder in founders:
        print(f"- {founder['name']} ({founder['title']}) at {founder['company']}")