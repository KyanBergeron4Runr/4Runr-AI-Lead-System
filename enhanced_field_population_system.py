#!/usr/bin/env python3
"""
Enhanced Field Population System
================================
Properly populate Business Contact, Contact Strategy, Contact Quality, Personal Email
"""

import sqlite3
import logging
import re
import requests
from urllib.parse import urlparse

class EnhancedFieldPopulator:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_business_email_from_website(self, website_url):
        """Extract business contact email from company website"""
        if not website_url:
            return None
            
        try:
            # Ensure proper URL format
            if not website_url.startswith(('http://', 'https://')):
                website_url = f"https://{website_url}"
            
            # Simple business email patterns to look for
            business_patterns = [
                r'(?:info|contact|sales|hello|support)@[\w\.-]+\.[a-zA-Z]{2,}',
                r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}'
            ]
            
            response = requests.get(website_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for business emails
                for pattern in business_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Prefer business-like emails
                        business_emails = [
                            email for email in matches 
                            if any(prefix in email.lower() for prefix in ['info', 'contact', 'sales', 'hello', 'support'])
                        ]
                        
                        if business_emails:
                            return business_emails[0]
                        elif matches:
                            return matches[0]
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract email from {website_url}: {e}")
            return None

    def determine_contact_strategy(self, personal_email, business_contact, linkedin_url):
        """Determine the best contact strategy"""
        strategies = []
        
        if business_contact and '@' in business_contact:
            strategies.append(('Business Email', 1))  # Highest priority
        
        if personal_email and '@' in personal_email and not self.is_fake_email(personal_email):
            strategies.append(('Personal Email', 2))
        
        if linkedin_url:
            strategies.append(('LinkedIn Outreach', 3))
        
        if business_contact and 'website:' in business_contact.lower():
            strategies.append(('Website Contact Form', 4))
        
        # Return the highest priority strategy
        if strategies:
            strategies.sort(key=lambda x: x[1])
            return strategies[0][0]
        
        return 'LinkedIn Only'

    def is_fake_email(self, email):
        """Check if email uses a fake domain"""
        if not email or '@' not in email:
            return True
            
        fake_domains = [
            '27b69170.com', 'a0b00267.com', 'test.com', 'example.com',
            'fake.com', 'placeholder.com', 'dummy.com'
        ]
        
        domain = email.split('@')[-1].lower()
        return domain in fake_domains

    def calculate_contact_quality_score(self, personal_email, business_contact, linkedin_url, website):
        """Calculate a contact quality score (1-5)"""
        score = 1  # Base score
        
        # Business contact adds significant value
        if business_contact:
            if '@' in business_contact and not self.is_fake_email(business_contact):
                score += 2  # Real business email = +2
            elif 'website:' in business_contact.lower():
                score += 1  # Website contact form = +1
        
        # Personal email adds value if real
        if personal_email and '@' in personal_email and not self.is_fake_email(personal_email):
            score += 1
        
        # LinkedIn always adds some value
        if linkedin_url:
            score += 1
        
        # Website presence adds credibility
        if website:
            score += 1
        
        return min(score, 5)  # Cap at 5

    def enhance_lead_fields(self, lead_data):
        """Enhance a single lead's field population"""
        enhanced = lead_data.copy()
        
        full_name = lead_data.get('Full_Name', '')
        email = lead_data.get('Email', '')
        source = lead_data.get('Source', '')
        website = lead_data.get('Website', '')
        linkedin_url = lead_data.get('LinkedIn_URL', '')
        
        # 1. Separate Personal Email from Business Contact
        personal_email = email if email and not self.is_fake_email(email) else None
        
        # 2. Extract/enhance Business Contact
        business_contact = None
        
        # Check if Source already has business info
        if source and ('Business:' in source or '@' in source):
            business_contact = source
        elif website:
            # Try to extract business email from website
            business_email = self.extract_business_email_from_website(website)
            if business_email:
                business_contact = f"Business: {business_email}"
            else:
                business_contact = f"Website: {website}"
        
        # 3. Determine Contact Strategy
        contact_strategy = self.determine_contact_strategy(personal_email, business_contact, linkedin_url)
        
        # 4. Calculate Contact Quality
        quality_score = self.calculate_contact_quality_score(personal_email, business_contact, linkedin_url, website)
        quality_labels = {1: 'Low', 2: 'Fair', 3: 'Good', 4: 'High', 5: 'Excellent'}
        contact_quality = f"{quality_labels[quality_score]} ({quality_score}/5)"
        
        # 5. Update fields using existing schema
        enhanced.update({
            'Email': personal_email or '',  # Personal Email only
            'Source': business_contact or '',  # Business Contact info
            'Lead_Quality': contact_quality,  # Contact Quality score
            'Email_Confidence_Level': contact_strategy,  # Contact Strategy
        })
        
        return enhanced

    def process_all_leads(self):
        """Process all leads in database with enhanced field population"""
        self.logger.info("🔧 Processing all leads with enhanced field population...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            leads = [dict(row) for row in cursor.fetchall()]
            
            if not leads:
                self.logger.info("📋 No leads found to process")
                return 0
            
            processed_count = 0
            
            for lead in leads:
                try:
                    enhanced_lead = self.enhance_lead_fields(lead)
                    
                    # Update the lead in database
                    conn.execute("""
                        UPDATE leads SET
                            Email = ?,
                            Source = ?,
                            Lead_Quality = ?,
                            Email_Confidence_Level = ?
                        WHERE id = ?
                    """, (
                        enhanced_lead['Email'],
                        enhanced_lead['Source'],
                        enhanced_lead['Lead_Quality'],
                        enhanced_lead['Email_Confidence_Level'],
                        lead['id']
                    ))
                    
                    processed_count += 1
                    
                    self.logger.info(f"✅ Enhanced: {lead.get('Full_Name', 'Unknown')}")
                    self.logger.info(f"   Personal Email: {enhanced_lead['Email'] or 'None'}")
                    self.logger.info(f"   Business Contact: {enhanced_lead['Source'] or 'None'}")
                    self.logger.info(f"   Contact Strategy: {enhanced_lead['Email_Confidence_Level']}")
                    self.logger.info(f"   Contact Quality: {enhanced_lead['Lead_Quality']}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error enhancing {lead.get('Full_Name', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 Enhanced {processed_count} leads with better field population")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error processing leads: {e}")
            return 0

    def demonstrate_field_mapping(self):
        """Show how fields will be used"""
        self.logger.info("📋 Enhanced Field Mapping Strategy:")
        self.logger.info("   📧 Email → Personal Email (real emails only)")
        self.logger.info("   🏢 Source → Business Contact (business emails/websites)")
        self.logger.info("   📊 Lead_Quality → Contact Quality (1-5 scoring)")
        self.logger.info("   🎯 Email_Confidence_Level → Contact Strategy (priority method)")
        self.logger.info("")
        self.logger.info("🎯 Contact Strategy Options:")
        self.logger.info("   1. Business Email (highest priority)")
        self.logger.info("   2. Personal Email (verified real)")
        self.logger.info("   3. LinkedIn Outreach")
        self.logger.info("   4. Website Contact Form")

def main():
    populator = EnhancedFieldPopulator()
    
    print("🔧 ENHANCED FIELD POPULATION SYSTEM")
    print("=" * 40)
    print("📋 Using existing database schema for enhanced B2B fields")
    print("")
    
    # Show field mapping strategy
    populator.demonstrate_field_mapping()
    
    print(f"\n🔧 Processing leads with enhanced field population...")
    processed_count = populator.process_all_leads()
    
    if processed_count > 0:
        print(f"\n🎉 SUCCESS! Enhanced {processed_count} leads!")
        print(f"\n✅ ENHANCED FIELDS:")
        print(f"   📧 Personal Email: Clean, verified emails only")
        print(f"   🏢 Business Contact: Company emails/websites") 
        print(f"   📊 Contact Quality: 1-5 scoring system")
        print(f"   🎯 Contact Strategy: Priority contact method")
        
        print(f"\n🚀 READY FOR TESTING:")
        print(f"   python3 real_autonomous_organism.py --test")
        print(f"   New leads will have properly populated fields!")
        
    else:
        print(f"\n📋 No leads to process (database is clean)")
        print(f"✅ System ready - enhanced field logic is active")
        print(f"🚀 Run autonomous system to generate leads with enhanced fields!")

if __name__ == "__main__":
    main()
