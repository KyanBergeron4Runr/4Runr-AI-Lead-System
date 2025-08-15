#!/usr/bin/env python3
"""
Data Validators

Validation utilities for lead data, email addresses, URLs, and other data types
used throughout the 4runr-lead-scraper system.
"""

import re
import dns.resolver
import validators as external_validators
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime

class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        """Initialize validation result."""
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add an error to the result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the result."""
        self.warnings.append(warning)
    
    def __bool__(self):
        """Return True if validation passed."""
        return self.is_valid
    
    def __str__(self):
        """String representation of validation result."""
        if self.is_valid:
            status = "✅ Valid"
        else:
            status = "❌ Invalid"
        
        messages = []
        if self.errors:
            messages.append(f"Errors: {', '.join(self.errors)}")
        if self.warnings:
            messages.append(f"Warnings: {', '.join(self.warnings)}")
        
        if messages:
            return f"{status} - {' | '.join(messages)}"
        else:
            return status

class EmailValidator:
    """Validator for email addresses."""
    
    @staticmethod
    def validate_format(email: str) -> ValidationResult:
        """
        Validate email format using regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        if not email:
            result.add_error("Email is empty")
            return result
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            result.add_error("Invalid email format")
            return result
        
        # Additional format checks
        local_part, domain = email.split('@')
        
        # Check local part length
        if len(local_part) > 64:
            result.add_error("Local part too long (max 64 characters)")
        
        # Check domain length
        if len(domain) > 253:
            result.add_error("Domain too long (max 253 characters)")
        
        # Check for consecutive dots
        if '..' in email:
            result.add_error("Consecutive dots not allowed")
        
        # Check for valid characters
        if local_part.startswith('.') or local_part.endswith('.'):
            result.add_error("Local part cannot start or end with dot")
        
        return result
    
    @staticmethod
    def validate_domain(email: str) -> ValidationResult:
        """
        Validate email domain using DNS lookup.
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        if not email or '@' not in email:
            result.add_error("Invalid email format")
            return result
        
        domain = email.split('@')[1]
        
        try:
            # Check for MX record
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                result.add_error("No MX record found for domain")
            else:
                result.add_warning(f"Found {len(mx_records)} MX records")
        
        except dns.resolver.NXDOMAIN:
            result.add_error("Domain does not exist")
        except dns.resolver.NoAnswer:
            result.add_error("No MX record found for domain")
        except Exception as e:
            result.add_warning(f"DNS lookup failed: {str(e)}")
        
        return result
    
    @staticmethod
    def validate_email(email: str, check_domain: bool = True) -> ValidationResult:
        """
        Comprehensive email validation.
        
        Args:
            email: Email address to validate
            check_domain: Whether to perform DNS domain validation
            
        Returns:
            ValidationResult
        """
        # Start with format validation
        result = EmailValidator.validate_format(email)
        
        if not result.is_valid:
            return result
        
        # Add domain validation if requested
        if check_domain:
            domain_result = EmailValidator.validate_domain(email)
            result.errors.extend(domain_result.errors)
            result.warnings.extend(domain_result.warnings)
            
            if domain_result.errors:
                result.is_valid = False
        
        return result

class URLValidator:
    """Validator for URLs."""
    
    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """
        Validate URL format and accessibility.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        if not url:
            result.add_error("URL is empty")
            return result
        
        # Use external validators library
        if not external_validators.url(url):
            result.add_error("Invalid URL format")
            return result
        
        # Parse URL for additional checks
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                result.add_warning(f"Unusual scheme: {parsed.scheme}")
            
            # Check domain
            if not parsed.netloc:
                result.add_error("Missing domain")
            
            # Check for localhost or private IPs (warning)
            if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
                result.add_warning("URL points to localhost")
            
        except Exception as e:
            result.add_error(f"URL parsing failed: {str(e)}")
        
        return result
    
    @staticmethod
    def validate_linkedin_url(url: str) -> ValidationResult:
        """
        Validate LinkedIn profile URL.
        
        Args:
            url: LinkedIn URL to validate
            
        Returns:
            ValidationResult
        """
        result = URLValidator.validate_url(url)
        
        if not result.is_valid:
            return result
        
        # Check if it's a LinkedIn URL
        if 'linkedin.com' not in url.lower():
            result.add_error("Not a LinkedIn URL")
            return result
        
        # Check if it's a profile URL
        if '/in/' not in url:
            result.add_warning("May not be a profile URL (missing /in/)")
        
        # Check for valid profile format
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+/?'
        if not re.match(linkedin_pattern, url):
            result.add_warning("Unusual LinkedIn profile URL format")
        
        return result

class LeadDataValidator:
    """Validator for lead data structures."""
    
    @staticmethod
    def validate_lead_data(lead_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate lead data structure and content.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        # Required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in lead_data or not lead_data[field]:
                result.add_error(f"Missing required field: {field}")
        
        # Validate name
        if 'name' in lead_data:
            name_result = LeadDataValidator.validate_name(lead_data['name'])
            result.errors.extend(name_result.errors)
            result.warnings.extend(name_result.warnings)
        
        # Validate email if present
        if lead_data.get('email'):
            email_result = EmailValidator.validate_email(lead_data['email'], check_domain=False)
            result.errors.extend(email_result.errors)
            result.warnings.extend(email_result.warnings)
        
        # Validate LinkedIn URL if present
        if lead_data.get('linkedin_url'):
            linkedin_result = URLValidator.validate_linkedin_url(lead_data['linkedin_url'])
            result.errors.extend(linkedin_result.errors)
            result.warnings.extend(linkedin_result.warnings)
        
        # Validate company website if present
        if lead_data.get('company_website'):
            website_result = URLValidator.validate_url(lead_data['company_website'])
            result.errors.extend(website_result.errors)
            result.warnings.extend(website_result.warnings)
        
        # Validate phone if present
        if lead_data.get('phone'):
            phone_result = LeadDataValidator.validate_phone(lead_data['phone'])
            result.errors.extend(phone_result.errors)
            result.warnings.extend(phone_result.warnings)
        
        # Check for data quality issues
        quality_result = LeadDataValidator.check_data_quality(lead_data)
        result.warnings.extend(quality_result.warnings)
        
        # Update validity based on errors
        if result.errors:
            result.is_valid = False
        
        return result
    
    @staticmethod
    def validate_name(name: str) -> ValidationResult:
        """
        Validate person name.
        
        Args:
            name: Person's name
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        if not name or not name.strip():
            result.add_error("Name is empty")
            return result
        
        name = name.strip()
        
        # Check length
        if len(name) < 2:
            result.add_error("Name too short")
        elif len(name) > 100:
            result.add_error("Name too long")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            result.add_warning("Name contains unusual characters")
        
        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', name):
            result.add_error("Name must contain at least one letter")
        
        # Check for reasonable structure (at least first name)
        parts = name.split()
        if len(parts) < 1:
            result.add_error("Name must have at least one part")
        elif len(parts) == 1:
            result.add_warning("Name has only one part (missing last name?)")
        
        return result
    
    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """
        Validate phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        if not phone:
            result.add_error("Phone is empty")
            return result
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        
        # Check if it's all digits (after cleaning)
        if not cleaned_phone.isdigit():
            result.add_error("Phone contains invalid characters")
            return result
        
        # Check length (reasonable range for international numbers)
        if len(cleaned_phone) < 7:
            result.add_error("Phone number too short")
        elif len(cleaned_phone) > 15:
            result.add_error("Phone number too long")
        
        # Check for North American format
        if len(cleaned_phone) == 10:
            result.add_warning("Appears to be North American format")
        elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
            result.add_warning("Appears to be North American format with country code")
        
        return result
    
    @staticmethod
    def check_data_quality(lead_data: Dict[str, Any]) -> ValidationResult:
        """
        Check data quality and completeness.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            ValidationResult with quality warnings
        """
        result = ValidationResult(True)
        
        # Check completeness
        important_fields = ['email', 'company', 'title', 'linkedin_url']
        missing_fields = [field for field in important_fields if not lead_data.get(field)]
        
        if missing_fields:
            result.add_warning(f"Missing important fields: {', '.join(missing_fields)}")
        
        # Check for placeholder or test data
        test_indicators = ['test', 'example', 'sample', 'dummy', 'placeholder']
        
        for field, value in lead_data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for indicator in test_indicators:
                    if indicator in value_lower:
                        result.add_warning(f"Field '{field}' may contain test data")
                        break
        
        # Check for very short or generic values
        if lead_data.get('company'):
            company = lead_data['company'].strip()
            if len(company) < 3:
                result.add_warning("Company name is very short")
            elif company.lower() in ['company', 'corp', 'inc', 'ltd']:
                result.add_warning("Company name appears generic")
        
        if lead_data.get('title'):
            title = lead_data['title'].strip()
            if len(title) < 3:
                result.add_warning("Job title is very short")
        
        return result

class ConfigValidator:
    """Validator for configuration settings."""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(True)
        
        # Check required configuration keys
        required_keys = ['serpapi_key', 'airtable_api_key', 'airtable_base_id']
        
        for key in required_keys:
            if key not in config or not config[key]:
                result.add_error(f"Missing required configuration: {key}")
        
        # Validate numeric settings
        numeric_settings = {
            'max_leads_per_run': (1, 1000),
            'enrichment_timeout_seconds': (5, 300),
            'max_email_attempts': (1, 10)
        }
        
        for setting, (min_val, max_val) in numeric_settings.items():
            if setting in config:
                try:
                    value = int(config[setting])
                    if value < min_val or value > max_val:
                        result.add_warning(f"{setting} should be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    result.add_error(f"{setting} must be a valid integer")
        
        # Validate boolean settings
        boolean_settings = [
            'use_pattern_emails', 'auto_sync_enabled', 'verbose_logging'
        ]
        
        for setting in boolean_settings:
            if setting in config:
                if not isinstance(config[setting], bool):
                    result.add_warning(f"{setting} should be a boolean value")
        
        return result

def validate_batch_data(data_list: List[Dict[str, Any]], validator_func) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate a batch of data items.
    
    Args:
        data_list: List of data items to validate
        validator_func: Validation function to apply
        
    Returns:
        Tuple of (valid_items, invalid_items)
    """
    valid_items = []
    invalid_items = []
    
    for item in data_list:
        result = validator_func(item)
        
        if result.is_valid:
            valid_items.append(item)
        else:
            # Add validation errors to the item for debugging
            item['_validation_errors'] = result.errors
            item['_validation_warnings'] = result.warnings
            invalid_items.append(item)
    
    return valid_items, invalid_items

def clean_lead_data(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize lead data.
    
    Args:
        lead_data: Raw lead data
        
    Returns:
        Cleaned lead data
    """
    cleaned = {}
    
    for key, value in lead_data.items():
        if isinstance(value, str):
            # Strip whitespace
            value = value.strip()
            
            # Remove empty strings
            if not value:
                continue
            
            # Clean specific fields
            if key == 'email':
                value = value.lower()
            elif key == 'name':
                # Normalize name capitalization
                value = ' '.join(word.capitalize() for word in value.split())
            elif key in ['linkedin_url', 'company_website']:
                # Ensure URLs have protocol
                if value and not value.startswith(('http://', 'https://')):
                    value = 'https://' + value
        
        cleaned[key] = value
    
    return cleaned

if __name__ == "__main__":
    # Test validators
    print("🧪 Testing Validators...")
    
    # Test email validation
    email_result = EmailValidator.validate_email("test@example.com", check_domain=False)
    print(f"Email validation: {email_result}")
    
    # Test URL validation
    url_result = URLValidator.validate_linkedin_url("https://linkedin.com/in/johndoe")
    print(f"LinkedIn URL validation: {url_result}")
    
    # Test lead data validation
    test_lead = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Test Company',
        'linkedin_url': 'https://linkedin.com/in/johndoe'
    }
    
    lead_result = LeadDataValidator.validate_lead_data(test_lead)
    print(f"Lead data validation: {lead_result}")
    
    # Test data cleaning
    dirty_lead = {
        'name': '  john doe  ',
        'email': '  JOHN@EXAMPLE.COM  ',
        'company': '  Test Company Inc  ',
        'linkedin_url': 'linkedin.com/in/johndoe'
    }
    
    cleaned_lead = clean_lead_data(dirty_lead)
    print(f"Cleaned lead data: {cleaned_lead}")
    
    print("✅ Validator tests completed")