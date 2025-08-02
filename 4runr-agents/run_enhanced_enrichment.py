#!/usr/bin/env python3
"""
Run Enhanced Enrichment on Existing Leads

This script runs the enhanced enrichment system on your existing leads,
adding comprehensive website analysis and improved Airtable integration.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced-enrichment-runner')

# Add paths
script_dir = Path(__file__).parent.absolute()
shared_dir = script_dir / 'shared'
enricher_dir = script_dir / 'enricher'

import sys
sys.path.append(str(shared_dir))
sys.path.append(str(enricher_dir))

try:
    from enhanced_enricher import EnhancedEnricher, enrich_leads_from_file
    ENHANCED_ENRICHER_AVAILABLE = True
    logger.info("✅ Enhanced enricher loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to load enhanced enricher: {e}")
    ENHANCED_ENRICHER_AVAILABLE = False

async def run_enhanced_enrichment_on_existing_leads():
    """Run enhanced enrichment on existing leads"""
    logger.info("🚀 Starting Enhanced Enrichment on Existing Leads")
    
    if not ENHANCED_ENRICHER_AVAILABLE:
        logger.error("❌ Enhanced enricher not available")
        return
    
    # Define file paths
    input_files = [
        shared_dir / "enriched_leads.json",
        shared_dir / "verified_leads.json",
        shared_dir / "scraped_leads.json"
    ]
    
    # Find the best input file
    input_file = None
    for file_path in input_files:
        if file_path.exists():
            input_file = file_path
            logger.info(f"📥 Found input file: {input_file}")
            break
    
    if not input_file:
        logger.error("❌ No input file found. Looking for:")
        for file_path in input_files:
            logger.error(f"   - {file_path}")
        return
    
    # Load and preview leads
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        logger.info(f"📊 Loaded {len(leads)} leads from {input_file.name}")
        
        # Show sample of leads
        if leads:
            sample_lead = leads[0]
            logger.info(f"📋 Sample lead: {sample_lead.get('name') or sample_lead.get('full_name', 'Unknown')}")
            logger.info(f"   Company: {sample_lead.get('company', 'Unknown')}")
            logger.info(f"   Has email: {bool(sample_lead.get('email'))}")
            logger.info(f"   Has website data: {bool(sample_lead.get('website_data'))}")
            
    except Exception as e:
        logger.error(f"❌ Failed to load leads: {str(e)}")
        return
    
    # Limit leads for testing (remove this for full processing)
    test_limit = 5
    if len(leads) > test_limit:
        logger.info(f"🔬 Testing with first {test_limit} leads (remove limit for full processing)")
        leads = leads[:test_limit]
    
    # Create output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = shared_dir / f"enhanced_enriched_leads_{timestamp}.json"
    
    # Run enhanced enrichment
    logger.info(f"🔍 Starting enhanced enrichment on {len(leads)} leads...")
    
    enricher = EnhancedEnricher()
    enriched_leads = []
    
    for i, lead in enumerate(leads, 1):
        lead_name = lead.get('full_name') or lead.get('name', f'Lead {i}')
        company_name = lead.get('company', 'Unknown Company')
        
        logger.info(f"🔍 Enriching lead {i}/{len(leads)}: {lead_name} at {company_name}")
        
        try:
            # Run comprehensive enrichment
            enriched_lead = await enricher.enrich_lead_comprehensive(lead)
            enriched_leads.append(enriched_lead)
            
            # Log results
            data_quality = enriched_lead.get('data_quality_score', 0)
            email_status = enriched_lead.get('email_confidence_level', 'unknown')
            engagement_status = enriched_lead.get('engagement_status', 'unknown')
            
            logger.info(f"   ✅ Enriched: Quality={data_quality}/100, Email={email_status}, Status={engagement_status}")
            
            # Small delay to avoid overwhelming services
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"   ❌ Failed to enrich {lead_name}: {str(e)}")
            # Add original lead with error info
            error_lead = lead.copy()
            error_lead.update({
                "enriched": False,
                "enrichment_error": str(e),
                "enriched_at": datetime.now().isoformat()
            })
            enriched_leads.append(error_lead)
    
    # Save results
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_leads, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved {len(enriched_leads)} enhanced leads to {output_file}")
    except Exception as e:
        logger.error(f"❌ Failed to save results: {str(e)}")
        return
    
    # Save logs and get summary
    enricher.save_enrichment_log()
    enricher.airtable_client.save_sync_log()
    
    # Generate summary
    enrichment_summary = enricher.get_enrichment_summary()
    airtable_summary = enricher.airtable_client.get_sync_summary()
    
    # Log final results
    logger.info("=" * 60)
    logger.info("ENHANCED ENRICHMENT RESULTS")
    logger.info("=" * 60)
    logger.info(f"📊 Total leads processed: {len(enriched_leads)}")
    logger.info(f"🌐 Website scraping success rate: {enrichment_summary.get('website_success_rate', 0):.1f}%")
    logger.info(f"📧 Email enrichment success rate: {enrichment_summary.get('email_success_rate', 0):.1f}%")
    logger.info(f"📤 Airtable sync success rate: {airtable_summary.get('success_rate', 0):.1f}%")
    logger.info(f"🎯 Overall success rate: {enrichment_summary.get('success_rate', 0):.1f}%")
    logger.info(f"💾 Results saved to: {output_file}")
    
    # Show sample enriched lead
    if enriched_leads:
        sample_enriched = enriched_leads[0]
        logger.info("\n📋 Sample Enhanced Lead:")
        logger.info(f"   Name: {sample_enriched.get('full_name') or sample_enriched.get('name', 'Unknown')}")
        logger.info(f"   Company: {sample_enriched.get('company', 'Unknown')}")
        logger.info(f"   Data Quality: {sample_enriched.get('data_quality_score', 0)}/100")
        logger.info(f"   Company Description: {len(sample_enriched.get('company_description', ''))} chars")
        logger.info(f"   Services Found: {len(sample_enriched.get('top_services', []))}")
        logger.info(f"   Website Tone: {sample_enriched.get('tone', 'unknown')}")
        logger.info(f"   Email Confidence: {sample_enriched.get('email_confidence_level', 'unknown')}")
        logger.info(f"   Engagement Status: {sample_enriched.get('engagement_status', 'unknown')}")
    
    logger.info("✅ Enhanced enrichment completed successfully!")
    
    return {
        "total_leads": len(enriched_leads),
        "enrichment_summary": enrichment_summary,
        "airtable_summary": airtable_summary,
        "output_file": str(output_file)
    }

async def main():
    """Main function"""
    try:
        results = await run_enhanced_enrichment_on_existing_leads()
        if results:
            logger.info("🎉 Enhanced enrichment pipeline completed successfully!")
        else:
            logger.error("❌ Enhanced enrichment pipeline failed")
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())