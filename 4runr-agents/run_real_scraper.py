#!/usr/bin/env python3
"""
Run Real Scraper - Get 5 Real Montreal CEOs
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

# Import the verified Montreal CEOs
from montreal_ceos_verified import get_verified_montreal_ceos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('real-scraper')

# Constants
SHARED_DIR = os.path.join(os.path.dirname(__file__), "shared")
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")

def save_raw_leads(leads):
    """Save leads to raw_leads.json - REAL PEOPLE ONLY"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Format leads for real people only pipeline
    formatted_leads = []
    for lead in leads:
        # STRICT VALIDATION: Only real people with LinkedIn URLs
        if not lead.get("linkedin_url") or not lead.get("name"):
            logger.warning(f"⚠️ Skipping person without LinkedIn URL: {lead.get('name', 'Unknown')}")
            continue
        
        # Generate UUID for tracking
        lead_uuid = str(uuid.uuid4())
        
        formatted_lead = {
            "uuid": lead_uuid,
            "full_name": lead["name"],
            "linkedin_url": lead["linkedin_url"],
            "company": lead.get("company", ""),
            "title": lead.get("title", ""),
            "location": lead.get("location", "Montreal, Quebec, Canada"),
            "verified": False,  # Will be set by verifier
            "enriched": False,  # Will be set by enricher
            "email": None,  # Will be set by enricher if found
            "engagement_method": None,  # Will be set by engager
            "scraped_at": datetime.now().isoformat(),
            "source": "Verified Montreal CEOs Database - Real People Only"
        }
        
        formatted_leads.append(formatted_lead)
    
    if not formatted_leads:
        logger.error("❌ No real people found with LinkedIn URLs")
        return
    
    # Save to raw_leads.json with proper UTF-8 encoding
    raw_leads_file = os.path.join(SHARED_DIR, "raw_leads.json")
    
    with open(raw_leads_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_leads, f, indent=2, ensure_ascii=False)
    
    # Update control file with proper UTF-8 encoding
    with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_scrape": datetime.now().isoformat(),
            "lead_count": len(formatted_leads),
            "status": "ready_for_verification",
            "pipeline_stage": "raw_leads"
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved {len(formatted_leads)} real people to raw_leads.json")
    logger.info(f"🔄 Pipeline status: Ready for verification")

async def main():
    """Main function to get real Montreal CEOs"""
    logger.info("🚀 Starting Real Montreal CEO Scraper")
    
    try:
        # Get 5 verified Montreal CEOs
        max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '5'))
        logger.info(f"🎯 Getting {max_leads} verified Montreal CEOs...")
        
        leads = await get_verified_montreal_ceos(max_leads)
        
        if not leads:
            logger.error("❌ No verified Montreal CEOs found")
            return
        
        logger.info(f"✅ Successfully retrieved {len(leads)} verified Montreal CEOs:")
        for lead in leads:
            logger.info(f"   📋 {lead['name']} - {lead['title']} at {lead['company']}")
            logger.info(f"   🔗 {lead['linkedin_url']}")
        
        # Save the leads for the validation-first pipeline
        save_raw_leads(leads)
        
        logger.info("✅ Real scraping completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in real scraper: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())