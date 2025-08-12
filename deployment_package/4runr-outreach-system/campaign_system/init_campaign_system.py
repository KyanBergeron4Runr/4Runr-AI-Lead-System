#!/usr/bin/env python3
"""
Initialize the Multi-Step Email Campaign System

This script sets up the database tables and validates configuration.
"""

import os
import sys

# Add the parent directory to the path so we can import from the campaign system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign_system.database.schema import create_campaign_tables
from campaign_system.config import get_config


def main():
    """Initialize the campaign system"""
    print("🚀 Initializing Multi-Step Email Campaign System...")
    
    # Load and validate configuration
    print("📋 Loading configuration...")
    config = get_config()
    
    if not config.validate_config():
        print("❌ Configuration validation failed. Please check your environment variables.")
        return False
    
    print("✅ Configuration loaded successfully")
    
    # Create database tables
    print("🗄️  Creating database tables...")
    try:
        create_campaign_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        print(f"📁 Created logs directory: {log_dir}")
    
    print("\n🎉 Campaign system initialization complete!")
    print("\nNext steps:")
    print("1. Start creating campaigns with the CampaignGenerator")
    print("2. Use the CampaignScheduler to manage timing")
    print("3. Monitor performance with CampaignAnalytics")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)