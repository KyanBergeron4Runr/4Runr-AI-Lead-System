#!/usr/bin/env python3
"""
Fix Fake LinkedIn Email Domains
==============================
Replace fake LinkedIn emails with website-based email extraction
"""

import sqlite3
import requests
import re
import logging
from urllib.parse import urlparse
import time

class LinkedInEmailFixer:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def is_fake_linkedin_email(self, email):
        """Check if email is a fake LinkedIn domain"""
        if not email or '@' not in email:
            return True
            
        domain = email.split('@')[1].lower()
        
        # Known fake LinkedIn domains
        fake_domains = [
            'a0b00267.com',
            '27b69170.com',
            # Add more as we discover them
        ]
        
        # Check for hex pattern domains (LinkedIn generates these)
        hex_pattern = re.match(r'^[a-f0-9]{8}\.com$', domain)
        
        return domain in fake_domains or bool(hex_pattern)

    def extract_company_website(self, company_name, linkedin_url=None):
        """Try to find company website from company name"""
        if not company_name or company_name.lower() in ['unknown company', 'unknown']:
            return None
            
        # Common website patterns
        company_clean = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        company_clean = company_clean.replace(' ', '')
        
        # Try common patterns
        possible_domains = [
            f"www.{company_clean}.com",
            f"{company_clean}.com",
            f"www.{company_clean}.ca",  # Canadian companies
            f"{company_clean}.ca",
        ]
        
        for domain in possible_domains:
            try:
                response = requests.head(f"https://{domain}", timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    self.logger.info(f"✅ Found website: {domain}")
                    return domain
            except:
                continue
                
        return None

    def extract_email_from_website(self, website):
        """Try to extract email from company website"""
        if not website:
            return None
            
        try:
            # Add protocol if missing
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return None
            
            content = response.text.lower()
            
            # Look for contact emails
            email_patterns = [
                r'contact@[\w.-]+\.[\w]+',
                r'info@[\w.-]+\.[\w]+',
                r'hello@[\w.-]+\.[\w]+',
                r'[\w.-]+@[\w.-]+\.[\w]+',
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Return the first valid-looking email
                    for email in matches:
                        if not any(skip in email for skip in ['noreply', 'example', 'test']):
                            return email
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting email from {website}: {e}")
            
        return None

    def fix_lead_contact_info(self, lead):
        """Fix a lead's contact information"""
        name = lead.get('Full_Name', 'Unknown')
        company = lead.get('Company', '')
        email = lead.get('Email', '')
        linkedin_url = lead.get('LinkedIn_URL', '')
        
        self.logger.info(f"🔧 Fixing contact info for: {name}")
        
        # Check if email is fake
        if not self.is_fake_linkedin_email(email):
            self.logger.info(f"   ✅ Email is valid: {email}")
            return lead
        
        self.logger.info(f"   ❌ Fake email detected: {email}")
        
        # Try to find company website
        website = self.extract_company_website(company, linkedin_url)
        
        if website:
            self.logger.info(f"   🌐 Found website: {website}")
            
            # Try to extract real email
            real_email = self.extract_email_from_website(website)
            
            if real_email:
                self.logger.info(f"   📧 Found real email: {real_email}")
                lead['Email'] = real_email
                lead['Website'] = website
                lead['Contact_Source'] = 'website_extraction'
                return lead
            else:
                self.logger.info(f"   ⚠️ No email found on website, but website is valuable")
                lead['Email'] = ''  # Clear fake email
                lead['Website'] = website
                lead['Contact_Source'] = 'website_only'
                return lead
        
        # If no website found, clear fake email but keep other data
        self.logger.info(f"   ❌ No website found, clearing fake email")
        lead['Email'] = ''
        lead['Contact_Source'] = 'linkedin_only'
        
        return lead

    def fix_all_fake_emails(self):
        """Fix all leads with fake LinkedIn emails"""
        self.logger.info("🔧 Fixing all fake LinkedIn emails...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Find leads with fake emails
            cursor = conn.execute("SELECT * FROM leads")
            all_leads = [dict(row) for row in cursor.fetchall()]
            
            fake_email_leads = []
            for lead in all_leads:
                if self.is_fake_linkedin_email(lead.get('Email', '')):
                    fake_email_leads.append(lead)
            
            if not fake_email_leads:
                self.logger.info("✅ No fake emails found")
                return 0
            
            self.logger.info(f"🔧 Found {len(fake_email_leads)} leads with fake emails")
            
            fixed_count = 0
            for lead in fake_email_leads:
                try:
                    fixed_lead = self.fix_lead_contact_info(lead)
                    
                    # Update database
                    conn.execute('''
                        UPDATE leads 
                        SET Email = ?, Website = ?, Contact_Source = ?
                        WHERE id = ?
                    ''', (
                        fixed_lead.get('Email', ''),
                        fixed_lead.get('Website', ''),
                        fixed_lead.get('Contact_Source', 'unknown'),
                        lead['id']
                    ))
                    
                    fixed_count += 1
                    self.logger.info(f"✅ Fixed: {lead.get('Full_Name', 'Unknown')}")
                    
                    # Rate limit to be nice to websites
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error fixing {lead.get('Full_Name', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed {fixed_count} leads with fake emails")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing fake emails: {e}")
            return 0

    def validate_fixed_leads(self):
        """Check if fixed leads now pass validation"""
        self.logger.info("✅ Validating fixed leads...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            all_leads = [dict(row) for row in cursor.fetchall()]
            
            syncable_count = 0
            for lead in all_leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', '')
                email = lead.get('Email', '')
                website = lead.get('Website', '')
                
                # Check if lead is now syncable
                has_contact = bool(email and not self.is_fake_linkedin_email(email)) or bool(website)
                has_company = company and company.lower() not in ['unknown company', 'unknown', '']
                
                if has_contact and has_company:
                    syncable_count += 1
                    self.logger.info(f"✅ {name} - Ready for sync")
                    self.logger.info(f"   Company: {company}")
                    self.logger.info(f"   Contact: {email or website}")
                else:
                    self.logger.info(f"❌ {name} - Still needs work")
                    if not has_company:
                        self.logger.info(f"   Missing: Real company name")
                    if not has_contact:
                        self.logger.info(f"   Missing: Real contact method")
            
            conn.close()
            
            self.logger.info(f"📊 {syncable_count}/{len(all_leads)} leads ready for sync")
            return syncable_count
            
        except Exception as e:
            self.logger.error(f"❌ Error validating leads: {e}")
            return 0

def main():
    fixer = LinkedInEmailFixer()
    
    print("🔧 LINKEDIN FAKE EMAIL FIXER")
    print("=" * 30)
    print("📋 Purpose: Replace fake LinkedIn emails with real website contact info")
    print("✅ Strategy:")
    print("   1. Detect fake LinkedIn email domains")
    print("   2. Find company websites")
    print("   3. Extract real contact emails")
    print("   4. Clear fake emails if no real ones found")
    print("")
    
    # Fix fake emails
    print("🔧 Fixing fake LinkedIn emails...")
    fixed_count = fixer.fix_all_fake_emails()
    
    # Validate results
    print("\n✅ Validating fixed leads...")
    syncable_count = fixer.validate_fixed_leads()
    
    print(f"\n🎉 EMAIL FIXING COMPLETE!")
    print(f"   🔧 Fixed: {fixed_count} fake emails")
    print(f"   ✅ Ready for sync: {syncable_count} leads")
    
    if syncable_count > 0:
        print(f"\n🚀 NEXT: Test autonomous system")
        print(f"   python3 real_autonomous_organism.py --test")
    else:
        print(f"\n📋 NEXT: Need to get leads with real contact info")
        print(f"   - Try different scraping sources")
        print(f"   - Focus on companies with public websites")

if __name__ == "__main__":
    main()
