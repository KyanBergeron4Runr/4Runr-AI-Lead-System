#!/usr/bin/env python3
"""
System validation script for 4Runr Outreach System.

This script validates that all critical fixes are working correctly:
1. Import system with absolute imports
2. OpenAI SDK integration
3. Airtable configurable integration
4. Health check system
5. Resilient engagement pipeline
6. Dependencies and configuration
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_import_system():
    """Test that the import system works with absolute imports."""
    print("🔍 Testing Import System")
    print("=" * 40)
    
    try:
        # Test absolute imports
        from outreach.shared.config import config
        from outreach.shared.logging_utils import get_logger
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        print("✅ Absolute imports working correctly")
        
        # Test module entry points
        modules_to_test = [
            'outreach.website_scraper.main',
            'outreach.message_generator.main',
            'outreach.engager.main',
            'outreach.email_validator.main'
        ]
        
        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
                print(f"✅ Module {module_name} imports successfully")
            except ImportError as e:
                print(f"❌ Module {module_name} import failed: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import system test failed: {e}")
        return False


def test_openai_integration():
    """Test OpenAI SDK integration."""
    print("\n🤖 Testing OpenAI Integration")
    print("=" * 40)
    
    try:
        # Test modern OpenAI import
        from openai import OpenAI
        import httpx
        
        print("✅ Modern OpenAI SDK imports successfully")
        
        # Test client initialization (without making API calls)
        try:
            # Test without proxy
            client = OpenAI(api_key="test_key")
            print("✅ OpenAI client initialization works")
            
            # Test with proxy configuration
            proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
            if proxy:
                http_client = httpx.Client(proxies=proxy, timeout=60)
                client_with_proxy = OpenAI(api_key="test_key", http_client=http_client)
                print("✅ OpenAI client with proxy support works")
            else:
                print("ℹ️  No proxy configured, skipping proxy test")
            
            return True
            
        except Exception as e:
            print(f"❌ OpenAI client initialization failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ OpenAI integration test failed: {e}")
        return False


def test_airtable_integration():
    """Test configurable Airtable integration."""
    print("\n📊 Testing Airtable Integration")
    print("=" * 40)
    
    try:
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        # Test client initialization
        client = get_configurable_airtable_client()
        print("✅ Configurable Airtable client initializes")
        
        # Test field mapping
        field_mapping = client.get_field_mapping()
        print(f"✅ Field mapping loaded: {len(field_mapping)} fields configured")
        
        # Show field configuration
        print("📋 Configured field mappings:")
        for logical_name, airtable_field in field_mapping.items():
            print(f"  {logical_name}: '{airtable_field}'")
        
        # Test connection (if API key is available)
        if os.getenv('AIRTABLE_API_KEY'):
            try:
                connection_ok = client.test_connection()
                if connection_ok:
                    print("✅ Airtable connection test successful")
                else:
                    print("⚠️  Airtable connection test failed (check API key/base ID)")
            except Exception as e:
                print(f"⚠️  Airtable connection test error: {e}")
        else:
            print("ℹ️  No Airtable API key configured, skipping connection test")
        
        return True
        
    except Exception as e:
        print(f"❌ Airtable integration test failed: {e}")
        return False


def test_health_check_system():
    """Test health check system components."""
    print("\n🏥 Testing Health Check System")
    print("=" * 40)
    
    try:
        # Test FastAPI import
        from fastapi import FastAPI
        import uvicorn
        print("✅ FastAPI and uvicorn available")
        
        # Test API module
        from api import app
        print("✅ API module imports successfully")
        
        # Test health endpoint exists
        routes = [route.path for route in app.routes]
        if '/health' in routes:
            print("✅ Health endpoint configured")
        else:
            print("❌ Health endpoint not found")
            return False
        
        if '/pipeline/status' in routes:
            print("✅ Pipeline status endpoint configured")
        else:
            print("❌ Pipeline status endpoint not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Health check system test failed: {e}")
        return False


def test_resilient_engagement():
    """Test resilient engagement pipeline."""
    print("\n🛡️  Testing Resilient Engagement Pipeline")
    print("=" * 40)
    
    try:
        from outreach.engager.app import EngagerAgent
        from outreach.engager.resilient_engager import ResilientEngager
        
        print("✅ Engagement classes import successfully")
        
        # Test fallback message generation
        engager = EngagerAgent()
        
        # Test with sample lead data
        test_lead = {
            'id': 'test_001',
            'Name': 'Test User',
            'Company': 'Test Company',
            'Email': 'test@testcompany.com',
            'Custom_Message': ''  # No custom message - should generate fallback
        }
        
        message = engager._get_or_generate_message(test_lead)
        
        if message and len(message) > 50:
            print("✅ Fallback message generation works")
            print(f"  Generated message length: {len(message)} characters")
        else:
            print("❌ Fallback message generation failed")
            return False
        
        # Test resilient engager
        resilient_engager = ResilientEngager()
        
        # Test skip logic
        skip_reason = resilient_engager._should_skip_lead(test_lead)
        if skip_reason is None:  # Should not skip this valid lead
            print("✅ Resilient skip logic works correctly")
        else:
            print(f"⚠️  Skip logic may be too restrictive: {skip_reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Resilient engagement test failed: {e}")
        return False


def test_dependencies():
    """Test that all dependencies are properly installed."""
    print("\n📦 Testing Dependencies")
    print("=" * 40)
    
    required_packages = [
        'python-dotenv',
        'pyairtable',
        'validators',
        'requests',
        'beautifulsoup4',
        'playwright',
        'openai',
        'httpx',
        'jinja2',
        'fastapi',
        'uvicorn',
        'email-validator',
        'colorama',
        'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Convert package names to import names
            import_name = package.replace('-', '_')
            if import_name == 'beautifulsoup4':
                import_name = 'bs4'
            elif import_name == 'python_dotenv':
                import_name = 'dotenv'
            elif import_name == 'email_validator':
                import_name = 'email_validator'
            
            importlib.import_module(import_name)
            print(f"✅ {package}")
            
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required dependencies are installed")
        return True


def test_configuration():
    """Test system configuration."""
    print("\n⚙️  Testing Configuration")
    print("=" * 40)
    
    try:
        from outreach.shared.config import config
        
        # Test configuration loading
        airtable_config = config.get_airtable_config()
        ai_config = config.get_ai_config()
        system_config = config.get_system_config()
        
        print("✅ Configuration loading works")
        
        # Check critical configuration
        required_env_vars = [
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
            else:
                print(f"✅ {var} configured")
        
        optional_vars = [
            'OPENAI_API_KEY',
            'MS_GRAPH_CLIENT_ID'
        ]
        
        for var in optional_vars:
            if os.getenv(var):
                print(f"✅ {var} configured")
            else:
                print(f"⚠️  {var} not configured (optional)")
        
        if missing_vars:
            print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_docker_configuration():
    """Test Docker configuration."""
    print("\n🐳 Testing Docker Configuration")
    print("=" * 40)
    
    # Check if Docker files exist
    docker_files = [
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore'
    ]
    
    for file_name in docker_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} missing")
            return False
    
    # Check if build script exists
    build_script = project_root / 'build.sh'
    if build_script.exists():
        print("✅ build.sh exists")
    else:
        print("⚠️  build.sh missing (optional)")
    
    # Test Docker availability
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
        else:
            print("⚠️  Docker not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Docker not available or not in PATH")
    
    return True


def main():
    """Main validation function."""
    print("🚀 4Runr Outreach System Validation")
    print("=" * 60)
    print("Testing all critical fixes and system components...\n")
    
    # Run all tests
    tests = [
        ("Import System", test_import_system),
        ("OpenAI Integration", test_openai_integration),
        ("Airtable Integration", test_airtable_integration),
        ("Health Check System", test_health_check_system),
        ("Resilient Engagement", test_resilient_engagement),
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Docker Configuration", test_docker_configuration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Validation Summary")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("The 4Runr Outreach System is ready for deployment.")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: docker-compose up -d")
        print("3. Check health: curl http://localhost:8080/health")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("Please address the issues above before deployment.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)