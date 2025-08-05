#!/usr/bin/env python3
"""
Enrichment Configuration - Controls how much time agents spend looking for missing data
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class EnrichmentLimits:
    """Configuration for enrichment time limits and retry policies"""
    
    # Time limits (in seconds)
    max_email_search_time: int = 30  # Max time to spend finding email
    max_website_search_time: int = 20  # Max time to spend finding website
    max_linkedin_search_time: int = 15  # Max time to spend on LinkedIn lookup
    max_company_info_time: int = 25  # Max time for company information
    
    # Retry limits
    max_email_attempts: int = 2  # Max attempts to find email
    max_website_attempts: int = 2  # Max attempts to find website
    max_linkedin_attempts: int = 1  # Max attempts for LinkedIn
    
    # Skip conditions
    skip_email_if_no_website: bool = True  # Skip email search if no website found
    skip_enrichment_if_basic_info: bool = False  # Skip if we have name, company, title
    
    # Quality thresholds
    min_confidence_score: float = 0.7  # Minimum confidence to accept enrichment
    require_email_verification: bool = False  # Whether to verify emails
    
    # Fallback behavior
    use_pattern_emails: bool = True  # Generate pattern-based emails if none found
    use_generic_enrichment: bool = True  # Use generic enrichment if specific fails
    
    # Status progression
    mark_as_enriched_with_partial: bool = True  # Mark as enriched even with partial data
    auto_ready_for_outreach: bool = True  # Auto-mark as ready if has email + company

class EnrichmentController:
    """Controls enrichment behavior based on configuration"""
    
    def __init__(self, config: Optional[EnrichmentLimits] = None):
        self.config = config or EnrichmentLimits()
        self.start_times: Dict[str, float] = {}
        self.attempt_counts: Dict[str, int] = {}
    
    def should_search_email(self, lead_data: dict) -> bool:
        """Determine if we should search for email"""
        # Already has email
        if lead_data.get('email'):
            return False
        
        # Check if we should skip based on website
        if self.config.skip_email_if_no_website and not lead_data.get('website'):
            return False
        
        # Check attempt limits
        lead_id = lead_data.get('id', 'unknown')
        attempts = self.attempt_counts.get(f"{lead_id}_email", 0)
        
        return attempts < self.config.max_email_attempts
    
    def should_search_website(self, lead_data: dict) -> bool:
        """Determine if we should search for website"""
        # Already has website
        if lead_data.get('website') or lead_data.get('company_website'):
            return False
        
        # Check attempt limits
        lead_id = lead_data.get('id', 'unknown')
        attempts = self.attempt_counts.get(f"{lead_id}_website", 0)
        
        return attempts < self.config.max_website_attempts
    
    def should_enrich_company(self, lead_data: dict) -> bool:
        """Determine if we should enrich company information"""
        # Skip if we have basic info and config says to skip
        if self.config.skip_enrichment_if_basic_info:
            has_basic = all([
                lead_data.get('full_name'),
                lead_data.get('company'),
                lead_data.get('title')
            ])
            if has_basic:
                return False
        
        return True
    
    def start_timer(self, operation: str, lead_id: str):
        """Start timing an operation"""
        import time
        key = f"{lead_id}_{operation}"
        self.start_times[key] = time.time()
    
    def is_time_exceeded(self, operation: str, lead_id: str) -> bool:
        """Check if time limit exceeded for operation"""
        import time
        key = f"{lead_id}_{operation}"
        
        if key not in self.start_times:
            return False
        
        elapsed = time.time() - self.start_times[key]
        
        limits = {
            'email': self.config.max_email_search_time,
            'website': self.config.max_website_search_time,
            'linkedin': self.config.max_linkedin_search_time,
            'company': self.config.max_company_info_time
        }
        
        return elapsed > limits.get(operation, 30)
    
    def increment_attempts(self, operation: str, lead_id: str):
        """Increment attempt counter"""
        key = f"{lead_id}_{operation}"
        self.attempt_counts[key] = self.attempt_counts.get(key, 0) + 1
    
    def should_use_fallback(self, operation: str, lead_data: dict) -> bool:
        """Determine if we should use fallback methods"""
        if operation == 'email' and self.config.use_pattern_emails:
            # Use pattern emails if we have company domain
            return bool(lead_data.get('company'))
        
        if operation == 'enrichment' and self.config.use_generic_enrichment:
            return True
        
        return False
    
    def determine_final_status(self, lead_data: dict, enrichment_results: dict) -> str:
        """Determine final status based on enrichment results"""
        has_email = bool(lead_data.get('email') or enrichment_results.get('email'))
        has_company = bool(lead_data.get('company'))
        has_basic_info = bool(lead_data.get('full_name') and lead_data.get('title'))
        
        # Auto ready for outreach if configured and has email + company
        if self.config.auto_ready_for_outreach and has_email and has_company:
            return 'Ready for Outreach'
        
        # Mark as enriched with partial data if configured
        if self.config.mark_as_enriched_with_partial and has_basic_info:
            return 'Enriched'
        
        # Default progression
        if has_email and has_company:
            return 'Ready for Outreach'
        elif has_basic_info:
            return 'Enriched'
        else:
            return 'new'
    
    def get_enrichment_summary(self, lead_data: dict, results: dict) -> str:
        """Generate enrichment summary with time/attempt info"""
        summary_parts = []
        
        # Add what was found
        if results.get('email'):
            summary_parts.append(f"Email: {results['email']}")
        if results.get('website'):
            summary_parts.append(f"Website: {results['website']}")
        if results.get('company_info'):
            summary_parts.append("Company info enriched")
        
        # Add method info
        methods = []
        if results.get('email_method'):
            methods.append(f"email_{results['email_method']}")
        if results.get('website_method'):
            methods.append(f"website_{results['website_method']}")
        
        if methods:
            summary_parts.append(f"Methods: {', '.join(methods)}")
        
        # Add efficiency info
        lead_id = lead_data.get('id', 'unknown')
        total_attempts = sum(
            self.attempt_counts.get(f"{lead_id}_{op}", 0) 
            for op in ['email', 'website', 'linkedin', 'company']
        )
        
        if total_attempts > 0:
            summary_parts.append(f"Attempts: {total_attempts}")
        
        return " | ".join(summary_parts)

# Global configuration instance
enrichment_config = EnrichmentController()

def get_enrichment_config() -> EnrichmentController:
    """Get the global enrichment configuration"""
    return enrichment_config

def update_enrichment_limits(**kwargs):
    """Update enrichment limits"""
    global enrichment_config
    
    # Update the config
    for key, value in kwargs.items():
        if hasattr(enrichment_config.config, key):
            setattr(enrichment_config.config, key, value)
    
    print(f"✅ Updated enrichment limits: {kwargs}")

# Environment-based configuration
def load_config_from_env():
    """Load configuration from environment variables"""
    config = EnrichmentLimits()
    
    # Time limits
    config.max_email_search_time = int(os.getenv('MAX_EMAIL_SEARCH_TIME', '30'))
    config.max_website_search_time = int(os.getenv('MAX_WEBSITE_SEARCH_TIME', '20'))
    config.max_linkedin_search_time = int(os.getenv('MAX_LINKEDIN_SEARCH_TIME', '15'))
    config.max_company_info_time = int(os.getenv('MAX_COMPANY_INFO_TIME', '25'))
    
    # Retry limits
    config.max_email_attempts = int(os.getenv('MAX_EMAIL_ATTEMPTS', '2'))
    config.max_website_attempts = int(os.getenv('MAX_WEBSITE_ATTEMPTS', '2'))
    config.max_linkedin_attempts = int(os.getenv('MAX_LINKEDIN_ATTEMPTS', '1'))
    
    # Boolean flags
    config.skip_email_if_no_website = os.getenv('SKIP_EMAIL_IF_NO_WEBSITE', 'true').lower() == 'true'
    config.use_pattern_emails = os.getenv('USE_PATTERN_EMAILS', 'true').lower() == 'true'
    config.auto_ready_for_outreach = os.getenv('AUTO_READY_FOR_OUTREACH', 'true').lower() == 'true'
    
    return EnrichmentController(config)

# Initialize with environment config
enrichment_config = load_config_from_env()

if __name__ == '__main__':
    # Demo the configuration
    print("🔧 Enrichment Configuration Demo")
    print("=" * 40)
    
    config = get_enrichment_config()
    print(f"Max email search time: {config.config.max_email_search_time}s")
    print(f"Max website search time: {config.config.max_website_search_time}s")
    print(f"Max email attempts: {config.config.max_email_attempts}")
    print(f"Use pattern emails: {config.config.use_pattern_emails}")
    print(f"Auto ready for outreach: {config.config.auto_ready_for_outreach}")
    
    # Test with sample lead
    sample_lead = {
        'id': 'test_123',
        'full_name': 'John Doe',
        'company': 'TechCorp',
        'title': 'CEO'
    }
    
    print(f"\nShould search email: {config.should_search_email(sample_lead)}")
    print(f"Should search website: {config.should_search_website(sample_lead)}")
    print(f"Should enrich company: {config.should_enrich_company(sample_lead)}")