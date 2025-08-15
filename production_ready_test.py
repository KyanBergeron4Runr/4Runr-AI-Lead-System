#!/usr/bin/env python3
"""
Production Ready Test - Comprehensive system validation without emojis
"""

import os
import sys
import time
import sqlite3
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

from production_db_manager import db_manager

# Configure logging without emojis
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionReadyTester:
    """Production-ready system tester."""
    
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'performance': {},
            'start_time': datetime.now()
        }
        
    def run_production_tests(self):
        """Run production readiness tests."""
        logger.info("PRODUCTION READINESS TESTING")
        logger.info("=" * 50)
        
        try:
            # Core functionality tests
            self.test_database_operations()
            self.test_lead_data_quality()
            self.test_airtable_connectivity()
            self.test_system_performance()
            self.test_data_integrity()
            
            # Generate final report
            return self.generate_final_report()
            
        except Exception as e:
            logger.error(f"CRITICAL TEST FAILURE: {e}")
            return False
    
    def test_database_operations(self):
        """Test core database operations."""
        logger.info("\nTESTING: Database Operations")
        logger.info("-" * 30)
        
        try:
            # Test 1: Basic connectivity
            start_time = time.time()
            stats = db_manager.get_database_stats()
            db_time = time.time() - start_time
            
            if stats:
                self.test_passed("Database connectivity")
                self.test_results['performance']['db_response_time'] = db_time
                logger.info(f"  Database response time: {db_time:.3f}s")
            else:
                self.test_failed("Database connectivity failed")
                return
            
            # Test 2: Data integrity
            with db_manager.get_connection() as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                
                if integrity == "ok":
                    self.test_passed("Database integrity")
                else:
                    self.test_failed(f"Database integrity compromised: {integrity}")
            
            # Test 3: Lead count verification
            lead_count = stats.get('total_leads', 0)
            if lead_count > 0:
                self.test_passed(f"Lead data present ({lead_count} leads)")
                logger.info(f"  Found {lead_count} leads in database")
            else:
                self.test_failed("No leads found in database")
                
        except Exception as e:
            self.test_failed(f"Database operations: {e}")
    
    def test_lead_data_quality(self):
        """Test lead data quality standards."""
        logger.info("\nTESTING: Lead Data Quality")
        logger.info("-" * 30)
        
        try:
            with db_manager.get_connection() as conn:
                # Test LinkedIn URL coverage
                cursor = conn.execute("SELECT COUNT(*) FROM leads")
                total_leads = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url IS NOT NULL AND linkedin_url != '' AND linkedin_url != 'N/A'")
                linkedin_leads = cursor.fetchone()[0]
                
                linkedin_coverage = (linkedin_leads / total_leads * 100) if total_leads > 0 else 0
                
                if linkedin_coverage >= 95:
                    self.test_passed(f"LinkedIn coverage ({linkedin_coverage:.1f}%)")
                    logger.info(f"  LinkedIn coverage: {linkedin_coverage:.1f}%")
                else:
                    self.test_failed(f"LinkedIn coverage too low: {linkedin_coverage:.1f}%")
                
                # Test business type coverage
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE business_type IS NOT NULL AND business_type != ''")
                business_type_leads = cursor.fetchone()[0]
                
                business_type_coverage = (business_type_leads / total_leads * 100) if total_leads > 0 else 0
                
                if business_type_coverage >= 90:
                    self.test_passed(f"Business type coverage ({business_type_coverage:.1f}%)")
                    logger.info(f"  Business type coverage: {business_type_coverage:.1f}%")
                else:
                    self.test_failed(f"Business type coverage too low: {business_type_coverage:.1f}%")
                
                # Test AI message quality
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE ai_message IS NOT NULL AND LENGTH(ai_message) > 500")
                quality_messages = cursor.fetchone()[0]
                
                message_quality = (quality_messages / total_leads * 100) if total_leads > 0 else 0
                
                if message_quality >= 90:
                    self.test_passed(f"AI message quality ({message_quality:.1f}%)")
                    logger.info(f"  AI message quality: {message_quality:.1f}%")
                else:
                    self.test_failed(f"AI message quality too low: {message_quality:.1f}%")
                
                self.test_results['performance']['data_quality'] = {
                    'linkedin_coverage': linkedin_coverage,
                    'business_type_coverage': business_type_coverage,
                    'message_quality': message_quality
                }
                
        except Exception as e:
            self.test_failed(f"Lead data quality: {e}")
    
    def test_airtable_connectivity(self):
        """Test Airtable integration."""
        logger.info("\nTESTING: Airtable Integration")
        logger.info("-" * 30)
        
        try:
            # Check environment variables
            api_key = os.getenv('AIRTABLE_API_KEY')
            base_id = os.getenv('AIRTABLE_BASE_ID')
            table_name = os.getenv('AIRTABLE_TABLE_NAME')
            
            if not all([api_key, base_id, table_name]):
                self.test_failed("Airtable environment variables missing")
                return
            
            # Test API connectivity
            headers = {
                'Authorization': f"Bearer {api_key}",
                'Content-Type': 'application/json'
            }
            
            url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            api_time = time.time() - start_time
            
            if response.status_code == 200:
                self.test_passed("Airtable API connectivity")
                self.test_results['performance']['airtable_response_time'] = api_time
                logger.info(f"  Airtable response time: {api_time:.3f}s")
                
                # Check if we can read records
                data = response.json()
                records = data.get('records', [])
                logger.info(f"  Found {len(records)} records in Airtable")
                
            else:
                self.test_failed(f"Airtable API error: {response.status_code}")
                
        except requests.RequestException as e:
            self.test_failed(f"Airtable connectivity: {e}")
        except Exception as e:
            self.test_failed(f"Airtable integration: {e}")
    
    def test_system_performance(self):
        """Test system performance metrics."""
        logger.info("\nTESTING: System Performance")
        logger.info("-" * 30)
        
        try:
            # Test response times
            response_times = []
            
            for i in range(10):
                start = time.time()
                db_manager.get_database_stats()
                end = time.time()
                response_times.append(end - start)
            
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            
            if avg_response < 0.1 and max_response < 0.5:
                self.test_passed("System response times")
                self.test_results['performance']['avg_response_time'] = avg_response
                self.test_results['performance']['max_response_time'] = max_response
                logger.info(f"  Average response time: {avg_response:.3f}s")
                logger.info(f"  Maximum response time: {max_response:.3f}s")
            else:
                self.test_failed(f"Performance degraded: avg={avg_response:.3f}s, max={max_response:.3f}s")
                
        except Exception as e:
            self.test_failed(f"Performance testing: {e}")
    
    def test_data_integrity(self):
        """Test data integrity and consistency."""
        logger.info("\nTESTING: Data Integrity")
        logger.info("-" * 30)
        
        try:
            with db_manager.get_connection() as conn:
                # Test for duplicate emails
                cursor = conn.execute("SELECT email, COUNT(*) FROM leads WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1")
                duplicates = cursor.fetchall()
                
                if len(duplicates) == 0:
                    self.test_passed("No duplicate emails")
                else:
                    self.test_failed(f"Found {len(duplicates)} duplicate emails")
                
                # Test for required fields
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE full_name IS NULL OR full_name = ''")
                missing_names = cursor.fetchone()[0]
                
                if missing_names == 0:
                    self.test_passed("All leads have names")
                else:
                    self.test_failed(f"Found {missing_names} leads without names")
                
                # Test for valid email formats
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE email NOT LIKE '%@%' AND email IS NOT NULL AND email != ''")
                invalid_emails = cursor.fetchone()[0]
                
                if invalid_emails == 0:
                    self.test_passed("All emails are valid format")
                else:
                    self.test_failed(f"Found {invalid_emails} invalid email formats")
                
        except Exception as e:
            self.test_failed(f"Data integrity testing: {e}")
    
    def test_passed(self, test_name):
        """Record a passed test."""
        self.test_results['passed'] += 1
        logger.info(f"PASSED: {test_name}")
    
    def test_failed(self, test_name):
        """Record a failed test."""
        self.test_results['failed'] += 1
        self.test_results['errors'].append(test_name)
        logger.error(f"FAILED: {test_name}")
    
    def generate_final_report(self):
        """Generate the final production readiness report."""
        end_time = datetime.now()
        duration = end_time - self.test_results['start_time']
        
        logger.info("\n" + "=" * 60)
        logger.info("PRODUCTION READINESS REPORT")
        logger.info("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"TEST SUMMARY:")
        logger.info(f"  Tests Passed: {self.test_results['passed']}")
        logger.info(f"  Tests Failed: {self.test_results['failed']}")
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        logger.info(f"  Total Duration: {duration}")
        
        if self.test_results['performance']:
            logger.info(f"\nPERFORMANCE METRICS:")
            for metric, value in self.test_results['performance'].items():
                if isinstance(value, dict):
                    logger.info(f"  {metric}:")
                    for sub_metric, sub_value in value.items():
                        logger.info(f"    {sub_metric}: {sub_value:.1f}%")
                elif isinstance(value, float):
                    logger.info(f"  {metric}: {value:.3f}s")
                else:
                    logger.info(f"  {metric}: {value}")
        
        if self.test_results['errors']:
            logger.info(f"\nFAILED TESTS:")
            for error in self.test_results['errors']:
                logger.info(f"  - {error}")
            
            logger.info("\nSYSTEM NOT READY FOR PRODUCTION!")
            logger.info("Please fix the failed tests before deployment.")
            return False
        else:
            logger.info(f"\nALL TESTS PASSED!")
            logger.info(f"SYSTEM IS 100% PRODUCTION READY!")
            logger.info(f"Data quality is excellent and all integrations work perfectly.")
            return True

if __name__ == "__main__":
    tester = ProductionReadyTester()
    success = tester.run_production_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("SYSTEM IS PRODUCTION READY!")
        print("=" * 50)
        exit(0)
    else:
        print("\n" + "=" * 50)
        print("SYSTEM NEEDS FIXES BEFORE PRODUCTION!")
        print("=" * 50)
        exit(1)
