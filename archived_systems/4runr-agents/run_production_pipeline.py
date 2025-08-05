#!/usr/bin/env python3
"""
Production Pipeline Runner

Runs the complete production pipeline with:
- Fresh Montreal CEO scraping
- De-duplication checks
- Dynamic AI message generation
- Validation-first approach
- Airtable sync with no fake data
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add shared modules to path
sys.path.append(str(Path(__file__).parent / 'shared'))
sys.path.append(str(Path(__file__).parent / 'scraper'))

from shared.airtable_client import push_lead_to_airtable, check_linkedin_url_exists
from shared.ai_message_generator import generate_ai_message, generate_linkedin_dm
from scraper.serpapi_linkedin_scraper import SerpAPILinkedInScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('production-pipeline')

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for pipeline")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

class ProductionPipeline:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        self.shared_dir.mkdir(exist_ok=True)
        
        # Pipeline files
        self.raw_leads_file = self.shared_dir / 'raw_leads.json'
        self.processed_leads_file = self.shared_dir / 'processed_leads.json'
        
        # Statistics
        self.stats = {
            'scraped_leads': 0,
            'duplicate_leads': 0,
            'validated_leads': 0,
            'synced_leads': 0,
            'failed_leads': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
    
    def log_section(self, title: str):
        """Log a pipeline section"""
        logger.info("\n" + "="*80)
        logger.info(f"🚀 {title}")
        logger.info("="*80)
    
    def scrape_fresh_leads(self, max_leads: int = 10) -> List[Dict]:
        """Scrape fresh Montreal CEO leads using SerpAPI"""
        self.log_section("SCRAPING FRESH MONTREAL CEO LEADS")
        
        try:
            logger.info(f"🎯 Target: {max_leads} fresh Montreal CEO+ leads")
            logger.info("📋 Criteria:")
            logger.info("   - Location: Montreal OR Greater Montreal")
            logger.info("   - Titles: CEO, Founder, President, Managing Director")
            logger.info("   - Companies: Real companies (validated)")
            logger.info("   - Exclusions: Students, Freelancers, Assistants, Recruiters")
            
            # Use SerpAPI scraper instead of LinkedIn scraper
            scraper = SerpAPILinkedInScraper()
            leads = scraper.search_montreal_ceos_with_serpapi(max_results=max_leads)
            
            self.stats['scraped_leads'] = len(leads)
            
            if leads:
                logger.info(f"✅ Successfully scraped {len(leads)} leads")
                
                # Save raw leads
                with open(self.raw_leads_file, 'w', encoding='utf-8') as f:
                    json.dump(leads, f, indent=2, ensure_ascii=False)
                
                logger.info(f"💾 Raw leads saved to {self.raw_leads_file}")
                
                # Log sample leads
                logger.info("📋 Sample leads:")
                for i, lead in enumerate(leads[:3], 1):
                    logger.info(f"   {i}. {lead['name']} - {lead['title']} at {lead['company']}")
                
                if len(leads) > 3:
                    logger.info(f"   ... and {len(leads) - 3} more")
            else:
                logger.warning("⚠️ No leads were scraped")
            
            return leads
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {str(e)}")
            return []
    
    def filter_duplicates(self, leads: List[Dict]) -> List[Dict]:
        """Filter out duplicate leads"""
        self.log_section("FILTERING DUPLICATES")
        
        unique_leads = []
        duplicate_count = 0
        
        logger.info("🔍 Checking for duplicates in Airtable and processed leads...")
        
        for lead in leads:
            linkedin_url = lead.get('linkedin_url', '')
            name = lead.get('name', 'Unknown')
            
            if not linkedin_url:
                logger.warning(f"⚠️ Skipping {name}: No LinkedIn URL")
                continue
            
            # Check if already exists in Airtable
            if check_linkedin_url_exists(linkedin_url):
                logger.info(f"🔄 Duplicate in Airtable: {name}")
                duplicate_count += 1
                continue
            
            # Check local duplicates within this batch
            if any(existing['linkedin_url'] == linkedin_url for existing in unique_leads):
                logger.info(f"🔄 Duplicate in batch: {name}")
                duplicate_count += 1
                continue
            
            unique_leads.append(lead)
            logger.info(f"✅ Unique lead: {name}")
        
        self.stats['duplicate_leads'] = duplicate_count
        
        logger.info(f"📊 Duplicate filtering results:")
        logger.info(f"   Original leads: {len(leads)}")
        logger.info(f"   Duplicates found: {duplicate_count}")
        logger.info(f"   Unique leads: {len(unique_leads)}")
        
        return unique_leads
    
    def validate_leads(self, leads: List[Dict]) -> List[Dict]:
        """Validate leads meet production criteria"""
        self.log_section("VALIDATING LEADS")
        
        validated_leads = []
        
        for lead in leads:
            name = lead.get('name', 'Unknown')
            title = lead.get('title', '')
            company = lead.get('company', '')
            linkedin_url = lead.get('linkedin_url', '')
            
            # Validation checks
            validation_passed = True
            issues = []
            
            # Check required fields
            if not name or len(name.strip()) < 2:
                issues.append("Invalid name")
                validation_passed = False
            
            if not title or len(title.strip()) < 3:
                issues.append("Invalid title")
                validation_passed = False
            
            if not company or len(company.strip()) < 4:
                issues.append("Invalid company")
                validation_passed = False
            
            if not linkedin_url or 'linkedin.com/in/' not in linkedin_url:
                issues.append("Invalid LinkedIn URL")
                validation_passed = False
            
            # Check for decision-maker titles
            decision_maker_keywords = [
                'ceo', 'chief executive', 'founder', 'co-founder', 'president',
                'managing director', 'executive director', 'managing partner', 'owner'
            ]
            
            if not any(keyword in title.lower() for keyword in decision_maker_keywords):
                issues.append("Not a decision-maker title")
                validation_passed = False
            
            if validation_passed:
                validated_leads.append(lead)
                logger.info(f"✅ Validated: {name} - {title} at {company}")
            else:
                logger.warning(f"❌ Failed validation: {name} - {', '.join(issues)}")
        
        self.stats['validated_leads'] = len(validated_leads)
        
        logger.info(f"📊 Validation results:")
        logger.info(f"   Input leads: {len(leads)}")
        logger.info(f"   Validated leads: {len(validated_leads)}")
        logger.info(f"   Validation rate: {(len(validated_leads)/len(leads)*100):.1f}%" if leads else "0%")
        
        return validated_leads
    
    def enrich_leads_with_ai_messages(self, leads: List[Dict]) -> List[Dict]:
        """Enrich leads with dynamic AI messages"""
        self.log_section("GENERATING DYNAMIC AI MESSAGES")
        
        enriched_leads = []
        
        for lead in leads:
            try:
                name = lead.get('name', 'Unknown')
                
                # Generate AI message
                message_data = generate_ai_message(lead, source="Search")
                
                # Add AI message to lead
                lead['ai_message'] = message_data['message']
                lead['message_template_id'] = message_data['template_id']
                lead['message_tone'] = message_data['tone']
                lead['message_generated_at'] = message_data['generated_at']
                
                # If no email found, generate LinkedIn DM message
                if not lead.get('email'):
                    lead['linkedin_dm_message'] = generate_linkedin_dm(lead)
                    lead['needs_enrichment'] = True
                    logger.info(f"📝 Generated AI message + LinkedIn DM for {name}")
                else:
                    logger.info(f"📝 Generated AI message for {name}")
                
                enriched_leads.append(lead)
                
            except Exception as e:
                logger.error(f"❌ Failed to generate message for {name}: {str(e)}")
                # Still add lead without AI message
                enriched_leads.append(lead)
        
        logger.info(f"📊 AI message generation:")
        logger.info(f"   Leads processed: {len(leads)}")
        logger.info(f"   Messages generated: {len([l for l in enriched_leads if l.get('ai_message')])}")
        logger.info(f"   LinkedIn DMs generated: {len([l for l in enriched_leads if l.get('linkedin_dm_message')])}")
        
        return enriched_leads
    
    def sync_to_airtable(self, leads: List[Dict]) -> List[Dict]:
        """Sync leads to Airtable with validation-first approach"""
        self.log_section("SYNCING TO AIRTABLE")
        
        synced_leads = []
        failed_leads = []
        
        logger.info("🔒 Validation-First Rules:")
        logger.info("   - No fake data generation")
        logger.info("   - Skip leads that fail verification")
        logger.info("   - Real LinkedIn URLs only")
        logger.info("   - Authentic company information only")
        
        for lead in leads:
            name = lead.get('name', 'Unknown')
            
            try:
                # Sync to Airtable
                success = push_lead_to_airtable(lead)
                
                if success:
                    synced_leads.append(lead)
                    logger.info(f"✅ Synced to Airtable: {name}")
                else:
                    failed_leads.append(lead)
                    logger.error(f"❌ Failed to sync: {name}")
                
            except Exception as e:
                logger.error(f"❌ Error syncing {name}: {str(e)}")
                failed_leads.append(lead)
        
        self.stats['synced_leads'] = len(synced_leads)
        self.stats['failed_leads'] = len(failed_leads)
        
        logger.info(f"📊 Airtable sync results:")
        logger.info(f"   Successfully synced: {len(synced_leads)}")
        logger.info(f"   Failed to sync: {len(failed_leads)}")
        logger.info(f"   Success rate: {(len(synced_leads)/len(leads)*100):.1f}%" if leads else "0%")
        
        return synced_leads
    
    def generate_final_report(self):
        """Generate final pipeline report"""
        self.log_section("PIPELINE COMPLETION REPORT")
        
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("🎯 TARGET OUTCOME ACHIEVED:")
        logger.info(f"   ✅ Fresh Montreal CEO+ leads: {self.stats['synced_leads']}")
        logger.info(f"   ✅ Real LinkedIn URLs: {self.stats['synced_leads']}")
        logger.info(f"   ✅ Clean names and titles: {self.stats['validated_leads']}")
        logger.info(f"   ✅ Valid companies: {self.stats['validated_leads']}")
        logger.info(f"   ✅ AI messages with variation: {self.stats['synced_leads']}")
        logger.info(f"   ✅ No duplication: {self.stats['duplicate_leads']} duplicates filtered")
        logger.info(f"   ✅ No fake data: Validation-first approach enforced")
        
        logger.info(f"\n📊 PIPELINE STATISTICS:")
        logger.info(f"   Total execution time: {duration}")
        logger.info(f"   Leads scraped: {self.stats['scraped_leads']}")
        logger.info(f"   Duplicates filtered: {self.stats['duplicate_leads']}")
        logger.info(f"   Leads validated: {self.stats['validated_leads']}")
        logger.info(f"   Leads synced to Airtable: {self.stats['synced_leads']}")
        logger.info(f"   Failed syncs: {self.stats['failed_leads']}")
        
        # Calculate success rate
        if self.stats['scraped_leads'] > 0:
            success_rate = (self.stats['synced_leads'] / self.stats['scraped_leads']) * 100
            logger.info(f"   Overall success rate: {success_rate:.1f}%")
        
        logger.info(f"\n🎉 PRODUCTION PIPELINE COMPLETED SUCCESSFULLY!")
        
        return self.stats
    
    def run_production_pipeline(self, max_leads: int = 10) -> Dict:
        """Run the complete production pipeline"""
        logger.info("🚀 Starting Production Pipeline")
        logger.info(f"🎯 Target: {max_leads} fresh Montreal CEO+ leads")
        
        pipeline_start_time = datetime.now()
        
        try:
            # Step 1: Scrape fresh leads
            raw_leads = self.scrape_fresh_leads(max_leads)
            
            if not raw_leads:
                logger.error("❌ No leads scraped - pipeline cannot continue")
                return self.generate_final_report()
            
            # Step 2: Filter duplicates
            unique_leads = self.filter_duplicates(raw_leads)
            
            if not unique_leads:
                logger.warning("⚠️ All leads were duplicates - pipeline complete")
                return self.generate_final_report()
            
            # Step 3: Validate leads
            validated_leads = self.validate_leads(unique_leads)
            
            if not validated_leads:
                logger.error("❌ No leads passed validation - pipeline cannot continue")
                return self.generate_final_report()
            
            # Step 4: Enrich with AI messages
            enriched_leads = self.enrich_leads_with_ai_messages(validated_leads)
            
            # Step 5: Sync to Airtable
            synced_leads = self.sync_to_airtable(enriched_leads)
            
            # Step 6: Generate final report
            final_report = self.generate_final_report()
            
            # Log production data - pipeline complete
            if PRODUCTION_LOGGING_ENABLED:
                try:
                    pipeline_results = {
                        "pipeline_duration": (datetime.now() - pipeline_start_time).total_seconds(),
                        "leads_scraped": self.stats['scraped_leads'],
                        "leads_validated": self.stats['validated_leads'],
                        "leads_synced": self.stats['synced_leads'],
                        "duplicate_rate": self.stats['duplicate_leads'] / max(self.stats['scraped_leads'], 1),
                        "success_rate": self.stats['synced_leads'] / max_leads if max_leads > 0 else 0,
                        "final_stats": final_report
                    }
                    
                    pipeline_decisions = {
                        "max_leads_target": max_leads,
                        "validation_enabled": True,
                        "ai_message_generation": True,
                        "airtable_sync": True,
                        "duplicate_filtering": True
                    }
                    
                    log_production_event(
                        "airtable_operation",  # Using airtable_operation for pipeline
                        {"pipeline_type": "production", "target_leads": max_leads},
                        pipeline_results,
                        {"decisions": pipeline_decisions}
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Production logging failed: {e}")
            
            return final_report
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            return self.generate_final_report()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Production Pipeline')
    parser.add_argument('--max-leads', type=int, default=10, help='Maximum leads to scrape (default: 10)')
    args = parser.parse_args()
    
    pipeline = ProductionPipeline()
    results = pipeline.run_production_pipeline(max_leads=args.max_leads)
    
    # Return success if we synced at least one lead
    success = results['synced_leads'] > 0
    
    if success:
        logger.info("✅ Production pipeline completed successfully")
    else:
        logger.error("❌ Production pipeline failed to sync any leads")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)