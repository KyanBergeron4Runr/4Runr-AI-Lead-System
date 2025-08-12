#!/usr/bin/env python3
"""
Installation Verification Script

Quick script to verify that the 4Runr Outreach System is properly installed
and configured for use.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Verify installation and configuration."""
    print("🔍 4Runr Outreach System Installation Verification")
    print("=" * 55)
    
    all_good = True
    
    # Test 1: Dependencies
    print("1. Testing dependencies...")
    try:
        import requests
        import openai
        from bs4 import BeautifulSoup
        from pyairtable import Api
        import validators
        from dotenv import load_dotenv
        from jinja2 import Template
        from playwright.async_api import async_playwright
        print("   ✅ All required dependencies available")
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        all_good = False
    
    # Test 2: Environment file
    print("\n2. Checking environment configuration...")
    env_file = Path(".env")
    if env_file.exists():
        print("   ✅ .env file exists")
        
        # Check for key variables
        try:
            load_dotenv()
            import os
            required_vars = ["AIRTABLE_API_KEY", "OPENAI_API_KEY"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"   ⚠️  Please configure these variables in .env: {', '.join(missing_vars)}")
            else:
                print("   ✅ Key environment variables configured")
                
        except Exception as e:
            print(f"   ⚠️  Could not validate environment variables: {e}")
    else:
        print("   ❌ .env file not found (copy from .env.example)")
        all_good = False
    
    # Test 3: Knowledge base
    print("\n3. Testing knowledge base...")
    try:
        from engager.knowledge_base_loader import KnowledgeBaseLoader
        loader = KnowledgeBaseLoader()
        is_valid = loader.validate_knowledge_base()
        
        if is_valid:
            print("   ✅ Knowledge base validation passed")
        else:
            print("   ❌ Knowledge base validation failed")
            all_good = False
            
    except Exception as e:
        print(f"   ❌ Knowledge base test failed: {e}")
        all_good = False
    
    # Test 4: System integration
    print("\n4. Testing system integration...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "engager.enhanced_engager_agent", 
            "--dry-run", "--limit", "1"
        ], capture_output=True, text=True, timeout=30)
        
        output = result.stdout + result.stderr
        
        if "4Runr knowledge base loaded successfully" in output:
            print("   ✅ System integration test passed")
        else:
            print("   ⚠️  System integration test completed with warnings")
            print("       (This may be due to missing API keys)")
            
    except Exception as e:
        print(f"   ❌ System integration test failed: {e}")
        all_good = False
    
    # Summary
    print("\n" + "=" * 55)
    if all_good:
        print("🎉 INSTALLATION VERIFIED!")
        print("   The system is ready for use.")
        print("\n📋 Next steps:")
        print("   1. Configure API keys in .env file if not done")
        print("   2. Run: python -m engager.enhanced_engager_agent --dry-run --limit 1")
        print("   3. See SETUP.md for detailed usage instructions")
    else:
        print("⚠️  INSTALLATION ISSUES DETECTED!")
        print("   Please fix the issues above before using the system.")
        print("\n📋 Troubleshooting:")
        print("   1. Run: pip install -r requirements.txt")
        print("   2. Copy .env.example to .env and configure API keys")
        print("   3. See SETUP.md for detailed troubleshooting")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)