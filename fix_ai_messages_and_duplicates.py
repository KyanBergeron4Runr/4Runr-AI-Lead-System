#!/usr/bin/env python3
"""
Fix AI Messages and Duplicate Prevention
- Ensure AI messages are properly generated 
- Prevent duplicate syncing to Airtable
- Check Airtable for existing records before syncing
"""

import sqlite3
import requests
import json
import logging
import os
from datetime import datetime

class AIMessageAndDuplicateFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
        # Airtable config
        self.base_id = "appBZvPvNXGqtoJdc"
        self.table_name = "Table 1"
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_leads_missing_ai_messages(self):
        """Check which leads are missing AI messages"""
        self.logger.info("🔍 Checking for leads missing AI messages...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT Full_Name, Company, Job_Title, AI_Message
                FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND (AI_Message IS NULL OR AI_Message = '')
                LIMIT 10
            """)
            
            missing_ai = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📋 Found {len(missing_ai)} leads missing AI messages:")
            for lead in missing_ai:
                self.logger.info(f"   - {lead['Full_Name']} at {lead['Company']}")
            
            return missing_ai
            
        except Exception as e:
            self.logger.error(f"❌ Error checking AI messages: {e}")
            return []

    def generate_professional_ai_message(self, lead):
        """Generate a professional AI message for a lead"""
        name = lead.get('Full_Name', '')
        company = lead.get('Company', '')
        job_title = lead.get('Job_Title', '')
        
        first_name = name.split()[0] if name else 'there'
        
        # Generate based on role
        if any(role in job_title.upper() for role in ['CEO', 'FOUNDER', 'PRESIDENT']):
            message = f"Hi {first_name}, I've been following {company}'s impressive growth and your leadership vision. I'd love to explore how our solutions could help accelerate your business objectives and drive even greater success. Would you be available for a brief conversation this week?"
        elif any(role in job_title.upper() for role in ['DIRECTOR', 'MANAGER', 'VP']):
            message = f"Hi {first_name}, I noticed your strategic role at {company} and believe there could be valuable synergies between our services and your team's goals. Would you be open to a quick discussion about potential collaboration opportunities?"
        else:
            message = f"Hi {first_name}, I'm impressed by the innovative work happening at {company}. I'd love to discuss how we can support your business growth and help you achieve your strategic objectives. Are you available for a brief chat?"
        
        return message

    def fix_missing_ai_messages(self):
        """Fix all leads missing AI messages"""
        self.logger.info("🤖 Generating missing AI messages...")
        
        missing_leads = self.check_leads_missing_ai_messages()
        
        if not missing_leads:
            self.logger.info("✅ All leads have AI messages")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            fixed_count = 0
            
            for lead in missing_leads:
                # Generate AI message
                ai_message = self.generate_professional_ai_message(lead)
                
                # Update database
                conn.execute("""
                    UPDATE leads SET 
                        AI_Message = ?,
                        Date_Enriched = ?
                    WHERE Full_Name = ? AND Company = ?
                """, (ai_message, datetime.now().isoformat(), lead['Full_Name'], lead['Company']))
                
                self.logger.info(f"✅ Generated AI message for: {lead['Full_Name']}")
                fixed_count += 1
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed {fixed_count} AI messages")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing AI messages: {e}")
            return 0

    def get_existing_airtable_records(self):
        """Get all existing records from Airtable to prevent duplicates"""
        self.logger.info("📋 Getting existing Airtable records for duplicate prevention...")
        
        if not self.api_key:
            self.logger.error("❌ No Airtable API key found")
            return {}
        
        try:
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            all_records = []
            offset = None
            
            while True:
                params = {'pageSize': 100}
                if offset:
                    params['offset'] = offset
                
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    self.logger.error(f"❌ Error getting Airtable records: {response.status_code}")
                    break
                
                data = response.json()
                all_records.extend(data.get('records', []))
                
                offset = data.get('offset')
                if not offset:
                    break
            
            # Create lookup by email and name for duplicate detection
            existing_lookup = {}
            for record in all_records:
                fields = record.get('fields', {})
                full_name = fields.get('Full Name', '').strip().lower()
                email = fields.get('Email', '').strip().lower()
                
                if full_name:
                    existing_lookup[full_name] = record['id']
                if email:
                    existing_lookup[email] = record['id']
            
            self.logger.info(f"📊 Found {len(all_records)} existing Airtable records")
            return existing_lookup
            
        except Exception as e:
            self.logger.error(f"❌ Error getting Airtable records: {e}")
            return {}

    def mark_synced_leads_in_database(self, existing_lookup):
        """Mark leads as synced if they already exist in Airtable"""
        self.logger.info("🔄 Marking already-synced leads in database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads that might need status updates
            cursor = conn.execute("""
                SELECT id, Full_Name, Email, Response_Status
                FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND Response_Status != 'synced'
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            updated_count = 0
            
            for lead in leads:
                full_name = lead['Full_Name'].strip().lower()
                email = lead['Email'].strip().lower() if lead['Email'] else ''
                
                # Check if this lead already exists in Airtable
                if full_name in existing_lookup or email in existing_lookup:
                    # Mark as synced to prevent duplicate
                    conn.execute("""
                        UPDATE leads SET 
                            Response_Status = 'synced',
                            Date_Messaged = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), lead['id']))
                    
                    self.logger.info(f"🔄 Marked as synced (already in Airtable): {lead['Full_Name']}")
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Updated {updated_count} leads to prevent duplicates")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"❌ Error marking synced leads: {e}")
            return 0

    def show_sync_candidates(self):
        """Show which leads are ready for sync (not duplicates)"""
        self.logger.info("📤 Checking sync candidates...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT Full_Name, Company, Email, AI_Message, Response_Status
                FROM leads 
                WHERE Full_Name IS NOT NULL AND Full_Name != ''
                AND AI_Message IS NOT NULL AND AI_Message != ''
                AND Response_Status != 'synced'
                LIMIT 10
            """)
            
            sync_candidates = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.logger.info(f"📋 Found {len(sync_candidates)} leads ready for sync:")
            for lead in sync_candidates:
                ai_preview = lead['AI_Message'][:50] + "..." if len(lead['AI_Message']) > 50 else lead['AI_Message']
                self.logger.info(f"   ✅ {lead['Full_Name']} - AI: {ai_preview}")
            
            return sync_candidates
            
        except Exception as e:
            self.logger.error(f"❌ Error checking sync candidates: {e}")
            return []

def main():
    fixer = AIMessageAndDuplicateFixer()
    
    print("🔧 FIXING AI MESSAGES AND DUPLICATE PREVENTION")
    print("=" * 55)
    
    # Step 1: Fix missing AI messages
    print("\n🤖 STEP 1: Fixing missing AI messages...")
    ai_fixed = fixer.fix_missing_ai_messages()
    
    # Step 2: Get existing Airtable records for duplicate prevention
    print("\n🚫 STEP 2: Setting up duplicate prevention...")
    existing_lookup = fixer.get_existing_airtable_records()
    
    # Step 3: Mark already-synced leads
    print("\n🔄 STEP 3: Marking duplicate leads as synced...")
    marked_count = fixer.mark_synced_leads_in_database(existing_lookup)
    
    # Step 4: Show what's ready for sync
    print("\n📤 STEP 4: Checking sync candidates...")
    sync_candidates = fixer.show_sync_candidates()
    
    # Summary
    print(f"\n🎉 AI MESSAGE AND DUPLICATE FIX COMPLETE!")
    print(f"   🤖 AI messages generated: {ai_fixed}")
    print(f"   🚫 Duplicates prevented: {marked_count}")
    print(f"   📤 Ready for sync: {len(sync_candidates)}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Test autonomous system: python3 real_autonomous_organism.py --test")
    print(f"   2. Should now show proper AI messages and no duplicates")
    print(f"   3. Restart autonomous mode when ready")

if __name__ == "__main__":
    main()
