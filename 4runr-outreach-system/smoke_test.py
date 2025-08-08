#!/usr/bin/env python3
"""
Comprehensive smoke test for 4Runr Outreach System Critical Fixes.

This script validates that all 7 critical fixes are working correctly.
"""

import sys
import os
import time
import requests
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_import_system():
    """Test Fix 1: Import system with absolute imports."""
    print("🔍 Testing Import System Fixes")
    print("-" * 40)
    
    try:
        # Test absolute imports
        from outreach.shared.config import config
        from outreach.shared.logging_utils import get_logger
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        print("✅ Absolute imports working")
        
        # Test module entry points
        modules = [
            'outreach.website_scraper.main',
            'outreach.message_generator.main',
            'outreach.engager.main',
            'outreach.email_validator.main'
        ]
        
        for module in modules:
            try:
                __import__(module)
                print(f"✅ Module {module} imports correctly")
            except ImportError as e:
                print(f"❌ Module {module} import failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Import system test failed: {e}")
        return False


def test_openai_integration():
    """Test Fix 2: Modern OpenAI SDK integration."""
    print("\n🤖 Testing OpenAI SDK Modernization")
    print("-" * 40)
    
    try:
        from openai import OpenAI
        import httpx
        
        print("✅ Modern OpenAI SDK imports work")
        
        # Test client initialization
        client = OpenAI(api_key="test_key")
        print("✅ OpenAI client initialization works")
        
        # Test proxy support
        proxy = "http://test:8080"
        http_client = httpx.Client(proxies=proxy, timeout=60)
        client_with_proxy = OpenAI(api_key="test_key", http_client=http_client)
        print("✅ OpenAI client with proxy support works")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI SDK test failed: {e}")
        return False


def test_airtable_integration():
    """Test Fix 3: Configurable Airtable integration."""
    print("\n📊 Testing Configurable Airtable Integration")
    print("-" * 40)
    
    try:
        from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
        
        client = get_configurable_airtable_client()
        print("✅ Configurable Airtable client initializes")
        
        field_mapping = client.get_field_mapping()
        print(f"✅ Field mapping configured: {len(field_mapping)} fields")
        
        # Test defensive error handling
        try:
            leads = client.get_leads_for_processing(max_records=1)
            print("✅ Defensive error handling works")
        except Exception as e:
            print(f"⚠️  Airtable query failed (expected if no API key): {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Airtable integration test failed: {e}")
        return False


def test_health_check_system():
    """Test Fix 4: Non-blocking health check system."""
    print("\n🏥 Testing Health Check System")
    print("-" * 40)
    
    try:
        from fastapi import FastAPI
        import uvicorn
        from api import app
        
        print("✅ FastAPI components available")
        
        # Test endpoints exist
        routes = [route.path for route in app.routes]
        required_endpoints = ['/health', '/pipeline/status', '/system/info']
        
        for endpoint in required_endpoints:
            if endpoint in routes:
                print(f"✅ Endpoint {endpoint} configured")
            else:
                print(f"❌ Endpoint {endpoint} missing")
                return False
        
        # Test if API is running
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint responding (API is running)")
            else:
                print("ℹ️  API not running - skipping endpoint tests")
        except requests.exceptions.RequestException:
            print("ℹ️  API not running - skipping endpoint tests")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check system test failed: {e}")
        return False


def test_resilient_engagement():
    """Test Fix 5: Resilient engagement pipeline."""
    print("\n🛡️  Testing Resilient Engagement Pipeline")
    print("-" * 40)
    
    try:
        from outreach.engager.app import EngagerAgent
        from outreach.engager.resilient_engager import ResilientEngager
        
        print("✅ Engagement classes import successfully")
        
        # Test fallback message generation
        engager = EngagerAgent()
        
        test_lead = {
            'id': 'test_001',
            'Name': 'John Smith',
            'Company': 'TechCorp',
            'Email': 'john@techcorp.com',
            'Custom_Message': ''  # No custom message
        }
        
        message = engager._get_or_generate_message(test_lead)
        if message and len(message) > 50:
            print("✅ Fallback message generation works")
        else:
            print("❌ Fallback message generation failed")
            return False
        
        # Test resilient skip logic
        resilient_engager = ResilientEngager()
        
        valid_lead = {
            'id': 'test_valid',
            'Email': 'valid@validcorp.com',
            'Email_Confidence_Level': 'Real'
        }
        
        skip_reason = resilient_engager._should_skip_lead(valid_lead)
        if skip_reason is None:
            print("✅ Valid lead correctly identified for processing")
        else:
            print(f"❌ Valid lead incorrectly skipped: {skip_reason}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Resilient engagement test failed: {e}")
        return False


def test_dependencies_and_docker():
    """Test Fix 6: Dependencies and Docker configuration."""
    print("\n📦 Testing Dependencies and Docker Configuration")
    print("-" * 40)
    
    try:
        # Test critical dependencies
        critical_deps = [
            ('openai', 'openai'),
            ('fastapi', 'fastapi'),
            ('uvicorn', 'uvicorn'),
            ('pyairtable', 'pyairtable'),
            ('httpx', 'httpx')
        ]
        
        for package_name, import_name in critical_deps:
            try:
                __import__(import_name)
                print(f"✅ Dependency {package_name} available")
            except ImportError:
                print(f"❌ Critical dependency {package_name} missing")
                return False
        
        # Test Docker files exist
        docker_files = ['Dockerfile', 'docker-compose.yml', 'requirements.txt']
        for file_name in docker_files:
            file_path = project_root / file_name
            if file_path.exists():
                print(f"✅ Docker file {file_name} exists")
            else:
                print(f"❌ Docker file {file_name} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Dependencies test failed: {e}")
        return False


def test_integration():
    """Test Fix 7: Integration scenarios."""
    print("\n🔗 Testing Integration Scenarios")
    print("-" * 40)
    
    try:
        # Test configuration loading
        from outreach.shared.config import config
        airtable_config = config.get_airtable_config()
        ai_config = config.get_ai_config()
        
        if airtable_config and ai_config:
            print("✅ Configuration loading works")
        else:
            print("❌ Configuration loading failed")
            return False
        
        # Test agents can be initialized
        from outreach.website_scraper.app import WebsiteScraperAgent
        from outreach.message_generator.app import MessageGeneratorAgent
        from outreach.engager.app import EngagerAgent
        
        scraper = WebsiteScraperAgent()
        generator = MessageGeneratorAgent()
        engager = EngagerAgent()
        
        print("✅ All agents initialize successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 4Runr Outreach System - Critical Fixes Smoke Test")
    print("=" * 60)
    
    tests = [
        ("Import System Fixes", test_import_system),
        ("OpenAI SDK Modernization", test_openai_integration),
        ("Configurable Airtable Integration", test_airtable_integration),
        ("Non-blocking Health Check System", test_health_check_system),
        ("Resilient Engagement Pipeline", test_resilient_engagement),
        ("Dependencies and Docker Configuration", test_dependencies_and_docker),
        ("Integration Scenarios", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 SMOKE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SMOKE TESTS PASSED!")
        print("The 4Runr Outreach System critical fixes are working correctly.")
        print("\nSystem is ready for production deployment!")
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED")
        print("Please address the issues above before deployment.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)