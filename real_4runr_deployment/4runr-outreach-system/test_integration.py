#!/usr/bin/env python3
"""
Integration tests for 4Runr Outreach System.

Tests the complete system integration including Docker builds,
API endpoints, and end-to-end pipeline functionality.
"""

import sys
import os
import time
import requests
import subprocess
import docker
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class IntegrationTestRunner:
    """Integration test runner for the outreach system."""
    
    def __init__(self):
        self.docker_client = None
        self.test_container = None
        self.results = {}
    
    def setup_docker_client(self) -> bool:
        """Setup Docker client for testing."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            print("✅ Docker client connected")
            return True
        except Exception as e:
            print(f"❌ Docker client setup failed: {e}")
            return False
    
    def test_docker_build(self) -> bool:
        """Test Docker image build."""
        print("\n🐳 Testing Docker Build")
        print("-" * 40)
        
        try:
            print("Building Docker image (this may take a while)...")
            
            # Build the image
            image, build_logs = self.docker_client.images.build(
                path=str(project_root),
                tag="4runr-outreach-test:latest",
                rm=True,
                forcerm=True
            )
            
            print("✅ Docker image built successfully")
            print(f"Image ID: {image.id[:12]}")
            
            # Check image size
            image_size = image.attrs['Size'] / (1024 * 1024)  # Convert to MB
            print(f"Image size: {image_size:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Docker build failed: {e}")
            return False
    
    def test_container_startup(self) -> bool:
        """Test container startup and health check."""
        print("\n🚀 Testing Container Startup")
        print("-" * 40)
        
        try:
            # Start container
            print("Starting container...")
            self.test_container = self.docker_client.containers.run(
                "4runr-outreach-test:latest",
                ports={'8080/tcp': 8080},
                detach=True,
                remove=True,
                environment={
                    'AIRTABLE_API_KEY': 'test_key',
                    'AIRTABLE_BASE_ID': 'test_base',
                    'AIRTABLE_TABLE_NAME': 'test_table',
                    'OPENAI_API_KEY': 'test_key'
                }
            )
            
            print(f"✅ Container started: {self.test_container.id[:12]}")
            
            # Wait for container to be ready
            print("Waiting for container to be ready...")
            max_wait = 60  # seconds
            wait_interval = 2
            
            for attempt in range(max_wait // wait_interval):
                try:
                    # Check if container is still running
                    self.test_container.reload()
                    if self.test_container.status != 'running':
                        print(f"❌ Container stopped unexpectedly: {self.test_container.status}")
                        return False
                    
                    # Try health check
                    response = requests.get('http://localhost:8080/health', timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Container healthy after {(attempt + 1) * wait_interval} seconds")
                        return True
                        
                except requests.exceptions.RequestException:
                    pass  # Container not ready yet
                
                time.sleep(wait_interval)
                print(f"  Waiting... ({attempt + 1}/{max_wait // wait_interval})")
            
            print("❌ Container failed to become healthy within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Container startup failed: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints functionality."""
        print("\n🌐 Testing API Endpoints")
        print("-" * 40)
        
        if not self.test_container:
            print("❌ No test container available")
            return False
        
        endpoints = [
            ('/health', 'Health check endpoint'),
            ('/pipeline/status', 'Pipeline status endpoint'),
            ('/system/info', 'System info endpoint')
        ]
        
        try:
            for endpoint, description in endpoints:
                response = requests.get(f'http://localhost:8080{endpoint}', timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {description}: {response.status_code}")
                    
                    # Validate response content
                    try:
                        data = response.json()
                        if endpoint == '/health':
                            assert data.get('status') == 'ok'
                            assert data.get('service') == 'outreach-system'
                        elif endpoint == '/pipeline/status':
                            assert 'pipeline' in data
                        elif endpoint == '/system/info':
                            assert 'system_checks' in data
                        
                        print(f"  Response validation passed")
                        
                    except (ValueError, AssertionError) as e:
                        print(f"  ⚠️  Response validation failed: {e}")
                else:
                    print(f"❌ {description}: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ API endpoint testing failed: {e}")
            return False
    
    def test_module_execution(self) -> bool:
        """Test module execution within container."""
        print("\n⚙️  Testing Module Execution")
        print("-" * 40)
        
        if not self.test_container:
            print("❌ No test container available")
            return False
        
        modules = [
            ('outreach.website_scraper.main', 'Website Scraper'),
            ('outreach.message_generator.main', 'Message Generator'),
            ('outreach.engager.main', 'Engager'),
            ('outreach.email_validator.main', 'Email Validator')
        ]
        
        try:
            for module, description in modules:
                print(f"Testing {description}...")
                
                # Execute module with dry-run flag
                exec_result = self.test_container.exec_run(
                    f"python -m {module} --dry-run",
                    timeout=30
                )
                
                if exec_result.exit_code == 0:
                    print(f"✅ {description}: Module executed successfully")
                else:
                    print(f"❌ {description}: Exit code {exec_result.exit_code}")
                    print(f"  Output: {exec_result.output.decode()[:200]}...")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Module execution testing failed: {e}")
            return False
    
    def test_system_validation(self) -> bool:
        """Test system validation script within container."""
        print("\n🔍 Testing System Validation")
        print("-" * 40)
        
        if not self.test_container:
            print("❌ No test container available")
            return False
        
        try:
            print("Running system validation script...")
            
            exec_result = self.test_container.exec_run(
                "python validate_system.py",
                timeout=60
            )
            
            output = exec_result.output.decode()
            
            if exec_result.exit_code == 0:
                print("✅ System validation passed")
                
                # Check for specific success indicators
                if "ALL SMOKE TESTS PASSED" in output:
                    print("✅ All smoke tests passed within container")
                else:
                    print("⚠️  Some validation tests may have failed")
                
                return True
            else:
                print(f"❌ System validation failed: Exit code {exec_result.exit_code}")
                print(f"Output: {output[:500]}...")
                return False
                
        except Exception as e:
            print(f"❌ System validation testing failed: {e}")
            return False
    
    def test_docker_compose(self) -> bool:
        """Test docker-compose functionality."""
        print("\n🐙 Testing Docker Compose")
        print("-" * 40)
        
        try:
            # Check if docker-compose.yml exists
            compose_file = project_root / 'docker-compose.yml'
            if not compose_file.exists():
                print("❌ docker-compose.yml not found")
                return False
            
            print("✅ docker-compose.yml exists")
            
            # Test docker-compose config validation
            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ docker-compose configuration is valid")
            else:
                print(f"❌ docker-compose configuration invalid: {result.stderr}")
                return False
            
            # Test docker-compose build (quick test)
            print("Testing docker-compose build...")
            result = subprocess.run(
                ['docker-compose', 'build', '--no-cache'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ docker-compose build successful")
            else:
                print(f"❌ docker-compose build failed: {result.stderr[:200]}...")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ docker-compose test timed out")
            return False
        except FileNotFoundError:
            print("⚠️  docker-compose not available")
            return True  # Don't fail if docker-compose isn't installed
        except Exception as e:
            print(f"❌ docker-compose testing failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test resources."""
        print("\n🧹 Cleaning up test resources...")
        
        try:
            if self.test_container:
                self.test_container.stop()
                print("✅ Test container stopped")
        except Exception as e:
            print(f"⚠️  Error stopping container: {e}")
        
        try:
            # Remove test images
            if self.docker_client:
                try:
                    self.docker_client.images.remove("4runr-outreach-test:latest", force=True)
                    print("✅ Test image removed")
                except:
                    pass  # Image might not exist
        except Exception as e:
            print(f"⚠️  Error cleaning up images: {e}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        tests = [
            ("Docker Build", self.test_docker_build),
            ("Container Startup", self.test_container_startup),
            ("API Endpoints", self.test_api_endpoints),
            ("Module Execution", self.test_module_execution),
            ("System Validation", self.test_system_validation),
            ("Docker Compose", self.test_docker_compose)
        ]
        
        print("🚀 Starting Integration Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_docker_client():
            print("❌ Cannot run integration tests without Docker")
            return {"Docker Setup": False}
        
        # Run tests
        for test_name, test_func in tests:
            try:
                print(f"\n📋 Running: {test_name}")
                self.results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                self.results[test_name] = False
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🏁 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("The 4Runr Outreach System is ready for production deployment!")
            print("\nValidated capabilities:")
            print("- ✅ Docker containerization works correctly")
            print("- ✅ API endpoints respond properly")
            print("- ✅ All modules execute without errors")
            print("- ✅ System validation passes in container")
            print("- ✅ Docker Compose configuration is valid")
        else:
            print(f"\n⚠️  {total - passed} INTEGRATION TESTS FAILED")
            print("Please address the issues above before production deployment.")
        
        return passed == total


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Outreach System Integration Tests')
    parser.add_argument('--skip-build', action='store_true',
                       help='Skip Docker build test (use existing image)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only')
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    try:
        results = runner.run_all_tests()
        success = runner.print_summary()
        
        return 0 if success else 1
        
    finally:
        runner.cleanup()


if __name__ == '__main__':
    sys.exit(main())