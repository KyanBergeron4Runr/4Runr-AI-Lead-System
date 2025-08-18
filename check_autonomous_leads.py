#!/usr/bin/env python3
"""
Check Autonomous Lead Detection
===============================
See what leads the autonomous system can find for sync
"""

import sqlite3
import logging

class AutonomousLeadChecker:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_all_leads(self):
        """Check all leads and their sync eligibility"""
        self.logger.info("🔍 Checking all leads for autonomous sync eligibility...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads ORDER BY Date_Scraped DESC")
            leads = cursor.fetchall()
            
            self.logger.info(f"📋 Found {len(leads)} total leads:")
            
            sync_ready = []
            for lead in leads:
                lead_data = dict(lead)
                name = lead_data.get('Full_Name', 'Unknown')
                company = lead_data.get('Company', 'Unknown')
                status = lead_data.get('Response_Status', 'pending')
                
                self.logger.info(f"\n   {name} - {company}")
                self.logger.info(f"      Response Status: {status}")
                self.logger.info(f"      Email: {lead_data.get('Email', 'None')}")
                self.logger.info(f"      AI Message: {'✅' if lead_data.get('AI_Message') else '❌'}")
                
                # Check sync eligibility (autonomous system logic)
                if (status == 'pending' and 
                    lead_data.get('AI_Message') and 
                    (lead_data.get('Email') or lead_data.get('LinkedIn_URL'))):
                    sync_ready.append(name)
                    self.logger.info(f"      🎯 SYNC READY!")
                else:
                    reasons = []
                    if status != 'pending':
                        reasons.append(f"Status: {status}")
                    if not lead_data.get('AI_Message'):
                        reasons.append("No AI message")
                    if not (lead_data.get('Email') or lead_data.get('LinkedIn_URL')):
                        reasons.append("No contact method")
                    
                    self.logger.info(f"      ⚠️ NOT READY: {', '.join(reasons)}")
            
            conn.close()
            
            self.logger.info(f"\n📊 SYNC SUMMARY:")
            self.logger.info(f"   📋 Total leads: {len(leads)}")
            self.logger.info(f"   🎯 Ready for sync: {len(sync_ready)}")
            
            if sync_ready:
                self.logger.info(f"   ✅ Ready leads: {', '.join(sync_ready)}")
            else:
                self.logger.info(f"   ❌ No leads ready for sync")
                
            return sync_ready
            
        except Exception as e:
            self.logger.error(f"❌ Error checking leads: {e}")
            return []

    def reset_francois_for_testing(self):
        """Reset Francois to pending so we can test autonomous sync again"""
        self.logger.info("🔧 Resetting Francois to test autonomous sync...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Reset Francois to pending
            cursor = conn.execute("""
                UPDATE leads 
                SET Response_Status = 'pending'
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated > 0:
                self.logger.info(f"✅ Reset {rows_updated} Francois record(s) to 'pending'")
                self.logger.info(f"🎯 Francois should now be detected by autonomous system")
                return True
            else:
                self.logger.error("❌ No Francois records found to reset")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error resetting Francois: {e}")
            return False

def main():
    checker = AutonomousLeadChecker()
    
    print("🔍 AUTONOMOUS LEAD DETECTION CHECK")
    print("=" * 35)
    print("📋 Checking what leads the autonomous system can find...")
    print("")
    
    # Check current status
    sync_ready = checker.check_all_leads()
    
    if not sync_ready:
        print(f"\n🔧 No leads ready - let's reset Francois for testing...")
        
        if checker.reset_francois_for_testing():
            print(f"\n✅ Francois reset - now test autonomous system:")
            print(f"   python3 real_autonomous_organism.py --test")
            print(f"\n🎯 Should now find and sync Francois!")
        else:
            print(f"\n❌ Failed to reset Francois")
    else:
        print(f"\n✅ Leads ready for autonomous sync!")
        print(f"   Run: python3 real_autonomous_organism.py --test")

if __name__ == "__main__":
    main()
