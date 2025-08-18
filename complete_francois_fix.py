#!/usr/bin/env python3
"""
Complete Francois Fix
=====================
Fix ALL blocking issues for autonomous sync
"""

import sqlite3
import logging

class CompleteFrancoisFix:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fix_all_blocking_issues(self):
        """Fix ALL issues blocking Francois from autonomous sync"""
        self.logger.info("🔧 Fixing ALL blocking issues for Francois...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Fix BOTH blocking issues:
            # 1. Response_Status -> 'pending'
            # 2. Date_Messaged -> NULL
            cursor = conn.execute("""
                UPDATE leads 
                SET 
                    Response_Status = 'pending',
                    Date_Messaged = NULL
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated > 0:
                self.logger.info(f"✅ Fixed {rows_updated} Francois record(s)")
                self.logger.info(f"   Response_Status: → 'pending'")
                self.logger.info(f"   Date_Messaged: → NULL")
                return True
            else:
                self.logger.error("❌ No Francois records found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error fixing Francois: {e}")
            return False

    def verify_autonomous_criteria(self):
        """Verify Francois now meets autonomous system criteria"""
        self.logger.info("✅ Verifying autonomous criteria...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT 
                    Full_Name, Company, Response_Status, 
                    Date_Messaged, AI_Message, Email, LinkedIn_URL
                FROM leads 
                WHERE Full_Name LIKE '%Francois%' OR Full_Name LIKE '%François%'
            """)
            
            francois = cursor.fetchone()
            conn.close()
            
            if not francois:
                self.logger.error("❌ Francois not found")
                return False
            
            francois_data = dict(francois)
            
            self.logger.info(f"📋 Francois verification:")
            self.logger.info(f"   Company: {francois_data.get('Company')}")
            self.logger.info(f"   Response_Status: {francois_data.get('Response_Status')}")
            self.logger.info(f"   Date_Messaged: {francois_data.get('Date_Messaged') or 'NULL'}")
            self.logger.info(f"   AI_Message: {'Present' if francois_data.get('AI_Message') else 'Missing'}")
            self.logger.info(f"   Email: {francois_data.get('Email') or 'None'}")
            
            # Check all autonomous criteria
            criteria = {
                'Status is pending/enriched': francois_data.get('Response_Status') in ['pending', 'enriched'],
                'Full_Name exists': bool(francois_data.get('Full_Name')),
                'Date_Messaged is NULL': not francois_data.get('Date_Messaged'),
                'AI_Message exists': bool(francois_data.get('AI_Message')),
                'Contact method exists': bool(francois_data.get('Email')) or bool(francois_data.get('LinkedIn_URL'))
            }
            
            self.logger.info(f"\n🧪 AUTONOMOUS CRITERIA CHECK:")
            all_passed = True
            for criterion, passed in criteria.items():
                status = "✅" if passed else "❌"
                self.logger.info(f"   {criterion}: {status}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                self.logger.info(f"\n🎯 ALL CRITERIA PASSED! Francois should be detected!")
                return True
            else:
                self.logger.warning(f"\n❌ Some criteria still failing")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying criteria: {e}")
            return False

    def test_autonomous_query(self):
        """Test the exact autonomous system query"""
        self.logger.info("🧪 Testing exact autonomous system query...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # EXACT query from autonomous system (lines 493-501)
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
            
            self.logger.info(f"📊 Autonomous query found: {len(leads)} leads")
            
            francois_found = False
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                self.logger.info(f"   ✅ {name} - {company}")
                
                if 'francois' in name.lower():
                    francois_found = True
            
            if francois_found:
                self.logger.info(f"\n🎉 FRANCOIS FOUND! Autonomous system should detect him!")
                return True
            else:
                self.logger.warning(f"\n❌ Francois still not found in autonomous query")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error testing autonomous query: {e}")
            return False

def main():
    fixer = CompleteFrancoisFix()
    
    print("🔧 COMPLETE FRANCOIS FIX")
    print("=" * 25)
    print("📋 Fixing ALL blocking issues for autonomous sync...")
    print("")
    
    # Fix all issues
    if fixer.fix_all_blocking_issues():
        print("✅ All fixes applied!")
        
        # Verify criteria
        if fixer.verify_autonomous_criteria():
            print("\n✅ All criteria verified!")
            
            # Test exact query
            if fixer.test_autonomous_query():
                print(f"\n🎉 SUCCESS! Francois ready for autonomous sync!")
                print(f"\n🚀 NOW TEST THE AUTONOMOUS SYSTEM:")
                print(f"   python3 real_autonomous_organism.py --test")
                print(f"\n🎯 Expected result:")
                print(f"   📊 Found 1 leads available for sync")
                print(f"   📤 Syncing: Francois Boulanger - CGI")
                print(f"   ✅ Synced 1 leads to Airtable")
            else:
                print(f"\n❌ Francois still not found - deeper issue")
        else:
            print(f"\n❌ Some criteria still failing")
    else:
        print(f"❌ Failed to apply fixes")

if __name__ == "__main__":
    main()
