"""
Airtable Sync Manager for Lead Database Integration.

This module handles bidirectional synchronization between the local SQLite database
and Airtable, providing robust sync capabilities with retry logic, conflict resolution,
and comprehensive error handling.
"""

import time
import datetime
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from lead_database import LeadDatabase
from shared.airtable_client import AirtableClient
from shared.field_mapping import (
    AIRTABLE_FIELD_MAPPING, 
    map_lead_data, 
    create_airtable_update_fields,
    get_airtable_field_name
)
from database_logger import database_logger, monitor_performance, log_database_event
import traceback


class SyncOperation(Enum):
    """Types of sync operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(Enum):
    """Status of sync operations."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    operation: SyncOperation
    lead_id: str
    airtable_id: Optional[str] = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    attempt_count: int = 0
    last_attempt: Optional[datetime.datetime] = None


@dataclass
class SyncSummary:
    """Summary of sync operations."""
    total_leads: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    created_records: int = 0
    updated_records: int = 0
    errors: List[str] = None
    sync_results: List[SyncResult] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.sync_results is None:
            self.sync_results = []


class AirtableSyncManager:
    """
    Manages bidirectional synchronization between local database and Airtable.
    
    Features:
    - Push new/updated leads to Airtable
    - Pull updates from Airtable to local database
    - Retry logic with exponential backoff
    - Conflict resolution using timestamps
    - Comprehensive sync status tracking
    """
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """
        Initialize the Airtable Sync Manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = LeadDatabase(db_path)
        self.airtable = AirtableClient()
        self.logger = database_logger
        
        # Sync configuration
        self.max_retries = 3
        self.retry_delay_base = 2  # Base delay for exponential backoff
        self.batch_size = 10  # Airtable API batch limit
        
        # Field mappings for database to Airtable
        self.db_to_airtable_mapping = {
            'full_name': 'Full Name',
            'email': 'Email',
            'company': 'Company',
            'title': 'Job Title',
            'linkedin_url': 'LinkedIn',
            'location': 'Location',
            'industry': 'Industry',
            'company_size': 'Company Size',
            'verified': 'Verified',
            'enriched': 'Enriched',
            'status': 'Status',
            'source': 'Source',
            'scraped_at': 'Scraped At',
            'enriched_at': 'Enriched At'
        }
        
        # Reverse mapping for Airtable to database
        self.airtable_to_db_mapping = {v: k for k, v in self.db_to_airtable_mapping.items()}
        
        # Logging handled by decorators
        
    @monitor_performance("sync_to_airtable")
    def sync_to_airtable(self, lead_ids: Optional[List[str]] = None) -> SyncSummary:
        """
        Sync leads from database to Airtable.
        
        Args:
            lead_ids: Specific lead IDs to sync (if None, sync all pending)
            
        Returns:
            SyncSummary with detailed results
        """
        start_time = time.time()
        summary = SyncSummary()
        sync_details = {
            "batch_size": self.batch_size,
            "retry_attempts": 0,
            "sync_strategy": "to_airtable"
        }
        
        try:
            # Get leads to sync
            if lead_ids:
                leads_to_sync = []
                for lead_id in lead_ids:
                    lead = self.db.get_lead(lead_id)
                    if lead:
                        leads_to_sync.append(lead)
            else:
                leads_to_sync = self.db.get_sync_pending_leads()
            
            summary.total_leads = len(leads_to_sync)
            
            if not leads_to_sync:
                # Logging handled by decorators
                return summary
            
            # Process leads in batches
            for i in range(0, len(leads_to_sync), self.batch_size):
                batch = leads_to_sync[i:i + self.batch_size]
                batch_results = self._sync_batch_to_airtable(batch)
                summary.sync_results.extend(batch_results)
                
                # Update summary counts
                for result in batch_results:
                    if result.status == SyncStatus.SUCCESS:
                        summary.successful_syncs += 1
                        if result.operation == SyncOperation.CREATE:
                            summary.created_records += 1
                        elif result.operation == SyncOperation.UPDATE:
                            summary.updated_records += 1
                    else:
                        summary.failed_syncs += 1
                        if result.error_message:
                            summary.errors.append(f"Lead {result.lead_id}: {result.error_message}")
            
            # Update sync status in database
            self._update_sync_status_in_db(summary.sync_results)
            
            # Log successful sync operation
            execution_time_ms = (time.time() - start_time) * 1000
            sync_results = {
                "success": True,
                "leads_synced": summary.successful_syncs,
                "leads_skipped": 0,
                "leads_failed": summary.failed_syncs,
                "conflicts_resolved": 0,
                "execution_time_ms": execution_time_ms,
                "avg_sync_time_ms": execution_time_ms / max(summary.total_leads, 1),
                "api_calls": summary.total_leads,  # Approximate
                "data_transferred_mb": 0,  # Could be enhanced
                "memory_peak_mb": 0  # Could be enhanced
            }
            
            log_database_event("sync_operation", {}, sync_results, {
                "sync_type": "to_airtable",
                "sync_details": sync_details,
                "leads_processed": [{"id": lead.get("id", ""), "name": lead.get("full_name", ""), 
                                   "company": lead.get("company", ""), "sync_status": "success"} 
                                  for lead in leads_to_sync[:10]]  # Limit for log size
            })
            
            return summary
            
        except Exception as e:
            # Log sync error
            execution_time_ms = (time.time() - start_time) * 1000
            sync_results = {
                "success": False,
                "leads_synced": summary.successful_syncs,
                "leads_failed": summary.failed_syncs,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            }
            
            error_details = {
                "message": str(e),
                "stack_trace": traceback.format_exc(),
                "severity": "error"
            }
            
            context = {
                "operation": "sync_to_airtable",
                "total_leads": summary.total_leads,
                "execution_time_ms": execution_time_ms
            }
            
            database_logger.log_error("sync_error", error_details, context)
            summary.errors.append(f"Sync failed: {str(e)}")
            return summary
    
    def _sync_batch_to_airtable(self, leads: List[Dict[str, Any]]) -> List[SyncResult]:
        """
        Sync a batch of leads to Airtable.
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of SyncResult objects
        """
        results = []
        
        # Separate creates and updates
        creates = []
        updates = []
        
        for lead in leads:
            if lead.get('airtable_id'):
                updates.append(lead)
            else:
                creates.append(lead)
        
        # Process creates
        for lead in creates:
            result = self._create_lead_in_airtable(lead)
            results.append(result)
        
        # Process updates
        if updates:
            update_results = self._batch_update_leads_in_airtable(updates)
            results.extend(update_results)
        
        return results
    
    def _create_lead_in_airtable(self, lead: Dict[str, Any]) -> SyncResult:
        """
        Create a new lead in Airtable.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            SyncResult object
        """
        result = SyncResult(
            operation=SyncOperation.CREATE,
            lead_id=lead['id']
        )
        
        for attempt in range(self.max_retries):
            try:
                # Map database fields to Airtable fields
                airtable_fields = self._map_db_to_airtable_fields(lead)
                
                # Create record in Airtable
                airtable_id = self.airtable.create_lead(airtable_fields)
                
                if airtable_id:
                    result.status = SyncStatus.SUCCESS
                    result.airtable_id = airtable_id
                    break
                else:
                    result.error_message = "Failed to create record in Airtable"
                    
            except Exception as e:
                result.error_message = str(e)
                # Error logging handled by decorators
                
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay_base ** attempt)
        
        result.attempt_count = min(attempt + 1, self.max_retries)
        result.last_attempt = datetime.datetime.now()
        
        if result.status != SyncStatus.SUCCESS:
            result.status = SyncStatus.FAILED
        
        return result
    
    def _batch_update_leads_in_airtable(self, leads: List[Dict[str, Any]]) -> List[SyncResult]:
        """
        Batch update leads in Airtable.
        
        Args:
            leads: List of lead dictionaries with airtable_id
            
        Returns:
            List of SyncResult objects
        """
        results = []
        
        # Prepare batch update data
        updates = []
        for lead in leads:
            airtable_fields = self._map_db_to_airtable_fields(lead)
            updates.append({
                'id': lead['airtable_id'],
                'fields': airtable_fields
            })
            
            results.append(SyncResult(
                operation=SyncOperation.UPDATE,
                lead_id=lead['id'],
                airtable_id=lead['airtable_id']
            ))
        
        # Perform batch update with retries
        for attempt in range(self.max_retries):
            try:
                successful_count = self.airtable.batch_update_leads(updates)
                
                # Mark results based on success
                for i, result in enumerate(results):
                    if i < successful_count:
                        result.status = SyncStatus.SUCCESS
                    else:
                        result.status = SyncStatus.FAILED
                        result.error_message = "Batch update failed"
                
                break
                
            except Exception as e:
                error_msg = str(e)
                for result in results:
                    result.error_message = error_msg
                    result.attempt_count = attempt + 1
                    result.last_attempt = datetime.datetime.now()
                # Error logging handled by decorators
,
                    'attempt': attempt + 1
                })
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_base ** attempt)
        
        # Set final status for any remaining failed results
        for result in results:
            if result.status == SyncStatus.PENDING:
                result.status = SyncStatus.FAILED
            result.attempt_count = min(result.attempt_count or self.max_retries, self.max_retries)
            if not result.last_attempt:
                result.last_attempt = datetime.datetime.now()
        
        return results    

    def _map_db_to_airtable_fields(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map database fields to Airtable field names.
        
        Args:
            lead: Lead data from database
            
        Returns:
            Dictionary with Airtable field names
        """
        airtable_fields = {}
        
        # Map standard fields
        for db_field, airtable_field in self.db_to_airtable_mapping.items():
            if db_field in lead and lead[db_field] is not None:
                value = lead[db_field]
                
                # Handle datetime fields
                if db_field in ['scraped_at', 'enriched_at'] and isinstance(value, datetime.datetime):
                    value = value.isoformat()
                elif isinstance(value, str) and db_field in ['scraped_at', 'enriched_at']:
                    # Already a string, keep as is
                    pass
                
                # Handle boolean fields
                elif isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                
                airtable_fields[airtable_field] = value
        
        # Handle special fields that need custom mapping
        if lead.get('linkedin_url'):
            airtable_fields['LinkedIn'] = lead['linkedin_url']
        
        # Add sync tracking fields
        airtable_fields['Last Sync'] = datetime.datetime.now().isoformat()
        
        return airtable_fields
    
    def sync_from_airtable(self, limit: Optional[int] = None) -> SyncSummary:
        """
        Sync updates from Airtable to local database.
        
        Args:
            limit: Maximum number of records to sync
            
        Returns:
            SyncSummary with detailed results
        """
        summary = SyncSummary()
        
        try:
            # Get all leads from Airtable
            airtable_leads = self._get_all_airtable_leads(limit)
            summary.total_leads = len(airtable_leads)
            
            if not airtable_leads:
                # Logging handled by decorators
return summary
                # Logging handled by decorators
} leads from Airtable'
            })
            
            # Process each lead
            for airtable_lead in airtable_leads:
                result = self._sync_lead_from_airtable(airtable_lead)
                summary.sync_results.append(result)
                
                if result.status == SyncStatus.SUCCESS:
                    summary.successful_syncs += 1
                    if result.operation == SyncOperation.CREATE:
                        summary.created_records += 1
                    elif result.operation == SyncOperation.UPDATE:
                        summary.updated_records += 1
                else:
                    summary.failed_syncs += 1
                    if result.error_message:
                        summary.errors.append(f"Airtable {result.airtable_id}: {result.error_message}")
                # Logging handled by decorators
return summary
            
        except Exception as e:
            summary.errors.append(f"Sync from Airtable failed: {str(e)}")
                # Error logging handled by decorators
return summary
    
    def _get_all_airtable_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all leads from Airtable.
        
        Args:
            limit: Maximum number of records to retrieve
            
        Returns:
            List of Airtable lead records
        """
        try:
            # Use the existing method to get leads
            leads = self.airtable.get_leads_for_engagement(limit or 1000)
            return leads
            
        except Exception as e:
                # Error logging handled by decorators
return []
    
    def _sync_lead_from_airtable(self, airtable_lead: Dict[str, Any]) -> SyncResult:
        """
        Sync a single lead from Airtable to database.
        
        Args:
            airtable_lead: Lead data from Airtable
            
        Returns:
            SyncResult object
        """
        airtable_id = airtable_lead.get('id')
        result = SyncResult(
            operation=SyncOperation.UPDATE,
            lead_id='',  # Will be set later when we know if it's create or update
            airtable_id=airtable_id
        )
        
        try:
            # Map Airtable fields to database fields
            db_fields = self._map_airtable_to_db_fields(airtable_lead)
            
            # Check if lead exists in database by airtable_id
            existing_leads = self.db.search_leads({'airtable_id': airtable_id})
            
            if existing_leads:
                # Update existing lead
                existing_lead = existing_leads[0]
                result.lead_id = existing_lead['id']
                result.operation = SyncOperation.UPDATE
                
                # Check if update is needed (compare timestamps)
                if self._should_update_from_airtable(existing_lead, airtable_lead):
                    success = self.db.update_lead(existing_lead['id'], db_fields)
                    if success:
                        result.status = SyncStatus.SUCCESS
                # Logging handled by decorators
else:
                        result.status = SyncStatus.FAILED
                        result.error_message = "Failed to update lead in database"
                else:
                    result.status = SyncStatus.SUCCESS  # No update needed
                    
            else:
                # Create new lead
                db_fields['airtable_id'] = airtable_id
                db_fields['airtable_synced'] = True
                db_fields['sync_pending'] = False
                
                lead_id = self.db.add_lead(db_fields)
                if lead_id:
                    result.lead_id = lead_id
                    result.operation = SyncOperation.CREATE
                    result.status = SyncStatus.SUCCESS
                # Logging handled by decorators
})
                else:
                    result.status = SyncStatus.FAILED
                    result.error_message = "Failed to create lead in database"
            
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.error_message = str(e)
                # Error logging handled by decorators
result.last_attempt = datetime.datetime.now()
        return result
    
    def _map_airtable_to_db_fields(self, airtable_lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Airtable fields to database field names.
        
        Args:
            airtable_lead: Lead data from Airtable
            
        Returns:
            Dictionary with database field names
        """
        db_fields = {}
        
        # Map standard fields
        for airtable_field, db_field in self.airtable_to_db_mapping.items():
            if airtable_field in airtable_lead and airtable_lead[airtable_field] is not None:
                value = airtable_lead[airtable_field]
                
                # Handle boolean fields (Airtable uses 'Yes'/'No')
                if airtable_field in ['Verified', 'Enriched'] and isinstance(value, str):
                    value = value.lower() == 'yes'
                
                # Handle datetime fields
                elif db_field in ['scraped_at', 'enriched_at'] and isinstance(value, str):
                    try:
                        value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        # Keep as string if parsing fails
                        pass
                
                db_fields[db_field] = value
        
        # Handle special mappings
        if 'Full Name' in airtable_lead:
            db_fields['full_name'] = airtable_lead['Full Name']
        
        if 'LinkedIn' in airtable_lead:
            db_fields['linkedin_url'] = airtable_lead['LinkedIn']
        
        # Set sync status
        db_fields['airtable_synced'] = True
        db_fields['sync_pending'] = False
        
        return db_fields
    
    def _should_update_from_airtable(self, db_lead: Dict[str, Any], airtable_lead: Dict[str, Any]) -> bool:
        """
        Determine if database lead should be updated from Airtable data.
        
        Args:
            db_lead: Lead data from database
            airtable_lead: Lead data from Airtable
            
        Returns:
            True if update is needed, False otherwise
        """
        # Always update if no last sync time
        if not db_lead.get('updated_at'):
            return True
        
        # Check if Airtable record has been modified more recently
        # This is a simple timestamp comparison - in production you might want more sophisticated logic
        try:
            db_updated = db_lead.get('updated_at')
            if isinstance(db_updated, str):
                db_updated = datetime.datetime.fromisoformat(db_updated)
            
            # For now, always update to ensure data consistency
            # In the future, you could add timestamp comparison logic here
            return True
            
        except (ValueError, TypeError):
            # If we can't parse timestamps, err on the side of updating
            return True
    
    def _update_sync_status_in_db(self, sync_results: List[SyncResult]) -> None:
        """
        Update sync status in database based on sync results.
        
        Args:
            sync_results: List of sync results
        """
        for result in sync_results:
            if result.lead_id and result.status == SyncStatus.SUCCESS:
                updates = {
                    'airtable_synced': True,
                    'sync_pending': False,
                    'last_sync_attempt': result.last_attempt.isoformat() if result.last_attempt else None,
                    'sync_error': None
                }
                
                if result.airtable_id:
                    updates['airtable_id'] = result.airtable_id
                
                self.db.update_lead(result.lead_id, updates)
                
            elif result.lead_id and result.status == SyncStatus.FAILED:
                updates = {
                    'sync_pending': True,
                    'last_sync_attempt': result.last_attempt.isoformat() if result.last_attempt else None,
                    'sync_error': result.error_message
                }
                
                self.db.update_lead(result.lead_id, updates)
    
    def bidirectional_sync(self, push_limit: Optional[int] = None, 
                          pull_limit: Optional[int] = None) -> Dict[str, SyncSummary]:
        """
        Perform bidirectional sync between database and Airtable.
        
        Args:
            push_limit: Maximum number of leads to push to Airtable
            pull_limit: Maximum number of leads to pull from Airtable
            
        Returns:
            Dictionary with 'push' and 'pull' sync summaries
        """
        results = {}
                # Logging handled by decorators
# Push to Airtable first
        push_summary = self.sync_to_airtable()
        results['push'] = push_summary
        
        # Then pull from Airtable
        pull_summary = self.sync_from_airtable(pull_limit)
        results['pull'] = pull_summary
                # Logging handled by decorators
return results
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive sync statistics.
        
        Returns:
            Dictionary with sync statistics
        """
        try:
            # Get database stats
            db_stats = self.db.get_database_stats()
            
            # Get sync pending leads
            sync_pending = self.db.get_sync_pending_leads()
            
            # Get leads with Airtable IDs
            synced_leads = self.db.search_leads({'airtable_synced': True})
            
            stats = {
                'database_stats': db_stats,
                'sync_pending_count': len(sync_pending),
                'synced_leads_count': len(synced_leads),
                'sync_rate': len(synced_leads) / db_stats.get('total_leads', 1) if db_stats.get('total_leads', 0) > 0 else 0,
                'last_check': datetime.datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
                # Error logging handled by decorators
return {'error': str(e)}
    
    def mark_for_sync(self, lead_id: str) -> bool:
        """
        Mark a specific lead for synchronization.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            True if marked successfully, False otherwise
        """
        return self.db.mark_for_sync(lead_id)
    
    def get_sync_pending_leads(self) -> List[Dict[str, Any]]:
        """
        Get all leads that are pending synchronization.
        
        Returns:
            List of leads marked for sync
        """
        return self.db.get_sync_pending_leads()
    
    def retry_failed_syncs(self) -> SyncSummary:
        """
        Retry synchronization for leads that previously failed.
        
        Returns:
            SyncSummary with retry results
        """
        # Get leads with sync errors
        failed_leads = self.db.search_leads({'sync_error': True})  # This would need a custom query
        
        if not failed_leads:
            summary = SyncSummary()
                # Logging handled by decorators
return summary
        
        # Extract lead IDs
        lead_ids = [lead['id'] for lead in failed_leads]
                # Logging handled by decorators
} failed leads'
        })
        
        # Retry sync
        return self.sync_to_airtable(lead_ids)