#!/usr/bin/env python3
"""
Full System Test Script

This script tests the entire 4Runr lead generation system, including:
1. Scraper agent
2. Enricher agent
3. Engager agent
4. Airtable integration

It provides detailed output to verify that each component is working correctly.
"""

import os
import sys
import json
import time
import logging
import pathlib
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system-test')

# Add the parent directory to the Python path
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
sys.path.append(str(root_dir))

def clean_test_environment():
    """Clean the test environment by removing any existing leads"""
    logger.info("Cleaning test environment...")
    
    # Remove the leads.json file if it exists
    leads_file = root_dir / "shared" / "leads.json"
    if leads_file.exists():
        leads_file.unlink()
        logger.info(f"Removed existing leads file: {leads_file}")
    
    # Remove the control file if it exists
    control_file = root_dir / "shared" / "control.json"
    if control_file.exists():
        control_file.unlink()
        logger.info(f"Removed existing control file: {control_file}")
    
    # Remove the failed leads file if it exists
    failed_leads_file = root_dir / "shared" / "failed_leads.json"
    if failed_leads_file.exists():
        failed_leads_file.unlink()
        logger.info(f"Removed existing failed leads file: {failed_leads_file}")
    
    logger.info("Test environment cleaned successfully")

def run_agent(agent_name):
    """Run an agent and capture its output"""
    logger.info(f"Running {agent_name} agent...")
    
    # Get the path to the agent script
    agent_script = root_dir / agent_name / "app.py"
    
    if not agent_script.exists():
        logger.error(f"Agent script not found: {agent_script}")
        return False, ""
    
    # Run the agent script
    try:
        # Set environment variable to run the agent only once (not in a loop)
        env = os.environ.copy()
        env["RUN_ONCE"] = "true"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Run the agent and capture output
        process = subprocess.run(
            [sys.executable, str(agent_script)],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info(f"{agent_name} agent completed with exit code {process.returncode}")
        return True, process.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {agent_name} agent: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False, e.stdout + "\n" + e.stderr

def check_leads_file():
    """Check the leads.json file and return its contents"""
    leads_file = root_dir / "shared" / "leads.json"
    
    if not leads_file.exists():
        logger.warning(f"Leads file not found: {leads_file}")
        return []
    
    try:
        with open(leads_file, 'r') as f:
            leads = json.load(f)
        
        logger.info(f"Leads file contains {len(leads)} leads")
        return leads
    except json.JSONDecodeError:
        logger.error(f"Could not parse leads file: {leads_file}")
        return []

def test_airtable_client():
    """Test the Airtable client directly"""
    logger.info("Testing Airtable client...")
    
    try:
        # Import the Airtable client
        from shared.airtable_client import push_lead_to_airtable
        
        # Create a test lead
        test_lead = {
            "name": "Test Lead",
            "linkedin_url": "https://linkedin.com/in/testlead",
            "company": "Test Company",
            "title": "Test Title",
            "email": "test@example.com",
            "status": "contacted",
            "engagement": {
                "channel": "email",
                "sent_at": datetime.now().isoformat(),
                "status": "sent"
            }
        }
        
        # Try to push the lead to Airtable
        result = push_lead_to_airtable(test_lead)
        
        if result:
            logger.info("✅ Airtable client test successful!")
        else:
            logger.warning("⚠️ Airtable client test failed. Check your Airtable configuration.")
        
        return result
    except Exception as e:
        logger.error(f"❌ Error testing Airtable client: {str(e)}")
        return False

def main():
    """Main function to test the full system"""
    logger.info("Starting full system test...")
    
    # Clean the test environment
    clean_test_environment()
    
    # Test the Airtable client directly
    airtable_works = test_airtable_client()
    
    # Run the scraper agent
    scraper_success, scraper_output = run_agent("scraper")
    if not scraper_success:
        logger.error("❌ Scraper agent failed, stopping test")
        return 1
    
    # Check the leads file after scraping
    leads_after_scrape = check_leads_file()
    if not leads_after_scrape:
        logger.error("❌ No leads found after scraping, stopping test")
        return 1
    
    # Print scraper output highlights
    logger.info("Scraper output highlights:")
    for line in scraper_output.splitlines():
        if "[SCRAPER]" in line:
            logger.info(f"  {line.strip()}")
    
    # Wait a moment before running the enricher
    time.sleep(2)
    
    # Run the enricher agent
    enricher_success, enricher_output = run_agent("enricher")
    if not enricher_success:
        logger.error("❌ Enricher agent failed, stopping test")
        return 1
    
    # Check the leads file after enrichment
    leads_after_enrich = check_leads_file()
    
    # Print enricher output highlights
    logger.info("Enricher output highlights:")
    for line in enricher_output.splitlines():
        if "[ENRICHER]" in line:
            logger.info(f"  {line.strip()}")
    
    # Verify that leads were enriched
    enriched_count = sum(1 for lead in leads_after_enrich if lead.get("status") == "enriched")
    logger.info(f"Found {enriched_count} enriched leads")
    
    if enriched_count == 0:
        logger.error("❌ No leads were enriched, stopping test")
        return 1
    
    # Wait a moment before running the engager
    time.sleep(2)
    
    # Run the engager agent
    engager_success, engager_output = run_agent("engager")
    if not engager_success:
        logger.error("❌ Engager agent failed, stopping test")
        return 1
    
    # Check the leads file after engagement
    leads_after_engage = check_leads_file()
    
    # Print engager output highlights
    logger.info("Engager output highlights:")
    for line in engager_output.splitlines():
        if "[ENGAGER]" in line or "[AIRTABLE]" in line:
            logger.info(f"  {line.strip()}")
    
    # Verify that leads were engaged
    engaged_count = sum(1 for lead in leads_after_engage if lead.get("status") == "contacted")
    logger.info(f"Found {engaged_count} contacted leads")
    
    if engaged_count == 0:
        logger.error("❌ No leads were engaged, stopping test")
        return 1
    
    # Verify Airtable sync status
    if airtable_works:
        synced_count = sum(1 for lead in leads_after_engage if lead.get("airtable_synced", False))
        logger.info(f"Found {synced_count} leads synced to Airtable")
        
        if synced_count == 0:
            logger.warning("⚠️ No leads were synced to Airtable")
    
    # Print test summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Scraper: {'✅ PASSED' if scraper_success else '❌ FAILED'}")
    logger.info(f"Enricher: {'✅ PASSED' if enricher_success else '❌ FAILED'}")
    logger.info(f"Engager: {'✅ PASSED' if engager_success else '❌ FAILED'}")
    logger.info(f"Airtable: {'✅ PASSED' if airtable_works else '⚠️ NOT TESTED'}")
    logger.info(f"Leads generated: {len(leads_after_scrape)}")
    logger.info(f"Leads enriched: {enriched_count}")
    logger.info(f"Leads engaged: {engaged_count}")
    if airtable_works:
        logger.info(f"Leads synced to Airtable: {synced_count}")
    
    if scraper_success and enricher_success and engager_success:
        logger.info("\n✅ FULL SYSTEM TEST PASSED!")
        return 0
    else:
        logger.error("\n❌ FULL SYSTEM TEST FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())