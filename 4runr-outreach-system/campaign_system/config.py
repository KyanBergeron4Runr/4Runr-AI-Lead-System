"""
Configuration management for the Multi-Step Email Campaign System
"""

import os
from typing import Dict, Any


class CampaignConfig:
    """Configuration manager for campaign system"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        
        # Campaign timing configuration
        self.HOOK_MESSAGE_DELAY_DAYS = int(os.getenv('HOOK_MESSAGE_DELAY_DAYS', '0'))
        self.PROOF_MESSAGE_DELAY_DAYS = int(os.getenv('PROOF_MESSAGE_DELAY_DAYS', '3'))
        self.FOMO_MESSAGE_DELAY_DAYS = int(os.getenv('FOMO_MESSAGE_DELAY_DAYS', '7'))
        
        # Campaign behavior configuration
        self.RESPECT_BUSINESS_DAYS = os.getenv('RESPECT_BUSINESS_DAYS', 'true').lower() == 'true'
        self.DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')
        self.MAX_CAMPAIGNS_PER_BATCH = int(os.getenv('MAX_CAMPAIGNS_PER_BATCH', '50'))
        
        # Message queue configuration
        self.QUEUE_BATCH_SIZE = int(os.getenv('QUEUE_BATCH_SIZE', '10'))
        self.MAX_DELIVERY_ATTEMPTS = int(os.getenv('MAX_DELIVERY_ATTEMPTS', '3'))
        self.RETRY_DELAY_MINUTES = int(os.getenv('RETRY_DELAY_MINUTES', '30'))
        
        # AI/LLM configuration for campaign generation
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1000'))
        
        # Database configuration
        self.DATABASE_PATH = os.getenv('CAMPAIGN_DATABASE_PATH', 'campaigns.db')
        
        # Email service configuration (inherits from existing system)
        self.SMTP_SERVER = os.getenv('SMTP_SERVER')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        self.FROM_EMAIL = os.getenv('FROM_EMAIL')
        self.FROM_NAME = os.getenv('FROM_NAME', '4Runr Team')
        
        # Airtable configuration (inherits from existing system)
        self.AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
        self.AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
        self.AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Leads')
        
        # Response monitoring configuration
        self.IMAP_SERVER = os.getenv('IMAP_SERVER')
        self.IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
        self.IMAP_USERNAME = os.getenv('IMAP_USERNAME')
        self.IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
        self.MONITOR_INBOX_FOLDER = os.getenv('MONITOR_INBOX_FOLDER', 'INBOX')
        
        # Analytics configuration
        self.ANALYTICS_RETENTION_DAYS = int(os.getenv('ANALYTICS_RETENTION_DAYS', '365'))
        self.ENABLE_DETAILED_ANALYTICS = os.getenv('ENABLE_DETAILED_ANALYTICS', 'true').lower() == 'true'
        
        # Logging configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE_PATH = os.getenv('CAMPAIGN_LOG_FILE_PATH', 'logs/campaigns.log')
        self.ENABLE_JSON_LOGS = os.getenv('ENABLE_JSON_LOGS', 'true').lower() == 'true'
    
    def get_message_delays(self) -> Dict[str, int]:
        """Get message delay configuration"""
        return {
            'hook': self.HOOK_MESSAGE_DELAY_DAYS,
            'proof': self.PROOF_MESSAGE_DELAY_DAYS,
            'fomo': self.FOMO_MESSAGE_DELAY_DAYS
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI service configuration"""
        return {
            'api_key': self.OPENAI_API_KEY,
            'model': self.OPENAI_MODEL,
            'temperature': self.AI_TEMPERATURE,
            'max_tokens': self.MAX_TOKENS
        }
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email service configuration"""
        return {
            'smtp_server': self.SMTP_SERVER,
            'smtp_port': self.SMTP_PORT,
            'username': self.SMTP_USERNAME,
            'password': self.SMTP_PASSWORD,
            'from_email': self.FROM_EMAIL,
            'from_name': self.FROM_NAME
        }
    
    def get_airtable_config(self) -> Dict[str, Any]:
        """Get Airtable configuration"""
        return {
            'api_key': self.AIRTABLE_API_KEY,
            'base_id': self.AIRTABLE_BASE_ID,
            'table_name': self.AIRTABLE_TABLE_NAME
        }
    
    def get_response_monitor_config(self) -> Dict[str, Any]:
        """Get response monitoring configuration"""
        return {
            'imap_server': self.IMAP_SERVER,
            'imap_port': self.IMAP_PORT,
            'username': self.IMAP_USERNAME,
            'password': self.IMAP_PASSWORD,
            'inbox_folder': self.MONITOR_INBOX_FOLDER
        }
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        required_fields = [
            'OPENAI_API_KEY',
            'SMTP_SERVER',
            'SMTP_USERNAME',
            'SMTP_PASSWORD',
            'FROM_EMAIL',
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        return True


# Global configuration instance
_config = None


def get_config() -> CampaignConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = CampaignConfig()
    return _config


def reload_config() -> CampaignConfig:
    """Reload configuration from environment"""
    global _config
    _config = CampaignConfig()
    return _config