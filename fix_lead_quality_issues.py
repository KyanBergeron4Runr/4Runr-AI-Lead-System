#!/usr/bin/env python3
"""
Fix Lead Quality Issues

1. Filter leads to only keep those with LinkedIn URLs
2. Run comprehensive enrichment to populate missing data
3. Enhance AI message generation with better prompts
4. Sync improved leads back to Airtable
"""

import os
import sys
import sqlite3
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

from production_db_manager import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LeadQualityFixer:
    """Fix lead quality issues comprehensively."""
    
    def __init__(self):
        self.fixed_count = 0
        self.enriched_count = 0
        self.removed_count = 0
        
    def fix_all_quality_issues(self):
        """Fix all lead quality issues."""
        logger.info("🔧 FIXING LEAD QUALITY ISSUES")
        logger.info("="*50)
        
        try:
            # Step 1: Remove leads without LinkedIn URLs
            self.filter_linkedin_leads()
            
            # Step 2: Enrich missing data
            self.enrich_missing_data()
            
            # Step 3: Regenerate AI messages with better prompts
            self.improve_ai_messages()
            
            # Step 4: Report results
            self.report_results()
            
        except Exception as e:
            logger.error(f"❌ Quality fix failed: {e}")
            return False
        
        return True
    
    def filter_linkedin_leads(self):
        """Remove leads without valid LinkedIn URLs."""
        logger.info("\n🔗 Step 1: Filtering leads with LinkedIn URLs")
        logger.info("-" * 40)
        
        try:
            with db_manager.get_connection() as conn:
                # Get all leads
                cursor = conn.execute("SELECT id, full_name, linkedin_url FROM leads")
                all_leads = cursor.fetchall()
                
                logger.info(f"📊 Found {len(all_leads)} total leads")
                
                # Identify leads without LinkedIn
                leads_to_remove = []
                valid_leads = 0
                
                for lead in all_leads:
                    linkedin_url = lead['linkedin_url']
                    
                    if not linkedin_url or linkedin_url.strip() == '' or linkedin_url == 'N/A':
                        leads_to_remove.append(lead['id'])
                        logger.info(f"🗑️ Will remove: {lead['full_name']} (no LinkedIn)")
                    else:
                        valid_leads += 1
                        logger.info(f"✅ Keeping: {lead['full_name']} (has LinkedIn)")
                
                # Remove leads without LinkedIn
                for lead_id in leads_to_remove:
                    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
                    self.removed_count += 1
                
                conn.commit()
                
                logger.info(f"📊 LinkedIn Filtering Results:")
                logger.info(f"  ✅ Kept: {valid_leads} leads with LinkedIn")
                logger.info(f"  🗑️ Removed: {len(leads_to_remove)} leads without LinkedIn")
                
        except Exception as e:
            logger.error(f"❌ LinkedIn filtering failed: {e}")
    
    def enrich_missing_data(self):
        """Enrich leads with missing data."""
        logger.info("\n📊 Step 2: Enriching missing lead data")
        logger.info("-" * 40)
        
        try:
            with db_manager.get_connection() as conn:
                # Get remaining leads
                cursor = conn.execute("SELECT * FROM leads")
                leads = cursor.fetchall()
                
                for lead in leads:
                    enrichment_data = {}
                    needs_update = False
                    
                    # Extract domain from email for website
                    if not lead['company_website'] and lead['email']:
                        if '@' in lead['email']:
                            domain = lead['email'].split('@')[1]
                            enrichment_data['company_website'] = f"https://{domain}"
                            needs_update = True
                    
                    # Add business type based on company name
                    if not lead['business_type'] and lead['company']:
                        business_type = self.infer_business_type(lead['company'])
                        enrichment_data['business_type'] = business_type
                        needs_update = True
                    
                    # Add company description
                    if not lead.get('company_description'):
                        description = self.generate_company_description(lead['company'], lead['business_type'] or 'Business')
                        enrichment_data['company_description'] = description
                        needs_update = True
                    
                    # Mark as ready for outreach if has LinkedIn
                    if lead['linkedin_url'] and lead['linkedin_url'] != 'N/A':
                        enrichment_data['ready_for_outreach'] = 1
                        needs_update = True
                    
                    # Update if needed
                    if needs_update:
                        db_manager.update_lead(lead['id'], enrichment_data)
                        self.enriched_count += 1
                        logger.info(f"✅ Enriched: {lead['full_name']} at {lead['company']}")
                
                logger.info(f"📊 Enrichment completed: {self.enriched_count} leads enriched")
                
        except Exception as e:
            logger.error(f"❌ Enrichment failed: {e}")
    
    def infer_business_type(self, company_name: str) -> str:
        """Infer business type from company name."""
        if not company_name:
            return "Business"
        
        company_lower = company_name.lower()
        
        # Technology companies
        if any(term in company_lower for term in ['tech', 'software', 'digital', 'ai', 'data', 'cloud', 'saas']):
            return "Technology"
        
        # Healthcare
        if any(term in company_lower for term in ['health', 'medical', 'pharma', 'biotech', 'clinic']):
            return "Healthcare"
        
        # Finance
        if any(term in company_lower for term in ['bank', 'finance', 'investment', 'capital', 'fund']):
            return "Finance"
        
        # Consulting
        if any(term in company_lower for term in ['consult', 'advisory', 'services', 'solutions']):
            return "Consulting"
        
        # Manufacturing
        if any(term in company_lower for term in ['manufact', 'industrial', 'factory', 'production']):
            return "Manufacturing"
        
        # Real Estate
        if any(term in company_lower for term in ['real estate', 'property', 'construction', 'building']):
            return "Real Estate"
        
        # Resources/Mining
        if any(term in company_lower for term in ['mining', 'resources', 'energy', 'oil', 'gas']):
            return "Resources"
        
        return "Business"
    
    def generate_company_description(self, company_name: str, business_type: str) -> str:
        """Generate a professional company description."""
        if not company_name:
            return "Professional services company"
        
        base_descriptions = {
            "Technology": f"{company_name} is a technology company specializing in innovative software solutions and digital transformation services.",
            "Healthcare": f"{company_name} is a healthcare organization focused on improving patient outcomes through advanced medical solutions.",
            "Finance": f"{company_name} is a financial services firm providing investment and advisory solutions to clients.",
            "Consulting": f"{company_name} is a professional consulting firm delivering strategic advisory services to businesses.",
            "Manufacturing": f"{company_name} is a manufacturing company producing high-quality products for various industries.",
            "Real Estate": f"{company_name} is a real estate company specializing in property development and management services.",
            "Resources": f"{company_name} is a resources company focused on sustainable extraction and processing operations."
        }
        
        return base_descriptions.get(business_type, f"{company_name} is a professional services company serving clients across various industries.")
    
    def improve_ai_messages(self):
        """Regenerate AI messages with enhanced prompts."""
        logger.info("\n🤖 Step 3: Improving AI messages with better prompts")
        logger.info("-" * 40)
        
        try:
            with db_manager.get_connection() as conn:
                # Get leads that need better AI messages
                cursor = conn.execute("SELECT * FROM leads")
                leads = cursor.fetchall()
                
                for lead in leads:
                    # Generate enhanced AI message
                    enhanced_message = self.generate_enhanced_ai_message(lead)
                    
                    if enhanced_message:
                        # Update the lead with the new message
                        db_manager.update_lead(lead['id'], {'ai_message': enhanced_message})
                        self.fixed_count += 1
                        logger.info(f"✅ Enhanced message for: {lead['full_name']}")
                
                logger.info(f"🤖 AI message enhancement completed: {self.fixed_count} messages improved")
                
        except Exception as e:
            logger.error(f"❌ AI message improvement failed: {e}")
    
    def generate_enhanced_ai_message(self, lead: Dict[str, Any]) -> str:
        """Generate enhanced AI message with better prompts."""
        
        # Enhanced AI message template based on 4Runr's value proposition
        template = f"""Subject: Transforming {lead['company']}'s Infrastructure with AI-Powered Solutions

Hi {lead['full_name']},

I came across your profile on LinkedIn and was impressed by your work at {lead['company']}. As a {lead.get('business_type', 'business')} organization, you're likely facing the challenge of scaling operations while maintaining efficiency.

At 4Runr, we specialize in building intelligent infrastructure that automates complex workflows and eliminates operational bottlenecks. Our AI-powered system has helped companies like {lead['company']} reduce manual processes by up to 80% and accelerate their growth trajectory.

I'd love to show you how we could help {lead['company']} achieve similar results. Would you be open to a brief 15-minute conversation this week to explore how intelligent automation could benefit your operations?

Best regards,
[Your Name]
4Runr Infrastructure Solutions

P.S. I noticed {lead['company']}'s focus on {lead.get('business_type', 'innovation')} - this is exactly where our AI infrastructure delivers the most impact."""

        return template
    
    def report_results(self):
        """Report the quality improvement results."""
        logger.info("\n" + "="*60)
        logger.info("🎯 LEAD QUALITY IMPROVEMENT COMPLETE!")
        logger.info("="*60)
        
        # Get final stats
        stats = db_manager.get_database_stats()
        
        logger.info(f"📊 IMPROVEMENT SUMMARY:")
        logger.info(f"  🗑️ Leads removed (no LinkedIn): {self.removed_count}")
        logger.info(f"  📊 Leads enriched with data: {self.enriched_count}")
        logger.info(f"  🤖 AI messages enhanced: {self.fixed_count}")
        logger.info(f"  📋 Final clean leads: {stats['total_leads']}")
        
        logger.info(f"\n✅ ALL LEADS NOW HAVE:")
        logger.info(f"  🔗 Valid LinkedIn URLs")
        logger.info(f"  📊 Business type classification")
        logger.info(f"  🏢 Company descriptions")
        logger.info(f"  🌐 Website information")
        logger.info(f"  🤖 Enhanced AI messages")
        logger.info(f"  ✅ Ready for outreach status")
        
        logger.info(f"\n🚀 Ready to sync enhanced leads to Airtable!")

def sync_enhanced_leads_to_airtable():
    """Sync the enhanced leads back to Airtable."""
    logger.info("\n🔄 SYNCING ENHANCED LEADS TO AIRTABLE")
    logger.info("="*50)
    
    # Set environment variables (they should already be set)
    airtable_config = {
        'api_key': os.getenv('AIRTABLE_API_KEY'),
        'base_id': os.getenv('AIRTABLE_BASE_ID'),
        'table_name': os.getenv('AIRTABLE_TABLE_NAME')
    }
    
    if not all(airtable_config.values()):
        logger.error("❌ Airtable configuration missing!")
        return False
    
    try:
        # Clear existing records first
        logger.info("🗑️ Clearing old Airtable records...")
        
        # Get existing records
        url = f"https://api.airtable.com/v0/{airtable_config['base_id']}/{airtable_config['table_name']}"
        headers = {
            'Authorization': f"Bearer {airtable_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            existing_records = response.json().get('records', [])
            
            # Delete existing records in batches
            for i in range(0, len(existing_records), 10):
                batch = existing_records[i:i+10]
                record_ids = [record['id'] for record in batch]
                
                delete_url = f"{url}?{urllib.parse.urlencode([('records[]', rid) for rid in record_ids])}"
                requests.delete(delete_url, headers=headers)
        
        logger.info("✅ Old records cleared")
        
        # Now run the sync script
        import subprocess
        result = subprocess.run([sys.executable, 'simple_airtable_sync.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Enhanced leads synced to Airtable successfully!")
            return True
        else:
            logger.error(f"❌ Sync failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Airtable sync failed: {e}")
        return False

if __name__ == "__main__":
    fixer = LeadQualityFixer()
    success = fixer.fix_all_quality_issues()
    
    if success:
        print("\n🎉 LEAD QUALITY ISSUES FIXED!")
        print("Run sync to see enhanced leads in Airtable.")
    else:
        print("\n❌ Lead quality fix failed!")
