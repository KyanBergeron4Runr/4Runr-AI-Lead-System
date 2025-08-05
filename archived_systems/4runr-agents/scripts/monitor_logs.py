#!/usr/bin/env python3
"""
Log Monitoring Script

This script monitors the logs of the 4Runr Multi-Agent System.
It checks for errors and warnings in the logs and sends alerts if necessary.
"""

import os
import sys
import re
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log-monitor')

# Constants
LOG_DIR = "logs"
ERROR_PATTERN = re.compile(r'error|exception|fail|critical', re.IGNORECASE)
WARNING_PATTERN = re.compile(r'warning|warn', re.IGNORECASE)

def get_log_files():
    """Get a list of log files in the logs directory"""
    if not os.path.isdir(LOG_DIR):
        logger.error(f"Logs directory not found: {LOG_DIR}")
        return []
    
    return [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith(".log")]

def check_log_file(log_file, since=None):
    """Check a log file for errors and warnings"""
    if not os.path.isfile(log_file):
        logger.error(f"Log file not found: {log_file}")
        return 0, 0
    
    # Get the file modification time
    mtime = os.path.getmtime(log_file)
    if since and mtime < since.timestamp():
        # File hasn't been modified since the specified time
        return 0, 0
    
    error_count = 0
    warning_count = 0
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if ERROR_PATTERN.search(line):
                    error_count += 1
                elif WARNING_PATTERN.search(line):
                    warning_count += 1
    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {e}")
    
    return error_count, warning_count

def monitor_logs(interval=60, alert_threshold=5):
    """Monitor logs for errors and warnings"""
    logger.info(f"Starting log monitoring (interval: {interval}s, alert threshold: {alert_threshold} errors)")
    
    last_check = datetime.now()
    
    while True:
        # Get the list of log files
        log_files = get_log_files()
        
        if not log_files:
            logger.warning("No log files found")
            time.sleep(interval)
            continue
        
        # Check each log file
        total_errors = 0
        total_warnings = 0
        
        for log_file in log_files:
            errors, warnings = check_log_file(log_file, since=last_check)
            total_errors += errors
            total_warnings += warnings
            
            if errors > 0 or warnings > 0:
                logger.info(f"{os.path.basename(log_file)}: {errors} errors, {warnings} warnings")
        
        # Send alerts if necessary
        if total_errors >= alert_threshold:
            logger.error(f"ALERT: {total_errors} errors found in logs")
            # In a real implementation, this would send an email or other alert
        
        # Update the last check time
        last_check = datetime.now()
        
        # Sleep until the next check
        time.sleep(interval)

def main():
    """Main function to run the log monitor"""
    logger.info("Starting log monitor...")
    
    # Parse command-line arguments
    interval = 60  # Default: check every 60 seconds
    alert_threshold = 5  # Default: alert if 5 or more errors
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid interval: {sys.argv[1]}")
            return 1
    
    if len(sys.argv) > 2:
        try:
            alert_threshold = int(sys.argv[2])
        except ValueError:
            logger.error(f"Invalid alert threshold: {sys.argv[2]}")
            return 1
    
    try:
        monitor_logs(interval, alert_threshold)
    except KeyboardInterrupt:
        logger.info("Log monitor stopped by user")
    except Exception as e:
        logger.error(f"Error in log monitor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())