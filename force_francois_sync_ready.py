#!/usr/bin/env python3
"""
Force Francois Sync Ready
========================
Make Francois available for autonomous system sync
"""

import sqlite3
import logging

class FrancoisSyncForcer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def reset_francois_for_sync(self):
        """Reset Francois to be ready for autonomous sync"""
        self.logger.info("🔧 Resetting Francois for autonomous sync...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Find Francois
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            
            if not francois:
                self.logger.error("❌ Francois not found in database")
                return False
            
            self.logger.info(f"✅ Found Francois in database")
            
            # Reset his status to make him available for sync
            conn.execute("""
                UPDATE leads 
                SET Response_Status = 'pending',
                    Needs_Enrichment = 0,
                    airtable_id = NULL
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Francois reset for sync:")
            self.logger.info(f"   Response_Status: enriched → pending")
            self.logger.info(f"   Needs_Enrichment: 1 → 0 (already enriched)")
            self.logger.info(f"   airtable_id: cleared")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error resetting Francois: {e}")
            return False

    def verify_francois_ready(self):
        """Verify Francois is ready for sync"""
        self.logger.info("✅ Verifying Francois sync readiness...")
        
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
                airtable_id = francois.get('airtable_id', 'None')
                
                self.logger.info(f"📋 {name} status:")
                self.logger.info(f"   Company: {company}")
                self.logger.info(f"   Email: {email}")
                self.logger.info(f"   Business Contact: {source}")
                self.logger.info(f"   Response Status: {status}")
                self.logger.info(f"   Needs Enrichment: {needs_enrichment}")
                self.logger.info(f"   AI Message: {'✅ Yes' if ai_message and ai_message != 'None' else '❌ No'}")
                self.logger.info(f"   Airtable ID: {airtable_id}")
                
                # Check sync readiness
                ready_criteria = {
                    'has_company': company and company != 'Unknown Company',
                    'has_contact': email or ('Business:' in source),
                    'has_ai_message': ai_message and ai_message != 'None',
                    'status_pending': status == 'pending',
                    'not_synced': not airtable_id or airtable_id == 'None'
                }
                
                self.logger.info(f"📊 Sync readiness check:")
                for criteria, status in ready_criteria.items():
                    self.logger.info(f"   {criteria}: {'✅' if status else '❌'}")
                
                all_ready = all(ready_criteria.values())
                
                if all_ready:
                    self.logger.info(f"🎉 FRANCOIS IS READY FOR SYNC!")
                    return True
                else:
                    self.logger.info(f"⚠️ Francois needs more preparation")
                    return False
            else:
                self.logger.error("❌ Francois not found")
                return False
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error verifying Francois: {e}")
            return False

def main():
    forcer = FrancoisSyncForcer()
    
    print("🔧 FORCE FRANCOIS SYNC READY")
    print("=" * 30)
    print("📋 Make Francois available for autonomous system sync")
    print("")
    
    # Reset Francois
    success = forcer.reset_francois_for_sync()
    
    if success:
        # Verify readiness
        ready = forcer.verify_francois_ready()
        
        print(f"\n🎉 FRANCOIS SYNC PREPARATION:")
        print(f"   🔧 Reset: {'✅ Success' if success else '❌ Failed'}")
        print(f"   ✅ Ready: {'✅ Yes' if ready else '❌ No'}")
        
        if ready:
            print(f"\n🚀 NOW TEST AUTONOMOUS SYSTEM:")
            print(f"   python3 real_autonomous_organism.py --test")
            print(f"   Should find Francois ready for sync!")
        else:
            print(f"\n⚠️ Francois still needs manual sync")
            print(f"   Try: python3 simple_airtable_sync.py")
    else:
        print(f"\n❌ Failed to reset Francois")

if __name__ == "__main__":
    main()
