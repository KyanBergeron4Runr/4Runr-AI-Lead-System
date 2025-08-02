#!/usr/bin/env python3
"""
Test LinkedIn Login

Simple test to check if we can login to LinkedIn with the new account
"""

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add scraper to path
import sys
sys.path.append(str(Path(__file__).parent / 'scraper'))

from montreal_ceo_scraper_enhanced import MontrealCEOScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('login-test')

async def test_login():
    """Test LinkedIn login with new account"""
    scraper = None
    
    try:
        logger.info("🧪 Testing LinkedIn login with new account")
        logger.info(f"📧 Account: {os.getenv('LINKEDIN_EMAIL')}")
        
        scraper = MontrealCEOScraper()
        
        # Start browser (non-headless so we can see what happens)
        await scraper.start_browser()
        
        # Attempt login
        logger.info("🔐 Attempting login...")
        login_success = await scraper.login()
        
        if login_success:
            logger.info("✅ Login successful!")
            
            # Try to navigate to a simple page
            await scraper.page.goto('https://www.linkedin.com/feed/')
            await asyncio.sleep(3)
            
            logger.info("✅ Successfully navigated to LinkedIn feed")
            
            # Keep browser open for a moment so you can see
            logger.info("🔍 Browser will stay open for 10 seconds so you can verify...")
            await asyncio.sleep(10)
            
        else:
            logger.error("❌ Login failed")
            
            # Keep browser open so you can see the challenge
            logger.info("🔍 Browser will stay open for 30 seconds so you can see the issue...")
            await asyncio.sleep(30)
        
        return login_success
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False
        
    finally:
        if scraper:
            await scraper.close()

if __name__ == "__main__":
    # Load environment
    load_dotenv()
    
    success = asyncio.run(test_login())
    
    if success:
        print("\n✅ Login test passed - account is working!")
    else:
        print("\n❌ Login test failed - account may need manual verification")
    
    exit(0 if success else 1)