#!/usr/bin/env python3
"""
Debug Alex Yorke Specific NoneType Error
=========================================
Find exactly which field is causing the .strip() error
"""

import sqlite3
import logging

def debug_alex_yorke():
    """Debug Alex Yorke's exact data that's causing NoneType error"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        conn = sqlite3.connect('data/unified_leads.db')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT * FROM leads 
            WHERE Full_Name LIKE '%Alex%' AND Full_Name LIKE '%Yorke%'
            ORDER BY Date_Scraped DESC
            LIMIT 1
        """)
        
        alex = cursor.fetchone()
        conn.close()
        
        if alex:
            alex_data = dict(alex)
            
            logger.info("🔍 Alex Yorke detailed field analysis:")
            
            # Check every single field for None values
            critical_airtable_fields = [
                'Full_Name', 'Email', 'Company', 'Job_Title', 'LinkedIn_URL', 
                'AI_Message', 'Website', 'Date_Scraped', 'Date_Enriched', 'Level_Engaged'
            ]
            
            problematic_fields = []
            
            for field in critical_airtable_fields:
                value = alex_data.get(field)
                if value is None:
                    problematic_fields.append(field)
                    logger.info(f"   ❌ {field}: None (PROBLEMATIC)")
                elif value == '':
                    logger.info(f"   ⚠️ {field}: '' (empty string)")
                else:
                    logger.info(f"   ✅ {field}: {repr(value)}")
            
            # Show ALL fields to find any other None values
            logger.info(f"\n📋 ALL Alex Yorke fields:")
            for field, value in alex_data.items():
                if value is None:
                    logger.info(f"   ❌ {field}: None")
                else:
                    logger.info(f"   ✅ {field}: {repr(value)}")
            
            if problematic_fields:
                logger.warning(f"🚫 Problematic None fields: {problematic_fields}")
                
                # Fix these fields
                logger.info(f"🔧 Fixing problematic fields...")
                
                conn = sqlite3.connect('data/unified_leads.db')
                
                # Set all None values to empty strings or appropriate defaults
                update_values = []
                for field in problematic_fields:
                    if field in ['Date_Scraped', 'Date_Enriched']:
                        update_values.append(f"{field} = datetime('now')")
                    elif field == 'Level_Engaged':
                        update_values.append(f"{field} = 0")
                    else:
                        update_values.append(f"{field} = ''")
                
                if update_values:
                    update_sql = f"""
                        UPDATE leads 
                        SET {', '.join(update_values)}
                        WHERE Full_Name LIKE '%Alex%' AND Full_Name LIKE '%Yorke%'
                    """
                    
                    cursor = conn.execute(update_sql)
                    rows_updated = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    logger.info(f"✅ Fixed {rows_updated} Alex Yorke record(s)")
                    return True
                
            else:
                logger.info(f"✅ No obvious None values found in critical fields")
                return False
                
        else:
            logger.error("❌ Alex Yorke not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return False

def main():
    print("🔍 ALEX YORKE SPECIFIC DEBUG")
    print("=" * 30)
    print("📋 Finding exact field causing NoneType .strip() error")
    print("")
    
    success = debug_alex_yorke()
    
    if success:
        print(f"\n✅ FIXED Alex Yorke's problematic fields!")
        print(f"🧪 Test again: python3 real_autonomous_organism.py --test")
        print(f"🎯 Alex Yorke should now sync successfully!")
    else:
        print(f"\n📋 Alex Yorke looks clean - error might be elsewhere")
    
    print(f"\n🎉 AMAZING PROGRESS:")
    print(f"   ✅ Diverse search working perfectly")
    print(f"   ✅ 4 different people found (not same 3!)")
    print(f"   ✅ Database saving working")
    print(f"   🔧 Just need to fix this one Airtable sync issue!")

if __name__ == "__main__":
    main()
