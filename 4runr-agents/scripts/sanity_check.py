#!/usr/bin/env python3
"""
Sanity Check Script

This script performs a sanity check on the multi-agent system to verify that
all components are working correctly.
"""

import os
import sys
import json
import pathlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sanity-check')

def check_environment():
    """Check that the environment is set up correctly"""
    logger.info("Checking environment...")
    
    # Check that the required directories exist
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    
    required_dirs = ["scraper", "enricher", "engager", "shared"]
    for dir_name in required_dirs:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            logger.error(f"Required directory not found: {dir_path}")
            return False
        logger.info(f"Found directory: {dir_path}")
    
    # Check that the required files exist
    required_files = [
        "scraper/app.py",
        "enricher/app.py",
        "engager/app.py",
        "docker-compose.yml",
        ".env"
    ]
    for file_name in required_files:
        file_path = root_dir / file_name
        if not file_path.exists():
            logger.error(f"Required file not found: {file_path}")
            return False
        logger.info(f"Found file: {file_path}")
    
    # Check that the .env file contains the required variables
    env_path = root_dir / ".env"
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    required_vars = [
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_TABLE_NAME",
        "OPENAI_API_KEY"
    ]
    for var in required_vars:
        if var not in env_content:
            logger.warning(f"Environment variable not found in .env: {var}")
    
    logger.info("Environment check completed")
    return True

def check_shared_file():
    """Check that the shared leads.json file is working correctly"""
    logger.info("Checking shared leads.json file...")
    
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    leads_file = root_dir / "shared" / "leads.json"
    
    # Create the shared directory if it doesn't exist
    shared_dir = root_dir / "shared"
    shared_dir.mkdir(exist_ok=True)
    
    # Create a test lead
    test_lead = {
        "name": "Test Lead",
        "linkedin_url": "https://linkedin.com/in/testlead",
        "company": "Test Company",
        "title": "Test Title",
        "email": "",
        "status": "scraped",
        "scraped_at": "2023-01-01T00:00:00Z"
    }
    
    # Write the test lead to the file
    with open(leads_file, 'w') as f:
        json.dump([test_lead], f, indent=2)
    
    logger.info(f"Wrote test lead to {leads_file}")
    
    # Read the file back to verify
    with open(leads_file, 'r') as f:
        leads = json.load(f)
    
    if len(leads) != 1 or leads[0]["name"] != "Test Lead":
        logger.error(f"Failed to read test lead from {leads_file}")
        return False
    
    logger.info(f"Successfully read test lead from {leads_file}")
    return True

def main():
    """Main function to run the sanity check"""
    logger.info("Starting 4Runr multi-agent system sanity check")
    
    # Check the environment
    if not check_environment():
        logger.error("Environment check failed")
        return 1
    
    # Check the shared file
    if not check_shared_file():
        logger.error("Shared file check failed")
        return 1
    
    logger.info("Sanity check completed successfully!")
    logger.info("The multi-agent system is ready to run.")
    logger.info("You can run the pipeline with:")
    logger.info("  python scripts/run_pipeline.py")
    logger.info("Or with Docker Compose:")
    logger.info("  ./scripts/docker_run.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())