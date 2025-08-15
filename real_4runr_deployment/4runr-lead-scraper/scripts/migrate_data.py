#!/usr/bin/env python3
"""
Data Migration Tool

Consolidates data from existing 4runr-agents and 4runr-lead-system databases
into the unified 4runr-lead-scraper database.
"""

import os
import sys
import json
import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import with absolute paths to avoid relative import issues
import importlib.util
import sqlite3

def load_module_from_path(module_name, file_path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load modules
base_path = Path(__file__).parent.parent
models_module = load_module_from_path("models", base_path / "database" / "models.py")
settings_module = load_module_from_path("settings", base_path / "config" / "settings.py")

get_lead_database = models_module.get_lead_database
Lead = models_module.Lead
get_settings = settings_module.get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data-migration')

@dataclass
class MigrationSource:
    """Represents a data source for migration."""
    name: str
    path: str
    type: str  # 'sqlite', 'json'
    description: str

@dataclass
class MigrationResult:
    """Results of a migration operation."""
    source_name: str
    leads_found: int
    leads_migrated: int
    leads_merged: int
    leads_skipped: int
    errors: List[str]
    success: bool

class DataMigrationTool:
    """
    Tool for migrating and consolidating lead data from multiple sources.
    """
    
    def __init__(self):
        """Initialize the migration tool."""
        self.settings = get_settings()
        self.target_db = get_lead_database()
        
        # Migration tracking
        self.migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir = Path("backups") / self.migration_id
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔄 Data Migration Tool initialized")
        logger.info(f"📁 Backup directory: {self.backup_dir}")
    
    def discover_existing_databases(self) -> List[MigrationSource]:
        """
        Discover all existing database files that can be migrated.
        
        Returns:
            List of migration sources
        """
        logger.info("🔍 Discovering existing databases...")
        
        sources = []
        
        # Define potential database locations
        potential_sources = [
            # 4runr-agents databases
            MigrationSource(
                name="4runr-agents-main",
                path="4runr-agents/data/leads.db",
                type="sqlite",
                description="Main 4runr-agents database"
            ),
            MigrationSource(
                name="4runr-agents-cache",
                path="4runr-agents/data/leads_cache.db",
                type="sqlite",
                description="4runr-agents cache database"
            ),
            
            # 4runr-brain database
            MigrationSource(
                name="4runr-brain-leads",
                path="4runr-brain/data/leads.db",
                type="sqlite",
                description="4runr-brain leads database"
            ),
            
            # 4runr-outreach-system databases
            MigrationSource(
                name="4runr-outreach-cache",
                path="4runr-outreach-system/data/leads_cache.db",
                type="sqlite",
                description="4runr-outreach-system cache database"
            ),
            MigrationSource(
                name="4runr-outreach-campaigns",
                path="4runr-outreach-system/campaign_system/campaigns.db",
                type="sqlite",
                description="4runr-outreach-system campaigns database"
            ),
            
            # Root level databases
            MigrationSource(
                name="root-cache",
                path="data/leads_cache.db",
                type="sqlite",
                description="Root level cache database"
            ),
            
            # JSON files from 4runr-agents
            MigrationSource(
                name="4runr-agents-json-raw",
                path="4runr-agents/shared/raw_leads.json",
                type="json",
                description="Raw leads JSON file"
            ),
            MigrationSource(
                name="4runr-agents-json-enriched",
                path="4runr-agents/shared/enriched_leads.json",
                type="json",
                description="Enriched leads JSON file"
            ),
            MigrationSource(
                name="4runr-agents-json-custom",
                path="4runr-agents/shared/custom_enriched_leads.json",
                type="json",
                description="Custom enriched leads JSON file"
            )
        ]
        
        # Check which sources exist
        for source in potential_sources:
            if os.path.exists(source.path):
                sources.append(source)
                logger.info(f"✅ Found: {source.name} at {source.path}")
            else:
                logger.debug(f"⚠️ Not found: {source.name} at {source.path}")
        
        logger.info(f"🔍 Discovery complete: {len(sources)} sources found")
        return sources
    
    def migrate_all_data(self, sources: List[MigrationSource] = None) -> Dict[str, Any]:
        """
        Migrate data from all discovered sources.
        
        Args:
            sources: Optional list of specific sources to migrate
            
        Returns:
            Migration summary
        """
        if sources is None:
            sources = self.discover_existing_databases()
        
        if not sources:
            logger.info("ℹ️ No data sources found to migrate")
            return {
                'success': True,
                'sources_processed': 0,
                'total_leads_migrated': 0,
                'total_leads_merged': 0,
                'migration_id': self.migration_id
            }
        
        logger.info(f"🚀 Starting migration of {len(sources)} sources...")
        
        # Create backups first
        self._create_backups(sources)
        
        # Process each source
        results = []
        total_migrated = 0
        total_merged = 0
        
        for source in sources:
            logger.info(f"📋 Processing source: {source.name}")
            
            try:
                if source.type == "sqlite":
                    result = self._migrate_sqlite_database(source)
                elif source.type == "json":
                    result = self._migrate_json_file(source)
                else:
                    logger.warning(f"⚠️ Unknown source type: {source.type}")
                    continue
                
                results.append(result)
                total_migrated += result.leads_migrated
                total_merged += result.leads_merged
                
                if result.success:
                    logger.info(f"✅ {source.name}: {result.leads_migrated} migrated, {result.leads_merged} merged")
                else:
                    logger.error(f"❌ {source.name}: Migration failed")
                    for error in result.errors:
                        logger.error(f"   Error: {error}")
                
            except Exception as e:
                logger.error(f"❌ Failed to migrate {source.name}: {str(e)}")
                results.append(MigrationResult(
                    source_name=source.name,
                    leads_found=0,
                    leads_migrated=0,
                    leads_merged=0,
                    leads_skipped=0,
                    errors=[str(e)],
                    success=False
                ))
        
        # Generate migration report
        report = self._generate_migration_report(results)
        
        # Log to database
        self._log_migration_to_database(results, total_migrated, total_merged)
        
        logger.info(f"🎯 Migration complete: {total_migrated} leads migrated, {total_merged} merged")
        
        return {
            'success': all(r.success for r in results),
            'sources_processed': len(results),
            'total_leads_migrated': total_migrated,
            'total_leads_merged': total_merged,
            'results': [self._result_to_dict(r) for r in results],
            'migration_id': self.migration_id,
            'backup_directory': str(self.backup_dir),
            'report_file': report
        }
    
    def _migrate_sqlite_database(self, source: MigrationSource) -> MigrationResult:
        """
        Migrate data from a SQLite database.
        
        Args:
            source: Migration source
            
        Returns:
            Migration result
        """
        result = MigrationResult(
            source_name=source.name,
            leads_found=0,
            leads_migrated=0,
            leads_merged=0,
            leads_skipped=0,
            errors=[],
            success=False
        )
        
        try:
            # Connect to source database
            conn = sqlite3.connect(source.path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if leads table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            if not cursor.fetchone():
                result.errors.append("No 'leads' table found in database")
                return result
            
            # Get all leads from source
            cursor.execute("SELECT * FROM leads")
            rows = cursor.fetchall()
            result.leads_found = len(rows)
            
            logger.info(f"📊 Found {result.leads_found} leads in {source.name}")
            
            # Process each lead
            for row in rows:
                try:
                    lead_data = dict(row)
                    
                    # Convert to our format
                    normalized_lead = self._normalize_lead_data(lead_data, source.name)
                    
                    # Check for duplicates and merge
                    merge_result = self._merge_or_create_lead(normalized_lead)
                    
                    if merge_result['action'] == 'created':
                        result.leads_migrated += 1
                    elif merge_result['action'] == 'merged':
                        result.leads_merged += 1
                    else:
                        result.leads_skipped += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process lead: {str(e)}")
                    result.errors.append(f"Lead processing error: {str(e)}")
            
            conn.close()
            result.success = True
            
        except Exception as e:
            result.errors.append(f"Database migration error: {str(e)}")
            logger.error(f"❌ SQLite migration failed for {source.name}: {str(e)}")
        
        return result
    
    def _migrate_json_file(self, source: MigrationSource) -> MigrationResult:
        """
        Migrate data from a JSON file.
        
        Args:
            source: Migration source
            
        Returns:
            Migration result
        """
        result = MigrationResult(
            source_name=source.name,
            leads_found=0,
            leads_migrated=0,
            leads_merged=0,
            leads_skipped=0,
            errors=[],
            success=False
        )
        
        try:
            # Read JSON file
            with open(source.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                leads = data
            elif isinstance(data, dict) and 'leads' in data:
                leads = data['leads']
            else:
                result.errors.append("Unknown JSON structure")
                return result
            
            result.leads_found = len(leads)
            logger.info(f"📊 Found {result.leads_found} leads in {source.name}")
            
            # Process each lead
            for lead_data in leads:
                try:
                    # Convert to our format
                    normalized_lead = self._normalize_lead_data(lead_data, source.name)
                    
                    # Check for duplicates and merge
                    merge_result = self._merge_or_create_lead(normalized_lead)
                    
                    if merge_result['action'] == 'created':
                        result.leads_migrated += 1
                    elif merge_result['action'] == 'merged':
                        result.leads_merged += 1
                    else:
                        result.leads_skipped += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process lead: {str(e)}")
                    result.errors.append(f"Lead processing error: {str(e)}")
            
            result.success = True
            
        except Exception as e:
            result.errors.append(f"JSON migration error: {str(e)}")
            logger.error(f"❌ JSON migration failed for {source.name}: {str(e)}")
        
        return result
    
    def _normalize_lead_data(self, lead_data: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """
        Normalize lead data to our standard format.
        
        Args:
            lead_data: Raw lead data
            source_name: Name of the source
            
        Returns:
            Normalized lead data
        """
        # Map common field variations
        field_mappings = {
            'name': ['name', 'full_name', 'Full Name', 'Name'],
            'email': ['email', 'Email'],
            'company': ['company', 'Company'],
            'title': ['title', 'job_title', 'Job Title', 'Title'],
            'linkedin_url': ['linkedin_url', 'LinkedIn URL', 'linkedin'],
            'phone': ['phone', 'Phone'],
            'location': ['location', 'Location'],
            'company_website': ['company_website', 'website', 'Company Website'],
            'scraped_at': ['scraped_at', 'created_at', 'Date Scraped'],
            'enriched': ['enriched', 'Enriched'],
            'status': ['status', 'Status']
        }
        
        normalized = {}
        
        # Map fields
        for target_field, source_fields in field_mappings.items():
            for source_field in source_fields:
                if source_field in lead_data and lead_data[source_field]:
                    normalized[target_field] = lead_data[source_field]
                    break
        
        # Set defaults
        normalized.setdefault('scraped_at', datetime.now().isoformat())
        normalized.setdefault('scraping_source', 'migration')
        normalized.setdefault('status', 'scraped')
        normalized.setdefault('enriched', False)
        normalized.setdefault('verified', False)
        normalized.setdefault('ready_for_outreach', False)
        
        # Add migration metadata
        normalized['migration_source'] = source_name
        normalized['migrated_at'] = datetime.now().isoformat()
        
        return normalized
    
    def _merge_or_create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Merge lead with existing data or create new lead.
        
        Args:
            lead_data: Normalized lead data
            
        Returns:
            Dictionary with action taken ('created', 'merged', 'skipped')
        """
        # Look for existing leads by email or LinkedIn URL
        existing_lead = None
        
        # First try email
        if lead_data.get('email'):
            existing_leads = self.target_db.search_leads({'email': lead_data['email']}, limit=1)
            if existing_leads:
                existing_lead = existing_leads[0]
        
        # Then try LinkedIn URL
        if not existing_lead and lead_data.get('linkedin_url'):
            existing_leads = self.target_db.search_leads({'linkedin_url': lead_data['linkedin_url']}, limit=1)
            if existing_leads:
                existing_lead = existing_leads[0]
        
        if existing_lead:
            # Merge data
            merged_data = self._merge_lead_data(existing_lead.to_dict(), lead_data)
            
            # Update existing lead
            success = self.target_db.update_lead(existing_lead.id, merged_data)
            
            if success:
                return {'action': 'merged', 'lead_id': existing_lead.id}
            else:
                return {'action': 'skipped', 'reason': 'update_failed'}
        else:
            # Create new lead
            try:
                lead_id = self.target_db.create_lead(lead_data)
                return {'action': 'created', 'lead_id': lead_id}
            except Exception as e:
                logger.warning(f"⚠️ Failed to create lead: {str(e)}")
                return {'action': 'skipped', 'reason': str(e)}
    
    def _merge_lead_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge lead data, preferring more complete information.
        
        Args:
            existing_data: Existing lead data
            new_data: New lead data to merge
            
        Returns:
            Merged lead data
        """
        merged = {}
        
        # Fields where we prefer non-empty values
        prefer_non_empty = [
            'email', 'phone', 'company_website', 'industry', 'company_size',
            'location', 'title', 'linkedin_url'
        ]
        
        for field in prefer_non_empty:
            existing_value = existing_data.get(field)
            new_value = new_data.get(field)
            
            # Prefer non-empty values
            if new_value and not existing_value:
                merged[field] = new_value
            elif existing_value and not new_value:
                # Keep existing (don't add to merged dict)
                pass
            elif new_value and len(str(new_value)) > len(str(existing_value)):
                # Prefer longer/more detailed values
                merged[field] = new_value
        
        # Boolean fields - prefer True values
        boolean_fields = ['enriched', 'verified', 'ready_for_outreach']
        for field in boolean_fields:
            existing_value = existing_data.get(field, False)
            new_value = new_data.get(field, False)
            
            if new_value and not existing_value:
                merged[field] = True
        
        # Always update migration metadata
        merged['updated_at'] = datetime.now().isoformat()
        
        return merged
    
    def _create_backups(self, sources: List[MigrationSource]):
        """Create backups of all source files before migration."""
        logger.info("💾 Creating backups of source files...")
        
        for source in sources:
            if os.path.exists(source.path):
                try:
                    backup_path = self.backup_dir / f"{source.name}_{Path(source.path).name}"
                    shutil.copy2(source.path, backup_path)
                    logger.info(f"💾 Backed up {source.name} to {backup_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to backup {source.name}: {str(e)}")
    
    def _generate_migration_report(self, results: List[MigrationResult]) -> str:
        """Generate detailed migration report."""
        report_path = self.backup_dir / "migration_report.txt"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"4Runr Lead Scraper - Data Migration Report\n")
                f.write(f"Migration ID: {self.migration_id}\n")
                f.write(f"Migration Date: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                
                # Summary
                total_found = sum(r.leads_found for r in results)
                total_migrated = sum(r.leads_migrated for r in results)
                total_merged = sum(r.leads_merged for r in results)
                total_skipped = sum(r.leads_skipped for r in results)
                
                f.write("SUMMARY\n")
                f.write("-" * 20 + "\n")
                f.write(f"Sources Processed: {len(results)}\n")
                f.write(f"Total Leads Found: {total_found}\n")
                f.write(f"Total Leads Migrated: {total_migrated}\n")
                f.write(f"Total Leads Merged: {total_merged}\n")
                f.write(f"Total Leads Skipped: {total_skipped}\n")
                f.write(f"Success Rate: {((total_migrated + total_merged) / total_found * 100):.1f}%\n\n")
                
                # Detailed results
                f.write("DETAILED RESULTS\n")
                f.write("-" * 20 + "\n")
                
                for result in results:
                    f.write(f"\nSource: {result.source_name}\n")
                    f.write(f"  Status: {'SUCCESS' if result.success else 'FAILED'}\n")
                    f.write(f"  Leads Found: {result.leads_found}\n")
                    f.write(f"  Leads Migrated: {result.leads_migrated}\n")
                    f.write(f"  Leads Merged: {result.leads_merged}\n")
                    f.write(f"  Leads Skipped: {result.leads_skipped}\n")
                    
                    if result.errors:
                        f.write(f"  Errors:\n")
                        for error in result.errors:
                            f.write(f"    - {error}\n")
            
            logger.info(f"📄 Migration report saved to {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate migration report: {str(e)}")
            return ""
    
    def _log_migration_to_database(self, results: List[MigrationResult], total_migrated: int, total_merged: int):
        """Log migration operation to database."""
        try:
            migration_details = {
                'migration_id': self.migration_id,
                'sources': [r.source_name for r in results],
                'total_found': sum(r.leads_found for r in results),
                'total_migrated': total_migrated,
                'total_merged': total_merged,
                'success_rate': ((total_migrated + total_merged) / sum(r.leads_found for r in results) * 100) if sum(r.leads_found for r in results) > 0 else 0
            }
            
            query = """
                INSERT INTO migration_log (migration_type, source_system, leads_migrated, leads_merged, migration_details)
                VALUES (?, ?, ?, ?, ?)
            """
            
            self.target_db.db.execute_update(
                query,
                (
                    'data_consolidation',
                    'multiple_sources',
                    total_migrated,
                    total_merged,
                    json.dumps(migration_details)
                )
            )
            
            logger.info("📊 Migration logged to database")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to log migration to database: {str(e)}")
    
    def _result_to_dict(self, result: MigrationResult) -> Dict[str, Any]:
        """Convert MigrationResult to dictionary."""
        return {
            'source_name': result.source_name,
            'leads_found': result.leads_found,
            'leads_migrated': result.leads_migrated,
            'leads_merged': result.leads_merged,
            'leads_skipped': result.leads_skipped,
            'errors': result.errors,
            'success': result.success
        }


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="4Runr Lead Scraper Data Migration Tool")
    parser.add_argument('--discover', action='store_true', help='Discover available data sources')
    parser.add_argument('--migrate', action='store_true', help='Migrate all discovered data')
    parser.add_argument('--source', help='Migrate specific source by name')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without doing it')
    
    args = parser.parse_args()
    
    try:
        migration_tool = DataMigrationTool()
        
        if args.discover:
            sources = migration_tool.discover_existing_databases()
            
            print(f"\n🔍 Discovered {len(sources)} data sources:")
            for source in sources:
                print(f"  📁 {source.name}: {source.path} ({source.type})")
                print(f"     {source.description}")
            
            return 0
        
        elif args.migrate:
            if args.dry_run:
                print("🧪 DRY RUN MODE - No data will be modified")
                sources = migration_tool.discover_existing_databases()
                print(f"Would migrate {len(sources)} sources")
                return 0
            
            result = migration_tool.migrate_all_data()
            
            print(f"\n🎯 Migration Results:")
            print(f"  Sources Processed: {result['sources_processed']}")
            print(f"  Total Leads Migrated: {result['total_leads_migrated']}")
            print(f"  Total Leads Merged: {result['total_leads_merged']}")
            print(f"  Success: {result['success']}")
            print(f"  Backup Directory: {result['backup_directory']}")
            
            if result['report_file']:
                print(f"  Report: {result['report_file']}")
            
            return 0 if result['success'] else 1
        
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())