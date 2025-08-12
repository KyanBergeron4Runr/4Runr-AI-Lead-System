"""
Unit tests for the Migration Manager.

Tests cover JSON file detection, validation, data normalization, migration,
backup creation, and error handling.
"""

import os
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migration_manager import MigrationManager, MigrationResult


class TestMigrationManager(unittest.TestCase):
    """Test cases for MigrationManager class."""
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize migration manager with temporary database
        self.migration_manager = MigrationManager(self.temp_db.name)
        
        # Sample lead data for testing
        self.sample_leads = [
            {
                "name": "John Doe",
                "title": "Software Engineer",
                "company": "Tech Corp",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "email": "john.doe@techcorp.com",
                "status": "scraped",
                "needs_enrichment": False,
                "scraped_at": "2025-08-04T21:37:42.904361",
                "updated_at": "2025-08-04T21:37:42.904362",
                "location": "San Francisco, CA",
                "Verified": True,
                "Last Verified": "2024-07-26",
                "Source": "Test Database",
                "email_status": "verified",
                "industry": "Technology",
                "company_size": "100-500",
                "enriched_at": "2025-08-04T23:49:03.382637",
                "ready_for_engagement": True
            },
            {
                "full_name": "Jane Smith",
                "title": "Marketing Manager",
                "company": "Marketing Inc",
                "email": "jane.smith@marketing.com",
                "location": "New York, NY",
                "industry": "Marketing",
                "verified": True,
                "enriched": True
            }
        ]
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary files and directories
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except (OSError, FileNotFoundError):
            pass
    
    def create_test_json_file(self, filename: str, data: any) -> str:
        """
        Create a test JSON file with given data.
        
        Args:
            filename: Name of the JSON file
            data: Data to write to the file
            
        Returns:
            Path to the created file
        """
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return file_path
    
    def test_find_json_files_with_additional_paths(self):
        """Test finding JSON files with additional search paths."""
        # Create test JSON files
        leads_file = self.create_test_json_file('leads.json', self.sample_leads)
        raw_leads_file = self.create_test_json_file('raw_leads.json', self.sample_leads)
        
        # Test finding files with additional paths
        found_files = self.migration_manager.find_json_files([self.temp_dir])
        
        self.assertIn(leads_file, found_files)
        self.assertIn(raw_leads_file, found_files)
        self.assertEqual(len(found_files), 2)
    
    def test_find_json_files_with_lead_pattern(self):
        """Test finding JSON files that contain 'lead' in filename."""
        # Create test files
        lead_data_file = self.create_test_json_file('lead_data.json', self.sample_leads)
        other_file = self.create_test_json_file('config.json', {'setting': 'value'})
        
        found_files = self.migration_manager.find_json_files([self.temp_dir])
        
        self.assertIn(lead_data_file, found_files)
        self.assertNotIn(other_file, found_files)
    
    def test_backup_json_files(self):
        """Test creating backup copies of JSON files."""
        # Create test JSON file
        test_file = self.create_test_json_file('test_leads.json', self.sample_leads)
        
        # Create backup
        backup_paths = self.migration_manager.backup_json_files([test_file])
        
        self.assertEqual(len(backup_paths), 1)
        self.assertTrue(os.path.exists(backup_paths[0]))
        
        # Verify backup content
        with open(backup_paths[0], 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        self.assertEqual(backup_data, self.sample_leads)
    
    def test_validate_json_file_valid_list(self):
        """Test validation of valid JSON file with list format."""
        test_file = self.create_test_json_file('valid_leads.json', self.sample_leads)
        
        is_valid, leads, errors = self.migration_manager.validate_json_file(test_file)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(leads), 2)
        self.assertEqual(len(errors), 0)
    
    def test_validate_json_file_valid_dict_with_leads_key(self):
        """Test validation of valid JSON file with dict format containing leads key."""
        data = {'leads': self.sample_leads, 'metadata': {'count': 2}}
        test_file = self.create_test_json_file('dict_leads.json', data)
        
        is_valid, leads, errors = self.migration_manager.validate_json_file(test_file)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(leads), 2)
        self.assertEqual(len(errors), 0)
    
    def test_validate_json_file_single_lead_dict(self):
        """Test validation of JSON file with single lead as dict."""
        single_lead = self.sample_leads[0]
        test_file = self.create_test_json_file('single_lead.json', single_lead)
        
        is_valid, leads, errors = self.migration_manager.validate_json_file(test_file)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(leads), 1)
        self.assertEqual(len(errors), 0)
    
    def test_validate_json_file_invalid_json(self):
        """Test validation of invalid JSON file."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_file, 'w') as f:
            f.write('{ invalid json content')
        
        is_valid, leads, errors = self.migration_manager.validate_json_file(invalid_file)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(leads), 0)
        self.assertGreater(len(errors), 0)
        self.assertIn('Invalid JSON', errors[0])
    
    def test_validate_json_file_missing_name_fields(self):
        """Test validation of JSON file with leads missing name fields."""
        invalid_leads = [
            {'email': 'test@example.com', 'company': 'Test Corp'},  # Missing name
            {'name': 'Valid Lead', 'email': 'valid@example.com'}    # Valid
        ]
        test_file = self.create_test_json_file('missing_names.json', invalid_leads)
        
        is_valid, leads, errors = self.migration_manager.validate_json_file(test_file)
        
        self.assertTrue(is_valid)  # File is valid, but some leads are filtered out
        self.assertEqual(len(leads), 1)  # Only the valid lead
        self.assertGreater(len(errors), 0)  # Error for missing name
    
    def test_normalize_lead_data_standard_fields(self):
        """Test normalization of lead data with standard fields."""
        lead_data = self.sample_leads[0]
        
        normalized = self.migration_manager.normalize_lead_data(lead_data, 'test.json')
        
        self.assertEqual(normalized['full_name'], 'John Doe')
        self.assertEqual(normalized['email'], 'john.doe@techcorp.com')
        self.assertEqual(normalized['company'], 'Tech Corp')
        self.assertEqual(normalized['title'], 'Software Engineer')
        self.assertEqual(normalized['linkedin_url'], 'https://linkedin.com/in/johndoe')
        self.assertTrue(normalized['verified'])
    
    def test_normalize_lead_data_alternative_field_names(self):
        """Test normalization with alternative field names."""
        lead_data = {
            'Name': 'Alternative Name',
            'Email': 'alt@example.com',
            'Company': 'Alt Corp',
            'LinkedIn': 'https://linkedin.com/in/alt',
            'Verified': 'true',
            'enriched': False
        }
        
        normalized = self.migration_manager.normalize_lead_data(lead_data, 'test.json')
        
        self.assertEqual(normalized['full_name'], 'Alternative Name')
        self.assertEqual(normalized['email'], 'alt@example.com')
        self.assertEqual(normalized['company'], 'Alt Corp')
        self.assertEqual(normalized['linkedin_url'], 'https://linkedin.com/in/alt')
        self.assertTrue(normalized['verified'])
        self.assertFalse(normalized['enriched'])
    
    def test_normalize_lead_data_raw_data_preservation(self):
        """Test that unmapped fields are preserved in raw_data."""
        lead_data = {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'custom_field': 'custom_value',
            'another_field': 123,
            'nested_data': {'key': 'value'}
        }
        
        normalized = self.migration_manager.normalize_lead_data(lead_data, 'test.json')
        
        self.assertIn('raw_data', normalized)
        self.assertEqual(normalized['raw_data']['custom_field'], 'custom_value')
        self.assertEqual(normalized['raw_data']['another_field'], 123)
        self.assertEqual(normalized['raw_data']['nested_data'], {'key': 'value'})
    
    def test_normalize_lead_data_source_tracking(self):
        """Test that source is properly tracked."""
        lead_data = {'name': 'Test Lead'}
        
        normalized = self.migration_manager.normalize_lead_data(lead_data, '/path/to/leads.json')
        
        self.assertEqual(normalized['source'], 'migrated_from_leads.json')
    
    def test_migrate_json_files_success(self):
        """Test successful migration of JSON files."""
        # Create test JSON file
        test_file = self.create_test_json_file('test_leads.json', self.sample_leads)
        
        # Perform migration
        result = self.migration_manager.migrate_json_files([test_file], create_backup=False)
        
        self.assertEqual(result.total_files, 1)
        self.assertEqual(result.total_leads, 2)
        self.assertEqual(result.migrated_leads, 2)
        self.assertEqual(result.failed_leads, 0)
        self.assertEqual(len(result.errors), 0)
    
    def test_migrate_json_files_with_backup(self):
        """Test migration with backup creation."""
        # Create test JSON file
        test_file = self.create_test_json_file('backup_test.json', self.sample_leads)
        
        # Perform migration with backup
        result = self.migration_manager.migrate_json_files([test_file], create_backup=True)
        
        self.assertEqual(result.total_files, 1)
        self.assertEqual(len(result.backup_paths), 1)
        self.assertTrue(os.path.exists(result.backup_paths[0]))
    
    def test_migrate_json_files_auto_detect(self):
        """Test migration with auto-detection of JSON files."""
        # Create test JSON files in temp directory
        self.create_test_json_file('leads.json', self.sample_leads[:1])
        self.create_test_json_file('raw_leads.json', self.sample_leads[1:])
        
        # Mock find_json_files to return our temp files
        with patch.object(self.migration_manager, 'find_json_files') as mock_find:
            mock_find.return_value = [
                os.path.join(self.temp_dir, 'leads.json'),
                os.path.join(self.temp_dir, 'raw_leads.json')
            ]
            
            result = self.migration_manager.migrate_json_files(create_backup=False)
        
        self.assertEqual(result.total_files, 2)
        self.assertEqual(result.total_leads, 2)
        self.assertEqual(result.migrated_leads, 2)
    
    def test_migrate_json_files_invalid_file(self):
        """Test migration with invalid JSON file."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_file, 'w') as f:
            f.write('{ invalid json')
        
        result = self.migration_manager.migrate_json_files([invalid_file], create_backup=False)
        
        self.assertEqual(result.total_files, 1)
        self.assertEqual(result.total_leads, 0)
        self.assertEqual(result.migrated_leads, 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_migrate_json_files_no_files(self):
        """Test migration when no JSON files are found."""
        result = self.migration_manager.migrate_json_files([], create_backup=False)
        
        self.assertEqual(result.total_files, 0)
        self.assertEqual(result.total_leads, 0)
        self.assertEqual(result.migrated_leads, 0)
    
    def test_validate_migration(self):
        """Test migration validation."""
        # Create and migrate test data
        test_file = self.create_test_json_file('validation_test.json', self.sample_leads)
        self.migration_manager.migrate_json_files([test_file], create_backup=False)
        
        # Validate migration
        validation_result = self.migration_manager.validate_migration([test_file])
        
        self.assertEqual(validation_result['total_json_leads'], 2)
        self.assertEqual(validation_result['total_db_leads'], 2)
        self.assertEqual(validation_result['matched_leads'], 2)
        self.assertEqual(len(validation_result['missing_leads']), 0)
    
    def test_validate_migration_missing_leads(self):
        """Test validation when some leads are missing from database."""
        # Create JSON file but don't migrate all leads
        test_file = self.create_test_json_file('missing_test.json', self.sample_leads)
        
        # Only add one lead to database manually
        self.migration_manager.db.add_lead({
            'full_name': 'John Doe',
            'email': 'john.doe@techcorp.com'
        })
        
        validation_result = self.migration_manager.validate_migration([test_file])
        
        self.assertEqual(validation_result['total_json_leads'], 2)
        self.assertEqual(validation_result['total_db_leads'], 1)
        self.assertEqual(validation_result['matched_leads'], 1)
        self.assertEqual(len(validation_result['missing_leads']), 1)
    
    def test_get_migration_status(self):
        """Test getting migration status."""
        # Mock find_json_files to return test files
        with patch.object(self.migration_manager, 'find_json_files') as mock_find:
            mock_find.return_value = ['test1.json', 'test2.json']
            
            status = self.migration_manager.get_migration_status()
        
        self.assertIn('database_stats', status)
        self.assertEqual(status['available_json_files'], 2)
        self.assertEqual(len(status['json_file_paths']), 2)
        self.assertTrue(status['migration_ready'])
        self.assertIn('last_check', status)
    
    def test_migration_result_dataclass(self):
        """Test MigrationResult dataclass initialization."""
        # Test default initialization
        result = MigrationResult()
        self.assertEqual(result.total_files, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.backup_paths, [])
        
        # Test with parameters
        result = MigrationResult(
            total_files=5,
            migrated_leads=10,
            errors=['error1', 'error2']
        )
        self.assertEqual(result.total_files, 5)
        self.assertEqual(result.migrated_leads, 10)
        self.assertEqual(len(result.errors), 2)
    
    def test_error_handling_file_permissions(self):
        """Test error handling for file permission issues."""
        # Create a file and make it unreadable (on Unix systems)
        test_file = self.create_test_json_file('permission_test.json', self.sample_leads)
        
        # Try to make file unreadable (this might not work on all systems)
        try:
            os.chmod(test_file, 0o000)
            
            result = self.migration_manager.migrate_json_files([test_file], create_backup=False)
            
            # Should handle the error gracefully
            # On Windows, this might not actually cause an error, so we check if it worked
            if os.access(test_file, os.R_OK):
                # File is still readable, skip this test
                self.skipTest("Cannot make file unreadable on this system")
            else:
                self.assertGreater(len(result.errors), 0)
            
        except (OSError, PermissionError):
            # Skip this test if we can't change permissions
            self.skipTest("Cannot change file permissions on this system")
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(test_file, 0o644)
            except (OSError, PermissionError):
                pass
    
    def test_duplicate_handling_during_migration(self):
        """Test that duplicates are handled correctly during migration."""
        # Create leads with potential duplicates
        duplicate_leads = [
            {
                'name': 'Duplicate Lead',
                'email': 'duplicate@example.com',
                'company': 'Test Corp'
            },
            {
                'full_name': 'Duplicate Lead',  # Same person, different field name
                'email': 'duplicate@example.com',
                'title': 'Updated Title'
            }
        ]
        
        test_file = self.create_test_json_file('duplicate_test.json', duplicate_leads)
        
        result = self.migration_manager.migrate_json_files([test_file], create_backup=False)
        
        # Should migrate both but the second should update the first
        self.assertEqual(result.total_leads, 2)
        self.assertEqual(result.migrated_leads, 2)  # Both processed
        
        # Verify only one lead exists in database
        all_leads = self.migration_manager.db.get_all_leads()
        matching_leads = [lead for lead in all_leads if lead['email'] == 'duplicate@example.com']
        self.assertEqual(len(matching_leads), 1)
        
        # Verify the lead has the updated title
        self.assertEqual(matching_leads[0]['title'], 'Updated Title')


if __name__ == '__main__':
    unittest.main()