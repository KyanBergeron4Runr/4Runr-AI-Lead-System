"""
Demo script showing how to use the Migration Manager.

This script demonstrates the key features of the migration system:
- Finding JSON files
- Creating backups
- Migrating data to database
- Validating migration results
"""

import json
from migration_manager import MigrationManager

def main():
    """Demonstrate migration manager functionality."""
    print("🔄 Lead Database Migration Demo")
    print("=" * 50)
    
    # Initialize migration manager
    migration_manager = MigrationManager()
    
    # 1. Check migration status
    print("\n📊 Current Migration Status:")
    status = migration_manager.get_migration_status()
    print(f"   Available JSON files: {status['available_json_files']}")
    print(f"   Database leads: {status['database_stats'].get('total_leads', 0)}")
    print(f"   Migration ready: {status['migration_ready']}")
    
    # 2. Find JSON files
    print("\n🔍 Finding JSON Files:")
    json_files = migration_manager.find_json_files()
    if json_files:
        for file in json_files:
            print(f"   Found: {file}")
    else:
        print("   No JSON files found for migration")
        return
    
    # 3. Perform migration
    print("\n🚀 Starting Migration:")
    result = migration_manager.migrate_json_files(create_backup=True)
    
    print(f"   Files processed: {result.total_files}")
    print(f"   Total leads: {result.total_leads}")
    print(f"   Migrated: {result.migrated_leads}")
    print(f"   Failed: {result.failed_leads}")
    print(f"   Backups created: {len(result.backup_paths)}")
    
    if result.errors:
        print("   Errors:")
        for error in result.errors:
            print(f"     - {error}")
    
    # 4. Validate migration
    print("\n✅ Validating Migration:")
    validation = migration_manager.validate_migration()
    print(f"   JSON leads: {validation['total_json_leads']}")
    print(f"   DB leads: {validation['total_db_leads']}")
    print(f"   Matched: {validation['matched_leads']}")
    print(f"   Missing: {len(validation['missing_leads'])}")
    
    print("\n🎉 Migration Demo Complete!")

if __name__ == "__main__":
    main()