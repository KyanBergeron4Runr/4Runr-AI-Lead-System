#!/usr/bin/env python3
"""
Fix Francois Sync Status
=======================
Simple fix to make Francois ready for Airtable sync
"""

import sqlite3
import logging

class FrancoisFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fix_francois_status(self):
        """Fix Francois to make him ready for sync"""
        self.logger.info("🔧 Fixing Francois for Airtable sync...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Update Francois to be ready for sync
            result = conn.execute("""
                UPDATE leads 
                SET Response_Status = 'pending',
                    Needs_Enrichment = 1
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            if result.rowcount > 0:
                self.logger.info(f"✅ Updated {result.rowcount} Francois record(s)")
                self.logger.info("   Status: enriched → pending")
                self.logger.info("   Needs_Enrichment: 0 → 1")
            else:
                self.logger.info("❌ No Francois found to update")
            
            conn.commit()
            conn.close()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing Francois: {e}")
            return False

    def verify_francois_status(self):
        """Verify Francois is now ready"""
        self.logger.info("✅ Verifying Francois status...")
        
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
                website = francois.get('Website', 'None')
                status = francois.get('Response_Status', 'Unknown')
                needs_enrichment = francois.get('Needs_Enrichment', 0)
                ai_message = francois.get('AI_Message', 'None')
                airtable_id = francois.get('airtable_id', 'None')
                
                self.logger.info(f"📋 {name} status:")
                self.logger.info(f"   Company: {company}")
                self.logger.info(f"   Email: {email}")
                self.logger.info(f"   Website: {website}")
                self.logger.info(f"   Status: {status}")
                self.logger.info(f"   Needs Enrichment: {needs_enrichment}")
                self.logger.info(f"   AI Message: {'✅ Yes' if ai_message and ai_message != 'None' else '❌ No'}")
                self.logger.info(f"   Airtable ID: {airtable_id}")
                
                # Check if ready for sync
                ready_for_sync = (
                    company and company != 'Unknown Company' and
                    email and '@' in email and
                    ai_message and ai_message != 'None' and
                    not airtable_id and
                    status == 'pending' and
                    needs_enrichment == 1
                )
                
                if ready_for_sync:
                    self.logger.info("   Status: ✅ READY FOR SYNC!")
                    return True
                else:
                    self.logger.info("   Status: ❌ Still not ready")
                    return False
            else:
                self.logger.info("❌ No Francois found in database")
                return False
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error verifying Francois: {e}")
            return False

def main():
    fixer = FrancoisFixer()
    
    print("🔧 FRANCOIS SYNC FIXER")
    print("=" * 22)
    print("📋 Fix Francois Boulanger to be ready for Airtable sync")
    print("")
    
    # Fix status
    success = fixer.fix_francois_status()
    
    if success:
        # Verify result
        ready = fixer.verify_francois_status()
        
        print(f"\n🎉 FRANCOIS FIX COMPLETE!")
        print(f"   🔧 Status updated: ✅")
        print(f"   📤 Ready for sync: {'✅' if ready else '❌'}")
        
        if ready:
            print(f"\n🚀 TEST THE FIXED SYSTEM:")
            print(f"   python3 real_autonomous_organism.py --test")
            print(f"   Should now sync Francois to Airtable!")
        else:
            print(f"\n⚠️ Still needs more fixing")
    else:
        print(f"\n❌ Failed to fix Francois")

if __name__ == "__main__":
    main()
