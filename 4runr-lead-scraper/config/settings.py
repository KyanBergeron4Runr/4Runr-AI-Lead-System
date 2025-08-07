#!/usr/bin/env python3
"""
Configuration Settings

Centralized configuration management for the 4runr-lead-scraper system.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from the correct location
config_dir = Path(__file__).parent.parent
env_file = config_dir / '.env'
load_dotenv(env_file)

@dataclass
class ScraperConfig:
    """Configuration for lead scraping operations."""
    serpapi_key: str
    max_leads_per_run: int = 10
    search_location: str = "Montreal, Quebec, Canada"
    search_queries: List[str] = field(default_factory=lambda: ["CEO", "Founder", "President"])
    
    def __post_init__(self):
        """Validate scraper configuration."""
        if not self.serpapi_key:
            raise ValueError("SERPAPI_KEY is required")
        
        # Parse search queries from string if needed
        if isinstance(self.search_queries, str):
            self.search_queries = [q.strip() for q in self.search_queries.split(',')]

@dataclass
class DatabaseConfig:
    """Configuration for database operations."""
    db_path: str = "data/leads.db"
    backup_enabled: bool = True
    backup_retention_days: int = 30
    
    def __post_init__(self):
        """Process database configuration."""
        # Make path absolute if not already
        if not os.path.isabs(self.db_path):
            # Relative to the config file location
            config_dir = os.path.dirname(os.path.dirname(__file__))
            self.db_path = os.path.join(config_dir, self.db_path)

@dataclass
class AirtableConfig:
    """Configuration for Airtable synchronization."""
    api_key: str
    base_id: str
    table_name: str = "Leads"
    sync_interval_minutes: int = 30
    auto_sync_enabled: bool = True
    
    def __post_init__(self):
        """Validate Airtable configuration."""
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY is required")
        if not self.base_id:
            raise ValueError("AIRTABLE_BASE_ID is required")

@dataclass
class SyncConfig:
    """Configuration for automatic synchronization."""
    immediate_sync_enabled: bool = True
    daily_sync_time: str = "06:00"
    batch_size: int = 50
    sync_on_create: bool = True
    sync_on_update: bool = True
    
    def __post_init__(self):
        """Validate sync configuration."""
        # Validate time format
        try:
            hour, minute = self.daily_sync_time.split(':')
            hour, minute = int(hour), int(minute)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid daily_sync_time format: {self.daily_sync_time}. Use HH:MM format.")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

@dataclass
class EnrichmentConfig:
    """Configuration for lead enrichment operations."""
    max_email_attempts: int = 2
    max_website_attempts: int = 2
    enrichment_timeout_seconds: int = 30
    skip_email_if_no_website: bool = True
    use_pattern_emails: bool = True
    auto_ready_for_outreach: bool = True
    mark_as_enriched_with_partial: bool = True

@dataclass
class EngagementDefaultsConfig:
    """Configuration for engagement defaults application."""
    enabled: bool = True
    default_values: dict = field(default_factory=lambda: {
        'Engagement_Status': 'Auto-Send',
        'Email_Confidence_Level': 'Pattern',
        'Level Engaged': ''
    })
    apply_on_scrape: bool = True
    apply_on_enrich: bool = True
    apply_on_verify: bool = True
    
    def __post_init__(self):
        """Process engagement defaults configuration."""
        # Validate default values structure
        if not isinstance(self.default_values, dict):
            raise ValueError("default_values must be a dictionary")
        
        # Validate that required fields are present if enabled
        if self.enabled:
            required_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
            missing_fields = [field for field in required_fields if field not in self.default_values]
            if missing_fields:
                raise ValueError(f"Missing required engagement default fields: {missing_fields}")
    
    def validate_field_values(self) -> List[str]:
        """
        Validate the configured default field values.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate Engagement_Status values
        valid_engagement_statuses = ['Auto-Send', 'Skip', 'Manual Review', 'Completed']
        engagement_status = self.default_values.get('Engagement_Status')
        if engagement_status and engagement_status not in valid_engagement_statuses:
            errors.append(f"Invalid Engagement_Status value: {engagement_status}. Must be one of: {valid_engagement_statuses}")
        
        # Validate Email_Confidence_Level values
        valid_confidence_levels = ['Real', 'Pattern', 'Guessed', 'Unknown']
        confidence_level = self.default_values.get('Email_Confidence_Level')
        if confidence_level and confidence_level not in valid_confidence_levels:
            errors.append(f"Invalid Email_Confidence_Level value: {confidence_level}. Must be one of: {valid_confidence_levels}")
        
        # Level Engaged can be any string (including empty), so no validation needed
        
        return errors
    
    def get_summary(self) -> dict:
        """
        Get a summary of the engagement defaults configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            'enabled': self.enabled,
            'default_values': self.default_values.copy(),
            'apply_on_scrape': self.apply_on_scrape,
            'apply_on_enrich': self.apply_on_enrich,
            'apply_on_verify': self.apply_on_verify,
            'validation_errors': self.validate_field_values()
        }

@dataclass
class LoggingConfig:
    """Configuration for logging."""
    log_level: str = "INFO"
    verbose_logging: bool = False
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Process logging configuration."""
        self.log_level = self.log_level.upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.log_level = "INFO"

@dataclass
class SystemConfig:
    """General system configuration."""
    run_once: bool = False
    debug: bool = False

@dataclass
class Settings:
    """Complete system settings."""
    scraper: ScraperConfig
    database: DatabaseConfig
    airtable: AirtableConfig
    sync: SyncConfig
    enrichment: EnrichmentConfig
    engagement_defaults: EngagementDefaultsConfig
    logging: LoggingConfig
    system: SystemConfig
    
    @classmethod
    def from_environment(cls) -> 'Settings':
        """Create settings from environment variables."""
        try:
            # Scraper configuration
            scraper = ScraperConfig(
                serpapi_key=os.getenv('SERPAPI_API_KEY', ''),
                max_leads_per_run=int(os.getenv('MAX_LEADS_PER_RUN', '10')),
                search_location=os.getenv('SEARCH_LOCATION', 'Montreal, Quebec, Canada'),
                search_queries=os.getenv('SEARCH_QUERIES', 'CEO,Founder,President')
            )
            
            # Database configuration
            database = DatabaseConfig(
                db_path=os.getenv('LEAD_DATABASE_PATH', 'data/leads.db'),
                backup_enabled=os.getenv('DATABASE_BACKUP_ENABLED', 'true').lower() == 'true',
                backup_retention_days=int(os.getenv('DATABASE_BACKUP_RETENTION_DAYS', '30'))
            )
            
            # Airtable configuration
            airtable = AirtableConfig(
                api_key=os.getenv('AIRTABLE_API_KEY', ''),
                base_id=os.getenv('AIRTABLE_BASE_ID', ''),
                table_name=os.getenv('AIRTABLE_TABLE_NAME', 'Leads'),
                sync_interval_minutes=int(os.getenv('AIRTABLE_SYNC_INTERVAL_MINUTES', '30')),
                auto_sync_enabled=os.getenv('AUTO_SYNC_TO_AIRTABLE', 'true').lower() == 'true'
            )
            
            # Sync configuration
            sync = SyncConfig(
                immediate_sync_enabled=os.getenv('IMMEDIATE_SYNC_ENABLED', 'true').lower() == 'true',
                daily_sync_time=os.getenv('DAILY_SYNC_TIME', '06:00'),
                batch_size=int(os.getenv('SYNC_BATCH_SIZE', '50')),
                sync_on_create=os.getenv('SYNC_ON_CREATE', 'true').lower() == 'true',
                sync_on_update=os.getenv('SYNC_ON_UPDATE', 'true').lower() == 'true'
            )
            
            # Enrichment configuration
            enrichment = EnrichmentConfig(
                max_email_attempts=int(os.getenv('MAX_EMAIL_ATTEMPTS', '2')),
                max_website_attempts=int(os.getenv('MAX_WEBSITE_ATTEMPTS', '2')),
                enrichment_timeout_seconds=int(os.getenv('ENRICHMENT_TIMEOUT_SECONDS', '30')),
                skip_email_if_no_website=os.getenv('SKIP_EMAIL_IF_NO_WEBSITE', 'true').lower() == 'true',
                use_pattern_emails=os.getenv('USE_PATTERN_EMAILS', 'true').lower() == 'true',
                auto_ready_for_outreach=os.getenv('AUTO_READY_FOR_OUTREACH', 'true').lower() == 'true',
                mark_as_enriched_with_partial=os.getenv('MARK_AS_ENRICHED_WITH_PARTIAL', 'true').lower() == 'true'
            )
            
            # Engagement defaults configuration
            engagement_defaults_values = {
                'Engagement_Status': 'Auto-Send',
                'Email_Confidence_Level': 'Pattern',
                'Level Engaged': ''
            }
            
            # Load custom defaults from environment if provided
            custom_defaults_json = os.getenv('ENGAGEMENT_DEFAULT_VALUES')
            if custom_defaults_json:
                try:
                    import json
                    custom_defaults = json.loads(custom_defaults_json)
                    engagement_defaults_values.update(custom_defaults)
                except (json.JSONDecodeError, TypeError):
                    pass  # Use defaults if parsing fails
            
            engagement_defaults = EngagementDefaultsConfig(
                enabled=os.getenv('APPLY_ENGAGEMENT_DEFAULTS', 'true').lower() == 'true',
                default_values=engagement_defaults_values,
                apply_on_scrape=os.getenv('APPLY_DEFAULTS_ON_SCRAPE', 'true').lower() == 'true',
                apply_on_enrich=os.getenv('APPLY_DEFAULTS_ON_ENRICH', 'true').lower() == 'true',
                apply_on_verify=os.getenv('APPLY_DEFAULTS_ON_VERIFY', 'true').lower() == 'true'
            )
            
            # Logging configuration
            logging_config = LoggingConfig(
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                verbose_logging=os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true',
                log_file=os.getenv('LOG_FILE')
            )
            
            # System configuration
            system = SystemConfig(
                run_once=os.getenv('RUN_ONCE', 'false').lower() == 'true',
                debug=os.getenv('DEBUG', 'false').lower() == 'true'
            )
            
            return cls(
                scraper=scraper,
                database=database,
                airtable=airtable,
                sync=sync,
                enrichment=enrichment,
                engagement_defaults=engagement_defaults,
                logging=logging_config,
                system=system
            )
            
        except Exception as e:
            raise ValueError(f"Failed to load settings from environment: {e}")
    
    def validate(self) -> List[str]:
        """
        Validate all settings and return list of errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate scraper settings
        if not self.scraper.serpapi_key:
            errors.append("SERPAPI_KEY is required")
        
        if self.scraper.max_leads_per_run <= 0:
            errors.append("MAX_LEADS_PER_RUN must be positive")
        
        # Validate Airtable settings
        if not self.airtable.api_key:
            errors.append("AIRTABLE_API_KEY is required")
        
        if not self.airtable.base_id:
            errors.append("AIRTABLE_BASE_ID is required")
        
        # Validate enrichment settings
        if self.enrichment.max_email_attempts <= 0:
            errors.append("MAX_EMAIL_ATTEMPTS must be positive")
        
        if self.enrichment.enrichment_timeout_seconds <= 0:
            errors.append("ENRICHMENT_TIMEOUT_SECONDS must be positive")
        
        # Validate engagement defaults settings
        if self.engagement_defaults.enabled:
            if not isinstance(self.engagement_defaults.default_values, dict):
                errors.append("ENGAGEMENT_DEFAULT_VALUES must be a dictionary")
            
            if not self.engagement_defaults.default_values:
                errors.append("ENGAGEMENT_DEFAULT_VALUES cannot be empty when engagement defaults are enabled")
            
            # Check for required engagement fields
            required_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
            for field in required_fields:
                if field not in self.engagement_defaults.default_values:
                    errors.append(f"Missing required engagement default field: {field}")
            
            # Validate field values
            field_errors = self.engagement_defaults.validate_field_values()
            errors.extend(field_errors)
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            'scraper': {
                'serpapi_key': '***' if self.scraper.serpapi_key else '',
                'max_leads_per_run': self.scraper.max_leads_per_run,
                'search_location': self.scraper.search_location,
                'search_queries': self.scraper.search_queries
            },
            'database': {
                'db_path': self.database.db_path,
                'backup_enabled': self.database.backup_enabled,
                'backup_retention_days': self.database.backup_retention_days
            },
            'airtable': {
                'api_key': '***' if self.airtable.api_key else '',
                'base_id': self.airtable.base_id,
                'table_name': self.airtable.table_name,
                'sync_interval_minutes': self.airtable.sync_interval_minutes,
                'auto_sync_enabled': self.airtable.auto_sync_enabled
            },
            'enrichment': {
                'max_email_attempts': self.enrichment.max_email_attempts,
                'max_website_attempts': self.enrichment.max_website_attempts,
                'enrichment_timeout_seconds': self.enrichment.enrichment_timeout_seconds,
                'skip_email_if_no_website': self.enrichment.skip_email_if_no_website,
                'use_pattern_emails': self.enrichment.use_pattern_emails,
                'auto_ready_for_outreach': self.enrichment.auto_ready_for_outreach,
                'mark_as_enriched_with_partial': self.enrichment.mark_as_enriched_with_partial
            },
            'engagement_defaults': {
                'enabled': self.engagement_defaults.enabled,
                'default_values': self.engagement_defaults.default_values,
                'apply_on_scrape': self.engagement_defaults.apply_on_scrape,
                'apply_on_enrich': self.engagement_defaults.apply_on_enrich,
                'apply_on_verify': self.engagement_defaults.apply_on_verify
            },
            'logging': {
                'log_level': self.logging.log_level,
                'verbose_logging': self.logging.verbose_logging,
                'log_file': self.logging.log_file
            },
            'system': {
                'run_once': self.system.run_once,
                'debug': self.system.debug
            }
        }


# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Get global settings instance.
    
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        _settings = Settings.from_environment()
        
        # Validate settings
        errors = _settings.validate()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return _settings

def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Returns:
        New settings instance
    """
    global _settings
    
    # Reload environment variables
    load_dotenv(override=True)
    
    # Create new settings
    _settings = Settings.from_environment()
    
    # Validate
    errors = _settings.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return _settings

def validate_environment() -> List[str]:
    """
    Validate environment configuration without creating settings.
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check required environment variables
    required_vars = [
        'SERPAPI_KEY',
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check numeric variables
    numeric_vars = {
        'MAX_LEADS_PER_RUN': 10,
        'MAX_EMAIL_ATTEMPTS': 2,
        'ENRICHMENT_TIMEOUT_SECONDS': 30
    }
    
    for var, default in numeric_vars.items():
        value = os.getenv(var, str(default))
        try:
            int(value)
        except ValueError:
            errors.append(f"Invalid numeric value for {var}: {value}")
    
    return errors


if __name__ == "__main__":
    # Test settings
    print("🧪 Testing Settings...")
    
    try:
        settings = get_settings()
        print("✅ Settings loaded successfully")
        
        # Validate
        errors = settings.validate()
        if errors:
            print(f"❌ Validation errors: {errors}")
        else:
            print("✅ Settings validation passed")
        
        # Show configuration (without sensitive data)
        config_dict = settings.to_dict()
        print(f"📋 Configuration: {config_dict}")
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
    
    print("✅ Settings test completed")