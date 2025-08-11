"""
Migration Manager for Lead Database Integration.

This module handles the migration of lead data from JSON files to the SQLite database,
providing backup functionality, validation, and comprehensive error handling.
"""

import os
import json
import shutil
import datetime
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from lead_database import LeadDatabase
from shared.logging_utils import get_logger


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    total_files: int = 0
    total_leads: int = 0
    migrated_leads: int = 0
    failed_leads: int = 0
    duplicate_leads: int = 0
    errors: List[str] = None
    backup_paths: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.backup_paths is None:
            self.backup_paths = []


class MigrationManager:
    """
    Handles migration of lead data from JSON files to SQLite database.
    
    Features:
    - Automatic detection of JSON lead files
    - Backup creation before migration
    - Data validation and error handling
    - Duplicate detection and merging
    - Comprehensive logging and reporting
    """
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """
        Initialize the Migration Manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = LeadDatabase(db_path)
        self.logger = get_logger('migration_manager')
        
        # Common JSON file patterns to look for
        self.json_file_patterns = [
            'leads.json',
            'raw_leads.json', 
            'enriched_leads.json',
            'scraped_leads.json'
        ]
        
        # Common directories to search
        self.search_directories = [
            'shared',
            'data',
            '.',
            'archived_systems/4runr-agents/shared'
        ]
        
        self.logger.log_module_activity('migration_manager', 'system', 'success', {
            'message': 'Migration Manager initialized successfully',
            'db_path': db_path
        })
    
    def find_json_files(self, additional_paths: Optional[List[str]] = None) -> List[str]:
        """
        Find all JSON files that might contain lead data.
        
        Args:
            additional_paths: Additional file paths to check
            
        Returns:
            List of paths to JSON files found
        """
        found_files = []
        search_paths = self.search_directories.copy()
        
        if additional_paths:
            search_paths.extend(additional_paths)
        
        for directory in search_paths:
            if not os.path.exists(directory):
                continue
                
            for pattern in self.json_file_patterns:
                file_path = os.path.join(directory, pattern)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    found_files.append(file_path)
        
        # Also search for any JSON files in the directories
        for directory in search_paths:
            if not os.path.exists(directory):
                continue
                
            try:
                for file in os.listdir(directory):
                    if file.endswith('.json') and 'lead' in file.lower():
                        file_path = os.path.join(directory, file)
                        if file_path not in found_files:
                            found_files.append(file_path)
            except (OSError, PermissionError):
                continue
        
        self.logger.log_module_activity('migration_manager', 'system', 'info', {
            'message': f'Found {len(found_files)} JSON files',
            'files': found_files
        })
        
        return found_files
    
    def backup_json_files(self, json_files: List[str]) -> List[str]:
        """
        Create backup copies of JSON files before migration.
        
        Args:
            json_files: List of JSON file paths to backup
            
        Returns:
            List of backup file paths created
        """
        backup_paths = []
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup directory
        backup_dir = Path("data/migration_backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for json_file in json_files:
            try:
                file_path = Path(json_file)
                if not file_path.exists():
                    continue
                
                # Create backup filename
                backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
                backup_path = backup_dir / backup_name
                
                # Copy file to backup location
                shutil.copy2(json_file, backup_path)
                backup_paths.append(str(backup_path))
                
                self.logger.log_module_activity('migration_manager', 'system', 'success', {
                    'message': f'Created backup of {json_file}',
                    'backup_path': str(backup_path),
                    'original_size': file_path.stat().st_size
                })
                
            except Exception as e:
                self.logger.log_error(e, {
                    'action': 'backup_json_file',
                    'file': json_file
                })
        
        return backup_paths
    
    def validate_json_file(self, file_path: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Validate and load JSON file content.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (is_valid, lead_data_list, errors)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                leads = data
            elif isinstance(data, dict):
                # Check if it's a single lead or has a leads key
                if 'leads' in data:
                    leads = data['leads']
                elif any(key in data for key in ['name', 'full_name', 'email']):
                    leads = [data]  # Single lead object
                else:
                    errors.append(f"Unknown JSON structure in {file_path}")
                    return False, [], errors
            else:
                errors.append(f"Invalid JSON structure in {file_path} - expected list or dict")
                return False, [], errors
            
            # Validate each lead has minimum required fields
            valid_leads = []
            for i, lead in enumerate(leads):
                if not isinstance(lead, dict):
                    errors.append(f"Lead {i} in {file_path} is not a dictionary")
                    continue
                
                # Check for required fields (name is essential)
                if not any(key in lead for key in ['name', 'full_name']):
                    errors.append(f"Lead {i} in {file_path} missing name field")
                    continue
                
                valid_leads.append(lead)
            
            return True, valid_leads, errors
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {file_path}: {str(e)}")
            return False, [], errors
        except Exception as e:
            errors.append(f"Error reading {file_path}: {str(e)}")
            return False, [], errors
    
    def normalize_lead_data(self, lead_data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """
        Normalize lead data from JSON to database format.
        
        Args:
            lead_data: Raw lead data from JSON
            source_file: Source file path for tracking
            
        Returns:
            Normalized lead data
        """
        normalized = {}
        
        # Handle name fields
        normalized['full_name'] = (
            lead_data.get('full_name') or 
            lead_data.get('name') or 
            lead_data.get('Name', '')
        )
        
        # Standard fields with fallbacks
        field_mappings = {
            'email': ['email', 'Email'],
            'company': ['company', 'Company'],
            'title': ['title', 'Title', 'position'],
            'linkedin_url': ['linkedin_url', 'LinkedIn', 'linkedin'],
            'location': ['location', 'Location'],
            'industry': ['industry', 'Industry'],
            'company_size': ['company_size', 'Company Size', 'size'],
            'status': ['status', 'Status'],
            'source': ['source', 'Source']
        }
        
        for db_field, json_fields in field_mappings.items():
            for json_field in json_fields:
                if json_field in lead_data and lead_data[json_field]:
                    normalized[db_field] = lead_data[json_field]
                    break
        
        # Boolean fields
        boolean_mappings = {
            'verified': ['Verified', 'verified', 'is_verified'],
            'enriched': ['enriched', 'Enriched', 'is_enriched'],
            'needs_enrichment': ['needs_enrichment', 'Needs Enrichment']
        }
        
        for db_field, json_fields in boolean_mappings.items():
            for json_field in json_fields:
                if json_field in lead_data:
                    value = lead_data[json_field]
                    if isinstance(value, bool):
                        normalized[db_field] = value
                    elif isinstance(value, str):
                        normalized[db_field] = value.lower() in ['true', '1', 'yes']
                    break
        
        # Timestamp fields
        timestamp_mappings = {
            'scraped_at': ['scraped_at', 'Scraped At', 'created_at'],
            'enriched_at': ['enriched_at', 'Enriched At', 'updated_at']
        }
        
        for db_field, json_fields in timestamp_mappings.items():
            for json_field in json_fields:
                if json_field in lead_data and lead_data[json_field]:
                    normalized[db_field] = lead_data[json_field]
                    break
        
        # Add source tracking
        if not normalized.get('source'):
            normalized['source'] = f"migrated_from_{Path(source_file).name}"
        
        # Store raw data for any unmapped fields
        raw_data = {}
        mapped_fields = set()
        for field_list in field_mappings.values():
            mapped_fields.update(field_list)
        for field_list in boolean_mappings.values():
            mapped_fields.update(field_list)
        for field_list in timestamp_mappings.values():
            mapped_fields.update(field_list)
        
        for key, value in lead_data.items():
            if key not in mapped_fields and key not in ['name', 'full_name']:
                raw_data[key] = value
        
        if raw_data:
            normalized['raw_data'] = raw_data
        
        return normalized
    
    def migrate_json_files(self, json_files: Optional[List[str]] = None, 
                          create_backup: bool = True) -> MigrationResult:
        """
        Migrate lead data from JSON files to database.
        
        Args:
            json_files: Specific JSON files to migrate (if None, auto-detect)
            create_backup: Whether to create backup copies
            
        Returns:
            MigrationResult with detailed statistics
        """
        result = MigrationResult()
        
        try:
            # Find JSON files if not provided
            if json_files is None:
                json_files = self.find_json_files()
            
            if not json_files:
                self.logger.log_module_activity('migration_manager', 'system', 'info', {
                    'message': 'No JSON files found for migration'
                })
                return result
            
            result.total_files = len(json_files)
            
            # Create backups if requested
            if create_backup:
                result.backup_paths = self.backup_json_files(json_files)
            
            # Process each JSON file
            for json_file in json_files:
                self.logger.log_module_activity('migration_manager', 'system', 'info', {
                    'message': f'Processing {json_file}'
                })
                
                # Validate and load JSON file
                is_valid, leads_data, file_errors = self.validate_json_file(json_file)
                
                if not is_valid:
                    result.errors.extend(file_errors)
                    continue
                
                result.total_leads += len(leads_data)
                
                # Migrate each lead
                for lead_data in leads_data:
                    try:
                        # Normalize the lead data
                        normalized_lead = self.normalize_lead_data(lead_data, json_file)
                        
                        # Add to database (will handle duplicates automatically)
                        lead_id = self.db.add_lead(normalized_lead)
                        
                        if lead_id:
                            result.migrated_leads += 1
                            
                            self.logger.log_module_activity('migration_manager', lead_id, 'success', {
                                'message': 'Lead migrated successfully',
                                'name': normalized_lead.get('full_name', 'Unknown'),
                                'source_file': json_file
                            })
                        else:
                            result.failed_leads += 1
                            
                    except Exception as e:
                        result.failed_leads += 1
                        error_msg = f"Failed to migrate lead from {json_file}: {str(e)}"
                        result.errors.append(error_msg)
                        
                        self.logger.log_error(e, {
                            'action': 'migrate_lead',
                            'source_file': json_file,
                            'lead_data': {k: v for k, v in lead_data.items() if k not in ['raw_data']}
                        })
            
            # Log migration summary
            self.logger.log_module_activity('migration_manager', 'system', 'success', {
                'message': 'Migration completed',
                'total_files': result.total_files,
                'total_leads': result.total_leads,
                'migrated_leads': result.migrated_leads,
                'failed_leads': result.failed_leads,
                'success_rate': result.migrated_leads / result.total_leads if result.total_leads > 0 else 0
            })
            
            return result
            
        except Exception as e:
            result.errors.append(f"Migration failed: {str(e)}")
            self.logger.log_error(e, {'action': 'migrate_json_files'})
            return result
    
    def validate_migration(self, json_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate migration by comparing JSON data with database data.
        
        Args:
            json_files: JSON files to validate against
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'total_json_leads': 0,
            'total_db_leads': 0,
            'matched_leads': 0,
            'missing_leads': [],
            'validation_errors': []
        }
        
        try:
            # Find JSON files if not provided
            if json_files is None:
                json_files = self.find_json_files()
            
            # Count leads in JSON files
            json_leads = {}
            for json_file in json_files:
                is_valid, leads_data, errors = self.validate_json_file(json_file)
                if is_valid:
                    for lead in leads_data:
                        # Create a key for matching
                        name = lead.get('full_name') or lead.get('name', '')
                        email = lead.get('email', '')
                        key = f"{name}|{email}".lower()
                        json_leads[key] = lead
            
            validation_result['total_json_leads'] = len(json_leads)
            
            # Get all leads from database
            db_leads = self.db.get_all_leads()
            validation_result['total_db_leads'] = len(db_leads)
            
            # Match leads
            for db_lead in db_leads:
                name = db_lead.get('full_name', '')
                email = db_lead.get('email', '')
                key = f"{name}|{email}".lower()
                
                if key in json_leads:
                    validation_result['matched_leads'] += 1
            
            # Find missing leads
            for key, json_lead in json_leads.items():
                found = False
                for db_lead in db_leads:
                    db_name = db_lead.get('full_name', '')
                    db_email = db_lead.get('email', '')
                    db_key = f"{db_name}|{db_email}".lower()
                    
                    if key == db_key:
                        found = True
                        break
                
                if not found:
                    validation_result['missing_leads'].append({
                        'name': json_lead.get('full_name') or json_lead.get('name'),
                        'email': json_lead.get('email'),
                        'key': key
                    })
            
            self.logger.log_module_activity('migration_manager', 'system', 'success', {
                'message': 'Migration validation completed',
                'json_leads': validation_result['total_json_leads'],
                'db_leads': validation_result['total_db_leads'],
                'matched': validation_result['matched_leads'],
                'missing': len(validation_result['missing_leads'])
            })
            
            return validation_result
            
        except Exception as e:
            validation_result['validation_errors'].append(str(e))
            self.logger.log_error(e, {'action': 'validate_migration'})
            return validation_result
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status and database statistics.
        
        Returns:
            Dictionary with migration status information
        """
        try:
            # Get database stats
            db_stats = self.db.get_database_stats()
            
            # Find available JSON files
            json_files = self.find_json_files()
            
            # Check for backup files
            backup_dir = Path("data/migration_backups")
            backup_files = []
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*_backup_*.json"))
            
            status = {
                'database_stats': db_stats,
                'available_json_files': len(json_files),
                'json_file_paths': json_files,
                'backup_files_count': len(backup_files),
                'backup_directory': str(backup_dir),
                'migration_ready': len(json_files) > 0,
                'last_check': datetime.datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_migration_status'})
            return {'error': str(e)}