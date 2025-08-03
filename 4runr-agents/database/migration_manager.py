#!/usr/bin/env python3
"""
Migration Manager

Handles migration from JSON files to the database system with
backup creation, validation, and comprehensive error handling.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .lead_database import get_lead_database

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MigrationResult:
    """
    Results of a migration operation
    """
    source_file: str
    leads_processed: int
    leads_migrated: int
    leads_failed: int
    leads_duplicates: int
    errors: List[str]
    duration_seconds: float
    backup_created: bool
    backup_path: Optional[str] = None

@dataclass
class MigrationSummary:
    """
    Summary of all migration operations
    """
    total_files_processed: int
    total_leads_processed: int
    total_leads_migrated: int
    total_leads_failed: int
    total_duplicates_merged: int
    total_duration_seconds: float
    backups_created: List[str]
    errors: List[str]
    success: bool

class MigrationManager:
    """
    Manages migration from JSON files to database
    """
    
    def __init__(self, shared_dir: Optional[str] = None, backup_dir: Optional[str] = None):
        """
        Initialize migration manager
        
        Args:
            shared_dir: Directory containing JSON files (default: shared)
            backup_dir: Directory for backups (default: shared/backups)
        """
        self.script_dir = Path(__file__).parent.parent
        self.shared_dir = Path(shared_dir) if shared_dir else self.script_dir / 'shared'
        self.backup_dir = Path(backup_dir) if backup_dir else self.shared_dir / 'backups'
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
        # Get database instance
        self.db = get_lead_database()
        
        # JSON files to migrate (in order of priority)
        self.json_files = [
            'raw_leads.json',
            'enriched_leads.json',
            'leads.json',
            'custom_enriched_leads.json',
            'scraped_leads.json'
        ]
        
        logger.info(f"Migration manager initialized")
        logger.info(f"Shared directory: {self.shared_dir}")
        logger.info(f"Backup directory: {self.backup_dir}")
    
    def migrate_all_json_files(self, create_backups: bool = True) -> MigrationSummary:
        """
        Migrate all JSON files to database
        
        Args:
            create_backups: Whether to create backup copies
            
        Returns:
            MigrationSummary: Summary of migration results
        """
        start_time = datetime.now()
        
        logger.info("🔄 Starting migration of all JSON files to database")
        
        results = []
        total_leads_processed = 0
        total_leads_migrated = 0
        total_leads_failed = 0
        total_duplicates_merged = 0
        backups_created = []
        all_errors = []
        
        # Process each JSON file
        for json_file in self.json_files:
            file_path = self.shared_dir / json_file
            
            if file_path.exists():
                logger.info(f"📁 Processing {json_file}...")
                
                try:
                    result = self.migrate_json_file(str(file_path), create_backups)
                    results.append(result)
                    
                    total_leads_processed += result.leads_processed
                    total_leads_migrated += result.leads_migrated
                    total_leads_failed += result.leads_failed
                    total_duplicates_merged += result.leads_duplicates
                    
                    if result.backup_created and result.backup_path:
                        backups_created.append(result.backup_path)
                    
                    all_errors.extend(result.errors)
                    
                    logger.info(f"✅ {json_file}: {result.leads_migrated} migrated, "
                               f"{result.leads_duplicates} duplicates, {result.leads_failed} failed")
                    
                except Exception as e:
                    error_msg = f"Failed to migrate {json_file}: {str(e)}"
                    logger.error(error_msg)
                    all_errors.append(error_msg)
            else:
                logger.info(f"⏭️ Skipping {json_file} (not found)")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create migration summary
        summary = MigrationSummary(
            total_files_processed=len(results),
            total_leads_processed=total_leads_processed,
            total_leads_migrated=total_leads_migrated,
            total_leads_failed=total_leads_failed,
            total_duplicates_merged=total_duplicates_merged,
            total_duration_seconds=duration,
            backups_created=backups_created,
            errors=all_errors,
            success=total_leads_failed == 0 and len(all_errors) == 0
        )
        
        # Log migration to database
        self._log_migration_to_database(summary)
        
        logger.info(f"🎉 Migration completed in {duration:.2f}s")
        logger.info(f"📊 Summary: {total_leads_migrated} migrated, "
                   f"{total_duplicates_merged} duplicates, {total_leads_failed} failed")
        
        return summary
    
    def migrate_json_file(self, file_path: str, create_backup: bool = True) -> MigrationResult:
        """
        Migrate a single JSON file to database
        
        Args:
            file_path: Path to JSON file
            create_backup: Whether to create backup
            
        Returns:
            MigrationResult: Migration results
        """
        start_time = datetime.now()
        file_path = Path(file_path)
        
        logger.info(f"📁 Migrating {file_path.name}...")
        
        # Initialize result
        result = MigrationResult(
            source_file=str(file_path),
            leads_processed=0,
            leads_migrated=0,
            leads_failed=0,
            leads_duplicates=0,
            errors=[],
            duration_seconds=0,
            backup_created=False
        )
        
        try:
            # Create backup if requested
            if create_backup:
                backup_path = self._create_backup(file_path)
                result.backup_created = True
                result.backup_path = backup_path
                logger.info(f"💾 Backup created: {backup_path}")
            
            # Load JSON data
            leads_data = self._load_json_file(file_path)
            
            if not leads_data:
                logger.warning(f"⚠️ No data found in {file_path.name}")
                return result
            
            if not isinstance(leads_data, list):
                error_msg = f"Invalid JSON format in {file_path.name}: expected list, got {type(leads_data)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            result.leads_processed = len(leads_data)
            logger.info(f"📊 Found {len(leads_data)} leads in {file_path.name}")
            
            # Process each lead
            for i, lead_data in enumerate(leads_data):
                try:
                    # Validate and clean lead data
                    cleaned_lead = self._clean_lead_data(lead_data, file_path.name)
                    
                    if not cleaned_lead.get('full_name'):
                        error_msg = f"Lead {i+1} missing required field 'full_name'"
                        logger.warning(error_msg)
                        result.errors.append(error_msg)
                        result.leads_failed += 1
                        continue
                    
                    # Check if this is a duplicate before adding
                    duplicates = self.db.find_all_duplicates(cleaned_lead)
                    
                    if duplicates:
                        # This will be merged by the database
                        result.leads_duplicates += 1
                        logger.debug(f"Duplicate detected for {cleaned_lead['full_name']}")
                    
                    # Add to database (handles duplicates automatically)
                    lead_id = self.db.add_lead(cleaned_lead)
                    result.leads_migrated += 1
                    
                    if i % 100 == 0 and i > 0:
                        logger.info(f"📈 Processed {i} leads...")
                    
                except Exception as e:
                    error_msg = f"Failed to migrate lead {i+1}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.leads_failed += 1
            
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Migration completed: {result.leads_migrated} migrated, "
                       f"{result.leads_duplicates} duplicates, {result.leads_failed} failed")
            
            return result
            
        except Exception as e:
            error_msg = f"Migration failed for {file_path.name}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            return result
    
    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate migration results by comparing JSON files with database
        
        Returns:
            dict: Validation results
        """
        logger.info("🔍 Validating migration results...")
        
        validation_results = {
            'total_json_leads': 0,
            'total_db_leads': 0,
            'files_checked': 0,
            'validation_errors': [],
            'success': True
        }
        
        try:
            # Count leads in database
            db_count = self.db.get_lead_count()
            validation_results['total_db_leads'] = db_count
            
            # Count leads in JSON files
            json_lead_count = 0
            unique_leads = set()  # Track unique leads to account for duplicates
            
            for json_file in self.json_files:
                file_path = self.shared_dir / json_file
                
                if file_path.exists():
                    try:
                        leads_data = self._load_json_file(file_path)
                        
                        if isinstance(leads_data, list):
                            validation_results['files_checked'] += 1
                            
                            for lead in leads_data:
                                # Create unique identifier for deduplication
                                identifier = self._create_lead_identifier(lead)
                                if identifier:
                                    unique_leads.add(identifier)
                                    json_lead_count += 1
                    
                    except Exception as e:
                        error_msg = f"Error validating {json_file}: {str(e)}"
                        validation_results['validation_errors'].append(error_msg)
            
            validation_results['total_json_leads'] = len(unique_leads)
            
            # Compare counts (allowing for some variance due to duplicates and data cleaning)
            if db_count == 0:
                validation_results['validation_errors'].append("No leads found in database")
                validation_results['success'] = False
            elif abs(db_count - len(unique_leads)) > len(unique_leads) * 0.1:  # Allow 10% variance
                warning_msg = f"Significant difference: {len(unique_leads)} unique JSON leads vs {db_count} DB leads"
                validation_results['validation_errors'].append(warning_msg)
            
            logger.info(f"📊 Validation: {len(unique_leads)} unique JSON leads, {db_count} DB leads")
            
            return validation_results
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(error_msg)
            validation_results['validation_errors'].append(error_msg)
            validation_results['success'] = False
            return validation_results
    
    def create_rollback_script(self) -> str:
        """
        Create a rollback script to restore JSON files
        
        Returns:
            str: Path to rollback script
        """
        rollback_script_path = self.backup_dir / f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
        rollback_script = f'''#!/usr/bin/env python3
"""
Rollback Script - Generated on {datetime.now().isoformat()}

This script restores JSON files from backups and clears the database.
USE WITH CAUTION - This will delete all database data!
"""

import os
import shutil
from pathlib import Path

def rollback_migration():
    """Rollback migration by restoring JSON files and clearing database"""
    
    backup_dir = Path("{self.backup_dir}")
    shared_dir = Path("{self.shared_dir}")
    
    print("⚠️  WARNING: This will restore JSON files and clear the database!")
    confirm = input("Type 'ROLLBACK' to confirm: ")
    
    if confirm != 'ROLLBACK':
        print("❌ Rollback cancelled")
        return False
    
    try:
        # Find latest backups
        backup_files = list(backup_dir.glob("*_backup_*.json"))
        
        if not backup_files:
            print("❌ No backup files found")
            return False
        
        # Group backups by original filename
        backups_by_file = {{}}
        for backup_file in backup_files:
            original_name = backup_file.name.split('_backup_')[0] + '.json'
            if original_name not in backups_by_file:
                backups_by_file[original_name] = []
            backups_by_file[original_name].append(backup_file)
        
        # Restore latest backup for each file
        restored_count = 0
        for original_name, backup_list in backups_by_file.items():
            latest_backup = max(backup_list, key=lambda x: x.stat().st_mtime)
            target_path = shared_dir / original_name
            
            print(f"📁 Restoring {{original_name}} from {{latest_backup.name}}")
            shutil.copy2(latest_backup, target_path)
            restored_count += 1
        
        print(f"✅ Restored {{restored_count}} JSON files")
        
        # Clear database (you'll need to implement this based on your needs)
        print("⚠️  Database clearing not implemented in this script")
        print("   Please manually clear the database if needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {{e}}")
        return False

if __name__ == "__main__":
    rollback_migration()
'''
        
        with open(rollback_script_path, 'w', encoding='utf-8') as f:
            f.write(rollback_script)
        
        # Make script executable
        os.chmod(rollback_script_path, 0o755)
        
        logger.info(f"📜 Rollback script created: {rollback_script_path}")
        return str(rollback_script_path)
    
    def _create_backup(self, file_path: Path) -> str:
        """
        Create backup of JSON file
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            str: Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        
        return str(backup_path)
    
    def _load_json_file(self, file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """
        Load JSON file with error handling
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            list: JSON data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            return None
    
    def _clean_lead_data(self, lead_data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """
        Clean and normalize lead data for database insertion
        
        Args:
            lead_data: Raw lead data
            source_file: Source file name
            
        Returns:
            dict: Cleaned lead data
        """
        cleaned = {}
        
        # Map common field variations
        field_mappings = {
            'full_name': ['full_name', 'name', 'Full Name', 'Name'],
            'email': ['email', 'Email', 'email_address'],
            'company': ['company', 'Company', 'company_name'],
            'title': ['title', 'Title', 'job_title', 'position'],
            'linkedin_url': ['linkedin_url', 'LinkedIn URL', 'linkedin', 'profile_url'],
            'location': ['location', 'Location', 'city', 'address'],
            'industry': ['industry', 'Industry', 'sector'],
            'verified': ['verified', 'Verified', 'is_verified'],
            'enriched': ['enriched', 'Enriched', 'is_enriched'],
            'status': ['status', 'Status', 'lead_status'],
            'source': ['source', 'Source', 'data_source']
        }
        
        # Map fields
        for target_field, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in lead_data and lead_data[field] is not None:
                    cleaned[target_field] = lead_data[field]
                    break
        
        # Handle boolean fields
        boolean_fields = ['verified', 'enriched', 'needs_enrichment']
        for field in boolean_fields:
            if field in cleaned:
                if isinstance(cleaned[field], str):
                    cleaned[field] = cleaned[field].lower() in ['true', '1', 'yes', 'verified', 'enriched']
                else:
                    cleaned[field] = bool(cleaned[field])
        
        # Handle datetime fields
        datetime_fields = ['scraped_at', 'enriched_at', 'created_at', 'updated_at']
        for field in datetime_fields:
            if field in lead_data and lead_data[field]:
                # Keep as string - database will handle conversion
                cleaned[field] = str(lead_data[field])
        
        # Add source information
        if not cleaned.get('source'):
            cleaned['source'] = f"Migrated from {source_file}"
        else:
            cleaned['source'] = f"{cleaned['source']} (from {source_file})"
        
        # Preserve additional data in raw_data
        excluded_fields = set(field_mappings.keys()) | set(datetime_fields) | {'raw_data'}
        additional_data = {k: v for k, v in lead_data.items() if k not in excluded_fields}
        
        if additional_data:
            cleaned['raw_data'] = additional_data
        
        return cleaned
    
    def _create_lead_identifier(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Create unique identifier for lead deduplication
        
        Args:
            lead_data: Lead data
            
        Returns:
            str: Unique identifier or None
        """
        # Try LinkedIn URL first
        linkedin_url = lead_data.get('linkedin_url') or lead_data.get('LinkedIn URL')
        if linkedin_url:
            return f"linkedin:{linkedin_url}"
        
        # Try email
        email = lead_data.get('email') or lead_data.get('Email')
        if email:
            return f"email:{email.lower()}"
        
        # Try name + company
        name = lead_data.get('full_name') or lead_data.get('name') or lead_data.get('Full Name')
        company = lead_data.get('company') or lead_data.get('Company')
        
        if name and company:
            return f"name_company:{name.lower()}:{company.lower()}"
        
        return None
    
    def _log_migration_to_database(self, summary: MigrationSummary):
        """
        Log migration summary to database
        
        Args:
            summary: Migration summary
        """
        try:
            # Log to migration_log table
            log_query = """
                INSERT INTO migration_log (
                    source_file, leads_migrated, leads_failed, 
                    migration_date, status, error_details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            status = 'completed' if summary.success else 'failed'
            error_details = '; '.join(summary.errors) if summary.errors else None
            
            params = (
                f"Migration of {summary.total_files_processed} files",
                summary.total_leads_migrated,
                summary.total_leads_failed,
                datetime.now().isoformat(),
                status,
                error_details
            )
            
            self.db.db_conn.execute_update(log_query, params)
            
            logger.info("📝 Migration logged to database")
            
        except Exception as e:
            logger.error(f"Failed to log migration to database: {e}")


def main():
    """
    Main function for standalone migration execution
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate JSON files to database')
    parser.add_argument('--shared-dir', help='Directory containing JSON files')
    parser.add_argument('--backup-dir', help='Directory for backups')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--validate', action='store_true', help='Validate migration only')
    parser.add_argument('--rollback-script', action='store_true', help='Create rollback script')
    
    args = parser.parse_args()
    
    try:
        # Initialize migration manager
        migration_manager = MigrationManager(args.shared_dir, args.backup_dir)
        
        if args.validate:
            # Validate existing migration
            validation = migration_manager.validate_migration()
            
            print(f"\\n📊 Migration Validation Results:")
            print(f"   Files checked: {validation['files_checked']}")
            print(f"   JSON leads: {validation['total_json_leads']}")
            print(f"   Database leads: {validation['total_db_leads']}")
            
            if validation['validation_errors']:
                print(f"\\n⚠️ Validation Issues:")
                for error in validation['validation_errors']:
                    print(f"   • {error}")
            
            if validation['success']:
                print("\\n✅ Migration validation passed!")
            else:
                print("\\n❌ Migration validation failed!")
            
            return
        
        if args.rollback_script:
            # Create rollback script
            script_path = migration_manager.create_rollback_script()
            print(f"\\n📜 Rollback script created: {script_path}")
            return
        
        # Perform migration
        print("🔄 Starting JSON to Database Migration")
        print("=" * 40)
        
        summary = migration_manager.migrate_all_json_files(not args.no_backup)
        
        # Print summary
        print(f"\\n📊 Migration Summary:")
        print(f"   Files processed: {summary.total_files_processed}")
        print(f"   Leads processed: {summary.total_leads_processed}")
        print(f"   Leads migrated: {summary.total_leads_migrated}")
        print(f"   Duplicates merged: {summary.total_duplicates_merged}")
        print(f"   Failed: {summary.total_leads_failed}")
        print(f"   Duration: {summary.total_duration_seconds:.2f}s")
        
        if summary.backups_created:
            print(f"\\n💾 Backups created:")
            for backup in summary.backups_created:
                print(f"   • {backup}")
        
        if summary.errors:
            print(f"\\n⚠️ Errors:")
            for error in summary.errors:
                print(f"   • {error}")
        
        if summary.success:
            print("\\n✅ Migration completed successfully!")
            
            # Validate migration
            validation = migration_manager.validate_migration()
            if validation['success']:
                print("✅ Migration validation passed!")
            else:
                print("⚠️ Migration validation had issues - check logs")
        else:
            print("\\n❌ Migration completed with errors!")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Migration cancelled by user")
    except Exception as e:
        print(f"\\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()