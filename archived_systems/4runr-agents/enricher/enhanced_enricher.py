#!/usr/bin/env python3
"""
Enhanced Enricher Agent for 4Runr Lead System

This agent combines website scraping, email enrichment, and comprehensive data analysis
with detailed logging and decision explanations.
"""

import os
import json
import time
import logging
import asyncio
import pathlib
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Find and load environment variables from .env file
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced-enricher')

# Import our enhanced modules
import sys
sys.path.append(str(root_dir / 'shared'))

try:
    from website_scraper import scrape_lead_website
    from enhanced_airtable_client import EnhancedAirtableClient
    WEBSITE_SCRAPER_AVAILABLE = True
    logger.info("✅ Enhanced website scraper loaded")
except ImportError as e:
    logger.warning(f"Enhanced website scraper not available: {e}")
    WEBSITE_SCRAPER_AVAILABLE = False

# Production enricher removed - functionality integrated into enhanced enricher
PRODUCTION_ENRICHER_AVAILABLE = False

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for enricher")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

# Constants
SHARED_DIR = os.path.join(root_dir, "shared")
ENRICHMENT_LOG_FILE = os.path.join(SHARED_DIR, "enrichment_decisions.json")

class EnhancedEnricher:
    """Enhanced enricher with website scraping and comprehensive logging"""
    
    def __init__(self):
        self.enrichment_log = []
        self.airtable_client = EnhancedAirtableClient()
        self.email_enricher = None  # Production enricher removed
    
    def log_enrichment_decision(self, decision_type: str, details: str, lead_name: str = "Unknown", data: Dict = None):
        """Log enrichment decisions for transparency"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "lead_name": lead_name,
            "decision_type": decision_type,
            "details": details,
            "data": data or {}
        }
        self.enrichment_log.append(log_entry)
        logger.info(f"[ENRICHMENT] {lead_name}: {decision_type} - {details}")
        
        # Also log to production logger for training
        if decision_type == "enrichment_complete":
            try:
                from shared.production_logger import log_production_event
                log_production_event("enrichment", data.get("lead_data", {}), 
                                   data.get("enrichment_results", {}),
                                   {"reasoning": self.enrichment_log})
            except Exception as e:
                logger.warning(f"Failed to log to production logger: {e}")
    
    async def enrich_lead_comprehensive(self, lead: Dict) -> Dict:
        """Perform comprehensive lead enrichment with website scraping and email validation"""
        lead_name = lead.get('full_name') or lead.get('name', 'Unknown')
        company_name = lead.get('company', 'Unknown Company')
        
        logger.info(f"🔍 Starting comprehensive enrichment for {lead_name} at {company_name}")
        self.log_enrichment_decision("enrichment_start", f"Beginning comprehensive enrichment", lead_name)
        
        # Start with a copy of the original lead
        enriched_lead = lead.copy()
        enrichment_results = {
            "website_scraping": {"success": False, "data_quality": 0},
            "email_enrichment": {"success": False, "method": "none"},
            "airtable_sync": {"success": False},
            "overall_success": False
        }
        
        # Step 1: Website Scraping
        if WEBSITE_SCRAPER_AVAILABLE:
            self.log_enrichment_decision("website_scraping_start", "Starting website analysis", lead_name)
            
            try:
                # Scrape the company website
                website_enhanced_lead = await scrape_lead_website(enriched_lead)
                
                # Merge website data
                enriched_lead.update(website_enhanced_lead)
                
                data_quality = enriched_lead.get('data_quality_score', 0)
                enrichment_results["website_scraping"] = {
                    "success": True,
                    "data_quality": data_quality
                }
                
                self.log_enrichment_decision("website_scraping_success", 
                                           f"Website analysis completed - Quality: {data_quality}/100", 
                                           lead_name, {
                                               "data_quality_score": data_quality,
                                               "company_description_length": len(enriched_lead.get('company_description', '')),
                                               "services_found": len(enriched_lead.get('top_services', [])),
                                               "tone_detected": enriched_lead.get('tone', 'unknown')
                                           })
                
                # Log what we found on the website
                if enriched_lead.get('website_data', {}).get('decision_log'):
                    website_decisions = enriched_lead['website_data']['decision_log']
                    key_findings = []
                    
                    for decision in website_decisions[-5:]:  # Last 5 decisions
                        if decision['decision_type'] in ['content_extraction', 'data_consolidation']:
                            key_findings.append(decision['details'])
                    
                    if key_findings:
                        self.log_enrichment_decision("website_findings", 
                                                   f"Key website findings: {' | '.join(key_findings)}", 
                                                   lead_name)
                
            except Exception as e:
                self.log_enrichment_decision("website_scraping_error", f"Website scraping failed: {str(e)}", lead_name)
                logger.error(f"❌ Website scraping failed for {lead_name}: {str(e)}")
        else:
            self.log_enrichment_decision("website_scraping_unavailable", "Website scraper not available", lead_name)
        
        # Step 2: Email Enrichment
        if self.email_enricher:
            self.log_enrichment_decision("email_enrichment_start", "Starting email validation and enrichment", lead_name)
            
            try:
                # Use production email enricher
                email_enriched_lead = self.email_enricher.enrich_lead_with_real_data(enriched_lead.copy())
                
                # Merge email enrichment results
                enriched_lead.update(email_enriched_lead)
                
                email_status = enriched_lead.get('email_status', 'unknown')
                email_confidence = enriched_lead.get('email_confidence', 0)
                
                enrichment_results["email_enrichment"] = {
                    "success": bool(enriched_lead.get('email')),
                    "method": email_status,
                    "confidence": email_confidence
                }
                
                self.log_enrichment_decision("email_enrichment_success", 
                                           f"Email enrichment completed - Status: {email_status}, Confidence: {email_confidence}%", 
                                           lead_name, {
                                               "email_found": bool(enriched_lead.get('email')),
                                               "email_status": email_status,
                                               "confidence": email_confidence
                                           })
                
            except Exception as e:
                self.log_enrichment_decision("email_enrichment_error", f"Email enrichment failed: {str(e)}", lead_name)
                logger.error(f"❌ Email enrichment failed for {lead_name}: {str(e)}")
        else:
            self.log_enrichment_decision("email_enrichment_unavailable", "Production email enricher not available", lead_name)
        
        # Step 3: Determine Email Confidence Level for Airtable
        email_confidence_level = self.determine_email_confidence_level(enriched_lead)
        enriched_lead['email_confidence_level'] = email_confidence_level
        
        self.log_enrichment_decision("email_confidence_determined", 
                                   f"Email confidence level set to: {email_confidence_level}", 
                                   lead_name, {
                                       "confidence_level": email_confidence_level,
                                       "has_email": bool(enriched_lead.get('email')),
                                       "reasoning": self.get_confidence_reasoning(enriched_lead)
                                   })
        
        # Step 4: Set Engagement Status
        engagement_status = self.determine_engagement_status(enriched_lead)
        enriched_lead['engagement_status'] = engagement_status
        
        self.log_enrichment_decision("engagement_status_determined", 
                                   f"Engagement status set to: {engagement_status}", 
                                   lead_name, {
                                       "engagement_status": engagement_status,
                                       "reasoning": self.get_engagement_reasoning(enriched_lead)
                                   })
        
        # Step 5: Mark as enriched and add metadata
        enriched_lead.update({
            "enriched": True,
            "enriched_at": datetime.now().isoformat(),
            "enrichment_method": "enhanced_comprehensive",
            "ready_for_engagement": engagement_status in ["auto_send", "ready"],
            "enrichment_results": enrichment_results
        })
        
        # Step 6: Sync to Airtable
        try:
            airtable_success = self.airtable_client.sync_lead(enriched_lead)
            enrichment_results["airtable_sync"]["success"] = airtable_success
            
            if airtable_success:
                self.log_enrichment_decision("airtable_sync_success", "Successfully synced to Airtable", lead_name)
            else:
                self.log_enrichment_decision("airtable_sync_failed", "Failed to sync to Airtable", lead_name)
                
        except Exception as e:
            self.log_enrichment_decision("airtable_sync_error", f"Airtable sync error: {str(e)}", lead_name)
            logger.error(f"❌ Airtable sync failed for {lead_name}: {str(e)}")
        
        # Determine overall success
        enrichment_results["overall_success"] = (
            enrichment_results["website_scraping"]["success"] or 
            enrichment_results["email_enrichment"]["success"]
        )
        
        # Final logging
        success_indicator = "✅" if enrichment_results["overall_success"] else "⚠️"
        self.log_enrichment_decision("enrichment_complete", 
                                   f"Comprehensive enrichment completed - Success: {enrichment_results['overall_success']}", 
                                   lead_name, enrichment_results)
        
        logger.info(f"{success_indicator} Comprehensive enrichment completed for {lead_name}")
        logger.info(f"   🌐 Website Quality: {enrichment_results['website_scraping']['data_quality']}/100")
        logger.info(f"   📧 Email Status: {enrichment_results['email_enrichment']['method']}")
        logger.info(f"   📤 Airtable Sync: {'✅' if enrichment_results['airtable_sync']['success'] else '❌'}")
        
        return enriched_lead
    
    def determine_email_confidence_level(self, lead: Dict) -> str:
        """Determine email confidence level based on enrichment results"""
        email = lead.get('email')
        email_status = lead.get('email_status', '').lower()
        
        if not email:
            return "guess"  # No email found
        
        # Check if email was found through website scraping (high confidence)
        website_data = lead.get('website_data', {})
        consolidated_data = website_data.get('consolidated_data', {})
        contact_emails = consolidated_data.get('contact_emails', [])
        
        if email in contact_emails:
            return "real"  # Found directly on website
        
        # Check email status from enricher
        if email_status in ['verified', 'found', 'scraped']:
            return "real"
        elif email_status in ['pattern', 'generated', 'standard']:
            return "pattern"
        else:
            return "guess"
    
    def get_confidence_reasoning(self, lead: Dict) -> str:
        """Get reasoning for email confidence level"""
        email = lead.get('email')
        confidence_level = lead.get('email_confidence_level', 'guess')
        
        if not email:
            return "No email address found"
        
        if confidence_level == "real":
            return "Email found directly on company website or verified through external source"
        elif confidence_level == "pattern":
            return "Email generated using standard company email patterns"
        else:
            return "Email generated using fallback logic - low confidence"
    
    def determine_engagement_status(self, lead: Dict) -> str:
        """Determine engagement status based on email confidence and data quality"""
        email_confidence = lead.get('email_confidence_level', 'guess')
        data_quality = lead.get('data_quality_score', 0)
        has_message_data = bool(lead.get('company_description') or lead.get('top_services'))
        
        # Auto-send criteria: Real or Pattern email + good website data
        if email_confidence in ['real', 'pattern'] and data_quality >= 50 and has_message_data:
            return "auto_send"
        
        # Ready criteria: Has email and some data
        elif email_confidence in ['real', 'pattern'] and (data_quality >= 30 or has_message_data):
            return "ready"
        
        # Needs review: Low confidence email or poor data quality
        elif email_confidence == 'guess' or data_quality < 30:
            return "needs_review"
        
        # Skip: No email found
        elif not lead.get('email'):
            return "skip"
        
        else:
            return "ready"  # Default fallback
    
    def get_engagement_reasoning(self, lead: Dict) -> str:
        """Get reasoning for engagement status"""
        status = lead.get('engagement_status', 'ready')
        email_confidence = lead.get('email_confidence_level', 'guess')
        data_quality = lead.get('data_quality_score', 0)
        
        if status == "auto_send":
            return f"High confidence email ({email_confidence}) + good website data (quality: {data_quality}/100)"
        elif status == "ready":
            return f"Decent email confidence ({email_confidence}) + adequate data (quality: {data_quality}/100)"
        elif status == "needs_review":
            return f"Low confidence email ({email_confidence}) or poor data quality ({data_quality}/100)"
        elif status == "skip":
            return "No email address found - cannot engage"
        else:
            return "Standard engagement readiness"
    
    def save_enrichment_log(self):
        """Save enrichment log to file for analysis"""
        try:
            with open(ENRICHMENT_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.enrichment_log, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Enrichment log saved to {ENRICHMENT_LOG_FILE}")
        except Exception as e:
            logger.error(f"❌ Failed to save enrichment log: {str(e)}")
    
    def get_enrichment_summary(self) -> Dict:
        """Get summary of enrichment operations"""
        if not self.enrichment_log:
            return {"total_operations": 0}
        
        summary = {
            "total_operations": len(self.enrichment_log),
            "leads_processed": len(set([log['lead_name'] for log in self.enrichment_log if log['lead_name'] != 'Unknown'])),
            "website_scraping_attempts": len([log for log in self.enrichment_log if log['decision_type'] == 'website_scraping_start']),
            "website_scraping_successes": len([log for log in self.enrichment_log if log['decision_type'] == 'website_scraping_success']),
            "email_enrichment_attempts": len([log for log in self.enrichment_log if log['decision_type'] == 'email_enrichment_start']),
            "email_enrichment_successes": len([log for log in self.enrichment_log if log['decision_type'] == 'email_enrichment_success']),
            "airtable_sync_successes": len([log for log in self.enrichment_log if log['decision_type'] == 'airtable_sync_success']),
            "overall_successes": len([log for log in self.enrichment_log if log['decision_type'] == 'enrichment_complete' and log.get('data', {}).get('overall_success')])
        }
        
        if summary["leads_processed"] > 0:
            summary["success_rate"] = (summary["overall_successes"] / summary["leads_processed"]) * 100
            summary["website_success_rate"] = (summary["website_scraping_successes"] / max(1, summary["website_scraping_attempts"])) * 100
            summary["email_success_rate"] = (summary["email_enrichment_successes"] / max(1, summary["email_enrichment_attempts"])) * 100
        
        return summary


async def enrich_leads_from_file(input_file: str, output_file: str) -> Dict:
    """Enrich leads from input file and save to output file"""
    enricher = EnhancedEnricher()
    
    # Load leads
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        logger.info(f"📥 Loaded {len(leads)} leads from {input_file}")
    except Exception as e:
        logger.error(f"❌ Failed to load leads from {input_file}: {str(e)}")
        return {"error": str(e)}
    
    # Enrich each lead
    enriched_leads = []
    for i, lead in enumerate(leads, 1):
        lead_name = lead.get('full_name') or lead.get('name', f'Lead {i}')
        logger.info(f"🔍 Enriching lead {i}/{len(leads)}: {lead_name}")
        
        try:
            enriched_lead = await enricher.enrich_lead_comprehensive(lead)
            enriched_leads.append(enriched_lead)
            
            # Small delay to avoid overwhelming services
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Failed to enrich {lead_name}: {str(e)}")
            # Add original lead with error info
            error_lead = lead.copy()
            error_lead.update({
                "enriched": False,
                "enrichment_error": str(e),
                "enriched_at": datetime.now().isoformat()
            })
            enriched_leads.append(error_lead)
    
    # Save enriched leads
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_leads, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved {len(enriched_leads)} enriched leads to {output_file}")
    except Exception as e:
        logger.error(f"❌ Failed to save enriched leads: {str(e)}")
        return {"error": f"Failed to save: {str(e)}"}
    
    # Save logs and get summary
    enricher.save_enrichment_log()
    enricher.airtable_client.save_sync_log()
    
    summary = enricher.get_enrichment_summary()
    airtable_summary = enricher.airtable_client.get_sync_summary()
    
    # Combine summaries
    final_summary = {
        "enrichment": summary,
        "airtable_sync": airtable_summary,
        "total_leads_processed": len(enriched_leads),
        "output_file": output_file
    }
    
    # Log final results
    logger.info(f"✅ Enhanced enrichment completed:")
    logger.info(f"   📊 Total leads: {len(enriched_leads)}")
    logger.info(f"   🌐 Website scraping success rate: {summary.get('website_success_rate', 0):.1f}%")
    logger.info(f"   📧 Email enrichment success rate: {summary.get('email_success_rate', 0):.1f}%")
    logger.info(f"   📤 Airtable sync success rate: {airtable_summary.get('success_rate', 0):.1f}%")
    logger.info(f"   🎯 Overall success rate: {summary.get('success_rate', 0):.1f}%")
    
    return final_summary


async def main():
    """Main function for enhanced enricher"""
    logger.info("🚀 Starting Enhanced Enricher Agent")
    
    # Define file paths
    input_file = os.path.join(SHARED_DIR, "verified_leads.json")
    output_file = os.path.join(SHARED_DIR, "enhanced_enriched_leads.json")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"❌ Input file not found: {input_file}")
        logger.info("💡 Run the verifier agent first to create verified_leads.json")
        return
    
    # Run enrichment
    summary = await enrich_leads_from_file(input_file, output_file)
    
    if "error" not in summary:
        logger.info("✅ Enhanced enrichment completed successfully")
        logger.info(f"📊 Final summary: {summary}")
    else:
        logger.error(f"❌ Enhanced enrichment failed: {summary['error']}")


if __name__ == "__main__":
    asyncio.run(main())