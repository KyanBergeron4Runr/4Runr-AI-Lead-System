#!/usr/bin/env python3
"""
Daily Enricher Scheduler
Sets up automated daily enrichment with advanced scheduling
"""

import schedule
import time
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_enricher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enricher-scheduler')

def run_daily_enrichment():
    """Run the daily enrichment process"""
    logger.info("🚀 Starting scheduled daily enrichment...")
    
    try:
        # Run the daily enricher agent
        script_path = Path(__file__).parent / "daily_enricher_agent.py"
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        if result.returncode == 0:
            logger.info("✅ Daily enrichment completed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Daily enrichment failed with code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Daily enrichment timed out after 1 hour")
    except Exception as e:
        logger.error(f"❌ Error running daily enrichment: {str(e)}")

def setup_schedule():
    """Set up the daily enrichment schedule"""
    # Schedule daily enrichment at 9:00 AM
    schedule.every().day.at("09:00").do(run_daily_enrichment)
    
    # Alternative: Schedule every 24 hours from now
    # schedule.every(24).hours.do(run_daily_enrichment)
    
    logger.info("📅 Daily enrichment scheduled for 9:00 AM every day")
    logger.info("🔄 Scheduler is now running...")

def main():
    """Main scheduler loop"""
    logger.info("🚀 Starting Daily Enricher Scheduler...")
    
    setup_schedule()
    
    # Run the scheduler
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("⏹️ Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Scheduler error: {str(e)}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    main()