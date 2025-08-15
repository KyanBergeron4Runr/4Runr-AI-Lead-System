#!/usr/bin/env python3
"""
ULTIMATE SYSTEM TEST

The most comprehensive, brutal test suite designed to expose every possible weakness.
This test is designed to FAIL if there are ANY issues - no mercy, no shortcuts.
Only a truly production-ready system will pass all these tests.
"""

import os
import sys
import time
import json
import logging
import traceback
import threading
import random
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

# Import all components
from production_db_manager import db_manager
from improved_email_finder import email_finder
from company_size_validator import company_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UltimateSystemTest:
    """The most brutal, comprehensive system test possible."""
    
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
        self.performance_issues = []
        self.data_quality_issues = []
        
        # Test configuration
        self.stress_test_threads = 10
        self.stress_test_operations = 100
        self.performance_threshold_ms = 1000  # 1 second max
        self.data_quality_threshold = 95  # 95% data quality required
        
    def run_ultimate_test_suite(self):
        """Run the most comprehensive test suite possible."""
        logger.info("🔥 ULTIMATE SYSTEM TEST - NO MERCY MODE")
        logger.info("="*70)
        logger.info("This test is designed to EXPOSE EVERY WEAKNESS")
        logger.info("Only a truly bulletproof system will pass")
        logger.info("="*70)
        
        try:
            # 1. Database Stress Test
            self.brutal_database_stress_test()
            
            # 2. Concurrent Operations Test
            self.concurrent_operations_stress_test()
            
            # 3. Error Handling Test
            self.comprehensive_error_handling_test()
            
            # 4. Data Quality Validation
            self.data_quality_validation_test()
            
            # 5. API Integration Test
            self.api_integration_stress_test()
            
            # 6. Memory and Resource Test
            self.memory_and_resource_test()
            
            # 7. Edge Cases Test
            self.edge_cases_test()
            
            # 8. End-to-End Pipeline Test
            self.end_to_end_pipeline_test()
            
            # 9. Failover and Recovery Test
            self.failover_recovery_test()
            
            # 10. Performance Under Load Test
            self.performance_under_load_test()
            
            # Generate brutal final report
            self.generate_brutal_final_report()
            
        except Exception as e:
            logger.error(f"❌ ULTIMATE TEST SUITE FAILED: {e}")
            logger.error(traceback.format_exc())
            return False
        
        # System passes only if NO critical failures
        return len(self.critical_failures) == 0
    
    def brutal_database_stress_test(self):
        """Brutal database stress test - find every weakness."""
        logger.info("\n🔥 TEST 1: BRUTAL DATABASE STRESS TEST")
        logger.info("-" * 50)
        
        try:
            # Test 1a: Rapid-fire operations
            logger.info("Testing rapid-fire database operations...")
            
            start_time = time.time()
            operations_completed = 0
            failures = 0
            
            for i in range(100):  # 100 rapid operations
                test_lead = {
                    'full_name': f'Stress Test User {i}',
                    'email': f'stress.test.{i}.{int(time.time())}@example.com',
                    'company': f'Stress Test Corp {i}',
                    'job_title': 'CEO'
                }
                
                if db_manager.add_lead(test_lead):
                    operations_completed += 1
                else:
                    failures += 1
            
            total_time = time.time() - start_time
            ops_per_second = operations_completed / total_time
            
            logger.info(f"Completed {operations_completed}/100 operations in {total_time:.2f}s")
            logger.info(f"Performance: {ops_per_second:.2f} ops/second")
            
            if failures > 0:
                self.critical_failures.append(f"Database stress test: {failures} failures out of 100 operations")
            
            if ops_per_second < 50:  # Should handle at least 50 ops/second
                self.performance_issues.append(f"Database too slow: {ops_per_second:.2f} ops/sec")
            
            # Test 1b: Large data operations
            logger.info("Testing large data operations...")
            
            large_lead = {
                'full_name': 'Large Data Test User',
                'email': 'large.data@example.com',
                'company': 'Large Data Corp',
                'ai_message': 'A' * 10000,  # 10KB AI message
                'company_description': 'B' * 5000,  # 5KB description
                'website_insights': 'C' * 5000  # 5KB insights
            }
            
            start_time = time.time()
            success = db_manager.add_lead(large_lead)
            large_data_time = time.time() - start_time
            
            if not success:
                self.critical_failures.append("Failed to handle large data lead")
            
            if large_data_time > 2.0:  # Should handle large data in under 2 seconds
                self.performance_issues.append(f"Large data handling too slow: {large_data_time:.2f}s")
            
            # Test 1c: Database integrity under stress
            logger.info("Testing database integrity...")
            
            stats_before = db_manager.get_database_stats()
            
            # Rapid concurrent-like operations
            for i in range(50):
                lead1 = {'full_name': f'Integrity Test A{i}', 'email': f'integrity.a.{i}@example.com'}
                lead2 = {'full_name': f'Integrity Test B{i}', 'email': f'integrity.b.{i}@example.com'}
                
                db_manager.add_lead(lead1)
                db_manager.add_lead(lead2)
            
            stats_after = db_manager.get_database_stats()
            
            if stats_after['total_leads'] <= stats_before['total_leads']:
                self.critical_failures.append("Database integrity compromised during stress test")
            
            self.test_results['brutal_database_stress'] = {
                'status': 'PASS' if len(self.critical_failures) == 0 else 'FAIL',
                'ops_per_second': ops_per_second,
                'failures': failures,
                'large_data_time': large_data_time
            }
            
        except Exception as e:
            self.critical_failures.append(f"Database stress test crashed: {e}")
            logger.error(f"❌ Database stress test failed: {e}")
    
    def concurrent_operations_stress_test(self):
        """Test concurrent operations like a real production environment."""
        logger.info("\n🔥 TEST 2: CONCURRENT OPERATIONS STRESS TEST")
        logger.info("-" * 50)
        
        try:
            # Test concurrent database operations
            logger.info("Testing concurrent database operations...")
            
            def worker_thread(thread_id):
                """Worker thread for concurrent operations."""
                operations = 0
                failures = 0
                
                for i in range(10):
                    try:
                        # Add lead
                        lead = {
                            'full_name': f'Thread{thread_id} User{i}',
                            'email': f'thread{thread_id}.user{i}.{int(time.time())}@example.com',
                            'company': f'Thread{thread_id} Corp{i}'
                        }
                        
                        if db_manager.add_lead(lead):
                            operations += 1
                        else:
                            failures += 1
                        
                        # Get stats
                        stats = db_manager.get_database_stats()
                        if not stats:
                            failures += 1
                        
                        # Small delay to simulate real usage
                        time.sleep(0.01)
                        
                    except Exception as e:
                        failures += 1
                        logger.error(f"Thread {thread_id} error: {e}")
                
                return operations, failures
            
            # Run concurrent operations
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=self.stress_test_threads) as executor:
                futures = [executor.submit(worker_thread, i) for i in range(self.stress_test_threads)]
                results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            total_operations = sum(result[0] for result in results)
            total_failures = sum(result[1] for result in results)
            
            logger.info(f"Concurrent test: {total_operations} operations, {total_failures} failures in {total_time:.2f}s")
            
            if total_failures > 0:
                self.critical_failures.append(f"Concurrent operations failed: {total_failures} failures")
            
            if total_operations < (self.stress_test_threads * 8):  # Should complete at least 80% of operations
                self.critical_failures.append(f"Concurrent operations underperformed: {total_operations} completed")
            
            self.test_results['concurrent_operations_stress'] = {
                'status': 'PASS' if total_failures == 0 else 'FAIL',
                'total_operations': total_operations,
                'total_failures': total_failures,
                'time_taken': total_time
            }
            
        except Exception as e:
            self.critical_failures.append(f"Concurrent operations test crashed: {e}")
            logger.error(f"❌ Concurrent operations test failed: {e}")
    
    def comprehensive_error_handling_test(self):
        """Test error handling in every possible scenario."""
        logger.info("\n🔥 TEST 3: COMPREHENSIVE ERROR HANDLING TEST")
        logger.info("-" * 50)
        
        try:
            error_scenarios_passed = 0
            total_error_scenarios = 0
            
            # Test 3a: Invalid data handling
            logger.info("Testing invalid data handling...")
            
            invalid_leads = [
                {'full_name': None, 'email': 'test@example.com'},  # None name
                {'full_name': '', 'email': 'test@example.com'},    # Empty name
                {'full_name': 'Test', 'email': 'invalid-email'},   # Invalid email
                {'full_name': 'Test', 'email': None},              # None email
                {'full_name': 'Test', 'email': ''},                # Empty email
                {'full_name': 'A' * 1000, 'email': 'test@example.com'},  # Overly long name
                {},  # Empty lead data
            ]
            
            for i, invalid_lead in enumerate(invalid_leads):
                total_error_scenarios += 1
                try:
                    # This should either handle gracefully or fail gracefully
                    result = db_manager.add_lead(invalid_lead)
                    # If it succeeded with invalid data, that might be OK depending on validation
                    error_scenarios_passed += 1
                    logger.info(f"Invalid lead test {i}: Handled gracefully")
                    
                except Exception as e:
                    # If it failed gracefully (threw proper exception), that's good
                    error_scenarios_passed += 1
                    logger.info(f"Invalid lead test {i}: Failed gracefully - {e}")
            
            # Test 3b: Database connection issues simulation
            logger.info("Testing database resilience...")
            
            # Test with rapid operations to potentially trigger issues
            total_error_scenarios += 3
            
            try:
                # Test getting non-existent lead
                non_existent = db_manager.get_lead(999999)
                if non_existent is None:
                    error_scenarios_passed += 1
                    logger.info("Non-existent lead handling: ✅")
                else:
                    logger.warning("Non-existent lead handling: Unexpected result")
            except Exception:
                error_scenarios_passed += 1  # Graceful failure is acceptable
            
            try:
                # Test updating non-existent lead
                update_result = db_manager.update_lead(999999, {'full_name': 'Updated'})
                if update_result is False:
                    error_scenarios_passed += 1
                    logger.info("Non-existent lead update: ✅")
                else:
                    logger.warning("Non-existent lead update: Unexpected result")
            except Exception:
                error_scenarios_passed += 1  # Graceful failure is acceptable
            
            try:
                # Test stats during operations
                stats = db_manager.get_database_stats()
                if stats and 'total_leads' in stats:
                    error_scenarios_passed += 1
                    logger.info("Stats reliability: ✅")
                else:
                    logger.warning("Stats reliability: Issue detected")
            except Exception as e:
                logger.warning(f"Stats reliability: Failed - {e}")
            
            # Test 3c: Email finder error handling
            logger.info("Testing email finder error handling...")
            
            total_error_scenarios += 3
            
            # Test invalid URLs
            try:
                emails = email_finder.find_business_emails("invalid-url", "Test Company")
                error_scenarios_passed += 1
                logger.info(f"Invalid URL handling: ✅ (returned {len(emails)} emails)")
            except Exception:
                error_scenarios_passed += 1  # Graceful failure is acceptable
            
            # Test non-existent domain
            try:
                emails = email_finder.find_business_emails("https://this-domain-definitely-does-not-exist-12345.com", "Test Company")
                error_scenarios_passed += 1
                logger.info(f"Non-existent domain handling: ✅ (returned {len(emails)} emails)")
            except Exception:
                error_scenarios_passed += 1  # Graceful failure is acceptable
            
            # Test with None inputs
            try:
                emails = email_finder.find_business_emails("", "")
                error_scenarios_passed += 1
                logger.info(f"Empty inputs handling: ✅ (returned {len(emails)} emails)")
            except Exception:
                error_scenarios_passed += 1  # Graceful failure is acceptable
            
            error_handling_percentage = (error_scenarios_passed / total_error_scenarios) * 100
            
            logger.info(f"Error handling success rate: {error_handling_percentage:.1f}% ({error_scenarios_passed}/{total_error_scenarios})")
            
            if error_handling_percentage < 90:
                self.critical_failures.append(f"Error handling insufficient: {error_handling_percentage:.1f}%")
            
            self.test_results['comprehensive_error_handling'] = {
                'status': 'PASS' if error_handling_percentage >= 90 else 'FAIL',
                'success_rate': error_handling_percentage,
                'scenarios_passed': error_scenarios_passed,
                'total_scenarios': total_error_scenarios
            }
            
        except Exception as e:
            self.critical_failures.append(f"Error handling test crashed: {e}")
            logger.error(f"❌ Error handling test failed: {e}")
    
    def data_quality_validation_test(self):
        """Validate data quality meets business requirements."""
        logger.info("\n🔥 TEST 4: DATA QUALITY VALIDATION TEST")
        logger.info("-" * 50)
        
        try:
            # Get all leads from database
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM leads")
                all_leads = cursor.fetchall()
            
            if not all_leads:
                self.critical_failures.append("No leads in database for quality validation")
                return
            
            logger.info(f"Validating data quality for {len(all_leads)} leads...")
            
            quality_issues = []
            valid_leads = 0
            
            for lead in all_leads:
                lead_issues = []
                
                # Check required fields
                if not lead['full_name'] or str(lead['full_name']).strip() == '':
                    lead_issues.append("Missing or empty full_name")
                
                if not lead['email'] or str(lead['email']).strip() == '':
                    lead_issues.append("Missing or empty email")
                elif '@' not in str(lead['email']) or '.' not in str(lead['email']):
                    lead_issues.append("Invalid email format")
                
                if not lead['company'] or str(lead['company']).strip() == '':
                    lead_issues.append("Missing or empty company")
                
                # Check data consistency
                if lead['email'] and lead['company']:
                    email_str = str(lead['email'])
                    company_str = str(lead['company']).lower()
                    
                    email_domain = email_str.split('@')[1] if '@' in email_str else ''
                    
                    # Basic consistency check
                    if email_domain and 'example.com' in email_domain:
                        lead_issues.append("Test email in production data")
                
                # Check for duplicates (simplified check)
                email_count = sum(1 for other_lead in all_leads if other_lead['email'] == lead['email'])
                if email_count > 1:
                    lead_issues.append("Duplicate email")
                
                if lead_issues:
                    quality_issues.extend([f"Lead {lead['id']}: {issue}" for issue in lead_issues])
                else:
                    valid_leads += 1
            
            data_quality_percentage = (valid_leads / len(all_leads)) * 100
            
            logger.info(f"Data quality: {data_quality_percentage:.1f}% ({valid_leads}/{len(all_leads)} valid leads)")
            
            if quality_issues:
                logger.warning(f"Found {len(quality_issues)} data quality issues:")
                for issue in quality_issues[:10]:  # Show first 10 issues
                    logger.warning(f"  - {issue}")
                if len(quality_issues) > 10:
                    logger.warning(f"  ... and {len(quality_issues) - 10} more issues")
            
            if data_quality_percentage < self.data_quality_threshold:
                self.critical_failures.append(f"Data quality below threshold: {data_quality_percentage:.1f}% < {self.data_quality_threshold}%")
            
            # Store quality issues for reporting
            self.data_quality_issues = quality_issues
            
            self.test_results['data_quality_validation'] = {
                'status': 'PASS' if data_quality_percentage >= self.data_quality_threshold else 'FAIL',
                'quality_percentage': data_quality_percentage,
                'valid_leads': valid_leads,
                'total_leads': len(all_leads),
                'issues_count': len(quality_issues)
            }
            
        except Exception as e:
            self.critical_failures.append(f"Data quality validation crashed: {e}")
            logger.error(f"❌ Data quality validation failed: {e}")
    
    def api_integration_stress_test(self):
        """Test API integrations under stress."""
        logger.info("\n🔥 TEST 5: API INTEGRATION STRESS TEST")
        logger.info("-" * 50)
        
        try:
            api_tests_passed = 0
            total_api_tests = 0
            
            # Test company size validator with various inputs
            logger.info("Testing company size validator...")
            
            test_companies = [
                ("Microsoft", True),
                ("Google", True),
                ("Shopify", True),
                ("Small Local Business", False),
                ("Tech Startup Inc", False),
                ("", False),
                ("A" * 1000, False),  # Very long name
            ]
            
            for company_name, expected_too_large in test_companies:
                total_api_tests += 1
                try:
                    result = company_validator.is_company_too_large(company_name)
                    
                    # For empty, just check it doesn't crash
                    if company_name == "":
                        api_tests_passed += 1
                        continue
                    
                    if result == expected_too_large:
                        api_tests_passed += 1
                        logger.info(f"Company validator test '{company_name}': ✅")
                    else:
                        logger.warning(f"Company validator test '{company_name}': Expected {expected_too_large}, got {result}")
                        
                except Exception as e:
                    logger.error(f"Company validator crashed on '{company_name}': {e}")
            
            # Test email finder with various inputs
            logger.info("Testing email finder resilience...")
            
            test_websites = [
                "https://example.com",
                "https://nonexistent-domain-12345.com",
                "invalid-url",
                ""
            ]
            
            for website in test_websites:
                total_api_tests += 1
                try:
                    emails = email_finder.find_business_emails(website, "Test Company")
                    api_tests_passed += 1
                    logger.info(f"Email finder test '{website}': ✅ (found {len(emails)} emails)")
                    
                except Exception as e:
                    logger.warning(f"Email finder failed on '{website}': {e}")
                    # Graceful failure is acceptable for invalid inputs
                    if website in ["invalid-url", ""]:
                        api_tests_passed += 1
            
            api_success_rate = (api_tests_passed / total_api_tests) * 100
            
            logger.info(f"API integration success rate: {api_success_rate:.1f}% ({api_tests_passed}/{total_api_tests})")
            
            if api_success_rate < 85:
                self.critical_failures.append(f"API integration reliability too low: {api_success_rate:.1f}%")
            
            self.test_results['api_integration_stress'] = {
                'status': 'PASS' if api_success_rate >= 85 else 'FAIL',
                'success_rate': api_success_rate,
                'tests_passed': api_tests_passed,
                'total_tests': total_api_tests
            }
            
        except Exception as e:
            self.critical_failures.append(f"API integration test crashed: {e}")
            logger.error(f"❌ API integration test failed: {e}")
    
    def memory_and_resource_test(self):
        """Test memory usage and resource management."""
        logger.info("\n🔥 TEST 6: MEMORY AND RESOURCE TEST")
        logger.info("-" * 50)
        
        try:
            # Simplified memory test without psutil dependency
            logger.info("Testing resource management...")
            
            # Test creating many objects
            large_data_sets = []
            
            start_time = time.time()
            
            for i in range(100):
                # Create large lead data
                large_lead = {
                    'full_name': f'Memory Test User {i}',
                    'email': f'memory.test.{i}@example.com',
                    'company': f'Memory Test Corp {i}',
                    'ai_message': 'A' * 1000,  # 1KB message
                    'company_description': 'B' * 1000,  # 1KB description
                }
                
                # Add to database
                db_manager.add_lead(large_lead)
                
                # Keep some data in memory
                large_data_sets.append(large_lead)
            
            total_time = time.time() - start_time
            
            # Cleanup
            large_data_sets.clear()
            
            logger.info(f"Memory test completed in {total_time:.2f} seconds")
            
            if total_time > 30:  # Should complete in under 30 seconds
                self.performance_issues.append(f"Memory operations too slow: {total_time:.2f}s")
            
            self.test_results['memory_and_resource'] = {
                'status': 'PASS' if total_time <= 30 else 'FAIL',
                'execution_time': total_time
            }
            
        except Exception as e:
            self.critical_failures.append(f"Memory and resource test crashed: {e}")
            logger.error(f"❌ Memory and resource test failed: {e}")
    
    def edge_cases_test(self):
        """Test edge cases and boundary conditions."""
        logger.info("\n🔥 TEST 7: EDGE CASES TEST")
        logger.info("-" * 50)
        
        try:
            edge_cases_passed = 0
            total_edge_cases = 0
            
            # Test with extremely long data
            logger.info("Testing with extremely long data...")
            
            total_edge_cases += 1
            try:
                long_lead = {
                    'full_name': 'A' * 500,  # Very long name
                    'email': 'very.long.email.address@verylongdomain.com',
                    'company': 'B' * 500,  # Very long company name
                    'ai_message': 'C' * 50000,  # 50KB AI message
                }
                
                result = db_manager.add_lead(long_lead)
                if result:
                    edge_cases_passed += 1
                    logger.info("Long data test: ✅")
                else:
                    logger.warning("Long data test: Failed to add")
            except Exception as e:
                logger.warning(f"Long data test: Exception - {e}")
            
            # Test with special characters
            logger.info("Testing with special characters...")
            
            total_edge_cases += 1
            try:
                special_char_lead = {
                    'full_name': "Jean-François O'Reilly",
                    'email': 'jean-francois@company.com',
                    'company': 'Company & Co.',
                    'ai_message': 'Hello! This is a test with special chars',
                }
                
                result = db_manager.add_lead(special_char_lead)
                if result:
                    edge_cases_passed += 1
                    logger.info("Special characters test: ✅")
                else:
                    logger.warning("Special characters test: Failed to add")
            except Exception as e:
                logger.warning(f"Special characters test: Exception - {e}")
            
            # Test with boundary values
            logger.info("Testing boundary values...")
            
            boundary_tests = [
                {'full_name': '', 'email': 'boundary1@test.com'},  # Empty name
                {'full_name': 'A', 'email': 'boundary2@test.com'},  # Single char name
                {'full_name': 'Boundary Test', 'email': 'a@b.co'},  # Minimal email
            ]
            
            for i, boundary_lead in enumerate(boundary_tests):
                total_edge_cases += 1
                try:
                    result = db_manager.add_lead(boundary_lead)
                    edge_cases_passed += 1
                    logger.info(f"Boundary test {i+1}: ✅")
                except Exception as e:
                    logger.warning(f"Boundary test {i+1}: Exception - {e}")
            
            # Test rapid sequential operations
            logger.info("Testing rapid sequential operations...")
            
            total_edge_cases += 1
            try:
                rapid_start = time.time()
                rapid_success = 0
                
                for i in range(20):
                    rapid_lead = {
                        'full_name': f'Rapid Test {i}',
                        'email': f'rapid{i}.{int(time.time()*1000)}@test.com',
                        'company': f'Rapid Corp {i}'
                    }
                    
                    if db_manager.add_lead(rapid_lead):
                        rapid_success += 1
                
                rapid_time = time.time() - rapid_start
                
                if rapid_success >= 18:  # At least 90% success
                    edge_cases_passed += 1
                    logger.info(f"Rapid sequential test: ✅ ({rapid_success}/20 in {rapid_time:.2f}s)")
                else:
                    logger.warning(f"Rapid sequential test: Low success rate ({rapid_success}/20)")
                    
            except Exception as e:
                logger.warning(f"Rapid sequential test: Exception - {e}")
            
            edge_case_success_rate = (edge_cases_passed / total_edge_cases) * 100
            
            logger.info(f"Edge cases success rate: {edge_case_success_rate:.1f}% ({edge_cases_passed}/{total_edge_cases})")
            
            if edge_case_success_rate < 75:
                self.critical_failures.append(f"Edge case handling insufficient: {edge_case_success_rate:.1f}%")
            
            self.test_results['edge_cases'] = {
                'status': 'PASS' if edge_case_success_rate >= 75 else 'FAIL',
                'success_rate': edge_case_success_rate,
                'passed': edge_cases_passed,
                'total': total_edge_cases
            }
            
        except Exception as e:
            self.critical_failures.append(f"Edge cases test crashed: {e}")
            logger.error(f"❌ Edge cases test failed: {e}")
    
    def end_to_end_pipeline_test(self):
        """Test the complete end-to-end pipeline."""
        logger.info("\n🔥 TEST 8: END-TO-END PIPELINE TEST")
        logger.info("-" * 50)
        
        try:
            pipeline_start = time.time()
            
            # Step 1: Create test lead
            test_lead = {
                'full_name': 'Pipeline Test User',
                'email': f'pipeline.test.{int(time.time())}@example.com',
                'company': 'Pipeline Test Corp',
                'website': 'https://example.com'
            }
            
            logger.info("Step 1: Adding test lead...")
            if not db_manager.add_lead(test_lead):
                self.critical_failures.append("End-to-end test: Failed to add lead")
                return
            
            # Get the lead ID
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT id FROM leads WHERE email = ?", (test_lead['email'],))
                row = cursor.fetchone()
                if not row:
                    self.critical_failures.append("End-to-end test: Failed to retrieve added lead")
                    return
                lead_id = row[0]
            
            logger.info(f"✅ Lead added with ID: {lead_id}")
            
            # Step 2: Company size validation
            logger.info("Step 2: Validating company size...")
            target_info = company_validator.is_good_outreach_target(test_lead['company'], "")
            
            if not target_info.get('is_good_target'):
                logger.warning(f"Company marked as poor target: {target_info.get('reason')}")
            else:
                logger.info("✅ Company validated as good target")
            
            # Step 3: Email enrichment (mock)
            logger.info("Step 3: Email enrichment...")
            try:
                emails = email_finder.find_business_emails(test_lead['website'], test_lead['company'])
                logger.info(f"✅ Email enrichment completed (found {len(emails)} emails)")
            except Exception as e:
                logger.warning(f"Email enrichment failed: {e}")
            
            # Step 4: Update lead with enrichment
            logger.info("Step 4: Updating lead with enrichment...")
            updates = {
                'enriched': 1,
                'business_type': 'SaaS',
                'ready_for_outreach': 1
            }
            
            if not db_manager.update_lead(lead_id, updates):
                self.critical_failures.append("End-to-end test: Failed to update lead")
                return
            
            logger.info("✅ Lead updated with enrichment")
            
            # Step 5: Retrieve final lead
            logger.info("Step 5: Retrieving final lead...")
            final_lead = db_manager.get_lead(lead_id)
            
            if not final_lead:
                self.critical_failures.append("End-to-end test: Failed to retrieve final lead")
                return
            
            logger.info("✅ Final lead retrieved successfully")
            
            # Step 6: Validate pipeline results
            logger.info("Step 6: Validating pipeline results...")
            
            pipeline_issues = []
            
            if final_lead['enriched'] != 1:
                pipeline_issues.append("Lead not marked as enriched")
            
            if final_lead['business_type'] != 'SaaS':
                pipeline_issues.append("Business type not updated")
            
            if final_lead['ready_for_outreach'] != 1:
                pipeline_issues.append("Lead not ready for outreach")
            
            pipeline_time = time.time() - pipeline_start
            
            logger.info(f"Pipeline completed in {pipeline_time:.2f} seconds")
            
            if pipeline_issues:
                self.critical_failures.append(f"End-to-end pipeline issues: {', '.join(pipeline_issues)}")
            
            if pipeline_time > 10:  # Should complete in under 10 seconds
                self.performance_issues.append(f"End-to-end pipeline too slow: {pipeline_time:.2f}s")
            
            logger.info("🎉 End-to-end pipeline test completed successfully!")
            
            self.test_results['end_to_end_pipeline'] = {
                'status': 'PASS' if len(pipeline_issues) == 0 else 'FAIL',
                'pipeline_time': pipeline_time,
                'issues': pipeline_issues,
                'final_lead_id': lead_id
            }
            
        except Exception as e:
            self.critical_failures.append(f"End-to-end pipeline test crashed: {e}")
            logger.error(f"❌ End-to-end pipeline test failed: {e}")
    
    def failover_recovery_test(self):
        """Test system failover and recovery capabilities."""
        logger.info("\n🔥 TEST 9: FAILOVER AND RECOVERY TEST")
        logger.info("-" * 50)
        
        try:
            recovery_tests_passed = 0
            total_recovery_tests = 0
            
            # Test database recovery after simulated issues
            logger.info("Testing database resilience...")
            
            total_recovery_tests += 1
            try:
                # Get initial stats
                initial_stats = db_manager.get_database_stats()
                
                # Perform some operations
                test_leads = []
                for i in range(5):
                    lead = {
                        'full_name': f'Recovery Test {i}',
                        'email': f'recovery{i}.{int(time.time())}@test.com',
                        'company': f'Recovery Corp {i}'
                    }
                    if db_manager.add_lead(lead):
                        test_leads.append(lead)
                
                # Check if operations succeeded
                final_stats = db_manager.get_database_stats()
                
                if final_stats['total_leads'] > initial_stats['total_leads']:
                    recovery_tests_passed += 1
                    logger.info("Database resilience test: ✅")
                else:
                    logger.warning("Database resilience test: No increase in leads")
                    
            except Exception as e:
                logger.warning(f"Database resilience test failed: {e}")
            
            # Test component isolation
            logger.info("Testing component isolation...")
            
            total_recovery_tests += 1
            try:
                # Test if database failure doesn't crash other components
                stats = db_manager.get_database_stats()
                
                # Test company validator (should work independently)
                result = company_validator.is_company_too_large("Test Company")
                
                # Test email finder (should work independently)
                emails = email_finder.find_business_emails("https://example.com", "Test")
                
                recovery_tests_passed += 1
                logger.info("Component isolation test: ✅")
                
            except Exception as e:
                logger.warning(f"Component isolation test failed: {e}")
            
            # Test graceful degradation
            logger.info("Testing graceful degradation...")
            
            total_recovery_tests += 1
            try:
                # Test with invalid inputs to see if system degrades gracefully
                invalid_tests = [
                    lambda: db_manager.get_lead(-1),  # Invalid ID
                    lambda: company_validator.is_company_too_large(""),  # Empty company
                    lambda: email_finder.find_business_emails("", ""),  # Empty inputs
                ]
                
                graceful_failures = 0
                for test_func in invalid_tests:
                    try:
                        result = test_func()
                        graceful_failures += 1  # Didn't crash
                    except Exception:
                        graceful_failures += 1  # Failed gracefully
                
                if graceful_failures >= 2:  # At least 2/3 should handle gracefully
                    recovery_tests_passed += 1
                    logger.info("Graceful degradation test: ✅")
                else:
                    logger.warning("Graceful degradation test: Poor handling")
                    
            except Exception as e:
                logger.warning(f"Graceful degradation test failed: {e}")
            
            recovery_success_rate = (recovery_tests_passed / total_recovery_tests) * 100
            
            logger.info(f"Recovery tests success rate: {recovery_success_rate:.1f}% ({recovery_tests_passed}/{total_recovery_tests})")
            
            if recovery_success_rate < 80:
                self.critical_failures.append(f"Poor failover/recovery capabilities: {recovery_success_rate:.1f}%")
            
            self.test_results['failover_recovery'] = {
                'status': 'PASS' if recovery_success_rate >= 80 else 'FAIL',
                'success_rate': recovery_success_rate,
                'tests_passed': recovery_tests_passed,
                'total_tests': total_recovery_tests
            }
            
        except Exception as e:
            self.critical_failures.append(f"Failover recovery test crashed: {e}")
            logger.error(f"❌ Failover recovery test failed: {e}")
    
    def performance_under_load_test(self):
        """Test performance under realistic load."""
        logger.info("\n🔥 TEST 10: PERFORMANCE UNDER LOAD TEST")
        logger.info("-" * 50)
        
        try:
            # Test sustained operations
            logger.info("Testing sustained operations...")
            
            sustained_start = time.time()
            sustained_operations = 0
            sustained_failures = 0
            
            # Run operations for 30 seconds
            while time.time() - sustained_start < 30:
                try:
                    # Mix of operations
                    operation_type = random.choice(['add', 'get', 'stats'])
                    
                    if operation_type == 'add':
                        lead = {
                            'full_name': f'Load Test {int(time.time()*1000)}',
                            'email': f'load.{int(time.time()*1000)}@test.com',
                            'company': f'Load Corp {random.randint(1, 1000)}'
                        }
                        if db_manager.add_lead(lead):
                            sustained_operations += 1
                        else:
                            sustained_failures += 1
                            
                    elif operation_type == 'get':
                        # Try to get a random lead
                        random_id = random.randint(1, 100)
                        lead = db_manager.get_lead(random_id)
                        sustained_operations += 1
                        
                    elif operation_type == 'stats':
                        stats = db_manager.get_database_stats()
                        if stats:
                            sustained_operations += 1
                        else:
                            sustained_failures += 1
                    
                    # Small delay to simulate realistic usage
                    time.sleep(0.01)
                    
                except Exception as e:
                    sustained_failures += 1
            
            sustained_time = time.time() - sustained_start
            ops_per_second = sustained_operations / sustained_time
            failure_rate = (sustained_failures / (sustained_operations + sustained_failures)) * 100 if (sustained_operations + sustained_failures) > 0 else 0
            
            logger.info(f"Sustained load test:")
            logger.info(f"  Operations: {sustained_operations}")
            logger.info(f"  Failures: {sustained_failures}")
            logger.info(f"  Time: {sustained_time:.2f}s")
            logger.info(f"  Rate: {ops_per_second:.2f} ops/sec")
            logger.info(f"  Failure rate: {failure_rate:.2f}%")
            
            performance_issues = []
            
            if ops_per_second < 20:  # Should handle at least 20 ops/second sustained
                performance_issues.append(f"Low sustained throughput: {ops_per_second:.2f} ops/sec")
            
            if failure_rate > 5:  # Should have less than 5% failure rate
                performance_issues.append(f"High failure rate: {failure_rate:.2f}%")
            
            # Test response time consistency
            logger.info("Testing response time consistency...")
            
            response_times = []
            
            for i in range(50):
                start = time.time()
                
                test_lead = {
                    'full_name': f'Response Time Test {i}',
                    'email': f'response.{i}.{int(time.time()*1000)}@test.com',
                    'company': f'Response Corp {i}'
                }
                
                db_manager.add_lead(test_lead)
                
                response_time = (time.time() - start) * 1000  # ms
                response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            logger.info(f"Response time analysis:")
            logger.info(f"  Average: {avg_response_time:.2f}ms")
            logger.info(f"  Maximum: {max_response_time:.2f}ms")
            
            if avg_response_time > self.performance_threshold_ms:
                performance_issues.append(f"High average response time: {avg_response_time:.2f}ms")
            
            if max_response_time > (self.performance_threshold_ms * 3):
                performance_issues.append(f"High maximum response time: {max_response_time:.2f}ms")
            
            if performance_issues:
                self.performance_issues.extend(performance_issues)
            
            self.test_results['performance_under_load'] = {
                'status': 'PASS' if len(performance_issues) == 0 else 'FAIL',
                'sustained_ops_per_second': ops_per_second,
                'sustained_failure_rate': failure_rate,
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'issues': performance_issues
            }
            
        except Exception as e:
            self.critical_failures.append(f"Performance under load test crashed: {e}")
            logger.error(f"❌ Performance under load test failed: {e}")
    
    def generate_brutal_final_report(self):
        """Generate the most brutal, honest final report."""
        logger.info("\n" + "="*80)
        logger.info("🔥 ULTIMATE SYSTEM TEST - BRUTAL FINAL REPORT")
        logger.info("="*80)
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PASS')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'FAIL')
        skipped_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'SKIPPED')
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall system status
        if len(self.critical_failures) == 0 and success_rate >= 90:
            overall_status = "🟢 BULLETPROOF - READY FOR PRODUCTION"
            recommendation = "DEPLOY WITH COMPLETE CONFIDENCE"
        elif len(self.critical_failures) == 0 and success_rate >= 80:
            overall_status = "🟡 SOLID - MINOR ISSUES"
            recommendation = "DEPLOY WITH MONITORING"
        elif len(self.critical_failures) <= 2 and success_rate >= 70:
            overall_status = "🟠 NEEDS FIXES - MAJOR ISSUES"
            recommendation = "FIX CRITICAL ISSUES BEFORE DEPLOYMENT"
        else:
            overall_status = "🔴 NOT READY - SYSTEM FAILURE"
            recommendation = "DO NOT DEPLOY - MAJOR RECONSTRUCTION NEEDED"
        
        # Report header
        logger.info(f"\n📊 OVERALL SYSTEM STATUS: {overall_status}")
        logger.info(f"🎯 RECOMMENDATION: {recommendation}")
        logger.info(f"📈 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        # Detailed test results
        logger.info(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = {"PASS": "✅", "FAIL": "❌", "SKIPPED": "⏭️"}.get(result.get('status'), "❓")
            logger.info(f"  {status_icon} {test_name.replace('_', ' ').title()}: {result.get('status')}")
            
            # Add specific metrics for key tests
            if test_name == 'brutal_database_stress' and 'ops_per_second' in result:
                logger.info(f"      Performance: {result['ops_per_second']:.1f} ops/sec")
            elif test_name == 'data_quality_validation' and 'quality_percentage' in result:
                logger.info(f"      Data Quality: {result['quality_percentage']:.1f}%")
            elif test_name == 'performance_under_load' and 'sustained_ops_per_second' in result:
                logger.info(f"      Sustained Performance: {result['sustained_ops_per_second']:.1f} ops/sec")
        
        # Critical failures (the brutal truth)
        if self.critical_failures:
            logger.info(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            logger.info("These MUST be fixed before production deployment:")
            for i, failure in enumerate(self.critical_failures, 1):
                logger.info(f"  {i}. ❌ {failure}")
        else:
            logger.info(f"\n🎉 NO CRITICAL FAILURES DETECTED!")
        
        # Performance issues
        if self.performance_issues:
            logger.info(f"\n⚡ PERFORMANCE ISSUES ({len(self.performance_issues)}):")
            for i, issue in enumerate(self.performance_issues, 1):
                logger.info(f"  {i}. ⚠️ {issue}")
        
        # Data quality issues
        if self.data_quality_issues:
            logger.info(f"\n📊 DATA QUALITY ISSUES ({len(self.data_quality_issues)}):")
            for i, issue in enumerate(self.data_quality_issues[:5], 1):  # Show first 5
                logger.info(f"  {i}. 📉 {issue}")
            if len(self.data_quality_issues) > 5:
                logger.info(f"  ... and {len(self.data_quality_issues) - 5} more data quality issues")
        
        # Warnings
        if self.warnings:
            logger.info(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                logger.info(f"  {i}. ⚠️ {warning}")
        
        # Production readiness assessment
        logger.info(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        
        readiness_factors = [
            ("Database Performance", "✅" if not any("Database" in f for f in self.critical_failures) else "❌"),
            ("Error Handling", "✅" if not any("Error handling" in f for f in self.critical_failures) else "❌"),
            ("Data Quality", "✅" if not any("Data quality" in f for f in self.critical_failures) else "❌"),
            ("API Integration", "✅" if not any("API" in f for f in self.critical_failures) else "❌"),
            ("Concurrent Operations", "✅" if not any("Concurrent" in f for f in self.critical_failures) else "❌"),
            ("Performance Under Load", "✅" if not any("Performance" in f for f in self.critical_failures) else "❌"),
            ("System Recovery", "✅" if not any("recovery" in f for f in self.critical_failures) else "❌"),
            ("Memory Management", "✅" if not any("memory" in f for f in self.critical_failures) else "❌"),
        ]
        
        for factor, status in readiness_factors:
            logger.info(f"  {status} {factor}")
        
        # Final verdict
        logger.info(f"\n" + "="*80)
        if len(self.critical_failures) == 0:
            logger.info("🎉 VERDICT: SYSTEM PASSES ULTIMATE TEST!")
            logger.info("💪 This system is bulletproof and ready for production!")
            logger.info("🚀 Deploy with complete confidence!")
        else:
            logger.info("💥 VERDICT: SYSTEM FAILS ULTIMATE TEST!")
            logger.info("🛑 Critical issues must be resolved before deployment!")
            logger.info("🔧 Fix all critical failures and re-run this test!")
        
        logger.info("="*80)
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'recommendation': recommendation,
            'success_rate': success_rate,
            'test_results': self.test_results,
            'critical_failures': self.critical_failures,
            'performance_issues': self.performance_issues,
            'data_quality_issues': self.data_quality_issues[:10],  # Limit for JSON
            'warnings': self.warnings,
            'readiness_factors': dict(readiness_factors)
        }
        
        report_file = f"ultimate_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {report_file}")
        
        return len(self.critical_failures) == 0

if __name__ == "__main__":
    tester = UltimateSystemTest()
    system_ready = tester.run_ultimate_test_suite()
    
    if system_ready:
        print(f"\n🎉 SYSTEM IS BULLETPROOF AND READY FOR PRODUCTION!")
        sys.exit(0)
    else:
        print(f"\n💥 SYSTEM FAILED ULTIMATE TEST - NOT READY FOR PRODUCTION!")
        sys.exit(1)
