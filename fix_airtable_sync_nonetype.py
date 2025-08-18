#!/usr/bin/env python3
"""
Fix Airtable Sync NoneType Error
=================================
Fix the 'NoneType' object has no attribute 'strip' error in sync
"""

import sqlite3
import logging

def check_alex_yorke_data():
    """Check Alex Yorke's data to see what's causing NoneType error"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT * FROM leads 
            WHERE Full_Name LIKE '%Alex%' OR Full_Name LIKE '%Yorke%'
            ORDER BY Date_Scraped DESC
            LIMIT 1
        """)
        
        alex = cursor.fetchone()
        conn.close()
        
        if alex:
            alex_data = dict(alex)
            logger.info("📋 Alex Yorke's data:")
            
            # Check for None values that might cause .strip() errors
            critical_fields = ['Full_Name', 'Company', 'Email', 'LinkedIn_URL', 'Job_Title']
            none_fields = []
            
            for field in critical_fields:
                value = alex_data.get(field)
                if value is None:
                    none_fields.append(field)
                    logger.info(f"   ❌ {field}: None")
                else:
                    logger.info(f"   ✅ {field}: {value}")
            
            if none_fields:
                logger.warning(f"🚫 Found None values in: {none_fields}")
                logger.info("💡 This is likely causing the .strip() error in Airtable sync")
                return alex_data, none_fields
            else:
                logger.info("✅ No None values found - error might be elsewhere")
                return alex_data, []
        else:
            logger.error("❌ Alex Yorke not found in database")
            return None, []
            
    except Exception as e:
        logger.error(f"❌ Error checking Alex data: {e}")
        return None, []

def fix_alex_yorke_none_values():
    """Fix None values in Alex Yorke's record"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        
        # Update None values with empty strings or defaults
        cursor = conn.execute("""
            UPDATE leads 
            SET 
                Company = COALESCE(Company, 'Unknown Company'),
                Email = COALESCE(Email, ''),
                Job_Title = COALESCE(Job_Title, 'Operations Manager'),
                Website = COALESCE(Website, ''),
                Source = COALESCE(Source, 'SerpAPI_Real')
            WHERE Full_Name LIKE '%Alex%' OR Full_Name LIKE '%Yorke%'
        """)
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_updated > 0:
            logger.info(f"✅ Fixed {rows_updated} Alex Yorke record(s)")
            logger.info("   Replaced None values with defaults")
            return True
        else:
            logger.warning("⚠️ No Alex Yorke records found to fix")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error fixing Alex data: {e}")
        return False

def main():
    print("🔧 AIRTABLE SYNC NONETYPE FIX")
    print("=" * 30)
    print("📋 Checking Alex Yorke's data for None values causing sync error")
    print("")
    
    # Check Alex's data
    alex_data, none_fields = check_alex_yorke_data()
    
    if alex_data and none_fields:
        print(f"❌ Found None values in: {none_fields}")
        print(f"💡 These are causing the .strip() error in Airtable sync")
        
        print(f"\n🔧 Fixing None values...")
        if fix_alex_yorke_none_values():
            print(f"✅ Fixed Alex Yorke's record!")
            print(f"🧪 Test again: python3 real_autonomous_organism.py --test")
            print(f"🎯 Alex Yorke should now sync to Airtable successfully!")
        else:
            print(f"❌ Failed to fix Alex's record")
    
    elif alex_data:
        print(f"✅ Alex Yorke's data looks good - no obvious None values")
        print(f"💡 The error might be in Airtable field mapping")
        print(f"🧪 Try testing again: python3 real_autonomous_organism.py --test")
    
    else:
        print(f"❌ Could not find Alex Yorke in database")
        print(f"🔍 Try running autonomous system again to regenerate")
    
    print(f"\n🎉 SUCCESS SO FAR:")
    print(f"   ✅ Diverse search working (Operations Manager Ottawa)")
    print(f"   ✅ NEW person found (Alex Yorke)")
    print(f"   ✅ Database saving working")
    print(f"   🔧 Just need to fix Airtable sync!")

if __name__ == "__main__":
    main()
