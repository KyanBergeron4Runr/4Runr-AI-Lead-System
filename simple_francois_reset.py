#!/usr/bin/env python3
"""
Simple Francois Reset
====================
Reset Francois using only existing database columns
"""

import sqlite3
import logging

class SimpleFrancoisReset:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def reset_francois_simple(self):
        """Reset Francois using only existing columns"""
        self.logger.info("🔧 Resetting Francois with existing columns...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Simple reset using only existing columns
            result = conn.execute("""
                UPDATE leads 
                SET Response_Status = 'pending',
                    Needs_Enrichment = 0
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            if result.rowcount > 0:
                self.logger.info(f"✅ Reset {result.rowcount} Francois record(s)")
                self.logger.info("   Response_Status: → pending")
                self.logger.info("   Needs_Enrichment: → 0 (already enriched)")
            else:
                self.logger.error("❌ No Francois found to reset")
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error resetting Francois: {e}")
            return False

    def verify_francois_status(self):
        """Verify Francois current status"""
        self.logger.info("📊 Checking Francois status...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            
            if francois:
                francois = dict(francois)
                
                name = francois.get('Full_Name', 'Unknown')
                company = francois.get('Company', 'Unknown')
                email = francois.get('Email', 'None')
                source = francois.get('Source', 'None')
                status = francois.get('Response_Status', 'Unknown')
                needs_enrichment = francois.get('Needs_Enrichment', 0)
                ai_message = francois.get('AI_Message', 'None')
                
                self.logger.info(f"📋 {name} current status:")
                self.logger.info(f"   Company: {company}")
                self.logger.info(f"   Email: {email}")
                self.logger.info(f"   Business Contact: {source}")
                self.logger.info(f"   Response Status: {status}")
                self.logger.info(f"   Needs Enrichment: {needs_enrichment}")
                self.logger.info(f"   AI Message: {'✅ Present' if ai_message and len(ai_message) > 10 else '❌ Missing'}")
                
                # Check if ready for sync
                ready_for_sync = (
                    company and company not in ['Unknown Company', 'Unknown'] and
                    (email or 'Business:' in source) and
                    ai_message and len(ai_message) > 10 and
                    status == 'pending'
                )
                
                if ready_for_sync:
                    self.logger.info(f"   Status: ✅ READY FOR AUTONOMOUS SYNC!")
                    return True
                else:
                    self.logger.info(f"   Status: ⚠️ Needs more preparation")
                    return False
            else:
                self.logger.error("❌ Francois not found")
                return False
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error checking status: {e}")
            return False

def main():
    resetter = SimpleFrancoisReset()
    
    print("🔧 SIMPLE FRANCOIS RESET")
    print("=" * 26)
    print("📋 Reset Francois using existing database columns")
    print("")
    
    # Check current status
    print("📊 Checking current status...")
    current_ready = resetter.verify_francois_status()
    
    if current_ready:
        print("\n✅ Francois is already ready for sync!")
        print("🚀 Test autonomous system: python3 real_autonomous_organism.py --test")
        return
    
    # Reset Francois
    print("\n🔧 Resetting Francois...")
    success = resetter.reset_francois_simple()
    
    if success:
        # Verify after reset
        print("\n✅ Verifying after reset...")
        ready = resetter.verify_francois_status()
        
        print(f"\n🎉 RESET COMPLETE!")
        print(f"   🔧 Reset: {'✅ Success' if success else '❌ Failed'}")
        print(f"   ✅ Ready: {'✅ Yes' if ready else '❌ No'}")
        
        if ready:
            print(f"\n🚀 NOW TEST AUTONOMOUS SYSTEM:")
            print(f"   python3 real_autonomous_organism.py --test")
            print(f"   Francois should now be found and synced!")
        else:
            print(f"\n💡 If still not ready, try direct sync:")
            print(f"   python3 simple_airtable_sync.py")
    else:
        print(f"\n❌ Reset failed")

if __name__ == "__main__":
    main()
