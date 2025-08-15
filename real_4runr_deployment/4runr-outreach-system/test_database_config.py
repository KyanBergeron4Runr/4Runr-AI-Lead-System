#!/usr/bin/env python3
"""
Tests for Database Configuration and Health Check functionality.

This test suite validates:
- Database configuration loading and validation
- Environment variable handling
- Backup and restore operations
- Health check functionality
- Configuration validation
"""

import unittest
import tempfile
import shutil
import os
import sqlite3
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from database_config import DatabaseConfig, DatabaseConfigManager, get_database_config
from database_backup import DatabaseBackupManager, BackupInfo
from database_health import DatabaseHealthMonitor, HealthCheckResult


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for database configuration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        self.test_backup_path = os.path.join(self.temp_dir, "backups")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_database_config_creation(self):
        """Test creating database configuration with defaults."""
        config = DatabaseConfig(
            database_path=self.test_db_path,
            backup_path=self.test_backup_path
        )
        
        self.assertEqual(config.database_path, self.test_db_path)
        self.assertEqual(config.backup_path, self.test_backup_path)
        self.assertEqual(config.max_connections, 10)
        self.assertEqual(config.connection_timeout, 30)
        self.assertTrue(config.enable_wal_mode)
        self.assertTrue(config.auto_vacuum)
        
        # Check that directories were created
        self.assertTrue(Path(self.test_db_path).parent.exists())
        self.assertTrue(Path(self.test_backup_path).exists())
    
    def test_database_config_validation(self):
        """Test configuration validation."""
        # Test invalid max_connections
        with self.assertRaises(ValueError):
            DatabaseConfig(
                database_path=self.test_db_path,
                backup_path=self.test_backup_path,
                max_connections=0
            )
        
        # Test invalid connection_timeout
        with self.assertRaises(ValueError):
            DatabaseConfig(
                database_path=self.test_db_path,
                backup_path=self.test_backup_path,
                connection_timeout=0
            )
        
        # Test invalid synchronous mode
        with self.assertRaises(ValueError):
            DatabaseConfig(
                database_path=self.test_db_path,
                backup_path=self.test_backup_path,
                synchronous="invalid"
            )
    
    def test_sqlite_pragmas(self):
        """Test SQLite PRAGMA generation."""
        config = DatabaseConfig(
            database_path=self.test_db_path,
            backup_path=self.test_backup_path,
            cache_size=-32000,
            synchronous="normal",
            journal_mode="wal"
        )
        
        pragmas = config.get_sqlite_pragmas()
        
        self.assertEqual(pragmas["cache_size"], -32000)
        self.assertEqual(pragmas["synchronous"], "normal")
        self.assertEqual(pragmas["journal_mode"], "wal")
        self.assertEqual(pragmas["foreign_keys"], "on")
        self.assertIn("busy_timeout", pragmas)
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = DatabaseConfig(
            database_path=self.test_db_path,
            backup_path=self.test_backup_path
        )
        
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict["database_path"], self.test_db_path)
        self.assertEqual(config_dict["backup_path"], self.test_backup_path)
        self.assertIn("max_connections", config_dict)
        self.assertIn("enable_wal_mode", config_dict)


class TestDatabaseConfigManager(unittest.TestCase):
    """Test cases for database configuration manager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, ".env")
        
        # Create test .env file
        with open(self.env_file, 'w') as f:
            f.write(f"""
LEAD_DATABASE_PATH={self.temp_dir}/test.db
LEAD_DATABASE_BACKUP_PATH={self.temp_dir}/backups
LEAD_DATABASE_MAX_CONNECTIONS=5
LEAD_DATABASE_CONNECTION_TIMEOUT=15
LEAD_DATABASE_ENABLE_WAL_MODE=false
LEAD_DATABASE_AUTO_VACUUM=false
LEAD_DATABASE_BACKUP_RETENTION_DAYS=14
LEAD_DATABASE_HEALTH_CHECK_INTERVAL=600
LEAD_DATABASE_SLOW_QUERY_THRESHOLD_MS=2000
LEAD_DATABASE_ENABLE_LOGGING=false
""")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_config_from_env(self):
        """Test loading configuration from environment file."""
        config_manager = DatabaseConfigManager(self.env_file)
        config = config_manager.load_config()
        
        self.assertEqual(config.max_connections, 5)
        self.assertEqual(config.connection_timeout, 15)
        self.assertFalse(config.enable_wal_mode)
        self.assertFalse(config.auto_vacuum)
        self.assertEqual(config.backup_retention_days, 14)
        self.assertEqual(config.health_check_interval, 600)
        self.assertEqual(config.slow_query_threshold_ms, 2000)
        self.assertFalse(config.enable_logging)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = DatabaseConfigManager(self.env_file)
        config = config_manager.load_config()
        
        validation_result = config_manager.validate_config(config)
        
        self.assertIsInstance(validation_result, dict)
        self.assertIn("valid", validation_result)
        self.assertIn("errors", validation_result)
        self.assertIn("warnings", validation_result)
        self.assertIn("recommendations", validation_result)
    
    def test_config_summary(self):
        """Test configuration summary generation."""
        config_manager = DatabaseConfigManager(self.env_file)
        config_manager.load_config()
        
        summary = config_manager.get_config_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn("database_path", summary)
        self.assertIn("backup_path", summary)
        self.assertIn("max_connections", summary)
        self.assertIn("wal_mode_enabled", summary)


class TestDatabaseBackup(unittest.TestCase):
    """Test cases for database backup functionality."""
    
    def setUp(self):
        """Set up test environment with database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.backup_path = os.path.join(self.temp_dir, "backups")
        
        # Create test database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                company TEXT
            )
        """)
        cursor.execute("INSERT INTO leads VALUES ('1', 'Test User', 'test@test.com', 'Test Corp')")
        conn.commit()
        conn.close()
        
        # Create config
        from database_config import DatabaseConfig
        self.config = DatabaseConfig(
            database_path=self.db_path,
            backup_path=self.backup_path
        )
        
        self.backup_manager = DatabaseBackupManager(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_backup(self):
        """Test creating a database backup."""
        backup_info = self.backup_manager.create_backup("test", compress=False)
        
        self.assertIsInstance(backup_info, BackupInfo)
        self.assertEqual(backup_info.backup_type, "test")
        self.assertTrue(Path(backup_info.backup_path).exists())
        self.assertGreater(backup_info.original_size, 0)
        self.assertGreater(backup_info.compressed_size, 0)
        self.assertTrue(backup_info.checksum)
    
    def test_create_compressed_backup(self):
        """Test creating a compressed backup."""
        backup_info = self.backup_manager.create_backup("test", compress=True)
        
        self.assertIsInstance(backup_info, BackupInfo)
        self.assertTrue(backup_info.backup_path.endswith('.gz'))
        self.assertTrue(Path(backup_info.backup_path).exists())
        # Compressed size should be smaller than original
        self.assertLess(backup_info.compressed_size, backup_info.original_size)
    
    def test_list_backups(self):
        """Test listing backups."""
        # Create a few backups
        backup1 = self.backup_manager.create_backup("manual", compress=False)
        backup2 = self.backup_manager.create_backup("scheduled", compress=True)
        
        # List all backups
        all_backups = self.backup_manager.list_backups()
        self.assertEqual(len(all_backups), 2)
        
        # List by type
        manual_backups = self.backup_manager.list_backups("manual")
        self.assertEqual(len(manual_backups), 1)
        self.assertEqual(manual_backups[0].backup_type, "manual")
        
        scheduled_backups = self.backup_manager.list_backups("scheduled")
        self.assertEqual(len(scheduled_backups), 1)
        self.assertEqual(scheduled_backups[0].backup_type, "scheduled")
    
    def test_restore_backup(self):
        """Test restoring from backup."""
        # Create backup
        backup_info = self.backup_manager.create_backup("test", compress=False)
        
        # Modify original database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leads VALUES ('2', 'Modified User', 'modified@test.com', 'Modified Corp')")
        conn.commit()
        conn.close()
        
        # Create new target path for restoration
        restore_path = os.path.join(self.temp_dir, "restored.db")
        
        # Restore backup
        success = self.backup_manager.restore_backup(backup_info.backup_id, restore_path)
        self.assertTrue(success)
        self.assertTrue(Path(restore_path).exists())
        
        # Verify restored data
        conn = sqlite3.connect(restore_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Should have only original record, not the modified one
        self.assertEqual(count, 1)
    
    def test_verify_backup(self):
        """Test backup verification."""
        backup_info = self.backup_manager.create_backup("test", compress=False)
        
        verification_result = self.backup_manager.verify_backup(backup_info.backup_id)
        
        self.assertIsInstance(verification_result, dict)
        self.assertTrue(verification_result["valid"])
        self.assertTrue(verification_result["checksum_valid"])
        self.assertTrue(verification_result["file_exists"])
        self.assertTrue(verification_result["readable"])
        self.assertTrue(verification_result["size_matches"])
        self.assertEqual(len(verification_result["errors"]), 0)
    
    def test_backup_statistics(self):
        """Test backup statistics generation."""
        # Create a few backups
        self.backup_manager.create_backup("manual", compress=False)
        self.backup_manager.create_backup("scheduled", compress=True)
        
        stats = self.backup_manager.get_backup_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_backups"], 2)
        self.assertGreater(stats["total_size_mb"], 0)
        self.assertIn("manual", stats["backup_types"])
        self.assertIn("scheduled", stats["backup_types"])
        self.assertIsNotNone(stats["oldest_backup"])
        self.assertIsNotNone(stats["newest_backup"])


class TestDatabaseHealth(unittest.TestCase):
    """Test cases for database health monitoring."""
    
    def setUp(self):
        """Set up test environment with database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # Create test database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                company TEXT
            )
        """)
        # Add some test data
        for i in range(100):
            cursor.execute("INSERT INTO leads VALUES (?, ?, ?, ?)", 
                         (f"id_{i}", f"User {i}", f"user{i}@test.com", f"Company {i}"))
        conn.commit()
        conn.close()
        
        # Create config
        from database_config import DatabaseConfig
        self.config = DatabaseConfig(
            database_path=self.db_path,
            backup_path=os.path.join(self.temp_dir, "backups")
        )
        
        self.health_monitor = DatabaseHealthMonitor(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_connectivity_check(self):
        """Test database connectivity check."""
        result = self.health_monitor._check_connectivity()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "connectivity")
        self.assertEqual(result.status, "healthy")
        self.assertIn("successful", result.message.lower())
        self.assertGreater(result.execution_time_ms, 0)
    
    def test_database_file_check(self):
        """Test database file check."""
        result = self.health_monitor._check_database_file()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "database_file")
        self.assertEqual(result.status, "healthy")
        self.assertIn("file_size_mb", result.details)
        self.assertIn("free_space_mb", result.details)
        self.assertGreater(result.details["file_size_mb"], 0)
    
    def test_schema_integrity_check(self):
        """Test schema integrity check."""
        result = self.health_monitor._check_schema_integrity()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "schema_integrity")
        self.assertEqual(result.status, "healthy")
        self.assertIn("existing_tables", result.details)
        self.assertIn("leads", result.details["existing_tables"])
    
    def test_data_integrity_check(self):
        """Test data integrity check."""
        result = self.health_monitor._check_data_integrity()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "data_integrity")
        self.assertEqual(result.status, "healthy")
        self.assertIn("total_records", result.details)
        self.assertEqual(result.details["total_records"], 100)
    
    def test_query_performance_check(self):
        """Test query performance check."""
        result = self.health_monitor._check_query_performance()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "query_performance")
        self.assertIn(result.status, ["healthy", "warning"])
        self.assertIn("count_query_ms", result.details)
        self.assertGreater(result.details["count_query_ms"], 0)
    
    def test_database_size_check(self):
        """Test database size check."""
        result = self.health_monitor._check_database_size()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "database_size")
        self.assertEqual(result.status, "healthy")  # Should be small test DB
        self.assertIn("file_size_mb", result.details)
        self.assertIn("record_count", result.details)
        self.assertEqual(result.details["record_count"], 100)
    
    def test_system_resources_check(self):
        """Test system resources check."""
        result = self.health_monitor._check_system_resources()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "system_resources")
        self.assertIn(result.status, ["healthy", "warning"])  # Depends on system state
        self.assertIn("cpu_percent", result.details)
        self.assertIn("memory_percent", result.details)
        self.assertIn("disk_percent", result.details)
    
    def test_configuration_check(self):
        """Test configuration check."""
        result = self.health_monitor._check_configuration()
        
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.check_name, "configuration")
        self.assertEqual(result.status, "healthy")
        self.assertIn("current_pragmas", result.details)
    
    def test_full_health_check(self):
        """Test complete health check."""
        report = self.health_monitor.run_health_check(include_performance=True)
        
        self.assertIsNotNone(report)
        self.assertIn(report.overall_status, ["healthy", "warning", "critical", "error"])
        self.assertGreater(len(report.checks), 5)  # Should have multiple checks
        self.assertIsInstance(report.summary, dict)
        self.assertIsInstance(report.recommendations, list)
        self.assertIsInstance(report.alerts, list)
        
        # Check that all expected checks are present
        check_names = {check.check_name for check in report.checks}
        expected_checks = {
            "connectivity", "database_file", "schema_integrity", 
            "data_integrity", "query_performance", "database_size",
            "system_resources", "configuration"
        }
        self.assertTrue(expected_checks.issubset(check_names))
    
    def test_health_check_history(self):
        """Test health check history tracking."""
        # Run a few health checks
        self.health_monitor.run_health_check()
        self.health_monitor.run_health_check()
        
        history = self.health_monitor.get_health_history()
        
        self.assertEqual(len(history), 2)
        self.assertTrue(all(hasattr(report, 'generated_at') for report in history))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)