#!/usr/bin/env python3
"""
Health Check Script

This script checks the health of the 4Runr Multi-Agent System.
It verifies that all containers are running and that the shared directory is accessible.
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('health-check')

def check_docker_containers():
    """Check that all required containers are running"""
    logger.info("Checking Docker containers...")
    
    required_containers = [
        "4runr-scraper",
        "4runr-enricher",
        "4runr-engager"
    ]
    
    try:
        # Get the list of running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        running_containers = result.stdout.strip().split('\n')
        
        # Check that all required containers are running
        missing_containers = []
        for container in required_containers:
            if container not in running_containers:
                missing_containers.append(container)
        
        if missing_containers:
            logger.error(f"Missing containers: {', '.join(missing_containers)}")
            return False
        
        logger.info("All required containers are running")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking Docker containers: {e}")
        return False

def check_shared_directory():
    """Check that the shared directory is accessible and contains the expected files"""
    logger.info("Checking shared directory...")
    
    # Check that the shared directory exists
    if not os.path.isdir("shared"):
        logger.error("Shared directory not found")
        return False
    
    # Check that the leads.json file exists
    leads_file = os.path.join("shared", "leads.json")
    if not os.path.isfile(leads_file):
        logger.warning("leads.json file not found")
        # This is not a critical error, as the file might not exist yet
    else:
        logger.info(f"Found leads.json file: {leads_file}")
    
    # Check that the control.json file exists
    control_file = os.path.join("shared", "control.json")
    if not os.path.isfile(control_file):
        logger.warning("control.json file not found")
        # This is not a critical error, as the file might not exist yet
    else:
        logger.info(f"Found control.json file: {control_file}")
    
    return True

def check_logs():
    """Check that log files are being written to"""
    logger.info("Checking log files...")
    
    # Check that the logs directory exists
    if not os.path.isdir("logs"):
        logger.error("Logs directory not found")
        return False
    
    # Check that log files exist and are recent
    log_files = [f for f in os.listdir("logs") if f.endswith(".log")]
    if not log_files:
        logger.warning("No log files found")
        # This is not a critical error, as logs might not have been generated yet
        return True
    
    # Check that at least one log file is recent (within the last 24 hours)
    recent_logs = False
    for log_file in log_files:
        log_path = os.path.join("logs", log_file)
        if os.path.getmtime(log_path) > (datetime.now() - timedelta(hours=24)).timestamp():
            recent_logs = True
            break
    
    if not recent_logs:
        logger.warning("No recent log files found (within the last 24 hours)")
        # This is not a critical error, as the system might not have run recently
    
    logger.info(f"Found {len(log_files)} log files")
    return True

def check_airtable_connection():
    """Check that the Airtable connection is working"""
    logger.info("Checking Airtable connection...")
    
    try:
        # Import the Airtable client
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from shared.airtable_client import push_lead_to_airtable
        
        # Create a test lead
        test_lead = {
            "name": "Health Check",
            "linkedin_url": "https://linkedin.com/in/healthcheck",
            "company": "4Runr",
            "title": "Health Check",
            "email": "health@check.com",
            "status": "test"
        }
        
        # Try to push the lead to Airtable
        result = push_lead_to_airtable(test_lead)
        
        if result:
            logger.info("Airtable connection is working")
            return True
        else:
            logger.warning("Airtable connection test failed")
            return False
    except Exception as e:
        logger.error(f"Error checking Airtable connection: {e}")
        return False

def main():
    """Main function to run the health check"""
    logger.info("Starting health check...")
    
    # Check Docker containers
    containers_ok = check_docker_containers()
    
    # Check shared directory
    shared_ok = check_shared_directory()
    
    # Check logs
    logs_ok = check_logs()
    
    # Check Airtable connection
    airtable_ok = check_airtable_connection()
    
    # Print summary
    logger.info("\n=== HEALTH CHECK SUMMARY ===")
    logger.info(f"Docker containers: {'✅ OK' if containers_ok else '❌ FAIL'}")
    logger.info(f"Shared directory: {'✅ OK' if shared_ok else '❌ FAIL'}")
    logger.info(f"Logs: {'✅ OK' if logs_ok else '❌ FAIL'}")
    logger.info(f"Airtable connection: {'✅ OK' if airtable_ok else '⚠️ WARNING'}")
    
    # Determine overall status
    if containers_ok and shared_ok and logs_ok:
        logger.info("\n✅ SYSTEM IS HEALTHY")
        return 0
    else:
        logger.error("\n❌ SYSTEM HAS ISSUES")
        return 1

if __name__ == "__main__":
    sys.exit(main())