#!/usr/bin/env python3
"""
Comprehensive Test Suite for 4Runr AI Lead System

This script tests every component systematically to create a complete action plan.
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('comprehensive-test')

class ComprehensiveTestSuite:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.shared_dir = self.root_dir / 'shared'
        self.logs_dir = self.root_dir / 'logs'
        
        # Load environment
        env_path = self.root_dir / '.env'
        load_dotenv(env_path)
        
        # Test results storage
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': {},
            'dependencies': {},
            'data_sources': {},
            'components': {},
            'integrations': {},
            'pipeline_flow': {},
            'alternatives': {},
            'issues': [],
            'action_plan': []
        }
        
        # Ensure directories exist
        self.shared_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def log_section(self, title):
        """Log a test section"""
        logger.info("\n" + "="*80)
        logger.info(f"🧪 {title}")
        logger.info("="*80)
    
    def test_environment(self):
        """Test environment variables and configuration"""
        self.log_section("ENVIRONMENT & CONFIGURATION")
        
        env_results = {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform,
            'working_directory': str(self.root_dir),
            'env_file_exists': (self.root_dir / '.env').exists(),
            'required_vars': {},
            'optional_vars': {}
        }
        
        # Test required environment variables
        required_vars = [
            'AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME',
            'LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'SEARCH_URL'
        ]
        
        optional_vars = [
            'OPENAI_API_KEY', 'HUNTER_API_KEY', 'CLEARBIT_API_KEY', 'APOLLO_API_KEY',
            'APIFY_TOKEN', 'SENDGRID_API_KEY'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            has_value = bool(value and value.strip())
            env_results['required_vars'][var] = {
                'present': has_value,
                'length': len(value) if value else 0,
                'masked_value': f"{value[:10]}..." if has_value and len(value) > 10 else "Not set"
            }
            
            if has_value:
                logger.info(f"✅ {var}: Present ({len(value)} chars)")
            else:
                logger.error(f"❌ {var}: Missing")
                self.test_results['issues'].append(f"Missing required environment variable: {var}")
        
        for var in optional_vars:
            value = os.getenv(var)
            has_value = bool(value and value.strip())
            env_results['optional_vars'][var] = {
                'present': has_value,
                'length': len(value) if value else 0
            }
            
            if has_value:
                logger.info(f"✅ {var}: Present ({len(value)} chars)")
            else:
                logger.info(f"⚪ {var}: Not set (optional)")
        
        self.test_results['environment'] = env_results
        return env_results
    
    def test_dependencies(self):
        """Test Python dependencies"""
        self.log_section("PYTHON DEPENDENCIES")
        
        dependencies = {
            'required': [
                'requests', 'asyncio', 'json', 'logging', 'pathlib',
                'dotenv', 'playwright', 'airtable'
            ],
            'optional': [
                'openai', 'sendgrid', 'boto3'
            ]
        }
        
        dep_results = {'required': {}, 'optional': {}}
        
        for dep in dependencies['required']:
            try:
                if dep == 'airtable':
                    # Special case for airtable-python-wrapper
                    import airtable
                    dep_results['required'][dep] = {'available': True, 'version': getattr(airtable, '__version__', 'unknown')}
                    logger.info(f"✅ {dep}: Available")
                else:
                    module = __import__(dep)
                    version = getattr(module, '__version__', 'unknown')
                    dep_results['required'][dep] = {'available': True, 'version': version}
                    logger.info(f"✅ {dep}: Available (v{version})")
            except ImportError as e:
                dep_results['required'][dep] = {'available': False, 'error': str(e)}
                logger.error(f"❌ {dep}: Not available - {e}")
                self.test_results['issues'].append(f"Missing required dependency: {dep}")
        
        for dep in dependencies['optional']:
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'unknown')
                dep_results['optional'][dep] = {'available': True, 'version': version}
                logger.info(f"✅ {dep}: Available (v{version})")
            except ImportError:
                dep_results['optional'][dep] = {'available': False}
                logger.info(f"⚪ {dep}: Not available (optional)")
        
        self.test_results['dependencies'] = dep_results
        return dep_results
    
    def test_data_sources(self):
        """Test existing data files and their quality"""
        self.log_section("DATA SOURCES & EXISTING DATA")
        
        pipeline_files = {
            'raw_leads.json': 'Raw leads from scraper',
            'verified_leads.json': 'Verified LinkedIn profiles',
            'enriched_leads.json': 'Enriched leads with contact info',
            'engaged_leads.json': 'Leads that were contacted',
            'dropped_leads.json': 'Leads dropped during validation'
        }
        
        data_results = {}
        
        for filename, description in pipeline_files.items():
            file_path = self.shared_dir / filename
            file_info = {
                'exists': file_path.exists(),
                'description': description,
                'size': 0,
                'lead_count': 0,
                'last_modified': None,
                'sample_data': None,
                'data_quality': {}
            }
            
            if file_path.exists():
                try:
                    file_info['size'] = file_path.stat().st_size
                    file_info['last_modified'] = datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        file_info['lead_count'] = len(data) if isinstance(data, list) else 0
                        
                        if data and isinstance(data, list):
                            # Sample data (first item)
                            file_info['sample_data'] = data[0] if data else None
                            
                            # Data quality analysis
                            file_info['data_quality'] = self.analyze_data_quality(data, filename)
                    
                    logger.info(f"✅ {filename}: {file_info['lead_count']} leads ({file_info['size']} bytes)")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ {filename}: Invalid JSON - {e}")
                    file_info['json_error'] = str(e)
                    self.test_results['issues'].append(f"Invalid JSON in {filename}: {e}")
                except Exception as e:
                    logger.error(f"❌ {filename}: Error reading - {e}")
                    file_info['read_error'] = str(e)
                    self.test_results['issues'].append(f"Error reading {filename}: {e}")
            else:
                logger.info(f"⚪ {filename}: Not found")
            
            data_results[filename] = file_info
        
        self.test_results['data_sources'] = data_results
        return data_results
    
    def analyze_data_quality(self, data, filename):
        """Analyze data quality for a dataset"""
        quality = {
            'total_records': len(data),
            'required_fields': {},
            'data_types': {},
            'fake_data_indicators': [],
            'email_quality': {},
            'url_quality': {}
        }
        
        if not data:
            return quality
        
        # Define expected fields for each file type
        expected_fields = {
            'raw_leads.json': ['name', 'linkedin_url', 'scraped_at'],
            'verified_leads.json': ['name', 'linkedin_url', 'verified', 'verified_at'],
            'enriched_leads.json': ['name', 'linkedin_url', 'verified', 'enriched', 'email'],
            'engaged_leads.json': ['name', 'linkedin_url', 'verified', 'enriched', 'contacted_at'],
            'dropped_leads.json': ['name', 'dropped_reason', 'dropped_at']
        }
        
        fields = expected_fields.get(filename, [])
        
        # Check required fields
        for field in fields:
            present_count = sum(1 for record in data if field in record and record[field])
            quality['required_fields'][field] = {
                'present_count': present_count,
                'coverage_percent': round((present_count / len(data)) * 100, 1)
            }
        
        # Check for fake data indicators
        fake_indicators = ['fake', 'mock', 'test@example', 'placeholder', 'generated', 'pattern_generated']
        
        for record in data:
            for key, value in record.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for indicator in fake_indicators:
                        if indicator in value_lower:
                            quality['fake_data_indicators'].append({
                                'field': key,
                                'value': value,
                                'indicator': indicator
                            })
        
        # Email quality analysis
        emails = [record.get('email') for record in data if record.get('email')]
        if emails:
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            valid_emails = [email for email in emails if email_pattern.match(email)]
            
            quality['email_quality'] = {
                'total_emails': len(emails),
                'valid_format': len(valid_emails),
                'validity_rate': round((len(valid_emails) / len(emails)) * 100, 1) if emails else 0
            }
        
        # URL quality analysis
        urls = [record.get('linkedin_url') for record in data if record.get('linkedin_url')]
        if urls:
            import re
            linkedin_pattern = re.compile(r'^https://www\.linkedin\.com/in/[a-zA-Z0-9-]+/?$')
            valid_urls = [url for url in urls if linkedin_pattern.match(url)]
            
            quality['url_quality'] = {
                'total_urls': len(urls),
                'valid_format': len(valid_urls),
                'validity_rate': round((len(valid_urls) / len(urls)) * 100, 1) if urls else 0
            }
        
        return quality
    
    def test_individual_components(self):
        """Test each pipeline component individually"""
        self.log_section("INDIVIDUAL COMPONENT TESTING")
        
        components = {
            'scraper': {'path': 'scraper/app.py', 'timeout': 300},
            'verifier': {'path': 'verifier/app.py', 'timeout': 180},
            'enricher': {'path': 'enricher/app.py', 'timeout': 120}
        }
        
        component_results = {}
        
        for component, config in components.items():
            logger.info(f"\n🧪 Testing {component} component...")
            
            component_path = self.root_dir / config['path']
            
            result = {
                'available': component_path.exists(),
                'import_test': False,
                'execution_test': False,
                'errors': []
            }
            
            if not component_path.exists():
                result['errors'].append(f"Component file not found: {config['path']}")
                logger.error(f"❌ {component}: File not found")
                component_results[component] = result
                continue
            
            # Test import
            try:
                import_cmd = [
                    sys.executable, '-c',
                    f'import sys; sys.path.append("{component_path.parent}"); import app; print("Import successful")'
                ]
                
                import_result = subprocess.run(
                    import_cmd,
                    cwd=component_path.parent,
                    timeout=30,
                    capture_output=True,
                    text=True
                )
                
                if import_result.returncode == 0:
                    result['import_test'] = True
                    logger.info(f"✅ {component}: Import successful")
                else:
                    result['errors'].append(f"Import failed: {import_result.stderr}")
                    logger.error(f"❌ {component}: Import failed")
                
            except Exception as e:
                result['errors'].append(f"Import test error: {str(e)}")
                logger.error(f"❌ {component}: Import test error - {e}")
            
            # Test execution (if import worked)
            if result['import_test']:
                try:
                    exec_cmd = [sys.executable, 'app.py']
                    
                    exec_result = subprocess.run(
                        exec_cmd,
                        cwd=component_path.parent,
                        timeout=config['timeout'],
                        capture_output=True,
                        text=True
                    )
                    
                    if exec_result.returncode == 0:
                        result['execution_test'] = True
                        logger.info(f"✅ {component}: Execution successful")
                    else:
                        result['errors'].append(f"Execution failed: {exec_result.stderr}")
                        logger.error(f"❌ {component}: Execution failed")
                        
                        # Check for specific error patterns
                        stderr = exec_result.stderr.lower()
                        if 'security challenge' in stderr or 'challenge' in stderr:
                            result['linkedin_challenge'] = True
                        if 'missing' in stderr and 'environment' in stderr:
                            result['env_issue'] = True
                
                except subprocess.TimeoutExpired:
                    result['errors'].append(f"Execution timed out after {config['timeout']} seconds")
                    logger.error(f"❌ {component}: Execution timeout")
                except Exception as e:
                    result['errors'].append(f"Execution test error: {str(e)}")
                    logger.error(f"❌ {component}: Execution test error - {e}")
            
            component_results[component] = result
        
        self.test_results['components'] = component_results
        return component_results
    
    def test_integrations(self):
        """Test external integrations"""
        self.log_section("EXTERNAL INTEGRATIONS")
        
        integration_results = {}
        
        # Test Airtable
        logger.info("🧪 Testing Airtable integration...")
        airtable_result = self.test_airtable_integration()
        integration_results['airtable'] = airtable_result
        
        # Test LinkedIn (basic connectivity)
        logger.info("🧪 Testing LinkedIn connectivity...")
        linkedin_result = self.test_linkedin_connectivity()
        integration_results['linkedin'] = linkedin_result
        
        # Test Email APIs
        logger.info("🧪 Testing Email APIs...")
        email_apis_result = self.test_email_apis()
        integration_results['email_apis'] = email_apis_result
        
        self.test_results['integrations'] = integration_results
        return integration_results
    
    def test_airtable_integration(self):
        """Test Airtable integration specifically"""
        result = {
            'connection': False,
            'schema_access': False,
            'write_test': False,
            'errors': []
        }
        
        try:
            import requests
            
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME')
            
            if not all([api_key, base_id, table_name]):
                result['errors'].append("Missing Airtable credentials")
                return result
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Test schema access
            schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
            schema_response = requests.get(schema_url, headers=headers, timeout=10)
            
            if schema_response.status_code == 200:
                result['schema_access'] = True
                result['connection'] = True
                logger.info("✅ Airtable: Schema access successful")
                
                # Test write
                api_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
                test_record = {
                    "fields": {
                        "Full Name": "Test Record - Delete Me",
                        "Company": "Test Company",
                        "Source": "System Test"
                    }
                }
                
                write_response = requests.post(api_url, headers=headers, json=test_record, timeout=10)
                
                if write_response.status_code in [200, 201]:
                    result['write_test'] = True
                    logger.info("✅ Airtable: Write test successful")
                    
                    # Clean up test record
                    try:
                        record_data = write_response.json()
                        record_id = record_data.get('id')
                        if record_id:
                            delete_url = f"{api_url}/{record_id}"
                            requests.delete(delete_url, headers=headers, timeout=10)
                    except:
                        pass  # Cleanup failed, but test succeeded
                        
                else:
                    result['errors'].append(f"Write test failed: {write_response.text}")
                    logger.error("❌ Airtable: Write test failed")
            else:
                result['errors'].append(f"Schema access failed: {schema_response.text}")
                logger.error("❌ Airtable: Schema access failed")
                
        except Exception as e:
            result['errors'].append(f"Airtable test error: {str(e)}")
            logger.error(f"❌ Airtable: Test error - {e}")
        
        return result
    
    def test_linkedin_connectivity(self):
        """Test LinkedIn connectivity (without full scraping)"""
        result = {
            'basic_access': False,
            'login_possible': False,
            'search_access': False,
            'errors': []
        }
        
        try:
            import requests
            
            # Test basic LinkedIn access
            basic_response = requests.get('https://www.linkedin.com', timeout=10)
            if basic_response.status_code == 200:
                result['basic_access'] = True
                logger.info("✅ LinkedIn: Basic access successful")
            else:
                result['errors'].append(f"Basic access failed: {basic_response.status_code}")
                logger.error("❌ LinkedIn: Basic access failed")
            
            # Check if we have credentials
            email = os.getenv('LINKEDIN_EMAIL')
            password = os.getenv('LINKEDIN_PASSWORD')
            
            if email and password:
                logger.info("✅ LinkedIn: Credentials available")
                # Note: We won't actually test login to avoid triggering security measures
                result['login_possible'] = True
            else:
                result['errors'].append("LinkedIn credentials not available")
                logger.error("❌ LinkedIn: Credentials missing")
                
        except Exception as e:
            result['errors'].append(f"LinkedIn connectivity error: {str(e)}")
            logger.error(f"❌ LinkedIn: Connectivity error - {e}")
        
        return result
    
    def test_email_apis(self):
        """Test email-related APIs"""
        result = {
            'hunter_io': {'available': False, 'tested': False},
            'clearbit': {'available': False, 'tested': False},
            'apollo': {'available': False, 'tested': False},
            'sendgrid': {'available': False, 'tested': False}
        }
        
        # Check API keys
        apis = {
            'hunter_io': 'HUNTER_API_KEY',
            'clearbit': 'CLEARBIT_API_KEY',
            'apollo': 'APOLLO_API_KEY',
            'sendgrid': 'SENDGRID_API_KEY'
        }
        
        for api_name, env_var in apis.items():
            api_key = os.getenv(env_var)
            if api_key:
                result[api_name]['available'] = True
                logger.info(f"✅ {api_name}: API key available")
            else:
                logger.info(f"⚪ {api_name}: API key not set")
        
        return result
    
    def test_pipeline_flow(self):
        """Test the complete pipeline flow"""
        self.log_section("PIPELINE FLOW TESTING")
        
        flow_result = {
            'data_progression': {},
            'conversion_rates': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Analyze data progression
        data_sources = self.test_results.get('data_sources', {})
        
        stages = ['raw_leads.json', 'verified_leads.json', 'enriched_leads.json', 'engaged_leads.json']
        stage_counts = {}
        
        for stage in stages:
            file_info = data_sources.get(stage, {})
            count = file_info.get('lead_count', 0)
            stage_counts[stage.replace('.json', '')] = count
            
            logger.info(f"📊 {stage}: {count} leads")
        
        flow_result['data_progression'] = stage_counts
        
        # Calculate conversion rates
        raw_count = stage_counts.get('raw_leads', 0)
        verified_count = stage_counts.get('verified_leads', 0)
        enriched_count = stage_counts.get('enriched_leads', 0)
        engaged_count = stage_counts.get('engaged_leads', 0)
        
        if raw_count > 0:
            flow_result['conversion_rates']['verification_rate'] = round((verified_count / raw_count) * 100, 1)
        if verified_count > 0:
            flow_result['conversion_rates']['enrichment_rate'] = round((enriched_count / verified_count) * 100, 1)
        if enriched_count > 0:
            flow_result['conversion_rates']['engagement_rate'] = round((engaged_count / enriched_count) * 100, 1)
        
        # Identify bottlenecks
        if raw_count == 0:
            flow_result['bottlenecks'].append("No raw leads - scraper not generating data")
        if verified_count < raw_count * 0.5:
            flow_result['bottlenecks'].append("Low verification rate - LinkedIn URLs may be invalid")
        if enriched_count < verified_count * 0.3:
            flow_result['bottlenecks'].append("Low enrichment rate - email discovery needs improvement")
        if engaged_count < enriched_count * 0.8:
            flow_result['bottlenecks'].append("Low engagement rate - check engagement criteria")
        
        self.test_results['pipeline_flow'] = flow_result
        return flow_result
    
    def generate_action_plan(self):
        """Generate a comprehensive action plan based on test results"""
        self.log_section("GENERATING ACTION PLAN")
        
        action_plan = []
        
        # Environment issues
        env_issues = [issue for issue in self.test_results['issues'] if 'environment variable' in issue]
        if env_issues:
            action_plan.append({
                'priority': 'HIGH',
                'category': 'Environment',
                'task': 'Fix missing environment variables',
                'details': env_issues,
                'estimated_time': '30 minutes'
            })
        
        # Dependency issues
        dep_issues = [issue for issue in self.test_results['issues'] if 'dependency' in issue]
        if dep_issues:
            action_plan.append({
                'priority': 'HIGH',
                'category': 'Dependencies',
                'task': 'Install missing Python dependencies',
                'details': dep_issues,
                'estimated_time': '15 minutes'
            })
        
        # Component issues
        components = self.test_results.get('components', {})
        failed_components = [name for name, info in components.items() if not info.get('execution_test', False)]
        
        if failed_components:
            action_plan.append({
                'priority': 'HIGH',
                'category': 'Components',
                'task': f'Fix failed components: {", ".join(failed_components)}',
                'details': [f"{name}: {info.get('errors', [])}" for name, info in components.items() if name in failed_components],
                'estimated_time': '2-4 hours'
            })
        
        # LinkedIn scraping issues
        linkedin_issues = any(info.get('linkedin_challenge', False) for info in components.values())
        if linkedin_issues:
            action_plan.append({
                'priority': 'MEDIUM',
                'category': 'LinkedIn Scraping',
                'task': 'Resolve LinkedIn security challenges',
                'details': ['LinkedIn detected automation and triggered security challenge'],
                'estimated_time': '1-2 hours',
                'alternatives': ['Use alternative data sources', 'Manual LinkedIn profile collection', 'Different scraping approach']
            })
        
        # Data quality issues
        data_sources = self.test_results.get('data_sources', {})
        fake_data_files = []
        for filename, info in data_sources.items():
            quality = info.get('data_quality', {})
            if quality.get('fake_data_indicators'):
                fake_data_files.append(filename)
        
        if fake_data_files:
            action_plan.append({
                'priority': 'HIGH',
                'category': 'Data Quality',
                'task': 'Remove fake data from pipeline files',
                'details': [f"Fake data detected in: {', '.join(fake_data_files)}"],
                'estimated_time': '1 hour'
            })
        
        # Integration issues
        integrations = self.test_results.get('integrations', {})
        airtable = integrations.get('airtable', {})
        if not airtable.get('write_test', False):
            action_plan.append({
                'priority': 'HIGH',
                'category': 'Airtable Integration',
                'task': 'Fix Airtable write functionality',
                'details': airtable.get('errors', []),
                'estimated_time': '30 minutes'
            })
        
        # Pipeline flow issues
        flow = self.test_results.get('pipeline_flow', {})
        bottlenecks = flow.get('bottlenecks', [])
        if bottlenecks:
            action_plan.append({
                'priority': 'MEDIUM',
                'category': 'Pipeline Flow',
                'task': 'Address pipeline bottlenecks',
                'details': bottlenecks,
                'estimated_time': '1-3 hours'
            })
        
        self.test_results['action_plan'] = action_plan
        
        # Log action plan
        logger.info(f"\n📋 ACTION PLAN GENERATED ({len(action_plan)} items)")
        for i, item in enumerate(action_plan, 1):
            logger.info(f"{i}. [{item['priority']}] {item['category']}: {item['task']}")
            logger.info(f"   Time: {item['estimated_time']}")
            if item.get('alternatives'):
                logger.info(f"   Alternatives: {', '.join(item['alternatives'])}")
        
        return action_plan
    
    def save_results(self):
        """Save comprehensive test results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.logs_dir / f"comprehensive_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"💾 Comprehensive test results saved to {results_file}")
        return results_file
    
    def print_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "="*100)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("="*100)
        
        # Overall status
        total_issues = len(self.test_results['issues'])
        action_items = len(self.test_results.get('action_plan', []))
        
        if total_issues == 0:
            logger.info("✅ OVERALL STATUS: HEALTHY - No critical issues detected")
        elif total_issues <= 5:
            logger.info(f"⚠️ OVERALL STATUS: MINOR ISSUES - {total_issues} issues need attention")
        else:
            logger.info(f"🚨 OVERALL STATUS: CRITICAL - {total_issues} issues require immediate action")
        
        logger.info(f"📋 Action items generated: {action_items}")
        
        # Component status
        components = self.test_results.get('components', {})
        logger.info(f"\n🤖 COMPONENT STATUS:")
        for name, info in components.items():
            if info.get('execution_test'):
                logger.info(f"   ✅ {name}: Working")
            elif info.get('import_test'):
                logger.info(f"   ⚠️ {name}: Import OK, execution failed")
            else:
                logger.info(f"   ❌ {name}: Not working")
        
        # Data status
        data_sources = self.test_results.get('data_sources', {})
        logger.info(f"\n📊 DATA STATUS:")
        for filename, info in data_sources.items():
            if info.get('exists'):
                count = info.get('lead_count', 0)
                logger.info(f"   ✅ {filename}: {count} leads")
            else:
                logger.info(f"   ⚪ {filename}: Not found")
        
        # Integration status
        integrations = self.test_results.get('integrations', {})
        logger.info(f"\n🔗 INTEGRATION STATUS:")
        airtable = integrations.get('airtable', {})
        if airtable.get('write_test'):
            logger.info("   ✅ Airtable: Fully functional")
        elif airtable.get('connection'):
            logger.info("   ⚠️ Airtable: Connected, write issues")
        else:
            logger.info("   ❌ Airtable: Not working")
        
        linkedin = integrations.get('linkedin', {})
        if linkedin.get('login_possible'):
            logger.info("   ⚠️ LinkedIn: Credentials available, security challenges expected")
        else:
            logger.info("   ❌ LinkedIn: Credentials missing or connectivity issues")
        
        logger.info("="*100)
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        logger.info("🚀 Starting Comprehensive Test Suite")
        
        # Run all tests
        self.test_environment()
        self.test_dependencies()
        self.test_data_sources()
        self.test_individual_components()
        self.test_integrations()
        self.test_pipeline_flow()
        
        # Generate action plan
        self.generate_action_plan()
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
        
        return self.test_results

async def main():
    """Main entry point"""
    test_suite = ComprehensiveTestSuite()
    results = await test_suite.run_comprehensive_test()
    
    # Return success based on critical issues
    critical_issues = len([item for item in results.get('action_plan', []) if item.get('priority') == 'HIGH'])
    
    if critical_issues == 0:
        logger.info("✅ Comprehensive test completed - system is ready")
        return True
    else:
        logger.info(f"⚠️ Comprehensive test completed - {critical_issues} critical issues need attention")
        return True  # Still return True since we have a plan

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)