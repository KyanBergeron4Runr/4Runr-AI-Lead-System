#!/usr/bin/env python3
"""
Test script for the Local Database Manager functionality.
"""

import sys
import os
import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.local_database_manager import LocalDatabaseManager


def test_database_manager():
    """Test the Local Database Manager functionality."""
    print("🧪 Testing Local Database Manager...")
    
    # Use a test database file
    test_db_path = "data/test_leads_cache.db"
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Test 1: Initialize database manager
    print("\n1. Testing database manager initialization...")
    try:
        db_manager = LocalDatabaseManager(test_db_path)
        print("   ✅ Database manager initialized successfully")
        print(f"   📁 Database path: {test_db_path}")
    except Exception as e:
        print(f"   ❌ Failed to initialize database manager: {e}")
        return False
    
    # Test 2: Test database connection
    print("\n2. Testing database connection...")
    try:
        connection_ok = db_manager.test_database_connection()
        print(f"   {'✅' if connection_ok else '❌'} Database connection test: {connection_ok}")
    except Exception as e:
        print(f"   ❌ Database connection test failed: {e}")
    
    # Test 3: Test engagement data update
    print("\n3. Testing engagement data update...")
    test_lead_id = "test_lead_123"
    engagement_data = {
        'engagement_stage': '2nd degree',
        'previous_stage': '1st degree',
        'last_contacted': datetime.datetime.now().isoformat(),
        'message_sent': 'Test message content',
        'company_summary': 'Test company summary',
        'success': True,
        'airtable_synced': True
    }
    
    try:
        update_success = db_manager.update_engagement_data(test_lead_id, engagement_data)
        print(f"   {'✅' if update_success else '❌'} Engagement data update: {update_success}")
    except Exception as e:
        print(f"   ❌ Engagement data update failed: {e}")
    
    # Test 4: Test engagement history retrieval
    print("\n4. Testing engagement history retrieval...")
    try:
        history = db_manager.get_engagement_history(test_lead_id)
        print(f"   ✅ Retrieved {len(history)} engagement history records")
        if history:
            latest = history[0]
            print(f"   📊 Latest engagement: {latest['engagement_level']} at {latest['contacted_at']}")
    except Exception as e:
        print(f"   ❌ Engagement history retrieval failed: {e}")
    
    # Test 5: Test lead engagement status
    print("\n5. Testing lead engagement status...")
    try:
        status = db_manager.get_lead_engagement_status(test_lead_id)
        if status:
            print(f"   ✅ Lead status retrieved: {status['engagement_stage']}")
        else:
            print("   ⚠️  No lead status found (expected for new test lead)")
    except Exception as e:
        print(f"   ❌ Lead engagement status test failed: {e}")
    
    # Test 6: Add more test data and test statistics
    print("\n6. Testing engagement statistics...")
    try:
        # Add a few more test records
        for i in range(3):
            test_data = {
                'engagement_stage': f'{i+1}st degree' if i == 0 else f'{i+1}nd degree' if i == 1 else f'{i+1}rd degree',
                'last_contacted': datetime.datetime.now().isoformat(),
                'success': i % 2 == 0,  # Alternate success/failure
                'airtable_synced': True
            }
            db_manager.update_engagement_data(f"test_lead_{i+200}", test_data)
        
        stats = db_manager.get_engagement_statistics()
        print(f"   ✅ Statistics retrieved:")
        print(f"      - Total leads: {stats.get('total_leads', 0)}")
        print(f"      - By stage: {stats.get('by_stage', {})}")
        print(f"      - Recent engagements: {stats.get('recent_engagements', 0)}")
        print(f"      - Success rate: {stats.get('success_rate', 0):.2%}")
        print(f"      - Airtable sync rate: {stats.get('airtable_sync_rate', 0):.2%}")
    except Exception as e:
        print(f"   ❌ Engagement statistics test failed: {e}")
    
    # Test 7: Test data export
    print("\n7. Testing data export...")
    try:
        export_data = db_manager.export_engagement_data()
        print(f"   ✅ Exported {len(export_data)} engagement records")
        if export_data:
            print(f"   📄 Sample record keys: {list(export_data[0].keys())}")
    except Exception as e:
        print(f"   ❌ Data export test failed: {e}")
    
    # Test 8: Test cleanup
    print("\n8. Testing cleanup functionality...")
    try:
        # This won't delete anything since our test data is recent
        deleted_count = db_manager.cleanup_old_records(days_to_keep=1)
        print(f"   ✅ Cleanup completed: {deleted_count} old records deleted")
    except Exception as e:
        print(f"   ❌ Cleanup test failed: {e}")
    
    # Clean up test database
    print("\n9. Cleaning up test database...")
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("   ✅ Test database cleaned up")
    except Exception as e:
        print(f"   ⚠️  Failed to clean up test database: {e}")
    
    print("\n🎉 Local Database Manager tests completed!")
    return True


if __name__ == '__main__':
    success = test_database_manager()
    sys.exit(0 if success else 1)