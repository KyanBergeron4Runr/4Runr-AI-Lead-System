#!/usr/bin/env python3
"""
Test Pipeline with Upgraded Components
Tests the upgraded scraper, enricher, and logging system
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pipeline-test-upgraded')

def create_test_results_log(test_results):
    """Create detailed test results log"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"test_results_{timestamp}.json"
    
    with open(log_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"📊 Test results saved to: {log_file}")
    return log_file

async def run_upgraded_pipeline_test():
    """Run the upgraded pipeline with detailed logging"""
    
    logger.info("🚀 Starting Upgraded Pipeline Test")
    logger.info("=" * 60)
    
    test_results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_type": "upgraded_pipeline_full_test",
        "max_leads": int(os.getenv('MAX_LEADS_PER_RUN', '3')),
        "leads": [],
        "summary": {
            "total_scraped": 0,
            "total_verified": 0,
            "total_enriched": 0,
            "total_engaged": 0,
            "verification_rate": 0,
            "enrichment_rate": 0,
            "engagement_rate": 0,
            "airtable_sync_rate": 0
        }
    }
    
    # Set test environment
    os.environ['MAX_LEADS_PER_RUN'] = '3'
    os.environ['RUN_ONCE'] = 'true'
    
    try:
        # Phase 1: Scraping
        logger.info("📋 PHASE 1: SCRAPING")
        logger.info("-" * 30)
        
        from scraper.app import main as scraper_main
        await scraper_main()
        
        # Load scraped leads
        shared_dir = Path(__file__).parent / "shared"
        raw_leads_file = shared_dir / "raw_leads.json"
        
        if raw_leads_file.exists():
            with open(raw_leads_file, 'r') as f:
                scraped_leads = json.load(f)
            
            test_results["summary"]["total_scraped"] = len(scraped_leads)
            logger.info(f"✅ Scraped {len(scraped_leads)} leads")
            
            # Initialize lead tracking
            for lead in scraped_leads:
                test_results["leads"].append({
                    "uuid": lead.get("uuid", "unknown"),
                    "full_name": lead.get("full_name", "Unknown"),
                    "profile_url": lead.get("linkedin_url", ""),
                    "verification_status": "pending",
                    "email_found": False,
                    "engagement_type": "pending",
                    "airtable_push_status": "pending"
                })
        else:
            logger.error("❌ No raw leads found")
            return test_results
        
        # Phase 2: Verification
        logger.info("\n🔍 PHASE 2: VERIFICATION")
        logger.info("-" * 30)
        
        os.system("python run_agent.py verifier")
        
        # Load verification results
        verified_leads_file = shared_dir / "verified_leads.json"
        dropped_leads_file = shared_dir / "dropped_leads.json"
        
        verified_count = 0
        if verified_leads_file.exists():
            with open(verified_leads_file, 'r') as f:
                verified_leads = json.load(f)
            verified_count = len(verified_leads)
            
            # Update test results
            for verified_lead in verified_leads:
                for result_lead in test_results["leads"]:
                    if result_lead["uuid"] == verified_lead.get("uuid"):
                        result_lead["verification_status"] = "verified"
                        break
        
        dropped_count = 0
        if dropped_leads_file.exists():
            with open(dropped_leads_file, 'r') as f:
                dropped_leads = json.load(f)
            dropped_count = len(dropped_leads)
            
            # Update test results for dropped leads
            for dropped_lead in dropped_leads:
                for result_lead in test_results["leads"]:
                    if result_lead["uuid"] == dropped_lead.get("uuid"):
                        result_lead["verification_status"] = f"dropped_{dropped_lead.get('dropped_reason', 'unknown')}"
                        break
        
        test_results["summary"]["total_verified"] = verified_count
        test_results["summary"]["verification_rate"] = (verified_count / test_results["summary"]["total_scraped"]) * 100 if test_results["summary"]["total_scraped"] > 0 else 0
        
        logger.info(f"✅ Verified: {verified_count}, Dropped: {dropped_count}")
        logger.info(f"📊 Verification Rate: {test_results['summary']['verification_rate']:.1f}%")
        
        # Phase 3: Enrichment
        logger.info("\n💎 PHASE 3: ENRICHMENT")
        logger.info("-" * 30)
        
        os.system("python run_agent.py enricher")
        
        # Load enrichment results
        enriched_leads_file = shared_dir / "enriched_leads.json"
        
        enriched_count = 0
        if enriched_leads_file.exists():
            with open(enriched_leads_file, 'r') as f:
                enriched_leads = json.load(f)
            enriched_count = len(enriched_leads)
            
            # Update test results
            for enriched_lead in enriched_leads:
                for result_lead in test_results["leads"]:
                    if result_lead["uuid"] == enriched_lead.get("uuid"):
                        has_email = enriched_lead.get("email") and enriched_lead.get("email") != "" and enriched_lead.get("email") is not None
                        result_lead["email_found"] = has_email
                        break
        
        test_results["summary"]["total_enriched"] = enriched_count
        test_results["summary"]["enrichment_rate"] = (enriched_count / verified_count) * 100 if verified_count > 0 else 0
        
        logger.info(f"✅ Enriched: {enriched_count}")
        logger.info(f"📊 Enrichment Rate: {test_results['summary']['enrichment_rate']:.1f}%")
        
        # Phase 4: Engagement
        logger.info("\n🎯 PHASE 4: ENGAGEMENT")
        logger.info("-" * 30)
        
        os.system("python run_agent.py engager")
        
        # Load engagement results
        engaged_leads_file = shared_dir / "engaged_leads.json"
        
        engaged_count = 0
        if engaged_leads_file.exists():
            with open(engaged_leads_file, 'r') as f:
                engaged_leads = json.load(f)
            engaged_count = len(engaged_leads)
            
            # Update test results
            airtable_synced = 0
            for engaged_lead in engaged_leads:
                for result_lead in test_results["leads"]:
                    if result_lead["uuid"] == engaged_lead.get("uuid"):
                        engagement_method = engaged_lead.get("engagement", {}).get("method", "unknown")
                        result_lead["engagement_type"] = engagement_method
                        
                        if engaged_lead.get("airtable_synced"):
                            result_lead["airtable_push_status"] = "success"
                            airtable_synced += 1
                        else:
                            result_lead["airtable_push_status"] = "failed"
                        break
            
            test_results["summary"]["airtable_sync_rate"] = (airtable_synced / engaged_count) * 100 if engaged_count > 0 else 0
        
        test_results["summary"]["total_engaged"] = engaged_count
        test_results["summary"]["engagement_rate"] = (engaged_count / enriched_count) * 100 if enriched_count > 0 else 0
        
        logger.info(f"✅ Engaged: {engaged_count}")
        logger.info(f"📊 Engagement Rate: {test_results['summary']['engagement_rate']:.1f}%")
        logger.info(f"📊 Airtable Sync Rate: {test_results['summary']['airtable_sync_rate']:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        test_results["error"] = str(e)
    
    # Generate final report
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL TEST RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"📋 Total Scraped: {test_results['summary']['total_scraped']}")
    logger.info(f"🔍 Total Verified: {test_results['summary']['total_verified']} ({test_results['summary']['verification_rate']:.1f}%)")
    logger.info(f"💎 Total Enriched: {test_results['summary']['total_enriched']} ({test_results['summary']['enrichment_rate']:.1f}%)")
    logger.info(f"🎯 Total Engaged: {test_results['summary']['total_engaged']} ({test_results['summary']['engagement_rate']:.1f}%)")
    logger.info(f"📊 Airtable Synced: {test_results['summary']['airtable_sync_rate']:.1f}%")
    
    logger.info("\n📋 INDIVIDUAL LEAD RESULTS:")
    for lead in test_results["leads"]:
        logger.info(f"   👤 {lead['full_name']}")
        logger.info(f"      🔗 {lead['profile_url']}")
        logger.info(f"      ✅ Verification: {lead['verification_status']}")
        logger.info(f"      📧 Email Found: {lead['email_found']}")
        logger.info(f"      🎯 Engagement: {lead['engagement_type']}")
        logger.info(f"      📊 Airtable: {lead['airtable_push_status']}")
        logger.info("")
    
    # Save detailed results
    log_file = create_test_results_log(test_results)
    
    logger.info(f"📁 Detailed results saved to: {log_file}")
    logger.info("🎉 Upgraded Pipeline Test Complete!")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(run_upgraded_pipeline_test())