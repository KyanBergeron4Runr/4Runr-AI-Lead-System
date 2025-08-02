#!/usr/bin/env python3
"""
Comprehensive System Test for 4Runr AI Lead System

This script runs a complete system-wide test to check what's working and what isn't.
It provides organized results so we know exactly what's functional.
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system-test')

class SystemTester:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.shared_dir = self.root_dir / 'shared'
        self.logs_dir = self.root_dir / 'logs'
        
        # Test results
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'environment': {},
            'pipeline_components': {},
            'data_flow': {},
            'integrations': {},
            'issues': [],
            'recommendations': []
        }
        
        # Ensure directories exist
        self.shared_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def log_test_section(self, section: str):
        """Log a test section header"""
        logger.info("\n" + "="*80)
        logger.info(f"🧪 TESTING: {section.upper()}")
        logger.info("="*80)
    
    def run_command(self, command: List[str], timeout: int = 60, cwd: Path = None) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.root_dir,
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def test_environment(self) -> Dict[str, Any]:
        """Test environment setup and dependencies"""
        self.log_test_section("Environment Setup")
        
        env_results = {
            'python_version': 'unknown',
            'required_files': {},
            'environment_variables': {},
            'dependencies': {}
        }
        
        # Check Python version
        try:
            env_results['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            logger.info(f"✅ Python version: {env_results['python_version']}")
        except Exception as e:
            logger.error(f"❌ Python version check failed: {e}")
            self.test_results['issues'].append(f"Python version check failed: {e}")
        
        # Check required files
        required_files = [
            '.env',
            'pipeline_cli.py',
            'run_validation_pipeline.py',
            'verify_pipeline_health.py',
            'scraper/app.py',
            'verifier/app.py',
            'enricher/app.py'
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            exists = full_path.exists()
            env_results['required_files'][file_path] = exists
            
            if exists:
                logger.info(f"✅ Found: {file_path}")
            else:
                logger.error(f"❌ Missing: {file_path}")
                self.test_results['issues'].append(f"Missing required file: {file_path}")
        
        # Check environment variables
        required_env_vars = [
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME',
            'LINKEDIN_EMAIL',
            'LINKEDIN_PASSWORD'
        ]
        
        for env_var in required_env_vars:
            value = os.getenv(env_var)
            has_value = bool(value and value.strip())
            env_results['environment_variables'][env_var] = has_value
            
            if has_value:
                logger.info(f"✅ Environment variable set: {env_var}")
            else:
                logger.error(f"❌ Missing environment variable: {env_var}")
                self.test_results['issues'].append(f"Missing environment variable: {env_var}")
        
        # Check Python dependencies
        dependencies = ['playwright', 'airtable-python-wrapper', 'requests', 'asyncio']
        
        for dep in dependencies:
            try:
                __import__(dep.replace('-', '_'))
                env_results['dependencies'][dep] = True
                logger.info(f"✅ Dependency available: {dep}")
            except ImportError:
                env_results['dependencies'][dep] = False
                logger.error(f"❌ Missing dependency: {dep}")
                self.test_results['issues'].append(f"Missing Python dependency: {dep}")
        
        return env_results
    
    def test_pipeline_components(self) -> Dict[str, Any]:
        """Test individual pipeline components"""
        self.log_test_section("Pipeline Components")
        
        components = {
            'scraper': {'script': 'scraper/app.py', 'timeout': 300},
            'verifier': {'script': 'verifier/app.py', 'timeout': 180},
            'enricher': {'script': 'enricher/app.py', 'timeout': 120}
        }
        
        component_results = {}
        
        for component, config in components.items():
            logger.info(f"🧪 Testing {component} component...")
            
            script_path = self.root_dir / config['script']
            
            if not script_path.exists():
                component_results[component] = {
                    'available': False,
                    'error': f"Script not found: {config['script']}"
                }
                logger.error(f"❌ {component}: Script not found")
                continue
            
            # Test if script can be imported/executed
            success, stdout, stderr = self.run_command(
                [sys.executable, '-c', f'import sys; sys.path.append("{script_path.parent}"); import app'],
                timeout=30,
                cwd=script_path.parent
            )
            
            component_results[component] = {
                'available': success,
                'script_path': str(script_path),
                'import_test': success
            }
            
            if success:
                logger.info(f"✅ {component}: Component available")
            else:
                logger.error(f"❌ {component}: Import failed - {stderr}")
                component_results[component]['error'] = stderr
                self.test_results['issues'].append(f"{component} component import failed: {stderr}")
        
        return component_results
    
    def test_data_flow(self) -> Dict[str, Any]:
        """Test data flow and file integrity"""
        self.log_test_section("Data Flow & File Integrity")
        
        pipeline_files = {
            'raw_leads.json': 'Raw leads from scraper',
            'verified_leads.json': 'Verified LinkedIn profiles',
            'enriched_leads.json': 'Enriched leads with contact info',
            'engaged_leads.json': 'Leads that were contacted',
            'dropped_leads.json': 'Leads dropped during validation'
        }
        
        data_flow_results = {
            'files': {},
            'data_integrity': {},
            'pipeline_progression': {}
        }
        
        total_leads_by_stage = {}
        
        for filename, description in pipeline_files.items():
            file_path = self.shared_dir / filename
            
            file_info = {
                'exists': file_path.exists(),
                'description': description,
                'lead_count': 0,
                'file_size': 0,
                'last_modified': None,
                'valid_json': False
            }
            
            if file_path.exists():
                try:
                    file_info['file_size'] = file_path.stat().st_size
                    file_info['last_modified'] = datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                    
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        file_info['valid_json'] = True
                        file_info['lead_count'] = len(data) if isinstance(data, list) else 0
                        
                        # Store for progression analysis
                        stage_name = filename.replace('.json', '')
                        total_leads_by_stage[stage_name] = file_info['lead_count']
                        
                        logger.info(f"✅ {filename}: {file_info['lead_count']} leads")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ {filename}: Invalid JSON - {e}")
                    file_info['json_error'] = str(e)
                    self.test_results['issues'].append(f"Invalid JSON in {filename}: {e}")
                except Exception as e:
                    logger.error(f"❌ {filename}: Error reading file - {e}")
                    file_info['read_error'] = str(e)
                    self.test_results['issues'].append(f"Error reading {filename}: {e}")
            else:
                logger.info(f"⚪ {filename}: File not found")
            
            data_flow_results['files'][filename] = file_info
        
        # Analyze pipeline progression
        if total_leads_by_stage:
            raw_count = total_leads_by_stage.get('raw_leads', 0)
            verified_count = total_leads_by_stage.get('verified_leads', 0)
            enriched_count = total_leads_by_stage.get('enriched_leads', 0)
            engaged_count = total_leads_by_stage.get('engaged_leads', 0)
            
            progression = {
                'raw_leads': raw_count,
                'verified_leads': verified_count,
                'enriched_leads': enriched_count,
                'engaged_leads': engaged_count,
                'conversion_rates': {}
            }
            
            # Calculate conversion rates
            if raw_count > 0:
                progression['conversion_rates']['verification_rate'] = round((verified_count / raw_count) * 100, 1)
            if verified_count > 0:
                progression['conversion_rates']['enrichment_rate'] = round((enriched_count / verified_count) * 100, 1)
            if enriched_count > 0:
                progression['conversion_rates']['engagement_rate'] = round((engaged_count / enriched_count) * 100, 1)
            
            data_flow_results['pipeline_progression'] = progression
            
            logger.info(f"📊 Pipeline progression: {raw_count} → {verified_count} → {enriched_count} → {engaged_count}")
        
        return data_flow_results
    
    def test_integrations(self) -> Dict[str, Any]:
        """Test external integrations"""
        self.log_test_section("External Integrations")
        
        integration_results = {
            'airtable': {'available': False, 'tested': False},
            'linkedin': {'available': False, 'tested': False},
            'playwright': {'available': False, 'tested': False}
        }
        
        # Test Airtable integration
        try:
            success, stdout, stderr = self.run_command([
                sys.executable, '-c', 
                'from shared.airtable_client import AirtableClient; print("Airtable client available")'
            ], timeout=30)
            
            integration_results['airtable']['available'] = success
            
            if success:
                logger.info("✅ Airtable: Client available")
            else:
                logger.error(f"❌ Airtable: Client not available - {stderr}")
                self.test_results['issues'].append(f"Airtable client not available: {stderr}")
                
        except Exception as e:
            logger.error(f"❌ Airtable: Test failed - {e}")
            integration_results['airtable']['error'] = str(e)
        
        # Test Playwright availability
        try:
            success, stdout, stderr = self.run_command([
                sys.executable, '-c', 
                'from playwright.async_api import async_playwright; print("Playwright available")'
            ], timeout=30)
            
            integration_results['playwright']['available'] = success
            
            if success:
                logger.info("✅ Playwright: Available")
            else:
                logger.error(f"❌ Playwright: Not available - {stderr}")
                self.test_results['issues'].append(f"Playwright not available: {stderr}")
                
        except Exception as e:
            logger.error(f"❌ Playwright: Test failed - {e}")
            integration_results['playwright']['error'] = str(e)
        
        return integration_results
    
    def test_pipeline_health(self) -> Dict[str, Any]:
        """Test overall pipeline health"""
        self.log_test_section("Pipeline Health Check")
        
        health_results = {'health_check_available': False, 'health_status': 'unknown'}
        
        # Run the health check script
        success, stdout, stderr = self.run_command([
            sys.executable, 'verify_pipeline_health.py'
        ], timeout=120)
        
        health_results['health_check_available'] = success
        
        if success:
            logger.info("✅ Pipeline health check completed successfully")
            health_results['health_status'] = 'healthy'
        else:
            logger.error(f"❌ Pipeline health check failed: {stderr}")
            health_results['health_status'] = 'unhealthy'
            health_results['error'] = stderr
            self.test_results['issues'].append(f"Pipeline health check failed: {stderr}")
        
        return health_results
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check critical issues
        critical_issues = len(self.test_results['issues'])
        
        if critical_issues == 0:
            recommendations.append("✅ No critical issues detected - system appears healthy")
        else:
            recommendations.append(f"⚠️ {critical_issues} issues detected - review and fix before production use")
        
        # Environment recommendations
        env = self.test_results.get('environment', {})
        missing_env_vars = [k for k, v in env.get('environment_variables', {}).items() if not v]
        
        if missing_env_vars:
            recommendations.append(f"🔧 Set missing environment variables: {', '.join(missing_env_vars)}")
        
        # Component recommendations
        components = self.test_results.get('pipeline_components', {})
        unavailable_components = [k for k, v in components.items() if not v.get('available', False)]
        
        if unavailable_components:
            recommendations.append(f"🔧 Fix unavailable components: {', '.join(unavailable_components)}")
        
        # Data flow recommendations
        data_flow = self.test_results.get('data_flow', {})
        files = data_flow.get('files', {})
        
        if not files.get('raw_leads.json', {}).get('exists'):
            recommendations.append("🚀 Run scraper to generate initial leads: python pipeline_cli.py scraper")
        
        if not files.get('verified_leads.json', {}).get('exists'):
            recommendations.append("🔍 Run verifier to validate leads: python pipeline_cli.py verifier")
        
        # Integration recommendations
        integrations = self.test_results.get('integrations', {})
        
        if not integrations.get('airtable', {}).get('available'):
            recommendations.append("🔧 Fix Airtable integration - check API credentials")
        
        if not integrations.get('playwright', {}).get('available'):
            recommendations.append("🔧 Install Playwright: pip install playwright && playwright install chromium")
        
        self.test_results['recommendations'] = recommendations
    
    def determine_overall_status(self):
        """Determine overall system status"""
        issues_count = len(self.test_results['issues'])
        
        # Check critical components
        env = self.test_results.get('environment', {})
        components = self.test_results.get('pipeline_components', {})
        integrations = self.test_results.get('integrations', {})
        
        # Critical failures
        missing_critical_env = not all(env.get('environment_variables', {}).values())
        missing_critical_components = not all(c.get('available', False) for c in components.values())
        missing_critical_integrations = not integrations.get('airtable', {}).get('available', False)
        
        if missing_critical_env or missing_critical_components or missing_critical_integrations:
            self.test_results['overall_status'] = 'critical'
        elif issues_count > 0:
            self.test_results['overall_status'] = 'warning'
        else:
            self.test_results['overall_status'] = 'healthy'
    
    def print_summary_report(self):
        """Print a comprehensive summary report"""
        results = self.test_results
        
        print("\n" + "="*100)
        print("🧪 COMPREHENSIVE SYSTEM TEST RESULTS")
        print("="*100)
        
        # Overall status
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🚨',
            'unknown': '❓'
        }
        
        overall_status = results['overall_status']
        print(f"\n{status_emoji.get(overall_status, '❓')} OVERALL SYSTEM STATUS: {overall_status.upper()}")
        
        # Environment summary
        print(f"\n🌍 ENVIRONMENT:")
        env = results.get('environment', {})
        env_vars = env.get('environment_variables', {})
        env_ok = all(env_vars.values())
        print(f"   Environment Variables: {'✅ All set' if env_ok else '❌ Missing variables'}")
        print(f"   Python Version: {env.get('python_version', 'Unknown')}")
        
        # Components summary
        print(f"\n🤖 PIPELINE COMPONENTS:")
        components = results.get('pipeline_components', {})
        for component, info in components.items():
            status = "✅" if info.get('available') else "❌"
            print(f"   {status} {component.capitalize()}: {'Available' if info.get('available') else 'Unavailable'}")
        
        # Data flow summary
        print(f"\n📊 DATA FLOW:")
        data_flow = results.get('data_flow', {})
        files = data_flow.get('files', {})
        
        for filename, info in files.items():
            if info.get('exists'):
                print(f"   ✅ {filename}: {info.get('lead_count', 0)} leads")
            else:
                print(f"   ⚪ {filename}: Not found")
        
        # Pipeline progression
        progression = data_flow.get('pipeline_progression', {})
        if progression:
            print(f"\n🔄 PIPELINE PROGRESSION:")
            print(f"   Raw → Verified → Enriched → Engaged")
            print(f"   {progression.get('raw_leads', 0)} → {progression.get('verified_leads', 0)} → {progression.get('enriched_leads', 0)} → {progression.get('engaged_leads', 0)}")
            
            rates = progression.get('conversion_rates', {})
            if rates:
                print(f"   Conversion rates: Verification {rates.get('verification_rate', 0)}%, Enrichment {rates.get('enrichment_rate', 0)}%, Engagement {rates.get('engagement_rate', 0)}%")
        
        # Integrations summary
        print(f"\n🔗 INTEGRATIONS:")
        integrations = results.get('integrations', {})
        for integration, info in integrations.items():
            status = "✅" if info.get('available') else "❌"
            print(f"   {status} {integration.capitalize()}: {'Available' if info.get('available') else 'Unavailable'}")
        
        # Issues
        if results.get('issues'):
            print(f"\n❌ ISSUES DETECTED ({len(results['issues'])}):")
            for i, issue in enumerate(results['issues'][:10], 1):  # Show first 10 issues
                print(f"   {i}. {issue}")
            if len(results['issues']) > 10:
                print(f"   ... and {len(results['issues']) - 10} more issues")
        
        # Recommendations
        if results.get('recommendations'):
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print(f"\n📅 Test completed: {results['timestamp']}")
        print("="*100)
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.logs_dir / f"system_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"💾 Test results saved to {results_file}")
        return results_file
    
    async def run_comprehensive_test(self):
        """Run the complete system test"""
        logger.info("🚀 Starting Comprehensive System Test")
        
        # Test environment
        self.test_results['environment'] = self.test_environment()
        
        # Test pipeline components
        self.test_results['pipeline_components'] = self.test_pipeline_components()
        
        # Test data flow
        self.test_results['data_flow'] = self.test_data_flow()
        
        # Test integrations
        self.test_results['integrations'] = self.test_integrations()
        
        # Test pipeline health
        health_results = self.test_pipeline_health()
        self.test_results['pipeline_health'] = health_results
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Determine overall status
        self.determine_overall_status()
        
        # Print summary
        self.print_summary_report()
        
        # Save results
        results_file = self.save_results()
        
        return self.test_results

async def main():
    """Main entry point"""
    tester = SystemTester()
    results = await tester.run_comprehensive_test()
    
    # Return appropriate exit code
    overall_status = results['overall_status']
    if overall_status == 'critical':
        logger.error("🚨 System test failed - critical issues detected")
        return False
    elif overall_status == 'warning':
        logger.warning("⚠️ System test completed with warnings")
        return True
    else:
        logger.info("✅ System test passed - all components healthy")
        return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)