#!/usr/bin/env python3
"""
System Health Check

Quick health check to verify the system is working properly.
"""

import sys
import json
from pathlib import Path
from production_db_manager import db_manager

def check_system_health():
    """Check system health and report issues."""
    issues = []
    warnings = []
    
    # Check database
    try:
        stats = db_manager.get_database_stats()
        
        if stats['total_leads'] == 0:
            issues.append("No leads in database")
        elif stats['total_leads'] < 10:
            warnings.append(f"Low lead count: {stats['total_leads']}")
        
        if stats['email_percentage'] < 50:
            warnings.append(f"Low email percentage: {stats['email_percentage']}%")
        
        print(f"✅ Database: {stats['total_leads']} leads, {stats['email_percentage']}% with emails")
        
    except Exception as e:
        issues.append(f"Database error: {e}")
    
    # Check log files
    log_dir = Path("logs")
    if log_dir.exists():
        recent_logs = list(log_dir.glob("*.log"))
        if recent_logs:
            print(f"✅ Logs: {len(recent_logs)} log files found")
        else:
            warnings.append("No recent log files")
    else:
        warnings.append("Log directory not found")
    
    # Report results
    if issues:
        print(f"❌ Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        return False
    elif warnings:
        print(f"⚠️ Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
        return True
    else:
        print("🎉 System health check passed!")
        return True

if __name__ == "__main__":
    healthy = check_system_health()
    sys.exit(0 if healthy else 1)
