#!/usr/bin/env python3
"""
Enhanced Lead Quality Filter
===========================
Only keep leads with email OR website. Remove worthless leads.
Enricher finds the rest of the missing data.
"""

import sqlite3
import json
import logging
import re
from datetime import datetime

class LeadQualityFilter:
    def __init__(self):
        self.setup_logging()
        self.db_path = 'data/unified_leads.db'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def is_valid_email(self, email):
        """Check if email is valid and not generic"""
        if not email or email.strip() == '':
            return False
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # Reject generic/fake emails
        generic_emails = [
            'info@', 'contact@', 'admin@', 'support@', 'sales@',
            'hello@', 'general@', 'office@', 'inquiries@'
        ]
        
        email_lower = email.lower()
        for generic in generic_emails:
            if email_lower.startswith(generic):
                return False
        
        return True

    def is_valid_website(self, website):
        """Check if website is valid"""
        if not website or website.strip() == '':
            return False
        
        website = website.strip().lower()
        
        # Must have domain extension
        if '.' not in website:
            return False
        
        # Reject social media as primary website
        social_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 
            'linkedin.com', 'youtube.com', 'tiktok.com'
        ]
        
        for social in social_domains:
            if social in website:
                return False
        
        return True

    def evaluate_lead_quality(self, lead):
        """
        Determine if lead is worth keeping based on:
        MUST HAVE: Email OR Website (at least one)
        NICE TO HAVE: Full name, LinkedIn, title, company
        """
        
        email = lead.get('Email', '').strip()
        website = lead.get('Website', '').strip()
        full_name = lead.get('Full_Name', '').strip()
        linkedin = lead.get('LinkedIn_URL', '').strip()
        
        # Check required data
        has_valid_email = self.is_valid_email(email)
        has_valid_website = self.is_valid_website(website)
        
        # CORE REQUIREMENT: Must have email OR website
        if not has_valid_email and not has_valid_website:
            return {
                'keep': False,
                'reason': 'No valid email or website - not worth pursuing',
                'quality_score': 0
            }
        
        # Calculate quality score
        quality_score = 0
        quality_details = []
        
        # Email gets high score (direct contact)
        if has_valid_email:
            quality_score += 40
            quality_details.append(f"✅ Valid email: {email}")
        
        # Website gets medium score (can find contact info)
        if has_valid_website:
            quality_score += 30
            quality_details.append(f"✅ Valid website: {website}")
        
        # Full name adds value
        if full_name and len(full_name.split()) >= 2:
            quality_score += 15
            quality_details.append(f"✅ Full name: {full_name}")
        else:
            quality_details.append(f"⚠️ Missing/incomplete name: {full_name}")
        
        # LinkedIn adds value
        if linkedin and 'linkedin.com' in linkedin:
            quality_score += 10
            quality_details.append(f"✅ LinkedIn: {linkedin}")
        else:
            quality_details.append("⚠️ No LinkedIn URL")
        
        # Company adds value
        company = lead.get('Company', '').strip()
        if company:
            quality_score += 5
            quality_details.append(f"✅ Company: {company}")
        else:
            quality_details.append("⚠️ No company")
        
        return {
            'keep': True,
            'reason': 'Has email or website - worth enriching',
            'quality_score': quality_score,
            'quality_details': quality_details,
            'has_email': has_valid_email,
            'has_website': has_valid_website
        }

    def filter_leads(self, dry_run=False):
        """Filter leads and remove low-quality ones"""
        self.logger.info("🔍 Analyzing lead quality...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all leads
            cursor = conn.execute("SELECT * FROM leads")
            all_leads = [dict(row) for row in cursor.fetchall()]
            
            if not all_leads:
                self.logger.info("📋 No leads found in database")
                return
            
            self.logger.info(f"📋 Analyzing {len(all_leads)} leads...")
            
            # Analyze each lead
            keep_leads = []
            remove_leads = []
            
            for lead in all_leads:
                evaluation = self.evaluate_lead_quality(lead)
                
                if evaluation['keep']:
                    keep_leads.append({
                        'lead': lead,
                        'evaluation': evaluation
                    })
                else:
                    remove_leads.append({
                        'lead': lead,
                        'evaluation': evaluation
                    })
            
            # Report results
            self.logger.info(f"\n📊 QUALITY ANALYSIS RESULTS:")
            self.logger.info(f"   ✅ Keep: {len(keep_leads)} leads")
            self.logger.info(f"   ❌ Remove: {len(remove_leads)} leads")
            
            # Show leads to keep
            if keep_leads:
                self.logger.info(f"\n✅ LEADS TO KEEP ({len(keep_leads)}):")
                for i, item in enumerate(keep_leads, 1):
                    lead = item['lead']
                    eval_data = item['evaluation']
                    
                    self.logger.info(f"   {i}. {lead.get('Full_Name', 'Unknown')} - {lead.get('Company', 'Unknown')}")
                    self.logger.info(f"      Quality Score: {eval_data['quality_score']}/100")
                    self.logger.info(f"      Email: {lead.get('Email', 'None')}")
                    self.logger.info(f"      Website: {lead.get('Website', 'None')}")
                    for detail in eval_data['quality_details'][:3]:  # Show top 3 details
                        self.logger.info(f"      {detail}")
                    self.logger.info("")
            
            # Show leads to remove
            if remove_leads:
                self.logger.info(f"\n❌ LEADS TO REMOVE ({len(remove_leads)}):")
                for i, item in enumerate(remove_leads, 1):
                    lead = item['lead']
                    eval_data = item['evaluation']
                    
                    self.logger.info(f"   {i}. {lead.get('Full_Name', 'Unknown')} - {lead.get('Company', 'Unknown')}")
                    self.logger.info(f"      Reason: {eval_data['reason']}")
                    self.logger.info(f"      Email: {lead.get('Email', 'None')}")
                    self.logger.info(f"      Website: {lead.get('Website', 'None')}")
                    self.logger.info("")
            
            # Actually remove low-quality leads (if not dry run)
            if not dry_run and remove_leads:
                self.logger.info(f"🗑️ Removing {len(remove_leads)} low-quality leads...")
                
                for item in remove_leads:
                    lead = item['lead']
                    conn.execute("DELETE FROM leads WHERE id = ?", (lead['id'],))
                
                conn.commit()
                self.logger.info(f"✅ Removed {len(remove_leads)} low-quality leads")
            elif dry_run:
                self.logger.info(f"🔍 DRY RUN: Would remove {len(remove_leads)} leads")
            
            conn.close()
            
            return {
                'total_analyzed': len(all_leads),
                'keep_count': len(keep_leads),
                'remove_count': len(remove_leads),
                'keep_leads': keep_leads,
                'remove_leads': remove_leads
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error filtering leads: {e}")
            return None

    def update_enhanced_scraper_filter(self):
        """Update the scraper to apply this filter during scraping"""
        
        filter_code = '''
    def apply_quality_filter(self, leads):
        """Apply quality filter during scraping - only keep leads with email OR website"""
        filtered_leads = []
        
        for lead in leads:
            # Must have email OR website
            email = lead.get('email', '').strip()
            website = lead.get('website', '').strip()
            
            has_email = email and '@' in email and '.' in email
            has_website = website and '.' in website and not any(social in website.lower() 
                for social in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com'])
            
            if has_email or has_website:
                lead['quality_filtered'] = True
                lead['filter_reason'] = 'Has email or website'
                filtered_leads.append(lead)
            else:
                print(f"❌ Filtered out: {lead.get('name', 'Unknown')} - No email or website")
        
        return filtered_leads
        '''
        
        self.logger.info("💡 ENHANCED SCRAPER FILTER CODE:")
        self.logger.info("Add this method to your SerpAPILeadScraper class:")
        self.logger.info(filter_code)

def main():
    filter_manager = LeadQualityFilter()
    
    print("🔍 LEAD QUALITY FILTER")
    print("=" * 30)
    print("📋 Requirements:")
    print("   ✅ MUST HAVE: Email OR Website (at least one)")
    print("   ❌ REMOVE: Leads with neither email nor website")
    print("   🔧 ENRICHER: Will find missing data for kept leads")
    print("")
    
    # First run as dry run
    print("🔍 DRY RUN - Analyzing current leads...")
    results = filter_manager.filter_leads(dry_run=True)
    
    if results:
        print(f"\n📊 ANALYSIS COMPLETE:")
        print(f"   📋 Total leads: {results['total_analyzed']}")
        print(f"   ✅ Keep: {results['keep_count']} ({results['keep_count']/results['total_analyzed']*100:.1f}%)")
        print(f"   ❌ Remove: {results['remove_count']} ({results['remove_count']/results['total_analyzed']*100:.1f}%)")
        
        if results['remove_count'] > 0:
            response = input(f"\n❓ Remove {results['remove_count']} low-quality leads? (y/n): ")
            if response.lower() == 'y':
                print("\n🗑️ Removing low-quality leads...")
                filter_manager.filter_leads(dry_run=False)
                print("✅ Quality filtering complete!")
        else:
            print("\n🎉 All leads meet quality requirements!")
    
    # Show enhanced scraper filter
    print("\n💡 For future scraping:")
    filter_manager.update_enhanced_scraper_filter()

if __name__ == "__main__":
    main()
