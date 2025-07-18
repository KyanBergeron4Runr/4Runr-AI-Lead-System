#!/usr/bin/env python3
"""
4Runr Lead Pipeline Runner

This script runs the entire lead generation pipeline by executing each agent in sequence.
It's the main entry point for running the pipeline.
"""

import os
import sys
import time
import json
import logging
import subprocess
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-runner')

def run_agent(agent_name):
    """Run an agent and wait for it to complete"""
    logger.info(f"[RUNNER] Running {agent_name} agent...")
    
    # Get the path to the agent script
    script_dir = pathlib.Path(__file__).parent.absolute()
    agent_script = script_dir / agent_name / "app.py"
    
    if not agent_script.exists():
        logger.error(f"Agent script not found: {agent_script}")
        return False
    
    # Run the agent script
    try:
        # Set environment variable to run the agent only once (not in a loop)
        env = os.environ.copy()
        env["RUN_ONCE"] = "true"
        
        # Run the agent
        result = subprocess.run(
            [sys.executable, str(agent_script)],
            env=env,
            check=True
        )
        
        logger.info(f"[RUNNER] {agent_name} agent completed with exit code {result.returncode}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"[RUNNER] Error running {agent_name} agent: {e}")
        return False

def check_leads_file():
    """Check the leads.json file and print its contents"""
    script_dir = pathlib.Path(__file__).parent.absolute()
    leads_file = script_dir / "shared" / "leads.json"
    
    if not leads_file.exists():
        logger.warning(f"Leads file not found: {leads_file}")
        return
    
    try:
        with open(leads_file, 'r') as f:
            leads = json.load(f)
            
        logger.info(f"[RUNNER] Leads file contains {len(leads)} leads")
        
        # Count leads by status
        status_counts = {}
        for lead in leads:
            status = lead.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            logger.info(f"[RUNNER] - {status}: {count} leads")
        
        # Check Airtable sync status
        synced = sum(1 for lead in leads if lead.get("airtable_synced", False))
        logger.info(f"[RUNNER] - {synced} leads synced to Airtable")
        
    except json.JSONDecodeError:
        logger.error(f"Could not parse leads file: {leads_file}")

def retry_failed_airtable_syncs():
    """Retry pushing failed leads to Airtable"""
    try:
        # Import the Airtable client
        from shared.airtable_client import retry_failed_leads
        
        # Retry failed leads
        retried = retry_failed_leads()
        if retried > 0:
            logger.info(f"[RUNNER] Successfully retried {retried} failed Airtable syncs")
    except Exception as e:
        logger.error(f"[RUNNER] Error retrying failed Airtable syncs: {str(e)}")

def main():
    """Run the entire pipeline"""
    logger.info("[RUNNER] Starting 4Runr lead generation pipeline...")
    
    # Check if the leads file exists before starting
    check_leads_file()
    
    # Run the scraper agent
    if not run_agent("scraper"):
        logger.error("[RUNNER] Scraper agent failed, stopping pipeline")
        return 1
    
    # Check the leads file after scraping
    logger.info("[RUNNER] Checking leads after scraping:")
    check_leads_file()
    
    # Wait a moment before running the enricher
    time.sleep(2)
    
    # Run the enricher agent
    if not run_agent("enricher"):
        logger.error("[RUNNER] Enricher agent failed, stopping pipeline")
        return 1
    
    # Check the leads file after enrichment
    logger.info("[RUNNER] Checking leads after enrichment:")
    check_leads_file()
    
    # Wait a moment before running the engager
    time.sleep(2)
    
    # Run the engager agent
    if not run_agent("engager"):
        logger.error("[RUNNER] Engager agent failed, stopping pipeline")
        return 1
    
    # Check the leads file after engagement
    logger.info("[RUNNER] Checking leads after engagement:")
    check_leads_file()
    
    # Retry any failed Airtable syncs
    retry_failed_airtable_syncs()
    
    logger.info("[RUNNER] Pipeline complete ✅")
    return 0

if __name__ == "__main__":
    sys.exit(main())