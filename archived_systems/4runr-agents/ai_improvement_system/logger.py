#!/usr/bin/env python3
"""
AI Improvement System Logger

Centralized logging system for the AI improvement analysis engine.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class AIImprovementLogger:
    """Centralized logger for the AI improvement system"""
    
    def __init__(self, name: str = "ai-improvement-system", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with appropriate handlers and formatting"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self._get_log_file_path()
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _get_log_file_path(self) -> Path:
        """Get the log file path, creating directories if needed"""
        log_dir = Path("4runr-agents/ai_improvement_system/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daily log files
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"ai_improvement_{date_str}.log"
        
        return log_file
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def log_analysis_start(self, analysis_type: str, parameters: dict):
        """Log the start of an analysis"""
        self.info(f"🔍 Starting {analysis_type} analysis")
        self.info(f"   Parameters: {parameters}")
    
    def log_analysis_complete(self, analysis_type: str, duration: float, results_summary: dict):
        """Log the completion of an analysis"""
        self.info(f"✅ {analysis_type} analysis completed in {duration:.2f} seconds")
        self.info(f"   Results: {results_summary}")
    
    def log_analysis_error(self, analysis_type: str, error: Exception):
        """Log an analysis error"""
        self.error(f"❌ {analysis_type} analysis failed: {str(error)}")
        self.error(f"   Error type: {type(error).__name__}")
    
    def log_report_generation(self, report_type: str, output_path: Path):
        """Log report generation"""
        self.info(f"📊 Generated {report_type} report: {output_path}")
    
    def log_system_health(self, health_status: str, details: dict):
        """Log system health status"""
        status_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "needs_attention": "🟠",
            "critical": "🔴"
        }
        
        emoji = status_emoji.get(health_status, "⚪")
        self.info(f"{emoji} System health: {health_status.upper()}")
        
        if details:
            for key, value in details.items():
                self.info(f"   {key}: {value}")
    
    def log_recommendation(self, recommendation_id: str, priority: str, title: str):
        """Log a generated recommendation"""
        priority_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        emoji = priority_emoji.get(priority, "⚪")
        self.info(f"{emoji} Recommendation [{recommendation_id}]: {title} (Priority: {priority})")
    
    def log_scheduler_event(self, event_type: str, details: Optional[dict] = None):
        """Log scheduler events"""
        self.info(f"⏰ Scheduler: {event_type}")
        if details:
            for key, value in details.items():
                self.info(f"   {key}: {value}")
    
    def log_data_collection(self, log_type: str, count: int, date_range: str):
        """Log data collection results"""
        self.info(f"📊 Collected {count} {log_type} logs from {date_range}")
    
    def log_archive_operation(self, operation: str, file_count: int, destination: Path):
        """Log archive operations"""
        self.info(f"📦 {operation}: {file_count} files to {destination}")

# Global logger instance
system_logger = AIImprovementLogger()

def get_logger(name: Optional[str] = None) -> AIImprovementLogger:
    """Get a logger instance"""
    if name:
        return AIImprovementLogger(name)
    return system_logger

def log_system_startup():
    """Log system startup information"""
    system_logger.info("🚀 AI Improvement System Starting Up")
    system_logger.info(f"   Python version: {sys.version}")
    system_logger.info(f"   Working directory: {Path.cwd()}")
    system_logger.info(f"   Log file: {system_logger._get_log_file_path()}")

def log_system_shutdown():
    """Log system shutdown"""
    system_logger.info("🛑 AI Improvement System Shutting Down")

# Log startup when module is imported
log_system_startup()