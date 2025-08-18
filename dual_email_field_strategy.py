#!/usr/bin/env python3
"""
Dual Email Field Strategy
========================
Use two fields: Personal Email + Business Contact for flexible B2B outreach
"""

import sqlite3
import requests
import re
import logging
import time

class DualEmailFieldManager:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

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
            
            # Try main page and contact pages
            pages_to_check = [
                '',
                '/contact',
                '/contact-us',
                '/about'
            ]
            
            for page in pages_to_check:
                try:
                    url = website + page if page else website
                    
                    response = requests.get(url, timeout=5, headers={
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
                            r'support@[\w.-]+\.[\w]+'
                        ]
                        
                        for pattern in business_email_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                email = matches[0]
                                if not any(skip in email for skip in ['noreply', 'example', 'test']):
                                    self.logger.info(f"   ✅ Found business email: {email}")
                                    return email
                        
                        time.sleep(1)  # Rate limit
                        
                except Exception as page_error:
                    continue
            
            self.logger.info(f"   ❌ No business email found on website")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting from {website}: {e}")
            return None

    def process_lead_dual_emails(self, lead):
        """Process a lead to populate both email fields"""
        name = lead.get('Full_Name', 'Unknown')
        company = lead.get('Company', 'Unknown')
        current_email = lead.get('Email', '')
        website = lead.get('Website', '')
        
        self.logger.info(f"🔧 Processing dual emails for: {name} - {company}")
        
        result = {
            'personal_email': '',
            'business_contact': '',
            'contact_strategy': '',
            'contact_quality': ''
        }
        
        # Check current email
        if current_email and not self.is_fake_email(current_email):
            # Real personal email
            result['personal_email'] = current_email
            result['contact_strategy'] = 'personal_email'
            result['contact_quality'] = 'direct_personal'
            self.logger.info(f"   ✅ Valid personal email: {current_email}")
        else:
            # Fake or no email
            result['personal_email'] = ''
            self.logger.info(f"   ❌ Invalid/fake personal email: {current_email}")
        
        # Try to get business email from website
        if website:
            business_email = self.extract_business_email_from_website(website)
            if business_email:
                result['business_contact'] = business_email
                result['contact_strategy'] = 'business_email'
                result['contact_quality'] = 'business_direct'
                self.logger.info(f"   ✅ Found business contact: {business_email}")
            else:
                # Website exists but no email found - use website as contact
                result['business_contact'] = f"Contact form: {website}"
                result['contact_strategy'] = 'website_form'
                result['contact_quality'] = 'business_form'
                self.logger.info(f"   📋 Website contact available: {website}")
        else:
            self.logger.info(f"   ❌ No website for business contact extraction")
        
        # Determine best contact strategy
        if result['business_contact'] and '@' in result['business_contact']:
            result['preferred_contact'] = 'business'
            self.logger.info(f"   🎯 Preferred: Business email")
        elif result['personal_email']:
            result['preferred_contact'] = 'personal'
            self.logger.info(f"   🎯 Preferred: Personal email")
        elif result['business_contact']:
            result['preferred_contact'] = 'website'
            self.logger.info(f"   🎯 Preferred: Website form")
        else:
            result['preferred_contact'] = 'linkedin'
            result['contact_strategy'] = 'linkedin_message'
            result['contact_quality'] = 'social_platform'
            self.logger.info(f"   🎯 Preferred: LinkedIn outreach")
        
        return result

    def update_database_with_dual_emails(self):
        """Update all leads with dual email strategy"""
        self.logger.info("🔄 Updating all leads with dual email strategy...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            if not leads:
                self.logger.info("📋 No leads found")
                return 0
            
            updated_count = 0
            for lead in leads:
                try:
                    # Process dual emails
                    email_result = self.process_lead_dual_emails(lead)
                    
                    # Update database - use existing Email field for personal, create business strategy
                    personal_email = email_result['personal_email']
                    business_contact = email_result['business_contact']
                    contact_strategy = email_result['contact_strategy']
                    
                    # Update with clean data
                    conn.execute("""
                        UPDATE leads 
                        SET Email = ?,
                            Phone = ?,
                            Response_Status = 'enriched'
                        WHERE id = ?
                    """, (
                        personal_email,  # Clean personal email (empty if fake)
                        business_contact if '@' in business_contact else '',  # Business email in Phone field for now
                        lead['id']
                    ))
                    
                    updated_count += 1
                    
                    name = lead.get('Full_Name', 'Unknown')
                    self.logger.info(f"✅ Updated: {name}")
                    self.logger.info(f"   Personal: {personal_email if personal_email else 'None'}")
                    self.logger.info(f"   Business: {business_contact if business_contact else 'None'}")
                    self.logger.info(f"   Strategy: {contact_strategy}")
                    self.logger.info("")
                    
                    time.sleep(1)  # Rate limit
                    
                except Exception as lead_error:
                    self.logger.error(f"❌ Error updating {lead.get('Full_Name', 'Unknown')}: {lead_error}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Dual email update complete: {updated_count}/{len(leads)} leads updated")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"❌ Error updating database: {e}")
            return 0

    def show_contact_summary(self):
        """Show summary of contact methods available"""
        self.logger.info("📊 Contact method summary...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            summary = {
                'personal_email': 0,
                'business_email': 0,
                'website_contact': 0,
                'linkedin_only': 0,
                'multiple_contacts': 0
            }
            
            for lead in leads:
                personal = lead.get('Email', '')
                business = lead.get('Phone', '')  # Business email stored in Phone for now
                website = lead.get('Website', '')
                
                has_personal = bool(personal and '@' in personal)
                has_business = bool(business and '@' in business)
                has_website = bool(website)
                
                contact_count = sum([has_personal, has_business, has_website])
                
                if contact_count > 1:
                    summary['multiple_contacts'] += 1
                
                if has_personal:
                    summary['personal_email'] += 1
                if has_business:
                    summary['business_email'] += 1
                elif has_website:
                    summary['website_contact'] += 1
                elif not has_personal:
                    summary['linkedin_only'] += 1
            
            conn.close()
            
            self.logger.info(f"📊 CONTACT METHOD SUMMARY:")
            self.logger.info(f"   📧 Personal emails: {summary['personal_email']}")
            self.logger.info(f"   🏢 Business emails: {summary['business_email']}")
            self.logger.info(f"   🌐 Website contacts: {summary['website_contact']}")
            self.logger.info(f"   💼 LinkedIn only: {summary['linkedin_only']}")
            self.logger.info(f"   🎯 Multiple contacts: {summary['multiple_contacts']}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Error generating summary: {e}")
            return {}

def main():
    manager = DualEmailFieldManager()
    
    print("📧 DUAL EMAIL FIELD STRATEGY")
    print("=" * 30)
    print("📋 Two-field approach for flexible B2B outreach:")
    print("   📧 Personal Email: Individual contact (if real)")
    print("   🏢 Business Contact: Company email/website")
    print("   🎯 Choose best contact method per lead")
    print("")
    
    # Update all leads with dual email strategy
    updated_count = manager.update_database_with_dual_emails()
    
    # Show summary
    print("\n📊 Generating contact summary...")
    summary = manager.show_contact_summary()
    
    print(f"\n🎉 DUAL EMAIL STRATEGY COMPLETE!")
    print(f"   🔧 Updated: {updated_count} leads")
    print(f"   📧 Personal emails: {summary.get('personal_email', 0)}")
    print(f"   🏢 Business contacts: {summary.get('business_email', 0) + summary.get('website_contact', 0)}")
    
    print(f"\n🚀 BENEFITS:")
    print(f"   ✅ Clean separation of personal vs business contact")
    print(f"   ✅ Flexible outreach strategy per lead")
    print(f"   ✅ No fake emails cluttering the database")
    print(f"   ✅ B2B-focused business contacts")

if __name__ == "__main__":
    main()
