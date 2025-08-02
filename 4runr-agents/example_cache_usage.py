#!/usr/bin/env python3
"""
Example: How to use the Lead Cache System with Airtable

This shows how to integrate the cache with your existing agents.
"""

import os
import sys
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from cache.lead_cache import LeadCache
from cache.sync_manager import SyncManager

def example_agent_workflow():
    """Example of how an agent would use the cache system"""
    
    print("🤖 Example Agent Workflow with Lead Cache")
    print("=" * 50)
    
    # 1. Initialize cache
    cache = LeadCache()
    
    # 2. Check if cache needs refresh (optional - cache handles this automatically)
    if not cache.is_cache_fresh(max_age_hours=2):
        print("⏰ Cache is stale, would normally sync with Airtable here")
        # In real usage: sync_manager.pull_from_airtable()
    
    # 3. Get leads for processing (FAST - no API calls!)
    print("\n📋 Getting leads for enrichment...")
    leads_to_enrich = cache.get_leads_by_status('scraped')
    print(f"Found {len(leads_to_enrich)} leads ready for enrichment")
    
    # 4. Process leads (example: enrichment)
    for lead in leads_to_enrich[:2]:  # Process first 2 for demo
        print(f"\n🔍 Processing: {lead['name']} at {lead['company']}")
        
        # Simulate enrichment work
        enrichment_data = {
            'Email': f"contact@{lead['company'].lower().replace(' ', '')}.com",
            'Status': 'enriched',
            'Enriched At': datetime.now().isoformat(),
            'Confidence': 'medium'
        }
        
        # Update cache (automatically marks for sync with Airtable)
        success = cache.update_lead(lead['id'], enrichment_data)
        print(f"   {'✅' if success else '❌'} Updated lead with enrichment data")
    
    # 5. Search for specific leads (FAST - local search)
    print("\n🔍 Searching for leads...")
    tech_leads = cache.search_leads('Tech')
    print(f"Found {len(tech_leads)} leads matching 'Tech'")
    
    # 6. Get cache statistics
    print("\n📊 Cache Statistics:")
    stats = cache.get_cache_stats()
    print(f"   Total leads: {stats['total_leads']}")
    print(f"   By status: {stats['status_counts']}")
    print(f"   Pending sync: {stats['pending_sync']} changes waiting for Airtable")
    print(f"   Cache fresh: {'Yes' if stats['cache_fresh'] else 'No'}")
    
    print("\n" + "=" * 50)
    print("✅ Agent workflow complete!")
    print("💡 Key benefits:")
    print("   - Fast lead access (10-50ms vs 500ms+ API calls)")
    print("   - Works offline with cached data")
    print("   - Automatic sync tracking")
    print("   - Persistent across deployments")

def example_with_airtable_sync():
    """Example showing how to integrate with actual Airtable"""
    
    print("\n🔄 Example: Airtable Integration")
    print("=" * 40)
    
    # This is how you'd integrate with your existing Airtable client
    try:
        # Import your existing Airtable client
        from airtable_client import get_airtable_client
        
        # Initialize cache and sync manager
        cache = LeadCache()
        airtable_client = get_airtable_client()
        sync_manager = SyncManager(airtable_client, cache)
        
        print("✅ Airtable client loaded successfully")
        
        # Example sync operations
        print("\n📥 To pull leads from Airtable:")
        print("   result = sync_manager.pull_from_airtable()")
        
        print("\n📤 To push changes to Airtable:")
        print("   result = sync_manager.push_to_airtable()")
        
        print("\n🔄 To do bidirectional sync:")
        print("   result = sync_manager.sync_bidirectional()")
        
        # Show pending sync count
        pending = sync_manager.get_pending_sync_count()
        print(f"\n📊 Currently {pending} changes pending sync to Airtable")
        
    except ImportError:
        print("⚠️ Airtable client not available in this demo")
        print("💡 In your real agents, you would:")
        print("   1. Import your existing airtable_client")
        print("   2. Create SyncManager(airtable_client, cache)")
        print("   3. Use sync_manager.pull_from_airtable() to load data")
        print("   4. Use sync_manager.push_to_airtable() to sync changes")

def example_deployment_usage():
    """Example showing deployment considerations"""
    
    print("\n🚀 Example: Deployment Usage")
    print("=" * 35)
    
    print("💡 For local development:")
    print("   cache = LeadCache()  # Uses data/leads_cache.db")
    
    print("\n🐳 For Docker deployment:")
    print("   # Mount volume: -v /host/data:/app/data")
    print("   # Database persists at /app/data/leads_cache.db")
    
    print("\n☁️ For EC2/server deployment:")
    print("   # Set environment variable:")
    print("   # LEAD_CACHE_DB_PATH=/persistent/storage/leads_cache.db")
    
    print("\n🔄 Automatic sync scheduling:")
    print("   # Add to cron or scheduler:")
    print("   # */2 * * * * python sync_leads.py  # Every 2 hours")

if __name__ == "__main__":
    try:
        # Run examples
        example_agent_workflow()
        example_with_airtable_sync()
        example_deployment_usage()
        
        print("\n🎯 Next Steps:")
        print("1. Update your agents to use LeadCache instead of direct Airtable calls")
        print("2. Set up sync_manager.pull_from_airtable() to load initial data")
        print("3. Schedule periodic syncs with sync_manager.sync_bidirectional()")
        print("4. Deploy with persistent storage for the database file")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()