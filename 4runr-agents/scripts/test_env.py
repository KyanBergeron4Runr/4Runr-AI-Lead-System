#!/usr/bin/env python3
"""
Environment Variables Test Script

This script tests that all required environment variables are properly loaded
and accessible to the Python agents.
"""

import os
import sys
import pathlib
from dotenv import load_dotenv

def create_sample_env(env_path):
    """Create a sample .env file with placeholder values"""
    sample_env_content = """# Airtable
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Leads

# Make.com
MAKE_WEBHOOK_URL=your_make_webhook_url_here

# Apify (scraping)
APIFY_TOKEN=your_apify_token_here

# OpenAI (enrichment/LLMs)
OPENAI_API_KEY=your_openai_api_key_here

# Microsoft Graph
MS_GRAPH_CLIENT_ID=your_ms_graph_client_id_here
MS_GRAPH_CLIENT_SECRET=your_ms_graph_client_secret_here
MS_GRAPH_TENANT_ID=your_ms_graph_tenant_id_here
MS_GRAPH_SENDER_EMAIL=your_ms_graph_sender_email_here

# Agent Configuration
SCRAPER_LEAD_COUNT=5
SCRAPER_DELAY_SECONDS=3600
ENRICHER_DELAY_SECONDS=60
ENGAGER_DELAY_SECONDS=300
LOG_LEVEL=INFO
"""
    with open(env_path, 'w') as f:
        f.write(sample_env_content)

def main():
    """Main function to test environment variables"""
    print("4Runr Environment Variables Test")
    print("================================\n")
    
    # Find the .env file
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    env_path = root_dir / '.env'
    
    print(f"Looking for .env file at: {env_path}")
    if env_path.exists():
        print(f"Found .env file at: {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}")
        print("Creating a sample .env file with placeholder values...")
        create_sample_env(env_path)
        print(f"Created sample .env file at: {env_path}")
    
    # Load environment variables
    print("\nLoading environment variables from .env file...")
    load_dotenv(dotenv_path=env_path)
    
    # Required environment variables
    required_vars = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID',
        'AIRTABLE_TABLE_NAME',
        'OPENAI_API_KEY'
    ]
    
    # Optional environment variables
    optional_vars = [
        'SCRAPER_LEAD_COUNT',
        'SCRAPER_DELAY_SECONDS',
        'ENRICHER_DELAY_SECONDS',
        'ENGAGER_DELAY_SECONDS',
        'LOG_LEVEL'
    ]
    
    # Check required variables
    print("\nChecking required environment variables:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)
    
    # Check optional variables
    print("\nChecking optional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set (will use default)")
    
    # Summary
    print("\nSummary:")
    if missing_vars:
        print(f"❌ Missing {len(missing_vars)} required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file and try again.")
        return 1
    else:
        print("✅ All required environment variables are set.")
        print("The Python agents should be able to run correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(main())