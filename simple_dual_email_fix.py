#!/usr/bin/env python3
"""
Simple Dual Email Fix
====================
Use existing database columns for dual email strategy
"""

import sqlite3
import requests
import re
import logging
import time

class SimpleDualEmailFix:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def check_database_schema(self):
        """Check what columns exist in the database"""
        self.logger.info("🔍 Checking database schema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("PRAGMA table_info(leads)")
            columns = [row[1] for row in cursor.fetchall()]  # Get column names
            conn.close()
            
            self.logger.info(f"📊 Available columns: {columns}")
            return columns
            
        except Exception as e:
            self.logger.error(f"❌ Error checking schema: {e}")
            return []

    def is_fake_email(self, email):
        """Check if email is fake LinkedIn domain"""
        if not email or '@' not in email:
            return True
        
        domain = email.split('@')[1].lower()
        
        # Fake LinkedIn patterns
        fake_patterns = [
            r'^[a-f0-9]{8}\.com$',  # Hex domains like 27b69170.com
            r'^[a-f0-9]{7,10}\.com$'  # Similar patterns
        ]
        
        for pattern in fake_patterns:
            if re.match(pattern, domain):
                return True
        
        return False

    def extract_business_email_from_website(self, website):
        """Extract business contact email from company website"""
        if not website:
            return None
        
        self.logger.info(f"🌐 Extracting business email from: {website}")
        
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Priority order for business emails
                business_email_patterns = [
                    r'info@[\w.-]+\.[\w]+',
                    r'contact@[\w.-]+\.[\w]+', 
                    r'sales@[\w.-]+\.[\w]+',
                    r'hello@[\w.-]+\.[\w]+',
                ]
                
                for pattern in business_email_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        email = matches[0]
                        if not any(skip in email for skip in ['noreply', 'example', 'test']):
                            self.logger.info(f"   ✅ Found business email: {email}")
                            return email
            
            self.logger.info(f"   ❌ No business email found")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting from {website}: {e}")
            return None

    def update_leads_with_existing_columns(self):
        """Update leads using only existing database columns"""
        self.logger.info("🔧 Updating leads with existing columns...")
        
        # Check what columns we have
        columns = self.check_database_schema()
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            updated_count = 0
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                current_email = lead.get('Email', '')
                website = lead.get('Website', '')
                
                self.logger.info(f"🔧 Processing: {name} - {company}")
                
                # Process emails
                personal_email = ''
                business_contact = ''
                contact_strategy = ''
                
                # Check current email
                if current_email and not self.is_fake_email(current_email):
                    personal_email = current_email
                    contact_strategy = 'personal_email'
                    self.logger.info(f"   ✅ Valid personal email: {current_email}")
                else:
                    self.logger.info(f"   ❌ Invalid/fake personal email: {current_email}")
                
                # Try to get business email from website
                if website:
                    business_email = self.extract_business_email_from_website(website)
                    if business_email:
                        business_contact = business_email
                        contact_strategy = 'business_email'
                        self.logger.info(f"   ✅ Business contact: {business_email}")
                    else:
                        business_contact = f"Website: {website}"
                        contact_strategy = 'website_form'
                        self.logger.info(f"   🌐 Website contact: {website}")
                else:
                    contact_strategy = 'linkedin_outreach'
                    self.logger.info(f"   💼 LinkedIn outreach only")
                
                # Update using existing columns creatively
                # Email = Personal email (clean)
                # Job_Title = Store contact strategy
                # LinkedIn_URL = Keep as is
                # Website = Keep as is
                
                update_fields = {
                    'Email': personal_email,  # Clean personal email only
                    'Response_Status': 'enriched'
                }
                
                # Store business contact in a creative way using existing columns
                if business_contact and '@' in business_contact:
                    # Store business email in a notes field or append to existing data
                    update_fields['Source'] = f"Business: {business_contact}"
                elif business_contact:
                    update_fields['Source'] = business_contact
                
                # Build update query
                set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
                values = list(update_fields.values()) + [lead['id']]
                
                conn.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", values)
                
                updated_count += 1
                self.logger.info(f"   ✅ Updated: Clean email + business contact info")
                self.logger.info("")
                
                time.sleep(1)  # Rate limit
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Update complete: {updated_count}/{len(leads)} leads updated")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"❌ Error updating leads: {e}")
            return 0

    def show_cleaned_results(self):
        """Show the cleaned results"""
        self.logger.info("📊 Showing cleaned results...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            self.logger.info(f"📋 CLEANED LEADS:")
            
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', 'Unknown')
                email = lead.get('Email', '')
                source = lead.get('Source', '')
                website = lead.get('Website', '')
                
                self.logger.info(f"   {name} - {company}")
                self.logger.info(f"      Personal Email: {email if email else 'None'}")
                self.logger.info(f"      Business Contact: {source if 'Business:' in source else 'None'}")
                self.logger.info(f"      Website: {website if website else 'None'}")
                
                # Determine contact method
                if email and '@' in email:
                    contact_method = "✅ Personal Email"
                elif 'Business:' in source and '@' in source:
                    contact_method = "✅ Business Email"
                elif website:
                    contact_method = "🌐 Website Form"
                else:
                    contact_method = "💼 LinkedIn Only"
                
                self.logger.info(f"      Contact Method: {contact_method}")
                self.logger.info("")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error showing results: {e}")

def main():
    fixer = SimpleDualEmailFix()
    
    print("🔧 SIMPLE DUAL EMAIL FIX")
    print("=" * 27)
    print("📋 Use existing database columns for dual email strategy")
    print("")
    
    # Update leads
    updated_count = fixer.update_leads_with_existing_columns()
    
    # Show results
    print("\n📊 Showing cleaned results...")
    fixer.show_cleaned_results()
    
    print(f"\n🎉 SIMPLE FIX COMPLETE!")
    print(f"   🔧 Updated: {updated_count} leads")
    print(f"   📧 Email field: Clean personal emails only")
    print(f"   🏢 Source field: Business contact info")
    print(f"   🌐 Website field: Company websites")
    
    print(f"\n📋 AIRTABLE FIELDS TO ADD:")
    print(f"   1. Business Contact (Single line text)")
    print(f"   2. Contact Strategy (Single select)")
    print(f"   3. Personal Email (rename existing Email)")

if __name__ == "__main__":
    main()
