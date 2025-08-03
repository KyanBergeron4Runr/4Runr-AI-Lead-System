#!/usr/bin/env python3
"""
Duplicate Detection Engine

Advanced duplicate detection for lead data with fuzzy matching,
confidence scoring, and intelligent data merging.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DuplicateMatch:
    """
    Represents a potential duplicate match with confidence score
    """
    lead_id: str
    confidence: float
    match_type: str  # 'linkedin_url', 'email', 'name_company', 'fuzzy_name'
    match_details: Dict[str, Any]
    existing_lead: Dict[str, Any]

class DuplicateDetector:
    """
    Advanced duplicate detection engine with fuzzy matching
    """
    
    def __init__(self, db_connection):
        """
        Initialize duplicate detector
        
        Args:
            db_connection: Database connection instance
        """
        self.db_conn = db_connection
        self.confidence_thresholds = {
            'linkedin_url': 1.0,      # Exact match required
            'email': 1.0,             # Exact match required
            'name_company': 0.95,     # Very high confidence for exact name+company
            'fuzzy_name': 0.85,       # Configurable fuzzy match threshold
            'phone': 1.0,             # Exact match if available
            'domain_name': 0.65       # Lower threshold for domain + name similarity
        }
        
    def find_duplicates(self, lead_data: Dict[str, Any]) -> List[DuplicateMatch]:
        """
        Find all potential duplicates for a lead with confidence scores
        
        Args:
            lead_data: Lead data to check for duplicates
            
        Returns:
            list: List of DuplicateMatch objects sorted by confidence
        """
        matches = []
        
        try:
            # 1. LinkedIn URL exact match (highest priority)
            linkedin_match = self._check_linkedin_url_match(lead_data)
            if linkedin_match:
                matches.append(linkedin_match)
            
            # 2. Email exact match (high priority)
            email_match = self._check_email_match(lead_data)
            if email_match:
                matches.append(email_match)
            
            # 3. Phone number match (if available)
            phone_match = self._check_phone_match(lead_data)
            if phone_match:
                matches.append(phone_match)
            
            # 4. Exact name + company match
            name_company_match = self._check_name_company_match(lead_data)
            if name_company_match:
                matches.append(name_company_match)
            
            # 5. Domain + name similarity (for business emails)
            domain_match = self._check_domain_name_match(lead_data)
            if domain_match:
                matches.append(domain_match)
            
            # 6. Fuzzy name matching (lowest priority, only if no exact matches)
            if not matches:
                fuzzy_matches = self._check_fuzzy_name_matches(lead_data)
                matches.extend(fuzzy_matches)
            
            # Remove duplicate matches (same lead_id with different match types)
            seen_lead_ids = set()
            unique_matches = []
            for match in matches:
                if match.lead_id not in seen_lead_ids:
                    unique_matches.append(match)
                    seen_lead_ids.add(match.lead_id)
            matches = unique_matches
            
            # Sort by confidence score (highest first)
            matches.sort(key=lambda x: x.confidence, reverse=True)
            
            # Filter by minimum confidence thresholds
            filtered_matches = []
            for match in matches:
                threshold = self.confidence_thresholds.get(match.match_type, 0.8)
                if match.confidence >= threshold:
                    filtered_matches.append(match)
            
            return filtered_matches
            
        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            return []
    
    def get_best_duplicate(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """
        Get the best duplicate match for a lead
        
        Args:
            lead_data: Lead data to check
            
        Returns:
            DuplicateMatch: Best match or None if no duplicates found
        """
        matches = self.find_duplicates(lead_data)
        return matches[0] if matches else None
    
    def merge_lead_data(self, existing_lead: Dict[str, Any], new_lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge lead data, preserving the best information
        
        Args:
            existing_lead: Current lead data in database
            new_lead_data: New lead data to merge
            
        Returns:
            dict: Merged lead data
        """
        merged = existing_lead.copy()
        
        # Fields that should be updated if new data is more complete
        updateable_fields = [
            'full_name', 'email', 'company', 'title', 'location', 
            'industry', 'company_size', 'linkedin_url'
        ]
        
        # Fields that should be set to True if either is True
        boolean_or_fields = ['verified', 'enriched']
        
        # Fields that should be set to False if either is False  
        boolean_and_fields = ['needs_enrichment']
        
        for field in updateable_fields:
            existing_value = existing_lead.get(field)
            new_value = new_lead_data.get(field)
            
            # Use new value if it's more complete or existing is empty
            if self._is_better_value(existing_value, new_value):
                merged[field] = new_value
                logger.debug(f"Updated {field}: '{existing_value}' -> '{new_value}'")
        
        # Handle boolean OR fields (verified, enriched)
        for field in boolean_or_fields:
            existing_value = existing_lead.get(field, False)
            new_value = new_lead_data.get(field, False)
            merged[field] = existing_value or new_value
        
        # Handle boolean AND fields (needs_enrichment)
        for field in boolean_and_fields:
            existing_value = existing_lead.get(field, True)
            new_value = new_lead_data.get(field, True)
            merged[field] = existing_value and new_value
        
        # Handle timestamps - keep earliest created_at, update updated_at
        if new_lead_data.get('created_at') and existing_lead.get('created_at'):
            # Keep the earlier creation date
            existing_created = self._parse_datetime(existing_lead['created_at'])
            new_created = self._parse_datetime(new_lead_data['created_at'])
            
            if new_created and existing_created and new_created < existing_created:
                merged['created_at'] = new_lead_data['created_at']
        
        # Always update the updated_at timestamp
        merged['updated_at'] = datetime.now().isoformat()
        
        # Handle enrichment timestamps
        if new_lead_data.get('enriched_at') and new_lead_data.get('enriched'):
            merged['enriched_at'] = new_lead_data['enriched_at']
        
        if new_lead_data.get('scraped_at'):
            # Keep the most recent scrape time
            existing_scraped = self._parse_datetime(existing_lead.get('scraped_at'))
            new_scraped = self._parse_datetime(new_lead_data['scraped_at'])
            
            if not existing_scraped or (new_scraped and new_scraped > existing_scraped):
                merged['scraped_at'] = new_lead_data['scraped_at']
        
        # Merge raw_data intelligently
        merged['raw_data'] = self._merge_raw_data(
            existing_lead.get('raw_data', {}),
            new_lead_data.get('raw_data', {})
        )
        
        # Update source information
        existing_source = existing_lead.get('source', '')
        new_source = new_lead_data.get('source', '')
        
        if new_source and new_source != existing_source:
            if existing_source:
                merged['source'] = f"{existing_source}, {new_source}"
            else:
                merged['source'] = new_source
        
        return merged
    
    def _check_linkedin_url_match(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """Check for LinkedIn URL exact match"""
        linkedin_url = lead_data.get('linkedin_url')
        if not linkedin_url or not linkedin_url.strip():
            return None
        
        # Normalize LinkedIn URL
        normalized_url = self._normalize_linkedin_url(linkedin_url.strip())
        
        try:
            cursor = self.db_conn.execute_query(
                "SELECT * FROM leads WHERE linkedin_url = ? AND linkedin_url IS NOT NULL",
                (normalized_url,)
            )
            row = cursor.fetchone()
            
            if row:
                existing_lead = dict(row)
                return DuplicateMatch(
                    lead_id=existing_lead['id'],
                    confidence=1.0,
                    match_type='linkedin_url',
                    match_details={'linkedin_url': normalized_url},
                    existing_lead=existing_lead
                )
        except Exception as e:
            logger.error(f"Error checking LinkedIn URL match: {e}")
        
        return None
    
    def _check_email_match(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """Check for email exact match"""
        email = lead_data.get('email')
        if not email or not email.strip():
            return None
        
        normalized_email = email.strip().lower()
        
        try:
            cursor = self.db_conn.execute_query(
                "SELECT * FROM leads WHERE LOWER(email) = ? AND email IS NOT NULL",
                (normalized_email,)
            )
            row = cursor.fetchone()
            
            if row:
                existing_lead = dict(row)
                return DuplicateMatch(
                    lead_id=existing_lead['id'],
                    confidence=1.0,
                    match_type='email',
                    match_details={'email': normalized_email},
                    existing_lead=existing_lead
                )
        except Exception as e:
            logger.error(f"Error checking email match: {e}")
        
        return None
    
    def _check_phone_match(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """Check for phone number match"""
        phone = lead_data.get('phone') or lead_data.get('raw_data', {}).get('phone')
        if not phone:
            return None
        
        normalized_phone = self._normalize_phone(phone)
        if not normalized_phone:
            return None
        
        try:
            # Check in both phone field and raw_data
            cursor = self.db_conn.execute_query("""
                SELECT * FROM leads 
                WHERE (phone = ? OR raw_data LIKE ?) 
                AND (phone IS NOT NULL OR raw_data IS NOT NULL)
            """, (normalized_phone, f'%{normalized_phone}%'))
            
            row = cursor.fetchone()
            
            if row:
                existing_lead = dict(row)
                return DuplicateMatch(
                    lead_id=existing_lead['id'],
                    confidence=1.0,
                    match_type='phone',
                    match_details={'phone': normalized_phone},
                    existing_lead=existing_lead
                )
        except Exception as e:
            logger.error(f"Error checking phone match: {e}")
        
        return None
    
    def _check_name_company_match(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """Check for exact name + company match"""
        full_name = lead_data.get('full_name', '').strip()
        company = lead_data.get('company', '').strip()
        
        if not full_name or not company:
            return None
        
        try:
            cursor = self.db_conn.execute_query(
                "SELECT * FROM leads WHERE LOWER(full_name) = ? AND LOWER(company) = ?",
                (full_name.lower(), company.lower())
            )
            row = cursor.fetchone()
            
            if row:
                existing_lead = dict(row)
                return DuplicateMatch(
                    lead_id=existing_lead['id'],
                    confidence=0.95,
                    match_type='name_company',
                    match_details={'full_name': full_name, 'company': company},
                    existing_lead=existing_lead
                )
        except Exception as e:
            logger.error(f"Error checking name+company match: {e}")
        
        return None
    
    def _check_domain_name_match(self, lead_data: Dict[str, Any]) -> Optional[DuplicateMatch]:
        """Check for same domain + similar name match"""
        email = lead_data.get('email')
        full_name = lead_data.get('full_name')
        
        if not email or not full_name:
            return None
        
        domain = self._extract_domain(email)
        if not domain:
            return None
        
        try:
            # Find leads with same domain
            cursor = self.db_conn.execute_query(
                "SELECT * FROM leads WHERE email LIKE ? AND email IS NOT NULL",
                (f'%@{domain}',)
            )
            
            rows = cursor.fetchall()
            
            for row in rows:
                existing_lead = dict(row)
                existing_name = existing_lead.get('full_name', '')
                
                # Calculate name similarity
                name_similarity = self._calculate_name_similarity(full_name, existing_name)
                
                if name_similarity >= 0.70:  # Threshold for domain matching
                    confidence = 0.9 * name_similarity  # Scale by similarity
                    
                    return DuplicateMatch(
                        lead_id=existing_lead['id'],
                        confidence=confidence,
                        match_type='domain_name',
                        match_details={
                            'domain': domain,
                            'name_similarity': name_similarity,
                            'existing_name': existing_name,
                            'new_name': full_name
                        },
                        existing_lead=existing_lead
                    )
        except Exception as e:
            logger.error(f"Error checking domain+name match: {e}")
        
        return None
    
    def _check_fuzzy_name_matches(self, lead_data: Dict[str, Any]) -> List[DuplicateMatch]:
        """Check for fuzzy name matches"""
        full_name = lead_data.get('full_name', '').strip()
        company = lead_data.get('company', '').strip()
        
        if not full_name:
            return []
        
        matches = []
        
        try:
            # Get all leads for fuzzy comparison
            # Limit to reasonable number to avoid performance issues
            query = "SELECT * FROM leads ORDER BY created_at DESC LIMIT 1000"
            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()
            
            for row in rows:
                existing_lead = dict(row)
                existing_name = existing_lead.get('full_name', '')
                existing_company = existing_lead.get('company', '')
                
                # Calculate name similarity
                name_similarity = self._calculate_name_similarity(full_name, existing_name)
                
                # Boost confidence if companies match
                company_boost = 0.0
                if company and existing_company:
                    company_similarity = self._calculate_text_similarity(company, existing_company)
                    if company_similarity > 0.8:
                        company_boost = 0.1
                
                total_confidence = name_similarity + company_boost
                
                if total_confidence >= 0.85:  # Minimum fuzzy match threshold
                    matches.append(DuplicateMatch(
                        lead_id=existing_lead['id'],
                        confidence=min(total_confidence, 0.95),  # Cap at 0.95 for fuzzy matches
                        match_type='fuzzy_name',
                        match_details={
                            'name_similarity': name_similarity,
                            'company_similarity': company_similarity if company and existing_company else 0,
                            'existing_name': existing_name,
                            'new_name': full_name,
                            'company_boost': company_boost
                        },
                        existing_lead=existing_lead
                    ))
        except Exception as e:
            logger.error(f"Error in fuzzy name matching: {e}")
        
        return matches
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL for consistent comparison"""
        if not url:
            return url
        
        # Remove trailing slashes and normalize case
        url = url.strip().rstrip('/')
        
        # Handle different LinkedIn URL formats
        if 'linkedin.com/in/' in url.lower():
            # Extract the profile identifier
            match = re.search(r'linkedin\.com/in/([^/?]+)', url.lower())
            if match:
                profile_id = match.group(1)
                return f"https://linkedin.com/in/{profile_id}"
        
        return url
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number for comparison"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Must have at least 10 digits
        if len(digits) < 10:
            return None
        
        # Handle North American numbers
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        
        return f"+{digits}"
    
    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        
        return email.split('@')[-1].lower()
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using multiple methods"""
        if not name1 or not name2:
            return 0.0
        
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
        
        # Method 1: Sequence matcher for overall similarity
        seq_similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Method 2: Check for name component matches (first/last name)
        name1_parts = set(name1.split())
        name2_parts = set(name2.split())
        
        if name1_parts and name2_parts:
            common_parts = name1_parts.intersection(name2_parts)
            component_similarity = len(common_parts) / max(len(name1_parts), len(name2_parts))
        else:
            component_similarity = 0.0
        
        # Method 3: Check for initials match
        initials_similarity = self._calculate_initials_similarity(name1, name2)
        
        # Combine methods with weights
        combined_similarity = (
            seq_similarity * 0.5 +
            component_similarity * 0.3 +
            initials_similarity * 0.2
        )
        
        return min(combined_similarity, 1.0)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _calculate_initials_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity based on initials"""
        def get_initials(name):
            return ''.join([part[0] for part in name.split() if part])
        
        initials1 = get_initials(name1)
        initials2 = get_initials(name2)
        
        if not initials1 or not initials2:
            return 0.0
        
        if initials1 == initials2:
            return 1.0
        
        return SequenceMatcher(None, initials1, initials2).ratio()
    
    def _is_better_value(self, existing_value: Any, new_value: Any) -> bool:
        """Determine if new value is better than existing value"""
        # New value is better if existing is None/empty and new has content
        if not existing_value and new_value:
            return True
        
        # New value is better if it's longer and contains existing value
        if isinstance(existing_value, str) and isinstance(new_value, str):
            if len(new_value) > len(existing_value) and existing_value.lower() in new_value.lower():
                return True
        
        return False
    
    def _merge_raw_data(self, existing_raw: Dict[str, Any], new_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently merge raw_data dictionaries"""
        if not existing_raw:
            return new_raw or {}
        
        if not new_raw:
            return existing_raw
        
        merged = existing_raw.copy()
        
        for key, value in new_raw.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self._merge_raw_data(merged[key], value)
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Merge lists, avoiding duplicates
                merged[key] = list(set(merged[key] + value))
            else:
                # Use new value if it's more complete or has higher numeric value
                if self._is_better_value(merged[key], value):
                    merged[key] = value
                elif isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                    # For numeric values, use the higher one (e.g., confidence scores)
                    merged[key] = max(merged[key], value)
        
        return merged
    
    def _parse_datetime(self, dt_string: str) -> Optional[datetime]:
        """Parse datetime string safely"""
        if not dt_string:
            return None
        
        try:
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None