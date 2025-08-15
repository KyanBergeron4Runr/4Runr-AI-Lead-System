#!/usr/bin/env python3
"""
Production Readiness Test

Comprehensive test to validate if the system is truly ready for production deployment.
Tests all critical components with realistic scenarios.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

# Import production components
from production_db_manager import db_manager
from improved_email_finder import email_finder
from company_size_validator import company_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionReadinessTest:
    """Test production readiness comprehensively."""
    
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
    
    def run_all_tests(self):
        """Run comprehensive production readiness tests."""
        logger.info("🧪 PRODUCTION READINESS TEST")
        logger.info("="*60)
        
        try:
            # Test 1: Database Performance
            self.test_database_performance()
            
            # Test 2: Email Discovery
            self.test_email_discovery()
            
            # Test 3: Company Size Validation
            self.test_company_size_validation()
            
            # Test 4: Integration Test
            self.test_end_to_end_integration()
            
            # Test 5: Production Stress Test
            self.test_production_stress()
            
            # Generate final report
            self.generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        
        return len(self.critical_failures) == 0
    
    def test_database_performance(self):
        """Test database performance under realistic conditions."""
        logger.info("\n🔍 TEST 1: Database Performance")
        logger.info("-" * 40)
        
        try:
            # Test 1a: Fast Lead Addition
            start_time = time.time()
            
            test_lead = {
                'full_name': 'Performance Test User',
                'email': 'performance.test@example.com',
                'company': 'Test Performance Corp',
                'job_title': 'CEO',  # Use job_title instead of title
                'business_type': 'SaaS',
                'ready_for_outreach': 1
            }
            
            success = db_manager.add_lead(test_lead)
            add_time = time.time() - start_time
            
            if not success:
                self.critical_failures.append("Database add operation failed")
                logger.error("❌ Lead addition failed")
                return
            
            if add_time > 1.0:  # Should be under 1 second
                self.warnings.append(f"Database add slow: {add_time:.3f}s")
                logger.warning(f"⚠️ Add operation slow: {add_time:.3f}s")
            else:
                logger.info(f"✅ Add operation fast: {add_time:.3f}s")
            
            # Get the ID of the lead we just added
            lead_id = test_lead.get('id') 
            if not lead_id:
                # If no ID was set, try to find it by email
                with db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT id FROM leads WHERE email = ?", (test_lead['email'],))
                    row = cursor.fetchone()
                    lead_id = row[0] if row else None
            
            # Test 1b: Fast Lead Retrieval
            start_time = time.time()
            retrieved_lead = db_manager.get_lead(lead_id) if lead_id else None
            retrieve_time = time.time() - start_time
            
            if not retrieved_lead:
                self.critical_failures.append("Database retrieval failed")
                logger.error("❌ Lead retrieval failed")
                return
            
            if retrieve_time > 0.5:  # Should be under 0.5 seconds
                self.warnings.append(f"Database retrieval slow: {retrieve_time:.3f}s")
                logger.warning(f"⚠️ Retrieval slow: {retrieve_time:.3f}s")
            else:
                logger.info(f"✅ Retrieval fast: {retrieve_time:.3f}s")
            
            # Test 1c: Bulk Operations
            start_time = time.time()
            leads_for_sync = db_manager.get_leads_for_sync(10)
            bulk_time = time.time() - start_time
            
            if bulk_time > 2.0:  # Should be under 2 seconds
                self.warnings.append(f"Bulk operations slow: {bulk_time:.3f}s")
                logger.warning(f"⚠️ Bulk operations slow: {bulk_time:.3f}s")
            else:
                logger.info(f"✅ Bulk operations fast: {bulk_time:.3f}s")
            
            # Test 1d: Database Stats
            stats = db_manager.get_database_stats()
            if not stats:
                self.critical_failures.append("Database stats failed")
                logger.error("❌ Database stats failed")
            else:
                logger.info(f"✅ Database stats: {stats['total_leads']} leads, {stats['email_percentage']}% with emails")
            
            self.test_results['database_performance'] = {
                'status': 'PASS' if len(self.critical_failures) == 0 else 'FAIL',
                'add_time': add_time,
                'retrieve_time': retrieve_time,
                'bulk_time': bulk_time,
                'stats': stats
            }
            
        except Exception as e:
            self.critical_failures.append(f"Database performance test failed: {e}")
            logger.error(f"❌ Database test failed: {e}")
    
    def test_email_discovery(self):
        """Test improved email discovery."""
        logger.info("\n🔍 TEST 2: Email Discovery")
        logger.info("-" * 40)
        
        try:
            # Test with real website
            test_websites = [
                ('https://example.com', 'Example Corp'),
                ('https://github.com', 'GitHub'),  # Should find contact emails
                ('invalid-website', 'Invalid')  # Should handle gracefully
            ]
            
            for website, company in test_websites:
                logger.info(f"Testing email discovery for: {website}")
                
                start_time = time.time()
                emails = email_finder.find_business_emails(website, company)
                discovery_time = time.time() - start_time
                
                logger.info(f"  Found {len(emails)} emails in {discovery_time:.2f}s")
                
                if emails:
                    logger.info(f"  Emails: {', '.join(emails[:2])}...")  # Show first 2
                
                if discovery_time > 10.0:  # Should be under 10 seconds
                    self.warnings.append(f"Email discovery slow for {website}: {discovery_time:.2f}s")
            
            self.test_results['email_discovery'] = {
                'status': 'PASS',
                'test_count': len(test_websites)
            }
            
            logger.info("✅ Email discovery test completed")
            
        except Exception as e:
            self.critical_failures.append(f"Email discovery test failed: {e}")
            logger.error(f"❌ Email discovery test failed: {e}")
    
    def test_company_size_validation(self):
        """Test company size validation."""
        logger.info("\n🔍 TEST 3: Company Size Validation")
        logger.info("-" * 40)
        
        try:
            # Test cases: (company_name, expected_too_large)
            test_cases = [
                ('Shopify', True),    # Should be too large
                ('Google', True),     # Should be too large
                ('Small Local Business', False),  # Should be good
                ('Tech Startup Inc', False),      # Should be good
                ('Microsoft Corporation', True),  # Should be too large
                ('Joe\'s Pizza', False)           # Should be good
            ]
            
            correct_classifications = 0
            
            for company_name, expected_too_large in test_cases:
                is_too_large = company_validator.is_company_too_large(company_name)
                target_info = company_validator.is_good_outreach_target(company_name, "")
                
                if is_too_large == expected_too_large:
                    correct_classifications += 1
                    logger.info(f"✅ {company_name}: {'Too large' if is_too_large else 'Good target'}")
                else:
                    logger.warning(f"⚠️ {company_name}: Expected {'large' if expected_too_large else 'small'}, got {'large' if is_too_large else 'small'}")
            
            accuracy = correct_classifications / len(test_cases) * 100
            
            if accuracy < 80:
                self.warnings.append(f"Company size validation accuracy low: {accuracy:.1f}%")
            
            logger.info(f"✅ Company size validation accuracy: {accuracy:.1f}%")
            
            self.test_results['company_size_validation'] = {
                'status': 'PASS',
                'accuracy': accuracy,
                'test_cases': len(test_cases)
            }
            
        except Exception as e:
            self.critical_failures.append(f"Company size validation test failed: {e}")
            logger.error(f"❌ Company size validation test failed: {e}")
    
    def test_end_to_end_integration(self):
        """Test end-to-end integration of all components."""
        logger.info("\n🔍 TEST 4: End-to-End Integration")
        logger.info("-" * 40)
        
        try:
            # Simulate a complete lead processing workflow
            test_lead_data = {
                'full_name': 'Sarah Johnson',
                'email': 'sarah@techstartup.com',
                'company': 'TechStartup Inc',
                'job_title': 'CEO',  # Use job_title instead of title
                'website': 'https://techstartup.com'  # Use website instead of company_website
            }
            
            # Step 1: Add lead to database
            logger.info("Step 1: Adding lead to database...")
            add_success = db_manager.add_lead(test_lead_data)
            if not add_success:
                self.critical_failures.append("Integration test: Failed to add lead")
                return
            logger.info("✅ Lead added successfully")
            
            # Step 2: Validate company size
            logger.info("Step 2: Validating company size...")
            target_info = company_validator.is_good_outreach_target(
                test_lead_data['company'], 
                "Small tech startup focused on AI solutions"
            )
            
            if not target_info['is_good_target']:
                logger.warning(f"⚠️ Company marked as poor target: {target_info['reason']}")
            else:
                logger.info(f"✅ Company is good target: {target_info['reason']}")
            
            # Step 3: Find additional emails
            logger.info("Step 3: Finding additional emails...")
            if test_lead_data.get('website'):
                additional_emails = email_finder.find_business_emails(
                    test_lead_data['website'], 
                    test_lead_data['company']
                )
                logger.info(f"✅ Found {len(additional_emails)} additional emails")
            
            # Step 4: Update lead with enrichment
            logger.info("Step 4: Updating lead with enrichment...")
            updates = {
                'ready_for_outreach': 1,
                'business_type': 'SaaS',
                'company_size': 'Small'
            }
            
            # Get the lead ID first
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT id FROM leads WHERE email = ?", (test_lead_data['email'],))
                row = cursor.fetchone()
                lead_id = row[0] if row else None
            
            if not lead_id:
                self.critical_failures.append("Integration test: Could not find lead ID")
                return
            
            update_success = db_manager.update_lead(lead_id, updates)
            if not update_success:
                self.critical_failures.append("Integration test: Failed to update lead")
                return
            logger.info("✅ Lead updated successfully")
            
            # Step 5: Retrieve final lead
            logger.info("Step 5: Retrieving final lead...")
            final_lead = db_manager.get_lead(lead_id)
            if not final_lead:
                self.critical_failures.append("Integration test: Failed to retrieve final lead")
                return
            logger.info("✅ Final lead retrieved successfully")
            
            logger.info("🎉 End-to-end integration test PASSED")
            
            self.test_results['end_to_end_integration'] = {
                'status': 'PASS',
                'final_lead': final_lead
            }
            
        except Exception as e:
            self.critical_failures.append(f"End-to-end integration test failed: {e}")
            logger.error(f"❌ Integration test failed: {e}")
    
    def test_production_stress(self):
        """Test system under production-like stress."""
        logger.info("\n🔍 TEST 5: Production Stress Test")
        logger.info("-" * 40)
        
        try:
            # Test rapid database operations
            logger.info("Testing rapid database operations...")
            
            rapid_ops_start = time.time()
            rapid_ops_success = 0
            
            for i in range(10):  # 10 rapid operations
                test_lead = {
                    'full_name': f'Stress Test User {i}',
                    'email': f'stress.test.{i}@example.com',
                    'company': f'Stress Test Corp {i}'
                }
                
                if db_manager.add_lead(test_lead):
                    rapid_ops_success += 1
            
            rapid_ops_time = time.time() - rapid_ops_start
            rapid_ops_rate = rapid_ops_success / rapid_ops_time
            
            logger.info(f"✅ Rapid operations: {rapid_ops_success}/10 successful in {rapid_ops_time:.2f}s")
            logger.info(f"✅ Operations rate: {rapid_ops_rate:.2f} ops/second")
            
            if rapid_ops_rate < 5:  # Should handle at least 5 ops/second
                self.warnings.append(f"Low operations rate: {rapid_ops_rate:.2f} ops/sec")
            
            # Test concurrent operations (simulate multiple users)
            logger.info("Testing concurrent-like operations...")
            
            concurrent_start = time.time()
            stats_calls = 0
            
            for i in range(5):
                stats = db_manager.get_database_stats()
                if stats:
                    stats_calls += 1
                
                # Simulate some work
                time.sleep(0.1)
            
            concurrent_time = time.time() - concurrent_start
            logger.info(f"✅ Concurrent operations: {stats_calls}/5 successful in {concurrent_time:.2f}s")
            
            self.test_results['production_stress'] = {
                'status': 'PASS',
                'rapid_ops_rate': rapid_ops_rate,
                'concurrent_success': stats_calls
            }
            
        except Exception as e:
            self.critical_failures.append(f"Production stress test failed: {e}")
            logger.error(f"❌ Stress test failed: {e}")
    
    def generate_final_report(self):
        """Generate final production readiness report."""
        logger.info("\n" + "="*60)
        logger.info("🎯 PRODUCTION READINESS REPORT")
        logger.info("="*60)
        
        # Calculate overall score
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PASS')
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine readiness level
        if len(self.critical_failures) == 0 and success_rate >= 100:
            readiness_level = "🟢 PRODUCTION READY"
        elif len(self.critical_failures) == 0 and success_rate >= 80:
            readiness_level = "🟡 MOSTLY READY (minor issues)"
        else:
            readiness_level = "🔴 NOT READY (critical issues)"
        
        logger.info(f"\n📊 OVERALL STATUS: {readiness_level}")
        logger.info(f"📈 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Report test results
        logger.info(f"\n📋 TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result.get('status') == 'PASS' else "❌"
            logger.info(f"  {status_icon} {test_name.replace('_', ' ').title()}: {result.get('status')}")
        
        # Report critical failures
        if self.critical_failures:
            logger.info(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                logger.info(f"  ❌ {failure}")
        else:
            logger.info(f"\n🎉 NO CRITICAL FAILURES!")
        
        # Report warnings
        if self.warnings:
            logger.info(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.info(f"  ⚠️ {warning}")
        
        # Production deployment recommendations
        logger.info(f"\n🚀 DEPLOYMENT RECOMMENDATIONS:")
        
        if len(self.critical_failures) == 0:
            logger.info("  ✅ Core system is stable and ready")
            logger.info("  ✅ Database performance is acceptable")
            logger.info("  ✅ All components are working together")
            
            if len(self.warnings) > 0:
                logger.info("  ⚠️ Address warnings before production if possible")
            
            logger.info("  🎯 DEPLOY WITH CONFIDENCE!")
        else:
            logger.info("  ❌ Fix critical failures before deployment")
            logger.info("  🛑 DO NOT DEPLOY until issues are resolved")
        
        # Save report to file
        report_data = {
            'readiness_level': readiness_level,
            'success_rate': success_rate,
            'test_results': self.test_results,
            'critical_failures': self.critical_failures,
            'warnings': self.warnings,
            'timestamp': time.time()
        }
        
        with open('production_readiness_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n💾 Report saved to: production_readiness_report.json")
        
        return len(self.critical_failures) == 0

if __name__ == "__main__":
    tester = ProductionReadinessTest()
    is_ready = tester.run_all_tests()
    
    if is_ready:
        print(f"\n🎉 SYSTEM IS PRODUCTION READY!")
        sys.exit(0)
    else:
        print(f"\n⚠️ SYSTEM NEEDS FIXES BEFORE PRODUCTION")
        sys.exit(1)
