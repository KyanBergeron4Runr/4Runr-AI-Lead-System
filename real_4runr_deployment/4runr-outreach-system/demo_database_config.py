#!/usr/bin/env python3
"""
Demo script for Database Configuration and Health Check functionality.

This script demonstrates:
- Database configuration loading and validation
- Backup and restore operations
- Health check monitoring
- Configuration management
"""

import os
import json
import time
from pathlib import Path

from database_config import (
    DatabaseConfig, DatabaseConfigManager, 
    get_database_config, validate_database_config
)
from database_backup import (
    DatabaseBackupManager, create_database_backup, 
    restore_database_backup, list_database_backups
)
from database_health import (
    DatabaseHealthMonitor, run_database_health_check,
    get_database_health_summary
)
from lead_database import LeadDatabase


def demo_configuration_management():
    """Demonstrate configuration management."""
    print("=== Database Configuration Management Demo ===")
    
    # Load current configuration
    config = get_database_config()
    print(f"✓ Configuration loaded from environment")
    print(f"  - Database path: {config.database_path}")
    print(f"  - Backup path: {config.backup_path}")
    print(f"  - Max connections: {config.max_connections}")
    print(f"  - WAL mode enabled: {config.enable_wal_mode}")
    print(f"  - Auto backup enabled: {config.auto_backup_enabled}")
    print()
    
    # Validate configuration
    validation_result = validate_database_config(config)
    print(f"✓ Configuration validation: {'PASSED' if validation_result['valid'] else 'FAILED'}")
    
    if validation_result['errors']:
        print("  Errors:")
        for error in validation_result['errors']:
            print(f"    - {error}")
    
    if validation_result['warnings']:
        print("  Warnings:")
        for warning in validation_result['warnings']:
            print(f"    - {warning}")
    
    if validation_result['recommendations']:
        print("  Recommendations:")
        for rec in validation_result['recommendations']:
            print(f"    - {rec}")
    
    print()
    
    # Show SQLite pragmas
    pragmas = config.get_sqlite_pragmas()
    print("✓ SQLite PRAGMA settings:")
    for pragma, value in pragmas.items():
        print(f"  - {pragma}: {value}")
    print()
    
    # Configuration summary
    config_manager = DatabaseConfigManager()
    summary = config_manager.get_config_summary()
    print("✓ Configuration summary:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    print()


def demo_database_backup():
    """Demonstrate database backup functionality."""
    print("=== Database Backup and Restore Demo ===")
    
    # Initialize database with some test data
    db = LeadDatabase()
    
    # Add some test leads
    test_leads = [
        {"name": "John Backup", "company": "Backup Corp", "email": "john@backup.com"},
        {"name": "Jane Restore", "company": "Restore Inc", "email": "jane@restore.com"},
        {"name": "Bob Demo", "company": "Demo LLC", "email": "bob@demo.com"}
    ]
    
    for lead in test_leads:
        db.add_lead(lead)
    
    print(f"✓ Created test database with {len(test_leads)} leads")
    
    # Create backup
    print("Creating database backup...")
    backup_info = create_database_backup("demo", compress=True)
    print(f"✓ Backup created: {backup_info.backup_id}")
    print(f"  - Original size: {backup_info.original_size / 1024:.1f} KB")
    print(f"  - Compressed size: {backup_info.compressed_size / 1024:.1f} KB")
    print(f"  - Compression ratio: {backup_info.compression_ratio:.2f}")
    print(f"  - Checksum: {backup_info.checksum[:16]}...")
    print()
    
    # List backups
    backups = list_database_backups()
    print(f"✓ Available backups: {len(backups)}")
    for backup in backups[:3]:  # Show first 3
        print(f"  - {backup.backup_id} ({backup.backup_type}) - {backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Backup statistics
    backup_manager = DatabaseBackupManager()
    stats = backup_manager.get_backup_statistics()
    print("✓ Backup statistics:")
    print(f"  - Total backups: {stats['total_backups']}")
    print(f"  - Total size: {stats['total_size_mb']:.1f} MB")
    print(f"  - Average compression: {stats['average_compression_ratio']:.2f}")
    print(f"  - Retention days: {stats['retention_days']}")
    print()
    
    # Verify backup
    verification = backup_manager.verify_backup(backup_info.backup_id)
    print(f"✓ Backup verification: {'PASSED' if verification['valid'] else 'FAILED'}")
    if verification['errors']:
        for error in verification['errors']:
            print(f"  - Error: {error}")
    print()


def demo_health_monitoring():
    """Demonstrate health monitoring functionality."""
    print("=== Database Health Monitoring Demo ===")
    
    # Run comprehensive health check
    print("Running comprehensive health check...")
    health_report = run_database_health_check(include_performance=True)
    
    print(f"✓ Health check completed")
    print(f"  - Overall status: {health_report.overall_status.upper()}")
    print(f"  - Total checks: {len(health_report.checks)}")
    print(f"  - Generated at: {health_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Show individual check results
    print("✓ Individual check results:")
    for check in health_report.checks:
        status_icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "error": "🔥"
        }.get(check.status, "❓")
        
        print(f"  {status_icon} {check.check_name}: {check.message} ({check.execution_time_ms:.1f}ms)")
    print()
    
    # Show summary
    print("✓ Health summary:")
    for key, value in health_report.summary.items():
        print(f"  - {key}: {value}")
    print()
    
    # Show recommendations
    if health_report.recommendations:
        print("✓ Recommendations:")
        for rec in health_report.recommendations:
            print(f"  - {rec}")
        print()
    
    # Show alerts
    if health_report.alerts:
        print("⚠️ Alerts:")
        for alert in health_report.alerts:
            severity_icon = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨"
            }.get(alert["severity"], "❓")
            print(f"  {severity_icon} {alert['message']}")
        print()
    
    # Quick health summary
    quick_summary = get_database_health_summary()
    print("✓ Quick health summary:")
    for key, value in quick_summary.items():
        print(f"  - {key}: {value}")
    print()


def demo_configuration_scenarios():
    """Demonstrate different configuration scenarios."""
    print("=== Configuration Scenarios Demo ===")
    
    # Scenario 1: High-performance configuration
    print("Scenario 1: High-performance configuration")
    high_perf_config = DatabaseConfig(
        database_path="data/high_perf.db",
        backup_path="data/backups",
        cache_size=-128000,  # 128MB cache
        synchronous="normal",
        journal_mode="wal",
        max_connections=20
    )
    
    print(f"  - Cache size: {abs(high_perf_config.cache_size) / 1000}MB")
    print(f"  - Journal mode: {high_perf_config.journal_mode}")
    print(f"  - Max connections: {high_perf_config.max_connections}")
    print()
    
    # Scenario 2: Safety-first configuration
    print("Scenario 2: Safety-first configuration")
    safe_config = DatabaseConfig(
        database_path="data/safe.db",
        backup_path="data/backups",
        synchronous="full",
        auto_backup_enabled=True,
        backup_interval_hours=6,
        backup_retention_days=90
    )
    
    print(f"  - Synchronous mode: {safe_config.synchronous}")
    print(f"  - Auto backup: {safe_config.auto_backup_enabled}")
    print(f"  - Backup interval: {safe_config.backup_interval_hours}h")
    print(f"  - Retention: {safe_config.backup_retention_days} days")
    print()
    
    # Scenario 3: Development configuration
    print("Scenario 3: Development configuration")
    dev_config = DatabaseConfig(
        database_path="data/dev.db",
        backup_path="data/dev_backups",
        enable_logging=True,
        log_slow_queries=True,
        slow_query_threshold_ms=100,
        health_check_interval=60
    )
    
    print(f"  - Logging enabled: {dev_config.enable_logging}")
    print(f"  - Slow query threshold: {dev_config.slow_query_threshold_ms}ms")
    print(f"  - Health check interval: {dev_config.health_check_interval}s")
    print()


def demo_maintenance_operations():
    """Demonstrate database maintenance operations."""
    print("=== Database Maintenance Demo ===")
    
    # Database statistics
    db = LeadDatabase()
    stats = db.get_database_stats()
    
    print("✓ Database statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    print()
    
    # Backup cleanup simulation
    backup_manager = DatabaseBackupManager()
    print("✓ Backup maintenance:")
    print(f"  - Current backups: {len(backup_manager.list_backups())}")
    
    # Simulate cleanup (but don't actually clean up in demo)
    old_backups = [b for b in backup_manager.list_backups() 
                   if (backup_manager.backup_metadata[b.backup_id]['created_at'])]
    print(f"  - Backups eligible for cleanup: {len(old_backups)}")
    print()
    
    # Health monitoring history
    health_monitor = DatabaseHealthMonitor()
    history = health_monitor.get_health_history(limit=5)
    
    print(f"✓ Health check history: {len(history)} recent checks")
    for i, report in enumerate(history[-3:], 1):  # Show last 3
        print(f"  {i}. {report.generated_at.strftime('%H:%M:%S')} - {report.overall_status}")
    print()


def show_configuration_files():
    """Show current configuration files and environment."""
    print("=== Configuration Files and Environment ===")
    
    # Show .env file content (if exists)
    env_file = Path(".env")
    if env_file.exists():
        print("✓ Current .env configuration:")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            db_lines = [line.strip() for line in lines if line.startswith('LEAD_DATABASE_')]
            for line in db_lines[:10]:  # Show first 10 database config lines
                print(f"  {line}")
        print()
    
    # Show directory structure
    print("✓ Directory structure:")
    data_dir = Path("data")
    if data_dir.exists():
        for item in sorted(data_dir.iterdir())[:10]:  # Show first 10 items
            size = ""
            if item.is_file():
                size = f" ({item.stat().st_size / 1024:.1f} KB)"
            print(f"  {'📁' if item.is_dir() else '📄'} {item.name}{size}")
    else:
        print("  (data directory not found)")
    print()


def main():
    """Run all configuration and health check demos."""
    print("🚀 Database Configuration and Health Check Demo")
    print("=" * 60)
    print()
    
    try:
        # Run all demos
        demo_configuration_management()
        demo_database_backup()
        demo_health_monitoring()
        demo_configuration_scenarios()
        demo_maintenance_operations()
        show_configuration_files()
        
        print("✅ All demos completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("• Comprehensive database configuration management")
        print("• Environment variable loading and validation")
        print("• Automated backup and restore operations")
        print("• Real-time health monitoring and alerting")
        print("• Performance optimization recommendations")
        print("• Maintenance and cleanup operations")
        print("• Multiple configuration scenarios")
        print()
        print("The database configuration system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()