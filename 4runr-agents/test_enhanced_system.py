#!/usr/bin/env python3
"""
Test Enhanced 4Runr System

This script tests the enhanced website scraping, enrichment, and Airtable integration.
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
logger = logging.getLogger('enhanced-system-test')

# Add shared directory to path
script_dir = Path(__file__).parent.absolute()
shared_dir = script_dir / 'shared'
import sys
sys.path.append(str(shared_dir))

try:
    from website_scraper import scrape_lead_website
    from enhanced_airtable_client import test_airtable_integration, sync_leads_to_airtable
    ENHANCED_MODULES_AVAILABLE = True
    logger.info("✅ Enhanced modules loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to load enhanced modules: {e}")
    ENHANCED_MODULES_AVAILABLE = False

async def test_website_scraping():
    """Test the enhanced website scraper"""
    logger.info("🌐 Testing Enhanced Website Scraper")
    
    # Test leads with different company types
    test_leads = [
        {
            "name": "Tobias Lütke",
            "company": "Shopify",
            "title": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/tobi/"
        },
        {
            "name": "George Schindler", 
            "company": "CGI Group",
            "title": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/george-schindler-cgi/"
        },
        {
            "name": "Test CEO",
            "company": "Dollarama",
            "title": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/testceo"
        }
    ]
    
    results = []
    
    for i, lead in enumerate(test_leads, 1):
        logger.info(f"🔍 Testing website scraping {i}/{len(test_leads)}: {lead['company']}")
        
        try:
            enhanced_lead = await scrape_lead_website(lead)
            
            # Log results
            data_quality = enhanced_lead.get('data_quality_score', 0)
            company_desc_len = len(enhanced_lead.get('company_description', ''))
            services_count = len(enhanced_lead.get('top_services', []))
            tone = enhanced_lead.get('tone', 'unknown')
            
            logger.info(f"   📊 Quality Score: {data_quality}/100")
            logger.info(f"   📝 Description: {company_desc_len} characters")
            logger.info(f"   🛠️ Services: {services_count} found")
            logger.info(f"   🎭 Tone: {tone}")
            
            # Show decision log summary
            if enhanced_lead.get('website_data', {}).get('decision_log'):
                decisions = enhanced_lead['website_data']['decision_log']
                key_decisions = [d for d in decisions if d['decision_type'] in ['base_url_success', 'content_extraction', 'quality_assessment']]
                logger.info(f"   🔍 Key decisions: {len(key_decisions)} logged")
                
                for decision in key_decisions[-3:]:  # Show last 3 key decisions
                    logger.info(f"      - {decision['decision_type']}: {decision['details']}")
            
            results.append(enhanced_lead)
            
        except Exception as e:
            logger.error(f"❌ Website scraping failed for {lead['company']}: {str(e)}")
            results.append(lead)  # Add original lead
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    # Save results
    output_file = shared_dir / "website_scraping_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Website scraping test results saved to {output_file}")
    
    return results

def test_airtable_enhanced():
    """Test the enhanced Airtable integration"""
    logger.info("📤 Testing Enhanced Airtable Integration")
    
    # Test with comprehensive lead data
    test_leads = [
        {
            "full_name": "Enhanced Test Lead 1",
            "email": "ceo@enhancedtest1.com",
            "company": "Enhanced Test Corp 1",
            "title": "Chief Executive Officer",
            "linkedin_url": "https://linkedin.com/in/enhancedtest1",
            "company_description": "A leading technology company specializing in innovative cloud solutions and digital transformation services for enterprise clients.",
            "top_services": ["Cloud Migration", "Digital Transformation", "AI Integration", "Cybersecurity"],
            "tone": "professional",
            "website_insights": "Homepage: Cutting-edge solutions | About: 15+ years experience | Services: Enterprise focus",
            "email_confidence_level": "real",
            "custom_message": "Hi there! I noticed your expertise in cloud migration and digital transformation...",
            "engagement_status": "auto_send",
            "data_quality_score": 92,
            "source": "LinkedIn Search",
            "scraped_at": datetime.now().isoformat(),
            "enriched_at": datetime.now().isoformat(),
            "website_data": {
                "data_quality_score": 92,
                "successful_urls": ["https://enhancedtest1.com"],
                "pages_scraped": {"homepage": {}, "about": {}, "services": {}},
                "decision_log": [
                    {"decision_type": "scrape_success", "details": "Successfully scraped 3 pages"},
                    {"decision_type": "content_extraction", "details": "Extracted comprehensive company data"},
                    {"decision_type": "quality_assessment", "details": "High quality data found"}
                ]
            }
        },
        {
            "full_name": "Enhanced Test Lead 2",
            "email": "founder@startup2.com", 
            "company": "Innovative Startup 2",
            "title": "Founder & CEO",
            "linkedin_url": "https://linkedin.com/in/enhancedtest2",
            "company_description": "A fast-growing startup focused on sustainable technology solutions.",
            "top_services": ["Green Tech", "Sustainability Consulting"],
            "tone": "friendly",
            "website_insights": "Homepage: Sustainability focus | About: Mission-driven team",
            "email_confidence_level": "pattern",
            "engagement_status": "ready",
            "data_quality_score": 67,
            "source": "LinkedIn Search",
            "scraped_at": datetime.now().isoformat(),
            "enriched_at": datetime.now().isoformat()
        }
    ]
    
    # Test sync
    results = sync_leads_to_airtable(test_leads)
    
    logger.info("📊 Enhanced Airtable test results:")
    logger.info(f"   Total leads: {results['total_leads']}")
    logger.info(f"   Successful syncs: {results['successful_syncs']}")
    logger.info(f"   Failed syncs: {results['failed_syncs']}")
    logger.info(f"   Success rate: {results.get('success_rate', 0):.1f}%")
    
    return results

async def test_full_pipeline():
    """Test the full enhanced pipeline"""
    logger.info("🚀 Testing Full Enhanced Pipeline")
    
    # Step 1: Website scraping
    logger.info("Step 1: Website Scraping")
    scraping_results = await test_website_scraping()
    
    # Step 2: Airtable sync with scraped data
    logger.info("Step 2: Airtable Sync")
    
    # Prepare leads for Airtable (add required fields)
    airtable_leads = []
    for lead in scraping_results:
        airtable_lead = lead.copy()
        
        # Add missing fields for complete test
        if not airtable_lead.get('email'):
            # Generate test email
            company_domain = airtable_lead.get('company', 'test').lower().replace(' ', '') + '.com'
            first_name = airtable_lead.get('name', 'test').split()[0].lower()
            airtable_lead['email'] = f"{first_name}@{company_domain}"
        
        # Set confidence levels based on data quality
        data_quality = airtable_lead.get('data_quality_score', 0)
        if data_quality >= 70:
            airtable_lead['email_confidence_level'] = 'pattern'
            airtable_lead['engagement_status'] = 'auto_send'
        elif data_quality >= 40:
            airtable_lead['email_confidence_level'] = 'pattern'
            airtable_lead['engagement_status'] = 'ready'
        else:
            airtable_lead['email_confidence_level'] = 'guess'
            airtable_lead['engagement_status'] = 'needs_review'
        
        # Add timestamps
        airtable_lead['enriched_at'] = datetime.now().isoformat()
        
        airtable_leads.append(airtable_lead)
    
    # Sync to Airtable
    airtable_results = sync_leads_to_airtable(airtable_leads)
    
    # Step 3: Generate summary report
    logger.info("Step 3: Generating Summary Report")
    
    summary = {
        "test_timestamp": datetime.now().isoformat(),
        "website_scraping": {
            "leads_tested": len(scraping_results),
            "successful_scrapes": len([l for l in scraping_results if l.get('data_quality_score', 0) > 0]),
            "average_quality_score": sum([l.get('data_quality_score', 0) for l in scraping_results]) / len(scraping_results),
            "leads_with_descriptions": len([l for l in scraping_results if l.get('company_description')]),
            "leads_with_services": len([l for l in scraping_results if l.get('top_services')])
        },
        "airtable_sync": airtable_results,
        "overall_success": airtable_results.get('success_rate', 0) > 50
    }
    
    # Save summary
    summary_file = shared_dir / "enhanced_system_test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📊 Full pipeline test summary:")
    logger.info(f"   🌐 Website scraping success rate: {(summary['website_scraping']['successful_scrapes'] / summary['website_scraping']['leads_tested']) * 100:.1f}%")
    logger.info(f"   📊 Average data quality: {summary['website_scraping']['average_quality_score']:.1f}/100")
    logger.info(f"   📤 Airtable sync success rate: {summary['airtable_sync'].get('success_rate', 0):.1f}%")
    logger.info(f"   🎯 Overall pipeline success: {'✅' if summary['overall_success'] else '❌'}")
    logger.info(f"   💾 Summary saved to: {summary_file}")
    
    return summary

async def main():
    """Main test function"""
    logger.info("🧪 Starting Enhanced 4Runr System Tests")
    
    if not ENHANCED_MODULES_AVAILABLE:
        logger.error("❌ Enhanced modules not available. Cannot run tests.")
        return
    
    try:
        # Test individual components first
        logger.info("=" * 60)
        logger.info("COMPONENT TESTS")
        logger.info("=" * 60)
        
        # Test Airtable integration
        airtable_test = test_airtable_integration()
        logger.info(f"Airtable integration test: {'✅ PASS' if airtable_test else '❌ FAIL'}")
        
        # Test full pipeline
        logger.info("=" * 60)
        logger.info("FULL PIPELINE TEST")
        logger.info("=" * 60)
        
        pipeline_summary = await test_full_pipeline()
        
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        if pipeline_summary['overall_success']:
            logger.info("✅ Enhanced 4Runr system tests PASSED")
            logger.info("🎉 System is ready for production use")
        else:
            logger.warning("⚠️ Enhanced 4Runr system tests had issues")
            logger.info("🔧 Review logs and fix issues before production use")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())