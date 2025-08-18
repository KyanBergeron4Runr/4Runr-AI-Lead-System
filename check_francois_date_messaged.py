#!/usr/bin/env python3
"""
Check Francois Date_Messaged Field
==================================
Check if Date_Messaged is blocking Francois from autonomous sync
"""

import sqlite3
import logging

class FrancoisDateChecker:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_francois_dates(self):
        """Check all date fields that might block Francois"""
        self.logger.info("🔍 Checking Francois date fields...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT 
                    Full_Name, Company, Response_Status,
                    Date_Messaged, Date_Scraped, Date_Enriched,
                    Created_At, Level_Engaged, Engagement_Status
                FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            
            if not francois:
                self.logger.error("❌ Francois not found")
                return False
            
            francois_data = dict(francois)
            
            self.logger.info(f"📋 Francois Boulanger date analysis:")
            self.logger.info(f"   Company: {francois_data.get('Company')}")
            self.logger.info(f"   Response_Status: {francois_data.get('Response_Status')}")
            self.logger.info(f"   Date_Messaged: '{francois_data.get('Date_Messaged', 'NULL')}'")
            self.logger.info(f"   Date_Scraped: '{francois_data.get('Date_Scraped', 'NULL')}'")
            self.logger.info(f"   Date_Enriched: '{francois_data.get('Date_Enriched', 'NULL')}'")
            self.logger.info(f"   Created_At: '{francois_data.get('Created_At', 'NULL')}'")
            
            # Check autonomous system criteria
            date_messaged = francois_data.get('Date_Messaged')
            
            self.logger.info(f"\n🧪 AUTONOMOUS SYSTEM CRITERIA CHECK:")
            self.logger.info(f"   Status = 'pending': ✅" if francois_data.get('Response_Status') == 'pending' else f"   Status = 'pending': ❌ ({francois_data.get('Response_Status')})")
            self.logger.info(f"   Date_Messaged IS NULL: {'✅' if not date_messaged or date_messaged == '' else '❌'}")
            
            if date_messaged and date_messaged != '':
                self.logger.warning(f"🚫 BLOCKING ISSUE: Date_Messaged = '{date_messaged}'")
                self.logger.info(f"   Autonomous system requires Date_Messaged to be NULL or empty")
                return False
            else:
                self.logger.info(f"✅ Date_Messaged is clear - should be detected!")
                return True
                
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error checking Francois dates: {e}")
            return False

    def clear_francois_date_messaged(self):
        """Clear Date_Messaged to unblock autonomous sync"""
        self.logger.info("🔧 Clearing Francois Date_Messaged...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute("""
                UPDATE leads 
                SET Date_Messaged = NULL
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated > 0:
                self.logger.info(f"✅ Cleared Date_Messaged for {rows_updated} Francois record(s)")
                return True
            else:
                self.logger.error("❌ No Francois records found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error clearing Date_Messaged: {e}")
            return False

    def simulate_autonomous_query(self):
        """Run the exact query the autonomous system uses"""
        self.logger.info("🧪 Running exact autonomous system query...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # EXACT query from autonomous system
            cursor = conn.execute('''
                SELECT * FROM leads 
                WHERE (Response_Status = 'enriched' OR Response_Status = 'pending')
                AND Full_Name IS NOT NULL AND Full_Name != ''
                AND (Date_Messaged IS NULL OR Date_Messaged = '')
                AND (Response_Status != 'synced')
                ORDER BY Date_Enriched DESC 
                LIMIT 10
            ''')
            
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📊 Autonomous query results: {len(leads)} leads found")
            
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                self.logger.info(f"   ✅ {name} - {company}")
            
            francois_found = any('francois' in lead.get('Full_Name', '').lower() for lead in leads)
            
            if francois_found:
                self.logger.info(f"🎯 Francois FOUND in autonomous query!")
                return True
            else:
                self.logger.warning(f"❌ Francois NOT found in autonomous query")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error running autonomous query: {e}")
            return False

def main():
    checker = FrancoisDateChecker()
    
    print("🔍 FRANCOIS DATE_MESSAGED CHECKER")
    print("=" * 35)
    print("📋 Checking if Date_Messaged is blocking autonomous sync...")
    print("")
    
    # Check current dates
    is_clear = checker.check_francois_dates()
    
    if not is_clear:
        print(f"\n🔧 Clearing Date_Messaged to unblock sync...")
        if checker.clear_francois_date_messaged():
            print(f"✅ Date_Messaged cleared!")
            is_clear = True
        else:
            print(f"❌ Failed to clear Date_Messaged")
    
    if is_clear:
        print(f"\n🧪 Testing autonomous system query...")
        
        if checker.simulate_autonomous_query():
            print(f"\n🎉 SUCCESS! Francois found in autonomous query!")
            print(f"🚀 Now test: python3 real_autonomous_organism.py --test")
        else:
            print(f"\n❌ Francois still not found - investigate further")
    else:
        print(f"\n❌ Francois still blocked by date fields")

if __name__ == "__main__":
    main()
