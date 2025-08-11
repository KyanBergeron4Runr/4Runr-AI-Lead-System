#!/usr/bin/env python3
"""
Database Logger for Lead Database Integration

This module provides comprehensive logging for all database operations,
sync activities, and migration processes. Follows the production logging
pattern established in the 4Runr system.
"""

import json
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import uuid
import traceback

class DatabaseLogger:
    """Production-grade logger for lead database operations"""
    
    def __init__(self, log_directory: str = "database_logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        (self.log_directory / "database_operations").mkdir(exist_ok=True)
        (self.log_directory / "sync_operations").mkdir(exist_ok=True)
        (self.log_directory / "migration_operations").mkdir(exist_ok=True)
        (self.log_directory / "performance_metrics").mkdir(exist_ok=True)
        (self.log_directory / "error_logs").mkdir(exist_ok=True)
        (self.log_directory / "monitoring_data").mkdir(exist_ok=True)
        
        self.session_id = str(uuid.uuid4())[:8]
        
        # Set up Python logging for console output
        self.logger = logging.getLogger('database_logger')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_database_operation(self, operation_type: str, lead_data: Dict, 
                             operation_result: Dict, performance_metrics: Dict = None) -> str:
        """Log database CRUD operations with performance metrics"""
        performance_metrics = performance_metrics or {}
        
        log_entry = {
            "log_type": "database_operation",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "operation_details": {
                "operation_type": operation_type,  # add_lead, get_lead, update_lead, delete_lead, search_leads
                "operation_id": str(uuid.uuid4())[:8],
                "execution_time_ms": performance_metrics.get("execution_time_ms", 0),
                "records_affected": operation_result.get("records_affected", 0),
                "success": operation_result.get("success", False),
                "error_message": operation_result.get("error", "")
            },
            "lead_identifier": {
                "lead_id": lead_data.get("id", ""),
                "name": lead_data.get("name", "Unknown"),
                "company": lead_data.get("company", "Unknown"),
                "email": lead_data.get("email", "")
            },
            "data_details": {
                "fields_processed": list(lead_data.keys()) if isinstance(lead_data, dict) else [],
                "data_size_bytes": len(str(lead_data)),
                "duplicate_detected": operation_result.get("duplicate_detected", False),
                "duplicate_action": operation_result.get("duplicate_action", "none")
            },
            "performance_metrics": {
                "execution_time_ms": performance_metrics.get("execution_time_ms", 0),
                "database_queries": performance_metrics.get("database_queries", 1),
                "memory_usage_mb": performance_metrics.get("memory_usage_mb", 0),
                "cpu_time_ms": performance_metrics.get("cpu_time_ms", 0)
            },
            "training_labels": {
                "operation_successful": operation_result.get("success", False),
                "performance_tier": self._classify_performance_tier(performance_metrics.get("execution_time_ms", 0)),
                "data_quality": self._assess_data_quality(lead_data),
                "complexity_level": self._assess_operation_complexity(operation_type, lead_data)
            }
        }
        
        # Log to console
        self.logger.info(f"Database {operation_type}: {operation_result.get('success', False)} "
                        f"({performance_metrics.get('execution_time_ms', 0)}ms)")
        
        # Save to file
        filename = f"db_op_{operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "database_operations" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
    
    def log_sync_operation(self, sync_type: str, sync_details: Dict, 
                          sync_results: Dict, leads_processed: List[Dict]) -> str:
        """Log Airtable sync operations with detailed results"""
        log_entry = {
            "log_type": "sync_operation",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "sync_details": {
                "sync_type": sync_type,  # to_airtable, from_airtable, bidirectional
                "sync_id": str(uuid.uuid4())[:8],
                "batch_size": sync_details.get("batch_size", 0),
                "total_leads": len(leads_processed),
                "execution_time_ms": sync_results.get("execution_time_ms", 0),
                "retry_attempts": sync_details.get("retry_attempts", 0),
                "sync_strategy": sync_details.get("sync_strategy", "default")
            },
            "sync_results": {
                "success": sync_results.get("success", False),
                "leads_synced": sync_results.get("leads_synced", 0),
                "leads_skipped": sync_results.get("leads_skipped", 0),
                "leads_failed": sync_results.get("leads_failed", 0),
                "conflicts_resolved": sync_results.get("conflicts_resolved", 0),
                "error_message": sync_results.get("error", ""),
                "airtable_rate_limited": sync_results.get("rate_limited", False)
            },
            "performance_metrics": {
                "avg_sync_time_per_lead_ms": sync_results.get("avg_sync_time_ms", 0),
                "api_calls_made": sync_results.get("api_calls", 0),
                "data_transferred_mb": sync_results.get("data_transferred_mb", 0),
                "memory_peak_mb": sync_results.get("memory_peak_mb", 0)
            },
            "leads_summary": [
                {
                    "lead_id": lead.get("id", ""),
                    "name": lead.get("name", "Unknown"),
                    "company": lead.get("company", "Unknown"),
                    "sync_status": lead.get("sync_status", "unknown"),
                    "last_sync": lead.get("last_sync", "")
                }
                for lead in leads_processed[:10]  # Limit to first 10 for log size
            ],
            "training_labels": {
                "sync_successful": sync_results.get("success", False),
                "sync_efficiency": self._assess_sync_efficiency(sync_results),
                "error_recovery": sync_details.get("retry_attempts", 0) > 0 and sync_results.get("success", False),
                "batch_optimization": self._assess_batch_performance(sync_details, sync_results)
            }
        }
        
        # Log to console
        success_rate = (sync_results.get("leads_synced", 0) / max(len(leads_processed), 1)) * 100
        self.logger.info(f"Sync {sync_type}: {sync_results.get('leads_synced', 0)}/{len(leads_processed)} "
                        f"leads ({success_rate:.1f}% success)")
        
        # Save to file
        filename = f"sync_{sync_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "sync_operations" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
    
    def log_migration_operation(self, migration_type: str, migration_details: Dict, 
                               migration_results: Dict, data_summary: Dict) -> str:
        """Log migration operations from JSON files to database"""
        log_entry = {
            "log_type": "migration_operation",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "migration_details": {
                "migration_type": migration_type,  # json_to_db, backup_creation, rollback
                "migration_id": str(uuid.uuid4())[:8],
                "source_files": migration_details.get("source_files", []),
                "backup_created": migration_details.get("backup_created", False),
                "backup_location": migration_details.get("backup_location", ""),
                "validation_enabled": migration_details.get("validation_enabled", True)
            },
            "migration_results": {
                "success": migration_results.get("success", False),
                "total_records_processed": migration_results.get("total_records", 0),
                "records_migrated": migration_results.get("records_migrated", 0),
                "records_skipped": migration_results.get("records_skipped", 0),
                "records_failed": migration_results.get("records_failed", 0),
                "duplicates_found": migration_results.get("duplicates_found", 0),
                "execution_time_ms": migration_results.get("execution_time_ms", 0),
                "error_message": migration_results.get("error", "")
            },
            "data_summary": {
                "source_file_sizes_mb": data_summary.get("source_file_sizes", {}),
                "data_quality_distribution": data_summary.get("quality_distribution", {}),
                "field_completeness": data_summary.get("field_completeness", {}),
                "validation_errors": data_summary.get("validation_errors", [])
            },
            "training_labels": {
                "migration_successful": migration_results.get("success", False),
                "data_integrity_maintained": migration_results.get("validation_passed", False),
                "performance_acceptable": migration_results.get("execution_time_ms", 0) < 60000,  # Under 1 minute
                "error_handling_effective": len(migration_results.get("error", "")) == 0 or migration_results.get("records_migrated", 0) > 0
            }
        }
        
        # Log to console
        success_rate = (migration_results.get("records_migrated", 0) / max(migration_results.get("total_records", 1), 1)) * 100
        self.logger.info(f"Migration {migration_type}: {migration_results.get('records_migrated', 0)}/{migration_results.get('total_records', 0)} "
                        f"records ({success_rate:.1f}% success)")
        
        # Save to file
        filename = f"migration_{migration_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "migration_operations" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath) 
   
    def log_error(self, error_type: str, error_details: Dict, context: Dict = None) -> str:
        """Log errors with full context and stack traces"""
        context = context or {}
        
        log_entry = {
            "log_type": "error_log",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "error_details": {
                "error_type": error_type,  # database_error, sync_error, migration_error, validation_error
                "error_id": str(uuid.uuid4())[:8],
                "error_message": error_details.get("message", ""),
                "error_code": error_details.get("code", ""),
                "stack_trace": error_details.get("stack_trace", ""),
                "severity": error_details.get("severity", "error")  # info, warning, error, critical
            },
            "context": {
                "operation_in_progress": context.get("operation", "unknown"),
                "lead_data": context.get("lead_data", {}),
                "system_state": context.get("system_state", {}),
                "user_action": context.get("user_action", ""),
                "environment": context.get("environment", "production")
            },
            "recovery_info": {
                "recovery_attempted": error_details.get("recovery_attempted", False),
                "recovery_successful": error_details.get("recovery_successful", False),
                "recovery_method": error_details.get("recovery_method", ""),
                "data_loss_occurred": error_details.get("data_loss", False)
            },
            "training_labels": {
                "error_severity": error_details.get("severity", "error"),
                "recoverable": error_details.get("recovery_successful", False),
                "user_error": error_type in ["validation_error", "input_error"],
                "system_error": error_type in ["database_error", "sync_error"]
            }
        }
        
        # Log to console with appropriate level
        severity = error_details.get("severity", "error")
        log_message = f"Error {error_type}: {error_details.get('message', 'Unknown error')}"
        
        if severity == "critical":
            self.logger.critical(log_message)
        elif severity == "error":
            self.logger.error(log_message)
        elif severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Save to file
        filename = f"error_{error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "error_logs" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
    
    def log_performance_metrics(self, operation_name: str, metrics: Dict, 
                               system_info: Dict = None) -> str:
        """Log detailed performance metrics for optimization"""
        system_info = system_info or {}
        
        log_entry = {
            "log_type": "performance_metrics",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "operation_info": {
                "operation_name": operation_name,
                "operation_id": str(uuid.uuid4())[:8],
                "start_time": metrics.get("start_time", ""),
                "end_time": metrics.get("end_time", ""),
                "total_duration_ms": metrics.get("total_duration_ms", 0)
            },
            "performance_data": {
                "cpu_usage_percent": metrics.get("cpu_usage", 0),
                "memory_usage_mb": metrics.get("memory_usage_mb", 0),
                "memory_peak_mb": metrics.get("memory_peak_mb", 0),
                "disk_io_mb": metrics.get("disk_io_mb", 0),
                "network_io_mb": metrics.get("network_io_mb", 0),
                "database_queries": metrics.get("database_queries", 0),
                "api_calls": metrics.get("api_calls", 0)
            },
            "system_info": {
                "database_size_mb": system_info.get("database_size_mb", 0),
                "total_leads": system_info.get("total_leads", 0),
                "pending_syncs": system_info.get("pending_syncs", 0),
                "active_connections": system_info.get("active_connections", 0),
                "system_load": system_info.get("system_load", 0)
            },
            "training_labels": {
                "performance_tier": self._classify_performance_tier(metrics.get("total_duration_ms", 0)),
                "resource_efficiency": self._assess_resource_efficiency(metrics),
                "scalability_indicator": self._assess_scalability(metrics, system_info),
                "optimization_needed": metrics.get("total_duration_ms", 0) > 5000  # Over 5 seconds
            }
        }
        
        # Log to console
        self.logger.info(f"Performance {operation_name}: {metrics.get('total_duration_ms', 0)}ms "
                        f"(CPU: {metrics.get('cpu_usage', 0)}%, Memory: {metrics.get('memory_usage_mb', 0)}MB)")
        
        # Save to file
        filename = f"perf_{operation_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "performance_metrics" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
    
    def log_monitoring_data(self, monitoring_type: str, data: Dict, 
                           alerts: List[Dict] = None) -> str:
        """Log system monitoring data and alerts"""
        alerts = alerts or []
        
        log_entry = {
            "log_type": "monitoring_data",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "monitoring_info": {
                "monitoring_type": monitoring_type,  # health_check, sync_status, database_stats
                "monitoring_id": str(uuid.uuid4())[:8],
                "collection_interval_seconds": data.get("collection_interval", 300),
                "data_points": len(data.get("metrics", []))
            },
            "system_health": {
                "database_responsive": data.get("database_responsive", True),
                "airtable_accessible": data.get("airtable_accessible", True),
                "sync_queue_size": data.get("sync_queue_size", 0),
                "error_rate_percent": data.get("error_rate", 0),
                "average_response_time_ms": data.get("avg_response_time", 0)
            },
            "statistics": {
                "total_leads": data.get("total_leads", 0),
                "leads_added_today": data.get("leads_added_today", 0),
                "successful_syncs_today": data.get("successful_syncs_today", 0),
                "failed_syncs_today": data.get("failed_syncs_today", 0),
                "database_size_mb": data.get("database_size_mb", 0)
            },
            "alerts": alerts,
            "training_labels": {
                "system_healthy": len([a for a in alerts if a.get("severity") == "critical"]) == 0,
                "performance_acceptable": data.get("avg_response_time", 0) < 1000,
                "sync_efficiency": data.get("error_rate", 0) < 5,  # Less than 5% error rate
                "capacity_adequate": data.get("sync_queue_size", 0) < 100
            }
        }
        
        # Log alerts to console
        for alert in alerts:
            severity = alert.get("severity", "info")
            message = alert.get("message", "Unknown alert")
            if severity == "critical":
                self.logger.critical(f"ALERT: {message}")
            elif severity == "warning":
                self.logger.warning(f"ALERT: {message}")
            else:
                self.logger.info(f"ALERT: {message}")
        
        # Save to file
        filename = f"monitor_{monitoring_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id}.json"
        filepath = self.log_directory / "monitoring_data" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
    
    def create_daily_summary(self, date: str = None) -> str:
        """Create a daily summary report from all log data"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        summary_data = {
            "summary_info": {
                "date": date,
                "created_at": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            "operation_summary": {
                "total_database_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "average_operation_time_ms": 0
            },
            "sync_summary": {
                "total_sync_operations": 0,
                "leads_synced": 0,
                "sync_success_rate": 0,
                "average_sync_time_ms": 0
            },
            "error_summary": {
                "total_errors": 0,
                "critical_errors": 0,
                "recoverable_errors": 0,
                "most_common_errors": []
            },
            "performance_summary": {
                "peak_memory_usage_mb": 0,
                "peak_cpu_usage_percent": 0,
                "slowest_operation_ms": 0,
                "total_api_calls": 0
            }
        }
        
        # Analyze log files from the specified date
        date_prefix = date.replace('-', '')
        
        # Process database operations
        db_ops_dir = self.log_directory / "database_operations"
        if db_ops_dir.exists():
            for log_file in db_ops_dir.glob(f"*{date_prefix}*.json"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        summary_data["operation_summary"]["total_database_operations"] += 1
                        if log_data.get("operation_details", {}).get("success", False):
                            summary_data["operation_summary"]["successful_operations"] += 1
                        else:
                            summary_data["operation_summary"]["failed_operations"] += 1
                except Exception:
                    continue
        
        # Process sync operations
        sync_ops_dir = self.log_directory / "sync_operations"
        if sync_ops_dir.exists():
            for log_file in sync_ops_dir.glob(f"*{date_prefix}*.json"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        summary_data["sync_summary"]["total_sync_operations"] += 1
                        summary_data["sync_summary"]["leads_synced"] += log_data.get("sync_results", {}).get("leads_synced", 0)
                except Exception:
                    continue
        
        # Calculate success rates
        total_ops = summary_data["operation_summary"]["total_database_operations"]
        if total_ops > 0:
            success_rate = (summary_data["operation_summary"]["successful_operations"] / total_ops) * 100
            summary_data["operation_summary"]["success_rate_percent"] = round(success_rate, 2)
        
        # Save summary
        filename = f"daily_summary_{date}_{self.session_id}.json"
        filepath = self.log_directory / "monitoring_data" / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Daily summary created: {total_ops} operations, "
                        f"{summary_data['sync_summary']['leads_synced']} leads synced")
        
        return str(filepath)
    
    # Helper methods for training labels and assessments
    def _classify_performance_tier(self, execution_time_ms: float) -> str:
        """Classify performance into tiers"""
        if execution_time_ms < 100:
            return "excellent"
        elif execution_time_ms < 500:
            return "good"
        elif execution_time_ms < 2000:
            return "acceptable"
        elif execution_time_ms < 5000:
            return "slow"
        else:
            return "very_slow"
    
    def _assess_data_quality(self, lead_data: Dict) -> str:
        """Assess quality of lead data"""
        if not isinstance(lead_data, dict):
            return "invalid"
        
        required_fields = ["name", "company"]
        optional_fields = ["email", "linkedin_url", "title", "company_description"]
        
        required_score = sum(1 for field in required_fields if lead_data.get(field))
        optional_score = sum(1 for field in optional_fields if lead_data.get(field))
        
        total_score = (required_score / len(required_fields)) * 0.7 + (optional_score / len(optional_fields)) * 0.3
        
        if total_score >= 0.8:
            return "high"
        elif total_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _assess_operation_complexity(self, operation_type: str, lead_data: Dict) -> str:
        """Assess complexity of database operation"""
        complexity_scores = {
            "add_lead": 2,
            "get_lead": 1,
            "update_lead": 2,
            "delete_lead": 1,
            "search_leads": 3,
            "find_duplicates": 4
        }
        
        base_score = complexity_scores.get(operation_type, 2)
        
        # Adjust based on data size
        if isinstance(lead_data, dict):
            data_size = len(str(lead_data))
            if data_size > 5000:
                base_score += 1
            elif data_size > 1000:
                base_score += 0.5
        
        if base_score >= 4:
            return "high"
        elif base_score >= 2.5:
            return "medium"
        else:
            return "low"
    
    def _assess_sync_efficiency(self, sync_results: Dict) -> str:
        """Assess efficiency of sync operation"""
        total_leads = sync_results.get("leads_synced", 0) + sync_results.get("leads_failed", 0)
        if total_leads == 0:
            return "unknown"
        
        success_rate = sync_results.get("leads_synced", 0) / total_leads
        avg_time = sync_results.get("avg_sync_time_ms", 0)
        
        if success_rate >= 0.95 and avg_time < 500:
            return "excellent"
        elif success_rate >= 0.85 and avg_time < 1000:
            return "good"
        elif success_rate >= 0.7 and avg_time < 2000:
            return "acceptable"
        else:
            return "poor"
    
    def _assess_batch_performance(self, sync_details: Dict, sync_results: Dict) -> str:
        """Assess batch processing performance"""
        batch_size = sync_details.get("batch_size", 1)
        total_time = sync_results.get("execution_time_ms", 0)
        
        if batch_size <= 1:
            return "no_batching"
        
        time_per_item = total_time / batch_size if batch_size > 0 else float('inf')
        
        if time_per_item < 200:
            return "optimal"
        elif time_per_item < 500:
            return "good"
        elif time_per_item < 1000:
            return "acceptable"
        else:
            return "inefficient"
    
    def _assess_resource_efficiency(self, metrics: Dict) -> str:
        """Assess resource usage efficiency"""
        cpu_usage = metrics.get("cpu_usage", 0)
        memory_usage = metrics.get("memory_usage_mb", 0)
        duration = metrics.get("total_duration_ms", 0)
        
        # Simple efficiency score based on resource usage vs time
        if cpu_usage < 20 and memory_usage < 100 and duration < 1000:
            return "excellent"
        elif cpu_usage < 50 and memory_usage < 500 and duration < 5000:
            return "good"
        elif cpu_usage < 80 and memory_usage < 1000 and duration < 10000:
            return "acceptable"
        else:
            return "poor"
    
    def _assess_scalability(self, metrics: Dict, system_info: Dict) -> str:
        """Assess system scalability indicators"""
        total_leads = system_info.get("total_leads", 0)
        duration = metrics.get("total_duration_ms", 0)
        memory_usage = metrics.get("memory_usage_mb", 0)
        
        # Assess if performance scales well with data size
        if total_leads < 1000:
            return "small_scale"
        elif total_leads < 10000:
            if duration < 2000 and memory_usage < 200:
                return "scales_well"
            else:
                return "scaling_issues"
        else:
            if duration < 5000 and memory_usage < 500:
                return "scales_excellently"
            elif duration < 10000 and memory_usage < 1000:
                return "scales_adequately"
            else:
                return "scaling_problems"


# Global database logger instance
database_logger = DatabaseLogger()


def log_database_event(event_type: str, operation_data: Dict, results: Dict, 
                      additional_data: Dict = None) -> str:
    """Convenience function to log database events"""
    additional_data = additional_data or {}
    
    if event_type == "database_operation":
        return database_logger.log_database_operation(
            additional_data.get("operation_type", "unknown"),
            operation_data, results, additional_data.get("performance_metrics", {})
        )
    elif event_type == "sync_operation":
        return database_logger.log_sync_operation(
            additional_data.get("sync_type", "unknown"),
            additional_data.get("sync_details", {}),
            results, additional_data.get("leads_processed", [])
        )
    elif event_type == "migration_operation":
        return database_logger.log_migration_operation(
            additional_data.get("migration_type", "unknown"),
            additional_data.get("migration_details", {}),
            results, additional_data.get("data_summary", {})
        )
    elif event_type == "error":
        return database_logger.log_error(
            additional_data.get("error_type", "unknown"),
            results, additional_data.get("context", {})
        )
    elif event_type == "performance":
        return database_logger.log_performance_metrics(
            additional_data.get("operation_name", "unknown"),
            results, additional_data.get("system_info", {})
        )
    elif event_type == "monitoring":
        return database_logger.log_monitoring_data(
            additional_data.get("monitoring_type", "unknown"),
            results, additional_data.get("alerts", [])
        )
    else:
        raise ValueError(f"Unknown event type: {event_type}")


# Performance monitoring decorator
def monitor_performance(operation_name: str):
    """Decorator to automatically monitor performance of database operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                
                # Log performance metrics
                metrics = {
                    "start_time": start_timestamp,
                    "end_time": datetime.now().isoformat(),
                    "total_duration_ms": execution_time_ms,
                    "success": True
                }
                
                database_logger.log_performance_metrics(operation_name, metrics)
                
                return result
                
            except Exception as e:
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                
                # Log error with performance context
                error_details = {
                    "message": str(e),
                    "stack_trace": traceback.format_exc(),
                    "severity": "error"
                }
                
                context = {
                    "operation": operation_name,
                    "execution_time_ms": execution_time_ms
                }
                
                database_logger.log_error("performance_error", error_details, context)
                
                raise
        
        return wrapper
    return decorator