#!/usr/bin/env python3
"""
Simple Database Test

This script tests database functionality using direct SQLite connections
to avoid the connection pool timeout issues.
"""

import sys
import time
import datetime
import sqlite3
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


class SimpleDatabaseTest:
    """
    Simple database test using direct SQLite connections.
    """
    
    def __init__(self):
        """Initialize test."""
        self.db_path = "4runr-outreach-system/data/leads_cache.db"
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        print("🧪 SIMPLE DATABASE TEST")
        print("=" * 40)
        print("Testing with direct SQLite connections...")
        print()
    
    def assert_true(self, condition: bool, message: str):
        """Assert that a condition is true."""
        if condition:
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
    
    def test_database_connection(self):
        """Test basic database connection and queries."""
        print("\n🔍 TEST 1: Database Connection")
        print("-" * 30)
        
        try:
            # Test direct connection
            start_time = time.time()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            connection_time = time.time() - start_time
            
            self.assert_true(connection_time < 0.1, f"Database connection fast ({connection_time:.3f}s)")
            
            # Test simple query
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            self.assert_true(query_time < 0.1, f"Simple query fast ({query_time:.3f}s)")
            self.assert_greater_than(count, 0, f"Database has {count} leads")
            
            conn.close()
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Database connection test failed: {e}")
            print(f"❌ ERROR: Database connection test failed: {e}")
    
    def test_lead_operations(self):
        """Test lead operations with direct database access."""
        print("\n📝 TEST 2: Lead Operations")
        print("-" * 30)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test adding a lead
            test_lead = {
                'uuid': 'test-uuid-123',
                'full_name': 'Test User',
                'email': 'test@example.com',
                'company': 'Test Company',
                'title': 'Test Title',
                'linkedin_url': 'https://linkedin.com/in/testuser',
                'company_website': 'testcompany.com',
                'location': 'Test City',
                'industry': 'Technology',
                'company_size': '10-50',
                'source': 'Test',
                'status': 'new',
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            # Insert test lead
            start_time = time.time()
            cursor.execute("""
                INSERT INTO leads (
                    id, uuid, full_name, email, company, title, linkedin_url, company_website,
                    location, industry, company_size, source, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_lead['uuid'], test_lead['uuid'], test_lead['full_name'], test_lead['email'],
                test_lead['company'], test_lead['title'], test_lead['linkedin_url'],
                test_lead['company_website'], test_lead['location'], test_lead['industry'],
                test_lead['company_size'], test_lead['source'], test_lead['status'],
                test_lead['created_at'], test_lead['updated_at']
            ))
            
            insert_time = time.time() - start_time
            self.assert_true(insert_time < 0.1, f"Lead insertion fast ({insert_time:.3f}s)")
            
            # Get the inserted lead ID (since ID is TEXT, we need to use the UUID)
            lead_id = test_lead['uuid']
            
            # Test retrieving the lead
            start_time = time.time()
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            retrieved_lead = cursor.fetchone()
            retrieve_time = time.time() - start_time
            
            self.assert_true(retrieve_time < 0.1, f"Lead retrieval fast ({retrieve_time:.3f}s)")
            self.assert_true(retrieved_lead is not None, "Can retrieve inserted lead")
            
            # Clean up test lead
            cursor.execute("DELETE FROM leads WHERE uuid = ?", (test_lead['uuid'],))
            conn.commit()
            
            conn.close()
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Lead operations test failed: {e}")
            print(f"❌ ERROR: Lead operations test failed: {e}")
    
    def test_data_integrity(self):
        """Test data integrity checks."""
        print("\n🔍 TEST 3: Data Integrity")
        print("-" * 30)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for duplicate emails
            cursor.execute("SELECT email, COUNT(*) FROM leads WHERE email != '' GROUP BY email HAVING COUNT(*) > 1")
            duplicates = cursor.fetchall()
            self.assert_true(len(duplicates) == 0, f"No duplicate emails found ({len(duplicates)} duplicates)")
            
            # Check for invalid records
            cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name = '' OR company = ''")
            invalid_records = cursor.fetchone()[0]
            self.assert_true(invalid_records == 0, f"No invalid records found ({invalid_records} invalid)")
            
            # Check total leads
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            self.assert_greater_than(total_leads, 0, f"Database has {total_leads} leads")
            
            conn.close()
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Data integrity test failed: {e}")
            print(f"❌ ERROR: Data integrity test failed: {e}")
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Simple Database Tests...")
        print()
        
        self.test_database_connection()
        self.test_lead_operations()
        self.test_data_integrity()
        
        # Print results
        print("\n" + "=" * 40)
        print("📊 SIMPLE DATABASE TEST RESULTS")
        print("=" * 40)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n🚨 Errors Found:")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            print("   🟢 EXCELLENT: Database is working perfectly")
        elif success_rate >= 80:
            print("   🟡 GOOD: Database is mostly working")
        elif success_rate >= 70:
            print("   🟠 FAIR: Database has some issues")
        else:
            print("   🔴 POOR: Database has critical issues")
        
        return success_rate >= 80


def main():
    """Main function."""
    print("🧪 Simple Database Test Suite")
    print("=" * 40)
    
    try:
        test_suite = SimpleDatabaseTest()
        success = test_suite.run_all_tests()
        
        if success:
            print("\n🎉 DATABASE TEST COMPLETED: Database is working!")
            return True
        else:
            print("\n⚠️  DATABASE TEST COMPLETED: Database has issues!")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: Database test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
