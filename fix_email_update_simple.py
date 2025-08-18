#!/usr/bin/env python3
"""
Simple Email Fix - Update existing columns only
==============================================
Fix fake LinkedIn emails using only existing database columns
"""

import sqlite3
import requests
import re
import logging
import time

class SimpleEmailFixer:
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
        ]
        
        # Check for hex pattern domains
        hex_pattern = re.match(r'^[a-f0-9]{8}\.com$', domain)
        
        return domain in fake_domains or bool(hex_pattern)

    def get_company_website(self, company_name):
        """Get company website"""
        if not company_name or company_name.lower() in ['unknown company', 'unknown']:
            return None
            
        # For known companies, use direct mapping
        company_lower = company_name.lower()
        
        known_websites = {
            'cgi': 'www.cgi.com',
            'bombardier': 'www.bombardier.com',
            'shopify': 'www.shopify.com',
            'desjardins': 'www.desjardins.com'
        }
        
        for company_key, website in known_websites.items():
            if company_key in company_lower:
                return website
        
        # Try common patterns
        company_clean = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
        possible_domains = [
            f"www.{company_clean}.com",
            f"www.{company_clean}.ca",
        ]
        
        for domain in possible_domains:
            try:
                response = requests.head(f"https://{domain}", timeout=3, allow_redirects=True)
                if response.status_code == 200:
                    return domain
            except:
                continue
                
        return None

    def get_company_email(self, website):
        """Get company email from website"""
        if not website:
            return None
            
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return None
            
            content = response.text.lower()
            
            # Look for contact emails
            email_patterns = [
                r'info@[\w.-]+\.[\w]+',
                r'contact@[\w.-]+\.[\w]+',
                r'hello@[\w.-]+\.[\w]+',
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return matches[0]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting email from {website}: {e}")
            
        return None

    def fix_leads_simple(self):
        """Fix leads using only existing database columns"""
        self.logger.info("🔧 Fixing fake emails with simple update...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get leads with fake emails
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            fixed_count = 0
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', '')
                email = lead.get('Email', '')
                
                if not self.is_fake_linkedin_email(email):
                    continue
                
                self.logger.info(f"🔧 Fixing: {name} - {company}")
                self.logger.info(f"   Fake email: {email}")
                
                # Get company website
                website = self.get_company_website(company)
                if website:
                    self.logger.info(f"   Found website: {website}")
                    
                    # Get real email
                    real_email = self.get_company_email(website)
                    if real_email:
                        self.logger.info(f"   Found real email: {real_email}")
                        
                        # Update with real email and website
                        conn.execute("""
                            UPDATE leads 
                            SET Email = ?, Website = ?
                            WHERE id = ?
                        """, (real_email, website, lead['id']))
                        
                        fixed_count += 1
                        self.logger.info(f"   ✅ Updated with real contact info")
                    else:
                        # No email found, but website is valuable
                        conn.execute("""
                            UPDATE leads 
                            SET Email = '', Website = ?
                            WHERE id = ?
                        """, (website, lead['id']))
                        
                        self.logger.info(f"   ✅ Updated with website (no email found)")
                else:
                    # No website found, clear fake email
                    conn.execute("""
                        UPDATE leads 
                        SET Email = ''
                        WHERE id = ?
                    """, (lead['id'],))
                    
                    self.logger.info(f"   ⚠️ Cleared fake email (no website found)")
                
                time.sleep(1)  # Be nice to websites
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Fixed {fixed_count} leads")
            return fixed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error fixing leads: {e}")
            return 0

    def check_results(self):
        """Check the results after fixing"""
        self.logger.info("📊 Checking results...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            self.logger.info(f"📋 Updated leads status:")
            
            syncable_count = 0
            for lead in leads:
                name = lead.get('Full_Name', 'Unknown')
                company = lead.get('Company', '')
                email = lead.get('Email', '')
                website = lead.get('Website', '')
                
                self.logger.info(f"   {name}:")
                self.logger.info(f"      Company: {company}")
                self.logger.info(f"      Email: {email if email else 'None'}")
                self.logger.info(f"      Website: {website if website else 'None'}")
                
                # Check if syncable
                has_real_email = email and not self.is_fake_linkedin_email(email)
                has_website = website and website.strip()
                has_real_company = company and company.lower() not in ['unknown company', 'unknown', '']
                
                if (has_real_email or has_website) and has_real_company:
                    syncable_count += 1
                    self.logger.info(f"      Status: ✅ READY FOR SYNC")
                else:
                    self.logger.info(f"      Status: ❌ Needs more work")
                
                self.logger.info("")
            
            conn.close()
            
            self.logger.info(f"📊 {syncable_count}/{len(leads)} leads ready for sync")
            return syncable_count
            
        except Exception as e:
            self.logger.error(f"❌ Error checking results: {e}")
            return 0

def main():
    fixer = SimpleEmailFixer()
    
    print("🔧 SIMPLE EMAIL FIXER")
    print("=" * 25)
    print("📋 Fix fake LinkedIn emails using existing database columns")
    print("")
    
    # Fix emails
    fixed_count = fixer.fix_leads_simple()
    
    # Check results
    syncable_count = fixer.check_results()
    
    print(f"\n🎉 SIMPLE FIX COMPLETE!")
    print(f"   🔧 Processed: {fixed_count} leads")
    print(f"   ✅ Ready for sync: {syncable_count} leads")
    
    if syncable_count > 0:
        print(f"\n🚀 TEST THE FIXED SYSTEM:")
        print(f"   python3 real_autonomous_organism.py --test")

if __name__ == "__main__":
    main()
