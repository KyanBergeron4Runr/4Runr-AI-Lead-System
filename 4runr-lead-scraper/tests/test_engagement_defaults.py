#!/usr/bin/env python3
"""
Unit tests for EngagementDefaultsManager

Tests cover:
- Default value determination logic
- Airtable API integration with mocked responses
- Error handling scenarios (API failures, invalid data)
- Configuration validation and environment variable handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.engagement_defaults import EngagementDefaultsManager, apply_defaults_to_lead, is_defaults_enabled
from config.settings import EngagementDefaultsConfig


class TestEngagementDefaultsManager(unittest.TestCase):
    """Test cases for EngagementDefaultsManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock settings to avoid loading real configuration
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
        
        # Patch get_settings to return our mock
        self.settings_patcher = patch('sync.engagement_defaults.get_settings')
        self.mock_get_settings = self.settings_patcher.start()
        self.mock_get_settings.return_value = self.mock_settings
        
        # Create manager instance
        self.manager = EngagementDefaultsManager()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.settings_patcher.stop()
    
    def test_initialization(self):
        """Test EngagementDefaultsManager initialization."""
        self.assertEqual(self.manager.api_key, 'test_api_key')
        self.assertEqual(self.manager.base_id, 'test_base_id')
        self.assertEqual(self.manager.table_name, 'test_table')
        self.assertEqual(self.manager.DEFAULT_VALUES['Engagement_Status'], 'Auto-Send')
        self.assertEqual(self.manager.DEFAULT_VALUES['Email_Confidence_Level'], 'Pattern')
        self.assertEqual(self.manager.DEFAULT_VALUES['Level Engaged'], '')
    
    def test_field_needs_default_logic(self):
        """Test the _field_needs_default method with various input scenarios."""
        # Test cases: (current_value, default_value, expected_result)
        test_cases = [
            # None values should get defaults
            (None, 'Auto-Send', True),
            
            # Empty strings should get defaults (except when default is also empty)
            ('', 'Auto-Send', True),
            ('', '', False),  # Empty default for empty value should not apply
            
            # Empty lists should get defaults
            ([], 'Auto-Send', True),
            ([''], 'Auto-Send', True),
            ([], '', False),  # Empty default for empty list should not apply
            ([''], '', False),  # Empty default for list with empty string should not apply
            
            # Existing values should not get defaults
            ('Existing Value', 'Auto-Send', False),
            (['Existing Value'], 'Auto-Send', False),
            
            # Whitespace-only strings should get defaults
            ('   ', 'Auto-Send', True),
            ('\t\n', 'Auto-Send', True),
        ]
        
        for current_value, default_value, expected in test_cases:
            with self.subTest(current=current_value, default=default_value):
                result = self.manager._field_needs_default(current_value, default_value)
                self.assertEqual(result, expected, 
                    f"Failed for current='{current_value}', default='{default_value}'. "
                    f"Expected {expected}, got {result}")
    
    def test_determine_needed_defaults(self):
        """Test the _determine_needed_defaults method."""
        # Test case 1: All fields need defaults
        current_values = {}
        needed = self.manager._determine_needed_defaults(current_values)
        expected = {
            'Engagement_Status': 'Auto-Send',
            'Email_Confidence_Level': 'Pattern'
            # Note: 'Level Engaged' with empty string default should not be included
        }
        self.assertEqual(needed, expected)
        
        # Test case 2: Some fields already have values
        current_values = {
            'Engagement_Status': 'Manual Review',
            'Email_Confidence_Level': '',  # Empty, should get default
            'Level Engaged': '1st degree'  # Has value, should not get default
        }
        needed = self.manager._determine_needed_defaults(current_values)
        expected = {
            'Email_Confidence_Level': 'Pattern'
        }
        self.assertEqual(needed, expected)
        
        # Test case 3: All fields already have values
        current_values = {
            'Engagement_Status': 'Auto-Send',
            'Email_Confidence_Level': 'Real',
            'Level Engaged': '2nd degree'
        }
        needed = self.manager._determine_needed_defaults(current_values)
        self.assertEqual(needed, {})
    
    @patch('sync.engagement_defaults.requests.get')
    def test_get_current_airtable_values_success(self, mock_get):
        """Test successful retrieval of current Airtable values."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'fields': {
                'Engagement_Status': 'Manual Review',
                'Email_Confidence_Level': '',
                'Level Engaged': '1st degree'
            }
        }
        mock_get.return_value = mock_response
        
        result = self.manager._get_current_airtable_values('test_record_id')
        
        expected = {
            'Engagement_Status': 'Manual Review',
            'Email_Confidence_Level': '',
            'Level Engaged': '1st degree'
        }
        self.assertEqual(result, expected)
        
        # Verify API call was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('test_record_id', call_args[0][0])  # URL contains record ID
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_api_key')
    
    @patch('sync.engagement_defaults.requests.get')
    def test_get_current_airtable_values_not_found(self, mock_get):
        """Test handling of record not found (404) response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.manager._get_current_airtable_values('nonexistent_record')
        self.assertIsNone(result)
    
    @patch('sync.engagement_defaults.requests.get')
    def test_get_current_airtable_values_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response
        
        result = self.manager._get_current_airtable_values('test_record_id')
        self.assertIsNone(result)
    
    @patch('sync.engagement_defaults.requests.get')
    def test_get_current_airtable_values_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = Exception('Request timeout')
        
        result = self.manager._get_current_airtable_values('test_record_id')
        self.assertIsNone(result)
    
    @patch('sync.engagement_defaults.requests.patch')
    def test_update_airtable_record_success(self, mock_patch):
        """Test successful Airtable record update."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        updates = {'Engagement_Status': 'Auto-Send'}
        result = self.manager._update_airtable_record('test_record_id', updates)
        
        self.assertTrue(result)
        
        # Verify API call
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        self.assertIn('test_record_id', call_args[0][0])
        self.assertEqual(call_args[1]['json']['fields'], updates)
    
    @patch('sync.engagement_defaults.requests.patch')
    def test_update_airtable_record_rate_limit_retry(self, mock_patch):
        """Test retry logic for rate limiting (429 response)."""
        # First call returns 429, second call succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        mock_patch.side_effect = [mock_response_429, mock_response_200]
        
        with patch('sync.engagement_defaults.time.sleep'):  # Mock sleep to speed up test
            updates = {'Engagement_Status': 'Auto-Send'}
            result = self.manager._update_airtable_record('test_record_id', updates)
        
        self.assertTrue(result)
        self.assertEqual(mock_patch.call_count, 2)  # Should have retried
    
    @patch('sync.engagement_defaults.requests.patch')
    def test_update_airtable_record_max_retries_exceeded(self, mock_patch):
        """Test behavior when max retries are exceeded."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_patch.return_value = mock_response
        
        with patch('sync.engagement_defaults.time.sleep'):  # Mock sleep to speed up test
            updates = {'Engagement_Status': 'Auto-Send'}
            result = self.manager._update_airtable_record('test_record_id', updates)
        
        self.assertFalse(result)
        self.assertEqual(mock_patch.call_count, 3)  # Initial + 2 retries
    
    @patch.object(EngagementDefaultsManager, '_get_current_airtable_values')
    @patch.object(EngagementDefaultsManager, '_update_airtable_record')
    def test_apply_defaults_to_lead_success(self, mock_update, mock_get_values):
        """Test successful application of defaults to a lead."""
        # Mock current values (some fields need defaults)
        mock_get_values.return_value = {
            'Engagement_Status': '',  # Needs default
            'Email_Confidence_Level': 'Real',  # Already has value
            'Level Engaged': ''  # Empty, but default is also empty
        }
        
        # Mock successful update
        mock_update.return_value = True
        
        result = self.manager.apply_defaults_to_lead('lead_123', 'airtable_456')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['fields_updated'], ['Engagement_Status'])
        self.assertEqual(result['values_applied'], {'Engagement_Status': 'Auto-Send'})
        
        # Verify update was called with correct values
        mock_update.assert_called_once_with('airtable_456', {'Engagement_Status': 'Auto-Send'})
    
    @patch.object(EngagementDefaultsManager, '_get_current_airtable_values')
    def test_apply_defaults_to_lead_no_defaults_needed(self, mock_get_values):
        """Test when no defaults are needed."""
        # Mock current values (all fields already have values)
        mock_get_values.return_value = {
            'Engagement_Status': 'Manual Review',
            'Email_Confidence_Level': 'Real',
            'Level Engaged': '1st degree'
        }
        
        result = self.manager.apply_defaults_to_lead('lead_123', 'airtable_456')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['fields_updated'], [])
        self.assertEqual(result['message'], 'No defaults needed')
    
    @patch.object(EngagementDefaultsManager, '_get_current_airtable_values')
    def test_apply_defaults_to_lead_get_values_failure(self, mock_get_values):
        """Test handling of failure to get current values."""
        mock_get_values.return_value = None
        
        result = self.manager.apply_defaults_to_lead('lead_123', 'airtable_456')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Failed to retrieve current Airtable values')
    
    @patch.object(EngagementDefaultsManager, '_get_current_airtable_values')
    @patch.object(EngagementDefaultsManager, '_update_airtable_record')
    def test_apply_defaults_to_lead_update_failure(self, mock_update, mock_get_values):
        """Test handling of update failure."""
        mock_get_values.return_value = {'Engagement_Status': ''}
        mock_update.return_value = False
        
        result = self.manager.apply_defaults_to_lead('lead_123', 'airtable_456')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Failed to update Airtable record')
    
    @patch.object(EngagementDefaultsManager, 'apply_defaults_to_lead')
    def test_apply_defaults_to_multiple_leads_success(self, mock_apply_single):
        """Test successful batch application of defaults."""
        # Mock individual applications
        mock_apply_single.side_effect = [
            {'success': True, 'fields_updated': ['Engagement_Status'], 'values_applied': {'Engagement_Status': 'Auto-Send'}},
            {'success': True, 'fields_updated': [], 'message': 'No defaults needed'},
            {'success': True, 'fields_updated': ['Email_Confidence_Level'], 'values_applied': {'Email_Confidence_Level': 'Pattern'}}
        ]
        
        lead_records = [
            {'lead_id': 'lead_1', 'airtable_record_id': 'airtable_1'},
            {'lead_id': 'lead_2', 'airtable_record_id': 'airtable_2'},
            {'lead_id': 'lead_3', 'airtable_record_id': 'airtable_3'}
        ]
        
        with patch('sync.engagement_defaults.time.sleep'):  # Mock sleep to speed up test
            result = self.manager.apply_defaults_to_multiple_leads(lead_records)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_leads'], 3)
        self.assertEqual(result['processed_count'], 3)
        self.assertEqual(result['updated_count'], 2)
        self.assertEqual(result['skipped_count'], 1)
        self.assertEqual(result['failed_count'], 0)
        self.assertEqual(set(result['fields_updated']), {'Engagement_Status', 'Email_Confidence_Level'})
    
    @patch.object(EngagementDefaultsManager, 'apply_defaults_to_lead')
    def test_apply_defaults_to_multiple_leads_with_failures(self, mock_apply_single):
        """Test batch application with some failures."""
        mock_apply_single.side_effect = [
            {'success': True, 'fields_updated': ['Engagement_Status']},
            {'success': False, 'error': 'API timeout'},
            Exception('Network error')
        ]
        
        lead_records = [
            {'lead_id': 'lead_1', 'airtable_record_id': 'airtable_1'},
            {'lead_id': 'lead_2', 'airtable_record_id': 'airtable_2'},
            {'lead_id': 'lead_3', 'airtable_record_id': 'airtable_3'}
        ]
        
        with patch('sync.engagement_defaults.time.sleep'):  # Mock sleep to speed up test
            result = self.manager.apply_defaults_to_multiple_leads(lead_records)
        
        self.assertFalse(result['success'])  # Should be False due to failures
        self.assertEqual(result['updated_count'], 1)
        self.assertEqual(result['failed_count'], 2)
        self.assertEqual(len(result['errors']), 2)
    
    def test_apply_defaults_to_multiple_leads_missing_airtable_id(self):
        """Test handling of leads without Airtable record IDs."""
        lead_records = [
            {'lead_id': 'lead_1'},  # Missing airtable_record_id
            {'lead_id': 'lead_2', 'airtable_record_id': ''}  # Empty airtable_record_id
        ]
        
        result = self.manager.apply_defaults_to_multiple_leads(lead_records)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['failed_count'], 2)
        self.assertEqual(result['processed_count'], 0)
    
    def test_validate_configuration_success(self):
        """Test configuration validation with valid settings."""
        errors = self.manager.validate_configuration()
        self.assertEqual(errors, [])
    
    def test_validate_configuration_missing_credentials(self):
        """Test configuration validation with missing credentials."""
        self.manager.api_key = ''
        self.manager.base_id = ''
        
        errors = self.manager.validate_configuration()
        
        self.assertIn('Airtable API key is missing', errors)
        self.assertIn('Airtable base ID is missing', errors)
    
    def test_validate_configuration_missing_default_values(self):
        """Test configuration validation with missing default values."""
        self.manager.DEFAULT_VALUES = {}
        
        errors = self.manager.validate_configuration()
        
        self.assertIn('No default values configured', errors)
    
    def test_validate_configuration_missing_required_fields(self):
        """Test configuration validation with missing required fields."""
        self.manager.DEFAULT_VALUES = {'Engagement_Status': 'Auto-Send'}  # Missing other required fields
        
        errors = self.manager.validate_configuration()
        
        self.assertIn('Missing default value for required field: Email_Confidence_Level', errors)
        self.assertIn('Missing default value for required field: Level Engaged', errors)
    
    def test_get_configuration_summary(self):
        """Test configuration summary generation."""
        summary = self.manager.get_configuration_summary()
        
        expected_keys = ['enabled', 'default_values', 'apply_on_scrape', 'apply_on_enrich', 
                        'apply_on_verify', 'airtable_configured', 'validation_errors', 'performance_stats']
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        self.assertTrue(summary['enabled'])
        self.assertTrue(summary['airtable_configured'])
        self.assertEqual(summary['validation_errors'], [])
    
    def test_performance_stats_tracking(self):
        """Test performance statistics tracking."""
        # Initial stats should be zero
        stats = self.manager.get_performance_stats()
        self.assertEqual(stats['total_operations'], 0)
        self.assertEqual(stats['successful_operations'], 0)
        self.assertEqual(stats['failed_operations'], 0)
        
        # Simulate some operations by calling _update_performance_stats
        self.manager._update_performance_stats('test_op_1', 0.5)
        self.manager._update_performance_stats('test_op_2', 1.0)
        self.manager._update_performance_stats('test_op_3', 1.5)
        
        # Manually set success/failure counts (these aren't updated by _update_performance_stats)
        self.manager.performance_stats['successful_operations'] = 2
        self.manager.performance_stats['failed_operations'] = 1
        
        stats = self.manager.get_performance_stats()
        self.assertEqual(stats['total_operations'], 3)
        self.assertEqual(stats['success_rate'], 66.66666666666666)  # 2/3 * 100
        self.assertEqual(stats['failure_rate'], 33.33333333333333)  # 1/3 * 100
        self.assertEqual(stats['average_processing_time'], 1.0)  # (0.5 + 1.0 + 1.5) / 3
        self.assertEqual(stats['total_processing_time'], 3.0)
    
    def test_get_monitoring_report(self):
        """Test monitoring report generation."""
        report = self.manager.get_monitoring_report()
        
        expected_keys = ['timestamp', 'configuration', 'performance', 'system_status', 'operational_metrics']
        
        for key in expected_keys:
            self.assertIn(key, report)
        
        self.assertIn('enabled', report['system_status'])
        self.assertIn('airtable_configured', report['system_status'])
        self.assertIn('total_operations', report['operational_metrics'])
    
    def test_reset_performance_stats(self):
        """Test performance statistics reset."""
        # Set some stats
        self.manager.performance_stats['total_operations'] = 10
        self.manager.performance_stats['successful_operations'] = 8
        
        # Reset
        self.manager.reset_performance_stats()
        
        # Verify reset
        stats = self.manager.get_performance_stats()
        self.assertEqual(stats['total_operations'], 0)
        self.assertEqual(stats['successful_operations'], 0)


class TestEngagementDefaultsConfig(unittest.TestCase):
    """Test cases for EngagementDefaultsConfig class."""
    
    def test_config_initialization_with_defaults(self):
        """Test configuration initialization with default values."""
        config = EngagementDefaultsConfig()
        
        self.assertTrue(config.enabled)
        self.assertTrue(config.apply_on_scrape)
        self.assertTrue(config.apply_on_enrich)
        self.assertTrue(config.apply_on_verify)
        
        expected_defaults = {
            'Engagement_Status': 'Auto-Send',
            'Email_Confidence_Level': 'Pattern',
            'Level Engaged': ''
        }
        self.assertEqual(config.default_values, expected_defaults)
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = EngagementDefaultsConfig()
        errors = config.validate_field_values()
        self.assertEqual(errors, [])
    
    def test_config_validation_invalid_engagement_status(self):
        """Test validation with invalid engagement status."""
        config = EngagementDefaultsConfig()
        config.default_values['Engagement_Status'] = 'InvalidStatus'
        
        errors = config.validate_field_values()
        self.assertTrue(any('Invalid Engagement_Status value' in error for error in errors))
    
    def test_config_validation_invalid_confidence_level(self):
        """Test validation with invalid confidence level."""
        config = EngagementDefaultsConfig()
        config.default_values['Email_Confidence_Level'] = 'InvalidLevel'
        
        errors = config.validate_field_values()
        self.assertTrue(any('Invalid Email_Confidence_Level value' in error for error in errors))
    
    def test_config_post_init_validation_missing_fields(self):
        """Test post-init validation with missing required fields."""
        with self.assertRaises(ValueError) as context:
            EngagementDefaultsConfig(
                enabled=True,
                default_values={'Engagement_Status': 'Auto-Send'}  # Missing required fields
            )
        
        self.assertIn('Missing required engagement default fields', str(context.exception))
    
    def test_config_post_init_validation_invalid_type(self):
        """Test post-init validation with invalid default_values type."""
        with self.assertRaises(ValueError) as context:
            EngagementDefaultsConfig(default_values="not a dict")
        
        self.assertIn('default_values must be a dictionary', str(context.exception))
    
    def test_config_get_summary(self):
        """Test configuration summary generation."""
        config = EngagementDefaultsConfig()
        summary = config.get_summary()
        
        expected_keys = ['enabled', 'default_values', 'apply_on_scrape', 'apply_on_enrich', 
                        'apply_on_verify', 'validation_errors']
        
        for key in expected_keys:
            self.assertIn(key, summary)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    @patch('sync.engagement_defaults.EngagementDefaultsManager')
    def test_apply_defaults_to_lead_convenience_function(self, mock_manager_class):
        """Test the apply_defaults_to_lead convenience function."""
        mock_manager = Mock()
        mock_manager.apply_defaults_to_lead.return_value = {'success': True}
        mock_manager_class.return_value = mock_manager
        
        result = apply_defaults_to_lead('lead_123', 'airtable_456')
        
        self.assertEqual(result, {'success': True})
        mock_manager.apply_defaults_to_lead.assert_called_once_with('lead_123', 'airtable_456')
    
    @patch('sync.engagement_defaults.get_settings')
    def test_is_defaults_enabled_convenience_function(self, mock_get_settings):
        """Test the is_defaults_enabled convenience function."""
        mock_settings = Mock()
        mock_settings.engagement_defaults.enabled = True
        mock_get_settings.return_value = mock_settings
        
        result = is_defaults_enabled()
        
        self.assertTrue(result)


class TestEnvironmentVariableHandling(unittest.TestCase):
    """Test cases for environment variable handling."""
    
    def setUp(self):
        """Set up test environment."""
        # Store original environment variables
        self.original_env = {}
        env_vars = ['APPLY_ENGAGEMENT_DEFAULTS', 'ENGAGEMENT_DEFAULT_VALUES', 
                   'APPLY_DEFAULTS_ON_SCRAPE', 'APPLY_DEFAULTS_ON_ENRICH', 'APPLY_DEFAULTS_ON_VERIFY']
        
        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    @patch('sync.engagement_defaults.get_settings')
    def test_environment_variable_enabled_false(self, mock_get_settings):
        """Test handling of APPLY_ENGAGEMENT_DEFAULTS=false."""
        mock_settings = Mock()
        mock_settings.engagement_defaults.enabled = False
        mock_get_settings.return_value = mock_settings
        
        result = is_defaults_enabled()
        self.assertFalse(result)
    
    @patch('sync.engagement_defaults.get_settings')
    def test_environment_variable_enabled_true(self, mock_get_settings):
        """Test handling of APPLY_ENGAGEMENT_DEFAULTS=true."""
        mock_settings = Mock()
        mock_settings.engagement_defaults.enabled = True
        mock_get_settings.return_value = mock_settings
        
        result = is_defaults_enabled()
        self.assertTrue(result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)