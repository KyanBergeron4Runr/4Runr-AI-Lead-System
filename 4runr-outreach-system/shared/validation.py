"""
Validation utilities for the 4Runr Autonomous Outreach System.

Provides validation functions for lead data, email formats, and system inputs.
"""

import re
import validators
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_lead_data(lead: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate lead data completeness and format.
    
    Args:
        lead: Lead data dictionary
        
    Returns:
        Dictionary with validation results and any errors
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['id', 'Name', 'Company', 'Email']
    for field in required_fields:
        if not lead.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Email validation
    email = lead.get('Email')
    if email and not validate_email_format(email):
        errors.append(f"Invalid email format: {email}")
    
    # Company website URL validation
    website_url = lead.get('company_website_url')
    if website_url and not validate_website_url(website_url):
        warnings.append(f"Invalid website URL format: {website_url}")
    
    # Name validation
    name = lead.get('Name')
    if name and len(name.strip()) < 2:
        warnings.append("Name appears to be too short")
    
    # Company validation
    company = lead.get('Company')
    if company and len(company.strip()) < 2:
        warnings.append("Company name appears to be too short")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_email_format(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        return False
    
    # Additional checks
    email = email.strip().lower()
    
    # Check for common invalid patterns
    invalid_patterns = [
        r'\.{2,}',  # Multiple consecutive dots
        r'^\.|\.$',  # Starts or ends with dot
        r'@\.|\@$',  # Invalid @ placement
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, email):
            return False
    
    return True


def validate_website_url(url: str) -> bool:
    """
    Validate website URL format.
    
    Args:
        url: Website URL to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Use validators library for URL validation
    return validators.url(url) is True


def classify_email_confidence(email: str, source_method: str) -> str:
    """
    Classify email confidence level based on source and format.
    
    Args:
        email: Email address
        source_method: How the email was obtained
        
    Returns:
        Confidence level: 'Real', 'Pattern', or 'Guess'
    """
    if not email or not validate_email_format(email):
        return 'Guess'
    
    email = email.lower().strip()
    
    # Real: Direct scrape from website
    if source_method in ['mailto_scrape', 'contact_page_scrape', 'direct_scrape']:
        return 'Real'
    
    # Pattern: Standard format emails
    if source_method in ['pattern_generation', 'standard_format']:
        # Check if it follows common patterns
        common_patterns = [
            r'^[a-z]+\.[a-z]+@',  # firstname.lastname@
            r'^[a-z]+@',          # firstname@
            r'^[a-z]\.[a-z]+@',   # f.lastname@
            r'^[a-z]+\.[a-z]@',   # firstname.l@
        ]
        
        for pattern in common_patterns:
            if re.match(pattern, email):
                return 'Pattern'
    
    # Default to Guess for uncertain cases
    return 'Guess'


def validate_message_quality(message: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate message quality against 4Runr standards.
    
    Args:
        message: Generated message content
        lead_data: Lead data for personalization check
        
    Returns:
        Validation results with quality score and issues
    """
    issues = []
    score = 100
    
    if not message or len(message.strip()) < 50:
        issues.append("Message too short")
        score -= 30
    
    if len(message) > 1000:
        issues.append("Message too long")
        score -= 20
    
    # Check for personalization
    company_name = lead_data.get('Company', '').lower()
    lead_name = lead_data.get('Name', '').lower()
    
    if company_name and company_name not in message.lower():
        issues.append("Missing company name personalization")
        score -= 25
    
    if lead_name and lead_name.split()[0].lower() not in message.lower():
        issues.append("Missing lead name personalization")
        score -= 20
    
    # Check for template-like content
    template_phrases = [
        "dear sir/madam",
        "to whom it may concern",
        "i hope this email finds you well",
        "i am writing to you today",
        "please find attached",
        "[name]",
        "[company]"
    ]
    
    message_lower = message.lower()
    for phrase in template_phrases:
        if phrase in message_lower:
            issues.append(f"Contains template phrase: {phrase}")
            score -= 15
    
    # Check for 4Runr tone requirements
    helpful_indicators = ['help', 'support', 'assist', 'solution', 'improve']
    strategic_indicators = ['strategy', 'growth', 'optimize', 'efficiency', 'results']
    
    has_helpful_tone = any(word in message_lower for word in helpful_indicators)
    has_strategic_tone = any(word in message_lower for word in strategic_indicators)
    
    if not has_helpful_tone:
        issues.append("Missing helpful tone indicators")
        score -= 10
    
    if not has_strategic_tone:
        issues.append("Missing strategic tone indicators")
        score -= 10
    
    # Check for overly salesy language
    salesy_phrases = [
        "buy now",
        "limited time",
        "act fast",
        "don't miss out",
        "special offer",
        "guaranteed results"
    ]
    
    for phrase in salesy_phrases:
        if phrase in message_lower:
            issues.append(f"Contains salesy phrase: {phrase}")
            score -= 20
    
    return {
        'valid': score >= 70,
        'score': max(0, score),
        'issues': issues,
        'needs_review': score < 80
    }


def validate_airtable_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Airtable field data before update.
    
    Args:
        fields: Dictionary of field values
        
    Returns:
        Validation results
    """
    errors = []
    warnings = []
    
    # Check field value lengths for Airtable limits
    text_field_limits = {
        'Company_Description': 100000,  # Long text field
        'Top_Services': 100000,         # Long text field
        'Website_Insights': 100000,     # Long text field
        'Custom_Message': 100000,       # Long text field
        'Message_Preview': 100000,      # Long text field
    }
    
    for field_name, max_length in text_field_limits.items():
        if field_name in fields:
            value = fields[field_name]
            if value and len(str(value)) > max_length:
                errors.append(f"{field_name} exceeds maximum length of {max_length}")
    
    # Validate select field values
    select_field_options = {
        'Tone': ['Bold', 'Formal', 'Friendly', 'Casual', 'Professional'],
        'Email_Confidence_Level': ['Real', 'Pattern', 'Guess'],
        'Engagement_Status': ['Sent', 'Skipped', 'Needs Review', 'Error', 'Auto-Send'],
        'Delivery_Method': ['Email', 'LinkedIn DM', 'Skipped']
    }
    
    for field_name, valid_options in select_field_options.items():
        if field_name in fields:
            value = fields[field_name]
            if value and value not in valid_options:
                errors.append(f"{field_name} has invalid value: {value}. Valid options: {valid_options}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }