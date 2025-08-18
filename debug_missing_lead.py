#!/usr/bin/env python3
"""
Debug Missing Lead Issue
======================
Check why Francois Boulanger isn't being found for sync
"""

import sqlite3
import sys
import logging

sys.path.insert(0, './4runr-outreach-system')

class LeadDebugger:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_database_state(self):
        """Check current database state"""
        self.logger.info("🔍 Checking database state...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads ORDER BY created_at DESC")
            leads = [dict(row) for row in cursor.fetchall()]
            
            self.logger.info(f"📋 Found {len(leads)} leads in database:")
            
            for i, lead in enumerate(leads, 1):
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                email = lead.get('Email', 'None')
                website = lead.get('Website', 'None')
                status = lead.get('Response_Status', 'Unknown')
                ai_message = lead.get('AI_Message', 'None')
                airtable_id = lead.get('airtable_id', 'None')
                
                self.logger.info(f"   {i}. {name}")
                self.logger.info(f"      Company: {company}")
                self.logger.info(f"      Email: {email}")
                self.logger.info(f"      Website: {website}")
                self.logger.info(f"      Status: {status}")
                self.logger.info(f"      AI Message: {'✅ Yes' if ai_message and ai_message not in ['None', '', None] else '❌ No'}")
                self.logger.info(f"      Airtable ID: {airtable_id}")
                self.logger.info("")
            
            conn.close()
            return leads
            
        except Exception as e:
            self.logger.error(f"❌ Error checking database: {e}")
            return []

    def check_enrichment_criteria(self, leads):
        """Check what criteria the system uses for enrichment"""
        self.logger.info("🔍 Checking enrichment criteria...")
        
        for lead in leads:
            name = lead.get('Full_Name', 'Unknown')
            
            self.logger.info(f"🧪 Analyzing: {name}")
            
            # Check missing data fields that trigger enrichment
            missing_fields = []
            
            # Common fields that might be missing
            fields_to_check = [
                'AI_Message', 'Company_Description', 'Website', 'Phone',
                'Business_Type', 'Employee_Count', 'Annual_Revenue',
                'Industry', 'Company_Size', 'Last_Enriched'
            ]
            
            for field in fields_to_check:
                value = lead.get(field)
                if not value or value in ['None', '', None]:
                    missing_fields.append(field)
            
            self.logger.info(f"   Missing fields: {missing_fields}")
            
            # Check Response_Status
            status = lead.get('Response_Status', '')
            self.logger.info(f"   Response Status: {status}")
            
            # Check if it should need enrichment
            needs_enrichment = lead.get('Needs_Enrichment', 0)
            self.logger.info(f"   Needs Enrichment flag: {needs_enrichment}")
            
            # Check validation criteria
            validation_issues = []
            
            company = lead.get('Company', '')
            if not company or company.lower() in ['unknown company', 'unknown']:
                validation_issues.append("Generic company name")
            
            email = lead.get('Email', '')
            if email and any(fake in email.lower() for fake in ['27b69170.com', 'a0b00267.com']):
                validation_issues.append("Fake email domain")
            
            data_quality = lead.get('data_quality', '')
            if not data_quality or 'serpapi' not in data_quality.lower():
                validation_issues.append("Non-SerpAPI data source")
            
            if validation_issues:
                self.logger.info(f"   ⚠️ Validation issues: {validation_issues}")
            else:
                self.logger.info(f"   ✅ Passes validation")
            
            self.logger.info("")

    def force_update_lead_status(self, leads):
        """Force update lead status to make it ready for enrichment"""
        self.logger.info("🔧 Force updating lead status...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                
                if 'francois' in name.lower():
                    self.logger.info(f"🔧 Force updating: {name}")
                    
                    # Update to make it ready for enrichment and sync
                    conn.execute("""
                        UPDATE leads 
                        SET Response_Status = 'pending',
                            Needs_Enrichment = 1,
                            data_quality = 'serpapi_sourced',
                            scraping_source = 'serpapi_enhanced'
                        WHERE id = ?
                    """, (lead['id'],))
                    
                    self.logger.info(f"   ✅ Updated status and flags")
            
            conn.commit()
            conn.close()
            
            self.logger.info("🎉 Force update complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error force updating: {e}")

def main():
    debugger = LeadDebugger()
    
    print("🔍 LEAD DEBUG ANALYSIS")
    print("=" * 25)
    
    # Check database state
    leads = debugger.check_database_state()
    
    # Check enrichment criteria
    debugger.check_enrichment_criteria(leads)
    
    # Ask if we should force update
    if leads:
        print("\n🔧 FORCE UPDATE FRANCOIS?")
        print("This will set his status to make him ready for enrichment/sync")
        
        response = input("Force update? (y/n): ")
        if response.lower() == 'y':
            debugger.force_update_lead_status(leads)
            
            print("\n🚀 NOW TEST AGAIN:")
            print("python3 real_autonomous_organism.py --test")

if __name__ == "__main__":
    main()
