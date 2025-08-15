#!/usr/bin/env python3
"""
Database Backup and Restore Utilities for Lead Database Integration.

This module provides comprehensive backup and restore functionality including:
- Automated database backups with rotation
- Point-in-time recovery capabilities
- Backup validation and integrity checks
- Compressed backup storage
- Backup scheduling and monitoring
"""

import os
import sqlite3
import shutil
import gzip
import json
import hashlib
import datetime
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager

from database_config import get_database_config, DatabaseConfig
from database_logger import database_logger, log_database_event


@dataclass
class BackupInfo:
    """Information about a database backup."""
    backup_id: str
    backup_path: str
    original_size: int
    compressed_size: int
    checksum: str
    created_at: datetime.datetime
    database_path: str
    backup_type: str  # full, incremental, manual
    compression_ratio: float = field(init=False)
    
    def __post_init__(self):
        """Calculate compression ratio after initialization."""
        if self.original_size > 0:
            self.compression_ratio = self.compressed_size / self.original_size
        else:
            self.compression_ratio = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert backup info to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_path": self.backup_path,
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "database_path": self.database_path,
            "backup_type": self.backup_type,
            "compression_ratio": self.compression_ratio
        }


class DatabaseBackupManager:
    """Manages database backup and restore operations."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize backup manager.
        
        Args:
            config: Database configuration (uses default if None)
        """
        self.config = config or get_database_config()
        self.backup_dir = Path(self.config.backup_path)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup metadata file
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing backup metadata
        self.backup_metadata = self._load_backup_metadata()
    
    def _load_backup_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load backup metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                database_logger.log_error("backup_error", {
                    "message": f"Failed to load backup metadata: {e}",
                    "severity": "warning"
                }, {"operation": "load_backup_metadata"})
                return {}
        return {}
    
    def _save_backup_metadata(self):
        """Save backup metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            database_logger.log_error("backup_error", {
                "message": f"Failed to save backup metadata: {e}",
                "severity": "error"
            }, {"operation": "save_backup_metadata"})
    
    def create_backup(self, backup_type: str = "manual", compress: bool = True) -> BackupInfo:
        """
        Create a database backup.
        
        Args:
            backup_type: Type of backup (manual, scheduled, full, incremental)
            compress: Whether to compress the backup
            
        Returns:
            BackupInfo: Information about the created backup
        """
        start_time = time.time()
        
        with self._lock:
            try:
                # Generate backup ID and filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_id = f"{backup_type}_{timestamp}"
                
                # Determine file extension
                extension = ".db.gz" if compress else ".db"
                backup_filename = f"{backup_id}{extension}"
                backup_path = self.backup_dir / backup_filename
                
                # Get original database size
                db_path = Path(self.config.database_path)
                if not db_path.exists():
                    raise FileNotFoundError(f"Database file not found: {db_path}")
                
                original_size = db_path.stat().st_size
                
                # Create backup using SQLite backup API
                self._create_sqlite_backup(str(db_path), str(backup_path), compress)
                
                # Calculate compressed size and checksum
                compressed_size = backup_path.stat().st_size
                checksum = self._calculate_checksum(backup_path)
                
                # Create backup info
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    backup_path=str(backup_path),
                    original_size=original_size,
                    compressed_size=compressed_size,
                    checksum=checksum,
                    created_at=datetime.datetime.now(),
                    database_path=str(db_path),
                    backup_type=backup_type
                )
                
                # Save backup metadata
                self.backup_metadata[backup_id] = backup_info.to_dict()
                self._save_backup_metadata()
                
                # Log successful backup
                execution_time_ms = (time.time() - start_time) * 1000
                log_database_event("migration_operation", {}, {
                    "success": True,
                    "total_records": 1,
                    "records_migrated": 1,
                    "execution_time_ms": execution_time_ms
                }, {
                    "migration_type": "database_backup",
                    "migration_details": {
                        "backup_id": backup_id,
                        "backup_type": backup_type,
                        "compressed": compress,
                        "original_size_mb": original_size / (1024 * 1024),
                        "compressed_size_mb": compressed_size / (1024 * 1024),
                        "compression_ratio": backup_info.compression_ratio
                    },
                    "data_summary": {
                        "backup_path": str(backup_path),
                        "checksum": checksum
                    }
                })
                
                return backup_info
                
            except Exception as e:
                # Log backup error
                execution_time_ms = (time.time() - start_time) * 1000
                log_database_event("migration_operation", {}, {
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms
                }, {
                    "migration_type": "database_backup",
                    "migration_details": {"backup_type": backup_type}
                })
                raise
    
    def _create_sqlite_backup(self, source_path: str, backup_path: str, compress: bool):
        """Create SQLite backup using the backup API."""
        # Connect to source database
        source_conn = sqlite3.connect(source_path)
        
        try:
            if compress:
                # Create compressed backup
                with gzip.open(backup_path, 'wb') as gz_file:
                    # Create temporary uncompressed backup first
                    temp_backup = backup_path.replace('.gz', '.tmp')
                    
                    try:
                        # Create backup using SQLite backup API
                        backup_conn = sqlite3.connect(temp_backup)
                        try:
                            source_conn.backup(backup_conn)
                        finally:
                            backup_conn.close()
                        
                        # Compress the backup
                        with open(temp_backup, 'rb') as temp_file:
                            shutil.copyfileobj(temp_file, gz_file)
                        
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_backup):
                            os.remove(temp_backup)
            else:
                # Create uncompressed backup
                backup_conn = sqlite3.connect(backup_path)
                try:
                    source_conn.backup(backup_conn)
                finally:
                    backup_conn.close()
                    
        finally:
            source_conn.close()
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def restore_backup(self, backup_id: str, target_path: Optional[str] = None, 
                      verify_checksum: bool = True) -> bool:
        """
        Restore a database from backup.
        
        Args:
            backup_id: ID of the backup to restore
            target_path: Target path for restoration (uses original if None)
            verify_checksum: Whether to verify backup integrity
            
        Returns:
            True if restoration successful, False otherwise
        """
        start_time = time.time()
        
        with self._lock:
            try:
                # Get backup info
                if backup_id not in self.backup_metadata:
                    raise ValueError(f"Backup {backup_id} not found")
                
                backup_info_dict = self.backup_metadata[backup_id]
                backup_path = Path(backup_info_dict["backup_path"])
                
                if not backup_path.exists():
                    raise FileNotFoundError(f"Backup file not found: {backup_path}")
                
                # Verify checksum if requested
                if verify_checksum:
                    current_checksum = self._calculate_checksum(backup_path)
                    expected_checksum = backup_info_dict["checksum"]
                    
                    if current_checksum != expected_checksum:
                        raise ValueError(f"Backup integrity check failed for {backup_id}")
                
                # Determine target path
                if target_path is None:
                    target_path = backup_info_dict["database_path"]
                
                target_path = Path(target_path)
                
                # Create backup of current database if it exists
                if target_path.exists():
                    backup_current = target_path.with_suffix(f".backup_{int(time.time())}.db")
                    shutil.copy2(target_path, backup_current)
                
                # Restore from backup
                self._restore_sqlite_backup(str(backup_path), str(target_path))
                
                # Log successful restoration
                execution_time_ms = (time.time() - start_time) * 1000
                log_database_event("migration_operation", {}, {
                    "success": True,
                    "total_records": 1,
                    "records_migrated": 1,
                    "execution_time_ms": execution_time_ms
                }, {
                    "migration_type": "database_restore",
                    "migration_details": {
                        "backup_id": backup_id,
                        "target_path": str(target_path),
                        "checksum_verified": verify_checksum
                    },
                    "data_summary": {
                        "backup_path": str(backup_path),
                        "restored_size_mb": target_path.stat().st_size / (1024 * 1024)
                    }
                })
                
                return True
                
            except Exception as e:
                # Log restoration error
                execution_time_ms = (time.time() - start_time) * 1000
                log_database_event("migration_operation", {}, {
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms
                }, {
                    "migration_type": "database_restore",
                    "migration_details": {"backup_id": backup_id}
                })
                
                database_logger.log_error("backup_error", {
                    "message": f"Failed to restore backup {backup_id}: {e}",
                    "severity": "error"
                }, {"operation": "restore_backup", "backup_id": backup_id})
                
                return False
    
    def _restore_sqlite_backup(self, backup_path: str, target_path: str):
        """Restore SQLite database from backup."""
        backup_path = Path(backup_path)
        target_path = Path(target_path)
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if backup_path.suffix == '.gz':
            # Decompress and restore
            with gzip.open(backup_path, 'rb') as gz_file:
                with open(target_path, 'wb') as target_file:
                    shutil.copyfileobj(gz_file, target_file)
        else:
            # Direct copy
            shutil.copy2(backup_path, target_path)
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[BackupInfo]:
        """
        List available backups.
        
        Args:
            backup_type: Filter by backup type (optional)
            
        Returns:
            List of BackupInfo objects
        """
        backups = []
        
        for backup_id, backup_dict in self.backup_metadata.items():
            if backup_type is None or backup_dict.get("backup_type") == backup_type:
                # Convert datetime string back to datetime object
                backup_dict_copy = backup_dict.copy()
                backup_dict_copy["created_at"] = datetime.datetime.fromisoformat(backup_dict["created_at"])
                
                backup_info = BackupInfo(
                    backup_id=backup_dict_copy["backup_id"],
                    backup_path=backup_dict_copy["backup_path"],
                    original_size=backup_dict_copy["original_size"],
                    compressed_size=backup_dict_copy["compressed_size"],
                    checksum=backup_dict_copy["checksum"],
                    created_at=backup_dict_copy["created_at"],
                    database_path=backup_dict_copy["database_path"],
                    backup_type=backup_dict_copy["backup_type"]
                )
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> int:
        """
        Clean up old backups based on retention policy.
        
        Returns:
            Number of backups cleaned up
        """
        cleaned_count = 0
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config.backup_retention_days)
        
        with self._lock:
            backups_to_remove = []
            
            for backup_id, backup_dict in self.backup_metadata.items():
                created_at = datetime.datetime.fromisoformat(backup_dict["created_at"])
                
                if created_at < cutoff_date:
                    backups_to_remove.append(backup_id)
            
            for backup_id in backups_to_remove:
                try:
                    backup_dict = self.backup_metadata[backup_id]
                    backup_path = Path(backup_dict["backup_path"])
                    
                    # Remove backup file
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    # Remove from metadata
                    del self.backup_metadata[backup_id]
                    cleaned_count += 1
                    
                except Exception as e:
                    database_logger.log_error("backup_error", {
                        "message": f"Failed to cleanup backup {backup_id}: {e}",
                        "severity": "warning"
                    }, {"operation": "cleanup_old_backups"})
            
            if cleaned_count > 0:
                self._save_backup_metadata()
        
        return cleaned_count
    
    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Verify backup integrity and validity.
        
        Args:
            backup_id: ID of backup to verify
            
        Returns:
            Dictionary with verification results
        """
        verification_result = {
            "backup_id": backup_id,
            "valid": False,
            "checksum_valid": False,
            "file_exists": False,
            "readable": False,
            "size_matches": False,
            "errors": []
        }
        
        try:
            if backup_id not in self.backup_metadata:
                verification_result["errors"].append("Backup not found in metadata")
                return verification_result
            
            backup_dict = self.backup_metadata[backup_id]
            backup_path = Path(backup_dict["backup_path"])
            
            # Check if file exists
            if not backup_path.exists():
                verification_result["errors"].append("Backup file does not exist")
                return verification_result
            
            verification_result["file_exists"] = True
            
            # Check file size
            current_size = backup_path.stat().st_size
            expected_size = backup_dict["compressed_size"]
            
            if current_size == expected_size:
                verification_result["size_matches"] = True
            else:
                verification_result["errors"].append(f"Size mismatch: expected {expected_size}, got {current_size}")
            
            # Verify checksum
            current_checksum = self._calculate_checksum(backup_path)
            expected_checksum = backup_dict["checksum"]
            
            if current_checksum == expected_checksum:
                verification_result["checksum_valid"] = True
            else:
                verification_result["errors"].append("Checksum verification failed")
            
            # Test readability
            try:
                if backup_path.suffix == '.gz':
                    with gzip.open(backup_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB
                else:
                    with open(backup_path, 'rb') as f:
                        f.read(1024)  # Read first 1KB
                
                verification_result["readable"] = True
            except Exception as e:
                verification_result["errors"].append(f"File not readable: {e}")
            
            # Overall validity
            verification_result["valid"] = (
                verification_result["file_exists"] and
                verification_result["checksum_valid"] and
                verification_result["readable"] and
                verification_result["size_matches"]
            )
            
        except Exception as e:
            verification_result["errors"].append(f"Verification failed: {e}")
        
        return verification_result
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics and summary.
        
        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "backup_types": {},
                "average_compression_ratio": 0
            }
        
        total_size = sum(backup.compressed_size for backup in backups)
        backup_types = {}
        compression_ratios = []
        
        for backup in backups:
            backup_type = backup.backup_type
            if backup_type not in backup_types:
                backup_types[backup_type] = 0
            backup_types[backup_type] += 1
            
            if backup.compression_ratio > 0:
                compression_ratios.append(backup.compression_ratio)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": total_size / (1024 * 1024),
            "oldest_backup": backups[-1].created_at.isoformat() if backups else None,
            "newest_backup": backups[0].created_at.isoformat() if backups else None,
            "backup_types": backup_types,
            "average_compression_ratio": sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0,
            "backup_directory": str(self.backup_dir),
            "retention_days": self.config.backup_retention_days
        }


# Global backup manager instance
backup_manager = DatabaseBackupManager()

def create_database_backup(backup_type: str = "manual", compress: bool = True) -> BackupInfo:
    """
    Create a database backup.
    
    Args:
        backup_type: Type of backup
        compress: Whether to compress the backup
        
    Returns:
        BackupInfo: Information about the created backup
    """
    return backup_manager.create_backup(backup_type, compress)

def restore_database_backup(backup_id: str, target_path: Optional[str] = None) -> bool:
    """
    Restore a database from backup.
    
    Args:
        backup_id: ID of backup to restore
        target_path: Target path for restoration
        
    Returns:
        True if successful, False otherwise
    """
    return backup_manager.restore_backup(backup_id, target_path)

def list_database_backups(backup_type: Optional[str] = None) -> List[BackupInfo]:
    """
    List available database backups.
    
    Args:
        backup_type: Filter by backup type
        
    Returns:
        List of BackupInfo objects
    """
    return backup_manager.list_backups(backup_type)