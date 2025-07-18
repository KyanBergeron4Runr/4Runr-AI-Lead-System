#!/usr/bin/env python3
"""
Pipeline Runner Script

This script runs the entire lead generation pipeline by executing each agent in sequence.
It's useful for testing the pipeline without using Docker.
"""

import os
import sys
import time
import json
import pathlib
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-runner')

def run_agent(agent_name):
    """Run an agent and wait for it to complete"""
    logger.info(f"Running {agent_name} agent...")
    
    # Get the path to the agent script
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    agent_script = root_dir / agent_name / "app.py"
    
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
        
        logger.info(f"{agent_name} agent completed with exit code {result.returncode}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {agent_name} agent: {e}")
        return False

def check_leads_file():
    """Check the leads.json file and print its contents"""
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    leads_file = root_dir / "shared" / "leads.json"
    
    if not leads_file.exists():
        logger.warning(f"Leads file not found: {leads_file}")
        return
    
    try:
        with open(leads_file, 'r') as f:
            leads = json.load(f)
            
        logger.info(f"Leads file contains {len(leads)} leads:")
        
        # Print a summary of the leads
        for i, lead in enumerate(leads):
            status = lead.get("status", "unknown")
            name = lead.get("name", "Unknown")
            company = lead.get("company", "Unknown")
            email = lead.get("email", "None")
            
            logger.info(f"  {i+1}. {name} ({company}) - Status: {status}, Email: {email}")
    
    except json.JSONDecodeError:
        logger.error(f"Could not parse leads file: {leads_file}")

def main():
    """Run the entire pipeline"""
    logger.info("Starting 4Runr lead generation pipeline")
    
    # Check if the leads file exists before starting
    check_leads_file()
    
    # Run the scraper agent
    if not run_agent("scraper"):
        logger.error("Scraper agent failed, stopping pipeline")
        return
    
    # Check the leads file after scraping
    logger.info("Checking leads file after scraping:")
    check_leads_file()
    
    # Wait a moment before running the enricher
    time.sleep(2)
    
    # Run the enricher agent
    if not run_agent("enricher"):
        logger.error("Enricher agent failed, stopping pipeline")
        return
    
    # Check the leads file after enrichment
    logger.info("Checking leads file after enrichment:")
    check_leads_file()
    
    # Wait a moment before running the engager
    time.sleep(2)
    
    # Run the engager agent
    if not run_agent("engager"):
        logger.error("Engager agent failed, stopping pipeline")
        return
    
    # Check the leads file after engagement
    logger.info("Checking leads file after engagement:")
    check_leads_file()
    
    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()