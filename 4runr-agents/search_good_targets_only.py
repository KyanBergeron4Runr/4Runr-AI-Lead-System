#!/usr/bin/env python3
"""
Search ONLY the good mid-size company targets - conserve API calls
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the current directory to path to import the LinkedIn agent
sys.path.append(os.path.dirname(__file__))
from linkedin_lookup_agent import LinkedInLookupAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('good-targets-search')

def get_good_targets_only():
    """Get only the 6 good mid-size company targets"""
    shared_dir = Path(__file__).parent / "shared"
    raw_leads_file = shared_dir / "raw_leads.json"
    
    if not raw_leads_file.exists():
        logger.error("❌ raw_leads.json not found")
        return []
    
    with open(raw_leads_file, 'r', encoding='utf-8') as f:
        all_leads = json.load(f)
    
    # Define the 6 GOOD targets (mid-size companies)
    good_targets = [
        'lightspeed', 'nuvei', 'cae', 'couche-tard', 'snc-lavalin', 'tfi'
    ]
    
    filtered_leads = []
    for lead in all_leads:
        company = lead.get('company', '').lower()
        if any(target in company for target in good_targets):
            filtered_leads.append(lead)
    
    return filtered_leads

def main():
    """Search only the good targets to conserve API calls"""
    logger.info("🎯 Searching ONLY good mid-size company targets")
    logger.info("💰 Conserving API calls - avoiding huge company CEOs")
    
    # Get only good targets
    good_leads = get_good_targets_only()
    
    if not good_leads:
        logger.error("❌ No good targets found")
        return
    
    logger.info(f"✅ Found {len(good_leads)} good targets:")
    for lead in good_leads:
        name = lead.get('full_name', 'Unknown')
        company = lead.get('company', 'Unknown')
        logger.info(f"   • {name} ({company})")
    
    # Initialize LinkedIn agent
    agent = LinkedInLookupAgent()
    
    # Process only the good leads with max searches limit
    logger.info(f"🔍 Starting LinkedIn search for {len(good_leads)} good targets...")
    resolved_results = agent.process_leads_batch(good_leads, max_searches=6)
    
    # Save results
    agent.save_results(resolved_results)
    
    # Update verified leads
    agent.update_verified_leads(resolved_results)
    
    # Summary
    successful_lookups = len([r for r in resolved_results if r['status'] == 'verified'])
    total_lookups = len(resolved_results)
    
    logger.info("🎯 GOOD TARGETS Search Summary:")
    logger.info(f"   API calls used: {total_lookups}")
    logger.info(f"   Successful matches: {successful_lookups}")
    logger.info(f"   Success rate: {successful_lookups/total_lookups*100:.1f}%")
    logger.info(f"   API calls remaining: ~{100-46-total_lookups}")
    
    if successful_lookups > 0:
        logger.info("✅ These are MUCH better targets than huge company CEOs!")
    
    logger.info("✅ Good targets search completed")

if __name__ == "__main__":
    main()