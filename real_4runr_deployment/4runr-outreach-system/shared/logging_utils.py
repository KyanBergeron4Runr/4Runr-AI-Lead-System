"""
Logging utilities for the 4Runr Autonomous Outreach System.

Provides structured logging with engagement tracking and JSON log export capabilities.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from .config import config


class OutreachLogger:
    """Enhanced logger for outreach system with engagement tracking."""
    
    def __init__(self, module_name: str):
        """
        Initialize the outreach logger.
        
        Args:
            module_name: Name of the module using this logger
        """
        self.module_name = module_name
        self.logger = logging.getLogger(module_name)
        self._setup_logging()
        
        # Create logs directory if it doesn't exist
        log_config = config.get_logging_config()
        self.log_directory = Path(log_config['log_directory'])
        self.log_directory.mkdir(exist_ok=True)
        
        self.save_json_logs = log_config['save_json_logs']
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        log_config = config.get_logging_config()
        
        # Set log level
        level = getattr(logging, log_config['level'].upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def log_module_activity(self, action: str, lead_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log module activity with lead traceability.
        
        Args:
            action: Action being performed
            lead_id: Lead record ID
            status: Status of the action (success, error, skip, etc.)
            details: Additional details about the action
        """
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'module': self.module_name,
            'action': action,
            'lead_id': lead_id,
            'status': status,
            'details': details or {}
        }
        
        # Log to console
        message = f"[{action}] Lead {lead_id}: {status}"
        if details:
            message += f" - {details}"
        
        if status.lower() in ['error', 'failed']:
            self.logger.error(message)
        elif status.lower() in ['warning', 'skip', 'skipped']:
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Save to JSON log if enabled
        if self.save_json_logs:
            self._save_json_log(log_entry)
    
    def save_engagement_log(self, engagement_data: Dict[str, Any]) -> None:
        """
        Save detailed engagement log for analysis.
        
        Args:
            engagement_data: Comprehensive engagement data
        """
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'module': self.module_name,
            'type': 'engagement',
            **engagement_data
        }
        
        # Log summary to console
        lead_id = engagement_data.get('lead_id', 'unknown')
        status = engagement_data.get('status', 'unknown')
        method = engagement_data.get('delivery_method', 'unknown')
        
        self.logger.info(f"[ENGAGEMENT] Lead {lead_id}: {status} via {method}")
        
        # Save detailed log
        if self.save_json_logs:
            filename = f"engagement_log_{datetime.date.today().isoformat()}.json"
            self._append_json_log(filename, log_entry)
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with context information.
        
        Args:
            error: Exception that occurred
            context: Context information about the error
        """
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'module': self.module_name,
            'type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        # Log to console
        lead_id = context.get('lead_id', 'unknown')
        action = context.get('action', 'unknown')
        self.logger.error(f"[ERROR] {action} for lead {lead_id}: {str(error)}")
        
        # Save to JSON log
        if self.save_json_logs:
            filename = f"error_log_{datetime.date.today().isoformat()}.json"
            self._append_json_log(filename, log_entry)
    
    def log_pipeline_start(self, total_leads: int) -> None:
        """Log the start of pipeline processing."""
        self.logger.info(f"[PIPELINE START] Processing {total_leads} leads with {self.module_name}")
    
    def log_pipeline_complete(self, processed: int, successful: int, errors: int) -> None:
        """Log pipeline completion statistics."""
        self.logger.info(f"[PIPELINE COMPLETE] Processed: {processed}, Successful: {successful}, Errors: {errors}")
    
    def log_batch_progress(self, current: int, total: int) -> None:
        """Log batch processing progress."""
        percentage = (current / total) * 100 if total > 0 else 0
        self.logger.info(f"[PROGRESS] {current}/{total} ({percentage:.1f}%)")
    
    def _save_json_log(self, log_entry: Dict[str, Any]) -> None:
        """Save a single log entry to JSON file."""
        filename = f"{self.module_name}_log_{datetime.date.today().isoformat()}.json"
        self._append_json_log(filename, log_entry)
    
    def _append_json_log(self, filename: str, log_entry: Dict[str, Any]) -> None:
        """Append log entry to JSON file."""
        try:
            log_file = self.log_directory / filename
            
            # Read existing logs
            logs = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            
            # Append new log entry
            logs.append(log_entry)
            
            # Write back to file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save JSON log: {str(e)}")


def get_logger(module_name: str) -> OutreachLogger:
    """
    Get a logger instance for a specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Configured OutreachLogger instance
    """
    return OutreachLogger(module_name)