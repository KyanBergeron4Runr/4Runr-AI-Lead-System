"""
Lead Database API - Core interface for lead data management with comprehensive logging.

This module provides a comprehensive API for managing lead data with features including:
- Thread-safe operations with connection pooling
- Automatic duplicate detection and merging
- UUID-based lead identification
- Comprehensive error handling and logging
- Integration with existing LocalDatabaseManager
"""

import os
import sqlite3
import json
import uuid
import datetime
import threading
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, field

from engager.local_database_manager import LocalDatabaseManager
from database_logger import database_logger, monitor_performance, log_database_event
from database_connection_pool import get_connection_pool, database_connection, database_transaction
from concurrent_access_manager import get_concurrent_access_manager, thread_safe_operation, OperationPriority


@dataclass
class Lead:
    """Lead data model with comprehensive field support."""
    id: str
    uuid: str
    full_name: str
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
    scraped_at: Optional[datetime.datetime] = None
    enriched_at: Optional[datetime.datetime] = None
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    airtable_id: Optional[str] = None
    airtable_synced: bool = False


class LeadDatabase:
    """
    Core Lead Database API providing comprehensive lead management functionality.
    
    This class extends the existing LocalDatabaseManager with enhanced features for
    lead data management, including duplicate detection, UUID-based identification,
    and comprehensive CRUD operations with full logging.
    """
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """
        Initialize the Lead Database API.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Initialize the underlying database manager
        self.db_manager = LocalDatabaseManager(db_path)
        self.db_path = self.db_manager.db_path
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Ensure extended schema
        self._ensure_extended_schema()
    
    @contextmanager
    def get_connection(self):
        """
        Thread-safe context manager for database connections using connection pool.
        
        Yields:
            sqlite3.Connection: Database connection with row factory
        """
        # Use the connection pool for better concurrency
        pool = get_connection_pool()
        with pool.get_connection() as conn:
            yield conn
    
    def _ensure_extended_schema(self) -> None:
        """Ensure database has the extended schema for comprehensive lead management."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check existing columns in leads table
                cursor.execute("PRAGMA table_info(leads)")
                existing_columns = {row[1] for row in cursor.fetchall()}
                
                # Define required columns for comprehensive lead management
                required_columns = {
                    'uuid': 'TEXT',
                    'full_name': 'TEXT',
                    'linkedin_url': 'TEXT',
                    'title': 'TEXT',
                    'location': 'TEXT',
                    'industry': 'TEXT',
                    'company_size': 'TEXT',
                    'verified': 'BOOLEAN DEFAULT FALSE',
                    'enriched': 'BOOLEAN DEFAULT FALSE',
                    'needs_enrichment': 'BOOLEAN DEFAULT TRUE',
                    'status': 'TEXT DEFAULT "new"',
                    'source': 'TEXT',
                    'scraped_at': 'TEXT',
                    'enriched_at': 'TEXT',
                    'airtable_id': 'TEXT',
                    'airtable_synced': 'BOOLEAN DEFAULT FALSE',
                    'sync_pending': 'BOOLEAN DEFAULT TRUE',
                    'last_sync_attempt': 'TEXT',
                    'sync_error': 'TEXT',
                    'raw_data': 'TEXT'
                }
                
                # Add missing columns
                for column_name, column_def in required_columns.items():
                    if column_name not in existing_columns:
                        try:
                            cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_def}")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" not in str(e).lower():
                                raise
                
                conn.commit()
                
        except Exception as e:
            # Error will be logged by calling functions if needed
            raise
    
    @monitor_performance("add_lead")
    @thread_safe_operation("add_lead", priority=OperationPriority.NORMAL, resource_locks=["leads_table"])
    def add_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Add a new lead with automatic duplicate detection and UUID generation.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            str: Lead ID (UUID) of the added or updated lead
            
        Raises:
            ValueError: If required fields are missing
            Exception: If database operation fails
        """
        start_time = time.time()
        operation_result = {"success": False, "records_affected": 0, "duplicate_detected": False}
        
        try:
            # Validate required fields
            if not lead_data.get('full_name') and not lead_data.get('name'):
                raise ValueError("Lead must have a name (full_name or name field)")
            
            # Normalize name field
            full_name = lead_data.get('full_name') or lead_data.get('name', '')
            
            # Check for duplicates
            existing_lead_id = self._find_duplicates(lead_data)
            
            if existing_lead_id:
                # Update existing lead instead of creating duplicate
                updated_data = self._merge_lead_data(existing_lead_id, lead_data)
                self.update_lead(existing_lead_id, updated_data)
                
                operation_result.update({
                    "success": True,
                    "records_affected": 1,
                    "duplicate_detected": True,
                    "duplicate_action": "updated"
                })
                
                return existing_lead_id
            
            # Generate new UUID for the lead
            lead_uuid = str(uuid.uuid4())
            lead_id = lead_data.get('id') or lead_uuid
            
            # Prepare lead data with defaults
            now = datetime.datetime.now()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO leads (
                        id, uuid, name, full_name, email, company, company_website,
                        linkedin_url, title, location, industry, company_size,
                        verified, enriched, needs_enrichment, status, source,
                        scraped_at, enriched_at, airtable_id, airtable_synced,
                        sync_pending, raw_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    lead_uuid,
                    full_name,  # For backward compatibility
                    full_name,
                    lead_data.get('email'),
                    lead_data.get('company'),
                    lead_data.get('company_website') or lead_data.get('website'),
                    lead_data.get('linkedin_url'),
                    lead_data.get('title'),
                    lead_data.get('location'),
                    lead_data.get('industry'),
                    lead_data.get('company_size'),
                    lead_data.get('verified', False),
                    lead_data.get('enriched', False),
                    lead_data.get('needs_enrichment', True),
                    lead_data.get('status', 'new'),
                    lead_data.get('source'),
                    self._parse_datetime(lead_data.get('scraped_at')),
                    self._parse_datetime(lead_data.get('enriched_at')),
                    lead_data.get('airtable_id'),
                    lead_data.get('airtable_synced', False),
                    lead_data.get('sync_pending', True),
                    json.dumps(lead_data.get('raw_data')) if lead_data.get('raw_data') else None,
                    now.isoformat(),
                    now.isoformat()
                ))
                
                conn.commit()
            
            # Log successful operation
            execution_time_ms = (time.time() - start_time) * 1000
            operation_result.update({
                "success": True,
                "records_affected": 1,
                "duplicate_detected": False,
                "duplicate_action": "created"
            })
            
            performance_metrics = {
                "execution_time_ms": execution_time_ms,
                "database_queries": 1,
                "memory_usage_mb": 0,
                "cpu_time_ms": execution_time_ms
            }
            
            log_database_event("database_operation", lead_data, operation_result, {
                "operation_type": "add_lead",
                "performance_metrics": performance_metrics
            })
            
            return lead_id
            
        except Exception as e:
            # Log error with context
            execution_time_ms = (time.time() - start_time) * 1000
            operation_result.update({
                "success": False,
                "error": str(e)
            })
            
            error_details = {
                "message": str(e),
                "stack_trace": traceback.format_exc(),
                "severity": "error"
            }
            
            context = {
                "operation": "add_lead",
                "lead_data": {k: v for k, v in lead_data.items() if k not in ['raw_data']},
                "execution_time_ms": execution_time_ms
            }
            
            database_logger.log_error("database_error", error_details, context)
            raise
    
    @monitor_performance("get_lead")
    @thread_safe_operation("get_lead", priority=OperationPriority.LOW, resource_locks=["leads_table"])
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a lead by ID.
        
        Args:
            lead_id: Lead identifier (ID or UUID)
            
        Returns:
            Dictionary with lead data or None if not found
        """
        start_time = time.time()
        operation_result = {"success": False, "records_affected": 0}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Try to find by ID first, then by UUID
                cursor.execute("""
                    SELECT * FROM leads 
                    WHERE id = ? OR uuid = ?
                    LIMIT 1
                """, (lead_id, lead_id))
                
                row = cursor.fetchone()
                
                if row:
                    lead_data = dict(row)
                    
                    # Parse JSON fields
                    if lead_data.get('raw_data'):
                        try:
                            lead_data['raw_data'] = json.loads(lead_data['raw_data'])
                        except (json.JSONDecodeError, TypeError):
                            lead_data['raw_data'] = None
                    
                    # Parse datetime fields
                    for field in ['scraped_at', 'enriched_at', 'created_at', 'updated_at', 'last_sync_attempt']:
                        if lead_data.get(field):
                            lead_data[field] = self._parse_datetime(lead_data[field])
                    
                    # Log successful retrieval
                    execution_time_ms = (time.time() - start_time) * 1000
                    operation_result.update({
                        "success": True,
                        "records_affected": 1
                    })
                    
                    performance_metrics = {
                        "execution_time_ms": execution_time_ms,
                        "database_queries": 1,
                        "memory_usage_mb": 0,
                        "cpu_time_ms": execution_time_ms
                    }
                    
                    log_database_event("database_operation", {"id": lead_id}, operation_result, {
                        "operation_type": "get_lead",
                        "performance_metrics": performance_metrics
                    })
                    
                    return lead_data
                
                # Log not found
                execution_time_ms = (time.time() - start_time) * 1000
                operation_result.update({
                    "success": True,
                    "records_affected": 0,
                    "error": "Lead not found"
                })
                
                log_database_event("database_operation", {"id": lead_id}, operation_result, {
                    "operation_type": "get_lead",
                    "performance_metrics": {"execution_time_ms": execution_time_ms}
                })
                
                return None
                
        except Exception as e:
            # Log error
            execution_time_ms = (time.time() - start_time) * 1000
            operation_result.update({
                "success": False,
                "error": str(e)
            })
            
            error_details = {
                "message": str(e),
                "stack_trace": traceback.format_exc(),
                "severity": "error"
            }
            
            context = {
                "operation": "get_lead",
                "lead_id": lead_id,
                "execution_time_ms": execution_time_ms
            }
            
            database_logger.log_error("database_error", error_details, context)
            return None
    
    @monitor_performance("update_lead")
    @thread_safe_operation("update_lead", priority=OperationPriority.NORMAL, resource_locks=["leads_table"])
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing lead with new data.
        
        Args:
            lead_id: Lead identifier
            updates: Dictionary with fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if not updates:
                return True
            
            # Get current lead data
            current_lead = self.get_lead(lead_id)
            if not current_lead:
                return False
            
            # Prepare update fields
            update_fields = []
            update_values = []
            
            # Handle special fields
            if 'name' in updates and 'full_name' not in updates:
                updates['full_name'] = updates['name']
            
            # Build update query
            for field, value in updates.items():
                if field in ['id', 'uuid']:  # Skip immutable fields
                    continue
                    
                if field == 'raw_data' and value is not None:
                    value = json.dumps(value)
                elif field in ['scraped_at', 'enriched_at'] and value:
                    value = self._parse_datetime(value)
                
                update_fields.append(f"{field} = ?")
                update_values.append(value)
            
            if not update_fields:
                return True
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            update_values.append(datetime.datetime.now().isoformat())
            
            # Execute update
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                    UPDATE leads 
                    SET {', '.join(update_fields)}
                    WHERE id = ? OR uuid = ?
                """
                update_values.extend([lead_id, lead_id])
                
                cursor.execute(query, update_values)
                
                if cursor.rowcount == 0:
                    return False
                
                conn.commit()
            
            return True
            
        except Exception as e:
            return False
    
    def _find_duplicates(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Find duplicate leads based on LinkedIn URL, email, or name+company.
        
        Args:
            lead_data: Lead data to check for duplicates
            
        Returns:
            Lead ID if duplicate found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check by LinkedIn URL (highest priority)
                linkedin_url = lead_data.get('linkedin_url')
                if linkedin_url:
                    cursor.execute("""
                        SELECT id FROM leads 
                        WHERE linkedin_url = ? AND linkedin_url != ''
                        LIMIT 1
                    """, (linkedin_url,))
                    
                    result = cursor.fetchone()
                    if result:
                        return result['id']
                
                # Check by email (second priority)
                email = lead_data.get('email')
                if email:
                    cursor.execute("""
                        SELECT id FROM leads 
                        WHERE email = ? AND email != ''
                        LIMIT 1
                    """, (email,))
                    
                    result = cursor.fetchone()
                    if result:
                        return result['id']
                
                # Check by name + company (third priority)
                name = lead_data.get('full_name') or lead_data.get('name')
                company = lead_data.get('company')
                
                if name and company:
                    cursor.execute("""
                        SELECT id FROM leads 
                        WHERE (full_name = ? OR name = ?) AND company = ?
                        LIMIT 1
                    """, (name, name, company))
                    
                    result = cursor.fetchone()
                    if result:
                        return result['id']
                
                return None
                
        except Exception as e:
            return None
    
    def _merge_lead_data(self, existing_lead_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge new lead data with existing lead data.
        
        Args:
            existing_lead_id: ID of existing lead
            new_data: New data to merge
            
        Returns:
            Merged data dictionary
        """
        try:
            existing_lead = self.get_lead(existing_lead_id)
            if not existing_lead:
                return new_data
            
            merged_data = {}
            
            # Merge fields, preferring non-empty new values
            for field, new_value in new_data.items():
                existing_value = existing_lead.get(field)
                
                # Use new value if it's not empty/None and existing is empty/None
                if new_value and not existing_value:
                    merged_data[field] = new_value
                # For enrichment status, prefer True over False
                elif field in ['verified', 'enriched'] and new_value and not existing_value:
                    merged_data[field] = new_value
                # For dates, use the most recent
                elif field in ['scraped_at', 'enriched_at'] and new_value:
                    merged_data[field] = new_value
            
            return merged_data
            
        except Exception as e:
            return new_data
    
    def _parse_datetime(self, dt_value: Any) -> Optional[str]:
        """
        Parse datetime value to ISO format string.
        
        Args:
            dt_value: Datetime value to parse
            
        Returns:
            ISO format datetime string or None
        """
        if not dt_value:
            return None
        
        if isinstance(dt_value, str):
            return dt_value
        elif isinstance(dt_value, datetime.datetime):
            return dt_value.isoformat()
        else:
            return str(dt_value)
    
    def get_sync_pending_leads(self) -> List[Dict[str, Any]]:
        """
        Get all leads that are pending sync to Airtable.
        
        Returns:
            List of lead dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM leads 
                    WHERE sync_pending = TRUE OR airtable_synced = FALSE
                    ORDER BY created_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            return []
    
    def mark_for_sync(self, lead_id: str) -> bool:
        """
        Mark a lead for sync to Airtable.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_lead(lead_id, {'sync_pending': True})
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total leads
                cursor.execute("SELECT COUNT(*) as total FROM leads")
                total_leads = cursor.fetchone()['total']
                
                # Pending syncs
                cursor.execute("SELECT COUNT(*) as pending FROM leads WHERE sync_pending = TRUE")
                pending_syncs = cursor.fetchone()['pending']
                
                # Enriched leads
                cursor.execute("SELECT COUNT(*) as enriched FROM leads WHERE enriched = TRUE")
                enriched_leads = cursor.fetchone()['enriched']
                
                return {
                    'total_leads': total_leads,
                    'pending_syncs': pending_syncs,
                    'enriched_leads': enriched_leads,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            return {'error': str(e)}   
 
    def search_leads(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search leads based on filters.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            List of matching lead dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause
                where_conditions = []
                values = []
                
                for field, value in filters.items():
                    if value is None:
                        where_conditions.append(f"{field} IS NULL OR {field} = ''")
                    else:
                        where_conditions.append(f"{field} = ?")
                        values.append(value)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                query = f"SELECT * FROM leads WHERE {where_clause}"
                cursor.execute(query, values)
                
                results = []
                for row in cursor.fetchall():
                    lead_data = dict(row)
                    
                    # Parse JSON fields
                    if lead_data.get('raw_data'):
                        try:
                            lead_data['raw_data'] = json.loads(lead_data['raw_data'])
                        except (json.JSONDecodeError, TypeError):
                            lead_data['raw_data'] = None
                    
                    # Parse datetime fields
                    for field in ['scraped_at', 'enriched_at', 'created_at', 'updated_at', 'last_sync_attempt']:
                        if lead_data.get(field):
                            lead_data[field] = self._parse_datetime(lead_data[field])
                    
                    results.append(lead_data)
                
                return results
                
        except Exception as e:
            return []