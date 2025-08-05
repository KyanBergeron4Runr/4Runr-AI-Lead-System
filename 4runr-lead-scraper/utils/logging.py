#!/usr/bin/env python3
"""
Logging Utilities

Centralized logging configuration and utilities for the 4runr-lead-scraper system.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        verbose: Enable verbose logging
        module_name: Optional module name for logger
        
    Returns:
        Configured logger instance
    """
    # Determine log level
    if verbose:
        log_level = "DEBUG"
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger_name = module_name or '4runr-lead-scraper'
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    if verbose:
        console_handler.setFormatter(detailed_formatter)
    else:
        console_handler.setFormatter(simple_formatter)
    
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with consistent configuration.
    
    Args:
        name: Logger name
        log_level: Optional log level override
        
    Returns:
        Logger instance
    """
    # Get configuration from environment
    env_log_level = os.getenv('LOG_LEVEL', 'INFO')
    env_verbose = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
    env_log_file = os.getenv('LOG_FILE')
    
    return setup_logging(
        log_level=log_level or env_log_level,
        log_file=env_log_file,
        verbose=env_verbose,
        module_name=name
    )

class StructuredLogger:
    """
    Structured logger for consistent logging with metadata.
    """
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = get_logger(name)
        self.name = name
    
    def log_operation(
        self,
        operation: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ):
        """
        Log an operation with structured data.
        
        Args:
            operation: Operation name
            status: Operation status (success, failed, warning)
            details: Optional additional details
            level: Log level
        """
        message = f"[{operation.upper()}] {status.upper()}"
        
        if details:
            detail_parts = []
            for key, value in details.items():
                detail_parts.append(f"{key}={value}")
            
            if detail_parts:
                message += f" | {' | '.join(detail_parts)}"
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    def log_scraping(self, status: str, leads_count: int = 0, source: str = "", **kwargs):
        """Log scraping operations."""
        details = {
            'leads_count': leads_count,
            'source': source,
            **kwargs
        }
        self.log_operation('scraping', status, details)
    
    def log_enrichment(self, status: str, lead_name: str = "", method: str = "", **kwargs):
        """Log enrichment operations."""
        details = {
            'lead_name': lead_name,
            'method': method,
            **kwargs
        }
        self.log_operation('enrichment', status, details)
    
    def log_sync(self, status: str, direction: str = "", count: int = 0, **kwargs):
        """Log synchronization operations."""
        details = {
            'direction': direction,
            'count': count,
            **kwargs
        }
        self.log_operation('sync', status, details)
    
    def log_database(self, status: str, operation: str = "", **kwargs):
        """Log database operations."""
        details = {
            'operation': operation,
            **kwargs
        }
        self.log_operation('database', status, details)

class PerformanceLogger:
    """
    Logger for performance monitoring and timing.
    """
    
    def __init__(self, name: str):
        """Initialize performance logger."""
        self.logger = get_logger(f"{name}-performance")
        self.timers = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.timers[operation] = datetime.now()
        self.logger.debug(f"⏱️ Started timing: {operation}")
    
    def end_timer(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """End timing an operation and log the duration."""
        if operation not in self.timers:
            self.logger.warning(f"⚠️ Timer not found for operation: {operation}")
            return
        
        start_time = self.timers.pop(operation)
        duration = (datetime.now() - start_time).total_seconds()
        
        message = f"⏱️ {operation} completed in {duration:.3f}s"
        
        if details:
            detail_parts = []
            for key, value in details.items():
                detail_parts.append(f"{key}={value}")
            
            if detail_parts:
                message += f" | {' | '.join(detail_parts)}"
        
        self.logger.info(message)
        
        return duration
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics."""
        message = "📊 Performance Metrics:"
        
        for metric, value in metrics.items():
            if isinstance(value, float):
                message += f" | {metric}={value:.3f}"
            else:
                message += f" | {metric}={value}"
        
        self.logger.info(message)

def configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise."""
    # Reduce noise from requests library
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Reduce noise from other libraries
    logging.getLogger('airtable').setLevel(logging.WARNING)
    logging.getLogger('sqlite3').setLevel(logging.WARNING)

def log_system_info():
    """Log system information for debugging."""
    logger = get_logger('system-info')
    
    logger.info(f"🖥️ Python version: {sys.version}")
    logger.info(f"🖥️ Platform: {sys.platform}")
    logger.info(f"🖥️ Working directory: {os.getcwd()}")
    
    # Log environment variables (without sensitive data)
    env_vars = [
        'LOG_LEVEL', 'VERBOSE_LOGGING', 'MAX_LEADS_PER_RUN',
        'SEARCH_LOCATION', 'ENRICHMENT_TIMEOUT_SECONDS'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"🔧 {var}={value}")

def create_log_directory():
    """Create logs directory if it doesn't exist."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (log_dir / "daily").mkdir(exist_ok=True)
    (log_dir / "errors").mkdir(exist_ok=True)
    (log_dir / "performance").mkdir(exist_ok=True)
    
    return log_dir

# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing."""
    
    def __init__(self, logger: StructuredLogger, operation: str, **details):
        """Initialize logged operation."""
        self.logger = logger
        self.operation = operation
        self.details = details
        self.start_time = None
    
    def __enter__(self):
        """Enter context - start operation."""
        self.start_time = datetime.now()
        self.logger.log_operation(self.operation, 'started', self.details)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - end operation."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Success
            details = {**self.details, 'duration_seconds': f"{duration:.3f}"}
            self.logger.log_operation(self.operation, 'completed', details)
        else:
            # Error
            details = {
                **self.details,
                'duration_seconds': f"{duration:.3f}",
                'error': str(exc_val)
            }
            self.logger.log_operation(self.operation, 'failed', details, level='ERROR')

# Initialize logging on import
configure_third_party_loggers()

if __name__ == "__main__":
    # Test logging configuration
    print("🧪 Testing Logging Configuration...")
    
    # Test basic logger
    logger = get_logger('test-logger')
    logger.info("Basic logger test")
    logger.debug("Debug message (may not show)")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test structured logger
    struct_logger = StructuredLogger('test-structured')
    struct_logger.log_scraping('success', leads_count=5, source='serpapi')
    struct_logger.log_enrichment('failed', lead_name='John Doe', method='email_patterns', error='timeout')
    
    # Test performance logger
    perf_logger = PerformanceLogger('test-performance')
    perf_logger.start_timer('test_operation')
    import time
    time.sleep(0.1)  # Simulate work
    perf_logger.end_timer('test_operation', {'items_processed': 10})
    
    # Test logged operation context manager
    with LoggedOperation(struct_logger, 'test_context', test_param='value'):
        time.sleep(0.05)  # Simulate work
    
    print("✅ Logging test completed")