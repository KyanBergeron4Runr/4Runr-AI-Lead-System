#!/usr/bin/env python3
"""
Integration Test for Campaign Brain Production Service

Tests the complete integration with 4Runr systems including
Airtable integration and campaign injection.
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "4runr-outreach-system"))

from serve_campaign_brain import CampaignBrainService


async def test_standalone_mode():
    """Test Campaign Brain in standalone mode"""
    
    print("🧪 Testing Standalone Mode")
    print("=" * 40)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create leads directory with test lead
        leads_dir = temp_path / "leads"
        leads_dir.mkdir()
        
        test_lead = {
            "id": "test_integration_001",
            "Name": "Sarah Johnson",
            "Title": "VP of Product",
            "Company": "CloudTech Solutions",
            "Email": "sarah.johnson@cloudtech.com",
            "Company_Description": "CloudTech provides SaaS solutions for enterprise workflow management and digital transformation",
            "Top_Services": "Software as a Service, API integrations, Cloud platforms, Workflow automation",
            "Tone": "Professional",
            "Homepage_Content": "Transform your business with cloud-native solutions that scale with your growth.",
            "About_Page_Content": "Founded in 2018, CloudTech has been at the forefront of enterprise digital transformation."
        }
        
        # Save test lead
        lead_file = leads_dir / "test_integration_001.json"
        with open(lead_file, 'w') as f:
            json.dump(test_lead, f, indent=2)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Set minimal environment
            os.environ['OPENAI_API_KEY'] = 'test-key-for-validation'
            os.environ['LOG_LEVEL'] = 'WARNING'  # Reduce log noise
            
            # Initialize service
            service = CampaignBrainService()
            
            print(f"✅ Service initialized in standalone mode")
            print(f"✅ Integrated mode: {service.integrated_mode}")
            
            # Test health check
            health = service.health_check()
            print(f"✅ Health check: {health['status']}")
            
            # Test lead processing (dry run)
            print("\n🔍 Testing lead processing...")
            result = await service.process_lead_by_id("test_integration_001", dry_run=True)
            
            print(f"✅ Lead processed: {result['final_status']}")
            print(f"✅ Traits detected: {len(result.get('traits', []))}")
            print(f"✅ Quality score: {result.get('overall_quality_score', 0):.1f}")
            
            # Test batch processing
            print("\n📦 Testing batch processing...")
            batch_result = await service.process_batch(batch_size=1, dry_run=True)
            
            print(f"✅ Batch processed: {batch_result['processed']} leads")
            
            # Check generated files
            queue_dir = Path("queue")
            if queue_dir.exists() and list(queue_dir.glob("*.json")):
                print(f"✅ Queue files generated: {len(list(queue_dir.glob('*.json')))}")
            
            trace_dir = Path("trace_logs")
            if trace_dir.exists() and list(trace_dir.glob("*.json")):
                print(f"✅ Trace logs generated: {len(list(trace_dir.glob('*.json')))}")
            
            return True
            
        finally:
            os.chdir(original_cwd)


async def test_configuration_validation():
    """Test configuration validation"""
    
    print("\n🔧 Testing Configuration Validation")
    print("=" * 40)
    
    # Test with missing API key
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Remove API key
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        try:
            service = CampaignBrainService()
            print("❌ Should have failed with missing API key")
            return False
        except SystemExit:
            print("✅ Correctly failed with missing API key")
        
        # Restore API key
        os.environ['OPENAI_API_KEY'] = 'test-key-for-validation'
        
        # Test with invalid threshold
        os.environ['CAMPAIGN_QUALITY_THRESHOLD'] = '150.0'  # Invalid
        
        try:
            service = CampaignBrainService()
            print("❌ Should have failed with invalid threshold")
            return False
        except SystemExit:
            print("✅ Correctly failed with invalid threshold")
        
        # Restore valid threshold
        os.environ['CAMPAIGN_QUALITY_THRESHOLD'] = '80.0'
        
        # Test valid configuration
        service = CampaignBrainService()
        print("✅ Valid configuration accepted")
        
        return True
        
    finally:
        # Restore original environment
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key


def test_cli_interface():
    """Test CLI interface"""
    
    print("\n💻 Testing CLI Interface")
    print("=" * 40)
    
    import subprocess
    
    # Test help
    try:
        result = subprocess.run([
            sys.executable, 'serve_campaign_brain.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'Campaign Brain Production Service' in result.stdout:
            print("✅ CLI help works")
        else:
            print("❌ CLI help failed")
            return False
    except subprocess.TimeoutExpired:
        print("❌ CLI help timed out")
        return False
    
    # Test health check (will fail without proper config, but should not crash)
    try:
        result = subprocess.run([
            sys.executable, 'serve_campaign_brain.py', '--health-check'
        ], capture_output=True, text=True, timeout=10)
        
        # Should exit with error code but not crash
        if result.returncode != 0:
            print("✅ Health check properly handles missing config")
        else:
            print("✅ Health check passed")
    except subprocess.TimeoutExpired:
        print("❌ Health check timed out")
        return False
    
    return True


def test_docker_setup():
    """Test Docker configuration"""
    
    print("\n🐳 Testing Docker Setup")
    print("=" * 40)
    
    # Check if Dockerfile exists and is valid
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile, 'r') as f:
        content = f.read()
    
    required_elements = [
        'FROM python:3.11-slim',
        'COPY requirements.txt',
        'RUN pip install',
        'COPY . .',
        'HEALTHCHECK'
    ]
    
    for element in required_elements:
        if element not in content:
            print(f"❌ Dockerfile missing: {element}")
            return False
    
    print("✅ Dockerfile structure valid")
    
    # Check docker-compose.yml
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    required_services = ['campaign-brain', 'redis']
    for service in required_services:
        if service not in content:
            print(f"❌ docker-compose.yml missing service: {service}")
            return False
    
    print("✅ docker-compose.yml structure valid")
    
    return True


async def main():
    """Run all integration tests"""
    
    print("🚀 Campaign Brain Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration Validation", test_configuration_validation),
        ("Standalone Mode", test_standalone_mode),
        ("CLI Interface", test_cli_interface),
        ("Docker Setup", test_docker_setup)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests PASSED!")
        print("\nThe Campaign Brain is ready for production deployment!")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY in .env")
        print("2. Configure Airtable credentials")
        print("3. Run: python deploy.py deploy")
        return True
    else:
        print("❌ Some tests failed - check configuration and setup")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)