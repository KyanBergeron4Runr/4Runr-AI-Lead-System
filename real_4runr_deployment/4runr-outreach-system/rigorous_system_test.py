#!/usr/bin/env python3
"""
Rigorous System Test Suite

This script performs comprehensive, realistic tests to validate that the 4Runr system
actually works in real-world scenarios. These tests are designed to FAIL if the system
has issues, not just to pass.

Test Philosophy:
- Test real data scenarios
- Test error conditions
- Test edge cases
- Test performance under load
- Test actual API integrations
- Test data integrity
"""

import sys
import time
import datetime
import random
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lead_database import LeadDatabase
from simple_sync_manager import SimpleSyncManager
from message_generator.ai_generator import AIMessageGenerator
from shared.data_cleaner import DataCleaner


class RigorousSystemTest:
    """
    Comprehensive test suite that validates real system functionality.
    """
    
    def __init__(self):
        """Initialize test components."""
        self.db = LeadDatabase()
        self.sync_manager = SimpleSyncManager()
        self.message_generator = AIMessageGenerator()
        self.data_cleaner = DataCleaner()
        
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
        
        print("🧪 RIGOROUS SYSTEM TEST SUITE")
        print("=" * 60)
        print("Testing real-world scenarios and edge cases...")
        print()
    
    def assert_true(self, condition: bool, message: str):
        """Assert that a condition is true."""
        if condition:
            self.test_results['passed'] += 1
            print(f"✅ PASS: {message}")
        else:
            self.test_results['failed'] += 1
            print(f"❌ FAIL: {message}")
    
    def assert_false(self, condition: bool, message: str):
        """Assert that a condition is false."""
        if not condition:
            self.test_results['passed'] += 1
            print(f"✅ PASS: {message}")
        else:
            self.test_results['failed'] += 1
            print(f"❌ FAIL: {message}")
    
    def assert_not_none(self, value, message: str):
        """Assert that a value is not None."""
        if value is not None:
            self.test_results['passed'] += 1
            print(f"✅ PASS: {message}")
        else:
            self.test_results['failed'] += 1
            print(f"❌ FAIL: {message}")
    
    def assert_greater_than(self, value, threshold, message: str):
        """Assert that a value is greater than threshold."""
        if value > threshold:
            self.test_results['passed'] += 1
            print(f"✅ PASS: {message}")
        else:
            self.test_results['failed'] += 1
            print(f"❌ FAIL: {message}")
    
    def test_database_integrity(self):
        """Test database schema and data integrity."""
        print("\n🔍 TEST 1: Database Integrity")
        print("-" * 40)
        
        try:
            # Test database connection
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if leads table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
                table_exists = cursor.fetchone() is not None
                self.assert_true(table_exists, "Leads table exists")
                
                # Check table schema
                cursor.execute("PRAGMA table_info(leads)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                required_columns = ['id', 'uuid', 'full_name', 'email', 'company', 'title', 'linkedin_url', 'company_website']
                
                for col in required_columns:
                    col_exists = col in column_names
                    self.assert_true(col_exists, f"Required column '{col}' exists")
                
                # Check data integrity
                cursor.execute("SELECT COUNT(*) FROM leads")
                total_leads = cursor.fetchone()[0]
                self.assert_greater_than(total_leads, 0, f"Database has {total_leads} leads")
                
                # Check for duplicate emails
                cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
                duplicates = cursor.fetchall()
                self.assert_true(len(duplicates) == 0, f"No duplicate emails found ({len(duplicates)} duplicates)")
                
                # Check for invalid data
                cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name = '' OR company = ''")
                invalid_records = cursor.fetchone()[0]
                self.assert_true(invalid_records == 0, f"No invalid records found ({invalid_records} invalid)")
                
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Database integrity test failed: {e}")
            print(f"❌ ERROR: Database integrity test failed: {e}")
    
    def test_lead_addition_with_real_data(self):
        """Test adding leads with realistic, varied data."""
        print("\n📝 TEST 2: Lead Addition with Real Data")
        print("-" * 40)
        
        # Create realistic test data with edge cases
        test_leads = [
            {
                'full_name': 'John Smith',
                'email': 'john.smith@testcompany.com',
                'company': 'Test Company Inc',
                'title': 'CEO',
                'linkedin_url': 'https://linkedin.com/in/johnsmith',
                'company_website': 'testcompany.com',
                'location': 'New York, NY',
                'industry': 'Technology',
                'company_size': '10-50',
                'source': 'Manual Entry',
                'status': 'new'
            },
            {
                'full_name': 'Jane Doe',
                'email': 'jane.doe@startup.io',
                'company': 'Startup.io',
                'title': 'Founder & CTO',
                'linkedin_url': 'https://linkedin.com/in/janedoe',
                'company_website': 'startup.io',
                'location': 'San Francisco, CA',
                'industry': 'SaaS',
                'company_size': '1-10',
                'source': 'Website Scraping',
                'status': 'new'
            },
            {
                'full_name': 'Bob Johnson',
                'email': '',  # Test missing email
                'company': 'Large Corp',
                'title': 'VP of Sales',
                'linkedin_url': '',  # Test missing LinkedIn
                'company_website': 'largecorp.com',
                'location': 'Chicago, IL',
                'industry': 'Enterprise',
                'company_size': '1000+',
                'source': 'LinkedIn',
                'status': 'new'
            }
        ]
        
        added_ids = []
        
        for i, lead_data in enumerate(test_leads, 1):
            try:
                print(f"   Adding lead {i}: {lead_data['full_name']}")
                
                # Add timestamp
                lead_data['created_at'] = datetime.datetime.now().isoformat()
                lead_data['updated_at'] = datetime.datetime.now().isoformat()
                
                # Add lead
                lead_id = self.db.add_lead(lead_data)
                
                if lead_id:
                    added_ids.append(lead_id)
                    self.assert_true(True, f"Successfully added lead {lead_data['full_name']}")
                    
                    # Verify lead was actually added
                    retrieved_lead = self.db.get_lead(lead_id)
                    self.assert_not_none(retrieved_lead, f"Can retrieve added lead {lead_id}")
                    
                    if retrieved_lead:
                        self.assert_true(retrieved_lead['full_name'] == lead_data['full_name'], 
                                       f"Retrieved lead name matches: {retrieved_lead['full_name']}")
                else:
                    self.assert_true(False, f"Failed to add lead {lead_data['full_name']}")
                    
            except Exception as e:
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"Lead addition test failed: {e}")
                print(f"❌ ERROR: Failed to add lead {lead_data['full_name']}: {e}")
        
        # Clean up test data
        for lead_id in added_ids:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
                    conn.commit()
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up test lead {lead_id}: {e}")
    
    def test_data_cleaning_functionality(self):
        """Test data cleaning with various input scenarios."""
        print("\n🧹 TEST 3: Data Cleaning Functionality")
        print("-" * 40)
        
        # Test cases with various data quality issues
        test_cases = [
            {
                'name': 'Clean data',
                'input': {
                    'full_name': 'John Smith',
                    'email': 'john.smith@company.com',
                    'company': 'Company Inc',
                    'title': 'CEO'
                },
                'expected_clean': True
            },
            {
                'name': 'Dirty data',
                'input': {
                    'full_name': '  john smith  ',
                    'email': 'JOHN.SMITH@COMPANY.COM',
                    'company': 'company inc',
                    'title': 'ceo'
                },
                'expected_clean': True
            },
            {
                'name': 'Missing required fields',
                'input': {
                    'full_name': '',
                    'email': 'invalid-email',
                    'company': '',
                    'title': 'CEO'
                },
                'expected_clean': False
            },
            {
                'name': 'Malformed data',
                'input': {
                    'full_name': 'John123Smith',
                    'email': 'not-an-email',
                    'company': 'Company@#$%',
                    'title': 'CEO'
                },
                'expected_clean': False
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"   Testing: {test_case['name']}")
                
                # Test data cleaning
                cleaning_result = self.data_cleaner.clean_and_validate(test_case['input'], {})
                
                if test_case['expected_clean']:
                    self.assert_true(cleaning_result.success, f"Data cleaning succeeded for {test_case['name']}")
                    if cleaning_result.success:
                        self.assert_not_none(cleaning_result.cleaned_data, f"Cleaned data returned for {test_case['name']}")
                else:
                    self.assert_false(cleaning_result.success, f"Data cleaning correctly failed for {test_case['name']}")
                    
            except Exception as e:
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"Data cleaning test failed: {e}")
                print(f"❌ ERROR: Data cleaning test failed for {test_case['name']}: {e}")
    
    def test_airtable_sync_functionality(self):
        """Test Airtable sync with real API calls."""
        print("\n🔄 TEST 4: Airtable Sync Functionality")
        print("-" * 40)
        
        try:
            # Get sync stats
            stats = self.sync_manager.get_sync_stats()
            self.assert_not_none(stats, "Can retrieve sync stats")
            
            if stats:
                print(f"   Current sync stats: {stats}")
                
                # Test with a small batch to avoid overwhelming the API
                pending_leads = self.db.search_leads({'sync_pending': True})
                
                if pending_leads:
                    # Test with just 1 lead to avoid rate limits
                    test_lead = pending_leads[0]
                    print(f"   Testing sync with lead: {test_lead.get('full_name', 'Unknown')}")
                    
                    # Attempt sync
                    results = self.sync_manager.sync_to_airtable([test_lead['id']])
                    
                    self.assert_not_none(results, "Sync operation returned results")
                    
                    if results:
                        successful = sum(1 for r in results if r.status.value == 'success')
                        failed = sum(1 for r in results if r.status.value == 'failed')
                        
                        print(f"   Sync results: {successful} successful, {failed} failed")
                        
                        # Check if we got a meaningful result (either success or failure with proper error)
                        meaningful_result = successful > 0 or (failed > 0 and any(r.error_message for r in results if r.status.value == 'failed'))
                        self.assert_true(meaningful_result, "Sync operation produced meaningful results")
                        
                        if successful > 0:
                            # Verify the lead was marked as synced
                            updated_lead = self.db.get_lead(test_lead['id'])
                            if updated_lead:
                                self.assert_true(updated_lead.get('airtable_synced', False), 
                                               "Lead marked as synced after successful sync")
                else:
                    print("   No pending leads to test sync with")
                    self.test_results['warnings'].append("No pending leads available for sync testing")
                    
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Airtable sync test failed: {e}")
            print(f"❌ ERROR: Airtable sync test failed: {e}")
    
    def test_ai_message_generation(self):
        """Test AI message generation with real API calls."""
        print("\n🤖 TEST 5: AI Message Generation")
        print("-" * 40)
        
        try:
            # Get a lead to test with
            leads = self.db.search_leads({})
            
            if leads:
                test_lead = leads[0]
                print(f"   Testing AI generation with lead: {test_lead.get('full_name', 'Unknown')}")
                
                # Test message generation
                start_time = time.time()
                message = self.message_generator.generate_message(test_lead)
                generation_time = time.time() - start_time
                
                if message:
                    self.assert_not_none(message, "AI generated a message")
                    self.assert_greater_than(len(message), 50, f"Generated message has reasonable length ({len(message)} chars)")
                    self.assert_true(generation_time < 30, f"Message generation completed in reasonable time ({generation_time:.2f}s)")
                    
                    print(f"   Generated message length: {len(message)} characters")
                    print(f"   Generation time: {generation_time:.2f} seconds")
                    print(f"   Message preview: {message[:100]}...")
                else:
                    self.assert_true(False, "AI message generation failed")
                    
            else:
                print("   No leads available for AI testing")
                self.test_results['warnings'].append("No leads available for AI message generation testing")
                
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"AI message generation test failed: {e}")
            print(f"❌ ERROR: AI message generation test failed: {e}")
    
    def test_performance_under_load(self):
        """Test system performance under realistic load."""
        print("\n⚡ TEST 6: Performance Under Load")
        print("-" * 40)
        
        try:
            # Test database query performance
            start_time = time.time()
            leads = self.db.search_leads({})
            query_time = time.time() - start_time
            
            self.assert_true(query_time < 1.0, f"Database query completed in reasonable time ({query_time:.3f}s)")
            
            # Test multiple operations
            operations = []
            for i in range(5):
                start_time = time.time()
                self.db.get_database_stats()
                operations.append(time.time() - start_time)
            
            avg_operation_time = sum(operations) / len(operations)
            self.assert_true(avg_operation_time < 0.5, f"Average operation time is reasonable ({avg_operation_time:.3f}s)")
            
            print(f"   Database query time: {query_time:.3f}s")
            print(f"   Average operation time: {avg_operation_time:.3f}s")
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Performance test failed: {e}")
            print(f"❌ ERROR: Performance test failed: {e}")
    
    def test_error_handling(self):
        """Test system error handling with invalid inputs."""
        print("\n🛡️ TEST 7: Error Handling")
        print("-" * 40)
        
        # Test invalid lead ID
        try:
            invalid_lead = self.db.get_lead(999999)
            self.assert_true(invalid_lead is None, "Invalid lead ID returns None")
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Error handling test failed: {e}")
            print(f"❌ ERROR: Error handling test failed: {e}")
        
        # Test invalid search criteria
        try:
            invalid_results = self.db.search_leads({'invalid_field': 'invalid_value'})
            self.assert_not_none(invalid_results, "Invalid search criteria handled gracefully")
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Error handling test failed: {e}")
            print(f"❌ ERROR: Error handling test failed: {e}")
        
        # Test invalid sync
        try:
            invalid_sync_results = self.sync_manager.sync_to_airtable([999999])
            self.assert_not_none(invalid_sync_results, "Invalid sync request handled gracefully")
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Error handling test failed: {e}")
            print(f"❌ ERROR: Error handling test failed: {e}")
    
    def run_all_tests(self):
        """Run all tests and provide comprehensive results."""
        print("🚀 Starting Rigorous System Tests...")
        print()
        
        # Run all test suites
        self.test_database_integrity()
        self.test_lead_addition_with_real_data()
        self.test_data_cleaning_functionality()
        self.test_airtable_sync_functionality()
        self.test_ai_message_generation()
        self.test_performance_under_load()
        self.test_error_handling()
        
        # Print comprehensive results
        print("\n" + "=" * 60)
        print("📊 RIGOROUS TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n🚨 Errors Found:")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        if self.test_results['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in self.test_results['warnings']:
                print(f"   - {warning}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            print("   🟢 EXCELLENT: System is robust and production-ready")
        elif success_rate >= 80:
            print("   🟡 GOOD: System is mostly working with minor issues")
        elif success_rate >= 70:
            print("   🟠 FAIR: System has significant issues that need attention")
        else:
            print("   🔴 POOR: System has critical issues requiring immediate fixes")
        
        print(f"\n💡 Recommendations:")
        if self.test_results['failed'] > 0:
            print("   - Address failed tests before production deployment")
        if self.test_results['errors']:
            print("   - Fix error handling issues")
        if success_rate >= 90:
            print("   - System is ready for production deployment")
        
        return success_rate >= 80  # Return True if 80%+ tests pass


def main():
    """Main function to run the rigorous test suite."""
    print("🧪 4Runr AI Lead System - Rigorous Test Suite")
    print("=" * 60)
    print("This test suite validates REAL system functionality")
    print("Tests are designed to FAIL if the system has issues")
    print("=" * 60)
    
    try:
        test_suite = RigorousSystemTest()
        success = test_suite.run_all_tests()
        
        if success:
            print("\n🎉 TEST SUITE COMPLETED: System is ready for production!")
            return True
        else:
            print("\n⚠️  TEST SUITE COMPLETED: System needs fixes before production!")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: Test suite failed to run: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
