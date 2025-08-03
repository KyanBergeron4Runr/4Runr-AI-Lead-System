#!/usr/bin/env python3
"""
Advanced Search Engine

Provides sophisticated search and query capabilities for lead data
with flexible filtering, sorting, pagination, and performance optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class SortOrder(Enum):
    """Sort order enumeration"""
    ASC = "ASC"
    DESC = "DESC"

class ComparisonOperator(Enum):
    """Comparison operators for filtering"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"

@dataclass
class SearchFilter:
    """
    Represents a search filter with field, operator, and value
    """
    field: str
    operator: ComparisonOperator
    value: Any = None
    case_sensitive: bool = False

@dataclass
class SortCriteria:
    """
    Represents sorting criteria
    """
    field: str
    order: SortOrder = SortOrder.DESC

@dataclass
class SearchQuery:
    """
    Comprehensive search query with filters, sorting, and pagination
    """
    filters: List[SearchFilter] = None
    sort_by: List[SortCriteria] = None
    limit: Optional[int] = None
    offset: int = 0
    include_raw_data: bool = True
    distinct: bool = False

@dataclass
class SearchResult:
    """
    Search result with metadata
    """
    leads: List[Dict[str, Any]]
    total_count: int
    filtered_count: int
    page_info: Dict[str, Any]
    query_time_ms: float
    query_sql: str

class LeadSearchEngine:
    """
    Advanced search engine for lead data
    """
    
    def __init__(self, db_connection):
        """
        Initialize search engine
        
        Args:
            db_connection: Database connection instance
        """
        self.db_conn = db_connection
        
        # Define searchable fields and their types
        self.searchable_fields = {
            'id': 'TEXT',
            'uuid': 'TEXT',
            'full_name': 'TEXT',
            'linkedin_url': 'TEXT',
            'email': 'TEXT',
            'company': 'TEXT',
            'title': 'TEXT',
            'location': 'TEXT',
            'industry': 'TEXT',
            'company_size': 'TEXT',
            'verified': 'BOOLEAN',
            'enriched': 'BOOLEAN',
            'needs_enrichment': 'BOOLEAN',
            'status': 'TEXT',
            'source': 'TEXT',
            'scraped_at': 'TIMESTAMP',
            'enriched_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'created_at': 'TIMESTAMP',
            'airtable_id': 'TEXT',
            'airtable_synced': 'BOOLEAN',
            'sync_pending': 'BOOLEAN',
            'last_sync_attempt': 'TIMESTAMP',
            'sync_error': 'TEXT'
        }
        
        # Define sortable fields
        self.sortable_fields = {
            'full_name', 'company', 'title', 'created_at', 'updated_at',
            'scraped_at', 'enriched_at', 'status', 'industry', 'location'
        }
    
    def search(self, query: SearchQuery) -> SearchResult:
        """
        Execute advanced search query
        
        Args:
            query: SearchQuery object with filters and options
            
        Returns:
            SearchResult: Search results with metadata
        """
        start_time = datetime.now()
        
        try:
            # Build SQL query
            sql_query, params = self._build_sql_query(query)
            
            # Execute count query for total results
            count_query = self._build_count_query(query)
            count_cursor = self.db_conn.execute_query(count_query, params)
            total_count = count_cursor.fetchone()[0]
            
            # Execute main query
            cursor = self.db_conn.execute_query(sql_query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries and process
            leads = []
            for row in rows:
                lead_data = dict(row)
                
                # Parse raw_data JSON if requested
                if query.include_raw_data and lead_data.get('raw_data'):
                    try:
                        lead_data['raw_data'] = json.loads(lead_data['raw_data'])
                    except (json.JSONDecodeError, TypeError):
                        lead_data['raw_data'] = None
                elif not query.include_raw_data:
                    lead_data.pop('raw_data', None)
                
                leads.append(lead_data)
            
            # Calculate query time
            end_time = datetime.now()
            query_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Build page info
            page_info = self._build_page_info(query, len(leads), total_count)
            
            return SearchResult(
                leads=leads,
                total_count=total_count,
                filtered_count=len(leads),
                page_info=page_info,
                query_time_ms=query_time_ms,
                query_sql=sql_query
            )
            
        except Exception as e:
            logger.error(f"Search query failed: {e}")
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
        if not search_term or not search_term.strip():
            return []
        
        search_term = search_term.strip()
        
        # Create filters for multiple fields
        filters = [
            SearchFilter('full_name', ComparisonOperator.LIKE, f'%{search_term}%'),
            SearchFilter('company', ComparisonOperator.LIKE, f'%{search_term}%'),
            SearchFilter('title', ComparisonOperator.LIKE, f'%{search_term}%'),
            SearchFilter('email', ComparisonOperator.LIKE, f'%{search_term}%'),
            SearchFilter('location', ComparisonOperator.LIKE, f'%{search_term}%'),
            SearchFilter('industry', ComparisonOperator.LIKE, f'%{search_term}%')
        ]
        
        # Build OR query
        where_clauses = []
        params = []
        
        for filter_obj in filters:
            clause, filter_params = self._build_filter_clause(filter_obj)
            where_clauses.append(clause)
            params.extend(filter_params)
        
        # Combine with OR
        where_sql = f"({' OR '.join(where_clauses)})"
        
        # Build full query
        sql_query = f"""
            SELECT * FROM leads 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        
        try:
            cursor = self.db_conn.execute_query(sql_query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
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
            logger.error(f"Quick search failed: {e}")
            return []
    
    def search_by_company(self, company: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search leads by company name
        
        Args:
            company: Company name to search for
            exact_match: Whether to use exact matching
            
        Returns:
            list: Matching leads
        """
        if exact_match:
            filter_obj = SearchFilter('company', ComparisonOperator.EQUALS, company)
        else:
            filter_obj = SearchFilter('company', ComparisonOperator.LIKE, f'%{company}%')
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('full_name', SortOrder.ASC)]
        )
        
        result = self.search(query)
        return result.leads
    
    def search_by_location(self, location: str) -> List[Dict[str, Any]]:
        """
        Search leads by location
        
        Args:
            location: Location to search for
            
        Returns:
            list: Matching leads
        """
        filter_obj = SearchFilter('location', ComparisonOperator.LIKE, f'%{location}%')
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('company', SortOrder.ASC)]
        )
        
        result = self.search(query)
        return result.leads
    
    def search_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Search leads by industry
        
        Args:
            industry: Industry to search for
            
        Returns:
            list: Matching leads
        """
        filter_obj = SearchFilter('industry', ComparisonOperator.LIKE, f'%{industry}%')
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('company', SortOrder.ASC)]
        )
        
        result = self.search(query)
        return result.leads
    
    def get_recent_leads(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently added leads
        
        Args:
            days: Number of days to look back
            limit: Maximum results to return
            
        Returns:
            list: Recent leads
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filter_obj = SearchFilter('created_at', ComparisonOperator.GREATER_EQUAL, cutoff_date.isoformat())
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('created_at', SortOrder.DESC)],
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_enriched_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all enriched leads
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Enriched leads
        """
        filter_obj = SearchFilter('enriched', ComparisonOperator.EQUALS, True)
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('enriched_at', SortOrder.DESC)],
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_unverified_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads that need verification
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Unverified leads
        """
        filter_obj = SearchFilter('verified', ComparisonOperator.EQUALS, False)
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('created_at', SortOrder.DESC)],
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_leads_needing_enrichment(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads that need enrichment
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Leads needing enrichment
        """
        filter_obj = SearchFilter('needs_enrichment', ComparisonOperator.EQUALS, True)
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('created_at', SortOrder.ASC)],  # Oldest first
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_sync_pending_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads pending Airtable sync
        
        Args:
            limit: Maximum results to return
            
        Returns:
            list: Leads pending sync
        """
        filter_obj = SearchFilter('sync_pending', ComparisonOperator.EQUALS, True)
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('updated_at', SortOrder.ASC)],  # Oldest updates first
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_leads_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads by status
        
        Args:
            status: Lead status to filter by
            limit: Maximum results to return
            
        Returns:
            list: Leads with specified status
        """
        filter_obj = SearchFilter('status', ComparisonOperator.EQUALS, status)
        
        query = SearchQuery(
            filters=[filter_obj],
            sort_by=[SortCriteria('updated_at', SortOrder.DESC)],
            limit=limit
        )
        
        result = self.search(query)
        return result.leads
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive search statistics
        
        Returns:
            dict: Database statistics
        """
        try:
            stats = {}
            
            # Total counts
            cursor = self.db_conn.execute_query("SELECT COUNT(*) FROM leads")
            stats['total_leads'] = cursor.fetchone()[0]
            
            # Status breakdown
            cursor = self.db_conn.execute_query("""
                SELECT status, COUNT(*) 
                FROM leads 
                GROUP BY status 
                ORDER BY COUNT(*) DESC
            """)
            stats['status_breakdown'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Company breakdown (top 10)
            cursor = self.db_conn.execute_query("""
                SELECT company, COUNT(*) 
                FROM leads 
                WHERE company IS NOT NULL AND company != ''
                GROUP BY company 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            stats['top_companies'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Industry breakdown (top 10)
            cursor = self.db_conn.execute_query("""
                SELECT industry, COUNT(*) 
                FROM leads 
                WHERE industry IS NOT NULL AND industry != ''
                GROUP BY industry 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            stats['top_industries'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Location breakdown (top 10)
            cursor = self.db_conn.execute_query("""
                SELECT location, COUNT(*) 
                FROM leads 
                WHERE location IS NOT NULL AND location != ''
                GROUP BY location 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            stats['top_locations'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Verification status
            cursor = self.db_conn.execute_query("""
                SELECT verified, COUNT(*) 
                FROM leads 
                GROUP BY verified
            """)
            verification_counts = {bool(row[0]): row[1] for row in cursor.fetchall()}
            stats['verified_count'] = verification_counts.get(True, 0)
            stats['unverified_count'] = verification_counts.get(False, 0)
            
            # Enrichment status
            cursor = self.db_conn.execute_query("""
                SELECT enriched, COUNT(*) 
                FROM leads 
                GROUP BY enriched
            """)
            enrichment_counts = {bool(row[0]): row[1] for row in cursor.fetchall()}
            stats['enriched_count'] = enrichment_counts.get(True, 0)
            stats['unenriched_count'] = enrichment_counts.get(False, 0)
            
            # Sync status
            cursor = self.db_conn.execute_query("""
                SELECT sync_pending, COUNT(*) 
                FROM leads 
                GROUP BY sync_pending
            """)
            sync_counts = {bool(row[0]): row[1] for row in cursor.fetchall()}
            stats['sync_pending_count'] = sync_counts.get(True, 0)
            stats['synced_count'] = sync_counts.get(False, 0)
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = self.db_conn.execute_query("""
                SELECT COUNT(*) FROM leads 
                WHERE created_at > ?
            """, (week_ago,))
            stats['leads_added_this_week'] = cursor.fetchone()[0]
            
            cursor = self.db_conn.execute_query("""
                SELECT COUNT(*) FROM leads 
                WHERE updated_at > ?
            """, (week_ago,))
            stats['leads_updated_this_week'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def _build_sql_query(self, query: SearchQuery) -> Tuple[str, List[Any]]:
        """
        Build SQL query from SearchQuery object
        
        Args:
            query: SearchQuery object
            
        Returns:
            tuple: (SQL query string, parameters list)
        """
        # Base query
        if query.distinct:
            sql_parts = ["SELECT DISTINCT * FROM leads"]
        else:
            sql_parts = ["SELECT * FROM leads"]
        
        params = []
        
        # Build WHERE clause
        if query.filters:
            where_clauses = []
            for filter_obj in query.filters:
                clause, filter_params = self._build_filter_clause(filter_obj)
                where_clauses.append(clause)
                params.extend(filter_params)
            
            if where_clauses:
                sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # Build ORDER BY clause
        if query.sort_by:
            order_clauses = []
            for sort_criteria in query.sort_by:
                if sort_criteria.field in self.sortable_fields:
                    order_clauses.append(f"{sort_criteria.field} {sort_criteria.order.value}")
            
            if order_clauses:
                sql_parts.append(f"ORDER BY {', '.join(order_clauses)}")
        else:
            # Default sort by created_at DESC
            sql_parts.append("ORDER BY created_at DESC")
        
        # Build LIMIT and OFFSET
        if query.limit:
            sql_parts.append(f"LIMIT {query.limit}")
        
        if query.offset > 0:
            sql_parts.append(f"OFFSET {query.offset}")
        
        return " ".join(sql_parts), params
    
    def _build_count_query(self, query: SearchQuery) -> str:
        """
        Build count query for total results
        
        Args:
            query: SearchQuery object
            
        Returns:
            str: Count SQL query
        """
        sql_parts = ["SELECT COUNT(*) FROM leads"]
        
        # Build WHERE clause (same as main query)
        if query.filters:
            where_clauses = []
            for filter_obj in query.filters:
                clause, _ = self._build_filter_clause(filter_obj)
                where_clauses.append(clause)
            
            if where_clauses:
                sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        return " ".join(sql_parts)
    
    def _build_filter_clause(self, filter_obj: SearchFilter) -> Tuple[str, List[Any]]:
        """
        Build SQL WHERE clause for a single filter
        
        Args:
            filter_obj: SearchFilter object
            
        Returns:
            tuple: (WHERE clause, parameters list)
        """
        field = filter_obj.field
        operator = filter_obj.operator
        value = filter_obj.value
        
        # Validate field
        if field not in self.searchable_fields:
            raise ValueError(f"Field '{field}' is not searchable")
        
        params = []
        
        if operator == ComparisonOperator.IS_NULL:
            return f"{field} IS NULL", params
        
        elif operator == ComparisonOperator.IS_NOT_NULL:
            return f"{field} IS NOT NULL", params
        
        elif operator == ComparisonOperator.IN:
            if not isinstance(value, (list, tuple)):
                raise ValueError("IN operator requires list or tuple value")
            placeholders = ",".join(["?" for _ in value])
            params.extend(value)
            return f"{field} IN ({placeholders})", params
        
        elif operator == ComparisonOperator.NOT_IN:
            if not isinstance(value, (list, tuple)):
                raise ValueError("NOT IN operator requires list or tuple value")
            placeholders = ",".join(["?" for _ in value])
            params.extend(value)
            return f"{field} NOT IN ({placeholders})", params
        
        elif operator == ComparisonOperator.BETWEEN:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("BETWEEN operator requires list/tuple with 2 values")
            params.extend(value)
            return f"{field} BETWEEN ? AND ?", params
        
        elif operator in [ComparisonOperator.LIKE, ComparisonOperator.NOT_LIKE]:
            # Handle case sensitivity for LIKE operations
            if not filter_obj.case_sensitive and self.searchable_fields[field] == 'TEXT':
                clause = f"LOWER({field}) {operator.value} LOWER(?)"
                params.append(str(value).lower() if value else '')
            else:
                clause = f"{field} {operator.value} ?"
                params.append(value)
            return clause, params
        
        else:
            # Standard comparison operators
            if not filter_obj.case_sensitive and self.searchable_fields[field] == 'TEXT' and operator in [ComparisonOperator.EQUALS, ComparisonOperator.NOT_EQUALS]:
                clause = f"LOWER({field}) {operator.value} LOWER(?)"
                params.append(str(value).lower() if value else '')
            else:
                clause = f"{field} {operator.value} ?"
                params.append(value)
            return clause, params
    
    def _build_page_info(self, query: SearchQuery, result_count: int, total_count: int) -> Dict[str, Any]:
        """
        Build pagination information
        
        Args:
            query: SearchQuery object
            result_count: Number of results returned
            total_count: Total number of matching results
            
        Returns:
            dict: Pagination information
        """
        page_info = {
            'has_results': result_count > 0,
            'result_count': result_count,
            'total_count': total_count,
            'offset': query.offset,
            'limit': query.limit
        }
        
        if query.limit:
            page_info['current_page'] = (query.offset // query.limit) + 1
            page_info['total_pages'] = (total_count + query.limit - 1) // query.limit
            page_info['has_next_page'] = query.offset + query.limit < total_count
            page_info['has_previous_page'] = query.offset > 0
            page_info['next_offset'] = query.offset + query.limit if page_info['has_next_page'] else None
            page_info['previous_offset'] = max(0, query.offset - query.limit) if page_info['has_previous_page'] else None
        
        return page_info