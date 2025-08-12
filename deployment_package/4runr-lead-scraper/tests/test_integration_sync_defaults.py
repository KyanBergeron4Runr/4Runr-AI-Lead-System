#!/usr/bin/env python3
"""
Integration tests for sync with engagement defaults

Tests the complete workflow:
- Scrape → sync → apply defaults
- Scenarios with partial engagement data
- Scenarios with complete engagement data  
- Performance tests for batch processing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.airtable_sync import AirtableSync
from sync.engagement_defaults import EngagementDefaultsManager
from database.models import Lead


class TestSyncWithDefaultsIntegration(unittest.TestCase):
    """Integration tests for sync operations with engagement defaults."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.airtable.api_key = 'test_api_key'
        self.mock_settings.airtable.base_id = 'test_base_id'
        self.mock_settings.airtable.table_name = 'test_table'
        self.mock_settings.engagement_defaults.enabled = True
        self.mock_settings.engagement_defaults.default_values = {
            'Engagement_Status': 'Auto-Send',
            'Email_Confidence_Level': 'Pattern',
            'Level Engaged': ''
        }
        
        # Mock database
        self.mock_db = Mock()
        
        # Patch dependencies
        self.settings_patcher = patch('sync.airtable_sync.get_settings')
        self.db_patcher = patch('sync.airtable_sync.get_lead_database')
        
        self.mock_get_settings = self.settings_patcher.start()
        self.mock_get_db = self.db_patcher.start()
        
        self.mock_get_settings.return_value = self.mock_settings
        self.mock_get_db.return_value = self.mock_db
        
        # Create AirtableSync instance
        self.airtable_sync = AirtableSync()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.settings_patcher.stop()
        self.db_patcher.stop()
    
    def _create_mock_lead(self, lead_id: str, name: str, email: str = None, airtable_id: str = None):
        """Create a mock Lead object."""
        lead = Mock(spec=Lead)
        lead.id = lead_id
        lead.name = name
        lead.email = email
        lead.linkedin_url = f"https://linkedin.com/in/{name.lower().replace(' ', '-')}"
        lead.enriched = True
        lead.scraped_at = datetime.now().isoformat()
        lead.airtable_id = airtable_id
        return lead
    
    @patch('sync.airtable_sync.requests.post')
    @patch('sync.airtable_sync.requests.get')
    @patch('sync.airtable_sync.requests.patch')
    def test_end_to_end_sync_with_defaults_new_leads(self, mock_patch, mock_get, mock_post):
        """Test complete workflow: new leads → sync → apply defaults."""
        # Setup: Create mock leads
        leads = [
            self._create_mock_lead('lead_1', 'John Doe', 'john@example.com'),
            self._create_mock_lead('lead_2', 'Jane Smith', 'jane@example.com'),
        ]
        
        # Mock Airtable sync response (successful creation)
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'records': [
                {'id': 'airtable_rec_1', 'fields': {}},
                {'id': 'airtable_rec_2', 'fields': {}}
            ]
        }
        
        # Mock database update success
        self.mock_db.update_lead.return_value = True
        
        # Mock getting current Airtable values (empty - new records)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'fields': {}  # Empty fields - all defaults needed
        }
        
        # Mock defaults application success
        mock_patch.return_value.status_code = 200
        
        # Execute: Sync leads with defaults
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        
        # Verify: Sync was successful
        self.assertTrue(result['success'])
        self.assertEqual(result['synced_count'], 2)
        self.assertEqual(result['failed_count'], 0)
        
        # Verify: Defaults were applied
        self.assertIn('defaults_applied', result)
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 2)  # Both leads got defaults
        self.assertIn('Engagement_Status', defaults['fields_updated'])
        self.assertIn('Email_Confidence_Level', defaults['fields_updated'])
        
        # Verify: Airtable API calls were made
        mock_post.assert_called_once()  # Sync call
        self.assertEqual(mock_get.call_count, 2)  # Get current values for each lead
        self.assertEqual(mock_patch.call_count, 2)  # Apply defaults for each lead
    
    @patch('sync.airtable_sync.requests.post')
    @patch('sync.airtable_sync.requests.get')
    @patch('sync.airtable_sync.requests.patch')
    def test_sync_with_partial_engagement_data(self, mock_patch, mock_get, mock_post):
        """Test sync with leads that have some engagement fields already set."""
        # Setup: Create mock lead
        leads = [self._create_mock_lead('lead_1', 'John Doe', 'john@example.com')]
        
        # Mock Airtable sync response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'records': [{'id': 'airtable_rec_1', 'fields': {}}]
        }
        
        self.mock_db.update_lead.return_value = True
        
        # Mock getting current values - some fields already set
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'fields': {
                'Engagement_Status': 'Manual Review',  # Already set
                'Email_Confidence_Level': '',  # Empty - needs default
                'Level Engaged': '1st degree'  # Already set
            }
        }
        
        mock_patch.return_value.status_code = 200
        
        # Execute
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        
        # Verify: Only missing field got default
        self.assertTrue(result['success'])
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 1)
        self.assertEqual(defaults['fields_updated'], ['Email_Confidence_Level'])
        
        # Verify: Only one patch call for the missing field
        mock_patch.assert_called_once()
        patch_call_data = mock_patch.call_args[1]['json']
        self.assertEqual(patch_call_data['fields'], {'Email_Confidence_Level': 'Pattern'})
    
    @patch('sync.airtable_sync.requests.post')
    @patch('sync.airtable_sync.requests.get')
    def test_sync_with_complete_engagement_data(self, mock_get, mock_post):
        """Test sync with leads that already have all engagement fields set."""
        # Setup
        leads = [self._create_mock_lead('lead_1', 'John Doe', 'john@example.com')]
        
        # Mock Airtable sync response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'records': [{'id': 'airtable_rec_1', 'fields': {}}]
        }
        
        self.mock_db.update_lead.return_value = True
        
        # Mock getting current values - all fields already set
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'fields': {
                'Engagement_Status': 'Manual Review',
                'Email_Confidence_Level': 'Real',
                'Level Engaged': '2nd degree'
            }
        }
        
        # Execute
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        
        # Verify: No defaults were applied
        self.assertTrue(result['success'])
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 0)
        self.assertEqual(defaults['fields_updated'], [])
        
        # Verify: No patch calls were made (no defaults needed)
        with patch('sync.airtable_sync.requests.patch') as mock_patch:
            # Re-run to verify no patch calls
            self.airtable_sync._apply_engagement_defaults_after_sync(leads)
            mock_patch.assert_not_called()
    
    @patch('sync.airtable_sync.requests.post')
    @patch('sync.airtable_sync.requests.get')
    @patch('sync.airtable_sync.requests.patch')
    def test_sync_with_defaults_api_errors(self, mock_patch, mock_get, mock_post):
        """Test handling of API errors during defaults application."""
        # Setup
        leads = [self._create_mock_lead('lead_1', 'John Doe', 'john@example.com')]
        
        # Mock successful sync
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'records': [{'id': 'airtable_rec_1', 'fields': {}}]
        }
        
        self.mock_db.update_lead.return_value = True
        
        # Mock getting current values success
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'fields': {}}
        
        # Mock defaults application failure
        mock_patch.return_value.status_code = 500
        mock_patch.return_value.text = 'Internal Server Error'
        
        # Execute
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        
        # Verify: Sync was successful but defaults failed
        self.assertTrue(result['success'])  # Main sync succeeded
        self.assertEqual(result['synced_count'], 1)
        
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 0)  # No defaults applied due to error
        self.assertTrue(len(defaults['errors']) > 0)  # Should have error messages
    
    @patch('sync.airtable_sync.requests.post')
    @patch('sync.airtable_sync.requests.get')
    @patch('sync.airtable_sync.requests.patch')
    def test_batch_processing_performance(self, mock_patch, mock_get, mock_post):
        """Test performance with batch processing of multiple leads."""
        # Setup: Create many mock leads
        leads = [
            self._create_mock_lead(f'lead_{i}', f'Person {i}', f'person{i}@example.com')
            for i in range(20)  # 20 leads for batch testing
        ]
        
        # Mock successful sync responses
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'records': [
                {'id': f'airtable_rec_{i}', 'fields': {}}
                for i in range(10)  # Airtable batch limit is 10
            ]
        }
        
        self.mock_db.update_lead.return_value = True
        
        # Mock getting current values (empty - all need defaults)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'fields': {}}
        
        # Mock successful defaults application
        mock_patch.return_value.status_code = 200
        
        # Execute
        import time
        start_time = time.time()
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        end_time = time.time()
        
        # Verify: All leads processed successfully
        self.assertTrue(result['success'])
        self.assertEqual(result['synced_count'], 20)
        
        # Verify: Defaults applied to all leads
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 20)
        
        # Verify: Performance is reasonable (should complete in reasonable time)
        processing_time = end_time - start_time
        self.assertLess(processing_time, 10.0)  # Should complete within 10 seconds
        
        # Verify: Correct number of API calls
        self.assertEqual(mock_post.call_count, 2)  # 2 batches (10 + 10)
        self.assertEqual(mock_get.call_count, 20)  # Get current values for each lead
        self.assertEqual(mock_patch.call_count, 20)  # Apply defaults for each lead
    
    @patch('sync.airtable_sync.requests.post')
    def test_sync_failure_no_defaults_applied(self, mock_post):
        """Test that defaults are not applied when sync fails."""
        # Setup
        leads = [self._create_mock_lead('lead_1', 'John Doe', 'john@example.com')]
        
        # Mock sync failure
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = 'Internal Server Error'
        
        # Execute
        result = self.airtable_sync.sync_leads_to_airtable(leads)
        
        # Verify: Sync failed and no defaults were applied
        self.assertFalse(result['success'])
        self.assertEqual(result['synced_count'], 0)
        
        defaults = result['defaults_applied']
        self.assertEqual(defaults['count'], 0)
        self.assertEqual(defaults['fields_updated'], [])
    
    def test_disabled_engagement_defaults(self):
        """Test behavior when engagement defaults are disabled."""
        # Setup: Disable engagement defaults
        self.mock_settings.engagement_defaults.enabled = False
        
        # Create new AirtableSync instance with disabled defaults
        airtable_sync = AirtableSync()
        
        # Verify: Engagement defaults manager is not initialized
        self.assertIsNone(airtable_sync.engagement_defaults_manager)
        
        # Setup mock lead
        leads = [self._create_mock_lead('lead_1', 'John Doe', 'john@example.com')]
        
        with patch('sync.airtable_sync.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'records': [{'id': 'airtable_rec_1', 'fields': {}}]
            }
            
            self.mock_db.update_lead.return_value = True
            
            # Execute
            result = airtable_sync.sync_leads_to_airtable(leads)
            
            # Verify: Sync succeeded but no defaults applied
            self.assertTrue(result['success'])
            defaults = result['defaults_applied']
            self.assertEqual(defaults['count'], 0)
            self.assertEqual(defaults['fields_updated'], [])


class TestSyncManagerIntegration(unittest.TestCase):
    """Integration tests for SyncManager with engagement defaults."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.airtable.api_key = 'test_api_key'
        self.mock_settings.airtable.base_id = 'test_base_id'
        self.mock_settings.airtable.table_name = 'test_table'
        self.mock_settings.airtable.sync_interval_minutes = 30
        self.mock_settings.airtable.auto_sync_enabled = True
        self.mock_settings.engagement_defaults.enabled = True
        self.mock_settings.engagement_defaults.default_values = {
            'Engagement_Status': 'Auto-Send',
            'Email_Confidence_Level': 'Pattern',
            'Level Engaged': ''
        }
        
        # Patch dependencies
        self.settings_patcher = patch('sync.sync_manager.get_settings')
        self.db_patcher = patch('sync.sync_manager.get_lead_database')
        
        self.mock_get_settings = self.settings_patcher.start()
        self.mock_get_db = self.db_patcher.start()
        
        self.mock_get_settings.return_value = self.mock_settings
        self.mock_get_db.return_value = Mock()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.settings_patcher.stop()
        self.db_patcher.stop()
    
    @patch('sync.sync_manager.AirtableSync')
    def test_sync_manager_includes_defaults_in_logging(self, mock_airtable_sync_class):
        """Test that SyncManager properly logs engagement defaults results."""
        from sync.sync_manager import SyncManager
        
        # Setup mock AirtableSync instance
        mock_airtable_sync = Mock()
        mock_airtable_sync.sync_leads_to_airtable.return_value = {
            'success': True,
            'synced_count': 3,
            'failed_count': 0,
            'errors': [],
            'defaults_applied': {
                'count': 2,
                'fields_updated': ['Engagement_Status', 'Email_Confidence_Level'],
                'errors': []
            }
        }
        mock_airtable_sync_class.return_value = mock_airtable_sync
        
        # Create SyncManager
        sync_manager = SyncManager()
        
        # Execute sync
        with patch('sync.sync_manager.logger') as mock_logger:
            result = sync_manager.sync_to_airtable()
            
            # Verify: Result includes defaults information
            self.assertTrue(result['success'])
            self.assertEqual(result['synced_count'], 3)
            self.assertIn('defaults_applied', result)
            
            # Verify: Logging includes defaults information
            mock_logger.info.assert_any_call("✅ Sync to Airtable completed: 3 leads synced")
            mock_logger.info.assert_any_call("🎯 Engagement defaults applied: 2 leads updated with fields ['Engagement_Status', 'Email_Confidence_Level']")
    
    @patch('sync.sync_manager.AirtableSync')
    def test_sync_manager_handles_defaults_errors(self, mock_airtable_sync_class):
        """Test SyncManager handling of defaults application errors."""
        from sync.sync_manager import SyncManager
        
        # Setup mock with defaults errors (no successful applications)
        mock_airtable_sync = Mock()
        mock_airtable_sync.sync_leads_to_airtable.return_value = {
            'success': True,
            'synced_count': 2,
            'failed_count': 0,
            'errors': [],
            'defaults_applied': {
                'count': 0,  # No successful defaults applied
                'fields_updated': [],
                'errors': ['Lead lead_2: API timeout']
            }
        }
        mock_airtable_sync_class.return_value = mock_airtable_sync
        
        sync_manager = SyncManager()
        
        # Execute sync
        with patch('sync.sync_manager.logger') as mock_logger:
            result = sync_manager.sync_to_airtable()
            
            # Verify: Sync still successful despite defaults errors
            self.assertTrue(result['success'])
            
            # Verify: Warning logged for defaults errors
            # Check if warning was called with the expected message
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'Engagement defaults had errors' in str(call)]
            self.assertTrue(len(warning_calls) > 0, "Expected warning about defaults errors was not logged")


class TestDailyScraperIntegration(unittest.TestCase):
    """Integration tests for DailyScraperAgent with engagement defaults."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock all dependencies to avoid real initialization
        self.patches = [
            patch('scripts.daily_scraper.get_settings'),
            patch('scripts.daily_scraper.get_lead_database'),
            patch('scripts.daily_scraper.get_sync_manager'),
            patch('scripts.daily_scraper.get_logger'),
            patch('scripts.daily_scraper.StructuredLogger'),
            patch('scripts.daily_scraper.PerformanceLogger'),
        ]
        
        for patcher in self.patches:
            patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        for patcher in self.patches:
            patcher.stop()
    
    @patch('scripts.daily_scraper.get_sync_manager')
    def test_daily_scraper_logs_defaults_results(self, mock_get_sync_manager):
        """Test that DailyScraperAgent properly logs engagement defaults results."""
        from scripts.daily_scraper import DailyScraperAgent
        
        # Setup mock sync manager
        mock_sync_manager = Mock()
        mock_sync_manager.sync_to_airtable.return_value = {
            'success': True,
            'synced_count': 5,
            'failed_count': 0,
            'errors': [],
            'defaults_applied': {
                'count': 3,
                'fields_updated': ['Engagement_Status', 'Email_Confidence_Level'],
                'errors': [],
                'skipped_count': 2,
                'failed_count': 0
            }
        }
        mock_get_sync_manager.return_value = mock_sync_manager
        
        # Create scraper in dry run mode to avoid complex setup
        scraper = DailyScraperAgent(dry_run=True)
        scraper.sync_manager = mock_sync_manager
        
        # Mock logger
        scraper.logger = Mock()
        scraper.struct_logger = Mock()
        
        # In dry run mode, we need to test differently since actual sync is skipped
        # Let's test the structure by calling the sync manager directly
        with patch.object(scraper, 'sync_manager', mock_sync_manager):
            # Mock the dry_run check to allow actual sync call
            scraper.dry_run = False
            
            # Mock other required methods
            scraper.perf_logger = Mock()
            scraper.perf_logger.start_timer = Mock()
            scraper.perf_logger.end_timer = Mock(return_value=1.0)
            scraper.struct_logger = Mock()
            scraper.stats = {'errors': 0, 'leads_synced': 0, 'operations': []}
            
            result = scraper._run_sync_phase()
            
            # Verify: Result includes defaults information
            self.assertEqual(result['defaults_applied'], 3)
            self.assertEqual(result['defaults_fields'], ['Engagement_Status', 'Email_Confidence_Level'])
            self.assertEqual(result['defaults_errors'], [])


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)