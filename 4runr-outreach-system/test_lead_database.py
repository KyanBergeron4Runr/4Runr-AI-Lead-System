"""
Unit tests for the Lead Database API.

Tests cover all core functionality including CRUD operations, duplicate detection,
thread safety, and error handling.
"""

import os
import sqlite3
import tempfile
import unittest
import json
import datetime
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lead_database import LeadDatabase, Lead


class TestLeadDatabase(unittest.TestCase):
    """Test cases for LeadDatabase class."""
    
    def setUp(self):
        """Set up test database for each test."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database with temporary file
        self.db = LeadDatabase(self.temp_db.name)
        
        # Sample lead data for testing
        self.sample_lead = {
            'full_name': 'John Doe',
            'email': 'john.doe@example.com',
            'company': 'Example Corp',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'title': 'Software Engineer',
            'location': 'San Francisco, CA',
            'industry': 'Technology',
            'company_size': '100-500',
            'source': 'test'
        }
    
    def tearDown(self):
        """Clean up after each test."""
        # Close database connections
        if hasattr(self.db, 'db_manager'):
            del self.db
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db.name)
        except (OSError, FileNotFoundError):
            pass
    
    def test_database_initialization(self):
        """Test that database initializes correctly with extended schema."""
        # Test that database file was created
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Test that extended schema exists
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check that leads table exists with extended columns
            cursor.execute("PRAGMA table_info(leads)")
            columns = {row[1] for row in cursor.fetchall()}
            
            expected_columns = {
                'id', 'uuid', 'name', 'full_name', 'email', 'company',
                'linkedin_url', 'title', 'location', 'industry', 'company_size',
                'verified', 'enriched', 'needs_enrichment', 'status', 'source',
                'scraped_at', 'enriched_at', 'airtable_id', 'airtable_synced',
                'sync_pending', 'raw_data', 'created_at', 'updated_at'
            }
            
            # Check that all expected columns exist
            for col in expected_columns:
                self.assertIn(col, columns, f"Column {col} missing from leads table")
    
    def test_add_lead_success(self):
        """Test successful lead addition."""
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Verify lead was added
        self.assertIsNotNone(lead_id)
        self.assertIsInstance(lead_id, str)
        
        # Verify lead can be retrieved
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead)
        self.assertEqual(retrieved_lead['full_name'], self.sample_lead['full_name'])
        self.assertEqual(retrieved_lead['email'], self.sample_lead['email'])
        self.assertEqual(retrieved_lead['company'], self.sample_lead['company'])
    
    def test_add_lead_with_missing_name(self):
        """Test that adding lead without name raises ValueError."""
        invalid_lead = {
            'email': 'test@example.com',
            'company': 'Test Corp'
        }
        
        with self.assertRaises(ValueError):
            self.db.add_lead(invalid_lead)
    
    def test_get_lead_by_id_and_uuid(self):
        """Test retrieving lead by both ID and UUID."""
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Get the lead to find its UUID
        lead = self.db.get_lead(lead_id)
        lead_uuid = lead['uuid']
        
        # Test retrieval by ID
        lead_by_id = self.db.get_lead(lead_id)
        self.assertIsNotNone(lead_by_id)
        self.assertEqual(lead_by_id['id'], lead_id)
        
        # Test retrieval by UUID
        lead_by_uuid = self.db.get_lead(lead_uuid)
        self.assertIsNotNone(lead_by_uuid)
        self.assertEqual(lead_by_uuid['uuid'], lead_uuid)
        
        # Both should return the same lead
        self.assertEqual(lead_by_id['id'], lead_by_uuid['id'])
    
    def test_get_nonexistent_lead(self):
        """Test retrieving non-existent lead returns None."""
        result = self.db.get_lead('nonexistent-id')
        self.assertIsNone(result)
    
    def test_update_lead_success(self):
        """Test successful lead update."""
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Update lead data
        updates = {
            'title': 'Senior Software Engineer',
            'verified': True,
            'enriched': True
        }
        
        result = self.db.update_lead(lead_id, updates)
        self.assertTrue(result)
        
        # Verify updates were applied
        updated_lead = self.db.get_lead(lead_id)
        self.assertEqual(updated_lead['title'], 'Senior Software Engineer')
        self.assertTrue(updated_lead['verified'])
        self.assertTrue(updated_lead['enriched'])
    
    def test_update_nonexistent_lead(self):
        """Test updating non-existent lead returns False."""
        result = self.db.update_lead('nonexistent-id', {'title': 'Test'})
        self.assertFalse(result)
    
    def test_search_leads_by_company(self):
        """Test searching leads by company name."""
        # Add multiple leads
        lead1_data = self.sample_lead.copy()
        lead1_data['company'] = 'Tech Corp'
        # Remove linkedin_url to avoid duplicate detection
        if 'linkedin_url' in lead1_data:
            del lead1_data['linkedin_url']
        lead1_id = self.db.add_lead(lead1_data)
        
        lead2_data = self.sample_lead.copy()
        lead2_data['full_name'] = 'Jane Smith'
        lead2_data['email'] = 'jane@example.com'
        lead2_data['company'] = 'Another Corp'
        # Remove linkedin_url to avoid duplicate detection
        if 'linkedin_url' in lead2_data:
            del lead2_data['linkedin_url']
        lead2_id = self.db.add_lead(lead2_data)
        
        # Search by company
        results = self.db.search_leads({'company': 'Tech'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], lead1_id)
        
        # Search for non-existent company
        results = self.db.search_leads({'company': 'NonExistent'})
        self.assertEqual(len(results), 0)
    
    def test_search_leads_with_multiple_filters(self):
        """Test searching leads with multiple filter criteria."""
        # Add lead with specific attributes
        lead_data = self.sample_lead.copy()
        lead_data['status'] = 'contacted'
        lead_data['verified'] = True
        lead_id = self.db.add_lead(lead_data)
        
        # Search with multiple filters
        results = self.db.search_leads({
            'company': 'Example',
            'status': 'contacted',
            'verified': True
        })
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], lead_id)
        
        # Search with non-matching filters
        results = self.db.search_leads({
            'company': 'Example',
            'status': 'contacted',
            'verified': False
        })
        
        self.assertEqual(len(results), 0)
    
    def test_search_leads_with_pagination(self):
        """Test lead search with pagination."""
        # Add multiple leads
        for i in range(5):
            lead_data = self.sample_lead.copy()
            lead_data['full_name'] = f'Test User {i}'
            lead_data['email'] = f'test{i}@example.com'
            # Remove linkedin_url to avoid duplicate detection
            if 'linkedin_url' in lead_data:
                del lead_data['linkedin_url']
            self.db.add_lead(lead_data)
        
        # Test pagination
        results_page1 = self.db.search_leads({'limit': 2, 'offset': 0})
        results_page2 = self.db.search_leads({'limit': 2, 'offset': 2})
        
        self.assertEqual(len(results_page1), 2)
        self.assertEqual(len(results_page2), 2)
        
        # Ensure different results
        page1_ids = {lead['id'] for lead in results_page1}
        page2_ids = {lead['id'] for lead in results_page2}
        self.assertEqual(len(page1_ids.intersection(page2_ids)), 0)
    
    def test_get_all_leads(self):
        """Test retrieving all leads."""
        # Add multiple leads
        lead_ids = []
        for i in range(3):
            lead_data = self.sample_lead.copy()
            lead_data['full_name'] = f'Test User {i}'
            lead_data['email'] = f'test{i}@example.com'
            # Remove linkedin_url to avoid duplicate detection
            if 'linkedin_url' in lead_data:
                del lead_data['linkedin_url']
            lead_id = self.db.add_lead(lead_data)
            lead_ids.append(lead_id)
        
        # Get all leads
        all_leads = self.db.get_all_leads()
        self.assertEqual(len(all_leads), 3)
        
        # Verify all added leads are present
        retrieved_ids = {lead['id'] for lead in all_leads}
        for lead_id in lead_ids:
            self.assertIn(lead_id, retrieved_ids)
    
    def test_mark_for_sync(self):
        """Test marking lead for synchronization."""
        lead_id = self.db.add_lead(self.sample_lead)
        
        # Initially should be marked for sync
        lead = self.db.get_lead(lead_id)
        self.assertTrue(lead['sync_pending'])
        
        # Update to not sync pending
        self.db.update_lead(lead_id, {'sync_pending': False})
        
        # Mark for sync again
        result = self.db.mark_for_sync(lead_id)
        self.assertTrue(result)
        
        # Verify it's marked for sync
        updated_lead = self.db.get_lead(lead_id)
        self.assertTrue(updated_lead['sync_pending'])
    
    def test_get_sync_pending_leads(self):
        """Test retrieving leads pending synchronization."""
        # Add leads with different sync status
        lead1_data = self.sample_lead.copy()
        lead1_data['sync_pending'] = True
        # Remove linkedin_url to avoid duplicate detection
        if 'linkedin_url' in lead1_data:
            del lead1_data['linkedin_url']
        lead1_id = self.db.add_lead(lead1_data)
        
        lead2_data = self.sample_lead.copy()
        lead2_data['full_name'] = 'Jane Smith'
        lead2_data['email'] = 'jane@example.com'
        # Remove linkedin_url to avoid duplicate detection
        if 'linkedin_url' in lead2_data:
            del lead2_data['linkedin_url']
        lead2_id = self.db.add_lead(lead2_data)
        self.db.update_lead(lead2_id, {'sync_pending': False})
        
        # Get sync pending leads
        pending_leads = self.db.get_sync_pending_leads()
        
        # Should only return lead1
        self.assertEqual(len(pending_leads), 1)
        self.assertEqual(pending_leads[0]['id'], lead1_id)
    
    def test_duplicate_detection_by_linkedin_url(self):
        """Test duplicate detection using LinkedIn URL."""
        # Add initial lead
        lead1_id = self.db.add_lead(self.sample_lead)
        
        # Try to add duplicate with same LinkedIn URL
        duplicate_lead = self.sample_lead.copy()
        duplicate_lead['full_name'] = 'Different Name'
        duplicate_lead['email'] = 'different@example.com'
        
        lead2_id = self.db.add_lead(duplicate_lead)
        
        # Should return the same ID (existing lead updated)
        self.assertEqual(lead1_id, lead2_id)
        
        # Verify only one lead exists
        all_leads = self.db.get_all_leads()
        self.assertEqual(len(all_leads), 1)
    
    def test_duplicate_detection_by_email(self):
        """Test duplicate detection using email address."""
        # Add initial lead without LinkedIn URL
        lead_data = self.sample_lead.copy()
        del lead_data['linkedin_url']
        lead1_id = self.db.add_lead(lead_data)
        
        # Try to add duplicate with same email
        duplicate_lead = lead_data.copy()
        duplicate_lead['full_name'] = 'Different Name'
        duplicate_lead['company'] = 'Different Corp'
        
        lead2_id = self.db.add_lead(duplicate_lead)
        
        # Should return the same ID
        self.assertEqual(lead1_id, lead2_id)
        
        # Verify only one lead exists
        all_leads = self.db.get_all_leads()
        self.assertEqual(len(all_leads), 1)
    
    def test_duplicate_detection_by_name_and_company(self):
        """Test duplicate detection using name and company."""
        # Add initial lead without LinkedIn URL or email
        lead_data = {
            'full_name': 'John Doe',
            'company': 'Example Corp',
            'title': 'Engineer'
        }
        lead1_id = self.db.add_lead(lead_data)
        
        # Try to add duplicate with same name and company
        duplicate_lead = lead_data.copy()
        duplicate_lead['title'] = 'Senior Engineer'
        
        lead2_id = self.db.add_lead(duplicate_lead)
        
        # Should return the same ID
        self.assertEqual(lead1_id, lead2_id)
        
        # Verify data was merged (title should be updated)
        updated_lead = self.db.get_lead(lead1_id)
        self.assertEqual(updated_lead['title'], 'Senior Engineer')
    
    def test_data_merging(self):
        """Test intelligent data merging for duplicates."""
        # Add initial lead with partial data
        initial_lead = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Example Corp'
        }
        lead_id = self.db.add_lead(initial_lead)
        
        # Add duplicate with additional data
        enhanced_lead = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Example Corp',
            'title': 'Software Engineer',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'verified': True
        }
        
        duplicate_id = self.db.add_lead(enhanced_lead)
        self.assertEqual(lead_id, duplicate_id)
        
        # Verify data was merged
        merged_lead = self.db.get_lead(lead_id)
        self.assertEqual(merged_lead['title'], 'Software Engineer')
        self.assertEqual(merged_lead['linkedin_url'], 'https://linkedin.com/in/johndoe')
        self.assertTrue(merged_lead['verified'])
    
    def test_raw_data_handling(self):
        """Test handling of raw_data JSON field."""
        lead_data = self.sample_lead.copy()
        lead_data['raw_data'] = {
            'custom_field': 'custom_value',
            'nested_data': {'key': 'value'}
        }
        
        lead_id = self.db.add_lead(lead_data)
        
        # Retrieve and verify raw_data
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead['raw_data'])
        self.assertEqual(retrieved_lead['raw_data']['custom_field'], 'custom_value')
        self.assertEqual(retrieved_lead['raw_data']['nested_data']['key'], 'value')
    
    def test_datetime_parsing(self):
        """Test datetime field parsing."""
        lead_data = self.sample_lead.copy()
        now = datetime.datetime.now()
        lead_data['scraped_at'] = now.isoformat()
        
        lead_id = self.db.add_lead(lead_data)
        
        # Retrieve and verify datetime parsing
        retrieved_lead = self.db.get_lead(lead_id)
        self.assertIsInstance(retrieved_lead['scraped_at'], datetime.datetime)
        self.assertEqual(retrieved_lead['scraped_at'].date(), now.date())
    
    def test_database_stats(self):
        """Test database statistics generation."""
        # Add leads with different statuses
        for i, status in enumerate(['new', 'contacted', 'responded']):
            lead_data = self.sample_lead.copy()
            lead_data['full_name'] = f'Test User {i}'
            lead_data['email'] = f'test{i}@example.com'
            lead_data['status'] = status
            lead_data['verified'] = i % 2 == 0  # Alternate verified status
            # Remove linkedin_url to avoid duplicate detection
            if 'linkedin_url' in lead_data:
                del lead_data['linkedin_url']
            self.db.add_lead(lead_data)
        
        stats = self.db.get_database_stats()
        
        # Verify stats structure
        self.assertIn('total_leads', stats)
        self.assertIn('by_status', stats)
        self.assertIn('verification', stats)
        self.assertIn('recent_additions', stats)
        
        # Verify counts
        self.assertEqual(stats['total_leads'], 3)
        self.assertEqual(stats['by_status']['new'], 1)
        self.assertEqual(stats['by_status']['contacted'], 1)
        self.assertEqual(stats['by_status']['responded'], 1)
        self.assertEqual(stats['verification']['verified'], 2)  # Users 0 and 2
    
    def test_thread_safety(self):
        """Test thread-safe operations."""
        def add_leads(thread_id, num_leads):
            """Add leads from a specific thread."""
            for i in range(num_leads):
                lead_data = self.sample_lead.copy()
                lead_data['full_name'] = f'Thread {thread_id} User {i}'
                lead_data['email'] = f'thread{thread_id}user{i}@example.com'
                # Make each lead unique by removing linkedin_url to avoid duplicates
                if 'linkedin_url' in lead_data:
                    del lead_data['linkedin_url']
                try:
                    self.db.add_lead(lead_data)
                except Exception as e:
                    print(f"Thread {thread_id} error: {e}")
        
        # Create multiple threads
        threads = []
        num_threads = 5
        leads_per_thread = 10
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=add_leads,
                args=(thread_id, leads_per_thread)
            )
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all leads were added
        all_leads = self.db.get_all_leads()
        expected_total = num_threads * leads_per_thread
        self.assertEqual(len(all_leads), expected_total)
    
    def test_connection_test(self):
        """Test database connection testing."""
        result = self.db.test_connection()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()