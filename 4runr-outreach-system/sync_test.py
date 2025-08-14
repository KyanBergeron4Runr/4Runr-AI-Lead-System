#!/usr/bin/env python3
"""
Simple sync test to verify database to Airtable synchronization
"""

import sys
from pathlib import Path

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

from data_synchronizer import DataSynchronizer

def main():
    print("🔄 Testing Database to Airtable Sync...")
    
    # Create synchronizer
    synchronizer = DataSynchronizer()
    
    # Check current state
    print("\n📊 Current State:")
    validation = synchronizer.validate_sync_integrity()
    print(f"Local Database: {validation.local_count} records")
    print(f"Airtable: {validation.airtable_count} records")
    print(f"Matched: {validation.matched_records} records")
    print(f"Unmatched Local: {validation.unmatched_local} records")
    print(f"Unmatched Airtable: {validation.unmatched_airtable} records")
    
    if validation.local_count > 0:
        print(f"\n🚀 Syncing {validation.local_count} local records to Airtable...")
        
        # Perform sync (dry run first)
        print("Dry run:")
        dry_result = synchronizer.sync_database_to_airtable(dry_run=True)
        print(f"Would create: {dry_result.records_created} records")
        print(f"Would update: {dry_result.records_updated} records")
        print(f"Would skip: {dry_result.records_skipped} records")
        
        if dry_result.errors:
            print(f"Errors: {dry_result.errors}")
        
        # Ask for confirmation
        if dry_result.records_created > 0 or dry_result.records_updated > 0:
            response = input(f"\nProceed with live sync? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                print("Performing live sync...")
                live_result = synchronizer.sync_database_to_airtable(dry_run=False)
                print(f"✅ Created: {live_result.records_created} records")
                print(f"✅ Updated: {live_result.records_updated} records")
                print(f"⏭️ Skipped: {live_result.records_skipped} records")
                
                if live_result.errors:
                    print(f"❌ Errors: {live_result.errors}")
            else:
                print("Sync cancelled.")
        else:
            print("No sync needed - all records are already synchronized.")
    else:
        print("❌ No records found in local database!")
    
    print("\n✅ Sync test completed!")

if __name__ == "__main__":
    main()