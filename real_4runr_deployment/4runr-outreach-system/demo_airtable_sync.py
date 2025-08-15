"""
Demo script showing how to use the Airtable Sync Manager.

This script demonstrates the key features of the Airtable synchronization system:
- Pushing leads to Airtable
- Pulling leads from Airtable
- Bidirectional sync
- Sync statistics and monitoring
"""

from airtable_sync_manager import AirtableSyncManager

def main():
    """Demonstrate Airtable sync manager functionality."""
    print("🔄 Airtable Sync Manager Demo")
    print("=" * 50)
    
    # Initialize sync manager
    try:
        sync_manager = AirtableSyncManager()
        print("✅ Airtable Sync Manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize sync manager: {e}")
        return
    
    # 1. Get sync statistics
    print("\n📊 Current Sync Statistics:")
    stats = sync_manager.get_sync_statistics()
    if 'error' not in stats:
        print(f"   Total leads in database: {stats['database_stats'].get('total_leads', 0)}")
        print(f"   Leads pending sync: {stats['sync_pending_count']}")
        print(f"   Synced leads: {stats['synced_leads_count']}")
        print(f"   Sync rate: {stats['sync_rate']:.1%}")
    else:
        print(f"   Error getting stats: {stats['error']}")
    
    # 2. Get pending leads
    print("\n🔍 Checking Pending Leads:")
    pending_leads = sync_manager.get_sync_pending_leads()
    print(f"   Found {len(pending_leads)} leads pending sync")
    
    if pending_leads:
        for lead in pending_leads[:3]:  # Show first 3
            print(f"     - {lead.get('full_name', 'Unknown')} ({lead.get('company', 'No company')})")
    
    # 3. Push to Airtable
    print("\n🚀 Pushing Leads to Airtable:")
    if pending_leads:
        push_summary = sync_manager.sync_to_airtable()
        
        print(f"   Total leads processed: {push_summary.total_leads}")
        print(f"   Successfully synced: {push_summary.successful_syncs}")
        print(f"   Failed syncs: {push_summary.failed_syncs}")
        print(f"   Created in Airtable: {push_summary.created_records}")
        print(f"   Updated in Airtable: {push_summary.updated_records}")
        
        if push_summary.errors:
            print("   Errors:")
            for error in push_summary.errors[:3]:  # Show first 3 errors
                print(f"     - {error}")
    else:
        print("   No leads pending sync")
    
    # 4. Pull from Airtable
    print("\n⬇️ Pulling Updates from Airtable:")
    pull_summary = sync_manager.sync_from_airtable(limit=10)  # Limit for demo
    
    print(f"   Total leads processed: {pull_summary.total_leads}")
    print(f"   Successfully synced: {pull_summary.successful_syncs}")
    print(f"   Failed syncs: {pull_summary.failed_syncs}")
    print(f"   Created in database: {pull_summary.created_records}")
    print(f"   Updated in database: {pull_summary.updated_records}")
    
    if pull_summary.errors:
        print("   Errors:")
        for error in pull_summary.errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
    
    # 5. Bidirectional sync
    print("\n🔄 Performing Bidirectional Sync:")
    bidirectional_results = sync_manager.bidirectional_sync(push_limit=5, pull_limit=5)
    
    push_results = bidirectional_results['push']
    pull_results = bidirectional_results['pull']
    
    print(f"   Push Results: {push_results.successful_syncs} successful, {push_results.failed_syncs} failed")
    print(f"   Pull Results: {pull_results.successful_syncs} successful, {pull_results.failed_syncs} failed")
    
    # 6. Final statistics
    print("\n📈 Final Sync Statistics:")
    final_stats = sync_manager.get_sync_statistics()
    if 'error' not in final_stats:
        print(f"   Total leads in database: {final_stats['database_stats'].get('total_leads', 0)}")
        print(f"   Leads pending sync: {final_stats['sync_pending_count']}")
        print(f"   Synced leads: {final_stats['synced_leads_count']}")
        print(f"   Sync rate: {final_stats['sync_rate']:.1%}")
    
    print("\n🎉 Airtable Sync Demo Complete!")
    print("\n💡 Tips:")
    print("   - Use sync_to_airtable() to push local changes to Airtable")
    print("   - Use sync_from_airtable() to pull Airtable updates to local database")
    print("   - Use bidirectional_sync() for complete synchronization")
    print("   - Monitor sync_pending_leads() to track what needs syncing")

if __name__ == "__main__":
    main()