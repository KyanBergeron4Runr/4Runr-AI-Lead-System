#!/usr/bin/env python3
"""
Retry Failed Airtable Syncs

This script retries sending failed leads to Airtable.
"""

import os
import sys
import logging
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('retry-failed-syncs')

def main():
    """Main function to retry failed Airtable syncs"""
    logger.info("Starting retry of failed Airtable syncs...")
    
    # Add the parent directory to the Python path
    script_dir = pathlib.Path(__file__).parent.absolute()
    root_dir = script_dir.parent
    sys.path.append(str(root_dir))
    
    try:
        # Import the Airtable client
        from shared.airtable_client import retry_failed_leads
        
        # Retry failed leads
        retried = retry_failed_leads()
        
        if retried > 0:
            logger.info(f"Successfully retried {retried} failed Airtable syncs")
        else:
            logger.info("No failed Airtable syncs to retry")
        
        return 0
    except Exception as e:
        logger.error(f"Error retrying failed Airtable syncs: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())