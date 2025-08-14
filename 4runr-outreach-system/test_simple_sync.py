#!/usr/bin/env python3
"""
Test Simple Sync Manager

This script tests the simple sync manager functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from simple_sync_manager import SimpleSyncManager
from lead_database import LeadDatabase


def test_sync_manager():
    """Test the simple sync manager."""
    print("🧪 Testing Simple Sync Manager")
    print("=" * 50)
    
    try:
        # Initialize sync manager
        sync_manager = SimpleSyncManager()
        print("✅ Sync manager initialized")
        
        # Get sync statistics
        stats = sync_manager.get_sync_stats()
        print(f"📊 Sync stats: {stats}")
        
        # Test sync to Airtable
        print("\n🔄 Testing sync to Airtable...")
        results = sync_manager.sync_to_airtable()
        
        print(f"\n📋 Sync Results:")
        print(f"   Total leads processed: {len(results)}")
        
        successful = sum(1 for r in results if r.status.value == 'success')
        failed = sum(1 for r in results if r.status.value == 'failed')
        
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        
        if results:
            print(f"\n📝 Sample results:")
            for result in results[:3]:  # Show first 3 results
                status_emoji = "✅" if result.status.value == 'success' else "❌"
                print(f"   {status_emoji} Lead {result.lead_id}: {result.status.value}")
                if result.airtable_id:
                    print(f"      Airtable ID: {result.airtable_id}")
                if result.error_message:
                    print(f"      Error: {result.error_message}")
        
        print("\n🎉 Sync test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sync_manager()
    sys.exit(0 if success else 1)
