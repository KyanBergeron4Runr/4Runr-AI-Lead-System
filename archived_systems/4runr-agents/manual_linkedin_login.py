#!/usr/bin/env python3
"""
Manual LinkedIn Login Helper

Opens LinkedIn login in a visible browser and waits for you to complete
any challenges (like picture orientation tests) manually
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
logger = logging.getLogger('manual-login')

async def manual_login_helper():
    """Help user complete LinkedIn login manually"""
    scraper = None
    
    try:
        logger.info("🔐 Manual LinkedIn Login Helper")
        logger.info("=" * 50)
        logger.info(f"📧 Account: {os.getenv('LINKEDIN_EMAIL')}")
        logger.info("🖥️  Browser will open in visible mode")
        logger.info("👤 You can complete any challenges manually")
        
        scraper = MontrealCEOScraper()
        
        # Force non-headless mode
        scraper.headless = False
        
        # Start browser
        await scraper.start_browser()
        
        # Navigate to LinkedIn login
        logger.info("🌐 Navigating to LinkedIn login page...")
        await scraper.page.goto('https://www.linkedin.com/login')
        
        # Fill in credentials
        logger.info("📝 Filling in credentials...")
        await scraper.page.wait_for_selector('#username', timeout=10000)
        await scraper.page.fill('#username', scraper.email)
        await scraper.page.fill('#password', scraper.password)
        
        logger.info("🖱️  Clicking login button...")
        await scraper.page.click('button[type="submit"]')
        
        # Wait and check for challenges
        await asyncio.sleep(3)
        
        current_url = scraper.page.url
        logger.info(f"📍 Current URL: {current_url}")
        
        if 'challenge' in current_url or 'checkpoint' in current_url:
            logger.info("🧩 CHALLENGE DETECTED!")
            logger.info("=" * 50)
            logger.info("🎯 ACTION REQUIRED:")
            logger.info("   1. Look at the browser window")
            logger.info("   2. Complete the challenge (e.g., select the right-side-up picture)")
            logger.info("   3. Click submit/continue")
            logger.info("   4. Wait for the page to load")
            logger.info("=" * 50)
            
            # Wait for user to complete challenge
            logger.info("⏳ Waiting for you to complete the challenge...")
            logger.info("   (Browser will stay open for 5 minutes)")
            
            # Check every 10 seconds if challenge is completed
            for i in range(30):  # 5 minutes total
                await asyncio.sleep(10)
                current_url = scraper.page.url
                
                if 'feed' in current_url or 'mynetwork' in current_url:
                    logger.info("✅ Challenge completed! Successfully logged in!")
                    break
                elif 'challenge' not in current_url and 'checkpoint' not in current_url:
                    logger.info("✅ Challenge page cleared!")
                    break
                else:
                    logger.info(f"⏳ Still on challenge page... ({i+1}/30 checks)")
            
            # Final check
            current_url = scraper.page.url
            if 'feed' in current_url or 'mynetwork' in current_url:
                logger.info("🎉 LOGIN SUCCESSFUL!")
                
                # Save cookies for future use
                await scraper.save_cookies()
                logger.info("🍪 Cookies saved for future sessions")
                
                # Test navigation
                logger.info("🧪 Testing navigation to search page...")
                await scraper.page.goto('https://www.linkedin.com/search/results/people/?keywords=CEO&geoUrn=%5B%22101449429%22%5D')
                await asyncio.sleep(3)
                
                if 'search' in scraper.page.url:
                    logger.info("✅ Search page accessible - ready for scraping!")
                else:
                    logger.warning("⚠️ Search page may not be accessible")
                
                # Keep browser open for a moment
                logger.info("🔍 Keeping browser open for 30 seconds so you can verify...")
                await asyncio.sleep(30)
                
                return True
            else:
                logger.error("❌ Challenge not completed or login failed")
                logger.info("🔍 Keeping browser open for 60 seconds so you can try again...")
                await asyncio.sleep(60)
                return False
        
        elif 'feed' in current_url or 'mynetwork' in current_url:
            logger.info("✅ No challenge - login successful!")
            await scraper.save_cookies()
            logger.info("🍪 Cookies saved for future sessions")
            
            # Keep browser open for verification
            logger.info("🔍 Keeping browser open for 30 seconds so you can verify...")
            await asyncio.sleep(30)
            
            return True
        
        else:
            logger.error("❌ Unexpected page after login")
            logger.info(f"📍 Current URL: {current_url}")
            logger.info("🔍 Keeping browser open for 60 seconds so you can investigate...")
            await asyncio.sleep(60)
            return False
        
    except Exception as e:
        logger.error(f"❌ Error during manual login: {str(e)}")
        return False
        
    finally:
        if scraper:
            await scraper.close()

async def main():
    """Main entry point"""
    # Load environment
    load_dotenv()
    
    logger.info("🚀 Starting Manual LinkedIn Login Helper")
    logger.info("📋 This tool will help you complete LinkedIn challenges manually")
    
    success = await manual_login_helper()
    
    if success:
        logger.info("✅ Manual login completed successfully!")
        logger.info("🚀 You can now run the production pipeline")
    else:
        logger.error("❌ Manual login failed")
        logger.info("💡 Try running this tool again")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)