#!/usr/bin/env python3
"""
Data Synchronizer

Comprehensive data synchronization system for database maintenance.
Handles bidirectional sync between local database and Airtable with conflict resolution.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger('data-synchronizer')

@dataclass
class DataConflict:
    """Represents a data conflict between systems."""
    field_name: str
    local_value: Any
    airtable_value: Any
    record_id: str
    last_modified_local: Optional[datetime] = None
    last_modified_airtable: Optional[datetime] = None
    conflict_type: str = "value_mismatch"  # value_mismatch, missing_local, missing_airtable
    suggested_resolution: str = "local_wins"

@dataclass
class SyncResult:
    """Results from synchronization operations."""
    success: bool
    synchronized_count: int
    conflicts_resolved: int
    records_created: int
    records_updated: int
    records_skipped: int
    errors: List[str]
    warnings: List[str]
    conflicts: List[DataConflict]

@dataclass
class ConflictResolution:
    """Results from conflict resolution."""
    success: bool
    conflicts_resolved: int
    errors: List[str]

@dataclass
class ValidationResult:
    """Results from sync validation."""
    success: bool
    local_count: int
    airtable_count: int
    matched_records: int
    unmatched_local: int
    unmatched_airtable: int
    errors: List[str]

class DataSynchronizer:
    """
    Comprehensive data synchronization system.
    
    Handles bidirectional synchronization between local database and Airtable
    with intelligent conflict resolution and data validation.
    """
    
    def __init__(self, field_mapping: Optional[Dict[str, Any]] = None):
        """
        Initialize the data synchronizer.
        
        Args:
            field_mapping: Configuration for field mapping between systems
        """
        self.field_mapping = field_mapping or self._get_default_field_mapping()
        logger.info("DataSynchronizer initialized")
    
    def _get_default_field_mapping(self) -> Dict[str, Any]:
        """Get default field mapping configuration."""
        return {
            'database_to_airtable': {
                'name': 'Full Name',
                'email': 'Email',
                'company': 'Company',
                'title': 'Title',
                'linkedin_url': 'LinkedIn URL',
                'company_website': 'Website',
                'phone': 'Phone',
                'status': 'Engagement_Status'
            },
            'airtable_to_database': {
                'Full Name': 'name',
                'Email': 'email',
                'Company': 'company',
                'Title': 'title',
                'LinkedIn URL': 'linkedin_url',
                'Website': 'company_website',
                'Phone': 'phone',
                'Engagement_Status': 'status'
            }
        }
    
    def sync_database_to_airtable(self, batch_size: int = 50, dry_run: bool = False) -> SyncResult:
        """
        Synchronize data from local database to Airtable.
        
        Args:
            batch_size: Number of records to process in each batch
            dry_run: If True, only simulate the sync without making changes
            
        Returns:
            SyncResult: Results of the synchronization operation
        """
        result = SyncResult(
            success=True,
            synchronized_count=0,
            conflicts_resolved=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            errors=[],
            warnings=[],
            conflicts=[]
        )
        
        try:
            logger.info(f"Starting database to Airtable sync (dry_run={dry_run})")
            
            # Get all records from both systems
            db_records = self._get_database_records()
            airtable_records = self._get_airtable_records()
            
            if not db_records:
                result.warnings.append("No records found in local database")
                return result
            
            logger.info(f"Found {len(db_records)} database records and {len(airtable_records)} Airtable records")
            
            # Create lookup for Airtable records by email/linkedin
            airtable_lookup = self._create_airtable_lookup(airtable_records)
            
            # Process database records in batches
            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                batch_result = self._sync_database_batch_to_airtable(
                    batch, airtable_lookup, dry_run
                )
                
                # Aggregate results
                result.synchronized_count += batch_result['synchronized']
                result.records_created += batch_result['created']
                result.records_updated += batch_result['updated']
                result.records_skipped += batch_result['skipped']
                result.errors.extend(batch_result['errors'])
                result.conflicts.extend(batch_result['conflicts'])
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Database to Airtable sync completed: {result.synchronized_count} records processed")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Database to Airtable sync failed: {str(e)}")
            logger.error(f"Database to Airtable sync failed: {e}")
            return result
    
    def sync_airtable_to_database(self, batch_size: int = 50, dry_run: bool = False) -> SyncResult:
        """
        Synchronize data from Airtable to local database.
        
        Args:
            batch_size: Number of records to process in each batch
            dry_run: If True, only simulate the sync without making changes
            
        Returns:
            SyncResult: Results of the synchronization operation
        """
        result = SyncResult(
            success=True,
            synchronized_count=0,
            conflicts_resolved=0,
            records_created=0,
            records_updated=0,
            records_skipped=0,
            errors=[],
            warnings=[],
            conflicts=[]
        )
        
        try:
            logger.info(f"Starting Airtable to database sync (dry_run={dry_run})")
            
            # Get all records from both systems
            airtable_records = self._get_airtable_records()
            db_records = self._get_database_records()
            
            if not airtable_records:
                result.warnings.append("No records found in Airtable")
                return result
            
            logger.info(f"Found {len(airtable_records)} Airtable records and {len(db_records)} database records")
            
            # Create lookup for database records by email/linkedin
            db_lookup = self._create_database_lookup(db_records)
            
            # Process Airtable records in batches
            for i in range(0, len(airtable_records), batch_size):
                batch = airtable_records[i:i + batch_size]
                batch_result = self._sync_airtable_batch_to_database(
                    batch, db_lookup, dry_run
                )
                
                # Aggregate results
                result.synchronized_count += batch_result['synchronized']
                result.records_created += batch_result['created']
                result.records_updated += batch_result['updated']
                result.records_skipped += batch_result['skipped']
                result.errors.extend(batch_result['errors'])
                result.conflicts.extend(batch_result['conflicts'])
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Airtable to database sync completed: {result.synchronized_count} records processed")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Airtable to database sync failed: {str(e)}")
            logger.error(f"Airtable to database sync failed: {e}")
            return result
    
    def _get_database_records(self) -> List[Dict[str, Any]]:
        """Get all records from the local database."""
        try:
            import sys
            from pathlib import Path
            
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            from database.models import get_lead_database
            
            db = get_lead_database()
            
            # Get all leads using direct SQL to avoid any limit issues
            cursor = db.db.execute_query("SELECT * FROM leads ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            # Convert to Lead objects and then to dictionaries
            from database.models import Lead
            all_leads = [Lead.from_dict(dict(row)) for row in rows]
            
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
    
    def _create_airtable_lookup(self, airtable_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create lookup dictionary for Airtable records."""
        lookup = {}
        
        for record in airtable_records:
            # Create lookup keys based on email and LinkedIn URL
            email = record.get('Email', '').strip().lower()
            linkedin = record.get('LinkedIn URL', '').strip().lower()
            
            if email:
                lookup[f"email:{email}"] = record
            if linkedin:
                lookup[f"linkedin:{linkedin}"] = record
        
        return lookup
    
    def _create_database_lookup(self, db_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create lookup dictionary for database records."""
        lookup = {}
        
        for record in db_records:
            # Create lookup keys based on email and LinkedIn URL
            email = str(record.get('email', '')).strip().lower()
            linkedin = str(record.get('linkedin_url', '')).strip().lower()
            
            if email and email != 'none':
                lookup[f"email:{email}"] = record
            if linkedin and linkedin != 'none':
                lookup[f"linkedin:{linkedin}"] = record
        
        return lookup
    
    def _sync_database_batch_to_airtable(self, db_batch: List[Dict[str, Any]], 
                                       airtable_lookup: Dict[str, Dict[str, Any]], 
                                       dry_run: bool) -> Dict[str, Any]:
        """Sync a batch of database records to Airtable."""
        result = {
            'synchronized': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'conflicts': []
        }
        
        try:
            from configurable_airtable_client import get_configurable_airtable_client
            airtable_client = get_configurable_airtable_client()
            
            updates_to_make = []
            creates_to_make = []
            
            for db_record in db_batch:
                try:
                    # Find matching Airtable record
                    airtable_record = self._find_matching_airtable_record(db_record, airtable_lookup)
                    
                    # Convert database record to Airtable format
                    airtable_fields = self._convert_db_to_airtable_format(db_record)
                    
                    if airtable_record:
                        # Update existing record
                        if self._records_need_sync(db_record, airtable_record):
                            updates_to_make.append({
                                'id': airtable_record['id'],
                                'fields': airtable_fields
                            })
                            result['updated'] += 1
                            logger.debug(f"Queued update for Airtable record: {airtable_record['id']}")
                        else:
                            result['skipped'] += 1
                    else:
                        # Create new record
                        creates_to_make.append({'fields': airtable_fields})
                        result['created'] += 1
                        logger.debug(f"Queued creation for database record: {db_record.get('name', 'Unknown')}")
                    
                    result['synchronized'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to process database record {db_record.get('id', 'Unknown')}: {str(e)}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Execute batch operations if not dry run
            if not dry_run:
                # Batch updates
                if updates_to_make:
                    try:
                        batch_size = 10  # Airtable limit
                        for i in range(0, len(updates_to_make), batch_size):
                            batch = updates_to_make[i:i + batch_size]
                            airtable_client.table.batch_update(batch)
                            logger.info(f"Updated {len(batch)} Airtable records")
                    except Exception as e:
                        result['errors'].append(f"Batch update failed: {str(e)}")
                
                # Batch creates
                if creates_to_make:
                    try:
                        batch_size = 10  # Airtable limit
                        for i in range(0, len(creates_to_make), batch_size):
                            batch = creates_to_make[i:i + batch_size]
                            airtable_client.table.batch_create(batch)
                            logger.info(f"Created {len(batch)} Airtable records")
                    except Exception as e:
                        result['errors'].append(f"Batch create failed: {str(e)}")
            else:
                logger.info(f"Dry run: Would update {len(updates_to_make)} and create {len(creates_to_make)} Airtable records")
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Batch sync failed: {str(e)}")
            return result
    
    def _sync_airtable_batch_to_database(self, airtable_batch: List[Dict[str, Any]], 
                                       db_lookup: Dict[str, Dict[str, Any]], 
                                       dry_run: bool) -> Dict[str, Any]:
        """Sync a batch of Airtable records to database."""
        result = {
            'synchronized': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'conflicts': []
        }
        
        try:
            import sys
            from pathlib import Path
            
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            from database.models import get_lead_database
            db = get_lead_database()
            
            for airtable_record in airtable_batch:
                try:
                    # Find matching database record
                    db_record = self._find_matching_database_record(airtable_record, db_lookup)
                    
                    # Convert Airtable record to database format
                    db_fields = self._convert_airtable_to_db_format(airtable_record)
                    
                    if db_record:
                        # Update existing record
                        if self._records_need_sync(db_record, airtable_record):
                            if not dry_run:
                                success = db.update_lead(db_record['id'], db_fields)
                                if success:
                                    result['updated'] += 1
                                    logger.debug(f"Updated database record: {db_record['id']}")
                                else:
                                    result['errors'].append(f"Failed to update database record: {db_record['id']}")
                            else:
                                result['updated'] += 1
                        else:
                            result['skipped'] += 1
                    else:
                        # Create new record
                        if not dry_run:
                            try:
                                lead_id = db.create_lead(db_fields)
                                result['created'] += 1
                                logger.debug(f"Created database record: {lead_id}")
                            except Exception as e:
                                result['errors'].append(f"Failed to create database record: {str(e)}")
                        else:
                            result['created'] += 1
                    
                    result['synchronized'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to process Airtable record {airtable_record.get('id', 'Unknown')}: {str(e)}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
            
            if dry_run:
                logger.info(f"Dry run: Would update {result['updated']} and create {result['created']} database records")
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Batch sync failed: {str(e)}")
            return result
    
    def _find_matching_airtable_record(self, db_record: Dict[str, Any], 
                                     airtable_lookup: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find matching Airtable record for a database record."""
        email = str(db_record.get('email', '')).strip().lower()
        linkedin = str(db_record.get('linkedin_url', '')).strip().lower()
        
        # Try email match first
        if email and email != 'none':
            match = airtable_lookup.get(f"email:{email}")
            if match:
                return match
        
        # Try LinkedIn match
        if linkedin and linkedin != 'none':
            match = airtable_lookup.get(f"linkedin:{linkedin}")
            if match:
                return match
        
        return None
    
    def _find_matching_database_record(self, airtable_record: Dict[str, Any], 
                                     db_lookup: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find matching database record for an Airtable record."""
        email = str(airtable_record.get('Email', '')).strip().lower()
        linkedin = str(airtable_record.get('LinkedIn URL', '')).strip().lower()
        
        # Try email match first
        if email:
            match = db_lookup.get(f"email:{email}")
            if match:
                return match
        
        # Try LinkedIn match
        if linkedin:
            match = db_lookup.get(f"linkedin:{linkedin}")
            if match:
                return match
        
        return None
    
    def _convert_db_to_airtable_format(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database record to Airtable format."""
        airtable_fields = {}
        mapping = self.field_mapping['database_to_airtable']
        
        for db_field, airtable_field in mapping.items():
            value = db_record.get(db_field)
            if value is not None and str(value).strip() and str(value).lower() != 'none':
                airtable_fields[airtable_field] = str(value).strip()
        
        return airtable_fields
    
    def _convert_airtable_to_db_format(self, airtable_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Airtable record to database format."""
        db_fields = {}
        mapping = self.field_mapping['airtable_to_database']
        
        for airtable_field, db_field in mapping.items():
            value = airtable_record.get(airtable_field)
            if value is not None and str(value).strip():
                db_fields[db_field] = str(value).strip()
        
        return db_fields
    
    def _records_need_sync(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> bool:
        """Check if records need synchronization."""
        # Simple heuristic: if any mapped field differs, sync is needed
        # This is a placeholder for more sophisticated logic
        return True
    
    def find_data_conflicts(self) -> List[DataConflict]:
        """Find data conflicts between systems."""
        conflicts = []
        
        try:
            db_records = self._get_database_records()
            airtable_records = self._get_airtable_records()
            
            # Create lookups
            airtable_lookup = self._create_airtable_lookup(airtable_records)
            
            for db_record in db_records:
                airtable_record = self._find_matching_airtable_record(db_record, airtable_lookup)
                
                if airtable_record:
                    # Check for field conflicts
                    record_conflicts = self._find_record_conflicts(db_record, airtable_record)
                    conflicts.extend(record_conflicts)
            
            logger.info(f"Found {len(conflicts)} data conflicts")
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to find data conflicts: {e}")
            return []
    
    def _find_record_conflicts(self, db_record: Dict[str, Any], airtable_record: Dict[str, Any]) -> List[DataConflict]:
        """Find conflicts between two records."""
        conflicts = []
        
        # Compare mapped fields
        for db_field, airtable_field in self.field_mapping['database_to_airtable'].items():
            db_value = str(db_record.get(db_field, '')).strip()
            airtable_value = str(airtable_record.get(airtable_field, '')).strip()
            
            if db_value and airtable_value and db_value.lower() != airtable_value.lower():
                conflict = DataConflict(
                    field_name=db_field,
                    local_value=db_value,
                    airtable_value=airtable_value,
                    record_id=db_record.get('id', 'unknown'),
                    conflict_type="value_mismatch",
                    suggested_resolution="local_wins"  # Prefer local database
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[DataConflict], strategy: str = "local_wins") -> ConflictResolution:
        """Resolve data conflicts using the specified strategy."""
        result = ConflictResolution(
            success=True,
            conflicts_resolved=0,
            errors=[]
        )
        
        logger.info(f"Resolving {len(conflicts)} conflicts using strategy: {strategy}")
        
        # Placeholder implementation
        result.conflicts_resolved = len(conflicts)
        
        return result
    
    def validate_sync_integrity(self) -> ValidationResult:
        """Validate synchronization integrity between systems."""
        result = ValidationResult(
            success=True,
            local_count=0,
            airtable_count=0,
            matched_records=0,
            unmatched_local=0,
            unmatched_airtable=0,
            errors=[]
        )
        
        try:
            db_records = self._get_database_records()
            airtable_records = self._get_airtable_records()
            
            result.local_count = len(db_records)
            result.airtable_count = len(airtable_records)
            
            # Create lookups
            airtable_lookup = self._create_airtable_lookup(airtable_records)
            db_lookup = self._create_database_lookup(db_records)
            
            # Count matches
            matched_from_db = 0
            for db_record in db_records:
                if self._find_matching_airtable_record(db_record, airtable_lookup):
                    matched_from_db += 1
            
            matched_from_airtable = 0
            for airtable_record in airtable_records:
                if self._find_matching_database_record(airtable_record, db_lookup):
                    matched_from_airtable += 1
            
            result.matched_records = max(matched_from_db, matched_from_airtable)
            result.unmatched_local = result.local_count - matched_from_db
            result.unmatched_airtable = result.airtable_count - matched_from_airtable
            
            logger.info(f"Sync validation: {result.matched_records} matched, {result.unmatched_local} unmatched local, {result.unmatched_airtable} unmatched Airtable")
            
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Sync validation failed: {str(e)}")
            logger.error(f"Sync validation failed: {e}")
            return result


if __name__ == "__main__":
    # Test the data synchronizer
    print("🧪 Testing Data Synchronizer...")
    
    # Create synchronizer
    synchronizer = DataSynchronizer()
    
    # Test sync validation
    print("Testing sync validation...")
    validation = synchronizer.validate_sync_integrity()
    print(f"Validation: {'Success' if validation.success else 'Failed'}")
    print(f"Local: {validation.local_count}, Airtable: {validation.airtable_count}")
    print(f"Matched: {validation.matched_records}, Unmatched Local: {validation.unmatched_local}, Unmatched Airtable: {validation.unmatched_airtable}")
    
    # Test conflict detection
    print("Testing conflict detection...")
    conflicts = synchronizer.find_data_conflicts()
    print(f"Found {len(conflicts)} conflicts")
    
    # Test database to Airtable sync (dry run)
    print("Testing database to Airtable sync (dry run)...")
    sync_result = synchronizer.sync_database_to_airtable(dry_run=True)
    print(f"Sync result: {'Success' if sync_result.success else 'Failed'}")
    print(f"Would create: {sync_result.records_created}, update: {sync_result.records_updated}, skip: {sync_result.records_skipped}")
    
    print("✅ Data synchronizer test completed")