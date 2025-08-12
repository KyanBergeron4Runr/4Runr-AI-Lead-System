#!/usr/bin/env python3
"""
Fix Kyan Bergeron lead with complete data and prevent duplicates.
"""

import sys
import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engager.local_database_manager import LocalDatabaseManager
from shared.logging_utils import get_logger


def fix_kyan_lead():
    """Fix Kyan Bergeron lead with complete data."""
    logger = get_logger('fix_lead')
    
    print("🔧 Fixing Kyan Bergeron Lead Data")
    print("=" * 40)
    
    # Complete Kyan data
    kyan_data = {
        'id': 'recgPdmwmX7xnR91E',  # Use the remaining Airtable ID
        'airtable_id': 'recgPdmwmX7xnR91E',
        'name': 'Kyan Bergeron',
        'full_name': 'Kyan Bergeron',
        'email': 'kyan@4runr.com',
        'company': '4Runr',
        'website': 'https://4runr.com',
        'company_website': 'https://4runr.com',
        'engagement_stage': '1st degree',
        'last_contacted': None,
        'engagement_history': None
    }
    
    try:
        db_manager = LocalDatabaseManager()
        
        # Clean up any existing incomplete records first
        print("\n🧹 Cleaning up incomplete records...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Remove records with no email or name
            cursor.execute("""
                DELETE FROM leads 
                WHERE (email IS NULL OR email = '') 
                AND (name IS NULL OR name = '' OR name = 'Unknown Name')
            """)
            
            deleted_leads = cursor.rowcount
            
            # Remove orphaned engagement tracking
            cursor.execute("""
                DELETE FROM engagement_tracking 
                WHERE lead_id NOT IN (SELECT id FROM leads)
            """)
            
            deleted_tracking = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Removed {deleted_leads} incomplete lead records")
            print(f"   ✅ Removed {deleted_tracking} orphaned tracking records")
        
        # Add Kyan with complete data using upsert
        print(f"\n👤 Adding Kyan Bergeron with complete data...")
        success = db_manager.upsert_lead(kyan_data)
        
        if success:
            print("   ✅ Kyan Bergeron added successfully with complete data")
            
            # Verify the data
            lead_status = db_manager.get_lead_engagement_status(kyan_data['id'])
            if lead_status:
                print(f"\n✅ VERIFICATION:")
                print(f"   👤 Name: {lead_status['name']}")
                print(f"   📧 Email: {lead_status['email']}")
                print(f"   🏢 Company: {lead_status['company']}")
                print(f"   🌐 Website: {lead_status['company_website']}")
                print(f"   📊 Engagement: {lead_status['engagement_stage']}")
                print(f"   🆔 ID: {lead_status['id']}")
            
            # Show updated stats
            stats = db_manager.get_engagement_statistics()
            print(f"\n📊 DATABASE STATS:")
            print(f"   Total leads: {stats.get('total_leads', 0)}")
            print(f"   By stage: {stats.get('by_stage', {})}")
            
        else:
            print("   ❌ Failed to add Kyan Bergeron")
            return False
        
        logger.log_module_activity('fix_lead', 'system', 'success', {
            'message': 'Kyan Bergeron lead fixed successfully',
            'name': kyan_data['name'],
            'email': kyan_data['email'],
            'company': kyan_data['company']
        })
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing lead: {e}")
        logger.log_error(e, {'action': 'fix_kyan_lead'})
        return False


if __name__ == '__main__':
    success = fix_kyan_lead()
    
    if success:
        print("\n🎉 Kyan Bergeron lead fixed successfully!")
        print("   Use: python view_lead_db.py search kyan")
    else:
        print("\n❌ Failed to fix lead!")
        sys.exit(1)