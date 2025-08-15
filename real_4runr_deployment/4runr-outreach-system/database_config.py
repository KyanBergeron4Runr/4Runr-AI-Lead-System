#!/usr/bin/env python3
"""
Database Configuration Management for Lead Database Integration.

This module handles all database configuration including:
- Environment variable loading and validation
- Database path configuration with fallback defaults
- Connection pool settings
- Backup and maintenance configuration
- Health check settings
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Database configuration settings with validation and defaults."""
    
    # Core database settings
    database_path: str = "data/leads_cache.db"
    backup_path: str = "data/backups"
    max_connections: int = 10
    connection_timeout: int = 30
    
    # SQLite optimization settings
    enable_wal_mode: bool = True
    auto_vacuum: bool = True
    cache_size: int = -64000  # 64MB cache
    temp_store: str = "memory"
    synchronous: str = "normal"
    journal_mode: str = "wal"
    
    # Backup and maintenance settings
    backup_retention_days: int = 30
    auto_backup_enabled: bool = True
    backup_interval_hours: int = 24
    vacuum_interval_days: int = 7
    
    # Health check settings
    health_check_interval: int = 300  # 5 minutes
    health_check_enabled: bool = True
    slow_query_threshold_ms: int = 1000
    
    # Logging settings
    enable_logging: bool = True
    log_slow_queries: bool = True
    log_level: str = "INFO"
    
    # Migration settings
    migration_batch_size: int = 1000
    migration_timeout: int = 3600  # 1 hour
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._ensure_directories()
    
    def _validate_config(self):
        """Validate configuration values."""
        if self.max_connections < 1:
            raise ValueError("max_connections must be at least 1")
        
        if self.connection_timeout < 1:
            raise ValueError("connection_timeout must be at least 1 second")
        
        if self.backup_retention_days < 1:
            raise ValueError("backup_retention_days must be at least 1")
        
        if self.health_check_interval < 60:
            raise ValueError("health_check_interval must be at least 60 seconds")
        
        if self.slow_query_threshold_ms < 1:
            raise ValueError("slow_query_threshold_ms must be at least 1")
        
        # Validate paths
        if not self.database_path:
            raise ValueError("database_path cannot be empty")
        
        if not self.backup_path:
            raise ValueError("backup_path cannot be empty")
        
        # Validate SQLite settings
        valid_synchronous = ["off", "normal", "full", "extra"]
        if self.synchronous not in valid_synchronous:
            raise ValueError(f"synchronous must be one of: {valid_synchronous}")
        
        valid_journal_modes = ["delete", "truncate", "persist", "memory", "wal", "off"]
        if self.journal_mode not in valid_journal_modes:
            raise ValueError(f"journal_mode must be one of: {valid_journal_modes}")
        
        valid_temp_stores = ["default", "file", "memory"]
        if self.temp_store not in valid_temp_stores:
            raise ValueError(f"temp_store must be one of: {valid_temp_stores}")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        # Create database directory
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup directory
        backup_dir = Path(self.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_sqlite_pragmas(self) -> Dict[str, Union[str, int]]:
        """Get SQLite PRAGMA settings as a dictionary."""
        return {
            "journal_mode": self.journal_mode,
            "synchronous": self.synchronous,
            "cache_size": self.cache_size,
            "temp_store": self.temp_store,
            "auto_vacuum": "incremental" if self.auto_vacuum else "none",
            "foreign_keys": "on",
            "busy_timeout": self.connection_timeout * 1000,  # Convert to milliseconds
        }
    
    def get_connection_string(self) -> str:
        """Get the database connection string with optimizations."""
        return f"file:{self.database_path}?mode=rwc"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "database_path": self.database_path,
            "backup_path": self.backup_path,
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "enable_wal_mode": self.enable_wal_mode,
            "auto_vacuum": self.auto_vacuum,
            "cache_size": self.cache_size,
            "temp_store": self.temp_store,
            "synchronous": self.synchronous,
            "journal_mode": self.journal_mode,
            "backup_retention_days": self.backup_retention_days,
            "auto_backup_enabled": self.auto_backup_enabled,
            "backup_interval_hours": self.backup_interval_hours,
            "vacuum_interval_days": self.vacuum_interval_days,
            "health_check_interval": self.health_check_interval,
            "health_check_enabled": self.health_check_enabled,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "enable_logging": self.enable_logging,
            "log_slow_queries": self.log_slow_queries,
            "log_level": self.log_level,
            "migration_batch_size": self.migration_batch_size,
            "migration_timeout": self.migration_timeout
        }


class DatabaseConfigManager:
    """Manages database configuration loading and validation."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Path to .env file (optional)
        """
        self.env_file = env_file
        self.config: Optional[DatabaseConfig] = None
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env file."""
        if self.env_file and os.path.exists(self.env_file):
            load_dotenv(self.env_file)
        else:
            # Try to find .env file in current directory or parent directories
            current_dir = Path.cwd()
            for parent in [current_dir] + list(current_dir.parents):
                env_path = parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    self.logger.info(f"Loaded environment from {env_path}")
                    break
    
    def load_config(self) -> DatabaseConfig:
        """
        Load database configuration from environment variables.
        
        Returns:
            DatabaseConfig: Validated configuration object
        """
        try:
            config_data = {
                "database_path": self._get_env_str("LEAD_DATABASE_PATH", "data/leads_cache.db"),
                "backup_path": self._get_env_str("LEAD_DATABASE_BACKUP_PATH", "data/backups"),
                "max_connections": self._get_env_int("LEAD_DATABASE_MAX_CONNECTIONS", 10),
                "connection_timeout": self._get_env_int("LEAD_DATABASE_CONNECTION_TIMEOUT", 30),
                "enable_wal_mode": self._get_env_bool("LEAD_DATABASE_ENABLE_WAL_MODE", True),
                "auto_vacuum": self._get_env_bool("LEAD_DATABASE_AUTO_VACUUM", True),
                "cache_size": self._get_env_int("LEAD_DATABASE_CACHE_SIZE", -64000),
                "temp_store": self._get_env_str("LEAD_DATABASE_TEMP_STORE", "memory"),
                "synchronous": self._get_env_str("LEAD_DATABASE_SYNCHRONOUS", "normal"),
                "journal_mode": self._get_env_str("LEAD_DATABASE_JOURNAL_MODE", "wal"),
                "backup_retention_days": self._get_env_int("LEAD_DATABASE_BACKUP_RETENTION_DAYS", 30),
                "auto_backup_enabled": self._get_env_bool("LEAD_DATABASE_AUTO_BACKUP_ENABLED", True),
                "backup_interval_hours": self._get_env_int("LEAD_DATABASE_BACKUP_INTERVAL_HOURS", 24),
                "vacuum_interval_days": self._get_env_int("LEAD_DATABASE_VACUUM_INTERVAL_DAYS", 7),
                "health_check_interval": self._get_env_int("LEAD_DATABASE_HEALTH_CHECK_INTERVAL", 300),
                "health_check_enabled": self._get_env_bool("LEAD_DATABASE_HEALTH_CHECK_ENABLED", True),
                "slow_query_threshold_ms": self._get_env_int("LEAD_DATABASE_SLOW_QUERY_THRESHOLD_MS", 1000),
                "enable_logging": self._get_env_bool("LEAD_DATABASE_ENABLE_LOGGING", True),
                "log_slow_queries": self._get_env_bool("LEAD_DATABASE_LOG_SLOW_QUERIES", True),
                "log_level": self._get_env_str("LEAD_DATABASE_LOG_LEVEL", "INFO"),
                "migration_batch_size": self._get_env_int("LEAD_DATABASE_MIGRATION_BATCH_SIZE", 1000),
                "migration_timeout": self._get_env_int("LEAD_DATABASE_MIGRATION_TIMEOUT", 3600),
            }
            
            self.config = DatabaseConfig(**config_data)
            self.logger.info("Database configuration loaded successfully")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load database configuration: {e}")
            raise
    
    def _get_env_str(self, key: str, default: str) -> str:
        """Get string environment variable with default."""
        value = os.getenv(key, default)
        return value.strip() if value else default
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            self.logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        
        return value.lower() in ("true", "1", "yes", "on", "enabled")
    
    def validate_config(self, config: DatabaseConfig) -> Dict[str, Any]:
        """
        Validate database configuration and return validation results.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Test database path accessibility
            db_path = Path(config.database_path)
            if not db_path.parent.exists():
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    validation_results["errors"].append(f"Cannot create database directory: {e}")
                    validation_results["valid"] = False
            
            # Test backup path accessibility
            backup_path = Path(config.backup_path)
            if not backup_path.exists():
                try:
                    backup_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    validation_results["errors"].append(f"Cannot create backup directory: {e}")
                    validation_results["valid"] = False
            
            # Check disk space
            try:
                import shutil
                db_free_space = shutil.disk_usage(db_path.parent).free
                backup_free_space = shutil.disk_usage(backup_path).free
                
                # Warn if less than 1GB free space
                if db_free_space < 1024 * 1024 * 1024:
                    validation_results["warnings"].append("Low disk space for database directory")
                
                if backup_free_space < 1024 * 1024 * 1024:
                    validation_results["warnings"].append("Low disk space for backup directory")
                    
            except Exception as e:
                validation_results["warnings"].append(f"Could not check disk space: {e}")
            
            # Performance recommendations
            if config.cache_size > -10000:  # Less than 10MB cache
                validation_results["recommendations"].append("Consider increasing cache_size for better performance")
            
            if config.journal_mode != "wal":
                validation_results["recommendations"].append("Consider using WAL mode for better concurrency")
            
            if config.synchronous == "full":
                validation_results["recommendations"].append("Consider using 'normal' synchronous mode for better performance")
            
            # Security recommendations
            if not config.enable_logging:
                validation_results["warnings"].append("Database logging is disabled - consider enabling for monitoring")
            
        except Exception as e:
            validation_results["errors"].append(f"Configuration validation failed: {e}")
            validation_results["valid"] = False
        
        return validation_results
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        if not self.config:
            return {"error": "Configuration not loaded"}
        
        return {
            "database_path": self.config.database_path,
            "backup_path": self.config.backup_path,
            "max_connections": self.config.max_connections,
            "wal_mode_enabled": self.config.enable_wal_mode,
            "auto_backup_enabled": self.config.auto_backup_enabled,
            "health_check_enabled": self.config.health_check_enabled,
            "logging_enabled": self.config.enable_logging,
            "cache_size_mb": abs(self.config.cache_size) / 1000 if self.config.cache_size < 0 else self.config.cache_size,
            "backup_retention_days": self.config.backup_retention_days
        }


# Global configuration manager instance
config_manager = DatabaseConfigManager()

def get_database_config() -> DatabaseConfig:
    """
    Get the current database configuration.
    
    Returns:
        DatabaseConfig: Current configuration
    """
    if config_manager.config is None:
        config_manager.load_config()
    
    return config_manager.config

def reload_database_config(env_file: Optional[str] = None) -> DatabaseConfig:
    """
    Reload database configuration from environment.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        DatabaseConfig: Reloaded configuration
    """
    global config_manager
    config_manager = DatabaseConfigManager(env_file)
    return config_manager.load_config()

def validate_database_config(config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """
    Validate database configuration.
    
    Args:
        config: Configuration to validate (uses current if None)
        
    Returns:
        Dictionary with validation results
    """
    if config is None:
        config = get_database_config()
    
    return config_manager.validate_config(config)