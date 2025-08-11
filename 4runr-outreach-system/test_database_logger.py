#!/usr/bin/env python3
"""
Comprehensive tests for the Database Logger system.

This test suite validates all logging functionality including:
- Database operation logging
- Sync operation logging  
- Migration operation logging
- Error logging with context
- Performance metrics logging
- Monitoring data logging
- Daily summary generation
"""

import unittest
import tempfile
import shutil
import json
import time
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from database_logger import (
    DatabaseLogger, 
    database_logger, 
    log_database_event, 
    monitor_performance
)


class TestDatabaseLogger(unittest.TestCase):
    """Test cases for DatabaseLogger functionality."""
    
    def setUp(self):
        """Set up test environment with temporary log directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = DatabaseLogger(log_directory=self.temp_dir)
        
        # Sample test data
        self.sample_lead_data = {
            "id": "test-lead-123",
            "name": "John Doe",
            "company": "Test Corp",
            "email": "john@testcorp.com",
            "linkedin_url": "https://linkedin.com/in/johndoe"
        }
        
        self.sample_operation_result = {
            "success": True,
            "records_affected": 1,
            "duplicate_detected": False
        }
        
        self.sample_performance_metrics = {
            "execution_time_ms": 150.5,
            "database_queries": 2,
            "memory_usage_mb": 25.3,
            "cpu_time_ms": 120.0
        }
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def test_logger_initialization(self):
        """Test that logger initializes correctly with proper directory structure."""
        # Check that all required subdirectories are created
        expected_dirs = [
            "database_operations",
            "sync_operations", 
            "migration_operations",
            "performance_metrics",
            "error_logs",
            "monitoring_data"
        ]
        
        for dir_name in expected_dirs:
            dir_path = Path(self.temp_dir) / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_name} should exist")
            self.assertTrue(dir_path.is_dir(), f"{dir_name} should be a directory")
        
        # Check session ID is generated
        self.assertIsNotNone(self.logger.session_id)
        self.assertEqual(len(self.logger.session_id), 8)
    
    def test_log_database_operation_success(self):
        """Test logging successful database operations."""
        log_path = self.logger.log_database_operation(
            "add_lead",
            self.sample_lead_data,
            self.sample_operation_result,
            self.sample_performance_metrics
        )
        
        # Verify log file was created
        self.assertTrue(os.path.exists(log_path))
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "database_operation")
        self.assertEqual(log_data["operation_details"]["operation_type"], "add_lead")
        self.assertTrue(log_data["operation_details"]["success"])
        self.assertEqual(log_data["operation_details"]["records_affected"], 1)
        self.assertEqual(log_data["lead_identifier"]["name"], "John Doe")
        self.assertEqual(log_data["performance_metrics"]["execution_time_ms"], 150.5)
        self.assertEqual(log_data["training_labels"]["operation_successful"], True)
    
    def test_log_database_operation_failure(self):
        """Test logging failed database operations."""
        failed_result = {
            "success": False,
            "records_affected": 0,
            "error": "Database connection failed"
        }
        
        log_path = self.logger.log_database_operation(
            "get_lead",
            self.sample_lead_data,
            failed_result,
            self.sample_performance_metrics
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["operation_details"]["operation_type"], "get_lead")
        self.assertFalse(log_data["operation_details"]["success"])
        self.assertEqual(log_data["operation_details"]["error_message"], "Database connection failed")
        self.assertEqual(log_data["training_labels"]["operation_successful"], False)
    
    def test_log_sync_operation(self):
        """Test logging sync operations with detailed results."""
        sync_details = {
            "batch_size": 10,
            "retry_attempts": 1,
            "sync_strategy": "to_airtable"
        }
        
        sync_results = {
            "success": True,
            "leads_synced": 8,
            "leads_skipped": 1,
            "leads_failed": 1,
            "conflicts_resolved": 2,
            "execution_time_ms": 5000.0,
            "avg_sync_time_ms": 500.0,
            "api_calls": 10,
            "rate_limited": False
        }
        
        leads_processed = [
            {"id": "lead1", "name": "John Doe", "company": "Corp A", "sync_status": "success"},
            {"id": "lead2", "name": "Jane Smith", "company": "Corp B", "sync_status": "failed"}
        ]
        
        log_path = self.logger.log_sync_operation(
            "to_airtable",
            sync_details,
            sync_results,
            leads_processed
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "sync_operation")
        self.assertEqual(log_data["sync_details"]["sync_type"], "to_airtable")
        self.assertEqual(log_data["sync_details"]["batch_size"], 10)
        self.assertEqual(log_data["sync_results"]["leads_synced"], 8)
        self.assertEqual(log_data["sync_results"]["leads_failed"], 1)
        self.assertEqual(log_data["performance_metrics"]["avg_sync_time_per_lead_ms"], 500.0)
        self.assertEqual(len(log_data["leads_summary"]), 2)
        self.assertTrue(log_data["training_labels"]["sync_successful"])
    
    def test_log_migration_operation(self):
        """Test logging migration operations."""
        migration_details = {
            "source_files": ["raw_leads.json", "enriched_leads.json"],
            "backup_created": True,
            "backup_location": "/backup/leads_backup_20240101.json",
            "validation_enabled": True
        }
        
        migration_results = {
            "success": True,
            "total_records": 1000,
            "records_migrated": 950,
            "records_skipped": 30,
            "records_failed": 20,
            "duplicates_found": 15,
            "execution_time_ms": 30000.0,
            "validation_passed": True
        }
        
        data_summary = {
            "source_file_sizes": {"raw_leads.json": 5.2, "enriched_leads.json": 8.7},
            "quality_distribution": {"high": 600, "medium": 300, "low": 100},
            "field_completeness": {"name": 0.98, "email": 0.75, "company": 0.92},
            "validation_errors": ["Invalid email format in record 123"]
        }
        
        log_path = self.logger.log_migration_operation(
            "json_to_db",
            migration_details,
            migration_results,
            data_summary
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "migration_operation")
        self.assertEqual(log_data["migration_details"]["migration_type"], "json_to_db")
        self.assertTrue(log_data["migration_details"]["backup_created"])
        self.assertEqual(log_data["migration_results"]["records_migrated"], 950)
        self.assertEqual(log_data["data_summary"]["quality_distribution"]["high"], 600)
        self.assertTrue(log_data["training_labels"]["migration_successful"])
        self.assertTrue(log_data["training_labels"]["data_integrity_maintained"])
    
    def test_log_error_with_context(self):
        """Test error logging with full context and stack traces."""
        error_details = {
            "message": "Connection timeout",
            "code": "DB_TIMEOUT",
            "stack_trace": "Traceback (most recent call last):\n  File test.py...",
            "severity": "error",
            "recovery_attempted": True,
            "recovery_successful": False
        }
        
        context = {
            "operation": "add_lead",
            "lead_data": self.sample_lead_data,
            "system_state": {"connections": 5, "memory_usage": "high"},
            "environment": "production"
        }
        
        log_path = self.logger.log_error(
            "database_error",
            error_details,
            context
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "error_log")
        self.assertEqual(log_data["error_details"]["error_type"], "database_error")
        self.assertEqual(log_data["error_details"]["error_message"], "Connection timeout")
        self.assertEqual(log_data["error_details"]["severity"], "error")
        self.assertEqual(log_data["context"]["operation_in_progress"], "add_lead")
        self.assertTrue(log_data["recovery_info"]["recovery_attempted"])
        self.assertFalse(log_data["recovery_info"]["recovery_successful"])
        self.assertEqual(log_data["training_labels"]["error_severity"], "error")
        self.assertFalse(log_data["training_labels"]["recoverable"])
    
    def test_log_performance_metrics(self):
        """Test performance metrics logging."""
        metrics = {
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:00:05",
            "total_duration_ms": 5000.0,
            "cpu_usage": 45.2,
            "memory_usage_mb": 128.5,
            "memory_peak_mb": 150.0,
            "disk_io_mb": 2.3,
            "network_io_mb": 1.8,
            "database_queries": 15,
            "api_calls": 5
        }
        
        system_info = {
            "database_size_mb": 250.0,
            "total_leads": 5000,
            "pending_syncs": 25,
            "active_connections": 3,
            "system_load": 0.75
        }
        
        log_path = self.logger.log_performance_metrics(
            "bulk_sync_operation",
            metrics,
            system_info
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "performance_metrics")
        self.assertEqual(log_data["operation_info"]["operation_name"], "bulk_sync_operation")
        self.assertEqual(log_data["performance_data"]["cpu_usage_percent"], 45.2)
        self.assertEqual(log_data["performance_data"]["memory_usage_mb"], 128.5)
        self.assertEqual(log_data["system_info"]["total_leads"], 5000)
        self.assertEqual(log_data["training_labels"]["performance_tier"], "slow")  # 5000ms
        self.assertFalse(log_data["training_labels"]["optimization_needed"])  # Exactly 5000ms
    
    def test_log_monitoring_data_with_alerts(self):
        """Test monitoring data logging with system alerts."""
        monitoring_data = {
            "collection_interval": 300,
            "database_responsive": True,
            "airtable_accessible": False,  # This should trigger alert
            "sync_queue_size": 150,  # High queue size
            "error_rate": 8.5,  # High error rate
            "avg_response_time": 1200,  # Slow response
            "total_leads": 10000,
            "leads_added_today": 50,
            "successful_syncs_today": 200,
            "failed_syncs_today": 25,
            "database_size_mb": 500.0
        }
        
        alerts = [
            {"severity": "warning", "message": "High sync queue size: 150 items"},
            {"severity": "critical", "message": "Airtable API not accessible"},
            {"severity": "warning", "message": "Error rate above threshold: 8.5%"}
        ]
        
        log_path = self.logger.log_monitoring_data(
            "health_check",
            monitoring_data,
            alerts
        )
        
        # Verify log content
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["log_type"], "monitoring_data")
        self.assertEqual(log_data["monitoring_info"]["monitoring_type"], "health_check")
        self.assertFalse(log_data["system_health"]["airtable_accessible"])
        self.assertEqual(log_data["system_health"]["sync_queue_size"], 150)
        self.assertEqual(log_data["statistics"]["total_leads"], 10000)
        self.assertEqual(len(log_data["alerts"]), 3)
        self.assertFalse(log_data["training_labels"]["system_healthy"])  # Critical alert present
        self.assertFalse(log_data["training_labels"]["performance_acceptable"])  # Slow response
        self.assertFalse(log_data["training_labels"]["sync_efficiency"])  # High error rate
    
    def test_convenience_function_log_database_event(self):
        """Test the convenience function for logging database events."""
        # Test database operation event
        log_path = log_database_event(
            "database_operation",
            self.sample_lead_data,
            self.sample_operation_result,
            {
                "operation_type": "add_lead",
                "performance_metrics": self.sample_performance_metrics
            }
        )
        
        self.assertTrue(os.path.exists(log_path))
        
        # Test sync operation event
        sync_results = {
            "success": True,
            "leads_synced": 5,
            "leads_failed": 0
        }
        
        log_path = log_database_event(
            "sync_operation",
            {},
            sync_results,
            {
                "sync_type": "to_airtable",
                "sync_details": {"batch_size": 5},
                "leads_processed": []
            }
        )
        
        self.assertTrue(os.path.exists(log_path))
    
    def test_performance_monitoring_decorator(self):
        """Test the performance monitoring decorator."""
        
        @monitor_performance("test_operation")
        def test_function(duration=0.1):
            time.sleep(duration)
            return "success"
        
        # Mock the database_logger to capture the log call
        with patch.object(database_logger, 'log_performance_metrics') as mock_log:
            result = test_function(0.05)  # 50ms sleep
            
            self.assertEqual(result, "success")
            mock_log.assert_called_once()
            
            # Verify the call arguments
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], "test_operation")  # operation_name
            metrics = call_args[0][1]
            self.assertIn("total_duration_ms", metrics)
            self.assertGreaterEqual(metrics["total_duration_ms"], 50)  # At least 50ms
            self.assertTrue(metrics["success"])
    
    def test_performance_monitoring_decorator_with_exception(self):
        """Test the performance monitoring decorator handles exceptions."""
        
        @monitor_performance("failing_operation")
        def failing_function():
            raise ValueError("Test error")
        
        # Mock the database_logger to capture the error log call
        with patch.object(database_logger, 'log_error') as mock_log_error:
            with self.assertRaises(ValueError):
                failing_function()
            
            mock_log_error.assert_called_once()
            
            # Verify error logging
            call_args = mock_log_error.call_args
            self.assertEqual(call_args[0][0], "performance_error")
            error_details = call_args[0][1]
            self.assertEqual(error_details["message"], "Test error")
            self.assertIn("stack_trace", error_details)
    
    def test_daily_summary_generation(self):
        """Test daily summary report generation."""
        # Create some sample log files for today
        today = datetime.now().strftime('%Y%m%d')
        
        # Create database operation logs
        db_ops_dir = Path(self.temp_dir) / "database_operations"
        for i in range(3):
            log_data = {
                "operation_details": {"success": i < 2, "operation_type": "add_lead"},
                "performance_metrics": {"execution_time_ms": 100 + i * 50}
            }
            log_file = db_ops_dir / f"db_op_add_lead_{today}_120000_{i}.json"
            with open(log_file, 'w') as f:
                json.dump(log_data, f)
        
        # Create sync operation logs
        sync_ops_dir = Path(self.temp_dir) / "sync_operations"
        for i in range(2):
            log_data = {
                "sync_results": {"leads_synced": 5 + i, "success": True},
                "sync_details": {"sync_type": "to_airtable"}
            }
            log_file = sync_ops_dir / f"sync_to_airtable_{today}_130000_{i}.json"
            with open(log_file, 'w') as f:
                json.dump(log_data, f)
        
        # Generate daily summary
        summary_path = self.logger.create_daily_summary()
        
        # Verify summary file exists and has correct content
        self.assertTrue(os.path.exists(summary_path))
        
        with open(summary_path, 'r') as f:
            summary_data = json.load(f)
        
        self.assertEqual(summary_data["summary_info"]["date"], datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(summary_data["operation_summary"]["total_database_operations"], 3)
        self.assertEqual(summary_data["operation_summary"]["successful_operations"], 2)
        self.assertEqual(summary_data["operation_summary"]["failed_operations"], 1)
        self.assertEqual(summary_data["sync_summary"]["total_sync_operations"], 2)
        self.assertEqual(summary_data["sync_summary"]["leads_synced"], 11)  # 5 + 6
    
    def test_helper_methods(self):
        """Test helper methods for training labels and assessments."""
        # Test performance tier classification
        self.assertEqual(self.logger._classify_performance_tier(50), "excellent")
        self.assertEqual(self.logger._classify_performance_tier(300), "good")
        self.assertEqual(self.logger._classify_performance_tier(1500), "acceptable")
        self.assertEqual(self.logger._classify_performance_tier(3000), "slow")
        self.assertEqual(self.logger._classify_performance_tier(8000), "very_slow")
        
        # Test data quality assessment
        high_quality_lead = {
            "name": "John Doe",
            "company": "Test Corp",
            "email": "john@test.com",
            "linkedin_url": "https://linkedin.com/in/john",
            "title": "CEO",
            "company_description": "Great company"
        }
        self.assertEqual(self.logger._assess_data_quality(high_quality_lead), "high")
        
        low_quality_lead = {"name": "John"}
        self.assertEqual(self.logger._assess_data_quality(low_quality_lead), "low")
        
        # Test operation complexity assessment
        self.assertEqual(self.logger._assess_operation_complexity("get_lead", {}), "low")
        self.assertEqual(self.logger._assess_operation_complexity("search_leads", {}), "medium")
        self.assertEqual(self.logger._assess_operation_complexity("find_duplicates", {}), "high")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)