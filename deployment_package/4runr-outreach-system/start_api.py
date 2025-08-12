#!/usr/bin/env python3
"""
Simple startup script for the 4Runr Outreach System API.

This script starts the API service with sensible defaults and
provides easy testing and development options.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_environment():
    """Check if the environment is properly configured."""
    print("🔍 Checking Environment Configuration")
    print("=" * 50)
    
    required_vars = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID', 
        'AIRTABLE_TABLE_NAME'
    ]
    
    optional_vars = [
        'OPENAI_API_KEY',
        'PIPELINE_CYCLE_DELAY'
    ]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: configured")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: configured")
        else:
            print(f"⚠️  {var}: not configured (using default)")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    print("\n✅ Environment configuration looks good!")
    return True


def start_api_service():
    """Start the API service."""
    print("\n🚀 Starting 4Runr Outreach System API")
    print("=" * 50)
    
    try:
        # Import and start the API
        from api import main
        
        print("Starting API service on http://localhost:8080")
        print("Health check available at: http://localhost:8080/health")
        print("Pipeline status at: http://localhost:8080/pipeline/status")
        print("System info at: http://localhost:8080/system/info")
        print("\nPress Ctrl+C to stop the service")
        print("-" * 50)
        
        # Start the service
        main()
        
    except KeyboardInterrupt:
        print("\n\n👋 Service stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Failed to start API service: {e}")
        return False


def main():
    """Main startup function."""
    print("🏁 4Runr Outreach System Startup")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n💡 To fix environment issues:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your API keys and configuration")
        print("3. Run this script again")
        return False
    
    # Start the service
    return start_api_service()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)