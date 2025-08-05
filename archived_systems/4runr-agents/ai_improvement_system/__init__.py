#!/usr/bin/env python3
"""
AI Improvement System

Automated system for analyzing AI decisions and generating improvement recommendations.
"""

from .config import get_config, save_config_to_file
from .logger import get_logger, log_system_startup, log_system_shutdown

__version__ = "1.0.0"
__author__ = "4Runr AI System"

# Initialize system on import
config = get_config()
logger = get_logger()

logger.info(f"🤖 AI Improvement System v{__version__} initialized")
logger.info(f"📁 System directory: {config.paths.improvement_system_dir}")
logger.info(f"📊 Reports directory: {config.paths.analysis_reports_dir}")

# Save initial configuration
config_file = save_config_to_file()
logger.info(f"⚙️ Configuration saved to: {config_file}")