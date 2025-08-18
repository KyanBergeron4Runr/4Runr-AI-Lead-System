#!/usr/bin/env python3
"""
Add Ready For Outreach Column
==============================
Add the missing ready_for_outreach column
"""

import sqlite3
import logging

def add_ready_for_outreach_column():
    """Add the missing ready_for_outreach column"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        
        # Add the missing column
        conn.execute("ALTER TABLE leads ADD COLUMN ready_for_outreach INTEGER DEFAULT 0")
        conn.commit()
        conn.close()
        
        logger.info("✅ Added ready_for_outreach column")
        print("✅ Added ready_for_outreach column")
        print("🧪 Now test: python3 real_autonomous_organism.py --test")
        
        return True
        
    except Exception as e:
        if "duplicate column name" in str(e):
            logger.info("✅ ready_for_outreach column already exists")
            print("✅ ready_for_outreach column already exists")
            return True
        else:
            logger.error(f"❌ Error adding column: {e}")
            print(f"❌ Error adding column: {e}")
            return False

if __name__ == "__main__":
    print("🔧 ADDING READY_FOR_OUTREACH COLUMN")
    print("=" * 35)
    
    success = add_ready_for_outreach_column()
    
    if success:
        print("\n🎉 COLUMN ADDED SUCCESSFULLY!")
        print("   Sarah-Eden Dadoun should now save properly!")
        print("   🚀 Your diverse search system is ready!")
    else:
        print("\n❌ Failed to add column - manual intervention needed")
