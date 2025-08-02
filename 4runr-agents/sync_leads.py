#!/usr/bin/env python3
"""
Sync Leads Script

Simple script to sync leads between Airtable and local cache.
Run this to initially load your leads or to refresh the cache.
"""

import os
import sys
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from cache.lead_cache import LeadCache
from cache.sync_manager import SyncManager

def main():
    """Main sync function"""
    
    print("🔄 4Runr Lead Sync")
    print("=" * 30)
    
    try:
        # Initialize cache
        print("📂 Initializing lead cache...")
        cache = LeadCache()
        
        # Get Airtable client
        print("🔗 Connecting to Airtable...")
        from airtable_client import get_airtable_client
        airtable_client = get_airtable_client()
        
        # Initialize sync manager
        sync_manager = SyncManager(airtable_client, cache)
        
        # Show current stats
        stats = cache.get_cache_stats()
        print(f"📊 Current cache: {stats['total_leads']} leads, {stats['pending_sync']} pending sync")
        
        # Ask what to do
        print("\nWhat would you like to do?")
        print("1. Pull leads from Airtable (refresh cache)")
        print("2. Push changes to Airtable")
        print("3. Bidirectional sync (recommended)")
        print("4. Show cache statistics")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n📥 Pulling leads from Airtable...")
            result = sync_manager.pull_from_airtable()
            
            if result['success']:
                print(f"✅ Success! Processed {result['leads_processed']} leads in {result['duration_seconds']}s")
                print(f"   Created: {result['leads_created']}, Updated: {result['leads_updated']}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "2":
            pending = sync_manager.get_pending_sync_count()
            if pending == 0:
                print("✅ No changes to push to Airtable")
            else:
                print(f"\n📤 Pushing {pending} changes to Airtable...")
                result = sync_manager.push_to_airtable()
                
                if result['success']:
                    print(f"✅ Success! Synced {result['records_synced']} records in {result['duration_seconds']}s")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        elif choice == "3":
            print("\n🔄 Running bidirectional sync...")
            result = sync_manager.sync_bidirectional()
            
            if result['overall_success']:
                print(f"✅ Success! Bidirectional sync completed in {result['duration_seconds']}s")
            else:
                print(f"⚠️ Partial success. Check results:")
                print(f"   Pull: {'✅' if result['pull_result']['success'] else '❌'}")
                print(f"   Push: {'✅' if result['push_result']['success'] else '❌'}")
        
        elif choice == "4":
            print("\n📊 Cache Statistics:")
            stats = cache.get_cache_stats()
            print(f"   Total leads: {stats['total_leads']}")
            print(f"   By status: {stats['status_counts']}")
            print(f"   Pending sync: {stats['pending_sync']}")
            print(f"   Last sync: {stats['last_sync'] or 'Never'}")
            print(f"   Cache fresh: {'Yes' if stats['cache_fresh'] else 'No'}")
        
        else:
            print("❌ Invalid choice")
            return
        
        # Show final stats
        print("\n📊 Final cache statistics:")
        final_stats = cache.get_cache_stats()
        print(f"   Total leads: {final_stats['total_leads']}")
        print(f"   Pending sync: {final_stats['pending_sync']}")
        
        print(f"\n💾 Database location: {cache.db_path}")
        
    except ImportError:
        print("❌ Could not import airtable_client")
        print("💡 Make sure your Airtable client is set up in the shared directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()