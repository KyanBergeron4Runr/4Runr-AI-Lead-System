"""
Configuration module for the 4Runr Autonomous Outreach System.

Handles loading and providing access to environment variables and configuration settings.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager for the outreach system."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        load_dotenv()
        self._validate_required_config()
    
    def _validate_required_config(self) -> None:
        """Validate that all required configuration values are present."""
        required_vars = [
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_airtable_config(self) -> Dict[str, str]:
        """Get Airtable API configuration."""
        return {
            'api_key': os.getenv('AIRTABLE_API_KEY'),
            'base_id': os.getenv('AIRTABLE_BASE_ID'),
            'table_name': os.getenv('AIRTABLE_TABLE_NAME', 'Leads')
        }
    
    def get_ai_config(self) -> Dict[str, str]:
        """Get AI service configuration."""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '1000')),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        }
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email service configuration."""
        return {
            'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD')
        }
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get web scraping configuration."""
        return {
            'delay': int(os.getenv('SCRAPING_DELAY', '2')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'timeout': int(os.getenv('SCRAPING_TIMEOUT', '30'))
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'save_json_logs': os.getenv('SAVE_JSON_LOGS', 'true').lower() == 'true',
            'log_directory': os.getenv('LOG_DIRECTORY', 'logs')
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get general system configuration."""
        return {
            'batch_size': int(os.getenv('BATCH_SIZE', '10')),
            'rate_limit_delay': int(os.getenv('RATE_LIMIT_DELAY', '1'))
        }
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a specific configuration value."""
        return os.getenv(key, default)


# Global configuration instance
config = Config()


def load_config() -> Config:
    """Load and return the configuration instance."""
    return config


def get_airtable_config() -> Dict[str, str]:
    """Get Airtable configuration."""
    return config.get_airtable_config()


def get_ai_config() -> Dict[str, str]:
    """Get AI configuration."""
    return config.get_ai_config()


def get_email_config() -> Dict[str, Any]:
    """Get email configuration."""
    return config.get_email_config()