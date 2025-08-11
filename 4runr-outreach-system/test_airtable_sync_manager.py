"""
Unit tests for the Airtable Sync Manager.

Tests cover sync operations, field mapping, error handling, retry logic,
and bidirectional synchronization.
"""

import os
import tempfile
import unittest
import datetime
from unittest.mock import patch, MagicMock, Mock

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from airtable_sync_manager import (
    AirtableSyncManager, 
    SyncOperation, 
    SyncStatus, 
    SyncResult, 
    SyncSummary
)


class TestAirtableSyncManager(unittest.TestCase):
    """Test cases for AirtableSyncManager class."""
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the AirtableClient to avoid actual API calls
        with patch('airtable_sync_manager.AirtableClient') as mock_airtable_class:
            self.mock_airtable = MagicMock()
            mock_airtable_class.return_value = self.mock_airtable
            
            # Initialize sync manager with temporary database
            self.sync_manager = AirtableSyncManager(self.temp_db.name)
        
        # Sample lead data for testing
        self.sample_db_lead = {
            'id': 'test-lead-1',
            'uuid': 'uuid-123',
            'full_name': 'John Doe',
            'email': 'john.doe@example.com',
            'company': 'Test Corp',
            'title': 'Software Engineer',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'location': 'San Francisco, CA',
            'industry': 'Technology',
            'verified': True,
            'enriched': False,
            'status': 'new',
            'airtable_id': None,
            'sync_pending': True,
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }
        
        self.sample_airtable_lead = {
            'id': 'airtable-123',
            'Full Name': 'Jane Smith',
            'Email': 'jane.smith@example.com',
            'Company': 'Airtable Corp',
            'Job Title': 'Product Manager',
            'LinkedIn': 'https://linkedin.com/in/janesmith',
            'Location': 'New York, NY',
            'Industry': 'Software',
            'Verified': 'Yes',
            'Enriched': 'No',
            'Status': 'contacted'
        }
    
    def tearDown(self):
        """Clean up after each test."""
        try:
            os.unlink(self.temp_db.name)
        except (OSError, FileNotFoundError):
            pass
    
    def test_initialization(self):
        """Test that sync manager initializes correctly."""
        self.assertIsNotNone(self.sync_manager.db)
        self.assertIsNotNone(self.sync_manager.airtable)
        self.assertEqual(self.sync_manager.max_retries, 3)
        self.assertEqual(self.sync_manager.batch_size, 10)
    
    def test_map_db_to_airtable_fields(self):
        """Test mapping database fields to Airtable fields."""
        mapped_fields = self.sync_manager._map_db_to_airtable_fields(self.sample_db_lead)
        
        # Check standard field mappings
        self.assertEqual(mapped_fields['Full Name'], 'John Doe')
        self.assertEqual(mapped_fields['Email'], 'john.doe@example.com')
        self.assertEqual(mapped_fields['Company'], 'Test Corp')
        self.assertEqual(mapped_fields['Job Title'], 'Software Engineer')
        self.assertEqual(mapped_fields['LinkedIn'], 'https://linkedin.com/in/johndoe')
        
        # Check boolean field conversion
        self.assertEqual(mapped_fields['Verified'], 'Yes')
        self.assertEqual(mapped_fields['Enriched'], 'No')
        
        # Check that sync timestamp is added
        self.assertIn('Last Sync', mapped_fields)
    
    def test_map_airtable_to_db_fields(self):
        """Test mapping Airtable fields to database fields."""
        mapped_fields = self.sync_manager._map_airtable_to_db_fields(self.sample_airtable_lead)
        
        # Check standard field mappings
        self.assertEqual(mapped_fields['full_name'], 'Jane Smith')
        self.assertEqual(mapped_fields['email'], 'jane.smith@example.com')
        self.assertEqual(mapped_fields['company'], 'Airtable Corp')
        self.assertEqual(mapped_fields['title'], 'Product Manager')
        self.assertEqual(mapped_fields['linkedin_url'], 'https://linkedin.com/in/janesmith')
        
        # Check boolean field conversion
        self.assertTrue(mapped_fields['verified'])
        self.assertFalse(mapped_fields['enriched'])
        
        # Check sync status fields
        self.assertTrue(mapped_fields['airtable_synced'])
        self.assertFalse(mapped_fields['sync_pending'])
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_sync_to_airtable_create_success(self, mock_db_class):
        """Test successful creation of lead in Airtable."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [self.sample_db_lead]
        
        # Mock Airtable client
        self.mock_airtable.create_lead.return_value = 'airtable-new-123'
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_to_airtable()
        
        # Verify results
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 1)
        self.assertEqual(summary.created_records, 1)
        self.assertEqual(summary.failed_syncs, 0)
        
        # Verify Airtable create was called
        self.mock_airtable.create_lead.assert_called_once()
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_sync_to_airtable_update_success(self, mock_db_class):
        """Test successful update of lead in Airtable."""
        # Mock database with lead that has airtable_id
        lead_with_airtable_id = self.sample_db_lead.copy()
        lead_with_airtable_id['airtable_id'] = 'existing-airtable-123'
        
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [lead_with_airtable_id]
        
        # Mock Airtable client
        self.mock_airtable.batch_update_leads.return_value = 1  # 1 successful update
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_to_airtable()
        
        # Verify results
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 1)
        self.assertEqual(summary.updated_records, 1)
        self.assertEqual(summary.failed_syncs, 0)
        
        # Verify Airtable batch update was called
        self.mock_airtable.batch_update_leads.assert_called_once()
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_sync_to_airtable_create_failure(self, mock_db_class):
        """Test handling of Airtable creation failure."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [self.sample_db_lead]
        
        # Mock Airtable client to fail
        self.mock_airtable.create_lead.return_value = None  # Creation failed
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_to_airtable()
        
        # Verify results
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 0)
        self.assertEqual(summary.failed_syncs, 1)
        self.assertGreater(len(summary.errors), 0)
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_sync_from_airtable_create_success(self, mock_db_class):
        """Test successful creation of lead from Airtable."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.search_leads.return_value = []  # No existing lead
        mock_db.add_lead.return_value = 'new-db-lead-123'
        
        # Mock Airtable client
        self.mock_airtable.get_leads_for_engagement.return_value = [self.sample_airtable_lead]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_from_airtable()
        
        # Verify results
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 1)
        self.assertEqual(summary.created_records, 1)
        self.assertEqual(summary.failed_syncs, 0)
        
        # Verify database add was called
        mock_db.add_lead.assert_called_once()
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_sync_from_airtable_update_success(self, mock_db_class):
        """Test successful update of lead from Airtable."""
        # Mock database with existing lead
        existing_lead = {
            'id': 'existing-db-123',
            'airtable_id': 'airtable-123',
            'updated_at': datetime.datetime.now() - datetime.timedelta(hours=1)
        }
        
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.search_leads.return_value = [existing_lead]
        mock_db.update_lead.return_value = True
        
        # Mock Airtable client
        self.mock_airtable.get_leads_for_engagement.return_value = [self.sample_airtable_lead]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_from_airtable()
        
        # Verify results
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 1)
        self.assertEqual(summary.updated_records, 1)
        self.assertEqual(summary.failed_syncs, 0)
        
        # Verify database update was called
        mock_db.update_lead.assert_called_once()
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_bidirectional_sync(self, mock_db_class):
        """Test bidirectional sync operation."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [self.sample_db_lead]
        mock_db.search_leads.return_value = []
        mock_db.add_lead.return_value = 'new-lead-123'
        
        # Mock Airtable client
        self.mock_airtable.create_lead.return_value = 'airtable-new-123'
        self.mock_airtable.get_leads_for_engagement.return_value = [self.sample_airtable_lead]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform bidirectional sync
        results = sync_manager.bidirectional_sync()
        
        # Verify results structure
        self.assertIn('push', results)
        self.assertIn('pull', results)
        
        # Verify push results
        push_summary = results['push']
        self.assertEqual(push_summary.total_leads, 1)
        self.assertEqual(push_summary.successful_syncs, 1)
        
        # Verify pull results
        pull_summary = results['pull']
        self.assertEqual(pull_summary.total_leads, 1)
        self.assertEqual(pull_summary.successful_syncs, 1)
    
    def test_should_update_from_airtable(self):
        """Test logic for determining if update from Airtable is needed."""
        # Test with no updated_at timestamp
        db_lead_no_timestamp = {'id': 'test'}
        result = self.sync_manager._should_update_from_airtable(db_lead_no_timestamp, self.sample_airtable_lead)
        self.assertTrue(result)
        
        # Test with old timestamp
        old_timestamp = datetime.datetime.now() - datetime.timedelta(hours=2)
        db_lead_old = {'id': 'test', 'updated_at': old_timestamp}
        result = self.sync_manager._should_update_from_airtable(db_lead_old, self.sample_airtable_lead)
        self.assertTrue(result)  # Currently always returns True for consistency
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_get_sync_statistics(self, mock_db_class):
        """Test getting sync statistics."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_database_stats.return_value = {'total_leads': 100}
        mock_db.get_sync_pending_leads.return_value = [{'id': '1'}, {'id': '2'}]
        mock_db.search_leads.return_value = [{'id': '3'}, {'id': '4'}, {'id': '5'}]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.db = mock_db
        
        # Get statistics
        stats = sync_manager.get_sync_statistics()
        
        # Verify statistics
        self.assertEqual(stats['database_stats']['total_leads'], 100)
        self.assertEqual(stats['sync_pending_count'], 2)
        self.assertEqual(stats['synced_leads_count'], 3)
        self.assertEqual(stats['sync_rate'], 0.03)  # 3/100
        self.assertIn('last_check', stats)
    
    def test_sync_result_dataclass(self):
        """Test SyncResult dataclass functionality."""
        result = SyncResult(
            operation=SyncOperation.CREATE,
            lead_id='test-123',
            airtable_id='airtable-456'
        )
        
        self.assertEqual(result.operation, SyncOperation.CREATE)
        self.assertEqual(result.lead_id, 'test-123')
        self.assertEqual(result.airtable_id, 'airtable-456')
        self.assertEqual(result.status, SyncStatus.PENDING)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.attempt_count, 0)
    
    def test_sync_summary_dataclass(self):
        """Test SyncSummary dataclass functionality."""
        summary = SyncSummary()
        
        # Test default initialization
        self.assertEqual(summary.total_leads, 0)
        self.assertEqual(summary.successful_syncs, 0)
        self.assertEqual(summary.failed_syncs, 0)
        self.assertEqual(summary.errors, [])
        self.assertEqual(summary.sync_results, [])
        
        # Test with parameters
        summary = SyncSummary(
            total_leads=10,
            successful_syncs=8,
            failed_syncs=2
        )
        self.assertEqual(summary.total_leads, 10)
        self.assertEqual(summary.successful_syncs, 8)
        self.assertEqual(summary.failed_syncs, 2)
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_retry_logic_on_failure(self, mock_db_class):
        """Test retry logic when Airtable operations fail."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [self.sample_db_lead]
        
        # Mock Airtable client to fail first two times, succeed on third
        self.mock_airtable.create_lead.side_effect = [
            Exception("Network error"),
            Exception("Rate limit"),
            'airtable-success-123'
        ]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_to_airtable()
        
        # Verify that retry logic worked
        self.assertEqual(summary.total_leads, 1)
        self.assertEqual(summary.successful_syncs, 1)
        self.assertEqual(self.mock_airtable.create_lead.call_count, 3)
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_batch_processing(self, mock_db_class):
        """Test that large numbers of leads are processed in batches."""
        # Create 25 leads (more than batch size of 10)
        leads = []
        for i in range(25):
            lead = self.sample_db_lead.copy()
            lead['id'] = f'lead-{i}'
            lead['full_name'] = f'Test User {i}'
            leads.append(lead)
        
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = leads
        
        # Mock Airtable client
        self.mock_airtable.create_lead.return_value = 'airtable-123'
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.airtable = self.mock_airtable
        sync_manager.db = mock_db
        
        # Perform sync
        summary = sync_manager.sync_to_airtable()
        
        # Verify all leads were processed
        self.assertEqual(summary.total_leads, 25)
        self.assertEqual(summary.successful_syncs, 25)
        
        # Verify create_lead was called for each lead
        self.assertEqual(self.mock_airtable.create_lead.call_count, 25)
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_mark_for_sync(self, mock_db_class):
        """Test marking a lead for sync."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.mark_for_sync.return_value = True
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.db = mock_db
        
        # Mark lead for sync
        result = sync_manager.mark_for_sync('test-lead-123')
        
        # Verify result and database call
        self.assertTrue(result)
        mock_db.mark_for_sync.assert_called_once_with('test-lead-123')
    
    @patch('airtable_sync_manager.LeadDatabase')
    def test_get_sync_pending_leads(self, mock_db_class):
        """Test getting sync pending leads."""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_sync_pending_leads.return_value = [self.sample_db_lead]
        
        # Reinitialize sync manager with mocked database
        sync_manager = AirtableSyncManager(self.temp_db.name)
        sync_manager.db = mock_db
        
        # Get pending leads
        pending_leads = sync_manager.get_sync_pending_leads()
        
        # Verify result
        self.assertEqual(len(pending_leads), 1)
        self.assertEqual(pending_leads[0]['id'], 'test-lead-1')
        mock_db.get_sync_pending_leads.assert_called_once()


if __name__ == '__main__':
    unittest.main()