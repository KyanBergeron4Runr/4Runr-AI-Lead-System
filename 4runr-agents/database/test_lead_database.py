#!/usr/bin/env python3
"""
Lead Database API Unit Tests

Comprehensive test suite for the Lead Database API functionality.
"""

import os
import sys
import uuid
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.lead_database import LeadDatabase, Lead, get_lead_database
from database.connection import get_database_connection

class TestLeadDatabase(unittest.TestCase):
    """Test cases for Lead Database API"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database with test file
        self.db = LeadDatabase(self.temp_db.name)
        
        # Ensure schema is initialized
        self.db.db_conn._initialize_database()
        
    def tearDown(self):
        """Clean up after each test"""
        # Close database connections
        if hasattr(self.db, 'db_conn'):
            self.db.db_conn.close_connections()
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def test_lead_dataclass(self):
        """Test Lead dataclass functionality"""
        # Test default values
        lead = Lead(full_name="Test Lead")
        
        self.assertIsNotNone(lead.id)
        self.assertIsNotNone(lead.uuid)
        self.assertEqual(lead.full_name, "Test Lead")
        self.assertFalse(lead.verified)
        self.assertFalse(lead.enriched)
        self.assertTrue(lead.needs_enrichment)
        self.assertEqual(lead.status, 'new')
        
        # Test to_dict conversion
        lead_dict = lead.to_dict()
        self.assertIsInstance(lead_dict, dict)
        self.assertEqual(lead_dict['full_name'], "Test Lead")
        self.assertIsInstance(lead_dict['created_at'], str)  # Should be ISO string
        
        # Test from_dict conversion
        lead2 = Lead.from_dict(lead_dict)
        self.assertEqual(lead2.full_name, lead.full_name)
        self.assertEqual(lead2.id, lead.id)
    
    def test_add_lead_basic(self):
        """Test basic lead addition"""
        lead_data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Example Corp',
            'title': 'CEO'
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        self.assertIsNotNone(lead_id)
        self.assertIsInstance(lead_id, str)
        
        # Verify lead was added
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead)
        self.assertEqual(retrieved_lead['full_name'], 'John Doe')
        self.assertEqual(retrieved_lead['email'], 'john@example.com')
    
    def test_add_lead_validation(self):
        """Test lead addition validation"""
        # Test missing required field
        with self.assertRaises(ValueError):
            self.db.add_lead({})
        
        with self.assertRaises(ValueError):
            self.db.add_lead({'email': 'test@example.com'})
    
    def test_duplicate_detection_linkedin(self):
        """Test duplicate detection by LinkedIn URL"""
        lead_data1 = {
            'full_name': 'John Doe',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'company': 'Company A'
        }
        
        lead_data2 = {
            'full_name': 'John D.',  # Different name
            'linkedin_url': 'https://linkedin.com/in/johndoe',  # Same LinkedIn
            'company': 'Company B'  # Different company
        }
        
        # Add first lead
        lead_id1 = self.db.add_lead(lead_data1)
        
        # Add second lead (should update first)
        lead_id2 = self.db.add_lead(lead_data2)
        
        # Should return same ID
        self.assertEqual(lead_id1, lead_id2)
        
        # Verify data was updated
        retrieved_lead = self.db.get_lead(lead_id1)
        self.assertEqual(retrieved_lead['full_name'], 'John D.')  # Updated
        self.assertEqual(retrieved_lead['company'], 'Company B')  # Updated
    
    def test_duplicate_detection_email(self):
        """Test duplicate detection by email"""
        lead_data1 = {
            'full_name': 'Jane Smith',
            'email': 'jane@example.com',
            'company': 'Company A'
        }
        
        lead_data2 = {
            'full_name': 'Jane S.',
            'email': 'jane@example.com',  # Same email
            'company': 'Company B'
        }
        
        # Add first lead
        lead_id1 = self.db.add_lead(lead_data1)
        
        # Add second lead (should update first)
        lead_id2 = self.db.add_lead(lead_data2)
        
        # Should return same ID
        self.assertEqual(lead_id1, lead_id2)
    
    def test_duplicate_detection_name_company(self):
        """Test duplicate detection by name and company"""
        lead_data1 = {
            'full_name': 'Bob Johnson',
            'company': 'Tech Corp'
        }
        
        lead_data2 = {
            'full_name': 'Bob Johnson',  # Same name
            'company': 'Tech Corp',     # Same company
            'email': 'bob@techcorp.com'  # Additional data
        }
        
        # Add first lead
        lead_id1 = self.db.add_lead(lead_data1)
        
        # Add second lead (should update first)
        lead_id2 = self.db.add_lead(lead_data2)
        
        # Should return same ID
        self.assertEqual(lead_id1, lead_id2)
        
        # Verify email was added
        retrieved_lead = self.db.get_lead(lead_id1)
        self.assertEqual(retrieved_lead['email'], 'bob@techcorp.com')
    
    def test_get_lead(self):
        """Test lead retrieval"""
        lead_data = {
            'full_name': 'Test Lead',
            'email': 'test@example.com',
            'raw_data': {'custom_field': 'custom_value'}
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        # Test successful retrieval
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead)
        self.assertEqual(retrieved_lead['full_name'], 'Test Lead')
        self.assertEqual(retrieved_lead['raw_data']['custom_field'], 'custom_value')
        
        # Test non-existent lead
        fake_id = str(uuid.uuid4())
        retrieved_lead = self.db.get_lead(fake_id)
        self.assertIsNone(retrieved_lead)
    
    def test_update_lead(self):
        """Test lead updates"""
        # Add initial lead
        lead_data = {
            'full_name': 'Original Name',
            'email': 'original@example.com'
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        # Update lead
        updates = {
            'full_name': 'Updated Name',
            'enriched': True,
            'enriched_at': datetime.now(),
            'raw_data': {'enrichment_source': 'test'}
        }
        
        success = self.db.update_lead(lead_id, updates)
        self.assertTrue(success)
        
        # Verify updates
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertEqual(retrieved_lead['full_name'], 'Updated Name')
        self.assertTrue(retrieved_lead['enriched'])
        self.assertIsNotNone(retrieved_lead['enriched_at'])
        self.assertEqual(retrieved_lead['raw_data']['enrichment_source'], 'test')
        
        # Test updating non-existent lead
        fake_id = str(uuid.uuid4())
        success = self.db.update_lead(fake_id, {'full_name': 'Test'})
        self.assertFalse(success)
    
    def test_search_leads(self):
        """Test lead search functionality"""
        # Add test leads
        leads_data = [
            {'full_name': 'Alice CEO', 'company': 'Tech Corp', 'title': 'CEO', 'verified': True},
            {'full_name': 'Bob CTO', 'company': 'Tech Corp', 'title': 'CTO', 'verified': False},
            {'full_name': 'Carol CFO', 'company': 'Finance Inc', 'title': 'CFO', 'verified': True},
        ]
        
        lead_ids = []
        for lead_data in leads_data:
            lead_id = self.db.add_lead(lead_data)
            lead_ids.append(lead_id)
        
        # Test search by company
        results = self.db.search_leads({'company': 'Tech Corp'})
        self.assertEqual(len(results), 2)
        
        # Test search by verified status
        results = self.db.search_leads({'verified': True})
        self.assertEqual(len(results), 2)
        
        # Test search by title
        results = self.db.search_leads({'title': 'CEO'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['full_name'], 'Alice CEO')
        
        # Test wildcard search
        results = self.db.search_leads({'full_name': '%CEO%'})
        self.assertEqual(len(results), 1)
        
        # Test multiple filters
        results = self.db.search_leads({'company': 'Tech Corp', 'verified': True})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['full_name'], 'Alice CEO')
    
    def test_get_all_leads(self):
        """Test getting all leads with pagination"""
        # Add multiple leads
        for i in range(5):
            lead_data = {
                'full_name': f'Lead {i}',
                'email': f'lead{i}@example.com'
            }
            self.db.add_lead(lead_data)
        
        # Test get all
        all_leads = self.db.get_all_leads()
        self.assertEqual(len(all_leads), 5)
        
        # Test pagination
        page1 = self.db.get_all_leads(limit=2, offset=0)
        self.assertEqual(len(page1), 2)
        
        page2 = self.db.get_all_leads(limit=2, offset=2)
        self.assertEqual(len(page2), 2)
        
        # Verify no overlap
        page1_ids = {lead['id'] for lead in page1}
        page2_ids = {lead['id'] for lead in page2}
        self.assertEqual(len(page1_ids.intersection(page2_ids)), 0)
    
    def test_sync_operations(self):
        """Test sync-related operations"""
        # Add lead
        lead_data = {'full_name': 'Sync Test Lead'}
        lead_id = self.db.add_lead(lead_data)
        
        # Test mark for sync
        success = self.db.mark_for_sync(lead_id)
        self.assertTrue(success)
        
        # Verify sync pending
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertTrue(retrieved_lead['sync_pending'])
        
        # Test get sync pending leads
        pending_leads = self.db.get_sync_pending_leads()
        self.assertEqual(len(pending_leads), 1)
        self.assertEqual(pending_leads[0]['id'], lead_id)
        
        # Test marking non-existent lead
        fake_id = str(uuid.uuid4())
        success = self.db.mark_for_sync(fake_id)
        self.assertFalse(success)
    
    def test_delete_lead(self):
        """Test lead deletion"""
        # Add lead
        lead_data = {'full_name': 'Delete Test Lead'}
        lead_id = self.db.add_lead(lead_data)
        
        # Verify lead exists
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead)
        
        # Delete lead
        success = self.db.delete_lead(lead_id)
        self.assertTrue(success)
        
        # Verify lead is gone
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNone(retrieved_lead)
        
        # Test deleting non-existent lead
        success = self.db.delete_lead(lead_id)
        self.assertFalse(success)
    
    def test_lead_count(self):
        """Test lead count functionality"""
        # Initial count should be 0
        count = self.db.get_lead_count()
        self.assertEqual(count, 0)
        
        # Add leads
        for i in range(3):
            lead_data = {'full_name': f'Count Test Lead {i}'}
            self.db.add_lead(lead_data)
        
        # Count should be 3
        count = self.db.get_lead_count()
        self.assertEqual(count, 3)
        
        # Delete one lead
        all_leads = self.db.get_all_leads()
        self.db.delete_lead(all_leads[0]['id'])
        
        # Count should be 2
        count = self.db.get_lead_count()
        self.assertEqual(count, 2)
    
    def test_database_stats(self):
        """Test database statistics"""
        # Add test data
        leads_data = [
            {'full_name': 'Lead 1', 'status': 'new', 'verified': True, 'enriched': False},
            {'full_name': 'Lead 2', 'status': 'contacted', 'verified': False, 'enriched': True},
            {'full_name': 'Lead 3', 'status': 'new', 'verified': True, 'enriched': True},
        ]
        
        for lead_data in leads_data:
            self.db.add_lead(lead_data)
        
        # Get stats
        stats = self.db.get_database_stats()
        
        # Verify basic counts
        self.assertEqual(stats['total_leads'], 3)
        self.assertEqual(stats['status_counts']['new'], 2)
        self.assertEqual(stats['status_counts']['contacted'], 1)
        self.assertEqual(stats['enriched_leads'], 2)
        self.assertEqual(stats['needs_enrichment'], 3)  # Default is True
        
        # Verify database info is included
        self.assertIn('database_path', stats)
        self.assertIn('database_size_mb', stats)
    
    def test_raw_data_handling(self):
        """Test raw_data JSON field handling"""
        # Test with complex raw_data
        raw_data = {
            'enrichment_source': 'linkedin_api',
            'confidence_score': 0.95,
            'additional_emails': ['alt@example.com'],
            'social_profiles': {
                'twitter': '@johndoe',
                'github': 'johndoe'
            }
        }
        
        lead_data = {
            'full_name': 'Raw Data Test',
            'raw_data': raw_data
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        # Retrieve and verify
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertEqual(retrieved_lead['raw_data'], raw_data)
        
        # Test update with raw_data
        updated_raw_data = raw_data.copy()
        updated_raw_data['updated'] = True
        
        self.db.update_lead(lead_id, {'raw_data': updated_raw_data})
        
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertTrue(retrieved_lead['raw_data']['updated'])
    
    def test_datetime_handling(self):
        """Test datetime field handling"""
        now = datetime.now()
        
        lead_data = {
            'full_name': 'DateTime Test',
            'scraped_at': now,
            'enriched_at': now - timedelta(hours=1)
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        # Retrieve and verify datetime fields
        retrieved_lead = self.db.get_lead(lead_id)
        
        # Dates should be stored as ISO strings in database
        self.assertIsInstance(retrieved_lead['scraped_at'], str)
        self.assertIsInstance(retrieved_lead['enriched_at'], str)
        
        # Convert back to Lead object to test datetime parsing
        lead_obj = Lead.from_dict(retrieved_lead)
        self.assertIsInstance(lead_obj.scraped_at, datetime)
        self.assertIsInstance(lead_obj.enriched_at, datetime)
    
    def test_singleton_pattern(self):
        """Test global database instance singleton"""
        # Get two instances
        db1 = get_lead_database(self.temp_db.name)
        db2 = get_lead_database(self.temp_db.name)
        
        # Should be the same instance
        self.assertIs(db1, db2)


class TestConcurrentAccess(unittest.TestCase):
    """Test concurrent database access"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = LeadDatabase(self.temp_db.name)
        
        # Ensure schema is initialized
        self.db.db_conn._initialize_database()
    
    def tearDown(self):
        """Clean up"""
        if hasattr(self.db, 'db_conn'):
            self.db.db_conn.close_connections()
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def test_concurrent_add_leads(self):
        """Test adding leads concurrently"""
        import threading
        
        results = []
        errors = []
        
        def add_lead_worker(worker_id):
            try:
                lead_data = {
                    'full_name': f'Concurrent Lead {worker_id}',
                    'email': f'concurrent{worker_id}@example.com'
                }
                lead_id = self.db.add_lead(lead_data)
                results.append(lead_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_lead_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        self.assertEqual(len(set(results)), 5)  # All IDs should be unique
        
        # Verify all leads were added
        total_count = self.db.get_lead_count()
        self.assertEqual(total_count, 5)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLeadDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrentAccess))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)