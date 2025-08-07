#!/usr/bin/env python3
"""
Unit tests for CLI apply-defaults command

Tests the CLI command functionality for applying engagement defaults.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from click.testing import CliRunner

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.cli import cli


class TestCLIApplyDefaults(unittest.TestCase):
    """Test cases for the apply-defaults CLI command."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.engagement_defaults.enabled = True
        
        # Mock database
        self.mock_db = Mock()
        
        # Mock engagement defaults manager
        self.mock_defaults_manager = Mock()
        self.mock_defaults_manager.validate_configuration.return_value = []
        self.mock_defaults_manager.get_configuration_summary.return_value = {
            'default_values': {
                'Engagement_Status': 'Auto-Send',
                'Email_Confidence_Level': 'Pattern',
                'Level Engaged': ''
            }
        }
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_help(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test that the help command works."""
        result = self.runner.invoke(cli, ['apply-defaults', '--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Apply engagement defaults', result.output)
        self.assertIn('--dry-run', result.output)
        self.assertIn('--filter-status', result.output)
        self.assertIn('--lead-id', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    def test_apply_defaults_disabled(self, mock_is_enabled):
        """Test behavior when engagement defaults are disabled."""
        mock_is_enabled.return_value = False
        
        result = self.runner.invoke(cli, ['apply-defaults'])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Engagement defaults are disabled', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_configuration_errors(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test handling of configuration errors."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        
        # Mock configuration errors
        mock_manager = Mock()
        mock_manager.validate_configuration.return_value = ['Missing API key', 'Invalid base ID']
        mock_manager_class.return_value = mock_manager
        
        result = self.runner.invoke(cli, ['apply-defaults'])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Configuration errors found', result.output)
        self.assertIn('Missing API key', result.output)
        self.assertIn('Invalid base ID', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_dry_run(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test dry run functionality."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        mock_manager_class.return_value = self.mock_defaults_manager
        
        # Mock leads with Airtable IDs
        mock_lead1 = Mock()
        mock_lead1.id = 'lead_1'
        mock_lead1.name = 'John Doe'
        mock_lead1.airtable_id = 'airtable_1'
        
        mock_lead2 = Mock()
        mock_lead2.id = 'lead_2'
        mock_lead2.name = 'Jane Smith'
        mock_lead2.airtable_id = 'airtable_2'
        
        self.mock_db.search_leads.return_value = [mock_lead1, mock_lead2]
        
        result = self.runner.invoke(cli, ['apply-defaults', '--dry-run', '--limit', '2'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('DRY RUN: Would process 2 leads', result.output)
        self.assertIn('John Doe', result.output)
        self.assertIn('Jane Smith', result.output)
        self.assertIn('No changes will be made', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_specific_lead_dry_run(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test applying defaults to a specific lead in dry run mode."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        mock_manager_class.return_value = self.mock_defaults_manager
        
        # Mock specific lead
        mock_lead = Mock()
        mock_lead.id = 'lead_123'
        mock_lead.name = 'John Doe'
        mock_lead.airtable_id = 'airtable_123'
        
        self.mock_db.search_leads.return_value = [mock_lead]
        
        result = self.runner.invoke(cli, ['apply-defaults', '--dry-run', '--lead-id', 'lead_123'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Processing specific lead: lead_123', result.output)
        self.assertIn('DRY RUN: Would apply defaults to lead', result.output)
        self.assertIn('John Doe', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_lead_not_found(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test handling of lead not found."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        mock_manager_class.return_value = self.mock_defaults_manager
        
        # Mock no leads found
        self.mock_db.search_leads.return_value = []
        
        result = self.runner.invoke(cli, ['apply-defaults', '--lead-id', 'nonexistent'])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Lead with ID \'nonexistent\' not found', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_lead_no_airtable_id(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test handling of lead without Airtable ID."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        mock_manager_class.return_value = self.mock_defaults_manager
        
        # Mock lead without Airtable ID
        mock_lead = Mock()
        mock_lead.id = 'lead_123'
        mock_lead.name = 'John Doe'
        mock_lead.airtable_id = None
        
        self.mock_db.search_leads.return_value = [mock_lead]
        
        result = self.runner.invoke(cli, ['apply-defaults', '--lead-id', 'lead_123'])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn('has no Airtable record ID', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_no_leads_found(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test handling when no leads are found."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        mock_manager_class.return_value = self.mock_defaults_manager
        
        # Mock no leads found
        self.mock_db.search_leads.return_value = []
        
        result = self.runner.invoke(cli, ['apply-defaults'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('No leads found with status \'synced\'', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_successful_execution(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test successful execution of defaults application."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        
        # Mock successful defaults application
        mock_manager = Mock()
        mock_manager.validate_configuration.return_value = []
        mock_manager.get_configuration_summary.return_value = {
            'default_values': {
                'Engagement_Status': 'Auto-Send',
                'Email_Confidence_Level': 'Pattern',
                'Level Engaged': ''
            }
        }
        mock_manager.apply_defaults_to_multiple_leads.return_value = {
            'updated_count': 2,
            'skipped_count': 0,
            'failed_count': 0,
            'errors': []
        }
        mock_manager_class.return_value = mock_manager
        
        # Mock leads
        mock_lead1 = Mock()
        mock_lead1.id = 'lead_1'
        mock_lead1.name = 'John Doe'
        mock_lead1.airtable_id = 'airtable_1'
        
        mock_lead2 = Mock()
        mock_lead2.id = 'lead_2'
        mock_lead2.name = 'Jane Smith'
        mock_lead2.airtable_id = 'airtable_2'
        
        self.mock_db.search_leads.return_value = [mock_lead1, mock_lead2]
        
        result = self.runner.invoke(cli, ['apply-defaults', '--confirm', '--limit', '2'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Found 2 leads to process', result.output)
        self.assertIn('Updated: 2', result.output)
        self.assertIn('Successfully applied engagement defaults', result.output)
    
    @patch('cli.cli.is_defaults_enabled')
    @patch('cli.cli.get_lead_database')
    @patch('cli.cli.EngagementDefaultsManager')
    def test_apply_defaults_with_failures(self, mock_manager_class, mock_get_db, mock_is_enabled):
        """Test handling of failures during defaults application."""
        mock_is_enabled.return_value = True
        mock_get_db.return_value = self.mock_db
        
        # Mock defaults application with failures
        mock_manager = Mock()
        mock_manager.validate_configuration.return_value = []
        mock_manager.get_configuration_summary.return_value = {
            'default_values': {
                'Engagement_Status': 'Auto-Send',
                'Email_Confidence_Level': 'Pattern',
                'Level Engaged': ''
            }
        }
        mock_manager.apply_defaults_to_multiple_leads.return_value = {
            'updated_count': 1,
            'skipped_count': 0,
            'failed_count': 1,
            'errors': ['Lead lead_2: API timeout']
        }
        mock_manager_class.return_value = mock_manager
        
        # Mock leads
        mock_lead1 = Mock()
        mock_lead1.id = 'lead_1'
        mock_lead1.name = 'John Doe'
        mock_lead1.airtable_id = 'airtable_1'
        
        mock_lead2 = Mock()
        mock_lead2.id = 'lead_2'
        mock_lead2.name = 'Jane Smith'
        mock_lead2.airtable_id = 'airtable_2'
        
        self.mock_db.search_leads.return_value = [mock_lead1, mock_lead2]
        
        result = self.runner.invoke(cli, ['apply-defaults', '--confirm', '--limit', '2'])
        
        self.assertEqual(result.exit_code, 1)  # Should exit with error due to failures
        self.assertIn('Updated: 1', result.output)
        self.assertIn('Failed: 1', result.output)
        self.assertIn('API timeout', result.output)
        self.assertIn('failed to update', result.output)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)