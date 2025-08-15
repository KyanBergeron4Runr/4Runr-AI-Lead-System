#!/usr/bin/env python3
"""
Data Cleaner System for the 4Runr Autonomous Outreach System.

This module provides intelligent data cleaning and validation to ensure only
high-quality, professional data reaches both Airtable and the internal database.
Removes Google search artifacts, HTML fragments, and validates data quality.
"""

import re
import os
import yaml
import json
import datetime
from datetime import timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from .logging_utils import get_logger


@dataclass
class CleaningAction:
    """Represents a single cleaning action performed on data."""
    rule_name: str
    field_name: str
    original_value: str
    cleaned_value: str
    confidence_score: float
    applied_at: str


@dataclass
class ValidationResult:
    """Represents the result of a validation check."""
    field_name: str
    is_valid: bool
    confidence_score: float
    validation_rule: str
    error_message: str
    suggested_fix: str


@dataclass
class FieldCleaningResult:
    """Represents the result of cleaning a single field."""
    field_name: str
    original_value: str
    cleaned_value: str
    patterns_applied: List[str]
    confidence_score: float
    processing_time: float


@dataclass
class CleaningResult:
    """Represents the complete result of data cleaning and validation."""
    success: bool
    cleaned_data: Dict[str, Any]
    original_data: Dict[str, Any]
    cleaning_actions: List[CleaningAction]
    validation_results: List[ValidationResult]
    rejection_reasons: List[str]
    confidence_score: float
    processing_time: float


class CleaningRulesEngine:
    """Engine for applying text cleaning rules to remove artifacts and normalize data."""
    
    def __init__(self, rules_config: Dict[str, Any]):
        """
        Initialize the cleaning rules engine.
        
        Args:
            rules_config: Configuration dictionary with cleaning rules
        """
        self.rules = rules_config
        self.logger = get_logger('data_cleaner')
    
    def clean_company_name(self, company: str) -> str:
        """
        Clean company name by removing search artifacts and normalizing format.
        
        This method specifically handles the garbage data mentioned in requirements:
        - "Sirius XM and ... Some results may have been delisted consistent with local laws. Learn more Next"
        - Google search result prefixes like "About 1,234 results for"
        - HTML fragments and entities
        - Company suffix normalization (Inc, LLC, Corp, etc.)
        
        Args:
            company: Raw company name from enricher
            
        Returns:
            Cleaned and normalized company name, or empty string if garbage
        """
        if not company or not isinstance(company, str):
            return ""
        
        original_company = company
        cleaned = company.strip()
        
        # Step 1: Remove search artifacts first (most aggressive cleaning)
        cleaned = self.remove_search_artifacts(cleaned)
        
        # Step 2: Remove HTML fragments and entities
        cleaned = self.remove_html_fragments(cleaned)
        
        # Step 3: Remove specific company name garbage patterns
        company_garbage_patterns = self.rules.get('company_name', {}).get('remove_patterns', [])
        for pattern in company_garbage_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Step 4: Remove search result prefixes and suffixes
        search_prefixes = [
            r'^About \d{1,3}(,\d{3})* results for\s*',
            r'^Search results for\s*',
            r'^Results for\s*',
            r'^Showing results for\s*',
            r'^\d+ results for\s*',
            r'^.*results for\s*',
            r'^for\s+',  # Remove standalone "for" at beginning
        ]
        
        for prefix_pattern in search_prefixes:
            cleaned = re.sub(prefix_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Step 5: Remove trailing garbage
        trailing_garbage = [
            r'\s*Learn more.*$',
            r'\s*Next$',
            r'\s*More results.*$',
            r'\s*Related searches.*$',
            r'\s*People also ask.*$',
            r'\s*\.\.\.$',  # Trailing ellipsis
        ]
        
        for trailing_pattern in trailing_garbage:
            cleaned = re.sub(trailing_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Step 6: Normalize text (whitespace, encoding, etc.)
        cleaned = self.normalize_text(cleaned)
        
        # Step 7: Normalize company suffixes and legal entities
        normalize_patterns = self.rules.get('company_name', {}).get('normalize_patterns', [])
        for pattern_config in normalize_patterns:
            pattern = pattern_config.get('pattern', '')
            replacement = pattern_config.get('replacement', '')
            if pattern and replacement:
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Step 8: Additional company-specific cleaning
        cleaned = self._apply_company_specific_rules(cleaned)
        
        # Step 9: Final validation - reject if too short or contains obvious garbage
        if len(cleaned.strip()) < 2:
            self.logger.log_module_activity('data_cleaner', 'company_cleaning', 'info', {
                'message': 'Company name too short after cleaning, rejecting',
                'original': original_company,
                'cleaned': cleaned
            })
            return ""
        
        # Check for remaining garbage indicators
        garbage_indicators = ['google', 'search', 'results', 'linkedin', 'facebook', 'www.', 'http', '.com', 'company/']
        cleaned_lower = cleaned.lower()
        for indicator in garbage_indicators:
            if indicator in cleaned_lower:
                self.logger.log_module_activity('data_cleaner', 'company_cleaning', 'info', {
                    'message': f'Company name contains garbage indicator "{indicator}", rejecting',
                    'original': original_company,
                    'cleaned': cleaned
                })
                return ""
        
        # Special check for URL-like patterns
        if re.match(r'^[a-z]+://.*', cleaned_lower) or '///' in cleaned:
            self.logger.log_module_activity('data_cleaner', 'company_cleaning', 'info', {
                'message': 'Company name looks like URL, rejecting',
                'original': original_company,
                'cleaned': cleaned
            })
            return ""
        
        # Final cleanup
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _apply_company_specific_rules(self, company: str) -> str:
        """
        Apply company-specific cleaning rules.
        
        Args:
            company: Company name to clean
            
        Returns:
            Company name with specific rules applied
        """
        if not company:
            return ""
        
        cleaned = company
        
        # Remove common prefixes that shouldn't be part of company names
        unwanted_prefixes = [
            r'^for\s+',  # "for TechCorp Inc"
            r'^about\s+',  # "about TechCorp Inc"
            r'^the\s+results?\s+for\s+',  # "the results for TechCorp"
        ]
        
        for prefix in unwanted_prefixes:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        # Fix common OCR/parsing errors in company names
        ocr_fixes = {
            r'\bl+c\b': 'LLC',  # "llc" -> "LLC"
            r'\binc\b': 'Inc',  # "inc" -> "Inc"
            r'\bcorp\b': 'Corp',  # "corp" -> "Corp"
            r'\bltd\b': 'Ltd',  # "ltd" -> "Ltd"
        }
        
        for pattern, replacement in ocr_fixes.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Remove duplicate words (common in scraped data)
        words = cleaned.split()
        unique_words = []
        for word in words:
            if word.lower() not in [w.lower() for w in unique_words]:
                unique_words.append(word)
        cleaned = ' '.join(unique_words)
        
        return cleaned.strip()
    
    def clean_website_url(self, website: str) -> str:
        """
        Clean website URL by validating format and removing invalid domains.
        
        This method handles various URL cleaning tasks:
        - Removes invalid domains (google.com, linkedin.com, facebook.com, etc.)
        - Fixes malformed URLs and protocol issues
        - Normalizes URL format and structure
        - Validates domain format and TLD
        - Removes search parameters and fragments when appropriate
        
        Args:
            website: Raw website URL from enricher
            
        Returns:
            Cleaned and validated website URL, or empty string if invalid
        """
        if not website or not isinstance(website, str):
            return ""
        
        original_website = website
        cleaned = website.strip()
        
        # Step 1: Remove search artifacts and HTML fragments first
        cleaned = self.remove_search_artifacts(cleaned)
        cleaned = self.remove_html_fragments(cleaned)
        cleaned = self.normalize_text(cleaned)
        
        # Step 2: Check for invalid domains that should be rejected entirely
        invalid_domains = self.rules.get('website_url', {}).get('remove_patterns', [])
        for pattern in invalid_domains:
            if pattern.lower() in cleaned.lower():
                self.logger.log_module_activity('data_cleaner', 'url_cleaning', 'info', {
                    'message': f'URL contains invalid domain "{pattern}", rejecting',
                    'original': original_website,
                    'cleaned': cleaned
                })
                return ""
        
        # Step 3: Handle malformed URLs and extract domain
        cleaned = self._extract_and_clean_domain(cleaned)
        if not cleaned:
            return ""
        
        # Step 4: Validate domain format
        if not self._is_valid_domain_format(cleaned):
            self.logger.log_module_activity('data_cleaner', 'url_cleaning', 'info', {
                'message': 'Invalid domain format, rejecting',
                'original': original_website,
                'cleaned': cleaned
            })
            return ""
        
        # Step 5: Ensure proper protocol
        if not cleaned.startswith(('http://', 'https://')):
            cleaned = 'https://' + cleaned
        
        # Step 6: Normalize URL structure
        cleaned = self._normalize_url_structure(cleaned)
        
        # Step 7: Final validation
        if not self._is_legitimate_business_url(cleaned):
            self.logger.log_module_activity('data_cleaner', 'url_cleaning', 'info', {
                'message': 'URL does not appear to be legitimate business website, rejecting',
                'original': original_website,
                'cleaned': cleaned
            })
            return ""
        
        return cleaned
    
    def _extract_and_clean_domain(self, url: str) -> str:
        """
        Extract and clean domain from potentially malformed URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Cleaned domain or empty string if invalid
        """
        if not url:
            return ""
        
        cleaned = url.lower().strip()
        
        # Remove common URL prefixes that might be malformed
        prefixes_to_remove = [
            'website:', 'url:', 'site:', 'web:', 'link:', 'page:',
            'visit:', 'see:', 'check:', 'go to:', 'at:'
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Handle various URL formats
        if cleaned.startswith(('http://', 'https://')):
            # Already has protocol
            pass
        elif cleaned.startswith('www.'):
            # Add protocol to www URLs
            cleaned = 'https://' + cleaned
        elif cleaned.startswith('//'):
            # Protocol-relative URL
            cleaned = 'https:' + cleaned
        elif '.' in cleaned and not cleaned.startswith(('ftp://', 'mailto:')):
            # Looks like a domain, add protocol
            cleaned = 'https://' + cleaned
        else:
            # Doesn't look like a valid URL
            return ""
        
        # Parse URL to extract components
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(cleaned)
            
            # Validate that we have a domain
            if not parsed.netloc:
                return ""
            
            # Reconstruct clean URL with just the essential parts
            clean_netloc = parsed.netloc.lower()
            
            # Remove port numbers for common ports
            if clean_netloc.endswith(':80'):
                clean_netloc = clean_netloc[:-3]
            elif clean_netloc.endswith(':443'):
                clean_netloc = clean_netloc[:-4]
            
            # Reconstruct URL
            scheme = 'https' if parsed.scheme in ('https', 'http') else 'https'
            path = parsed.path if parsed.path and parsed.path != '/' else ''
            
            cleaned_url = f"{scheme}://{clean_netloc}{path}"
            return cleaned_url
            
        except Exception:
            # URL parsing failed, try basic domain extraction
            # Look for domain-like patterns, but be more selective
            domain_matches = re.findall(r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', cleaned)
            if domain_matches:
                # Take the first valid-looking domain
                domain = domain_matches[0].lower()
                return f"https://{domain}"
            
            # Try without protocol
            domain_match = re.search(r'\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', cleaned)
            if domain_match:
                domain = domain_match.group(1).lower()
                # Basic validation before returning
                if '&' not in domain and ' ' not in domain:
                    return f"https://{domain}"
            
            return ""
    
    def _is_valid_domain_format(self, url: str) -> bool:
        """
        Validate that URL has proper domain format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if domain format is valid
        """
        if not url:
            return False
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            if not parsed.netloc:
                return False
            
            domain = parsed.netloc.lower()
            
            # Remove www prefix for validation
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Basic domain format validation
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
                return False
            
            # Check for valid TLD
            tld = domain.split('.')[-1]
            if len(tld) < 2 or not tld.isalpha():
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'\.\.+',  # Multiple consecutive dots
                r'^-',     # Starting with dash
                r'-\.',    # Ending with dash before TLD
                r'--',     # Double dashes
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, domain):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _normalize_url_structure(self, url: str) -> str:
        """
        Normalize URL structure and format.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        if not url:
            return ""
        
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url)
            
            # Normalize scheme
            scheme = 'https' if parsed.scheme in ('http', 'https') else 'https'
            
            # Normalize netloc (domain)
            netloc = parsed.netloc.lower()
            
            # Normalize path
            path = parsed.path
            if path == '/':
                path = ''  # Remove trailing slash for root
            
            # Remove query parameters and fragments for business websites
            # (they're usually not needed for business identification)
            query = ''
            fragment = ''
            
            # Reconstruct normalized URL
            normalized = urlunparse((scheme, netloc, path, '', query, fragment))
            
            # Final cleanup
            normalized = normalized.rstrip('/')
            
            return normalized
            
        except Exception:
            # Fallback to basic cleanup
            cleaned = url.rstrip('/')
            if not cleaned.startswith(('http://', 'https://')):
                cleaned = 'https://' + cleaned
            return cleaned
    
    def _is_legitimate_business_url(self, url: str) -> bool:
        """
        Check if URL appears to be a legitimate business website.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears legitimate for business use
        """
        if not url:
            return False
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check against known non-business domains
            non_business_domains = [
                'google.com', 'google.ca', 'google.co.uk',
                'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
                'youtube.com', 'tiktok.com', 'snapchat.com',
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'example.com', 'test.com', 'localhost',
                'wikipedia.org', 'reddit.com', 'pinterest.com'
            ]
            
            for non_business in non_business_domains:
                if domain == non_business or domain.endswith('.' + non_business):
                    return False
            
            # Check for suspicious TLDs that are rarely used for business
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq']
            for tld in suspicious_tlds:
                if domain.endswith(tld):
                    return False
            
            # Check for IP addresses (not typical for business websites)
            if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
                return False
            
            # Check minimum domain length (too short domains are suspicious)
            if len(domain) < 4:  # e.g., "a.co" is suspicious
                return False
            
            # Additional check for domains ending with dash
            if domain.endswith('-'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def remove_search_artifacts(self, text: str) -> str:
        """
        Remove Google search artifacts and navigation elements.
        
        This method specifically targets the garbage data mentioned in requirements:
        - "Sirius XM and ... Some results may have been delisted consistent with local laws. Learn more Next"
        - Google search navigation elements
        - Search result metadata
        
        Args:
            text: Raw text content
            
        Returns:
            Text with search artifacts removed
        """
        if not text or not isinstance(text, str):
            return ""
        
        cleaned = text
        
        # Remove specific search artifacts from configuration
        artifacts = self.rules.get('search_artifacts', {}).get('remove_patterns', [])
        for pattern in artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Additional aggressive search artifact removal
        additional_artifacts = [
            r'Showing results for\s*',
            r'Search results for\s*',
            r'Results for\s*',
            r'About.*?results for\s*',  # More aggressive "About X results for" removal
        ]
        
        for pattern in additional_artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove common Google search navigation elements
        navigation_patterns = [
            r'About \d{1,3}(,\d{3})* results',
            r'Search instead for.*',
            r'Did you mean:.*',
            r'Showing results for.*',
            r'No results found for.*',
            r'Learn more Next',
            r'Previous.*Next',
            r'Page \d+ of \d+',
            r'More results',
            r'Related searches',
            r'People also ask',
            r'Videos.*Images.*News.*Shopping',
            r'Cached.*Similar.*',
            r'More from.*',
            r'Jump to.*',
            r'See results about.*'
        ]
        
        for pattern in navigation_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove specific garbage patterns that appear in real data
        garbage_patterns = [
            r'Sirius XM.*',  # Remove anything starting with "Sirius XM"
            r'Some results may have been delisted.*',
            r'consistent with local laws.*',
            r'\.{3,}.*?Next',  # Multiple dots followed by Next
            r'and\s*\.{3,}.*?Next',  # "and ..." patterns
            r'and\s*\.{3,}.*',  # "and ..." at end of text
            r'Learn more.*',  # Remove anything starting with "Learn more"
        ]
        
        for pattern in garbage_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned.strip()
    
    def remove_html_fragments(self, text: str) -> str:
        """
        Remove HTML tags, entities, and fragments.
        
        This method handles various HTML artifacts that can appear in scraped data:
        - HTML tags like <div>, <span>, <p>, etc.
        - HTML entities like &nbsp;, &amp;, etc.
        - Malformed HTML fragments
        - CSS and JavaScript remnants
        
        Args:
            text: Text that may contain HTML
            
        Returns:
            Text with HTML removed and cleaned
        """
        if not text or not isinstance(text, str):
            return ""
        
        cleaned = text
        
        # Remove script and style tags with their content
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove HTML comments
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        
        # Remove all HTML tags (including malformed ones)
        cleaned = re.sub(r'<[^>]*>', '', cleaned)
        cleaned = re.sub(r'<[^>]*$', '', cleaned)  # Handle incomplete tags at end
        cleaned = re.sub(r'^[^<]*>', '', cleaned)  # Handle incomplete tags at start
        
        # Remove HTML entities (comprehensive list)
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&apos;': "'",
            '&nbsp;': ' ',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '...',
            '&laquo;': '«',
            '&raquo;': '»',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': ''',
            '&rsquo;': ''',
            '&bull;': '•',
            '&middot;': '·'
        }
        
        for entity, replacement in html_entities.items():
            cleaned = cleaned.replace(entity, replacement)
        
        # Remove any remaining HTML entities (numeric and named)
        cleaned = re.sub(r'&#\d+;', '', cleaned)  # Numeric entities
        cleaned = re.sub(r'&#x[0-9a-fA-F]+;', '', cleaned)  # Hex entities
        cleaned = re.sub(r'&[a-zA-Z][a-zA-Z0-9]*;', '', cleaned)  # Named entities
        
        # Remove CSS remnants
        cleaned = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'class\s*=\s*["\'][^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up excessive whitespace created by HTML removal
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def normalize_text(self, text: str) -> str:
        """
        Apply comprehensive text normalization.
        
        This method handles various text normalization tasks:
        - Whitespace cleanup and normalization
        - Control character removal
        - Unicode normalization
        - Special character handling
        - Encoding issue fixes
        
        Args:
            text: Raw text
            
        Returns:
            Normalized and cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        normalized = text
        
        # Remove control characters (except newlines and tabs which we'll handle separately)
        normalized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', normalized)
        
        # Remove zero-width characters and other invisible Unicode characters
        normalized = re.sub(r'[\u200b-\u200d\ufeff\u2060\u180e]', '', normalized)
        
        # Normalize different types of quotes and dashes
        quote_replacements = {
            '"': '"',  # Left double quotation mark
            '"': '"',  # Right double quotation mark
            ''': "'",  # Left single quotation mark
            ''': "'",  # Right single quotation mark
            '`': "'",  # Grave accent
            '´': "'",  # Acute accent
            '—': '-',  # Em dash
            '–': '-',  # En dash
            '−': '-',  # Minus sign
        }
        
        for old_char, new_char in quote_replacements.items():
            normalized = normalized.replace(old_char, new_char)
        
        # Convert tabs and multiple newlines to single spaces
        normalized = re.sub(r'[\t\n\r]+', ' ', normalized)
        
        # Remove excessive whitespace (multiple spaces become single space)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove leading/trailing whitespace
        normalized = normalized.strip()
        
        # Remove common encoding artifacts
        encoding_artifacts = [
            'â€™',  # Curly apostrophe encoding issue
            'â€œ',  # Left double quote encoding issue
            'â€',   # Right double quote encoding issue
            'â€"',  # Em dash encoding issue
            'Â',    # Non-breaking space encoding issue
        ]
        
        for artifact in encoding_artifacts:
            normalized = normalized.replace(artifact, '')
        
        return normalized


class ValidationEngine:
    """
    Engine for validating data quality against configurable criteria.
    
    This engine provides comprehensive validation for lead data including:
    - Company name professional standards validation
    - Website URL format and legitimacy validation
    - Data completeness and integrity checks
    - Professional business standards assessment
    - Context-aware validation with confidence scoring
    """
    
    def __init__(self, validation_config: Dict[str, Any]):
        """
        Initialize the validation engine.
        
        Args:
            validation_config: Configuration dictionary with validation rules
        """
        self.rules = validation_config
        self.logger = get_logger('data_cleaner')
        
        # Initialize validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'by_rule': {},
            'by_field': {}
        }
    
    def validate_company_name(self, company: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate company name against professional standards.
        
        Args:
            company: Company name to validate
            context: Additional context (lead name, etc.)
            
        Returns:
            ValidationResult with validation outcome
        """
        field_name = "company"
        
        if not company or not isinstance(company, str):
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.0,
                validation_rule="required_field",
                error_message="Company name is required",
                suggested_fix="Provide a valid company name"
            )
            self._update_validation_stats(result)
            return result
        
        company_rules = self.rules.get('company_name', {})
        min_confidence = company_rules.get('min_confidence', 0.7)
        
        # Check minimum length
        if len(company.strip()) < 2:
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.0,
                validation_rule="min_length",
                error_message="Company name too short",
                suggested_fix="Provide a company name with at least 2 characters"
            )
            self._update_validation_stats(result)
            return result
        
        # Check for forbidden patterns
        forbidden_patterns = company_rules.get('forbidden_patterns', [])
        for pattern in forbidden_patterns:
            if re.search(str(pattern), company, re.IGNORECASE):
                result = ValidationResult(
                    field_name=field_name,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_rule="forbidden_pattern",
                    error_message=f"Company name contains forbidden pattern: {pattern}",
                    suggested_fix="Remove search artifacts and provide clean company name"
                )
                self._update_validation_stats(result)
                return result
        
        # Check required format
        required_patterns = company_rules.get('required_patterns', [])
        format_valid = True
        if required_patterns:
            format_valid = any(re.match(str(pattern), company) for pattern in required_patterns)
        
        if not format_valid:
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.3,
                validation_rule="format_validation",
                error_message="Company name format is invalid",
                suggested_fix="Ensure company name contains only letters, numbers, and standard punctuation"
            )
            self._update_validation_stats(result)
            return result
        
        # Calculate confidence score
        confidence = 0.8  # Base confidence
        
        # Boost confidence for professional indicators
        professional_indicators = company_rules.get('professional_indicators', [])
        for indicator in professional_indicators:
            if indicator.lower() in company.lower():
                confidence = min(1.0, confidence + 0.1)
                break
        
        # Check if confidence meets minimum threshold
        is_valid = confidence >= min_confidence
        
        result = ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=confidence,
            validation_rule="professional_standards",
            error_message="" if is_valid else f"Company name confidence ({confidence:.2f}) below threshold ({min_confidence})",
            suggested_fix="" if is_valid else "Provide a more professional company name"
        )
        
        self._update_validation_stats(result)
        return result
    
    def validate_website_url(self, website: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate website URL format and domain.
        
        Args:
            website: Website URL to validate
            context: Additional context
            
        Returns:
            ValidationResult with validation outcome
        """
        field_name = "website"
        
        if not website or not isinstance(website, str):
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.0,
                validation_rule="required_field",
                error_message="Website URL is required",
                suggested_fix="Provide a valid website URL"
            )
            self._update_validation_stats(result)
            return result
        
        website_rules = self.rules.get('website_url', {})
        min_confidence = website_rules.get('min_confidence', 0.8)
        
        # Check required format
        required_format = website_rules.get('required_format', '')
        if required_format and not re.match(str(required_format), website):
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.0,
                validation_rule="format_validation",
                error_message="Website URL format is invalid",
                suggested_fix="Provide a valid URL starting with http:// or https://"
            )
            self._update_validation_stats(result)
            return result
        
        # Check for forbidden domains
        forbidden_domains = website_rules.get('forbidden_domains', [])
        for domain in forbidden_domains:
            if str(domain).lower() in website.lower():
                result = ValidationResult(
                    field_name=field_name,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_rule="forbidden_domain",
                    error_message=f"Website contains forbidden domain: {domain}",
                    suggested_fix="Provide a legitimate business website URL"
                )
                self._update_validation_stats(result)
                return result
        
        # Calculate confidence score
        confidence = 0.9  # Base confidence for valid format
        
        # Prefer HTTPS
        if website.startswith('https://'):
            confidence = min(1.0, confidence + 0.1)
        
        # Check if confidence meets minimum threshold
        is_valid = confidence >= min_confidence
        
        result = ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=confidence,
            validation_rule="url_validation",
            error_message="" if is_valid else f"Website confidence ({confidence:.2f}) below threshold ({min_confidence})",
            suggested_fix="" if is_valid else "Provide a more reliable website URL"
        )
        
        self._update_validation_stats(result)
        return result
    
    def validate_data_completeness(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate that required data fields are present and complete.
        
        Enhanced to handle edge cases including:
        - International company formats
        - Optional fields based on context
        - Flexible field requirements
        - Data quality scoring beyond just presence
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            ValidationResult with completeness assessment
        """
        field_name = "data_completeness"
        
        # Get configurable required fields from rules
        data_quality_rules = self.rules.get('data_quality', {})
        required_fields = data_quality_rules.get('required_fields', ['company', 'website'])
        optional_fields = data_quality_rules.get('optional_fields', ['phone', 'email', 'address'])
        
        missing_fields = []
        present_fields = []
        quality_issues = []
        
        # Check required fields
        for field in required_fields:
            field_value = data.get(field)
            if not field_value or not str(field_value).strip():
                missing_fields.append(field)
            else:
                # Check field quality beyond just presence
                field_str = str(field_value).strip()
                if len(field_str) < 2:
                    quality_issues.append(f"{field} too short")
                elif field_str.lower() in ['n/a', 'na', 'none', 'null', 'undefined', 'unknown']:
                    quality_issues.append(f"{field} contains placeholder value")
                else:
                    present_fields.append(field)
        
        # If missing critical fields, return failure
        if missing_fields:
            result = ValidationResult(
                field_name=field_name,
                is_valid=False,
                confidence_score=0.0,
                validation_rule="required_fields",
                error_message=f"Missing required fields: {', '.join(missing_fields)}",
                suggested_fix=f"Provide values for: {', '.join(missing_fields)}"
            )
            self._update_validation_stats(result)
            return result
        
        # Calculate completeness score including optional fields and quality
        total_possible_fields = len(required_fields) + len(optional_fields)
        present_optional = sum(1 for field in optional_fields if data.get(field) and str(data[field]).strip())
        
        # Base score from required fields
        base_score = len(present_fields) / len(required_fields)
        
        # Bonus score from optional fields (up to 0.2 additional)
        optional_bonus = (present_optional / len(optional_fields)) * 0.2 if optional_fields else 0
        
        # Quality penalty for issues (more aggressive)
        quality_penalty = len(quality_issues) * 0.2
        
        completeness_score = max(0.0, min(1.0, base_score + optional_bonus - quality_penalty))
        
        # Determine validity with more nuanced thresholds
        is_valid = completeness_score >= 0.8 and len(quality_issues) == 0
        
        error_message = ""
        suggested_fix = ""
        
        if not is_valid:
            issues = []
            if quality_issues:
                issues.extend(quality_issues)
            if completeness_score < 0.8:
                issues.append("insufficient data completeness")
            
            error_message = f"Data quality issues: {'; '.join(issues)}"
            suggested_fix = "Provide complete, high-quality data for all required fields"
        
        result = ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=completeness_score,
            validation_rule="completeness_check",
            error_message=error_message,
            suggested_fix=suggested_fix
        )
        
        self._update_validation_stats(result)
        return result
    
    def validate_professional_standards(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against professional business standards.
        
        Enhanced to handle edge cases including:
        - International company formats (GmbH, SA, AB, Pty Ltd, etc.)
        - Non-English company names and formats
        - Cultural variations in business naming
        - Alternative professional indicators
        - Industry-specific naming patterns
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            ValidationResult with professional standards assessment
        """
        field_name = "professional_standards"
        
        # Check for professional quality indicators
        quality_score = 0.0
        quality_checks = 0
        
        # Company name quality with international support
        company = data.get('company', '')
        company_score = 0.0
        if company:
            quality_checks += 1
            company_lower = company.lower()
            
            # International business entity indicators
            international_entities = [
                # English
                'inc', 'llc', 'corp', 'ltd', 'company', 'group', 'limited', 'corporation',
                'co.', 'co', 'plc', 'partnership', 'partners', 'associates',
                # German
                'gmbh', 'ag', 'kg', 'ohg', 'gbr',
                # French
                'sa', 'sarl', 'sas', 'sca', 'sci',
                # Spanish
                'sl', 'sa', 'srl', 'scl',
                # Italian
                'spa', 'srl', 'snc', 'sas',
                # Dutch
                'bv', 'nv', 'cv', 'vof',
                # Scandinavian
                'ab', 'as', 'aps', 'oyj',
                # Other
                'pty ltd', 'pvt ltd', 'pte ltd', 'sdn bhd', 'bhd'
            ]
            
            # Check for any business entity indicator
            entity_found = False
            for entity in international_entities:
                if entity in company_lower:
                    company_score += 0.4
                    entity_found = True
                    break
            
            # Check for proper capitalization (more flexible for international names)
            if company and (company[0].isupper() or any(c.isupper() for c in company[:3])):
                company_score += 0.2
            
            # International business-like words
            business_words = [
                # English
                'services', 'solutions', 'consulting', 'business', 'systems', 'technologies',
                'international', 'global', 'worldwide', 'enterprises', 'industries',
                'manufacturing', 'trading', 'holdings', 'investments', 'development',
                # Common international terms
                'tech', 'digital', 'software', 'engineering', 'construction', 'finance',
                'medical', 'pharmaceutical', 'automotive', 'logistics', 'transport'
            ]
            
            if any(word in company_lower for word in business_words):
                company_score += 0.2
            
            # Additional scoring for professional patterns
            # Multi-word company names (more professional)
            if len(company.split()) >= 2:
                company_score += 0.1
            
            # Reasonable length (not too short, not too long)
            if 3 <= len(company) <= 80:
                company_score += 0.1
            
            # Penalty for obvious non-professional patterns
            unprofessional_patterns = [
                'test', 'demo', 'sample', 'example', 'placeholder', 'temp',
                'xxx', '123', 'abc', 'company1', 'mycompany'
            ]
            
            # More aggressive penalty for unprofessional patterns
            for pattern in unprofessional_patterns:
                if pattern in company_lower:
                    company_score -= 0.8  # Very strong penalty to ensure failure
                    break
            
            quality_score += min(1.0, company_score)  # Cap company score at 1.0
        
        # Website quality with international domain support
        website = data.get('website', '')
        website_score = 0.0
        if website:
            quality_checks += 1
            website_lower = website.lower()
            
            # Protocol scoring
            if website.startswith('https://'):
                website_score += 0.4
            elif website.startswith('http://'):
                website_score += 0.2
            
            # Professional domain indicators
            if not any(social in website_lower for social in [
                'facebook', 'linkedin', 'twitter', 'instagram', 'tiktok',
                'youtube', 'snapchat', 'pinterest', 'reddit'
            ]):
                website_score += 0.3
            
            # International TLD support
            professional_tlds = [
                '.com', '.org', '.net', '.biz', '.info', '.pro',
                # Country codes
                '.ca', '.uk', '.de', '.fr', '.it', '.es', '.nl', '.se', '.no', '.dk',
                '.au', '.nz', '.jp', '.kr', '.cn', '.in', '.br', '.mx', '.ar',
                '.co.uk', '.com.au', '.co.nz', '.co.jp', '.co.kr', '.com.br'
            ]
            
            if any(tld in website_lower for tld in professional_tlds):
                website_score += 0.2
            
            # Bonus for country-specific business domains
            business_domains = ['.biz', '.pro', '.company', '.business']
            if any(domain in website_lower for domain in business_domains):
                website_score += 0.1
            
            quality_score += min(1.0, website_score)  # Cap website score at 1.0
        
        # Calculate final professional score
        professional_score = quality_score / max(quality_checks, 1) if quality_checks > 0 else 0.0
        
        # Enhanced validation logic with cultural considerations
        is_valid = False
        
        if professional_score >= 0.6:
            is_valid = True  # High quality
        elif professional_score >= 0.45:
            # Check for moderate quality with business indicators
            company_str = str(data.get('company', '')).lower()
            if any(word in company_str for word in ['services', 'business', 'solutions', 'consulting']):
                is_valid = True
            # Or international entity indicators
            elif any(entity in company_str for entity in ['gmbh', 'sarl', 'pty ltd', 'pvt ltd']):
                is_valid = True
        elif professional_score >= 0.3:
            # Very lenient for international companies with entity indicators
            company_str = str(data.get('company', '')).lower()
            international_entities = ['gmbh', 'sa', 'ab', 'bv', 'nv', 'pty ltd', 'pvt ltd', 'sdn bhd']
            # But not if it contains unprofessional patterns
            has_entity = any(entity in company_str for entity in international_entities)
            has_unprofessional = any(pattern in company_str for pattern in ['test', 'demo', 'sample', 'example'])
            if has_entity and not has_unprofessional:
                is_valid = True
        
        result = ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=professional_score,
            validation_rule="professional_quality",
            error_message="" if is_valid else f"Professional quality score ({professional_score:.2f}) below threshold",
            suggested_fix="" if is_valid else "Improve data quality with more professional business information"
        )
        
        self._update_validation_stats(result)
        return result
    
    def validate_context_consistency(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """
        Validate that data is consistent with the provided context.
        
        Args:
            data: Data dictionary to validate
            context: Context information (lead name, etc.)
            
        Returns:
            ValidationResult with consistency assessment
        """
        field_name = "context_consistency"
        
        consistency_score = 1.0  # Start with perfect consistency
        issues = []
        
        company = data.get('company', '')
        website = data.get('website', '')
        lead_name = context.get('Full Name', '')
        
        # Check if company name and website domain are related
        if company and website:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(website)
                domain = parsed_url.netloc.lower().replace('www.', '')
                
                # Extract company name words for comparison
                company_words = re.findall(r'\b\w+\b', company.lower())
                company_words = [w for w in company_words if len(w) > 2 and w not in ['inc', 'llc', 'corp', 'ltd', 'the', 'and', 'of', 'gmbh', 'sarl', 'pty', 'sdn', 'bhd']]
                
                # Check if any company words appear in domain (with international character handling)
                domain_match = False
                for word in company_words:
                    # Direct match
                    if word in domain:
                        domain_match = True
                        break
                    # Handle common international character substitutions
                    word_normalized = word.replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae')
                    if word_normalized in domain:
                        domain_match = True
                        break
                    # Check if domain contains normalized version
                    if any(word_normalized in part for part in domain.split('.')):
                        domain_match = True
                        break
                
                if not domain_match and len(company_words) > 0:
                    consistency_score -= 0.4  # More aggressive penalty for unrelated domains
                    issues.append("Company name and website domain don't appear related")
                    
            except Exception:
                pass
        
        # Check for suspicious patterns that might indicate data mixing
        if lead_name and company:
            # Check if lead name appears in company name (might indicate confusion)
            name_parts = lead_name.lower().split()
            for name_part in name_parts:
                if len(name_part) > 2 and name_part in company.lower():
                    consistency_score -= 0.2
                    issues.append("Lead name appears in company name - possible data confusion")
                    break
        
        # Validate that data makes business sense
        if company and website:
            # Check for obvious mismatches
            mismatch_patterns = [
                ('google', ['google.com']),
                ('facebook', ['facebook.com']),
                ('linkedin', ['linkedin.com']),
                ('twitter', ['twitter.com'])
            ]
            
            for company_pattern, domain_patterns in mismatch_patterns:
                if company_pattern in company.lower():
                    for domain_pattern in domain_patterns:
                        if domain_pattern in website.lower():
                            consistency_score -= 0.5
                            issues.append(f"Company mentions {company_pattern} but website is {domain_pattern}")
        
        is_valid = consistency_score >= 0.7
        
        return ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=consistency_score,
            validation_rule="context_consistency",
            error_message="" if is_valid else f"Data consistency issues: {'; '.join(issues)}",
            suggested_fix="" if is_valid else "Review data for consistency and accuracy"
        )
    
    def validate_business_legitimacy(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """
        Validate that the data represents a legitimate business entity.
        
        Args:
            data: Data dictionary to validate
            context: Context information
            
        Returns:
            ValidationResult with business legitimacy assessment
        """
        field_name = "business_legitimacy"
        
        legitimacy_score = 0.0
        legitimacy_checks = 0
        
        company = data.get('company', '')
        website = data.get('website', '')
        
        # Company legitimacy indicators
        if company:
            legitimacy_checks += 1
            company_score = 0.0
            
            # Check for business entity indicators
            business_entities = ['inc', 'llc', 'corp', 'ltd', 'company', 'group', 'partners', 'associates']
            if any(entity in company.lower() for entity in business_entities):
                company_score += 0.4
            
            # Check for professional naming patterns
            if re.match(r'^[A-Z][a-zA-Z0-9\s&,.\'-]+$', company):
                company_score += 0.2
            
            # Check for reasonable length (not too short or too long)
            if 3 <= len(company) <= 80:
                company_score += 0.2
            
            # Check for business-like words
            business_words = ['solutions', 'services', 'systems', 'technologies', 'consulting', 'group', 'international']
            if any(word in company.lower() for word in business_words):
                company_score += 0.2
            
            legitimacy_score += min(1.0, company_score)
        
        # Website legitimacy indicators
        if website:
            legitimacy_checks += 1
            website_score = 0.0
            
            # Check for professional domain structure
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(website)
                domain = parsed_url.netloc.lower()
                
                # Professional TLDs
                professional_tlds = ['.com', '.org', '.net', '.biz', '.info', '.ca', '.co.uk', '.de', '.fr']
                if any(domain.endswith(tld) for tld in professional_tlds):
                    website_score += 0.3
                
                # HTTPS preference
                if website.startswith('https://'):
                    website_score += 0.2
                
                # Reasonable domain length
                if 4 <= len(domain) <= 50:
                    website_score += 0.2
                
                # Not a subdomain of major platforms
                platform_domains = ['blogspot.com', 'wordpress.com', 'wix.com', 'squarespace.com']
                if not any(platform in domain for platform in platform_domains):
                    website_score += 0.3
                
                legitimacy_score += min(1.0, website_score)
                
            except Exception:
                pass
        
        # Calculate final legitimacy score
        final_score = legitimacy_score / max(legitimacy_checks, 1) if legitimacy_checks > 0 else 0.0
        
        is_valid = final_score >= 0.6
        
        return ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=final_score,
            validation_rule="business_legitimacy",
            error_message="" if is_valid else f"Business legitimacy score ({final_score:.2f}) below threshold (0.6)",
            suggested_fix="" if is_valid else "Provide more professional business information"
        )
    
    def validate_data_freshness(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """
        Validate that the data appears fresh and not stale/cached.
        
        Args:
            data: Data dictionary to validate
            context: Context information
            
        Returns:
            ValidationResult with data freshness assessment
        """
        field_name = "data_freshness"
        
        freshness_score = 1.0  # Start assuming fresh
        staleness_indicators = []
        
        company = data.get('company', '')
        website = data.get('website', '')
        
        # Check for stale data indicators
        stale_patterns = [
            r'cached',
            r'archived',
            r'old',
            r'previous',
            r'former',
            r'ex-',
            r'outdated',
            r'legacy'
        ]
        
        for pattern in stale_patterns:
            if company and re.search(pattern, company, re.IGNORECASE):
                freshness_score -= 0.3
                staleness_indicators.append(f"Company name contains stale indicator: {pattern}")
            
            if website and re.search(pattern, website, re.IGNORECASE):
                freshness_score -= 0.3
                staleness_indicators.append(f"Website contains stale indicator: {pattern}")
        
        # Check for placeholder or template data
        placeholder_patterns = [
            r'example',
            r'sample',
            r'test',
            r'demo',
            r'placeholder',
            r'template',
            r'default'
        ]
        
        for pattern in placeholder_patterns:
            if company and re.search(pattern, company, re.IGNORECASE):
                freshness_score -= 0.4
                staleness_indicators.append(f"Company name appears to be placeholder: {pattern}")
            
            if website and re.search(pattern, website, re.IGNORECASE):
                freshness_score -= 0.4
                staleness_indicators.append(f"Website appears to be placeholder: {pattern}")
        
        freshness_score = max(0.0, freshness_score)
        is_valid = freshness_score >= 0.7
        
        return ValidationResult(
            field_name=field_name,
            is_valid=is_valid,
            confidence_score=freshness_score,
            validation_rule="data_freshness",
            error_message="" if is_valid else f"Data freshness issues: {'; '.join(staleness_indicators)}",
            suggested_fix="" if is_valid else "Ensure data is current and not from cached/stale sources"
        )
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        total = self.validation_stats['total_validations']
        if total == 0:
            return {
                'total_validations': 0,
                'success_rate': 0.0,
                'failure_rate': 0.0,
                'by_rule': {},
                'by_field': {}
            }
        
        return {
            'total_validations': total,
            'success_rate': (self.validation_stats['passed_validations'] / total) * 100,
            'failure_rate': (self.validation_stats['failed_validations'] / total) * 100,
            'by_rule': dict(self.validation_stats['by_rule']),
            'by_field': dict(self.validation_stats['by_field'])
        }
    
    def _update_validation_stats(self, result: ValidationResult) -> None:
        """Update internal validation statistics."""
        self.validation_stats['total_validations'] += 1
        
        if result.is_valid:
            self.validation_stats['passed_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
        
        # Update by rule
        rule = result.validation_rule
        if rule not in self.validation_stats['by_rule']:
            self.validation_stats['by_rule'][rule] = {'passed': 0, 'failed': 0}
        
        if result.is_valid:
            self.validation_stats['by_rule'][rule]['passed'] += 1
        else:
            self.validation_stats['by_rule'][rule]['failed'] += 1
        
        # Update by field
        field = result.field_name
        if field not in self.validation_stats['by_field']:
            self.validation_stats['by_field'][field] = {'passed': 0, 'failed': 0}
        
        if result.is_valid:
            self.validation_stats['by_field'][field]['passed'] += 1
        else:
            self.validation_stats['by_field'][field]['failed'] += 1


class ConfigurationManager:
    """
    Enhanced configuration manager for the data cleaner.
    
    Features:
    - Configuration versioning and change tracking
    - Comprehensive rule integrity validation
    - Backup and rollback capabilities
    - Configuration schema validation
    - Hot-reload support
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration directory
        """
        self.logger = get_logger('data_cleaner')
        
        # Set default config path relative to this file
        if config_path is None:
            config_path = Path(__file__).parent / "data_cleaner_config"
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config_path.mkdir(exist_ok=True)
        
        # Initialize versioning and change tracking
        self.version_history = []
        self.current_version = None
        self.config_checksums = {}
        
        # Create backup directory
        self.backup_path = self.config_path / "backups"
        self.backup_path.mkdir(exist_ok=True)
        
        # Load or create default configurations
        self.cleaning_rules = self.load_rules('cleaning_rules.yaml')
        self.validation_rules = self.load_rules('validation_rules.yaml')
        
        # Initialize version tracking
        self._initialize_version_tracking()
    
    def load_rules(self, filename: str) -> Dict[str, Any]:
        """
        Load rules from configuration file with integrity checking.
        
        Args:
            filename: Configuration filename
            
        Returns:
            Configuration dictionary
        """
        config_file = self.config_path / filename
        
        try:
            if config_file.exists():
                # Read and validate configuration
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    config = yaml.safe_load(config_content)
                
                # Validate configuration integrity
                if not self.validate_config(config or {}):
                    self.logger.log_module_activity('data_cleaner', 'system', 'warning', {
                        'message': f'Configuration validation failed for {filename}, using defaults',
                        'filename': filename
                    })
                    return self._get_default_config(filename)
                
                # Calculate and store checksum for change tracking
                import hashlib
                checksum = hashlib.md5(config_content.encode()).hexdigest()
                self.config_checksums[filename] = checksum
                
                self.logger.log_module_activity('data_cleaner', 'system', 'success', {
                    'message': f'Loaded configuration from {filename}',
                    'config_keys': list(config.keys()) if config else [],
                    'checksum': checksum[:8]  # First 8 chars for logging
                })
                
                return config or {}
            else:
                # Create default configuration
                default_config = self._get_default_config(filename)
                self._save_config(filename, default_config)
                return default_config
                
        except yaml.YAMLError as e:
            self.logger.log_error(e, {
                'action': 'load_rules',
                'filename': filename,
                'error_type': 'yaml_parsing',
                'config_path': str(config_file)
            })
            return self._get_default_config(filename)
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'load_rules',
                'filename': filename,
                'config_path': str(config_file)
            })
            return self._get_default_config(filename)
    
    def _get_default_config(self, filename: str) -> Dict[str, Any]:
        """Get default configuration for a given filename."""
        if filename == 'cleaning_rules.yaml':
            return {
                'company_name': {
                    'remove_patterns': [
                        r'google',
                        r'search results?',
                        r'linkedin',
                        r'Some results may have been.*',
                        r'Learn more Next',
                        r'About \d+.*results',
                        r'Sirius XM and.*',
                        r'delisted consistent with local laws'
                    ],
                    'normalize_patterns': [
                        {'pattern': r'\s+Inc\.?$', 'replacement': ' Inc'},
                        {'pattern': r'\s+LLC\.?$', 'replacement': ' LLC'},
                        {'pattern': r'\s+Corp\.?$', 'replacement': ' Corp'},
                        {'pattern': r'\s+Ltd\.?$', 'replacement': ' Ltd'}
                    ],
                    'min_length': 2,
                    'max_length': 100
                },
                'website_url': {
                    'remove_patterns': [
                        'google.com',
                        'linkedin.com',
                        'facebook.com',
                        'twitter.com',
                        'instagram.com'
                    ],
                    'required_protocols': ['http://', 'https://'],
                    'domain_validation': True
                },
                'search_artifacts': {
                    'remove_patterns': [
                        r'Some results may have been delisted consistent with local laws.*',
                        r'Learn more Next',
                        r'About [0-9,]+ results',
                        r'Search instead for.*',
                        r'Did you mean:.*',
                        r'Showing results for.*'
                    ]
                }
            }
        elif filename == 'validation_rules.yaml':
            return {
                'company_name': {
                    'min_confidence': 0.7,
                    'required_patterns': [r'^[A-Za-z0-9\s&,.\'\-]+$'],
                    'forbidden_patterns': [
                        'google',
                        'search',
                        'results',
                        'linkedin',
                        'facebook'
                    ],
                    'professional_indicators': [
                        'Inc',
                        'LLC',
                        'Corp',
                        'Ltd',
                        'Company',
                        'Group',
                        'Partners'
                    ]
                },
                'website_url': {
                    'min_confidence': 0.8,
                    'required_format': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$',
                    'forbidden_domains': [
                        'google.com',
                        'linkedin.com',
                        'facebook.com',
                        'twitter.com',
                        'instagram.com'
                    ],
                    'ssl_preferred': True
                }
            }
        else:
            return {}
    
    def _save_config(self, filename: str, config: Dict[str, Any]) -> None:
        """Save configuration to file and update checksum."""
        config_file = self.config_path / filename
        
        try:
            # Convert config to YAML string
            yaml_content = yaml.dump(config, default_flow_style=False, indent=2)
            
            # Write to file
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # Update checksum for change tracking
            import hashlib
            checksum = hashlib.md5(yaml_content.encode()).hexdigest()
            self.config_checksums[filename] = checksum
                
            self.logger.log_module_activity('data_cleaner', 'system', 'success', {
                'message': f'Saved configuration to {filename}',
                'checksum': checksum[:8]  # First 8 chars for logging
            })
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'save_config',
                'filename': filename
            })
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Comprehensive configuration validation with rule integrity checks.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            # Basic structure validation
            if not isinstance(config, dict):
                self.logger.log_module_activity('data_cleaner', 'config_validation', 'error', {
                    'message': 'Configuration is not a dictionary',
                    'type': type(config).__name__
                })
                return False
            
            # Validate cleaning rules structure
            if 'company_name' in config:
                if not self._validate_company_name_rules(config['company_name']):
                    return False
            
            if 'website_url' in config:
                if not self._validate_website_url_rules(config['website_url']):
                    return False
            
            if 'search_artifacts' in config:
                if not self._validate_search_artifacts_rules(config['search_artifacts']):
                    return False
            
            if 'data_quality' in config:
                if not self._validate_data_quality_rules(config['data_quality']):
                    return False
            
            # Validate regex patterns
            if not self._validate_regex_patterns(config):
                return False
            
            self.logger.log_module_activity('data_cleaner', 'config_validation', 'success', {
                'message': 'Configuration validation passed',
                'sections': list(config.keys())
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'validate_config'})
            return False
    
    def _validate_company_name_rules(self, rules: Dict[str, Any]) -> bool:
        """Validate company name rules structure."""
        if not isinstance(rules, dict):
            return False
        
        # Validate remove_patterns
        if 'remove_patterns' in rules:
            if not isinstance(rules['remove_patterns'], list):
                return False
            for pattern in rules['remove_patterns']:
                if not isinstance(pattern, str):
                    return False
        
        # Validate normalize_patterns
        if 'normalize_patterns' in rules:
            if not isinstance(rules['normalize_patterns'], list):
                return False
            for pattern_config in rules['normalize_patterns']:
                if not isinstance(pattern_config, dict):
                    return False
                if 'pattern' not in pattern_config or 'replacement' not in pattern_config:
                    return False
        
        # Validate confidence thresholds
        if 'min_confidence' in rules:
            confidence = rules['min_confidence']
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                return False
        
        return True
    
    def _validate_website_url_rules(self, rules: Dict[str, Any]) -> bool:
        """Validate website URL rules structure."""
        if not isinstance(rules, dict):
            return False
        
        # Validate remove_patterns/forbidden_domains
        for key in ['remove_patterns', 'forbidden_domains']:
            if key in rules:
                if not isinstance(rules[key], list):
                    return False
                for domain in rules[key]:
                    if not isinstance(domain, str):
                        return False
        
        # Validate required_format
        if 'required_format' in rules:
            if not isinstance(rules['required_format'], str):
                return False
        
        # Validate confidence thresholds
        if 'min_confidence' in rules:
            confidence = rules['min_confidence']
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                return False
        
        return True
    
    def _validate_search_artifacts_rules(self, rules: Dict[str, Any]) -> bool:
        """Validate search artifacts rules structure."""
        if not isinstance(rules, dict):
            return False
        
        if 'remove_patterns' in rules:
            if not isinstance(rules['remove_patterns'], list):
                return False
            for pattern in rules['remove_patterns']:
                if not isinstance(pattern, str):
                    return False
        
        return True
    
    def _validate_data_quality_rules(self, rules: Dict[str, Any]) -> bool:
        """Validate data quality rules structure."""
        if not isinstance(rules, dict):
            return False
        
        # Validate required_fields
        if 'required_fields' in rules:
            if not isinstance(rules['required_fields'], list):
                return False
            for field in rules['required_fields']:
                if not isinstance(field, str):
                    return False
        
        # Validate optional_fields
        if 'optional_fields' in rules:
            if not isinstance(rules['optional_fields'], list):
                return False
            for field in rules['optional_fields']:
                if not isinstance(field, str):
                    return False
        
        # Validate thresholds
        for threshold_key in ['min_overall_confidence', 'professional_standards_threshold']:
            if threshold_key in rules:
                threshold = rules[threshold_key]
                if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
                    return False
        
        return True
    
    def _validate_regex_patterns(self, config: Dict[str, Any]) -> bool:
        """Validate that all regex patterns are valid."""
        import re
        
        patterns_to_check = []
        
        # Collect all regex patterns from config
        for section_name, section in config.items():
            if isinstance(section, dict):
                # Check remove_patterns
                if 'remove_patterns' in section and isinstance(section['remove_patterns'], list):
                    patterns_to_check.extend(section['remove_patterns'])
                
                # Check normalize_patterns
                if 'normalize_patterns' in section and isinstance(section['normalize_patterns'], list):
                    for pattern_config in section['normalize_patterns']:
                        if isinstance(pattern_config, dict) and 'pattern' in pattern_config:
                            patterns_to_check.append(pattern_config['pattern'])
                
                # Check required_format
                if 'required_format' in section:
                    patterns_to_check.append(section['required_format'])
        
        # Validate each pattern
        for pattern in patterns_to_check:
            if isinstance(pattern, str):
                try:
                    re.compile(pattern)
                except re.error as e:
                    self.logger.log_module_activity('data_cleaner', 'config_validation', 'error', {
                        'message': f'Invalid regex pattern: {pattern}',
                        'error': str(e)
                    })
                    return False
        
        return True
    
    def update_rules(self, new_rules: Dict[str, Any], reason: str = "Manual update") -> bool:
        """
        Update rules configuration with versioning and backup.
        
        Args:
            new_rules: New rules to apply
            reason: Reason for the update
            
        Returns:
            True if update successful
        """
        try:
            # Validate new rules first
            if not self.validate_config(new_rules):
                self.logger.log_module_activity('data_cleaner', 'update_rules', 'error', {
                    'message': 'New rules failed validation',
                    'reason': reason
                })
                return False
            
            # Create backup before update
            backup_version = self.create_backup(f"Pre-update backup: {reason}")
            if not backup_version:
                self.logger.log_module_activity('data_cleaner', 'update_rules', 'warning', {
                    'message': 'Failed to create backup, proceeding with update',
                    'reason': reason
                })
            
            updated_files = []
            
            # Update cleaning rules
            if 'cleaning_rules' in new_rules:
                self.cleaning_rules.update(new_rules['cleaning_rules'])
                self._save_config('cleaning_rules.yaml', self.cleaning_rules)
                updated_files.append('cleaning_rules.yaml')
            
            # Update validation rules
            if 'validation_rules' in new_rules:
                self.validation_rules.update(new_rules['validation_rules'])
                self._save_config('validation_rules.yaml', self.validation_rules)
                updated_files.append('validation_rules.yaml')
            
            # Update version tracking
            self.current_version = datetime.datetime.now().isoformat()
            update_record = {
                'version': self.current_version,
                'timestamp': datetime.datetime.now().isoformat(),
                'reason': reason,
                'files': updated_files,
                'backup_version': backup_version
            }
            
            self.version_history.append(update_record)
            self._save_version_history()
            
            self.logger.log_module_activity('data_cleaner', 'update_rules', 'success', {
                'message': 'Rules updated successfully',
                'reason': reason,
                'files': updated_files,
                'version': self.current_version
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'update_rules',
                'reason': reason
            })
            return False
    
    def get_rule_version(self) -> str:
        """Get current rule version timestamp."""
        return self.current_version or datetime.datetime.now().isoformat()
    
    def _initialize_version_tracking(self) -> None:
        """Initialize version tracking system."""
        try:
            version_file = self.config_path / "version_history.json"
            
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self.version_history = version_data.get('history', [])
                    self.current_version = version_data.get('current_version')
            else:
                # Create initial version
                self.current_version = datetime.datetime.now().isoformat()
                self._save_version_history()
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'initialize_version_tracking'})
            self.current_version = datetime.datetime.now().isoformat()
    
    def _save_version_history(self) -> None:
        """Save version history to file."""
        try:
            version_file = self.config_path / "version_history.json"
            version_data = {
                'current_version': self.current_version,
                'history': self.version_history,
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2)
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'save_version_history'})
    
    def create_backup(self, reason: str = "Manual backup") -> str:
        """
        Create a backup of current configuration.
        
        Args:
            reason: Reason for creating backup
            
        Returns:
            Backup version identifier
        """
        try:
            backup_version = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_path / backup_version
            backup_dir.mkdir(exist_ok=True)
            
            # Backup all configuration files
            config_files = ['cleaning_rules.yaml', 'validation_rules.yaml']
            backed_up_files = []
            
            for filename in config_files:
                source_file = self.config_path / filename
                if source_file.exists():
                    backup_file = backup_dir / filename
                    import shutil
                    shutil.copy2(source_file, backup_file)
                    backed_up_files.append(filename)
            
            # Record backup in version history
            backup_record = {
                'version': backup_version,
                'timestamp': datetime.datetime.now().isoformat(),
                'reason': reason,
                'files': backed_up_files,
                'checksums': dict(self.config_checksums)
            }
            
            self.version_history.append(backup_record)
            self._save_version_history()
            
            self.logger.log_module_activity('data_cleaner', 'backup', 'success', {
                'message': f'Configuration backup created: {backup_version}',
                'reason': reason,
                'files': backed_up_files
            })
            
            return backup_version
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'create_backup',
                'reason': reason
            })
            return ""
    
    def restore_backup(self, backup_version: str) -> bool:
        """
        Restore configuration from backup.
        
        Args:
            backup_version: Version identifier to restore
            
        Returns:
            True if restore successful
        """
        try:
            backup_dir = self.backup_path / backup_version
            if not backup_dir.exists():
                self.logger.log_module_activity('data_cleaner', 'restore', 'error', {
                    'message': f'Backup version not found: {backup_version}'
                })
                return False
            
            # Create backup of current state before restore
            self.create_backup(f"Pre-restore backup before restoring {backup_version}")
            
            # Restore files
            config_files = ['cleaning_rules.yaml', 'validation_rules.yaml']
            restored_files = []
            
            for filename in config_files:
                backup_file = backup_dir / filename
                if backup_file.exists():
                    target_file = self.config_path / filename
                    import shutil
                    shutil.copy2(backup_file, target_file)
                    restored_files.append(filename)
            
            # Reload configurations
            self.cleaning_rules = self.load_rules('cleaning_rules.yaml')
            self.validation_rules = self.load_rules('validation_rules.yaml')
            
            # Update version tracking
            self.current_version = datetime.datetime.now().isoformat()
            restore_record = {
                'version': self.current_version,
                'timestamp': datetime.datetime.now().isoformat(),
                'reason': f'Restored from backup {backup_version}',
                'files': restored_files,
                'restored_from': backup_version
            }
            
            self.version_history.append(restore_record)
            self._save_version_history()
            
            self.logger.log_module_activity('data_cleaner', 'restore', 'success', {
                'message': f'Configuration restored from backup: {backup_version}',
                'files': restored_files
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'restore_backup',
                'backup_version': backup_version
            })
            return False
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get configuration version history."""
        return list(self.version_history)
    
    def detect_config_changes(self) -> Dict[str, bool]:
        """
        Detect if configuration files have changed since last load.
        
        Returns:
            Dictionary mapping filename to changed status
        """
        changes = {}
        
        try:
            import hashlib
            
            config_files = ['cleaning_rules.yaml', 'validation_rules.yaml']
            
            for filename in config_files:
                config_file = self.config_path / filename
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    current_checksum = hashlib.md5(current_content.encode()).hexdigest()
                    stored_checksum = self.config_checksums.get(filename)
                    
                    changes[filename] = current_checksum != stored_checksum
                else:
                    changes[filename] = True  # File missing is a change
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'detect_config_changes'})
            # Assume changes if we can't detect
            changes = {f: True for f in ['cleaning_rules.yaml', 'validation_rules.yaml']}
        
        return changes
    
    def reload_if_changed(self) -> bool:
        """
        Reload configurations if files have changed.
        
        Returns:
            True if configurations were reloaded
        """
        changes = self.detect_config_changes()
        
        if any(changes.values()):
            self.logger.log_module_activity('data_cleaner', 'hot_reload', 'info', {
                'message': 'Configuration changes detected, reloading',
                'changed_files': [f for f, changed in changes.items() if changed]
            })
            
            # Create backup before reload
            self.create_backup("Pre-reload backup")
            
            # Reload configurations
            self.cleaning_rules = self.load_rules('cleaning_rules.yaml')
            self.validation_rules = self.load_rules('validation_rules.yaml')
            
            # Update version
            self.current_version = datetime.datetime.now().isoformat()
            self._save_version_history()
            
            return True
        
        return False


class AuditLogger:
    """
    Comprehensive audit logging and metrics system for the data cleaner.
    
    Provides detailed tracking of cleaning actions, validation decisions,
    performance metrics, and quality reporting capabilities.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the audit logger with comprehensive metrics tracking.
        
        Args:
            log_dir: Directory for storing audit log files
        """
        self.logger = get_logger('data_cleaner')
        
        # Set up log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.cwd() / 'logs' / 'data_cleaner'
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize comprehensive statistics tracking
        self.cleaning_stats = {
            'total_cleanings': 0,
            'successful_cleanings': 0,
            'patterns_applied': 0,
            'fields_cleaned': {},
            'rules_usage': {},
            'confidence_scores': [],
            'processing_times': [],
            'start_time': datetime.datetime.now()
        }
        
        self.validation_stats = {
            'total_validations': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'by_field': {},
            'by_rule': {},
            'confidence_scores': [],
            'error_patterns': {},
            'start_time': datetime.datetime.now()
        }
        
        self.performance_stats = {
            'total_operations': 0,
            'total_duration': 0.0,
            'total_records_processed': 0,
            'operations_by_type': {},
            'peak_memory_usage': 0,
            'average_throughput': 0.0,
            'start_time': datetime.datetime.now()
        }
        
        # Initialize log storage
        self.cleaning_logs = []
        self.validation_logs = []
        self.performance_logs = []
        self.quality_metrics = []
        
        self.logger.log_module_activity('data_cleaner', 'audit_logger', 'success', {
            'message': 'AuditLogger initialized with comprehensive metrics',
            'log_dir': str(self.log_dir)
        })
    
    def log_cleaning_action(self, cleaning_result: 'CleaningResult') -> None:
        """
        Log a comprehensive cleaning action with detailed metrics.
        
        Args:
            cleaning_result: Complete cleaning result with all metadata
        """
        try:
            # Update statistics
            self.cleaning_stats['total_cleanings'] += 1
            self.cleaning_stats['patterns_applied'] += len(cleaning_result.patterns_applied)
            
            # Track field-specific statistics
            field = cleaning_result.field_name
            if field not in self.cleaning_stats['fields_cleaned']:
                self.cleaning_stats['fields_cleaned'][field] = {
                    'count': 0,
                    'changes_made': 0,
                    'avg_confidence': 0.0
                }
            
            self.cleaning_stats['fields_cleaned'][field]['count'] += 1
            if cleaning_result.original_value != cleaning_result.cleaned_value:
                self.cleaning_stats['fields_cleaned'][field]['changes_made'] += 1
                self.cleaning_stats['successful_cleanings'] += 1
            
            # Track rule usage
            for pattern in cleaning_result.patterns_applied:
                if pattern not in self.cleaning_stats['rules_usage']:
                    self.cleaning_stats['rules_usage'][pattern] = 0
                self.cleaning_stats['rules_usage'][pattern] += 1
            
            # Track confidence scores and processing times
            self.cleaning_stats['confidence_scores'].append(cleaning_result.confidence_score)
            self.cleaning_stats['processing_times'].append(cleaning_result.processing_time)
            
            # Create detailed log entry
            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'field_name': cleaning_result.field_name,
                'original_value': cleaning_result.original_value,
                'cleaned_value': cleaning_result.cleaned_value,
                'patterns_applied': cleaning_result.patterns_applied,
                'confidence_score': cleaning_result.confidence_score,
                'processing_time': cleaning_result.processing_time,
                'changed': cleaning_result.original_value != cleaning_result.cleaned_value
            }
            
            self.cleaning_logs.append(log_entry)
            
            # Log to system logger
            self.logger.log_module_activity('data_cleaner', 'cleaning', 'info', {
                'field': cleaning_result.field_name,
                'patterns': len(cleaning_result.patterns_applied),
                'confidence': cleaning_result.confidence_score,
                'changed': cleaning_result.original_value != cleaning_result.cleaned_value,
                'processing_time': cleaning_result.processing_time
            })
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'log_cleaning_action'})
    
    def log_validation_decision(self, validation_result: ValidationResult) -> None:
        """
        Log a comprehensive validation decision with detailed metrics.
        
        Args:
            validation_result: Complete validation result with all metadata
        """
        try:
            # Update statistics
            self.validation_stats['total_validations'] += 1
            
            if validation_result.is_valid:
                self.validation_stats['valid_count'] += 1
            else:
                self.validation_stats['invalid_count'] += 1
            
            # Track field-specific statistics
            field = validation_result.field_name
            if field not in self.validation_stats['by_field']:
                self.validation_stats['by_field'][field] = {
                    'total': 0,
                    'valid': 0,
                    'invalid': 0,
                    'avg_confidence': 0.0
                }
            
            self.validation_stats['by_field'][field]['total'] += 1
            if validation_result.is_valid:
                self.validation_stats['by_field'][field]['valid'] += 1
            else:
                self.validation_stats['by_field'][field]['invalid'] += 1
            
            # Track rule-specific statistics
            rule = validation_result.validation_rule
            if rule not in self.validation_stats['by_rule']:
                self.validation_stats['by_rule'][rule] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0
                }
            
            self.validation_stats['by_rule'][rule]['total'] += 1
            if validation_result.is_valid:
                self.validation_stats['by_rule'][rule]['passed'] += 1
            else:
                self.validation_stats['by_rule'][rule]['failed'] += 1
            
            # Track error patterns
            if validation_result.error_message:
                error_key = validation_result.error_message[:50]  # First 50 chars as key
                if error_key not in self.validation_stats['error_patterns']:
                    self.validation_stats['error_patterns'][error_key] = 0
                self.validation_stats['error_patterns'][error_key] += 1
            
            # Track confidence scores
            self.validation_stats['confidence_scores'].append(validation_result.confidence_score)
            
            # Create detailed log entry
            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'field_name': validation_result.field_name,
                'is_valid': validation_result.is_valid,
                'confidence_score': validation_result.confidence_score,
                'validation_rule': validation_result.validation_rule,
                'error_message': validation_result.error_message,
                'suggested_fix': validation_result.suggested_fix
            }
            
            self.validation_logs.append(log_entry)
            
            # Log to system logger
            self.logger.log_module_activity('data_cleaner', 'validation', 
                                           'success' if validation_result.is_valid else 'warning', {
                'field': validation_result.field_name,
                'valid': validation_result.is_valid,
                'confidence': validation_result.confidence_score,
                'rule': validation_result.validation_rule
            })
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'log_validation_decision'})
    
    def log_performance_metrics(self, operation: str, duration: float, records_processed: int = 1) -> None:
        """
        Log performance metrics for operations.
        
        Args:
            operation: Name of the operation performed
            duration: Time taken in seconds
            records_processed: Number of records processed
        """
        try:
            # Update performance statistics
            self.performance_stats['total_operations'] += 1
            self.performance_stats['total_duration'] += duration
            self.performance_stats['total_records_processed'] += records_processed
            
            # Track operation-specific metrics
            if operation not in self.performance_stats['operations_by_type']:
                self.performance_stats['operations_by_type'][operation] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'total_records': 0,
                    'avg_duration': 0.0,
                    'avg_throughput': 0.0
                }
            
            op_stats = self.performance_stats['operations_by_type'][operation]
            op_stats['count'] += 1
            op_stats['total_duration'] += duration
            op_stats['total_records'] += records_processed
            op_stats['avg_duration'] = op_stats['total_duration'] / op_stats['count']
            op_stats['avg_throughput'] = op_stats['total_records'] / op_stats['total_duration'] if op_stats['total_duration'] > 0 else 0
            
            # Update overall average throughput
            if self.performance_stats['total_duration'] > 0:
                self.performance_stats['average_throughput'] = (
                    self.performance_stats['total_records_processed'] / 
                    self.performance_stats['total_duration']
                )
            
            # Create detailed log entry
            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'operation': operation,
                'duration': duration,
                'records_processed': records_processed,
                'throughput': records_processed / duration if duration > 0 else 0
            }
            
            self.performance_logs.append(log_entry)
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'log_performance_metrics'})
    
    def log_rejection(self, data: Dict[str, Any], reasons: List[str]) -> None:
        """Log data rejection with detailed reasons."""
        try:
            rejection_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'data_fields': list(data.keys()),
                'rejection_reasons': reasons,
                'data_preview': {k: str(v)[:50] + '...' if len(str(v)) > 50 else str(v) 
                               for k, v in data.items()}
            }
            
            # This could be stored in a separate rejection log if needed
            self.logger.log_module_activity('data_cleaner', 'rejection', 'warning', rejection_entry)
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'log_rejection'})
    
    def generate_quality_report(self, time_period: str = "all_time") -> Dict[str, Any]:
        """
        Generate a comprehensive quality report with detailed analytics.
        
        Args:
            time_period: Time period for the report (e.g., "24h", "7d", "30d", "all_time")
            
        Returns:
            Comprehensive quality report with metrics and insights
        """
        try:
            report_time = datetime.datetime.now()
            
            # Calculate time-based filtering if needed
            cutoff_time = None
            if time_period != "all_time":
                if time_period == "24h":
                    cutoff_time = report_time - timedelta(hours=24)
                elif time_period == "7d":
                    cutoff_time = report_time - timedelta(days=7)
                elif time_period == "30d":
                    cutoff_time = report_time - timedelta(days=30)
            
            # Calculate cleaning effectiveness
            cleaning_effectiveness = 0.0
            if self.cleaning_stats['total_cleanings'] > 0:
                cleaning_effectiveness = (
                    self.cleaning_stats['successful_cleanings'] / 
                    self.cleaning_stats['total_cleanings']
                )
            
            # Calculate validation success rate
            validation_success_rate = 0.0
            if self.validation_stats['total_validations'] > 0:
                validation_success_rate = (
                    self.validation_stats['valid_count'] / 
                    self.validation_stats['total_validations']
                )
            
            # Calculate average confidence scores
            avg_cleaning_confidence = 0.0
            if self.cleaning_stats['confidence_scores']:
                avg_cleaning_confidence = sum(self.cleaning_stats['confidence_scores']) / len(self.cleaning_stats['confidence_scores'])
            
            avg_validation_confidence = 0.0
            if self.validation_stats['confidence_scores']:
                avg_validation_confidence = sum(self.validation_stats['confidence_scores']) / len(self.validation_stats['confidence_scores'])
            
            # Calculate performance metrics
            avg_processing_time = 0.0
            if self.cleaning_stats['processing_times']:
                avg_processing_time = sum(self.cleaning_stats['processing_times']) / len(self.cleaning_stats['processing_times'])
            
            # Identify top issues and patterns
            top_error_patterns = sorted(
                self.validation_stats['error_patterns'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            top_cleaning_rules = sorted(
                self.cleaning_stats['rules_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Generate comprehensive report
            report = {
                'report_metadata': {
                    'generated_at': report_time.isoformat(),
                    'time_period': time_period,
                    'report_version': '2.0',
                    'system_uptime': str(report_time - self.cleaning_stats['start_time'])
                },
                
                'executive_summary': {
                    'total_records_processed': self.performance_stats['total_records_processed'],
                    'cleaning_effectiveness': round(cleaning_effectiveness * 100, 2),
                    'validation_success_rate': round(validation_success_rate * 100, 2),
                    'average_processing_time': round(avg_processing_time * 1000, 2),  # in milliseconds
                    'data_quality_score': round((cleaning_effectiveness + validation_success_rate) * 50, 1)
                },
                
                'cleaning_analytics': {
                    'total_cleanings': self.cleaning_stats['total_cleanings'],
                    'successful_cleanings': self.cleaning_stats['successful_cleanings'],
                    'patterns_applied': self.cleaning_stats['patterns_applied'],
                    'average_confidence': round(avg_cleaning_confidence, 3),
                    'fields_processed': len(self.cleaning_stats['fields_cleaned']),
                    'top_cleaning_rules': [{'rule': rule, 'usage_count': count} for rule, count in top_cleaning_rules],
                    'field_statistics': self.cleaning_stats['fields_cleaned']
                },
                
                'validation_analytics': {
                    'total_validations': self.validation_stats['total_validations'],
                    'valid_count': self.validation_stats['valid_count'],
                    'invalid_count': self.validation_stats['invalid_count'],
                    'success_rate': round(validation_success_rate * 100, 2),
                    'average_confidence': round(avg_validation_confidence, 3),
                    'validation_by_field': self.validation_stats['by_field'],
                    'validation_by_rule': self.validation_stats['by_rule'],
                    'top_error_patterns': [{'error': error, 'count': count} for error, count in top_error_patterns]
                },
                
                'performance_analytics': {
                    'total_operations': self.performance_stats['total_operations'],
                    'total_duration': round(self.performance_stats['total_duration'], 3),
                    'average_throughput': round(self.performance_stats['average_throughput'], 2),
                    'operations_by_type': self.performance_stats['operations_by_type'],
                    'system_efficiency': round(
                        self.performance_stats['total_records_processed'] / 
                        max(self.performance_stats['total_duration'], 0.001), 2
                    )
                },
                
                'quality_insights': {
                    'data_quality_trends': self._calculate_quality_trends(),
                    'improvement_recommendations': self._generate_improvement_recommendations(),
                    'risk_indicators': self._identify_risk_indicators(),
                    'system_health': self._assess_system_health()
                }
            }
            
            # Store report for historical tracking
            self.quality_metrics.append(report)
            
            self.logger.log_module_activity('data_cleaner', 'quality_report', 'success', {
                'message': 'Quality report generated successfully',
                'time_period': time_period,
                'records_analyzed': self.performance_stats['total_records_processed'],
                'data_quality_score': report['executive_summary']['data_quality_score']
            })
            
            return report
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'generate_quality_report'})
            return {
                'error': 'Failed to generate quality report',
                'timestamp': datetime.datetime.now().isoformat(),
                'time_period': time_period
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics across all tracking categories.
        
        Returns:
            Complete statistics dictionary with all metrics
        """
        try:
            # Calculate derived metrics
            cleaning_success_rate = 0.0
            if self.cleaning_stats['total_cleanings'] > 0:
                cleaning_success_rate = (
                    self.cleaning_stats['successful_cleanings'] / 
                    self.cleaning_stats['total_cleanings']
                )
            
            validation_success_rate = 0.0
            if self.validation_stats['total_validations'] > 0:
                validation_success_rate = (
                    self.validation_stats['valid_count'] / 
                    self.validation_stats['total_validations']
                )
            
            average_duration = 0.0
            if self.performance_stats['total_operations'] > 0:
                average_duration = (
                    self.performance_stats['total_duration'] / 
                    self.performance_stats['total_operations']
                )
            
            return {
                'cleaning': {
                    **self.cleaning_stats,
                    'success_rate': cleaning_success_rate
                },
                'validation': {
                    **self.validation_stats,
                    'success_rate': validation_success_rate
                },
                'performance': {
                    **self.performance_stats,
                    'average_duration': average_duration
                },
                'summary': {
                    'total_records': self.performance_stats['total_records_processed'],
                    'overall_success_rate': (cleaning_success_rate + validation_success_rate) / 2,
                    'system_uptime': str(datetime.datetime.now() - self.cleaning_stats['start_time']),
                    'reports_generated': len(self.quality_metrics)
                }
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_statistics'})
            return {}
    
    def save_logs(self) -> None:
        """Save all logs to persistent storage."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Save cleaning logs
            if self.cleaning_logs:
                cleaning_file = self.log_dir / f"cleaning_log_{timestamp}.json"
                with open(cleaning_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cleaning_logs, f, indent=2)
            
            # Save validation logs
            if self.validation_logs:
                validation_file = self.log_dir / f"validation_log_{timestamp}.json"
                with open(validation_file, 'w', encoding='utf-8') as f:
                    json.dump(self.validation_logs, f, indent=2)
            
            # Save performance logs
            if self.performance_logs:
                performance_file = self.log_dir / f"performance_log_{timestamp}.json"
                with open(performance_file, 'w', encoding='utf-8') as f:
                    json.dump(self.performance_logs, f, indent=2)
            
            # Save quality reports
            if self.quality_metrics:
                quality_file = self.log_dir / f"quality_reports_{timestamp}.json"
                with open(quality_file, 'w', encoding='utf-8') as f:
                    json.dump(self.quality_metrics, f, indent=2)
            
            self.logger.log_module_activity('data_cleaner', 'save_logs', 'success', {
                'message': 'Audit logs saved successfully',
                'files_saved': 4,
                'log_dir': str(self.log_dir)
            })
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'save_logs'})
    
    def _calculate_quality_trends(self) -> Dict[str, Any]:
        """Calculate quality trends over time."""
        try:
            # This is a simplified version - in production, you'd analyze time-series data
            recent_validations = self.validation_logs[-100:] if len(self.validation_logs) > 100 else self.validation_logs
            recent_cleanings = self.cleaning_logs[-100:] if len(self.cleaning_logs) > 100 else self.cleaning_logs
            
            if not recent_validations and not recent_cleanings:
                return {'trend': 'insufficient_data'}
            
            # Calculate recent success rates
            recent_validation_success = sum(1 for v in recent_validations if v['is_valid']) / max(len(recent_validations), 1)
            recent_cleaning_confidence = sum(c['confidence_score'] for c in recent_cleanings) / max(len(recent_cleanings), 1)
            
            return {
                'trend': 'stable',  # Could be 'improving', 'declining', 'stable'
                'recent_validation_success': round(recent_validation_success, 3),
                'recent_cleaning_confidence': round(recent_cleaning_confidence, 3),
                'data_points_analyzed': len(recent_validations) + len(recent_cleanings)
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'calculate_quality_trends'})
            return {'trend': 'error', 'message': str(e)}
    
    def _generate_improvement_recommendations(self) -> List[Dict[str, str]]:
        """Generate actionable improvement recommendations."""
        recommendations = []
        
        try:
            # Analyze validation success rate
            if self.validation_stats['total_validations'] > 0:
                success_rate = self.validation_stats['valid_count'] / self.validation_stats['total_validations']
                if success_rate < 0.8:
                    recommendations.append({
                        'category': 'validation',
                        'priority': 'high',
                        'recommendation': 'Validation success rate is below 80%. Review validation rules for accuracy.',
                        'metric': f'Current success rate: {success_rate:.1%}'
                    })
            
            # Analyze cleaning effectiveness
            if self.cleaning_stats['total_cleanings'] > 0:
                effectiveness = self.cleaning_stats['successful_cleanings'] / self.cleaning_stats['total_cleanings']
                if effectiveness < 0.5:
                    recommendations.append({
                        'category': 'cleaning',
                        'priority': 'medium',
                        'recommendation': 'Low cleaning effectiveness detected. Consider updating cleaning rules.',
                        'metric': f'Current effectiveness: {effectiveness:.1%}'
                    })
            
            # Analyze performance
            if self.performance_stats['total_operations'] > 0:
                avg_duration = self.performance_stats['total_duration'] / self.performance_stats['total_operations']
                if avg_duration > 1.0:  # More than 1 second per operation
                    recommendations.append({
                        'category': 'performance',
                        'priority': 'medium',
                        'recommendation': 'Average processing time is high. Consider optimizing cleaning rules.',
                        'metric': f'Average duration: {avg_duration:.2f}s'
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'generate_improvement_recommendations'})
            return [{'category': 'error', 'priority': 'high', 'recommendation': 'Failed to generate recommendations'}]
    
    def _identify_risk_indicators(self) -> List[Dict[str, str]]:
        """Identify potential risk indicators in the data quality."""
        risks = []
        
        try:
            # Check for high error rates
            if self.validation_stats['total_validations'] > 10:
                error_rate = self.validation_stats['invalid_count'] / self.validation_stats['total_validations']
                if error_rate > 0.3:
                    risks.append({
                        'risk_type': 'high_error_rate',
                        'severity': 'high',
                        'description': f'High validation error rate detected: {error_rate:.1%}',
                        'impact': 'Data quality may be compromised'
                    })
            
            # Check for low confidence scores
            if self.cleaning_stats['confidence_scores']:
                avg_confidence = sum(self.cleaning_stats['confidence_scores']) / len(self.cleaning_stats['confidence_scores'])
                if avg_confidence < 0.6:
                    risks.append({
                        'risk_type': 'low_confidence',
                        'severity': 'medium',
                        'description': f'Low average confidence in cleaning: {avg_confidence:.2f}',
                        'impact': 'Cleaning accuracy may be questionable'
                    })
            
            return risks
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'identify_risk_indicators'})
            return [{'risk_type': 'analysis_error', 'severity': 'high', 'description': 'Failed to analyze risks'}]
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health and performance."""
        try:
            health_score = 100  # Start with perfect score
            issues = []
            
            # Check processing volume
            if self.performance_stats['total_records_processed'] == 0:
                health_score -= 20
                issues.append('No records processed yet')
            
            # Check error rates
            if self.validation_stats['total_validations'] > 0:
                error_rate = self.validation_stats['invalid_count'] / self.validation_stats['total_validations']
                if error_rate > 0.2:
                    health_score -= 15
                    issues.append(f'High error rate: {error_rate:.1%}')
            
            # Check performance
            if self.performance_stats['total_operations'] > 0:
                avg_duration = self.performance_stats['total_duration'] / self.performance_stats['total_operations']
                if avg_duration > 0.5:
                    health_score -= 10
                    issues.append(f'Slow processing: {avg_duration:.2f}s avg')
            
            # Determine health status
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 75:
                status = 'good'
            elif health_score >= 60:
                status = 'fair'
            else:
                status = 'poor'
            
            return {
                'health_score': max(health_score, 0),
                'status': status,
                'issues': issues,
                'uptime': str(datetime.datetime.now() - self.cleaning_stats['start_time']),
                'last_assessment': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'assess_system_health'})
            return {
                'health_score': 0,
                'status': 'error',
                'issues': ['Failed to assess system health'],
                'last_assessment': datetime.datetime.now().isoformat()
            }


class DataCleaner:
    """
    Main Data Cleaner class that orchestrates cleaning and validation.
    
    This class provides the primary interface for cleaning and validating
    lead data before it's stored in Airtable or the internal database.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Data Cleaner.
        
        Args:
            config_path: Path to configuration directory
        """
        self.logger = get_logger('data_cleaner')
        
        # Initialize components
        self.config_manager = ConfigurationManager(config_path)
        self.cleaning_engine = CleaningRulesEngine(self.config_manager.cleaning_rules)
        self.validation_engine = ValidationEngine(self.config_manager.validation_rules)
        self.audit_logger = AuditLogger()
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'successful_cleanings': 0,
            'rejections': 0,
            'start_time': datetime.datetime.now()
        }
        
        self.logger.log_module_activity('data_cleaner', 'system', 'success', {
            'message': 'Data Cleaner initialized successfully',
            'config_path': str(self.config_manager.config_path)
        })
    
    def clean_and_validate(self, raw_data: Dict[str, Any], lead_context: Dict[str, Any]) -> CleaningResult:
        """
        Clean and validate raw data.
        
        Args:
            raw_data: Raw data dictionary (e.g., {'Company': 'raw company', 'Website': 'raw url'})
            lead_context: Additional context (e.g., {'id': 'lead123', 'Full Name': 'John Doe'})
            
        Returns:
            CleaningResult with cleaned data or rejection reasons
        """
        start_time = datetime.datetime.now()
        
        try:
            self.stats['total_processed'] += 1
            
            # Initialize result tracking
            cleaning_actions = []
            validation_results = []
            rejection_reasons = []
            cleaned_data = {}
            
            # Clean each field
            for field_name, raw_value in raw_data.items():
                if not raw_value:
                    continue
                
                original_value = str(raw_value)
                cleaned_value = original_value
                
                # Apply field-specific cleaning
                if field_name.lower() in ['company', 'company_name']:
                    cleaned_value = self.cleaning_engine.clean_company_name(original_value)
                    
                    if cleaned_value != original_value:
                        cleaning_actions.append(CleaningAction(
                            rule_name='company_name_cleaning',
                            field_name=field_name,
                            original_value=original_value,
                            cleaned_value=cleaned_value,
                            confidence_score=0.9,
                            applied_at=datetime.datetime.now().isoformat()
                        ))
                        
                        # Log with new comprehensive AuditLogger interface
                        field_cleaning_result = FieldCleaningResult(
                            field_name=field_name,
                            original_value=original_value,
                            cleaned_value=cleaned_value,
                            patterns_applied=['company_name_rules'],
                            confidence_score=0.9,
                            processing_time=0.01
                        )
                        self.audit_logger.log_cleaning_action(field_cleaning_result)
                
                elif field_name.lower() in ['website', 'website_url', 'company_website']:
                    cleaned_value = self.cleaning_engine.clean_website_url(original_value)
                    
                    if cleaned_value != original_value:
                        cleaning_actions.append(CleaningAction(
                            rule_name='website_url_cleaning',
                            field_name=field_name,
                            original_value=original_value,
                            cleaned_value=cleaned_value,
                            confidence_score=0.9,
                            applied_at=datetime.datetime.now().isoformat()
                        ))
                        
                        # Log with new comprehensive AuditLogger interface
                        field_cleaning_result = FieldCleaningResult(
                            field_name=field_name,
                            original_value=original_value,
                            cleaned_value=cleaned_value,
                            patterns_applied=['website_url_rules'],
                            confidence_score=0.9,
                            processing_time=0.01
                        )
                        self.audit_logger.log_cleaning_action(field_cleaning_result)
                
                # Store cleaned value if it's not empty
                if cleaned_value and cleaned_value.strip():
                    cleaned_data[field_name] = cleaned_value
            
            # Validate cleaned data
            for field_name, cleaned_value in cleaned_data.items():
                validation_result = None
                
                if field_name.lower() in ['company', 'company_name']:
                    validation_result = self.validation_engine.validate_company_name(cleaned_value, lead_context)
                elif field_name.lower() in ['website', 'website_url', 'company_website']:
                    validation_result = self.validation_engine.validate_website_url(cleaned_value, lead_context)
                
                if validation_result:
                    validation_results.append(validation_result)
                    self.audit_logger.log_validation_decision(validation_result)
                    
                    if not validation_result.is_valid:
                        rejection_reasons.append(f"{field_name}: {validation_result.error_message}")
            
            # Create normalized field mapping for validation
            normalized_data = {}
            for field_name, value in cleaned_data.items():
                if field_name.lower() in ['company', 'company_name']:
                    normalized_data['company'] = value
                elif field_name.lower() in ['website', 'website_url', 'company_website']:
                    normalized_data['website'] = value
            
            # Overall data quality validation
            completeness_result = self.validation_engine.validate_data_completeness(normalized_data)
            validation_results.append(completeness_result)
            
            if not completeness_result.is_valid:
                rejection_reasons.append(f"Data completeness: {completeness_result.error_message}")
            
            professional_result = self.validation_engine.validate_professional_standards(normalized_data)
            validation_results.append(professional_result)
            
            if not professional_result.is_valid:
                rejection_reasons.append(f"Professional standards: {professional_result.error_message}")
            
            # Calculate overall confidence score
            if validation_results:
                confidence_score = sum(r.confidence_score for r in validation_results) / len(validation_results)
            else:
                confidence_score = 0.0
            
            # Determine success
            success = len(rejection_reasons) == 0 and confidence_score >= 0.7
            
            if success:
                self.stats['successful_cleanings'] += 1
            else:
                self.stats['rejections'] += 1
                self.audit_logger.log_rejection(raw_data, rejection_reasons)
            
            # Calculate processing time
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            
            result = CleaningResult(
                success=success,
                cleaned_data=cleaned_data if success else {},
                original_data=raw_data,
                cleaning_actions=cleaning_actions,
                validation_results=validation_results,
                rejection_reasons=rejection_reasons,
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
            self.logger.log_module_activity('data_cleaner', lead_context.get('id', 'unknown'), 
                                           'success' if success else 'warning', {
                'message': 'Data cleaning completed',
                'success': success,
                'confidence_score': confidence_score,
                'processing_time': processing_time,
                'cleaning_actions': len(cleaning_actions),
                'validation_results': len(validation_results),
                'rejection_reasons': len(rejection_reasons)
            })
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'clean_and_validate',
                'raw_data': raw_data,
                'lead_context': lead_context
            })
            
            # Return failure result
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            return CleaningResult(
                success=False,
                cleaned_data={},
                original_data=raw_data,
                cleaning_actions=[],
                validation_results=[],
                rejection_reasons=[f"System error: {str(e)}"],
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """Get cleaning statistics."""
        runtime = (datetime.datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'total_processed': self.stats['total_processed'],
            'successful_cleanings': self.stats['successful_cleanings'],
            'rejections': self.stats['rejections'],
            'success_rate': (self.stats['successful_cleanings'] / max(self.stats['total_processed'], 1)) * 100,
            'rejection_rate': (self.stats['rejections'] / max(self.stats['total_processed'], 1)) * 100,
            'runtime_seconds': runtime,
            'processing_rate': self.stats['total_processed'] / max(runtime, 1)
        }
    
    def update_rules(self, new_rules: Dict[str, Any]) -> bool:
        """Update cleaning and validation rules."""
        return self.config_manager.update_rules(new_rules)