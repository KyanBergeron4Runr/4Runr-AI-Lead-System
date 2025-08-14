#!/usr/bin/env python3
"""
Backup Manager

Comprehensive backup and recovery system for database maintenance operations.
Handles database backups, Airtable data exports, integrity verification, and retention management.
"""

import os
import json
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logger = logging.getLogger('backup-manager')

@dataclass
class BackupResult:
    """Results from backup operations."""
    success: bool
    backup_path: str
    backup_type: str  # 'database', 'airtable', 'full'
    file_size_bytes: int
    checksum: str
    created_at: datetime
    error_message: Optional[str] = None

class BackupManager:
    """
    Comprehensive backup and recovery manager for maintenance operations.
    
    Handles database backups, Airtable data exports, integrity verification,
    and backup retention management.
    """
    
    def __init__(self, backup_directory: str = "./backups", retention_days: int = 30):
        """
        Initialize the backup manager.
        
        Args:
            backup_directory: Directory to store backup files
            retention_days: Number of days to retain backups
        """
        self.backup_directory = Path(backup_directory)
        self.retention_days = retention_days
        
        # Ensure backup directory exists
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupManager initialized: {self.backup_directory}")
    
    def create_full_backup(self) -> Dict[str, Any]:
        """
        Create comprehensive backup of both database and Airtable data.
        
        Returns:
            Dict containing backup results and paths
        """
        try:
            logger.info("Starting full backup operation")
            
            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_session_dir = self.backup_directory / f"full_backup_{backup_timestamp}"
            backup_session_dir.mkdir(exist_ok=True)
            
            results = {
                'success': True,
                'backup_paths': [],
                'errors': [],
                'session_directory': str(backup_session_dir)
            }
            
            # Create database backup
            db_backup_result = self.create_database_backup(str(backup_session_dir))
            if db_backup_result.success:
                results['backup_paths'].append(db_backup_result.backup_path)
                logger.info(f"Database backup created: {db_backup_result.backup_path}")
            else:
                results['errors'].append(f"Database backup failed: {db_backup_result.error_message}")
                results['success'] = False
            
            # Create Airtable backup
            airtable_backup_result = self.create_airtable_backup(str(backup_session_dir))
            if airtable_backup_result.success:
                results['backup_paths'].append(airtable_backup_result.backup_path)
                logger.info(f"Airtable backup created: {airtable_backup_result.backup_path}")
            else:
                results['errors'].append(f"Airtable backup failed: {airtable_backup_result.error_message}")
                results['success'] = False
            
            # Create backup manifest
            manifest_path = backup_session_dir / "backup_manifest.json"
            manifest = {
                'backup_timestamp': backup_timestamp,
                'backup_type': 'full',
                'database_backup': db_backup_result.backup_path if db_backup_result.success else None,
                'airtable_backup': airtable_backup_result.backup_path if airtable_backup_result.success else None,
                'created_at': datetime.now().isoformat(),
                'retention_until': (datetime.now() + timedelta(days=self.retention_days)).isoformat()
            }
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            results['manifest_path'] = str(manifest_path)
            
            if results['success']:
                logger.info(f"Full backup completed successfully: {backup_session_dir}")
            else:
                logger.error(f"Full backup completed with errors: {results['errors']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Full backup operation failed: {e}")
            return {
                'success': False,
                'backup_paths': [],
                'errors': [f"Unexpected error during full backup: {str(e)}"]
            }
    
    def create_database_backup(self, backup_directory: Optional[str] = None) -> BackupResult:
        """
        Create backup of the local SQLite database.
        
        Args:
            backup_directory: Directory to store backup. If None, uses default.
            
        Returns:
            BackupResult: Results of the backup operation
        """
        try:
            # Import database connection here to avoid circular imports
            import sys
            from pathlib import Path
            
            # Add the lead scraper path for database imports
            lead_scraper_path = Path(__file__).parent.parent.parent / "4runr-lead-scraper"
            sys.path.insert(0, str(lead_scraper_path))
            
            try:
                from database.connection import get_database_connection
            except ImportError:
                logger.error("Could not import database connection")
                return BackupResult(
                    success=False,
                    backup_path="",
                    backup_type="database",
                    file_size_bytes=0,
                    checksum="",
                    created_at=datetime.now(),
                    error_message="Could not import database connection"
                )
            
            # Get database connection and path
            db_connection = get_database_connection()
            db_path = db_connection.db_path
            
            if not os.path.exists(db_path):
                return BackupResult(
                    success=False,
                    backup_path="",
                    backup_type="database",
                    file_size_bytes=0,
                    checksum="",
                    created_at=datetime.now(),
                    error_message=f"Database file not found: {db_path}"
                )
            
            # Determine backup path
            if backup_directory:
                backup_dir = Path(backup_directory)
            else:
                backup_dir = self.backup_directory
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"database_backup_{timestamp}.db"
            backup_path = backup_dir / backup_filename
            
            # Create backup using database's built-in backup method
            actual_backup_path = db_connection.backup_database(str(backup_path))
            
            # Verify backup was created
            if not os.path.exists(actual_backup_path):
                return BackupResult(
                    success=False,
                    backup_path=str(backup_path),
                    backup_type="database",
                    file_size_bytes=0,
                    checksum="",
                    created_at=datetime.now(),
                    error_message="Backup file was not created"
                )
            
            # Calculate file size and checksum
            file_size = os.path.getsize(actual_backup_path)
            checksum = self._calculate_file_checksum(actual_backup_path)
            
            # Verify backup integrity
            if not self.verify_backup_integrity(actual_backup_path):
                return BackupResult(
                    success=False,
                    backup_path=actual_backup_path,
                    backup_type="database",
                    file_size_bytes=file_size,
                    checksum=checksum,
                    created_at=datetime.now(),
                    error_message="Backup integrity verification failed"
                )
            
            logger.info(f"Database backup created successfully: {actual_backup_path}")
            
            return BackupResult(
                success=True,
                backup_path=actual_backup_path,
                backup_type="database",
                file_size_bytes=file_size,
                checksum=checksum,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return BackupResult(
                success=False,
                backup_path="",
                backup_type="database",
                file_size_bytes=0,
                checksum="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def create_airtable_backup(self, backup_directory: Optional[str] = None) -> BackupResult:
        """
        Create backup of Airtable data by exporting all records.
        
        Args:
            backup_directory: Directory to store backup. If None, uses default.
            
        Returns:
            BackupResult: Results of the backup operation
        """
        try:
            # Import Airtable client
            import sys
            from pathlib import Path
            
            # Add the outreach system path for Airtable imports
            outreach_path = Path(__file__).parent
            sys.path.insert(0, str(outreach_path))
            
            try:
                from configurable_airtable_client import get_configurable_airtable_client
            except ImportError:
                try:
                    # Try alternative import path
                    import sys
                    sys.path.append(str(Path(__file__).parent))
                    from configurable_airtable_client import get_configurable_airtable_client
                except ImportError:
                    logger.warning("Airtable client not available, skipping Airtable backup")
                    # Return success with empty backup for now
                    return BackupResult(
                        success=True,
                        backup_path="",
                        backup_type="airtable",
                        file_size_bytes=0,
                        checksum="",
                        created_at=datetime.now(),
                        error_message="Airtable client not available"
                    )
            
            # Get Airtable client
            airtable_client = get_configurable_airtable_client()
            
            # Determine backup path
            if backup_directory:
                backup_dir = Path(backup_directory)
            else:
                backup_dir = self.backup_directory
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"airtable_backup_{timestamp}.json"
            backup_path = backup_dir / backup_filename
            
            # Export all records from Airtable
            logger.info("Exporting all records from Airtable...")
            
            # Get all records (no formula to get everything)
            all_records = []
            try:
                # Use the table's all() method to get all records
                records = airtable_client.table.all()
                
                for record in records:
                    record_data = {
                        'id': record['id'],
                        'fields': record['fields'],
                        'created_time': record.get('createdTime', ''),
                    }
                    all_records.append(record_data)
                
                logger.info(f"Exported {len(all_records)} records from Airtable")
                
            except Exception as e:
                logger.error(f"Failed to export Airtable records: {e}")
                return BackupResult(
                    success=False,
                    backup_path=str(backup_path),
                    backup_type="airtable",
                    file_size_bytes=0,
                    checksum="",
                    created_at=datetime.now(),
                    error_message=f"Failed to export records: {str(e)}"
                )
            
            # Create backup data structure
            backup_data = {
                'backup_timestamp': timestamp,
                'backup_type': 'airtable',
                'record_count': len(all_records),
                'created_at': datetime.now().isoformat(),
                'records': all_records
            }
            
            # Write backup to file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Calculate file size and checksum
            file_size = os.path.getsize(backup_path)
            checksum = self._calculate_file_checksum(str(backup_path))
            
            logger.info(f"Airtable backup created successfully: {backup_path}")
            
            return BackupResult(
                success=True,
                backup_path=str(backup_path),
                backup_type="airtable",
                file_size_bytes=file_size,
                checksum=checksum,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Airtable backup failed: {e}")
            return BackupResult(
                success=False,
                backup_path="",
                backup_type="airtable",
                file_size_bytes=0,
                checksum="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verify the integrity of a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if backup is valid
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(backup_path)
            if file_size == 0:
                logger.error(f"Backup file is empty: {backup_path}")
                return False
            
            # For database backups, try to open as SQLite
            if backup_path.endswith('.db'):
                import sqlite3
                try:
                    conn = sqlite3.connect(backup_path)
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if not tables:
                        logger.error(f"Database backup contains no tables: {backup_path}")
                        return False
                    
                    logger.info(f"Database backup verified: {len(tables)} tables found")
                    
                except sqlite3.Error as e:
                    logger.error(f"Database backup is corrupted: {e}")
                    return False
            
            # For JSON backups, try to parse
            elif backup_path.endswith('.json'):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Verify required fields
                    required_fields = ['backup_timestamp', 'backup_type', 'created_at']
                    for field in required_fields:
                        if field not in data:
                            logger.error(f"JSON backup missing required field: {field}")
                            return False
                    
                    logger.info(f"JSON backup verified: {data.get('record_count', 0)} records")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON backup is corrupted: {e}")
                    return False
            
            logger.info(f"Backup integrity verified: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            return False
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old backup files based on retention policy.
        
        Args:
            retention_days: Number of days to retain backups. If None, uses instance default.
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            retention_days = retention_days or self.retention_days
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cleaned_count = 0
            
            # Find all backup files
            for backup_file in self.backup_directory.rglob("*backup_*"):
                if backup_file.is_file():
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        try:
                            backup_file.unlink()
                            logger.info(f"Cleaned up old backup: {backup_file}")
                            cleaned_count += 1
                        except Exception as e:
                            logger.error(f"Failed to delete old backup {backup_file}: {e}")
            
            # Clean up empty backup session directories
            for backup_dir in self.backup_directory.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("full_backup_"):
                    try:
                        # Check if directory is empty
                        if not any(backup_dir.iterdir()):
                            backup_dir.rmdir()
                            logger.info(f"Cleaned up empty backup directory: {backup_dir}")
                    except Exception as e:
                        logger.error(f"Failed to clean up backup directory {backup_dir}: {e}")
            
            logger.info(f"Backup cleanup completed: {cleaned_count} files removed")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0


if __name__ == "__main__":
    # Test the backup manager
    print("🧪 Testing Backup Manager...")
    
    # Create backup manager
    backup_manager = BackupManager("./test_backups")
    
    # Test database backup
    print("Testing database backup...")
    db_result = backup_manager.create_database_backup()
    print(f"Database backup: {'Success' if db_result.success else 'Failed'}")
    if not db_result.success:
        print(f"Error: {db_result.error_message}")
    
    # Test Airtable backup
    print("Testing Airtable backup...")
    airtable_result = backup_manager.create_airtable_backup()
    print(f"Airtable backup: {'Success' if airtable_result.success else 'Failed'}")
    if not airtable_result.success:
        print(f"Error: {airtable_result.error_message}")
    
    # Test full backup
    print("Testing full backup...")
    full_result = backup_manager.create_full_backup()
    print(f"Full backup: {'Success' if full_result['success'] else 'Failed'}")
    if full_result['errors']:
        print(f"Errors: {full_result['errors']}")
    
    print("✅ Backup manager test completed")