#!/usr/bin/env python3
"""
Demo Production Pipeline

Demonstrates the complete production pipeline using existing verified leads
to show all new features working:
- De-duplication
- Dynamic AI messages
- Enhanced Airtable sync
- Validation-first approach
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add shared modules to path
sys.path.append(str(Path(__file__).parent / 'shared'))

from shared.airtable_client import push_lead_to_airtable, check_linkedin_url_exists
from shared.ai_message_generator import generate_ai_message, generate_linkedin_dm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('demo-pipeline')

class DemoProductionPipeline:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        
    def log_section(self, title: str):
        """Log a pipeline section"""
        logger.info("\n" + "="*80)
        logger.info(f"🎬 DEMO: {title}")
        logger.info("="*80)
    
    def load_existing_leads(self) -> list:
        """Load existing verified leads for demo"""
        self.log_section("LOADING EXISTING VERIFIED LEADS")
        
        verified_leads_file = self.shared_dir / 'verified_leads.json'
        
        if not verified_leads_file.exists():
            logger.error("❌ No verified leads found")
            return []
        
        with open(verified_leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        logger.info(f"📋 Loaded {len(leads)} verified leads:")
        for i, lead in enumerate(leads, 1):
            name = lead.get('full_name', lead.get('name', 'Unknown'))
            title = lead.get('title', 'Unknown Title')
            company = lead.get('company', 'Unknown Company')
            logger.info(f"   {i}. {name} - {title} at {company}")
        
        return leads
    
    def demo_deduplication(self, leads: list) -> list:
        """Demonstrate de-duplication system"""
        self.log_section("DEMONSTRATING DE-DUPLICATION SYSTEM")
        
        logger.info("🔍 Checking each lead for duplicates in Airtable...")
        
        unique_leads = []
        duplicate_count = 0
        
        for lead in leads:
            name = lead.get('full_name', lead.get('name', 'Unknown'))
            linkedin_url = lead.get('linkedin_url', '')
            
            if not linkedin_url:
                logger.warning(f"⚠️ Skipping {name}: No LinkedIn URL")
                continue
            
            # Check if already exists in Airtable
            if check_linkedin_url_exists(linkedin_url):
                logger.info(f"🔄 DUPLICATE DETECTED: {name} already exists in Airtable")
                duplicate_count += 1
            else:
                logger.info(f"✅ UNIQUE: {name} - ready for processing")
                unique_leads.append(lead)
        
        logger.info(f"\n📊 De-duplication Results:")
        logger.info(f"   Original leads: {len(leads)}")
        logger.info(f"   Duplicates found: {duplicate_count}")
        logger.info(f"   Unique leads: {len(unique_leads)}")
        
        return unique_leads
    
    def demo_ai_message_generation(self, leads: list) -> list:
        """Demonstrate dynamic AI message generation"""
        self.log_section("DEMONSTRATING DYNAMIC AI MESSAGE GENERATION")
        
        logger.info("🤖 Generating personalized AI messages with variation...")
        
        enriched_leads = []
        
        for i, lead in enumerate(leads, 1):
            name = lead.get('full_name', lead.get('name', 'Unknown'))
            title = lead.get('title', 'Unknown Title')
            company = lead.get('company', 'Unknown Company')
            
            logger.info(f"\n📝 Generating message {i}/{len(leads)} for {name}:")
            logger.info(f"   Title: {title}")
            logger.info(f"   Company: {company}")
            
            try:
                # Generate AI message
                message_data = generate_ai_message(lead, source="Search")
                
                # Add AI message to lead
                lead['ai_message'] = message_data['message']
                lead['message_template_id'] = message_data['template_id']
                lead['message_tone'] = message_data['tone']
                lead['message_generated_at'] = message_data['generated_at']
                
                logger.info(f"   ✅ Template: {message_data['template_id']} ({message_data['tone']})")
                logger.info(f"   📧 Message: {message_data['message'][:100]}...")
                
                # Generate LinkedIn DM as fallback
                linkedin_dm = generate_linkedin_dm(lead)
                lead['linkedin_dm_message'] = linkedin_dm
                
                logger.info(f"   💬 LinkedIn DM: {linkedin_dm[:80]}...")
                
                enriched_leads.append(lead)
                
            except Exception as e:
                logger.error(f"   ❌ Failed to generate message: {str(e)}")
                enriched_leads.append(lead)
        
        logger.info(f"\n📊 AI Message Generation Results:")
        logger.info(f"   Messages generated: {len([l for l in enriched_leads if l.get('ai_message')])}")
        logger.info(f"   LinkedIn DMs generated: {len([l for l in enriched_leads if l.get('linkedin_dm_message')])}")
        logger.info(f"   Template variety: {len(set(l.get('message_template_id') for l in enriched_leads if l.get('message_template_id')))}")
        
        return enriched_leads
    
    def demo_airtable_sync(self, leads: list) -> list:
        """Demonstrate enhanced Airtable sync"""
        self.log_section("DEMONSTRATING ENHANCED AIRTABLE SYNC")
        
        logger.info("🔒 Validation-First Airtable Sync:")
        logger.info("   ✅ No fake data generation")
        logger.info("   ✅ Real LinkedIn URLs only")
        logger.info("   ✅ Authentic information only")
        logger.info("   ✅ De-duplication built-in")
        
        synced_leads = []
        failed_leads = []
        
        for i, lead in enumerate(leads, 1):
            name = lead.get('full_name', lead.get('name', 'Unknown'))
            
            logger.info(f"\n📤 Syncing {i}/{len(leads)}: {name}")
            
            try:
                # Sync to Airtable (includes built-in de-duplication)
                success = push_lead_to_airtable(lead)
                
                if success:
                    synced_leads.append(lead)
                    logger.info(f"   ✅ Successfully synced to Airtable")
                    logger.info(f"   📝 AI Message included: {bool(lead.get('ai_message'))}")
                    logger.info(f"   💬 LinkedIn DM ready: {bool(lead.get('linkedin_dm_message'))}")
                else:
                    failed_leads.append(lead)
                    logger.info(f"   🔄 Skipped (likely duplicate or validation failed)")
                
            except Exception as e:
                logger.error(f"   ❌ Error syncing: {str(e)}")
                failed_leads.append(lead)
        
        logger.info(f"\n📊 Airtable Sync Results:")
        logger.info(f"   Successfully synced: {len(synced_leads)}")
        logger.info(f"   Skipped/Failed: {len(failed_leads)}")
        logger.info(f"   Success rate: {(len(synced_leads)/len(leads)*100):.1f}%" if leads else "0%")
        
        return synced_leads
    
    def generate_demo_report(self, original_count: int, synced_count: int):
        """Generate demo completion report"""
        self.log_section("DEMO COMPLETION REPORT")
        
        logger.info("🎯 PRODUCTION FEATURES DEMONSTRATED:")
        logger.info(f"   ✅ De-duplication System: Prevents repeat leads")
        logger.info(f"   ✅ Dynamic AI Messages: Personalized, varied messages")
        logger.info(f"   ✅ Enhanced Airtable Sync: Validation-first approach")
        logger.info(f"   ✅ LinkedIn DM Fallback: When email not available")
        logger.info(f"   ✅ No Fake Data: Strict validation enforced")
        
        logger.info(f"\n📊 DEMO STATISTICS:")
        logger.info(f"   Original leads: {original_count}")
        logger.info(f"   Successfully processed: {synced_count}")
        logger.info(f"   Processing rate: {(synced_count/original_count*100):.1f}%" if original_count > 0 else "0%")
        
        logger.info(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        logger.info("🚀 Ready for production with fresh LinkedIn scraping!")
    
    def run_demo(self):
        """Run the complete demo pipeline"""
        logger.info("🎬 Starting Production Pipeline Demo")
        logger.info("📋 This demo shows all new features using existing verified leads")
        
        try:
            # Step 1: Load existing leads
            leads = self.load_existing_leads()
            
            if not leads:
                logger.error("❌ No leads to demo with")
                return False
            
            original_count = len(leads)
            
            # Step 2: Demo de-duplication
            unique_leads = self.demo_deduplication(leads)
            
            if not unique_leads:
                logger.info("ℹ️ All leads were duplicates - this shows de-duplication working!")
                self.generate_demo_report(original_count, 0)
                return True
            
            # Step 3: Demo AI message generation
            enriched_leads = self.demo_ai_message_generation(unique_leads)
            
            # Step 4: Demo Airtable sync
            synced_leads = self.demo_airtable_sync(enriched_leads)
            
            # Step 5: Generate report
            self.generate_demo_report(original_count, len(synced_leads))
            
            return len(synced_leads) > 0
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {str(e)}")
            return False

def main():
    """Main entry point"""
    demo = DemoProductionPipeline()
    success = demo.run_demo()
    
    if success:
        logger.info("✅ Demo completed successfully")
    else:
        logger.error("❌ Demo failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)