#!/usr/bin/env python3
"""
Database Maintenance System

Comprehensive cleanup and synchronization tool for database and Airtable maintenance.
Provides duplicate removal, field standardization, data synchronization, and backup capabilities.
"""

import os
import uuid
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logger = logging.getLogger('database-maintenance')

@dataclass
class MaintenanceOptions:
    """Configuration options for maintenance operations."""
    backup_before_operation: bool = True
    remove_duplicates: bool = True
    standardize_fields: bool = True
    sync_data: bool = True
    engagement_status_default: str = "auto_send"
    duplicate_matching_fields: List[str] = field(default_factory=lambda: ["email", "linkedin_url"])
    conflict_resolution_strategy: str = "most_recent"  # most_recent, highest_quality, manual
    batch_size: int = 50
    dry_run: bool = False
    max_memory_usage_mb: int = 512
    progress_update_interval: int = 100

@dataclass
class MaintenanceResult:
    """Results from maintenance operations."""
    success: bool
    operation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    backup_paths: List[str] = field(default_factory=list)
    duplicates_removed: int = 0
    records_standardized: int = 0
    records_synchronized: int = 0
    conflicts_resolved: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detailed_results: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate operation duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

@dataclass
class OperationStatus:
    """Current status of maintenance operations."""
    operation_id: str
    current_phase: str
    progress_percentage: float
    records_processed: int
    total_records: int
    estimated_time_remaining: Optional[float] = None
    last_update: datetime = field(default_factory=datetime.now)

class MaintenanceOrchestrator:
    """
    Main orchestrator for database maintenance operations.
    
    Coordinates backup, cleanup, synchronization, and standardization operations
    across both local database and Airtable systems.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the maintenance orchestrator.
        
        Args:
            config_path: Path to configuration file. If None, uses default config.
        """
        self.operation_id = str(uuid.uuid4())
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_configuration()
        self.status = OperationStatus(
            operation_id=self.operation_id,
            current_phase="initialized",
            progress_percentage=0.0,
            records_processed=0,
            total_records=0
        )
        
        logger.info(f"MaintenanceOrchestrator initialized with operation ID: {self.operation_id}")
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        return str(Path(__file__).parent / "config" / "maintenance_config.yaml")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load maintenance configuration from YAML file.
        
        Returns:
            Dict containing configuration settings
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from: {self.config_path}")
                return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return self._get_default_configuration()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_configuration()
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            'maintenance_config': {
                'backup': {
                    'enabled': True,
                    'retention_days': 30,
                    'backup_directory': "./backups",
                    'verify_integrity': True
                },
                'duplicate_detection': {
                    'matching_fields': ["email", "linkedin_url", "company"],
                    'matching_threshold': 0.85,
                    'resolution_strategy': "most_recent"
                },
                'field_standardization': {
                    'engagement_status': {
                        'default_value': "auto_send",
                        'valid_values': ["auto_send", "manual_review", "contacted", "responded"]
                    },
                    'company_name': {
                        'normalize_case': True,
                        'remove_suffixes': ["Inc.", "LLC", "Corp.", "Ltd."],
                        'add_proper_suffix': True
                    },
                    'website_url': {
                        'ensure_protocol': True,
                        'preferred_protocol': "https",
                        'remove_trailing_slash': True
                    },
                    'email': {
                        'normalize_case': "lower",
                        'validate_format': True
                    }
                },
                'synchronization': {
                    'conflict_resolution': "most_recent",
                    'batch_size': 50,
                    'max_retries': 3,
                    'retry_delay_seconds': 2
                },
                'performance': {
                    'max_memory_usage_mb': 512,
                    'progress_update_interval': 100,
                    'enable_parallel_processing': False
                }
            }
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate the loaded configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check required sections
            required_sections = ['maintenance_config']
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate maintenance config structure
            maintenance_config = self.config['maintenance_config']
            required_subsections = ['backup', 'duplicate_detection', 'field_standardization', 'synchronization']
            
            for subsection in required_subsections:
                if subsection not in maintenance_config:
                    logger.error(f"Missing required configuration subsection: {subsection}")
                    return False
            
            # Validate specific settings
            backup_config = maintenance_config['backup']
            if not isinstance(backup_config.get('retention_days'), int) or backup_config['retention_days'] < 1:
                logger.error("Invalid backup retention_days configuration")
                return False
            
            sync_config = maintenance_config['synchronization']
            if not isinstance(sync_config.get('batch_size'), int) or sync_config['batch_size'] < 1:
                logger.error("Invalid synchronization batch_size configuration")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def run_full_maintenance(self, options: MaintenanceOptions) -> MaintenanceResult:
        """
        Run complete maintenance workflow.
        
        Args:
            options: Maintenance operation options
            
        Returns:
            MaintenanceResult: Results of the maintenance operation
        """
        result = MaintenanceResult(
            success=False,
            operation_id=self.operation_id,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Starting full maintenance operation: {self.operation_id}")
            
            # Validate configuration
            if not self.validate_configuration():
                result.errors.append("Configuration validation failed")
                return result
            
            # Update status
            self._update_status("validation_complete", 5.0)
            
            # Phase 1: Create backups if enabled
            if options.backup_before_operation:
                self._update_status("creating_backups", 10.0)
                backup_result = self._create_backups()
                if not backup_result['success']:
                    result.errors.extend(backup_result['errors'])
                    return result
                result.backup_paths = backup_result['backup_paths']
            
            # Phase 2: Remove duplicates if enabled
            if options.remove_duplicates:
                self._update_status("removing_duplicates", 30.0)
                duplicate_result = self._remove_duplicates(options)
                result.duplicates_removed = duplicate_result.get('removed_count', 0)
                if duplicate_result.get('errors'):
                    result.errors.extend(duplicate_result['errors'])
            
            # Phase 3: Standardize fields if enabled
            if options.standardize_fields:
                self._update_status("standardizing_fields", 60.0)
                standardization_result = self._standardize_fields(options)
                result.records_standardized = standardization_result.get('standardized_count', 0)
                if standardization_result.get('errors'):
                    result.errors.extend(standardization_result['errors'])
            
            # Phase 4: Synchronize data if enabled
            if options.sync_data:
                self._update_status("synchronizing_data", 80.0)
                sync_result = self._synchronize_data(options)
                result.records_synchronized = sync_result.get('synchronized_count', 0)
                result.conflicts_resolved = sync_result.get('conflicts_resolved', 0)
                if sync_result.get('errors'):
                    result.errors.extend(sync_result['errors'])
            
            # Phase 5: Final validation and cleanup
            self._update_status("finalizing", 95.0)
            validation_result = self._validate_final_state()
            if validation_result.get('errors'):
                result.errors.extend(validation_result['errors'])
            
            # Complete operation
            result.end_time = datetime.now()
            result.success = len(result.errors) == 0
            self._update_status("completed", 100.0)
            
            logger.info(f"Maintenance operation completed: {self.operation_id}")
            logger.info(f"Duration: {result.duration_seconds:.2f} seconds")
            logger.info(f"Duplicates removed: {result.duplicates_removed}")
            logger.info(f"Records standardized: {result.records_standardized}")
            logger.info(f"Records synchronized: {result.records_synchronized}")
            
            return result
            
        except Exception as e:
            result.end_time = datetime.now()
            result.errors.append(f"Unexpected error during maintenance: {str(e)}")
            logger.error(f"Maintenance operation failed: {e}")
            return result
    
    def _update_status(self, phase: str, progress: float, records_processed: int = 0, total_records: int = 0):
        """Update the current operation status."""
        self.status.current_phase = phase
        self.status.progress_percentage = progress
        self.status.records_processed = records_processed
        self.status.total_records = total_records
        self.status.last_update = datetime.now()
        
        logger.info(f"Status update: {phase} ({progress:.1f}%)")
    
    def _create_backups(self) -> Dict[str, Any]:
        """Create backups before maintenance operations."""
        try:
            from backup_manager import BackupManager
            
            # Get backup configuration
            backup_config = self.config['maintenance_config']['backup']
            backup_manager = BackupManager(
                backup_directory=backup_config.get('backup_directory', './backups'),
                retention_days=backup_config.get('retention_days', 30)
            )
            
            # Create full backup
            result = backup_manager.create_full_backup()
            
            logger.info(f"Backup operation completed: {'Success' if result['success'] else 'Failed'}")
            return result
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                'success': False,
                'backup_paths': [],
                'errors': [f"Backup creation failed: {str(e)}"]
            }
    
    def _remove_duplicates(self, options: MaintenanceOptions) -> Dict[str, Any]:
        """Remove duplicate records."""
        try:
            from duplicate_detector import DuplicateDetector
            
            # Get duplicate detection configuration
            duplicate_config = self.config['maintenance_config']['duplicate_detection']
            
            # Create duplicate detector
            detector = DuplicateDetector(
                matching_threshold=duplicate_config.get('matching_threshold', 0.85)
            )
            
            # Find duplicates in both systems
            matching_fields = options.duplicate_matching_fields
            
            logger.info(f"Finding duplicates using fields: {matching_fields}")
            
            # Find database duplicates
            db_duplicates = detector.find_database_duplicates(matching_fields)
            logger.info(f"Found {len(db_duplicates)} duplicate groups in database")
            
            # Find Airtable duplicates
            airtable_duplicates = detector.find_airtable_duplicates(matching_fields)
            logger.info(f"Found {len(airtable_duplicates)} duplicate groups in Airtable")
            
            # Find cross-system duplicates
            cross_duplicates = detector.find_cross_system_duplicates()
            logger.info(f"Found {len(cross_duplicates)} cross-system duplicates")
            
            total_removed = 0
            errors = []
            
            # Resolve duplicates if not in dry run mode
            if not options.dry_run:
                # Resolve database duplicates
                if db_duplicates:
                    db_resolution = detector.resolve_duplicates(
                        db_duplicates, 
                        options.conflict_resolution_strategy
                    )
                    total_removed += db_resolution.records_deleted
                    errors.extend(db_resolution.errors)
                
                # Resolve Airtable duplicates
                if airtable_duplicates:
                    airtable_resolution = detector.resolve_duplicates(
                        airtable_duplicates, 
                        options.conflict_resolution_strategy
                    )
                    total_removed += airtable_resolution.records_deleted
                    errors.extend(airtable_resolution.errors)
            else:
                logger.info("Dry run mode: duplicates identified but not removed")
                # Count potential removals
                total_removed = sum(len(group.records) - 1 for group in db_duplicates + airtable_duplicates)
            
            logger.info(f"Duplicate removal completed: {total_removed} records processed")
            
            return {
                'removed_count': total_removed,
                'database_duplicates': len(db_duplicates),
                'airtable_duplicates': len(airtable_duplicates),
                'cross_system_duplicates': len(cross_duplicates),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Duplicate removal failed: {e}")
            return {
                'removed_count': 0,
                'errors': [f"Duplicate removal failed: {str(e)}"]
            }
    
    def _standardize_fields(self, options: MaintenanceOptions) -> Dict[str, Any]:
        """Standardize field values."""
        try:
            from field_standardizer import FieldStandardizer
            
            # Get field standardization configuration
            field_config = self.config['maintenance_config']['field_standardization']
            
            # Create field standardizer
            standardizer = FieldStandardizer(field_config)
            
            total_standardized = 0
            errors = []
            
            logger.info("Starting field standardization...")
            
            # Standardize engagement status
            engagement_result = standardizer.standardize_engagement_status(options.engagement_status_default)
            total_standardized += engagement_result.records_updated
            errors.extend(engagement_result.errors)
            
            if engagement_result.success:
                logger.info(f"Engagement status standardized: {engagement_result.records_updated} records")
            else:
                logger.error(f"Engagement status standardization failed: {engagement_result.errors}")
            
            # Standardize company names
            company_result = standardizer.standardize_company_names()
            total_standardized += company_result.records_updated
            errors.extend(company_result.errors)
            
            # Standardize website URLs
            website_result = standardizer.standardize_website_urls()
            total_standardized += website_result.records_updated
            errors.extend(website_result.errors)
            
            # Standardize email formats
            email_result = standardizer.standardize_email_formats()
            total_standardized += email_result.records_updated
            errors.extend(email_result.errors)
            
            logger.info(f"Field standardization completed: {total_standardized} total records updated")
            
            return {
                'standardized_count': total_standardized,
                'engagement_status_updates': engagement_result.records_updated,
                'company_name_updates': company_result.records_updated,
                'website_url_updates': website_result.records_updated,
                'email_format_updates': email_result.records_updated,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Field standardization failed: {e}")
            return {
                'standardized_count': 0,
                'errors': [f"Field standardization failed: {str(e)}"]
            }
    
    def _synchronize_data(self, options: MaintenanceOptions) -> Dict[str, Any]:
        """Synchronize data between systems."""
        try:
            from data_synchronizer import DataSynchronizer
            
            # Get field mapping from configuration
            field_mapping = self.config.get('field_mapping', {})
            
            # Create data synchronizer
            synchronizer = DataSynchronizer(field_mapping)
            
            logger.info("Starting data synchronization...")
            
            # First, validate current sync state
            validation = synchronizer.validate_sync_integrity()
            logger.info(f"Sync validation: Local={validation.local_count}, Airtable={validation.airtable_count}, Matched={validation.matched_records}")
            
            total_synchronized = 0
            conflicts_resolved = 0
            errors = []
            
            # Sync database to Airtable (local database is source of truth)
            db_to_airtable_result = synchronizer.sync_database_to_airtable(
                batch_size=options.batch_size,
                dry_run=options.dry_run
            )
            
            total_synchronized += db_to_airtable_result.synchronized_count
            conflicts_resolved += db_to_airtable_result.conflicts_resolved
            errors.extend(db_to_airtable_result.errors)
            
            if db_to_airtable_result.success:
                logger.info(f"Database to Airtable sync: {db_to_airtable_result.records_created} created, {db_to_airtable_result.records_updated} updated")
            else:
                logger.error(f"Database to Airtable sync failed: {db_to_airtable_result.errors}")
            
            # Find and resolve conflicts
            conflicts = synchronizer.find_data_conflicts()
            if conflicts:
                logger.info(f"Found {len(conflicts)} data conflicts")
                conflict_resolution = synchronizer.resolve_conflicts(
                    conflicts, 
                    options.conflict_resolution_strategy
                )
                conflicts_resolved += conflict_resolution.conflicts_resolved
                errors.extend(conflict_resolution.errors)
            
            # Final validation
            final_validation = synchronizer.validate_sync_integrity()
            
            logger.info(f"Data synchronization completed: {total_synchronized} records synchronized")
            
            return {
                'synchronized_count': total_synchronized,
                'conflicts_resolved': conflicts_resolved,
                'records_created': db_to_airtable_result.records_created,
                'records_updated': db_to_airtable_result.records_updated,
                'initial_state': {
                    'local_count': validation.local_count,
                    'airtable_count': validation.airtable_count,
                    'matched_records': validation.matched_records
                },
                'final_state': {
                    'local_count': final_validation.local_count,
                    'airtable_count': final_validation.airtable_count,
                    'matched_records': final_validation.matched_records
                },
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Data synchronization failed: {e}")
            return {
                'synchronized_count': 0,
                'conflicts_resolved': 0,
                'errors': [f"Data synchronization failed: {str(e)}"]
            }
    
    def _validate_final_state(self) -> Dict[str, Any]:
        """Validate the final state after maintenance operations."""
        # Placeholder for final validation functionality
        logger.info("Validating final state...")
        return {
            'errors': []
        }
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """
        Get current maintenance operation status.
        
        Returns:
            Dict containing current status information
        """
        return {
            'operation_id': self.status.operation_id,
            'current_phase': self.status.current_phase,
            'progress_percentage': self.status.progress_percentage,
            'records_processed': self.status.records_processed,
            'total_records': self.status.total_records,
            'estimated_time_remaining': self.status.estimated_time_remaining,
            'last_update': self.status.last_update.isoformat()
        }


if __name__ == "__main__":
    # Test the maintenance orchestrator
    print("🧪 Testing Database Maintenance System...")
    
    # Create orchestrator
    orchestrator = MaintenanceOrchestrator()
    
    # Test configuration validation
    if orchestrator.validate_configuration():
        print("✅ Configuration validation passed")
    else:
        print("❌ Configuration validation failed")
    
    # Test status tracking
    status = orchestrator.get_maintenance_status()
    print(f"Initial status: {status['current_phase']} ({status['progress_percentage']}%)")
    
    # Test dry run
    options = MaintenanceOptions(dry_run=True)
    result = orchestrator.run_full_maintenance(options)
    
    print(f"Maintenance result: {'Success' if result.success else 'Failed'}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")
    print(f"Errors: {len(result.errors)}")
    
    print("✅ Database maintenance system test completed")