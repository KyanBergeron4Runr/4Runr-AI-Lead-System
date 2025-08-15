#!/usr/bin/env python3
"""
Daily Lead Generation Automation

Main script that runs daily to:
1. Scrape new leads
2. Enrich with emails and business data
3. Generate AI messages
4. Sync to Airtable
5. Monitor system health
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.append('4runr-outreach-system')
sys.path.append('4runr-lead-scraper')

# Import production components
from production_db_manager import db_manager
from improved_email_finder import email_finder
from company_size_validator import company_validator

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"daily_automation_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyAutomation:
    """Daily lead generation automation."""
    
    def __init__(self):
        self.stats = {
            'leads_scraped': 0,
            'leads_enriched': 0,
            'emails_found': 0,
            'ai_messages_generated': 0,
            'leads_synced': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
    def run_daily_pipeline(self):
        """Run the complete daily lead generation pipeline."""
        logger.info("🎯 STARTING DAILY LEAD GENERATION")
        logger.info("="*50)
        
        try:
            # Step 1: Scrape new leads
            self.scrape_new_leads()
            
            # Step 2: Enrich leads with emails and business data
            self.enrich_leads()
            
            # Step 3: Generate AI messages
            self.generate_ai_messages()
            
            # Step 4: Sync to Airtable
            self.sync_to_airtable()
            
            # Step 5: System health check
            self.system_health_check()
            
            self.stats['end_time'] = datetime.now()
            self.report_results()
            
        except Exception as e:
            logger.error(f"❌ Daily automation failed: {e}")
            logger.error(traceback.format_exc())
            self.stats['errors'] += 1
            return False
        
        return True
    
    def scrape_new_leads(self):
        """Scrape new leads using SerpAPI."""
        logger.info("🔍 Step 1: Scraping new leads...")
        
        try:
            # Import lead scraper
            from 4runr_lead_scraper.scraper.lead_finder import LeadFinder
            
            lead_finder = LeadFinder()
            new_leads = lead_finder.find_montreal_executives(max_leads=5)
            
            if not new_leads:
                logger.info("📭 No new leads found today")
                return
            
            logger.info(f"📋 Found {len(new_leads)} potential leads")
            
            # Add leads to database
            added_count = 0
            for lead_data in new_leads:
                # Validate company size before adding
                if lead_data.get('company'):
                    target_info = company_validator.is_good_outreach_target(
                        lead_data['company'], ""
                    )
                    
                    if not target_info['is_good_target']:
                        logger.info(f"⏭️ Skipping {lead_data['company']}: {target_info['reason']}")
                        continue
                
                # Add to database
                if db_manager.add_lead(lead_data):
                    added_count += 1
                    logger.info(f"✅ Added lead: {lead_data.get('full_name', 'Unknown')} at {lead_data.get('company', 'Unknown')}")
                else:
                    logger.warning(f"⚠️ Failed to add lead: {lead_data.get('full_name', 'Unknown')}")
            
            self.stats['leads_scraped'] = added_count
            logger.info(f"✅ Successfully added {added_count} new leads")
            
        except Exception as e:
            logger.error(f"❌ Lead scraping failed: {e}")
            self.stats['errors'] += 1
    
    def enrich_leads(self):
        """Enrich leads with emails and business data."""
        logger.info("🔧 Step 2: Enriching leads...")
        
        try:
            # Get leads that need enrichment
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, full_name, company, website, email 
                    FROM leads 
                    WHERE (email IS NULL OR email = '') 
                    AND website IS NOT NULL 
                    AND website != ''
                    LIMIT 10
                """)
                leads_to_enrich = cursor.fetchall()
            
            if not leads_to_enrich:
                logger.info("📭 No leads need enrichment")
                return
            
            logger.info(f"🔧 Enriching {len(leads_to_enrich)} leads...")
            
            enriched_count = 0
            emails_found = 0
            
            for lead in leads_to_enrich:
                lead_id = lead['id']
                website = lead['website']
                company = lead['company']
                
                try:
                    # Find emails
                    if website and not lead['email']:
                        emails = email_finder.find_business_emails(website, company)
                        
                        if emails:
                            # Update lead with first email found
                            update_data = {'email': emails[0]}
                            if db_manager.update_lead(lead_id, update_data):
                                emails_found += 1
                                logger.info(f"📧 Found email for {lead['full_name']}: {emails[0]}")
                    
                    # Mark as enriched
                    db_manager.update_lead(lead_id, {'enriched': 1})
                    enriched_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to enrich lead {lead_id}: {e}")
            
            self.stats['leads_enriched'] = enriched_count
            self.stats['emails_found'] = emails_found
            logger.info(f"✅ Enriched {enriched_count} leads, found {emails_found} emails")
            
        except Exception as e:
            logger.error(f"❌ Lead enrichment failed: {e}")
            self.stats['errors'] += 1
    
    def generate_ai_messages(self):
        """Generate AI messages for leads."""
        logger.info("🤖 Step 3: Generating AI messages...")
        
        try:
            # Get leads that need AI messages
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, full_name, company, business_type, email 
                    FROM leads 
                    WHERE (ai_message IS NULL OR ai_message = '') 
                    AND email IS NOT NULL 
                    AND email != ''
                    LIMIT 10
                """)
                leads_for_ai = cursor.fetchall()
            
            if not leads_for_ai:
                logger.info("📭 No leads need AI messages")
                return
            
            logger.info(f"🤖 Generating AI messages for {len(leads_for_ai)} leads...")
            
            messages_generated = 0
            
            for lead in leads_for_ai:
                lead_id = lead['id']
                
                try:
                    # Generate AI message (simplified for now)
                    ai_message = self._generate_simple_ai_message(lead)
                    
                    if ai_message:
                        update_data = {
                            'ai_message': ai_message,
                            'message_generated_at': datetime.now().isoformat()
                        }
                        
                        if db_manager.update_lead(lead_id, update_data):
                            messages_generated += 1
                            logger.info(f"🤖 Generated AI message for {lead['full_name']}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate AI message for {lead_id}: {e}")
            
            self.stats['ai_messages_generated'] = messages_generated
            logger.info(f"✅ Generated {messages_generated} AI messages")
            
        except Exception as e:
            logger.error(f"❌ AI message generation failed: {e}")
            self.stats['errors'] += 1
    
    def _generate_simple_ai_message(self, lead):
        """Generate a simple AI message for a lead."""
        name = lead['full_name'] or 'there'
        company = lead['company'] or 'your company'
        business_type = lead['business_type'] or 'business'
        
        message = f"""Subject: Helping {company} Optimize Operations

Hi {name},

I noticed {company} and thought you might be interested in how we're helping {business_type} companies like yours optimize their operations and scale more efficiently.

Would you be open to a quick 15-minute call to discuss how we could potentially help {company}?

Best regards,
The 4Runr Team"""
        
        return message
    
    def sync_to_airtable(self):
        """Sync leads to Airtable."""
        logger.info("🔄 Step 4: Syncing to Airtable...")
        
        try:
            # Get leads ready for sync
            leads_for_sync = db_manager.get_leads_for_sync(limit=20)
            
            if not leads_for_sync:
                logger.info("📭 No leads to sync to Airtable")
                return
            
            logger.info(f"🔄 Syncing {len(leads_for_sync)} leads to Airtable...")
            
            # Import and use simple Airtable sync
            from simple_airtable_sync import sync_leads_to_airtable
            
            sync_result = sync_leads_to_airtable(leads_for_sync)
            
            if sync_result.get('success'):
                synced_count = sync_result.get('synced_count', 0)
                self.stats['leads_synced'] = synced_count
                logger.info(f"✅ Successfully synced {synced_count} leads to Airtable")
            else:
                logger.error(f"❌ Airtable sync failed: {sync_result.get('error')}")
                self.stats['errors'] += 1
            
        except Exception as e:
            logger.error(f"❌ Airtable sync failed: {e}")
            self.stats['errors'] += 1
    
    def system_health_check(self):
        """Perform system health check."""
        logger.info("🏥 Step 5: System health check...")
        
        try:
            # Get database stats
            stats = db_manager.get_database_stats()
            
            # Check for issues
            issues = []
            
            if stats['total_leads'] == 0:
                issues.append("No leads in database")
            
            if stats['email_percentage'] < 50:
                issues.append(f"Low email percentage: {stats['email_percentage']}%")
            
            if self.stats['errors'] > 0:
                issues.append(f"{self.stats['errors']} errors occurred")
            
            if issues:
                logger.warning(f"⚠️ Health check issues: {', '.join(issues)}")
            else:
                logger.info("✅ System health check passed")
            
            # Save health report
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'database_stats': stats,
                'automation_stats': self.stats,
                'issues': issues
            }
            
            health_file = Path("logs") / f"health_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(health_file, 'w') as f:
                json.dump(health_report, f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def report_results(self):
        """Report daily automation results."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("="*50)
        logger.info("📊 DAILY AUTOMATION RESULTS")
        logger.info("="*50)
        logger.info(f"⏱️ Duration: {duration}")
        logger.info(f"📋 Leads scraped: {self.stats['leads_scraped']}")
        logger.info(f"🔧 Leads enriched: {self.stats['leads_enriched']}")
        logger.info(f"📧 Emails found: {self.stats['emails_found']}")
        logger.info(f"🤖 AI messages generated: {self.stats['ai_messages_generated']}")
        logger.info(f"🔄 Leads synced to Airtable: {self.stats['leads_synced']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        
        # Save results
        results_file = Path("logs") / f"daily_results_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        if self.stats['errors'] == 0:
            logger.info("🎉 Daily automation completed successfully!")
        else:
            logger.warning("⚠️ Daily automation completed with errors")

if __name__ == "__main__":
    automation = DailyAutomation()
    success = automation.run_daily_pipeline()
    
    if success:
        print("✅ Daily automation completed successfully")
        sys.exit(0)
    else:
        print("❌ Daily automation failed")
        sys.exit(1)
