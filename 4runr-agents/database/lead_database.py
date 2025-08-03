#!/usr/bin/env python3
"""
Lead Database API

Provides a clean, high-level API for lead database operations.
Handles CRUD operations, duplicate detection, and data validation.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict

from .connection import get_database_connection
from .duplicate_detector import DuplicateDetector
from .search_engine import LeadSearchEngine, SearchQuery, SearchFilter, SortCriteria, ComparisonOperator, SortOrder

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """
    Lead data model with all supported fields
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str = ""
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    verified: bool = False
    enriched: bool = False
    needs_enrichment: bool = True
    status: str = 'new'
    source: Optional[str] = None
    scraped_at: Optional[datetime] = None
    enriched_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    airtable_id: Optional[str] = None
    airtable_synced: bool = False
    sync_pending: bool = True
    last_sync_attempt: Optional[datetime] = None
    sync_error: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary format"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        for field_name in ['scraped_at', 'enriched_at', 'updated_at', 'created_at', 'last_sync_attempt']:
            if data[field_name] and isinstance(data[field_name], datetime):
                data[field_name] = data[field_name].isoformat()
        
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create lead from dictionary data"""
        # Convert ISO strings back to datetime objects
        datetime_fields = ['scraped_at', 'enriched_at', 'updated_at', 'created_at', 'last_sync_attempt']
        
        for field_name in datetime_fields:
            if data.get(field_name) and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    data[field_name] = None
        
        # Handle raw_data JSON parsing
        if data.get('raw_data') and isinstance(data['raw_data'], str):
            try:
                data['raw_data'] = json.loads(data['raw_data'])
            except (json.JSONDecodeError, TypeError):
                data['raw_data'] = None
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class LeadDatabase:
    """
    High-level API for lead database operations
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Lead Database API
        
        Args:
            db_path: Optional custom database path
        """
        self.db_conn = get_database_connection(db_path)
        self.duplicate_detector = DuplicateDetector(self.db_conn)
        self.search_engine = LeadSearchEngine(self.db_conn)
        logger.info("Lead Database API initialized")
    
    def add_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Add a new lead to the database with duplicate detection
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            str: Lead ID (existing if duplicate found, new if created)
            
        Raises:
            ValueError: If required fields are missing
            RuntimeError: If database operation fails
        """
        try:
            # Validate required fields
            if not lead_data.get('full_name'):
                raise ValueError("full_name is required")
            
            # Check for duplicates using enhanced detection
            duplicate_match = self.duplicate_detector.get_best_duplicate(lead_data)
            
            if duplicate_match:
                logger.info(f"Duplicate lead found (confidence: {duplicate_match.confidence:.2f}, "
                           f"type: {duplicate_match.match_type}): {duplicate_match.lead_id}")
                
                # Merge data intelligently
                merged_data = self.duplicate_detector.merge_lead_data(
                    duplicate_match.existing_lead, lead_data
                )
                
                # Update with merged data
                self.update_lead(duplicate_match.lead_id, merged_data)
                return duplicate_match.lead_id
            
            # Create new lead
            lead = Lead.from_dict(lead_data)
            
            # Ensure timestamps are set
            now = datetime.now()
            if not lead.created_at:
                lead.created_at = now
            lead.updated_at = now
            
            # Prepare raw_data JSON
            raw_data_json = None
            if lead.raw_data:
                raw_data_json = json.dumps(lead.raw_data)
            
            # Insert into database
            insert_query = """
                INSERT INTO leads (
                    id, uuid, full_name, linkedin_url, email, company, title,
                    location, industry, company_size, verified, enriched, needs_enrichment,
                    status, source, scraped_at, enriched_at, updated_at, created_at,
                    airtable_id, airtable_synced, sync_pending, last_sync_attempt,
                    sync_error, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                lead.id, lead.uuid, lead.full_name, lead.linkedin_url, lead.email,
                lead.company, lead.title, lead.location, lead.industry, lead.company_size,
                lead.verified, lead.enriched, lead.needs_enrichment, lead.status, lead.source,
                lead.scraped_at.isoformat() if lead.scraped_at else None,
                lead.enriched_at.isoformat() if lead.enriched_at else None,
                lead.updated_at.isoformat(), lead.created_at.isoformat(),
                lead.airtable_id, lead.airtable_synced, lead.sync_pending,
                lead.last_sync_attempt.isoformat() if lead.last_sync_attempt else None,
                lead.sync_error, raw_data_json
            )
            
            rows_affected = self.db_conn.execute_update(insert_query, params)
            
            if rows_affected != 1:
                raise RuntimeError(f"Expected 1 row affected, got {rows_affected}")
            
            logger.info(f"Lead added successfully: {lead.id} ({lead.full_name})")
            return lead.id
            
        except Exception as e:
            logger.error(f"Failed to add lead: {e}")
            raise
    
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a lead by ID
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            dict: Lead data or None if not found
        """
        try:
            query = "SELECT * FROM leads WHERE id = ?"
            cursor = self.db_conn.execute_query(query, (lead_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            lead_data = dict(row)
            
            # Parse raw_data JSON
            if lead_data.get('raw_data'):
                try:
                    lead_data['raw_data'] = json.loads(lead_data['raw_data'])
                except (json.JSONDecodeError, TypeError):
                    lead_data['raw_data'] = None
            
            return lead_data
            
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            raise
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing lead
        
        Args:
            lead_id: Lead identifier
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if update successful, False if lead not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            # Get existing lead to preserve creation timestamp
            existing = self.get_lead(lead_id)
            if not existing:
                logger.warning(f"Lead not found for update: {lead_id}")
                return False
            
            # Prepare update data
            updates = updates.copy()
            updates['updated_at'] = datetime.now().isoformat()
            
            # Handle raw_data JSON serialization
            if 'raw_data' in updates:
                if updates['raw_data']:
                    updates['raw_data'] = json.dumps(updates['raw_data'])
                else:
                    updates['raw_data'] = None
            
            # Build dynamic update query
            update_fields = []
            params = []
            
            for field, value in updates.items():
                if field in ['id', 'uuid', 'created_at']:  # Skip immutable fields
                    continue
                
                update_fields.append(f"{field} = ?")
                params.append(value)
            
            if not update_fields:
                logger.warning(f"No valid fields to update for lead: {lead_id}")
                return True
            
            params.append(lead_id)  # Add WHERE parameter
            
            query = f"UPDATE leads SET {', '.join(update_fields)} WHERE id = ?"
            rows_affected = self.db_conn.execute_update(query, tuple(params))
            
            if rows_affected == 1:
                logger.info(f"Lead updated successfully: {lead_id}")
                return True
            else:
                logger.warning(f"No rows affected in update for lead: {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id}: {e}")
            raise
    
    def search_leads(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search leads with flexible filtering (legacy method for backward compatibility)
        
        Args:
            filters: Dictionary of search criteria
            
        Returns:
            list: List of matching leads
        """
        try:
            # Convert legacy filters to new SearchFilter format
            search_filters = []
            
            for field, value in filters.items():
                if value is None:
                    continue
                
                if field in ['full_name', 'company', 'title', 'email', 'linkedin_url']:
                    if isinstance(value, str) and '%' in value:
                        search_filters.append(SearchFilter(field, ComparisonOperator.LIKE, value))
                    else:
                        search_filters.append(SearchFilter(field, ComparisonOperator.EQUALS, value))
                
                elif field in ['verified', 'enriched', 'needs_enrichment', 'airtable_synced', 'sync_pending']:
                    search_filters.append(SearchFilter(field, ComparisonOperator.EQUALS, bool(value)))
                
                elif field == 'status':
                    search_filters.append(SearchFilter(field, ComparisonOperator.EQUALS, value))
                
                elif field == 'created_after':
                    search_filters.append(SearchFilter('created_at', ComparisonOperator.GREATER_THAN, value))
                
                elif field == 'created_before':
                    search_filters.append(SearchFilter('created_at', ComparisonOperator.LESS_THAN, value))
            
            # Use new search engine
            query = SearchQuery(
                filters=search_filters,
                sort_by=[SortCriteria('created_at', SortOrder.DESC)]
            )
            
            result = self.search_engine.search(query)
            logger.info(f"Search returned {len(result.leads)} leads")
            return result.leads
            
        except Exception as e:
            logger.error(f"Failed to search leads: {e}")
            raise
    
    def get_all_leads(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all leads with optional pagination
        
        Args:
            limit: Maximum number of leads to return
            offset: Number of leads to skip
            
        Returns:
            list: List of all leads
        """
        try:
            query = "SELECT * FROM leads ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                lead_data = dict(row)
                
                # Parse raw_data JSON
                if lead_data.get('raw_data'):
                    try:
                        lead_data['raw_data'] = json.loads(lead_data['raw_data'])
                    except (json.JSONDecodeError, TypeError):
                        lead_data['raw_data'] = None
                
                results.append(lead_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get all leads: {e}")
            raise
    
    def mark_for_sync(self, lead_id: str) -> bool:
        """
        Mark a lead for Airtable synchronization
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            bool: True if successful
        """
        try:
            query = "UPDATE leads SET sync_pending = ?, updated_at = ? WHERE id = ?"
            params = (True, datetime.now().isoformat(), lead_id)
            
            rows_affected = self.db_conn.execute_update(query, params)
            
            if rows_affected == 1:
                logger.info(f"Lead marked for sync: {lead_id}")
                return True
            else:
                logger.warning(f"Lead not found for sync marking: {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to mark lead for sync {lead_id}: {e}")
            raise
    
    def get_sync_pending_leads(self) -> List[Dict[str, Any]]:
        """
        Get all leads that need to be synced to Airtable
        
        Returns:
            list: List of leads pending sync
        """
        try:
            return self.search_leads({'sync_pending': True})
            
        except Exception as e:
            logger.error(f"Failed to get sync pending leads: {e}")
            raise
    
    def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead from the database
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            query = "DELETE FROM leads WHERE id = ?"
            rows_affected = self.db_conn.execute_update(query, (lead_id,))
            
            if rows_affected == 1:
                logger.info(f"Lead deleted: {lead_id}")
                return True
            else:
                logger.warning(f"Lead not found for deletion: {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            raise
    
    def get_lead_count(self) -> int:
        """
        Get total number of leads in database
        
        Returns:
            int: Total lead count
        """
        try:
            cursor = self.db_conn.execute_query("SELECT COUNT(*) FROM leads")
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.error(f"Failed to get lead count: {e}")
            raise
    
    def find_all_duplicates(self, lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all potential duplicates for a lead with confidence scores
        
        Args:
            lead_data: Lead data to check for duplicates
            
        Returns:
            list: List of duplicate matches with confidence scores
        """
        try:
            matches = self.duplicate_detector.find_duplicates(lead_data)
            
            # Convert to dictionary format for API consistency
            result = []
            for match in matches:
                result.append({
                    'lead_id': match.lead_id,
                    'confidence': match.confidence,
                    'match_type': match.match_type,
                    'match_details': match.match_details,
                    'existing_lead': match.existing_lead
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    def advanced_search(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Execute advanced search with full SearchQuery capabilities
        
        Args:
            query: SearchQuery object with filters, sorting, and pagination
            
        Returns:
            dict: SearchResult as dictionary with leads and metadata
        """
        try:
            result = self.search_engine.search(query)
            
            # Convert SearchResult to dictionary for API consistency
            return {
                'leads': result.leads,
                'total_count': result.total_count,
                'filtered_count': result.filtered_count,
                'page_info': result.page_info,
                'query_time_ms': result.query_time_ms,
                'query_sql': result.query_sql
            }
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise
    
    def quick_search(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Quick search across multiple fields
        
        Args:
            search_term: Term to search for
            limit: Maximum results to return
            
        Returns:
            list: Matching leads
        """
        try:
            return self.search_engine.quick_search(search_term, limit)
            
        except Exception as e:
            logger.error(f"Quick search failed: {e}")
            raise
    
    def search_by_company(self, company: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search leads by company name
        
        Args:
            company: Company name to search for
            exact_match: Whether to use exact matching
            
        Returns:
            list: Matching leads
        """
        try:
            return self.search_engine.search_by_company(company, exact_match)
            
        except Exception as e:
            logger.error(f"Company search failed: {e}")
            raise
    
    def search_by_location(self, location: str) -> List[Dict[str, Any]]:
        """
        Search leads by location
        
        Args:
            location: Location to search for
            
        Returns:
            list: Matching leads
        """
        try:
            return self.search_engine.search_by_location(location)
            
        except Exception as e:
            logger.error(f"Location search failed: {e}")
            raise
    
    def search_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Search leads by industry
        
        Args:
            industry: Industry to search for
            
        Returns:
            list: Matching leads
        """
        try:
            return self.search_engine.search_by_industry(industry)
            
        except Exception as e:
            logger.error(f"Industry search failed: {e}")
            raise
    
    def get_recent_leads(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently added leads
        
        Args:
            days: Number of days to look back
            limit: Maximum results to return
            
        Returns:
            list: Recent leads
        """
        try:
            return self.search_engine.get_recent_leads(days, limit)
            
        except Exception as e:
            logger.error(f"Recent leads search failed: {e}")
            raise
    
    def get_enriched_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all enriched leads
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Enriched leads
        """
        try:
            return self.search_engine.get_enriched_leads(limit)
            
        except Exception as e:
            logger.error(f"Enriched leads search failed: {e}")
            raise
    
    def get_unverified_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads that need verification
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Unverified leads
        """
        try:
            return self.search_engine.get_unverified_leads(limit)
            
        except Exception as e:
            logger.error(f"Unverified leads search failed: {e}")
            raise
    
    def get_leads_needing_enrichment(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads that need enrichment
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Leads needing enrichment
        """
        try:
            return self.search_engine.get_leads_needing_enrichment(limit)
            
        except Exception as e:
            logger.error(f"Leads needing enrichment search failed: {e}")
            raise
    
    def get_leads_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads by status
        
        Args:
            status: Lead status to filter by
            limit: Maximum results to return
            
        Returns:
            list: Leads with specified status
        """
        try:
            return self.search_engine.get_leads_by_status(status, limit)
            
        except Exception as e:
            logger.error(f"Status search failed: {e}")
            raise
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive search and database statistics
        
        Returns:
            dict: Database statistics
        """
        try:
            return self.search_engine.get_statistics()
            
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Returns:
            dict: Database statistics
        """
        try:
            stats = {}
            
            # Basic counts
            stats['total_leads'] = self.get_lead_count()
            
            # Status breakdown
            cursor = self.db_conn.execute_query(
                "SELECT status, COUNT(*) FROM leads GROUP BY status"
            )
            stats['status_counts'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Sync status
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE sync_pending = 1"
            )
            stats['pending_sync'] = cursor.fetchone()[0]
            
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE airtable_synced = 1"
            )
            stats['synced_to_airtable'] = cursor.fetchone()[0]
            
            # Enrichment status
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE enriched = 1"
            )
            stats['enriched_leads'] = cursor.fetchone()[0]
            
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE needs_enrichment = 1"
            )
            stats['needs_enrichment'] = cursor.fetchone()[0]
            
            # Recent activity
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE created_at > datetime('now', '-24 hours')"
            )
            stats['leads_added_today'] = cursor.fetchone()[0]
            
            cursor = self.db_conn.execute_query(
                "SELECT COUNT(*) FROM leads WHERE updated_at > datetime('now', '-24 hours')"
            )
            stats['leads_updated_today'] = cursor.fetchone()[0]
            
            # Database info
            db_info = self.db_conn.get_database_info()
            stats.update(db_info)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise


# Global database instance
_lead_db: Optional[LeadDatabase] = None

def get_lead_database(db_path: Optional[str] = None) -> LeadDatabase:
    """
    Get global Lead Database instance (singleton pattern)
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        LeadDatabase: Lead database API instance
    """
    global _lead_db
    
    if _lead_db is None:
        _lead_db = LeadDatabase(db_path)
    
    return _lead_db