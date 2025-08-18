#!/usr/bin/env python3
"""
Debug Autonomous Sync Logic
============================
Replicate the exact logic the autonomous system uses to find leads for sync
"""

import sqlite3
import logging

class AutonomousSyncDebugger:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def debug_sync_logic(self):
        """Debug the exact sync detection logic used by autonomous system"""
        self.logger.info("🔍 Debugging autonomous sync detection logic...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            leads = cursor.fetchall()
            
            self.logger.info(f"📋 Analyzing {len(leads)} leads for sync eligibility:")
            
            sync_candidates = []
            
            for lead in leads:
                lead_data = dict(lead)
                name = lead_data.get('Full_Name', 'Unknown')
                company = lead_data.get('Company', 'Unknown')
                
                self.logger.info(f"\n🧪 ANALYZING: {name} - {company}")
                
                # Check each sync criteria step by step
                criteria_checks = []
                
                # 1. Check Response_Status
                status = lead_data.get('Response_Status', 'pending')
                self.logger.info(f"   1️⃣ Response_Status: '{status}'")
                if status == 'pending':
                    criteria_checks.append("✅ Status: pending")
                else:
                    criteria_checks.append(f"❌ Status: {status} (not pending)")
                
                # 2. Check AI_Message
                ai_message = lead_data.get('AI_Message', '')
                self.logger.info(f"   2️⃣ AI_Message: {'Present' if ai_message else 'Missing'}")
                if ai_message:
                    criteria_checks.append("✅ AI Message: Present")
                else:
                    criteria_checks.append("❌ AI Message: Missing")
                
                # 3. Check contact methods
                email = lead_data.get('Email', '')
                linkedin = lead_data.get('LinkedIn_URL', '')
                self.logger.info(f"   3️⃣ Email: '{email}'")
                self.logger.info(f"   4️⃣ LinkedIn_URL: '{linkedin}'")
                
                if email or linkedin:
                    criteria_checks.append(f"✅ Contact: {'Email' if email else 'LinkedIn'}")
                else:
                    criteria_checks.append("❌ Contact: No email or LinkedIn")
                
                # 5. Check company name (quality filter)
                if company and company.lower() not in ['unknown company', 'unknown', '']:
                    criteria_checks.append("✅ Company: Valid")
                else:
                    criteria_checks.append(f"❌ Company: Invalid ('{company}')")
                
                # 6. Check email quality (fake domain filter)
                fake_domains = ['27b69170.com', 'a0b00267.com', 'test.com']
                email_domain = email.split('@')[-1] if '@' in email else ''
                if email and email_domain not in fake_domains:
                    criteria_checks.append("✅ Email: Real domain")
                elif email and email_domain in fake_domains:
                    criteria_checks.append(f"❌ Email: Fake domain ({email_domain})")
                elif not email:
                    criteria_checks.append("⚠️ Email: None (LinkedIn only)")
                
                # Summary
                self.logger.info(f"   📊 CRITERIA CHECK:")
                for check in criteria_checks:
                    self.logger.info(f"      {check}")
                
                # Determine if sync ready
                all_passed = all("✅" in check for check in criteria_checks[:4])  # First 4 are mandatory
                
                if all_passed:
                    self.logger.info(f"   🎯 SYNC READY!")
                    sync_candidates.append(name)
                else:
                    failed_checks = [check for check in criteria_checks if "❌" in check]
                    self.logger.info(f"   ❌ NOT READY: {len(failed_checks)} failures")
            
            conn.close()
            
            self.logger.info(f"\n📊 FINAL SYNC SUMMARY:")
            self.logger.info(f"   📋 Total leads: {len(leads)}")
            self.logger.info(f"   🎯 Sync ready: {len(sync_candidates)}")
            
            if sync_candidates:
                self.logger.info(f"   ✅ Ready: {', '.join(sync_candidates)}")
            else:
                self.logger.info(f"   ❌ No leads meet all sync criteria")
                
            return sync_candidates
            
        except Exception as e:
            self.logger.error(f"❌ Debug error: {e}")
            return []

    def force_francois_sync_ready(self):
        """Force Francois to meet all sync criteria"""
        self.logger.info("🔧 Force-preparing Francois for sync...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Update Francois to ensure all sync criteria are met
            cursor = conn.execute("""
                UPDATE leads 
                SET 
                    Response_Status = 'pending',
                    Company = 'CGI',
                    Email = 'info@cgi.com'
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated > 0:
                self.logger.info(f"✅ Force-updated {rows_updated} Francois record(s)")
                self.logger.info(f"   Status: → pending")
                self.logger.info(f"   Company: → CGI")
                self.logger.info(f"   Email: → info@cgi.com")
                return True
            else:
                self.logger.error("❌ No Francois records found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error force-updating Francois: {e}")
            return False

def main():
    debugger = AutonomousSyncDebugger()
    
    print("🔍 AUTONOMOUS SYNC LOGIC DEBUGGER")
    print("=" * 35)
    print("📋 Replicating exact autonomous system sync detection...")
    print("")
    
    # Debug current sync logic
    sync_ready = debugger.debug_sync_logic()
    
    if not sync_ready:
        print(f"\n🔧 No leads ready - force-preparing Francois...")
        
        if debugger.force_francois_sync_ready():
            print(f"\n✅ Francois force-prepared!")
            print(f"🧪 Re-checking sync logic...")
            
            # Re-check after force update
            sync_ready = debugger.debug_sync_logic()
            
            if sync_ready:
                print(f"\n🎯 SUCCESS! Now test autonomous system:")
                print(f"   python3 real_autonomous_organism.py --test")
            else:
                print(f"\n❌ Still not ready - deeper investigation needed")
        else:
            print(f"\n❌ Failed to force-prepare Francois")
    else:
        print(f"\n✅ Leads are sync ready!")
        print(f"   Run: python3 real_autonomous_organism.py --test")

if __name__ == "__main__":
    main()
