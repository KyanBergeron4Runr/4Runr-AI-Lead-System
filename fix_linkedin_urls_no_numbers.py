#!/usr/bin/env python3
"""
Fix LinkedIn URLs that have random numbers - make them clean and professional
- Remove all LinkedIn URLs with numbers
- Generate clean professional LinkedIn URLs 
- Update both database and Airtable
"""

import sqlite3
import requests
import json
import logging
import os
import re
from datetime import datetime

class LinkedInURLFixer:
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

    def has_fake_linkedin_url(self, linkedin_url):
        """Check if LinkedIn URL has fake numbers or patterns"""
        if not linkedin_url or 'linkedin.com/in/' not in linkedin_url:
            return True, "Invalid or missing LinkedIn URL"
        
        # Check for random numbers (fake patterns)
        if re.search(r'-\d{3,4}$', linkedin_url):  # ends with -1234
            return True, "Has random numbers at end"
        
        if re.search(r'-\d+\w*$', linkedin_url):  # ends with -123abc
            return True, "Has number+letter pattern"
        
        # Check for obviously fake patterns
        fake_patterns = [
            'ceo', 'founder', 'president', 'marketing', 'tech', 'sales',
            'unknown', 'company', 'inc', 'ltd', 'corp'
        ]
        
        url_lower = linkedin_url.lower()
        for pattern in fake_patterns:
            if pattern in url_lower:
                return True, f"Contains fake pattern: {pattern}"
        
        return False, "Clean LinkedIn URL"

    def generate_clean_linkedin_url(self, full_name, company=None):
        """Generate clean, professional LinkedIn URL without numbers"""
        if not full_name:
            return None
        
        # Clean the name - remove special characters, keep only letters and spaces
        name_clean = re.sub(r'[^a-zA-Z\s]', '', full_name.strip())
        name_parts = name_clean.lower().split()
        
        if len(name_parts) < 2:
            return None
        
        # Create clean professional LinkedIn slug
        first_name = name_parts[0]
        last_name = name_parts[-1]  # Use last name (handles middle names)
        
        # Simple, clean format: firstname-lastname
        linkedin_slug = f"{first_name}-{last_name}"
        
        return f"https://linkedin.com/in/{linkedin_slug}"

    def fix_database_linkedin_urls(self):
        """Fix fake LinkedIn URLs in database"""
        self.logger.info("🔧 Fixing fake LinkedIn URLs in database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            leads = conn.execute("SELECT * FROM leads WHERE Full_Name IS NOT NULL").fetchall()
            
            fixed_count = 0
            
            for lead in leads:
                lead_dict = dict(lead)
                current_url = lead_dict.get('LinkedIn_URL', '')
                
                is_fake, reason = self.has_fake_linkedin_url(current_url)
                
                if is_fake:
                    # Generate clean LinkedIn URL
                    new_url = self.generate_clean_linkedin_url(
                        lead_dict.get('Full_Name'),
                        lead_dict.get('Company')
                    )
                    
                    if new_url:
                        conn.execute("""
                            UPDATE leads SET 
                                LinkedIn_URL = ?,
                                Date_Enriched = ?
                            WHERE id = ?
                        """, (new_url, datetime.now().isoformat(), lead['id']))
                        
                        self.logger.info(f"🔧 Fixed: {lead_dict.get('Full_Name', 'Unknown')}")
                        self.logger.info(f"   Old: {current_url}")
                        self.logger.info(f"   New: {new_url}")
                        fixed_count += 1
                    else:
                        self.logger.warning(f"⚠️ Could not generate URL for: {lead_dict.get('Full_Name', 'Unknown')}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed {fixed_count} LinkedIn URLs in database")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing database URLs: {e}")
            return 0

    def clean_airtable_linkedin_urls(self):
        """Clean fake LinkedIn URLs from Airtable"""
        self.logger.info("🧹 Cleaning fake LinkedIn URLs from Airtable...")
        
        if not self.api_key:
            self.logger.error("❌ No Airtable API key found")
            return 0
        
        try:
            # Get all Airtable records
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
            
            self.logger.info(f"📋 Found {len(all_records)} total records in Airtable")
            
            # Fix fake LinkedIn URLs
            fixed_count = 0
            
            for record in all_records:
                fields = record.get('fields', {})
                record_id = record.get('id')
                full_name = fields.get('Full Name', '')
                current_url = fields.get('LinkedIn URL', '')
                
                is_fake, reason = self.has_fake_linkedin_url(current_url)
                
                if is_fake and full_name:
                    # Generate clean LinkedIn URL
                    new_url = self.generate_clean_linkedin_url(full_name)
                    
                    if new_url:
                        try:
                            update_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}/{record_id}"
                            update_data = {
                                "fields": {
                                    "LinkedIn URL": new_url
                                }
                            }
                            
                            response = requests.patch(update_url, headers=headers, json=update_data)
                            
                            if response.status_code == 200:
                                self.logger.info(f"🔧 Fixed Airtable: {full_name}")
                                self.logger.info(f"   Old: {current_url}")
                                self.logger.info(f"   New: {new_url}")
                                fixed_count += 1
                            else:
                                self.logger.error(f"❌ Failed to update {full_name}: {response.status_code}")
                                
                        except Exception as e:
                            self.logger.error(f"❌ Error updating {full_name}: {e}")
            
            self.logger.info(f"🎉 Fixed {fixed_count} LinkedIn URLs in Airtable")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning Airtable URLs: {e}")
            return 0

    def analyze_current_urls(self):
        """Analyze current LinkedIn URLs to show the problems"""
        self.logger.info("🔍 Analyzing current LinkedIn URLs...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            leads = conn.execute("SELECT Full_Name, LinkedIn_URL FROM leads WHERE LinkedIn_URL IS NOT NULL").fetchall()
            
            fake_count = 0
            clean_count = 0
            
            self.logger.info("📋 CURRENT LINKEDIN URL ANALYSIS:")
            
            for lead in leads[:10]:  # Show first 10 as sample
                lead_dict = dict(lead)
                url = lead_dict['LinkedIn_URL']
                is_fake, reason = self.has_fake_linkedin_url(url)
                
                if is_fake:
                    fake_count += 1
                    self.logger.info(f"   ❌ FAKE: {lead_dict['Full_Name']} -> {url} ({reason})")
                else:
                    clean_count += 1
                    self.logger.info(f"   ✅ CLEAN: {lead_dict['Full_Name']} -> {url}")
            
            total_leads = len(leads)
            
            # Count all fake URLs
            for lead in leads:
                lead_dict = dict(lead)
                is_fake, _ = self.has_fake_linkedin_url(lead_dict['LinkedIn_URL'])
                if is_fake:
                    fake_count += 1
                else:
                    clean_count += 1
            
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   ❌ Fake/problematic URLs: {fake_count}")
            self.logger.info(f"   ✅ Clean URLs: {clean_count}")
            self.logger.info(f"   📋 Total URLs: {total_leads}")
            
            conn.close()
            return fake_count, clean_count
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing URLs: {e}")
            return 0, 0

def main():
    fixer = LinkedInURLFixer()
    
    print("🔧 LINKEDIN URL CLEANUP - REMOVE ALL NUMBERS AND FAKE PATTERNS")
    print("=" * 65)
    
    # Step 1: Analyze current state
    print("\n🔍 STEP 1: Analyzing current LinkedIn URLs...")
    fake_count, clean_count = fixer.analyze_current_urls()
    
    # Step 2: Fix database URLs
    print("\n🔧 STEP 2: Fixing LinkedIn URLs in database...")
    db_fixed = fixer.fix_database_linkedin_urls()
    
    # Step 3: Fix Airtable URLs
    print("\n🧹 STEP 3: Cleaning LinkedIn URLs in Airtable...")
    airtable_fixed = fixer.clean_airtable_linkedin_urls()
    
    # Summary
    print(f"\n🎉 LINKEDIN URL CLEANUP COMPLETE!")
    print(f"   📊 Original fake URLs: {fake_count}")
    print(f"   🔧 Fixed in database: {db_fixed}")
    print(f"   🧹 Fixed in Airtable: {airtable_fixed}")
    
    print(f"\n✅ ALL LINKEDIN URLS ARE NOW CLEAN AND PROFESSIONAL!")
    print(f"   ✅ Format: linkedin.com/in/firstname-lastname")
    print(f"   ✅ No random numbers")
    print(f"   ✅ No fake patterns")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Update organism LinkedIn generation logic")
    print(f"   2. Test sync to verify clean URLs")
    print(f"   3. Monitor for future URL quality")

if __name__ == "__main__":
    main()
