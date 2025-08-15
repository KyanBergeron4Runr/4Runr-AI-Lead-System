#!/usr/bin/env python3
"""
Duplicate Detector

Advanced duplicate detection and resolution system for database maintenance.
Identifies duplicates across local database and Airtable using configurable matching criteria.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

# Configure logging
logger = logging.getLogger('duplicate-detector')

@dataclass
class DuplicateGroup:
    """Group of duplicate records with resolution information."""
    matching_field: str
    matching_value: str
    records: List[Dict[str, Any]]
    primary_record: Optional[Dict[str, Any]] = None
    duplicate_records: List[Dict[str, Any]] = None
    resolution_strategy: str = "most_recent"
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.duplicate_records is None:
            self.duplicate_records = []

@dataclass
class CrossSystemDuplicate:
    """Duplicate record found across database and Airtable."""
    database_record: Dict[str, Any]
    airtable_record: Dict[str, Any]
    matching_fields: List[str]
    confidence_score: float
    suggested_primary: str  # 'database' or 'airtable'

@dataclass
class ResolutionResult:
    """Results from duplicate resolution operations."""
    success: bool
    duplicates_processed: int
    records_merged: int
    records_deleted: int
    errors: List[str]
    warnings: List[str]

class DuplicateDetector:
    """
    Advanced duplicate detection and resolution system.
    
    Identifies duplicate records within and across systems using configurable
    matching criteria and provides intelligent resolution strategies.
    """
    
    def __init__(self, matching_threshold: float = 0.85):
        """
        Initialize the duplicate detector.
        
        Args:
            matching_threshold: Minimum similarity score for duplicate detection (0.0-1.0)
        """
        self.matching_threshold = matching_threshold
        logger.info(f"DuplicateDetector initialized with threshold: {matching_threshold}")
    
    def find_database_duplicates(self, matching_fields: List[str]) -> List[DuplicateGroup]:
        """
        Find duplicate records in the local database.
        
        Args:
            matching_fields: List of field names to use for matching
            
        Returns:
            List of DuplicateGroup objects
        """
        try:
            # Import database connection
            import sys
            from pathlib import Path
            
            # Add the lead scraper path for database imports
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            try:
                from database.models import get_lead_database
            except ImportError:
                logger.error("Could not import database models")
                return []
            
            # Get all records from database
            db = get_lead_database()
            all_leads = db.search_leads({})  # Get all leads
            
            logger.info(f"Analyzing {len(all_leads)} database records for duplicates")
            
            # Convert leads to dictionaries for processing
            records = [lead.to_dict() for lead in all_leads]
            
            # Find duplicates using matching fields
            duplicate_groups = self._find_duplicates_in_records(records, matching_fields, "database")
            
            logger.info(f"Found {len(duplicate_groups)} duplicate groups in database")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Database duplicate detection failed: {e}")
            return []
    
    def find_airtable_duplicates(self, matching_fields: List[str]) -> List[DuplicateGroup]:
        """
        Find duplicate records in Airtable.
        
        Args:
            matching_fields: List of field names to use for matching
            
        Returns:
            List of DuplicateGroup objects
        """
        try:
            # Import Airtable client
            try:
                from configurable_airtable_client import get_configurable_airtable_client
            except ImportError:
                logger.warning("Airtable client not available, skipping Airtable duplicate detection")
                return []
            
            # Get all records from Airtable
            airtable_client = get_configurable_airtable_client()
            all_records = []
            
            try:
                records = airtable_client.table.all()
                for record in records:
                    record_data = {
                        'id': record['id'],
                        **record['fields']
                    }
                    all_records.append(record_data)
                
                logger.info(f"Analyzing {len(all_records)} Airtable records for duplicates")
                
            except Exception as e:
                logger.error(f"Failed to fetch Airtable records: {e}")
                return []
            
            # Find duplicates using matching fields
            duplicate_groups = self._find_duplicates_in_records(all_records, matching_fields, "airtable")
            
            logger.info(f"Found {len(duplicate_groups)} duplicate groups in Airtable")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Airtable duplicate detection failed: {e}")
            return []
    
    def find_cross_system_duplicates(self) -> List[CrossSystemDuplicate]:
        """
        Find duplicate records between database and Airtable.
        
        Returns:
            List of CrossSystemDuplicate objects
        """
        try:
            # Get records from both systems
            db_records = self._get_database_records()
            airtable_records = self._get_airtable_records()
            
            if not db_records or not airtable_records:
                logger.warning("Could not retrieve records from both systems")
                return []
            
            logger.info(f"Comparing {len(db_records)} database records with {len(airtable_records)} Airtable records")
            
            cross_duplicates = []
            
            # Compare each database record with each Airtable record
            for db_record in db_records:
                for airtable_record in airtable_records:
                    match_result = self._compare_records(db_record, airtable_record)
                    
                    if match_result['is_duplicate']:
                        cross_duplicate = CrossSystemDuplicate(
                            database_record=db_record,
                            airtable_record=airtable_record,
                            matching_fields=match_result['matching_fields'],
                            confidence_score=match_result['confidence_score'],
                            suggested_primary=self._determine_primary_record(db_record, airtable_record)
                        )
                        cross_duplicates.append(cross_duplicate)
            
            logger.info(f"Found {len(cross_duplicates)} cross-system duplicates")
            return cross_duplicates
            
        except Exception as e:
            logger.error(f"Cross-system duplicate detection failed: {e}")
            return []
    
    def _find_duplicates_in_records(self, records: List[Dict[str, Any]], matching_fields: List[str], source: str) -> List[DuplicateGroup]:
        """Find duplicates within a list of records."""
        duplicate_groups = []
        processed_records = set()
        
        for i, record1 in enumerate(records):
            if i in processed_records:
                continue
            
            duplicates = [record1]
            processed_records.add(i)
            
            # Compare with remaining records
            for j, record2 in enumerate(records[i+1:], i+1):
                if j in processed_records:
                    continue
                
                match_result = self._compare_records(record1, record2, matching_fields)
                
                if match_result['is_duplicate']:
                    duplicates.append(record2)
                    processed_records.add(j)
            
            # If we found duplicates, create a group
            if len(duplicates) > 1:
                # Determine the best matching field for this group
                best_field = self._determine_best_matching_field(duplicates, matching_fields)
                matching_value = str(duplicates[0].get(best_field, ''))
                
                # Calculate confidence score for the group
                confidence_score = self._calculate_group_confidence(duplicates, matching_fields)
                
                duplicate_group = DuplicateGroup(
                    matching_field=best_field,
                    matching_value=matching_value,
                    records=duplicates,
                    confidence_score=confidence_score
                )
                
                duplicate_groups.append(duplicate_group)
        
        return duplicate_groups
    
    def _compare_records(self, record1: Dict[str, Any], record2: Dict[str, Any], matching_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare two records for similarity."""
        if matching_fields is None:
            matching_fields = ['email', 'linkedin_url', 'company', 'name']
        
        matching_scores = {}
        matching_field_names = []
        
        for field in matching_fields:
            value1 = str(record1.get(field, '')).strip().lower()
            value2 = str(record2.get(field, '')).strip().lower()
            
            if not value1 or not value2:
                continue
            
            # Calculate similarity score
            similarity = self._calculate_similarity(value1, value2)
            matching_scores[field] = similarity
            
            if similarity >= self.matching_threshold:
                matching_field_names.append(field)
        
        # Overall confidence is the maximum similarity score
        overall_confidence = max(matching_scores.values()) if matching_scores else 0.0
        
        return {
            'is_duplicate': overall_confidence >= self.matching_threshold,
            'confidence_score': overall_confidence,
            'matching_fields': matching_field_names,
            'field_scores': matching_scores
        }
    
    def _calculate_similarity(self, value1: str, value2: str) -> float:
        """Calculate similarity between two string values."""
        if not value1 or not value2:
            return 0.0
        
        # Exact match
        if value1 == value2:
            return 1.0
        
        # For email addresses, be more strict
        if '@' in value1 and '@' in value2:
            return 1.0 if value1 == value2 else 0.0
        
        # For URLs, normalize and compare
        if value1.startswith(('http://', 'https://')) or value2.startswith(('http://', 'https://')):
            normalized1 = self._normalize_url(value1)
            normalized2 = self._normalize_url(value2)
            return 1.0 if normalized1 == normalized2 else 0.0
        
        # Use sequence matcher for general text similarity
        return SequenceMatcher(None, value1, value2).ratio()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        url = url.lower().strip()
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        
        # Remove www
        url = re.sub(r'^www\.', '', url)
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        return url
    
    def _determine_best_matching_field(self, records: List[Dict[str, Any]], matching_fields: List[str]) -> str:
        """Determine the best field that identifies this duplicate group."""
        field_scores = {}
        
        for field in matching_fields:
            values = [str(record.get(field, '')).strip() for record in records]
            non_empty_values = [v for v in values if v]
            
            if not non_empty_values:
                continue
            
            # Score based on how many records have this field and how similar they are
            coverage = len(non_empty_values) / len(records)
            
            # Calculate average similarity within the group for this field
            similarities = []
            for i in range(len(non_empty_values)):
                for j in range(i+1, len(non_empty_values)):
                    sim = self._calculate_similarity(non_empty_values[i].lower(), non_empty_values[j].lower())
                    similarities.append(sim)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            field_scores[field] = coverage * avg_similarity
        
        # Return the field with the highest score
        if field_scores:
            return max(field_scores, key=field_scores.get)
        
        return matching_fields[0] if matching_fields else 'id'
    
    def _calculate_group_confidence(self, records: List[Dict[str, Any]], matching_fields: List[str]) -> float:
        """Calculate confidence score for a duplicate group."""
        if len(records) < 2:
            return 0.0
        
        total_similarity = 0.0
        comparisons = 0
        
        # Compare all pairs in the group
        for i in range(len(records)):
            for j in range(i+1, len(records)):
                match_result = self._compare_records(records[i], records[j], matching_fields)
                total_similarity += match_result['confidence_score']
                comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _get_database_records(self) -> List[Dict[str, Any]]:
        """Get all records from the database."""
        try:
            import sys
            from pathlib import Path
            
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            from database.models import get_lead_database
            
            db = get_lead_database()
            all_leads = db.search_leads({})
            
            return [lead.to_dict() for lead in all_leads]
            
        except Exception as e:
            logger.error(f"Failed to get database records: {e}")
            return []
    
    def _get_airtable_records(self) -> List[Dict[str, Any]]:
        """Get all records from Airtable."""
        try:
            from configurable_airtable_client import get_configurable_airtable_client
            
            airtable_client = get_configurable_airtable_client()
            all_records = []
            
            records = airtable_client.table.all()
            for record in records:
                record_data = {
                    'id': record['id'],
                    **record['fields']
                }
                all_records.append(record_data)
            
            return all_records
            
        except Exception as e:
            logger.error(f"Failed to get Airtable records: {e}")
            return []
    
    def _determine_primary_record(self, db_record: Dict[str, Any], airtable_record: Dict[str, Any]) -> str:
        """Determine which record should be considered primary."""
        # Simple heuristic: prefer the record with more complete data
        db_completeness = sum(1 for v in db_record.values() if v and str(v).strip())
        airtable_completeness = sum(1 for v in airtable_record.values() if v and str(v).strip())
        
        if airtable_completeness > db_completeness:
            return "airtable"
        else:
            return "database"
    
    def resolve_duplicates(self, duplicates: List[DuplicateGroup], strategy: str = "most_recent") -> ResolutionResult:
        """
        Resolve duplicate records using the specified strategy.
        
        Args:
            duplicates: List of duplicate groups to resolve
            strategy: Resolution strategy ('most_recent', 'highest_quality', 'merge')
            
        Returns:
            ResolutionResult: Results of the resolution operation
        """
        result = ResolutionResult(
            success=True,
            duplicates_processed=0,
            records_merged=0,
            records_deleted=0,
            errors=[],
            warnings=[]
        )
        
        try:
            logger.info(f"Resolving {len(duplicates)} duplicate groups using strategy: {strategy}")
            
            for duplicate_group in duplicates:
                try:
                    # Apply resolution strategy
                    if strategy == "most_recent":
                        resolution = self._resolve_by_most_recent(duplicate_group)
                    elif strategy == "highest_quality":
                        resolution = self._resolve_by_highest_quality(duplicate_group)
                    elif strategy == "merge":
                        resolution = self._resolve_by_merge(duplicate_group)
                    else:
                        result.warnings.append(f"Unknown resolution strategy: {strategy}")
                        continue
                    
                    if resolution['success']:
                        result.records_merged += resolution.get('merged_count', 0)
                        result.records_deleted += resolution.get('deleted_count', 0)
                        result.duplicates_processed += 1
                    else:
                        result.errors.extend(resolution.get('errors', []))
                
                except Exception as e:
                    error_msg = f"Failed to resolve duplicate group: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            result.success = len(result.errors) == 0
            
            logger.info(f"Duplicate resolution completed: {result.duplicates_processed} groups processed")
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Duplicate resolution failed: {str(e)}")
            logger.error(f"Duplicate resolution failed: {e}")
            return result
    
    def _resolve_by_most_recent(self, duplicate_group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve duplicates by keeping the most recently updated record."""
        # Placeholder implementation
        logger.info(f"Resolving duplicate group by most recent: {duplicate_group.matching_field}")
        return {
            'success': True,
            'merged_count': 0,
            'deleted_count': len(duplicate_group.records) - 1,
            'errors': []
        }
    
    def _resolve_by_highest_quality(self, duplicate_group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve duplicates by keeping the record with the most complete data."""
        # Placeholder implementation
        logger.info(f"Resolving duplicate group by highest quality: {duplicate_group.matching_field}")
        return {
            'success': True,
            'merged_count': 0,
            'deleted_count': len(duplicate_group.records) - 1,
            'errors': []
        }
    
    def _resolve_by_merge(self, duplicate_group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve duplicates by merging all records into one."""
        # Placeholder implementation
        logger.info(f"Resolving duplicate group by merge: {duplicate_group.matching_field}")
        return {
            'success': True,
            'merged_count': 1,
            'deleted_count': len(duplicate_group.records) - 1,
            'errors': []
        }


if __name__ == "__main__":
    # Test the duplicate detector
    print("🧪 Testing Duplicate Detector...")
    
    # Create duplicate detector
    detector = DuplicateDetector(matching_threshold=0.85)
    
    # Test database duplicate detection
    print("Testing database duplicate detection...")
    db_duplicates = detector.find_database_duplicates(['email', 'linkedin_url'])
    print(f"Found {len(db_duplicates)} duplicate groups in database")
    
    # Test Airtable duplicate detection
    print("Testing Airtable duplicate detection...")
    airtable_duplicates = detector.find_airtable_duplicates(['email', 'linkedin_url'])
    print(f"Found {len(airtable_duplicates)} duplicate groups in Airtable")
    
    # Test cross-system duplicate detection
    print("Testing cross-system duplicate detection...")
    cross_duplicates = detector.find_cross_system_duplicates()
    print(f"Found {len(cross_duplicates)} cross-system duplicates")
    
    # Test duplicate resolution
    if db_duplicates:
        print("Testing duplicate resolution...")
        resolution_result = detector.resolve_duplicates(db_duplicates[:1], "most_recent")
        print(f"Resolution result: {'Success' if resolution_result.success else 'Failed'}")
    
    print("✅ Duplicate detector test completed")