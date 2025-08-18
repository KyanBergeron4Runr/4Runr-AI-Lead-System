#!/usr/bin/env python3
"""
Debug Autonomous Detection
=========================
Find out why Francois isn't being detected by autonomous system
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class AutonomousDetectionDebugger:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def simulate_autonomous_logic(self):
        """Simulate the autonomous system's lead detection logic"""
        self.logger.info("🔍 Simulating autonomous system lead detection...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            all_leads = [dict(row) for row in cursor.fetchall()]
            
            self.logger.info(f"📋 Found {len(all_leads)} total leads in database")
            
            for lead in all_leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                status = lead.get('Response_Status', 'Unknown')
                needs_enrichment = lead.get('Needs_Enrichment', 0)
                
                self.logger.info(f"\n🧪 Analyzing: {name} - {company}")
                self.logger.info(f"   Response_Status: {status}")
                self.logger.info(f"   Needs_Enrichment: {needs_enrichment}")
                
                # Check what the autonomous system looks for
                # Based on the logs, it looks for "existing leads with missing data"
                
                # Common criteria for "missing data"
                missing_data_fields = []
                
                # Check common fields that might be considered "missing"
                fields_to_check = [
                    'AI_Message', 'Company_Description', 'Business_Type', 
                    'Website', 'Response_Date', 'Date_Enriched'
                ]
                
                for field in fields_to_check:
                    value = lead.get(field, '')
                    if not value or value in ['', 'None', None]:
                        missing_data_fields.append(field)
                
                self.logger.info(f"   Missing fields: {missing_data_fields}")
                
                # Check if this would be considered for enrichment
                has_missing_data = len(missing_data_fields) > 0
                is_pending = status == 'pending'
                needs_processing = needs_enrichment == 1
                
                self.logger.info(f"   Has missing data: {has_missing_data}")
                self.logger.info(f"   Is pending: {is_pending}")
                self.logger.info(f"   Needs processing: {needs_processing}")
                
                # Determine if autonomous system would pick this up
                would_be_detected = has_missing_data and (is_pending or needs_processing)
                
                if would_be_detected:
                    self.logger.info(f"   🎯 WOULD BE DETECTED by autonomous system")
                else:
                    self.logger.info(f"   ❌ Would NOT be detected")
                    
                    # Suggest fixes
                    if not has_missing_data:
                        self.logger.info(f"      Fix: Create missing data (clear a field)")
                    if not is_pending:
                        self.logger.info(f"      Fix: Set Response_Status = 'pending'")
                    if not needs_processing:
                        self.logger.info(f"      Fix: Set Needs_Enrichment = 1")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error simulating detection: {e}")

    def force_francois_detectable(self):
        """Force Francois to be detectable by creating missing data"""
        self.logger.info("🔧 Making Francois detectable by autonomous system...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Clear one field to create "missing data" and set proper flags
            result = conn.execute("""
                UPDATE leads 
                SET Response_Status = 'pending',
                    Needs_Enrichment = 1,
                    Company_Description = NULL
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            if result.rowcount > 0:
                self.logger.info(f"✅ Updated Francois to be detectable:")
                self.logger.info(f"   Response_Status: → pending")
                self.logger.info(f"   Needs_Enrichment: → 1")
                self.logger.info(f"   Company_Description: → NULL (creates missing data)")
                
                conn.commit()
                conn.close()
                return True
            else:
                self.logger.error("❌ No Francois found to update")
                conn.close()
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error making Francois detectable: {e}")
            return False

def main():
    debugger = AutonomousDetectionDebugger()
    
    print("🔍 AUTONOMOUS DETECTION DEBUGGER")
    print("=" * 35)
    print("📋 Find out why Francois isn't being detected")
    print("")
    
    # Simulate autonomous logic
    debugger.simulate_autonomous_logic()
    
    print(f"\n🔧 FORCE FRANCOIS DETECTABLE?")
    print(f"This will create missing data so autonomous system finds him")
    
    response = input("Make Francois detectable? (y/n): ")
    if response.lower() == 'y':
        success = debugger.force_francois_detectable()
        
        if success:
            print(f"\n✅ Francois is now detectable!")
            print(f"🚀 Test again: python3 real_autonomous_organism.py --test")
        else:
            print(f"\n❌ Failed to make Francois detectable")
    else:
        print(f"\n💡 Try direct sync instead: python3 simple_airtable_sync.py")

if __name__ == "__main__":
    main()
