#!/usr/bin/env python3
"""
Database Maintenance CLI

Command line interface for the database maintenance system.
Provides easy access to cleanup, synchronization, and maintenance operations.
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

from database_maintenance import MaintenanceOrchestrator, MaintenanceOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Maintenance System - Clean up and synchronize your lead data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full maintenance with default settings
  python database_maintenance_cli.py --full-maintenance

  # Remove duplicates only
  python database_maintenance_cli.py --remove-duplicates

  # Standardize engagement status to 'auto_send'
  python database_maintenance_cli.py --standardize-fields --engagement-status auto_send

  # Dry run to see what would be changed
  python database_maintenance_cli.py --full-maintenance --dry-run

  # Custom configuration file
  python database_maintenance_cli.py --full-maintenance --config custom_config.yaml
        """
    )
    
    # Operation modes
    parser.add_argument(
        '--full-maintenance',
        action='store_true',
        help='Run complete maintenance workflow (backup, duplicates, standardization, sync)'
    )
    
    parser.add_argument(
        '--remove-duplicates',
        action='store_true',
        help='Remove duplicate records only'
    )
    
    parser.add_argument(
        '--standardize-fields',
        action='store_true',
        help='Standardize field values only'
    )
    
    parser.add_argument(
        '--sync-data',
        action='store_true',
        help='Synchronize data between database and Airtable only'
    )
    
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Create backups only'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--engagement-status',
        type=str,
        default='auto_send',
        help='Default engagement status to set (default: auto_send)'
    )
    
    parser.add_argument(
        '--matching-fields',
        nargs='+',
        default=['email', 'linkedin_url'],
        help='Fields to use for duplicate matching (default: email linkedin_url)'
    )
    
    parser.add_argument(
        '--conflict-strategy',
        choices=['most_recent', 'highest_quality', 'merge'],
        default='most_recent',
        help='Strategy for resolving conflicts (default: most_recent)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for processing records (default: 50)'
    )
    
    # Operation modifiers
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if not any([args.full_maintenance, args.remove_duplicates, args.standardize_fields, 
                args.sync_data, args.backup_only]):
        parser.error("Must specify at least one operation mode")
    
    # Create maintenance options
    options = MaintenanceOptions(
        backup_before_operation=not args.no_backup,
        remove_duplicates=args.full_maintenance or args.remove_duplicates,
        standardize_fields=args.full_maintenance or args.standardize_fields,
        sync_data=args.full_maintenance or args.sync_data,
        engagement_status_default=args.engagement_status,
        duplicate_matching_fields=args.matching_fields,
        conflict_resolution_strategy=args.conflict_strategy,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Print operation summary
    print("🔧 Database Maintenance System")
    print("=" * 50)
    print(f"Operation Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Backup: {'Yes' if options.backup_before_operation else 'No'}")
    print(f"Remove Duplicates: {'Yes' if options.remove_duplicates else 'No'}")
    print(f"Standardize Fields: {'Yes' if options.standardize_fields else 'No'}")
    print(f"Sync Data: {'Yes' if options.sync_data else 'No'}")
    print(f"Engagement Status Default: {options.engagement_status_default}")
    print(f"Duplicate Matching Fields: {', '.join(options.duplicate_matching_fields)}")
    print(f"Conflict Resolution: {options.conflict_resolution_strategy}")
    print("=" * 50)
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE: No changes will be made")
    else:
        print("⚠️  LIVE MODE: Changes will be made to your data")
        
        # Confirmation prompt for live mode
        response = input("\nDo you want to continue? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("Operation cancelled.")
            return
    
    print("\n🚀 Starting maintenance operation...")
    
    try:
        # Create orchestrator
        orchestrator = MaintenanceOrchestrator(config_path=args.config)
        
        # Handle specific operations
        if args.backup_only:
            print("📦 Creating backups...")
            backup_result = orchestrator._create_backups()
            if backup_result['success']:
                print(f"✅ Backups created successfully:")
                for path in backup_result['backup_paths']:
                    print(f"   - {path}")
            else:
                print(f"❌ Backup failed: {backup_result['errors']}")
                return
        else:
            # Run full or partial maintenance
            result = orchestrator.run_full_maintenance(options)
            
            # Print results
            print(f"\n{'🎉' if result.success else '❌'} Maintenance {'completed successfully' if result.success else 'failed'}")
            print("=" * 50)
            print(f"Duration: {result.duration_seconds:.2f} seconds")
            print(f"Duplicates Removed: {result.duplicates_removed}")
            print(f"Records Standardized: {result.records_standardized}")
            print(f"Records Synchronized: {result.records_synchronized}")
            print(f"Conflicts Resolved: {result.conflicts_resolved}")
            
            if result.backup_paths:
                print(f"\nBackup Files Created:")
                for path in result.backup_paths:
                    print(f"  - {path}")
            
            if result.errors:
                print(f"\n❌ Errors ({len(result.errors)}):")
                for error in result.errors:
                    print(f"  - {error}")
            
            if result.warnings:
                print(f"\n⚠️  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            if not result.success:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ Database maintenance completed!")

if __name__ == "__main__":
    main()