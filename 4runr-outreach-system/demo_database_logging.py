#!/usr/bin/env python3
"""
Demo script for Database Logging System.

This script demonstrates the comprehensive logging capabilities of the
lead database integration system, showing how all operations are logged
with detailed metrics and context.
"""

import time
import json
from pathlib import Path
from datetime import datetime

from database_logger import database_logger, log_database_event, monitor_performance
from lead_database import LeadDatabase
from airtable_sync_manager import AirtableSyncManager


def demo_database_operation_logging():
    """Demonstrate database operation logging."""
    print("=== Database Operation Logging Demo ===")
    
    # Sample lead data
    sample_lead = {
        "name": "John Demo",
        "company": "Demo Corp",
        "email": "john@democorp.com",
        "linkedin_url": "https://linkedin.com/in/johndemo",
        "title": "CEO",
        "industry": "Technology"
    }
    
    # Simulate database operations with logging
    start_time = time.time()
    
    # Simulate successful add operation
    operation_result = {
        "success": True,
        "records_affected": 1,
        "duplicate_detected": False,
        "duplicate_action": "created"
    }
    
    performance_metrics = {
        "execution_time_ms": (time.time() - start_time) * 1000,
        "database_queries": 2,
        "memory_usage_mb": 15.5,
        "cpu_time_ms": 45.2
    }
    
    log_path = log_database_event("database_operation", sample_lead, operation_result, {
        "operation_type": "add_lead",
        "performance_metrics": performance_metrics
    })
    
    print(f"✓ Database operation logged to: {log_path}")
    
    # Show log content
    with open(log_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    print(f"  - Operation: {log_data['operation_details']['operation_type']}")
    print(f"  - Success: {log_data['operation_details']['success']}")
    print(f"  - Execution time: {log_data['performance_metrics']['execution_time_ms']:.1f}ms")
    print(f"  - Performance tier: {log_data['training_labels']['performance_tier']}")
    print()


def demo_sync_operation_logging():
    """Demonstrate sync operation logging."""
    print("=== Sync Operation Logging Demo ===")
    
    # Simulate sync operation
    sync_details = {
        "batch_size": 5,
        "retry_attempts": 0,
        "sync_strategy": "to_airtable"
    }
    
    sync_results = {
        "success": True,
        "leads_synced": 4,
        "leads_skipped": 1,
        "leads_failed": 0,
        "conflicts_resolved": 0,
        "execution_time_ms": 2500.0,
        "avg_sync_time_ms": 500.0,
        "api_calls": 5,
        "data_transferred_mb": 0.5,
        "memory_peak_mb": 25.0
    }
    
    leads_processed = [
        {"id": "demo1", "name": "John Demo", "company": "Demo Corp", "sync_status": "success"},
        {"id": "demo2", "name": "Jane Demo", "company": "Demo Inc", "sync_status": "success"},
        {"id": "demo3", "name": "Bob Demo", "company": "Demo LLC", "sync_status": "skipped"}
    ]
    
    log_path = log_database_event("sync_operation", {}, sync_results, {
        "sync_type": "to_airtable",
        "sync_details": sync_details,
        "leads_processed": leads_processed
    })
    
    print(f"✓ Sync operation logged to: {log_path}")
    
    # Show log content
    with open(log_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    print(f"  - Sync type: {log_data['sync_details']['sync_type']}")
    print(f"  - Leads synced: {log_data['sync_results']['leads_synced']}")
    print(f"  - Success rate: {(log_data['sync_results']['leads_synced'] / log_data['sync_details']['total_leads']) * 100:.1f}%")
    print(f"  - Sync efficiency: {log_data['training_labels']['sync_efficiency']}")
    print()


def demo_error_logging():
    """Demonstrate error logging with context."""
    print("=== Error Logging Demo ===")
    
    # Simulate an error scenario
    error_details = {
        "message": "Connection timeout to Airtable API",
        "code": "AIRTABLE_TIMEOUT",
        "stack_trace": "Traceback (most recent call last):\n  File demo.py, line 42, in sync_lead\n    response = airtable.create_record(data)\n  ConnectionTimeout: Request timed out",
        "severity": "error",
        "recovery_attempted": True,
        "recovery_successful": False,
        "recovery_method": "retry_with_backoff"
    }
    
    context = {
        "operation": "sync_to_airtable",
        "lead_data": {"id": "demo-lead-123", "name": "John Demo", "company": "Demo Corp"},
        "system_state": {"active_connections": 3, "memory_usage": "normal", "api_rate_limit": "approaching"},
        "user_action": "bulk_sync",
        "environment": "production"
    }
    
    log_path = database_logger.log_error("sync_error", error_details, context)
    
    print(f"✓ Error logged to: {log_path}")
    
    # Show log content
    with open(log_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    print(f"  - Error type: {log_data['error_details']['error_type']}")
    print(f"  - Severity: {log_data['error_details']['severity']}")
    print(f"  - Recovery attempted: {log_data['recovery_info']['recovery_attempted']}")
    print(f"  - Recoverable: {log_data['training_labels']['recoverable']}")
    print()


def demo_performance_monitoring():
    """Demonstrate performance monitoring decorator."""
    print("=== Performance Monitoring Demo ===")
    
    @monitor_performance("demo_heavy_operation")
    def simulate_heavy_operation(duration=0.5):
        """Simulate a heavy database operation."""
        print(f"  Performing heavy operation (simulated {duration}s)...")
        time.sleep(duration)
        return {"processed_records": 100, "success": True}
    
    # Run the monitored operation
    result = simulate_heavy_operation(0.3)
    print(f"  Operation result: {result}")
    print("  ✓ Performance metrics automatically logged")
    print()


def demo_monitoring_data_logging():
    """Demonstrate system monitoring data logging."""
    print("=== System Monitoring Demo ===")
    
    # Simulate system monitoring data
    monitoring_data = {
        "collection_interval": 300,
        "database_responsive": True,
        "airtable_accessible": True,
        "sync_queue_size": 25,
        "error_rate": 2.1,
        "avg_response_time": 450,
        "total_leads": 5000,
        "leads_added_today": 75,
        "successful_syncs_today": 150,
        "failed_syncs_today": 8,
        "database_size_mb": 125.5
    }
    
    # Simulate some alerts
    alerts = [
        {"severity": "info", "message": "System operating normally"},
        {"severity": "warning", "message": "Sync queue size approaching threshold: 25 items"}
    ]
    
    log_path = database_logger.log_monitoring_data("health_check", monitoring_data, alerts)
    
    print(f"✓ Monitoring data logged to: {log_path}")
    
    # Show log content
    with open(log_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    print(f"  - System healthy: {log_data['training_labels']['system_healthy']}")
    print(f"  - Performance acceptable: {log_data['training_labels']['performance_acceptable']}")
    print(f"  - Total leads: {log_data['statistics']['total_leads']}")
    print(f"  - Alerts: {len(log_data['alerts'])}")
    print()


def demo_daily_summary():
    """Demonstrate daily summary generation."""
    print("=== Daily Summary Demo ===")
    
    # Generate daily summary (this will analyze existing log files)
    summary_path = database_logger.create_daily_summary()
    
    print(f"✓ Daily summary generated: {summary_path}")
    
    # Show summary content
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)
    
    print(f"  - Date: {summary_data['summary_info']['date']}")
    print(f"  - Database operations: {summary_data['operation_summary']['total_database_operations']}")
    print(f"  - Sync operations: {summary_data['sync_summary']['total_sync_operations']}")
    print(f"  - Total errors: {summary_data['error_summary']['total_errors']}")
    print()


def show_log_directory_structure():
    """Show the structure of generated log files."""
    print("=== Log Directory Structure ===")
    
    log_dir = Path("database_logs")
    if log_dir.exists():
        print(f"Log directory: {log_dir.absolute()}")
        
        for subdir in log_dir.iterdir():
            if subdir.is_dir():
                file_count = len(list(subdir.glob("*.json")))
                print(f"  📁 {subdir.name}/ ({file_count} files)")
                
                # Show a few recent files
                recent_files = sorted(subdir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                for file in recent_files:
                    file_size = file.stat().st_size
                    print(f"    📄 {file.name} ({file_size} bytes)")
    else:
        print("No log directory found yet. Run some operations first!")
    print()


def main():
    """Run all logging demos."""
    print("🚀 Database Logging System Demo")
    print("=" * 50)
    print()
    
    # Run all demos
    demo_database_operation_logging()
    demo_sync_operation_logging()
    demo_error_logging()
    demo_performance_monitoring()
    demo_monitoring_data_logging()
    demo_daily_summary()
    show_log_directory_structure()
    
    print("✅ All logging demos completed successfully!")
    print()
    print("Key Features Demonstrated:")
    print("• Database operation logging with performance metrics")
    print("• Sync operation logging with detailed results")
    print("• Error logging with full context and stack traces")
    print("• Automatic performance monitoring via decorators")
    print("• System monitoring data with alerts")
    print("• Daily summary report generation")
    print("• Structured log files for training and analysis")
    print()
    print("The logging system is now ready for production use!")


if __name__ == "__main__":
    main()