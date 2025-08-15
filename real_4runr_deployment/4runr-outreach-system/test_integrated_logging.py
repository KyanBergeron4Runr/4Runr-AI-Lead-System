#!/usr/bin/env python3
"""
Integration tests for Database Logging with Lead Database components.

This test suite validates that logging is properly integrated with:
- LeadDatabase operations
- AirtableSyncManager operations
- MigrationManager operations
- Error handling and recovery
"""

import unittest
import tempfile
import shutil
import json
import os
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

from lead_database import LeadDatabase
from database_logger import database_logger
from migration_manager import MigrationManager


class TestIntegratedLogging(unittest.TestCase):
    """Integration tests for logging with database components."""
    
    def setUp(self):
        """Set up test environment with temporary database and logs."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_leads.db")
        self.log_dir = os.path.join(self.temp_dir, "test_logs")
        
        # Create test database
        self.db = LeadDatabase(self.db_path)
        
        # Override logger to use test directory
        database_logger.log_directory = Path(self.log_dir)
        database_logger.log_directory.mkdir(exist_ok=True)
        for subdir in ["database_operations", "sync_operations", "migration_operations", 
                      "performance_metrics", "error_logs", "monitoring_data"]:
            (database_logger.log_directory / subdir).mkdir(exist_ok=True)
        
        # Sample test data
        self.sample_lead = {
            "name": "Integration Test Lead",
            "company": "Test Integration Corp",
            "email": "test@integration.com",
            "linkedin_url": "https://linkedin.com/in/testintegration",
            "title": "Test Manager",
            "industry": "Testing"
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_lead_database_add_lead_logging(self):
        """Test that add_lead operations are properly logged."""
        # Add a lead (this should trigger logging)
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Check that log file was created
        log_dir = Path(self.log_dir) / "database_operations"
        log_files = list(log_dir.glob("db_op_add_lead_*.json"))
        
        self.assertGreater(len(log_files), 0, "Add lead operation should create log file")
        
        # Verify log content
        with open(log_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "database_operation")
        self.assertEqual(log_data["operation_details"]["operation_type"], "add_lead")
        self.assertTrue(log_data["operation_details"]["success"])
        self.assertEqual(log_data["lead_identifier"]["name"], "Integration Test Lead")
        self.assertIn("execution_time_ms", log_data["performance_metrics"])
        self.assertTrue(log_data["training_labels"]["operation_successful"])
    
    def test_lead_database_get_lead_logging(self):
        """Test that get_lead operations are properly logged."""
        # First add a lead
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Clear existing logs
        log_dir = Path(self.log_dir) / "database_operations"
        for log_file in log_dir.glob("*.json"):
            log_file.unlink()
        
        # Get the lead (this should trigger logging)
        retrieved_lead = self.db.get_lead(lead_id)
        
        # Check that log file was created
        log_files = list(log_dir.glob("db_op_get_lead_*.json"))
        
        self.assertGreater(len(log_files), 0, "Get lead operation should create log file")
        self.assertIsNotNone(retrieved_lead, "Lead should be retrieved successfully")
        
        # Verify log content
        with open(log_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["operation_details"]["operation_type"], "get_lead")
        self.assertTrue(log_data["operation_details"]["success"])
        self.assertEqual(log_data["operation_details"]["records_affected"], 1)
    
    def test_lead_database_get_lead_not_found_logging(self):
        """Test that get_lead operations log when lead is not found."""
        # Try to get non-existent lead
        retrieved_lead = self.db.get_lead("non-existent-id")
        
        # Check that log file was created
        log_dir = Path(self.log_dir) / "database_operations"
        log_files = list(log_dir.glob("db_op_get_lead_*.json"))
        
        self.assertGreater(len(log_files), 0, "Get lead operation should create log file")
        self.assertIsNone(retrieved_lead, "Non-existent lead should return None")
        
        # Verify log content
        with open(log_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["operation_details"]["operation_type"], "get_lead")
        self.assertTrue(log_data["operation_details"]["success"])  # Operation succeeded, just no result
        self.assertEqual(log_data["operation_details"]["records_affected"], 0)
        self.assertEqual(log_data["operation_details"]["error_message"], "Lead not found")
    
    def test_lead_database_error_logging(self):
        """Test that database errors are properly logged."""
        # Create a scenario that will cause an error
        # Close the database connection to simulate an error
        self.db.db_manager.close()
        
        # Try to add a lead (this should fail and log an error)
        with self.assertRaises(Exception):
            self.db.add_lead(self.sample_lead)
        
        # Check that error log was created
        error_log_dir = Path(self.log_dir) / "error_logs"
        error_files = list(error_log_dir.glob("error_database_error_*.json"))
        
        self.assertGreater(len(error_files), 0, "Database error should create error log")
        
        # Verify error log content
        with open(error_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "error_log")
        self.assertEqual(log_data["error_details"]["error_type"], "database_error")
        self.assertIn("error_message", log_data["error_details"])
        self.assertIn("stack_trace", log_data["error_details"])
        self.assertEqual(log_data["context"]["operation_in_progress"], "add_lead")
    
    def test_duplicate_detection_logging(self):
        """Test that duplicate detection is properly logged."""
        # Add initial lead
        lead_id1 = self.db.add_lead(self.sample_lead)
        
        # Clear existing logs
        log_dir = Path(self.log_dir) / "database_operations"
        for log_file in log_dir.glob("*.json"):
            log_file.unlink()
        
        # Add duplicate lead (same email)
        duplicate_lead = self.sample_lead.copy()
        duplicate_lead["name"] = "Different Name"  # Different name, same email
        
        lead_id2 = self.db.add_lead(duplicate_lead)
        
        # Should return same ID due to duplicate detection
        self.assertEqual(lead_id1, lead_id2, "Duplicate lead should return same ID")
        
        # Check that log file shows duplicate detection
        log_files = list(log_dir.glob("db_op_add_lead_*.json"))
        self.assertGreater(len(log_files), 0, "Duplicate add should create log file")
        
        # Verify log content shows duplicate detection
        with open(log_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertTrue(log_data["data_details"]["duplicate_detected"])
        self.assertEqual(log_data["data_details"]["duplicate_action"], "updated")
    
    def test_migration_logging_integration(self):
        """Test that migration operations are properly logged."""
        # Create sample JSON files for migration
        json_dir = Path(self.temp_dir) / "json_files"
        json_dir.mkdir()
        
        # Create sample leads.json
        sample_leads = [
            {
                "name": "Migration Test 1",
                "company": "Migration Corp 1",
                "email": "test1@migration.com"
            },
            {
                "name": "Migration Test 2", 
                "company": "Migration Corp 2",
                "email": "test2@migration.com"
            }
        ]
        
        leads_file = json_dir / "leads.json"
        with open(leads_file, 'w') as f:
            json.dump(sample_leads, f)
        
        # Create migration manager and run migration
        migration_manager = MigrationManager(self.db_path)
        
        # Mock the logging to capture calls
        with patch.object(database_logger, 'log_migration_operation') as mock_log:
            # Run migration
            result = migration_manager.migrate_json_files([str(leads_file)])
            
            # Verify migration logging was called
            mock_log.assert_called()
            
            # Get the call arguments
            call_args = mock_log.call_args
            migration_type = call_args[0][0]
            migration_details = call_args[0][1]
            migration_results = call_args[0][2]
            
            self.assertEqual(migration_type, "json_to_db")
            self.assertIn("source_files", migration_details)
            self.assertIn("success", migration_results)
            self.assertTrue(migration_results["success"])
    
    def test_performance_monitoring_integration(self):
        """Test that performance monitoring works with database operations."""
        # Performance monitoring should be automatic via decorators
        
        # Add a lead (decorated method should log performance)
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Check that performance log was created
        perf_log_dir = Path(self.log_dir) / "performance_metrics"
        perf_files = list(perf_log_dir.glob("perf_add_lead_*.json"))
        
        self.assertGreater(len(perf_files), 0, "Performance monitoring should create log file")
        
        # Verify performance log content
        with open(perf_files[0], 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "performance_metrics")
        self.assertEqual(log_data["operation_info"]["operation_name"], "add_lead")
        self.assertIn("total_duration_ms", log_data["operation_info"])
        self.assertTrue(log_data["training_labels"]["performance_tier"] in 
                       ["excellent", "good", "acceptable", "slow", "very_slow"])
    
    def test_concurrent_logging(self):
        """Test that logging works correctly with concurrent operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def add_lead_worker(worker_id):
            try:
                lead_data = self.sample_lead.copy()
                lead_data["name"] = f"Concurrent Test {worker_id}"
                lead_data["email"] = f"test{worker_id}@concurrent.com"
                
                lead_id = self.db.add_lead(lead_data)
                results.append(lead_id)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_lead_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Concurrent operations should not cause errors: {errors}")
        self.assertEqual(len(results), 5, "All concurrent operations should succeed")
        
        # Verify that log files were created for each operation
        log_dir = Path(self.log_dir) / "database_operations"
        log_files = list(log_dir.glob("db_op_add_lead_*.json"))
        
        self.assertGreaterEqual(len(log_files), 5, "Each concurrent operation should create a log file")
    
    def test_log_file_structure_and_content(self):
        """Test that log files have correct structure and required fields."""
        # Perform various operations to generate different log types
        lead_id = self.db.add_lead(self.sample_lead)
        retrieved_lead = self.db.get_lead(lead_id)
        
        # Check database operation logs
        log_dir = Path(self.log_dir) / "database_operations"
        log_files = list(log_dir.glob("*.json"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # Verify required top-level fields
            required_fields = ["log_type", "session_id", "timestamp", "operation_details", 
                             "lead_identifier", "data_details", "performance_metrics", "training_labels"]
            
            for field in required_fields:
                self.assertIn(field, log_data, f"Log file should contain {field}")
            
            # Verify operation_details structure
            op_details = log_data["operation_details"]
            self.assertIn("operation_type", op_details)
            self.assertIn("success", op_details)
            self.assertIn("execution_time_ms", op_details)
            
            # Verify training_labels structure
            training_labels = log_data["training_labels"]
            self.assertIn("operation_successful", training_labels)
            self.assertIn("performance_tier", training_labels)
            self.assertIn("data_quality", training_labels)
    
    def test_daily_summary_with_real_data(self):
        """Test daily summary generation with real operation data."""
        # Perform several operations to generate log data
        for i in range(3):
            lead_data = self.sample_lead.copy()
            lead_data["name"] = f"Summary Test {i}"
            lead_data["email"] = f"summary{i}@test.com"
            self.db.add_lead(lead_data)
        
        # Generate daily summary
        summary_path = database_logger.create_daily_summary()
        
        # Verify summary file exists and has correct content
        self.assertTrue(os.path.exists(summary_path))
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Verify summary structure
        self.assertIn("summary_info", summary_data)
        self.assertIn("operation_summary", summary_data)
        self.assertIn("sync_summary", summary_data)
        self.assertIn("error_summary", summary_data)
        
        # Verify operation counts
        self.assertGreaterEqual(summary_data["operation_summary"]["total_database_operations"], 3)
        self.assertGreaterEqual(summary_data["operation_summary"]["successful_operations"], 3)


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)