#!/usr/bin/env python3
"""
AI Improvement System Configuration

Centralized configuration management for the automated AI improvement system.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class AnalysisConfig:
    """Configuration for AI analysis parameters"""
    # Analysis settings
    analysis_days_back: int = 7
    minimum_logs_required: int = 5
    confidence_threshold: float = 0.8
    
    # Report settings
    report_retention_days: int = 90
    archive_after_days: int = 30
    max_reports_per_directory: int = 50
    
    # Alert thresholds
    critical_success_rate: float = 0.3  # Below 30% triggers critical alert
    warning_success_rate: float = 0.5   # Below 50% triggers warning
    critical_approval_rate: float = 0.4  # Below 40% triggers critical alert
    warning_approval_rate: float = 0.6   # Below 60% triggers warning
    
    # Performance thresholds
    max_processing_time: float = 60.0   # Seconds
    warning_processing_time: float = 45.0  # Seconds
    
    # Recommendation settings
    max_recommendations: int = 10
    high_priority_threshold: float = 0.7
    medium_priority_threshold: float = 0.4

@dataclass
class SystemPaths:
    """System directory and file paths"""
    # Base directories
    base_dir: Path = Path("4runr-agents")
    production_logs_dir: Path = Path("4runr-agents/production_logs")
    analysis_reports_dir: Path = Path("4runr-agents/ai_analysis_reports")
    improvement_system_dir: Path = Path("4runr-agents/ai_improvement_system")
    
    # Report subdirectories
    weekly_reports_dir: Path = Path("4runr-agents/ai_analysis_reports/weekly")
    monthly_reports_dir: Path = Path("4runr-agents/ai_analysis_reports/monthly")
    archive_dir: Path = Path("4runr-agents/ai_analysis_reports/archive")
    
    # Data directories
    tracking_data_dir: Path = Path("4runr-agents/ai_improvement_system/tracking")
    cache_dir: Path = Path("4runr-agents/ai_improvement_system/cache")
    
    def create_directories(self):
        """Create all required directories"""
        directories = [
            self.analysis_reports_dir,
            self.improvement_system_dir,
            self.weekly_reports_dir,
            self.monthly_reports_dir,
            self.archive_dir,
            self.tracking_data_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

class AIImprovementConfig:
    """Main configuration class for the AI Improvement System"""
    
    def __init__(self):
        self.analysis = AnalysisConfig()
        self.paths = SystemPaths()
        self.version = "1.0.0"
        self.created_at = datetime.now()
        
        # Create directories on initialization
        self.paths.create_directories()
        
        # Load environment-specific overrides
        self._load_environment_config()
    
    def _load_environment_config(self):
        """Load configuration overrides from environment variables"""
        # Analysis settings
        if os.getenv('AI_ANALYSIS_DAYS_BACK'):
            self.analysis.analysis_days_back = int(os.getenv('AI_ANALYSIS_DAYS_BACK'))
        
        if os.getenv('AI_REPORT_RETENTION_DAYS'):
            self.analysis.report_retention_days = int(os.getenv('AI_REPORT_RETENTION_DAYS'))
        
        # Alert thresholds
        if os.getenv('AI_CRITICAL_SUCCESS_RATE'):
            self.analysis.critical_success_rate = float(os.getenv('AI_CRITICAL_SUCCESS_RATE'))
        
        if os.getenv('AI_WARNING_SUCCESS_RATE'):
            self.analysis.warning_success_rate = float(os.getenv('AI_WARNING_SUCCESS_RATE'))
    
    def get_log_directories(self) -> Dict[str, Path]:
        """Get all production log directories"""
        return {
            "campaign_generation": self.paths.production_logs_dir / "campaign_generation",
            "enrichment_decisions": self.paths.production_logs_dir / "enrichment_decisions",
            "website_analysis": self.paths.production_logs_dir / "website_analysis",
            "airtable_operations": self.paths.production_logs_dir / "airtable_operations",
            "email_delivery": self.paths.production_logs_dir / "email_delivery"
        }
    
    def get_report_filename(self, report_type: str, timestamp: datetime = None) -> str:
        """Generate standardized report filename"""
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"{report_type}_{date_str}.json"
    
    def get_summary_filename(self, report_type: str, timestamp: datetime = None) -> str:
        """Generate standardized summary filename"""
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"{report_type}_summary_{date_str}.txt"
    
    def should_archive_report(self, report_path: Path) -> bool:
        """Check if a report should be archived based on age"""
        if not report_path.exists():
            return False
        
        file_age_days = (datetime.now() - datetime.fromtimestamp(report_path.stat().st_mtime)).days
        return file_age_days > self.analysis.archive_after_days
    
    def should_delete_report(self, report_path: Path) -> bool:
        """Check if a report should be deleted based on retention policy"""
        if not report_path.exists():
            return False
        
        file_age_days = (datetime.now() - datetime.fromtimestamp(report_path.stat().st_mtime)).days
        return file_age_days > self.analysis.report_retention_days
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for serialization"""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "analysis_config": {
                "analysis_days_back": self.analysis.analysis_days_back,
                "minimum_logs_required": self.analysis.minimum_logs_required,
                "confidence_threshold": self.analysis.confidence_threshold,
                "report_retention_days": self.analysis.report_retention_days,
                "archive_after_days": self.analysis.archive_after_days,
                "max_reports_per_directory": self.analysis.max_reports_per_directory
            },
            "alert_thresholds": {
                "critical_success_rate": self.analysis.critical_success_rate,
                "warning_success_rate": self.analysis.warning_success_rate,
                "critical_approval_rate": self.analysis.critical_approval_rate,
                "warning_approval_rate": self.analysis.warning_approval_rate
            },
            "performance_thresholds": {
                "max_processing_time": self.analysis.max_processing_time,
                "warning_processing_time": self.analysis.warning_processing_time
            },
            "paths": {
                "production_logs_dir": str(self.paths.production_logs_dir),
                "analysis_reports_dir": str(self.paths.analysis_reports_dir),
                "improvement_system_dir": str(self.paths.improvement_system_dir)
            }
        }

# Global configuration instance
config = AIImprovementConfig()

def get_config() -> AIImprovementConfig:
    """Get the global configuration instance"""
    return config

def save_config_to_file():
    """Save current configuration to file for reference"""
    config_file = config.paths.improvement_system_dir / "system_config.json"
    
    import json
    with open(config_file, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)
    
    return config_file