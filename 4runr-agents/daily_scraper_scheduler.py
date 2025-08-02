#!/usr/bin/env python3
"""
Daily Scraper Scheduler
Runs the scraper once per day at a specified time
"""

import os
import sys
import time
import logging
import schedule
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('daily-scraper-scheduler')

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

def run_daily_scraping():
    """Run the daily scraping process"""
    try:
        logger.info("🚀 Starting daily scraping process...")
        
        # Import and run the scraper
        from scraper.app import main as scraper_main
        
        # Set environment to run once
        os.environ['RUN_ONCE'] = 'true'
        
        # Run the scraper
        asyncio.run(scraper_main())
        
        logger.info("✅ Daily scraping completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Daily scraping failed: {str(e)}")

def run_daily_pipeline():
    """Run the complete daily pipeline: scrape -> enrich -> sync to Airtable"""
    try:
        logger.info("🚀 Starting daily pipeline: Scrape -> Enrich -> Airtable")
        
        # Step 1: Scrape leads
        logger.info("📋 Step 1: Scraping leads...")
        run_daily_scraping()
        
        # Wait a moment for files to be written
        time.sleep(5)
        
        # Step 2: Enrich leads
        logger.info("💎 Step 2: Enriching leads...")
        try:
            from enrich_scraped_leads import main as enricher_main
            enricher_main()
        except Exception as e:
            logger.error(f"❌ Enrichment failed: {str(e)}")
        
        # Step 3: Sync to Airtable
        logger.info("📊 Step 3: Syncing to Airtable...")
        try:
            from sync_fresh_leads_only import sync_fresh_leads
            sync_fresh_leads()
        except Exception as e:
            logger.error(f"❌ Airtable sync failed: {str(e)}")
        
        # Step 4: Send outreach emails
        logger.info("📧 Step 4: Sending outreach emails...")
        try:
            from outreach_agent import OutreachAgent
            agent = OutreachAgent()
            agent.run_outreach_campaign(max_emails=3)  # Send to 3 leads per day
        except Exception as e:
            logger.error(f"❌ Outreach failed: {str(e)}")
        
        logger.info("✅ Daily pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Daily pipeline failed: {str(e)}")

def schedule_daily_scraping():
    """Schedule daily scraping at specified time"""
    
    # Get schedule time from environment
    scrape_time = os.getenv('DAILY_SCRAPE_TIME', '09:00')
    timezone = os.getenv('DAILY_SCRAPE_TIMEZONE', 'America/Montreal')
    
    logger.info(f"📅 Scheduling daily scraping at {scrape_time} ({timezone})")
    
    # Schedule the daily pipeline
    schedule.every().day.at(scrape_time).do(run_daily_pipeline)
    
    logger.info("⏰ Daily scraper scheduler started")
    logger.info(f"🎯 Next scrape scheduled for: {scrape_time}")
    
    # Run immediately for testing
    logger.info("🚀 Running pipeline immediately for testing...")
    run_daily_pipeline()
    
    # Keep the scheduler running
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

def main():
    """Main function"""
    logger.info("🕐 Daily Scraper Scheduler starting...")
    
    # Check required environment variables
    required_vars = ['SERPAPI_KEY', 'AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    # Start the scheduler
    schedule_daily_scraping()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())