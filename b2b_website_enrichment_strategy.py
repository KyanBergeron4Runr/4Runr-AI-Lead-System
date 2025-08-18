#!/usr/bin/env python3
"""
B2B Website Enrichment Strategy
==============================
Focus on websites for B2B lead enrichment instead of individual emails
"""

import sqlite3
import requests
import re
import logging
from urllib.parse import urljoin, urlparse
import time

class B2BWebsiteEnricher:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_business_contact_info(self, website):
        """Extract business contact information from website"""
        if not website:
            return {}
        
        self.logger.info(f"🌐 Analyzing website: {website}")
        
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            # Try different contact pages
            contact_pages = [
                '',  # Main page
                '/contact',
                '/contact-us',
                '/about',
                '/about-us',
                '/support',
                '/sales'
            ]
            
            contact_info = {}
            
            for page_path in contact_pages:
                try:
                    url = urljoin(website, page_path)
                    
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        content = response.text.lower()
                        
                        # Extract business emails (prioritize general business emails)
                        email_patterns = [
                            r'info@[\w.-]+\.[\w]+',
                            r'contact@[\w.-]+\.[\w]+',
                            r'sales@[\w.-]+\.[\w]+',
                            r'hello@[\w.-]+\.[\w]+',
                            r'support@[\w.-]+\.[\w]+',
                            r'business@[\w.-]+\.[\w]+',
                        ]
                        
                        for pattern in email_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                email = matches[0]
                                if not any(skip in email for skip in ['noreply', 'example', 'test']):
                                    contact_info['business_email'] = email
                                    self.logger.info(f"   📧 Found business email: {email}")
                                    break
                        
                        # Extract phone numbers
                        phone_patterns = [
                            r'\+?1?\s*\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})',
                            r'\+?1?\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',
                        ]
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, content)
                            if matches and not contact_info.get('phone'):
                                phone = ''.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
                                contact_info['phone'] = f"+1{phone}"
                                self.logger.info(f"   📞 Found phone: {contact_info['phone']}")
                                break
                        
                        # Extract company description
                        if not contact_info.get('description'):
                            # Look for meta description
                            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', response.text)
                            if desc_match:
                                contact_info['description'] = desc_match.group(1)[:200]
                                self.logger.info(f"   📝 Found description: {contact_info['description'][:50]}...")
                        
                        # Stop if we found key contact info
                        if contact_info.get('business_email'):
                            break
                            
                except Exception as page_error:
                    self.logger.debug(f"   ⚠️ Could not check {page_path}: {page_error}")
                    continue
                
                time.sleep(1)  # Be nice to websites
            
            return contact_info
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing website {website}: {e}")
            return {}

    def enrich_lead_with_website_data(self, lead):
        """Enrich a lead using their website"""
        name = lead.get('Full_Name', 'Unknown')
        company = lead.get('Company', 'Unknown')
        website = lead.get('Website', '')
        
        self.logger.info(f"🔧 Enriching B2B lead: {name} - {company}")
        
        if not website:
            self.logger.info(f"   ❌ No website to analyze")
            return lead
        
        # Extract business contact info
        contact_info = self.extract_business_contact_info(website)
        
        # Update lead with business contact info
        if contact_info.get('business_email'):
            lead['Business_Email'] = contact_info['business_email']
            lead['Contact_Method'] = 'business_email'
            self.logger.info(f"   ✅ Added business email: {contact_info['business_email']}")
        else:
            lead['Contact_Method'] = 'website_form'
            self.logger.info(f"   📋 No email found - will use website contact form")
        
        if contact_info.get('phone'):
            lead['Business_Phone'] = contact_info['phone']
            self.logger.info(f"   ✅ Added business phone: {contact_info['phone']}")
        
        if contact_info.get('description'):
            lead['Company_Description'] = contact_info['description']
            self.logger.info(f"   ✅ Added company description")
        
        # Mark as B2B enriched
        lead['Enrichment_Type'] = 'b2b_website'
        lead['Contact_Quality'] = 'business_focused'
        
        return lead

    def update_lead_for_b2b_outreach(self, lead):
        """Update lead data optimized for B2B outreach"""
        
        # Create B2B outreach message
        name = lead.get('Full_Name', 'Unknown')
        company = lead.get('Company', 'Unknown')
        business_email = lead.get('Business_Email', '')
        website = lead.get('Website', '')
        
        if business_email:
            outreach_strategy = f"Direct business email to {business_email}"
        elif website:
            outreach_strategy = f"Website contact form at {website}"
        else:
            outreach_strategy = "LinkedIn outreach"
        
        # B2B focused AI message
        ai_message = f"""Subject: Partnership Opportunity - 4Runr & {company}

Hi {company} team,

I came across {company} and was impressed by your business. We're 4Runr, and we help companies like yours streamline operations and grow revenue.

I'd love to explore how we might work together. {name} seems like the right person to connect with about this.

Could we schedule a brief call to discuss potential synergies?

Best regards,
4Runr Business Development

Contact: {outreach_strategy}"""

        lead['AI_Message'] = ai_message
        lead['Outreach_Strategy'] = outreach_strategy
        lead['Target_Type'] = 'b2b_business'
        
        return lead

    def process_all_website_leads(self):
        """Process all leads with websites for B2B enrichment"""
        self.logger.info("🏢 Processing all leads for B2B website enrichment...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get leads with websites
            cursor = conn.execute("""
                SELECT * FROM leads 
                WHERE Website IS NOT NULL AND Website != ''
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            
            if not leads:
                self.logger.info("📋 No leads with websites found")
                return 0
            
            self.logger.info(f"🔧 Found {len(leads)} leads with websites to enrich")
            
            enriched_count = 0
            for lead in leads:
                try:
                    # Enrich with website data
                    enriched_lead = self.enrich_lead_with_website_data(lead)
                    
                    # Update for B2B outreach
                    b2b_lead = self.update_lead_for_b2b_outreach(enriched_lead)
                    
                    # Update database (use existing columns where possible)
                    conn.execute("""
                        UPDATE leads 
                        SET AI_Message = ?, 
                            Company_Description = ?,
                            Phone = ?,
                            Response_Status = 'enriched'
                        WHERE id = ?
                    """, (
                        b2b_lead.get('AI_Message', ''),
                        b2b_lead.get('Company_Description', ''),
                        b2b_lead.get('Business_Phone', ''),
                        lead['id']
                    ))
                    
                    enriched_count += 1
                    self.logger.info(f"✅ Enriched: {lead.get('Full_Name', 'Unknown')} - {lead.get('Company', 'Unknown')}")
                    
                    time.sleep(2)  # Rate limit
                    
                except Exception as lead_error:
                    self.logger.error(f"❌ Error enriching {lead.get('Full_Name', 'Unknown')}: {lead_error}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"🎉 B2B enrichment complete: {enriched_count}/{len(leads)} leads enriched")
            return enriched_count
            
        except Exception as e:
            self.logger.error(f"❌ Error processing leads: {e}")
            return 0

def main():
    enricher = B2BWebsiteEnricher()
    
    print("🏢 B2B WEBSITE ENRICHMENT STRATEGY")
    print("=" * 35)
    print("📋 Focus on websites for B2B lead enrichment")
    print("✅ Strategy:")
    print("   1. Use website as primary contact method")
    print("   2. Extract business emails (info@, contact@, sales@)")
    print("   3. Create B2B-focused outreach messages")
    print("   4. Target the business, not just individuals")
    print("")
    
    # Process all leads with websites
    enriched_count = enricher.process_all_website_leads()
    
    print(f"\n🎉 B2B ENRICHMENT COMPLETE!")
    print(f"   🔧 Enriched: {enriched_count} leads")
    print(f"   🏢 Strategy: Website-first B2B approach")
    print(f"   📧 Contact: Business emails + website forms")
    
    if enriched_count > 0:
        print(f"\n🚀 NEXT: Test the B2B enriched system")
        print(f"   python3 real_autonomous_organism.py --test")
        print(f"   Should now sync B2B-enriched leads")

if __name__ == "__main__":
    main()
