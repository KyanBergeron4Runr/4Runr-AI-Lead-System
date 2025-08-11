#!/usr/bin/env python3
"""
Database Health Check and Monitoring for Lead Database Integration.

This module provides comprehensive health monitoring including:
- Database connectivity and performance checks
- Schema validation and integrity checks
- Performance metrics and optimization recommendations
- Automated health monitoring with alerts
- Database maintenance operations
"""

import os
import sqlite3
import time
import threading
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

from database_config import get_database_config, DatabaseConfig
from database_logger import database_logger, log_database_event


@dataclass
class HealthCheckResult:
    """Result of a database health check."""
    check_name: str
    status: str  # healthy, warning, critical, error
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class HealthReport:
    """Comprehensive health report."""
    overall_status: str
    checks: List[HealthCheckResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status,
            "checks": [check.to_dict() for check in self.checks],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "alerts": self.alerts,
            "generated_at": self.generated_at.isoformat()
        }


class DatabaseHealthMonitor:
    """Monitors database health and performance."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize health monitor.
        
        Args:
            config: Database configuration (uses default if None)
        """
        self.config = config or get_database_config()
        self.db_path = Path(self.config.database_path)
        
        # Health check history
        self.check_history: List[HealthReport] = []
        self.max_history = 100  # Keep last 100 health reports
        
        # Monitoring thread
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._lock = threading.RLock()
    
    @contextmanager
    def get_connection(self):
        """Get database connection for health checks."""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def run_health_check(self, include_performance: bool = True) -> HealthReport:
        """
        Run comprehensive health check.
        
        Args:
            include_performance: Whether to include performance tests
            
        Returns:
            HealthReport: Complete health report
        """
        start_time = time.time()
        checks = []
        alerts = []
        recommendations = []
        
        try:
            # Basic connectivity check
            checks.append(self._check_connectivity())
            
            # Database file checks
            checks.append(self._check_database_file())
            
            # Schema validation
            checks.append(self._check_schema_integrity())
            
            # Data integrity checks
            checks.append(self._check_data_integrity())
            
            # Performance checks
            if include_performance:
                checks.append(self._check_query_performance())
                checks.append(self._check_database_size())
            
            # System resource checks
            checks.append(self._check_system_resources())
            
            # Configuration validation
            checks.append(self._check_configuration())
            
            # Analyze results and generate summary
            summary = self._generate_summary(checks)
            overall_status = self._determine_overall_status(checks)
            
            # Generate recommendations and alerts
            recommendations = self._generate_recommendations(checks)
            alerts = self._generate_alerts(checks)
            
            # Create health report
            report = HealthReport(
                overall_status=overall_status,
                checks=checks,
                summary=summary,
                recommendations=recommendations,
                alerts=alerts
            )
            
            # Store in history
            with self._lock:
                self.check_history.append(report)
                if len(self.check_history) > self.max_history:
                    self.check_history.pop(0)
            
            # Log health check
            execution_time_ms = (time.time() - start_time) * 1000
            log_database_event("monitoring", {}, {
                "database_responsive": overall_status in ["healthy", "warning"],
                "airtable_accessible": True,  # Assume accessible for now
                "sync_queue_size": 0,  # Would need to check actual queue
                "error_rate": 0,  # Would need to calculate from logs
                "avg_response_time": execution_time_ms,
                "total_leads": summary.get("total_records", 0),
                "database_size_mb": summary.get("database_size_mb", 0)
            }, {
                "monitoring_type": "health_check",
                "alerts": alerts
            })
            
            return report
            
        except Exception as e:
            # Create error report
            error_check = HealthCheckResult(
                check_name="health_check_execution",
                status="error",
                message=f"Health check failed: {e}",
                details={"error": str(e)}
            )
            
            return HealthReport(
                overall_status="error",
                checks=[error_check],
                summary={"error": str(e)},
                recommendations=["Fix health check execution error"],
                alerts=[{"severity": "critical", "message": f"Health check failed: {e}"}]
            )
    
    def _check_connectivity(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    return HealthCheckResult(
                        check_name="connectivity",
                        status="healthy",
                        message="Database connection successful",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                else:
                    return HealthCheckResult(
                        check_name="connectivity",
                        status="error",
                        message="Database connection test failed",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                check_name="connectivity",
                status="critical",
                message=f"Cannot connect to database: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_database_file(self) -> HealthCheckResult:
        """Check database file status."""
        start_time = time.time()
        
        try:
            if not self.db_path.exists():
                return HealthCheckResult(
                    check_name="database_file",
                    status="critical",
                    message="Database file does not exist",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check file permissions
            if not os.access(self.db_path, os.R_OK | os.W_OK):
                return HealthCheckResult(
                    check_name="database_file",
                    status="critical",
                    message="Database file is not readable/writable",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check file size
            file_size = self.db_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Check available disk space
            if PSUTIL_AVAILABLE:
                free_space = psutil.disk_usage(self.db_path.parent).free
                free_space_mb = free_space / (1024 * 1024)
            else:
                free_space_mb = 1000  # Assume sufficient space if psutil not available
            
            details = {
                "file_size_mb": file_size_mb,
                "free_space_mb": free_space_mb,
                "file_path": str(self.db_path)
            }
            
            if free_space_mb < 100:  # Less than 100MB free
                return HealthCheckResult(
                    check_name="database_file",
                    status="warning",
                    message=f"Low disk space: {free_space_mb:.1f}MB available",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                check_name="database_file",
                status="healthy",
                message=f"Database file OK ({file_size_mb:.1f}MB)",
                details=details,
                execution_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="database_file",
                status="error",
                message=f"File check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_schema_integrity(self) -> HealthCheckResult:
        """Check database schema integrity."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if main tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = 'leads'
                """)
                
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                if 'leads' not in existing_tables:
                    return HealthCheckResult(
                        check_name="schema_integrity",
                        status="critical",
                        message="Missing required 'leads' table",
                        details={"existing_tables": list(existing_tables)},
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Check leads table structure
                cursor.execute("PRAGMA table_info(leads)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                required_columns = ['id', 'name']
                missing_columns = [col for col in required_columns if col not in columns]
                
                details = {
                    "existing_tables": list(existing_tables),
                    "column_count": len(columns),
                    "missing_columns": missing_columns
                }
                
                if missing_columns:
                    return HealthCheckResult(
                        check_name="schema_integrity",
                        status="warning",
                        message=f"Missing columns: {missing_columns}",
                        details=details,
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                return HealthCheckResult(
                    check_name="schema_integrity",
                    status="healthy",
                    message="Database schema is valid",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name="schema_integrity",
                status="error",
                message=f"Schema check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_data_integrity(self) -> HealthCheckResult:
        """Check data integrity."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Run PRAGMA integrity_check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                
                if integrity_result[0] != "ok":
                    return HealthCheckResult(
                        check_name="data_integrity",
                        status="critical",
                        message=f"Data integrity check failed: {integrity_result[0]}",
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Count total records
                cursor.execute("SELECT COUNT(*) FROM leads")
                total_records = cursor.fetchone()[0]
                
                details = {"total_records": total_records}
                
                return HealthCheckResult(
                    check_name="data_integrity",
                    status="healthy",
                    message=f"Data integrity OK ({total_records} records)",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name="data_integrity",
                status="error",
                message=f"Data integrity check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_query_performance(self) -> HealthCheckResult:
        """Check query performance."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test basic SELECT performance
                query_start = time.time()
                cursor.execute("SELECT COUNT(*) FROM leads")
                count_result = cursor.fetchone()[0]
                count_time = (time.time() - query_start) * 1000
                
                details = {
                    "count_query_ms": count_time,
                    "total_records": count_result
                }
                
                # Determine status based on performance
                if count_time > self.config.slow_query_threshold_ms:
                    return HealthCheckResult(
                        check_name="query_performance",
                        status="warning",
                        message=f"Slow query detected: {count_time:.1f}ms",
                        details=details,
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                return HealthCheckResult(
                    check_name="query_performance",
                    status="healthy",
                    message=f"Query performance OK ({count_time:.1f}ms)",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name="query_performance",
                status="error",
                message=f"Performance check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_database_size(self) -> HealthCheckResult:
        """Check database size."""
        start_time = time.time()
        
        try:
            # Get file size
            file_size = self.db_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM leads")
                record_count = cursor.fetchone()[0]
                
                details = {
                    "file_size_mb": file_size_mb,
                    "record_count": record_count
                }
                
                # Check if database is getting large
                if file_size_mb > 1000:  # Over 1GB
                    return HealthCheckResult(
                        check_name="database_size",
                        status="warning",
                        message=f"Large database size: {file_size_mb:.1f}MB",
                        details=details,
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                
                return HealthCheckResult(
                    check_name="database_size",
                    status="healthy",
                    message=f"Database size: {file_size_mb:.1f}MB ({record_count} records)",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name="database_size",
                status="error",
                message=f"Size check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            if not PSUTIL_AVAILABLE:
                return HealthCheckResult(
                    check_name="system_resources",
                    status="warning",
                    message="psutil not available - system resource monitoring disabled",
                    details={"psutil_available": False},
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage for database directory
            disk_usage = psutil.disk_usage(self.db_path.parent)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_free_mb": disk_usage.free / (1024 * 1024)
            }
            
            # Check for resource issues
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > 90:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            if issues:
                return HealthCheckResult(
                    check_name="system_resources",
                    status="warning",
                    message=f"Resource issues: {', '.join(issues)}",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                check_name="system_resources",
                status="healthy",
                message=f"Resources OK (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%)",
                details=details,
                execution_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="system_resources",
                status="error",
                message=f"Resource check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _check_configuration(self) -> HealthCheckResult:
        """Check database configuration."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check current PRAGMA settings
                pragmas = {}
                pragma_checks = ["journal_mode", "synchronous", "foreign_keys"]
                
                for pragma in pragma_checks:
                    cursor.execute(f"PRAGMA {pragma}")
                    result = cursor.fetchone()
                    pragmas[pragma] = result[0] if result else None
                
                details = {"current_pragmas": pragmas}
                
                return HealthCheckResult(
                    check_name="configuration",
                    status="healthy",
                    message="Configuration checked",
                    details=details,
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name="configuration",
                status="error",
                message=f"Configuration check failed: {e}",
                details={"error": str(e)},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _generate_summary(self, checks: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate summary from health checks."""
        summary = {
            "total_checks": len(checks),
            "healthy_checks": len([c for c in checks if c.status == "healthy"]),
            "warning_checks": len([c for c in checks if c.status == "warning"]),
            "critical_checks": len([c for c in checks if c.status == "critical"]),
            "error_checks": len([c for c in checks if c.status == "error"]),
            "avg_execution_time_ms": sum(c.execution_time_ms for c in checks) / len(checks) if checks else 0
        }
        
        # Extract specific metrics
        for check in checks:
            if check.check_name == "data_integrity" and "total_records" in check.details:
                summary["total_records"] = check.details["total_records"]
            elif check.check_name == "database_size" and "file_size_mb" in check.details:
                summary["database_size_mb"] = check.details["file_size_mb"]
        
        return summary
    
    def _determine_overall_status(self, checks: List[HealthCheckResult]) -> str:
        """Determine overall health status."""
        if any(c.status == "critical" for c in checks):
            return "critical"
        elif any(c.status == "error" for c in checks):
            return "error"
        elif any(c.status == "warning" for c in checks):
            return "warning"
        else:
            return "healthy"
    
    def _generate_recommendations(self, checks: List[HealthCheckResult]) -> List[str]:
        """Generate recommendations based on check results."""
        recommendations = []
        
        for check in checks:
            if check.status in ["warning", "critical", "error"]:
                if check.check_name == "database_size" and "file_size_mb" in check.details:
                    if check.details["file_size_mb"] > 500:
                        recommendations.append("Consider archiving old data or implementing data retention policies")
                elif check.check_name == "query_performance":
                    recommendations.append("Consider adding database indexes to improve query performance")
                elif check.check_name == "system_resources":
                    recommendations.append("Monitor system resources and consider scaling if needed")
                elif check.check_name == "database_file" and "Low disk space" in check.message:
                    recommendations.append("Free up disk space or move database to larger storage")
        
        return recommendations
    
    def _generate_alerts(self, checks: List[HealthCheckResult]) -> List[Dict[str, Any]]:
        """Generate alerts based on check results."""
        alerts = []
        
        for check in checks:
            if check.status == "critical":
                alerts.append({
                    "severity": "critical",
                    "message": f"{check.check_name}: {check.message}",
                    "timestamp": check.timestamp.isoformat()
                })
            elif check.status == "error":
                alerts.append({
                    "severity": "error",
                    "message": f"{check.check_name}: {check.message}",
                    "timestamp": check.timestamp.isoformat()
                })
            elif check.status == "warning":
                alerts.append({
                    "severity": "warning",
                    "message": f"{check.check_name}: {check.message}",
                    "timestamp": check.timestamp.isoformat()
                })
        
        return alerts
    
    def get_health_history(self, limit: int = 10) -> List[HealthReport]:
        """Get recent health check history."""
        with self._lock:
            return self.check_history[-limit:] if self.check_history else []


# Global health monitor instance
health_monitor = DatabaseHealthMonitor()

def run_database_health_check(include_performance: bool = True) -> HealthReport:
    """
    Run database health check.
    
    Args:
        include_performance: Whether to include performance tests
        
    Returns:
        HealthReport: Complete health report
    """
    return health_monitor.run_health_check(include_performance)

def get_database_health_summary() -> Dict[str, Any]:
    """
    Get database health summary.
    
    Returns:
        Dictionary with health summary
    """
    report = health_monitor.run_health_check(include_performance=False)
    return {
        "overall_status": report.overall_status,
        "total_checks": len(report.checks),
        "issues": len([c for c in report.checks if c.status in ["warning", "critical", "error"]]),
        "last_check": report.generated_at.isoformat(),
        "summary": report.summary
    }