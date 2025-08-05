#!/usr/bin/env python3
"""
LinkedIn Profile Verifier Agent

This agent validates LinkedIn URLs from raw_leads.json to ensure they are accessible
and real before passing to enrichment. This prevents fake data from entering the pipeline.

Pipeline: raw_leads.json → VERIFIER → verified_leads.json
"""

import os
import json
import uuid
import logging
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin-verifier')

class LinkedInVerifier:
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        
        # File paths
        self.shared_dir = Path(__file__).parent.parent / 'shared'
        self.raw_leads_file = self.shared_dir / 'raw_leads.json'
        self.verified_leads_file = self.shared_dir / 'verified_leads.json'
        self.dropped_leads_file = self.shared_dir / 'dropped_leads.json'
        
        # Ensure shared directory exists
        self.shared_dir.mkdir(exist_ok=True)
        
    async def start_browser(self):
        """Start browser for LinkedIn URL validation"""
        try:
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=os.getenv('HEADLESS', 'true').lower() == 'true',
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(15000)
            
            logger.info("✅ Browser started for LinkedIn verification")
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser: {str(e)}")
            raise
    
    async def verify_linkedin_url(self, url: str, lead_name: str = "Unknown") -> dict:
        """
        Verify that a LinkedIn URL is accessible and returns a real profile
        
        Args:
            url: LinkedIn profile URL to verify
            lead_name: Name of the lead for logging
            
        Returns:
            dict: Verification result with status and details
        """
        verification_result = {
            'url': url,
            'verified': False,
            'status_code': None,
            'error': None,
            'verified_at': datetime.now().isoformat(),
            'method': 'playwright'
        }
        
        try:
            logger.info(f"🔍 Verifying LinkedIn URL for {lead_name}: {url}")
            
            # Navigate to the LinkedIn profile
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=15000)
            
            if not response:
                verification_result['error'] = 'No response received'
                logger.warning(f"⚠️ No response for {lead_name}: {url}")
                return verification_result
            
            verification_result['status_code'] = response.status
            
            # Check HTTP status
            if response.status != 200:
                verification_result['error'] = f'HTTP {response.status}'
                logger.warning(f"⚠️ HTTP {response.status} for {lead_name}: {url}")
                return verification_result
            
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Check if it's actually a LinkedIn profile page with multiple validation methods
            profile_indicators = [
                # Primary profile indicators
                '.pv-text-details__left-panel',  # Main profile section
                '.ph5.pb5',  # Alternative profile container
                '[data-test-id="profile-top-card"]',  # Profile top card
                '.pv-top-card',  # Profile top card alternative
                
                # Secondary profile indicators
                '.profile-photo-edit__preview',  # Profile photo section
                '.pv-entity__photo',  # Profile entity photo
                '.pv-top-card-profile-picture',  # Profile picture
                '.presence-entity__image',  # Presence image
                
                # Content indicators
                '.pv-profile-section',  # Profile sections
                '.experience-section',  # Experience section
                '.education-section',  # Education section
                '.pv-about-section',  # About section
                
                # Modern LinkedIn selectors
                '.artdeco-card.pv-profile-card',  # Modern profile card
                '.scaffold-layout__main',  # Main layout
                '.profile-rail-card'  # Profile rail
            ]
            
            profile_found = False
            matched_selector = None
            
            # Try multiple selectors for better reliability
            for selector in profile_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    profile_found = True
                    matched_selector = selector
                    logger.info(f"✅ Profile verified for {lead_name} using selector: {selector}")
                    break
                except PlaywrightTimeoutError:
                    continue
            
            # Additional content-based validation
            if not profile_found:
                try:
                    # Check for profile-specific text content
                    page_content = await self.page.content()
                    profile_keywords = [
                        'linkedin.com/in/',
                        'professional profile',
                        'experience at',
                        'connections',
                        'activity',
                        'about this profile'
                    ]
                    
                    keyword_matches = sum(1 for keyword in profile_keywords if keyword.lower() in page_content.lower())
                    
                    if keyword_matches >= 2:
                        profile_found = True
                        matched_selector = f"content_keywords_{keyword_matches}"
                        logger.info(f"✅ Profile verified for {lead_name} using content analysis ({keyword_matches} keywords)")
                    
                except Exception as e:
                    logger.warning(f"Content analysis failed for {lead_name}: {str(e)}")
            
            # Store validation details
            verification_result['validation_method'] = matched_selector if profile_found else 'none'
            verification_result['profile_indicators_checked'] = len(profile_indicators)
            
            if profile_found:
                verification_result['verified'] = True
                logger.info(f"✅ LinkedIn profile verified for {lead_name}")
            else:
                # Check if we hit a LinkedIn login wall or error page
                page_content = await self.page.content()
                
                if 'authwall' in page_content.lower() or 'sign in' in page_content.lower():
                    verification_result['error'] = 'LinkedIn auth wall encountered'
                    logger.warning(f"⚠️ Auth wall for {lead_name}: {url}")
                elif 'not found' in page_content.lower() or '404' in page_content:
                    verification_result['error'] = 'Profile not found'
                    logger.warning(f"⚠️ Profile not found for {lead_name}: {url}")
                else:
                    verification_result['error'] = 'Profile page structure not recognized'
                    logger.warning(f"⚠️ Unrecognized page structure for {lead_name}: {url}")
            
            return verification_result
            
        except PlaywrightTimeoutError:
            verification_result['error'] = 'Page load timeout'
            logger.warning(f"⚠️ Timeout loading profile for {lead_name}: {url}")
            return verification_result
            
        except Exception as e:
            verification_result['error'] = str(e)
            logger.error(f"❌ Error verifying {lead_name}: {str(e)}")
            return verification_result
    
    def load_raw_leads(self) -> list:
        """Load real people from raw_leads.json"""
        try:
            if not self.raw_leads_file.exists():
                logger.warning(f"⚠️ Raw leads file not found: {self.raw_leads_file}")
                return []
            
            with open(self.raw_leads_file, 'r', encoding='utf-8') as f:
                leads = json.load(f)
            
            logger.info(f"📥 Loaded {len(leads)} real people from raw_leads.json")
            return leads
            
        except Exception as e:
            logger.error(f"❌ Failed to load raw leads: {str(e)}")
            return []
    
    def save_verified_leads(self, leads: list):
        """Save verified leads to verified_leads.json"""
        try:
            with open(self.verified_leads_file, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved {len(leads)} verified leads to verified_leads.json")
            
        except Exception as e:
            logger.error(f"❌ Failed to save verified leads: {str(e)}")
    
    def save_dropped_leads(self, leads: list):
        """Save dropped leads to dropped_leads.json for analysis"""
        try:
            # Load existing dropped leads
            existing_dropped = []
            if self.dropped_leads_file.exists():
                with open(self.dropped_leads_file, 'r', encoding='utf-8') as f:
                    existing_dropped = json.load(f)
            
            # Add new dropped leads
            existing_dropped.extend(leads)
            
            with open(self.dropped_leads_file, 'w', encoding='utf-8') as f:
                json.dump(existing_dropped, f, indent=2, ensure_ascii=False)
            
            logger.info(f"🗑️ Saved {len(leads)} dropped leads to dropped_leads.json")
            
        except Exception as e:
            logger.error(f"❌ Failed to save dropped leads: {str(e)}")
    
    async def verify_leads(self) -> dict:
        """
        Main verification process
        
        Returns:
            dict: Summary of verification results
        """
        try:
            # Load raw leads
            raw_leads = self.load_raw_leads()
            
            if not raw_leads:
                logger.warning("⚠️ No raw leads to verify")
                return {
                    'total_leads': 0,
                    'verified_leads': 0,
                    'dropped_leads': 0,
                    'verification_rate': 0.0
                }
            
            # Start browser for verification
            await self.start_browser()
            
            verified_leads = []
            dropped_leads = []
            
            logger.info(f"🔍 Starting verification of {len(raw_leads)} leads")
            
            for i, lead in enumerate(raw_leads, 1):
                try:
                    linkedin_url = lead.get('linkedin_url', '')
                    lead_name = lead.get('full_name', f'Person {i}')
                    lead_uuid = lead.get('uuid', str(uuid.uuid4()))
                    
                    if not linkedin_url:
                        logger.warning(f"⚠️ No LinkedIn URL for {lead_name}, dropping person")
                        lead['dropped_reason'] = 'No LinkedIn URL'
                        lead['dropped_at'] = datetime.now().isoformat()
                        dropped_leads.append(lead)
                        continue
                    
                    # Verify the LinkedIn URL
                    verification_result = await self.verify_linkedin_url(linkedin_url, lead_name)
                    
                    # Update lead with verification results
                    lead['verification'] = verification_result
                    lead['verified'] = verification_result['verified']
                    lead['verified_at'] = verification_result['verified_at']
                    
                    if verification_result['verified']:
                        verified_leads.append(lead)
                        logger.info(f"✅ Person {i}/{len(raw_leads)}: {lead_name} - VERIFIED")
                    else:
                        lead['dropped_reason'] = f"LinkedIn verification failed: {verification_result.get('error', 'Unknown error')}"
                        lead['dropped_at'] = datetime.now().isoformat()
                        dropped_leads.append(lead)
                        logger.warning(f"❌ Person {i}/{len(raw_leads)}: {lead_name} - DROPPED ({verification_result.get('error', 'Unknown error')})")
                    
                    # Small delay between verifications to be respectful
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing person {i}: {str(e)}")
                    lead['dropped_reason'] = f"Processing error: {str(e)}"
                    lead['dropped_at'] = datetime.now().isoformat()
                    dropped_leads.append(lead)
            
            # Save results
            self.save_verified_leads(verified_leads)
            self.save_dropped_leads(dropped_leads)
            
            # Calculate verification rate
            verification_rate = (len(verified_leads) / len(raw_leads)) * 100 if raw_leads else 0
            
            # Summary
            summary = {
                'total_leads': len(raw_leads),
                'verified_leads': len(verified_leads),
                'dropped_leads': len(dropped_leads),
                'verification_rate': round(verification_rate, 2)
            }
            
            logger.info(f"🎯 Verification Summary:")
            logger.info(f"   Total leads processed: {summary['total_leads']}")
            logger.info(f"   Verified leads: {summary['verified_leads']}")
            logger.info(f"   Dropped leads: {summary['dropped_leads']}")
            logger.info(f"   Verification rate: {summary['verification_rate']}%")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Verification process failed: {str(e)}")
            return {
                'total_leads': 0,
                'verified_leads': 0,
                'dropped_leads': 0,
                'verification_rate': 0.0,
                'error': str(e)
            }
        
        finally:
            if self.browser:
                await self.browser.close()
                logger.info("🔒 Browser closed")

async def main():
    """Main entry point for the verifier agent"""
    logger.info("🚀 Starting LinkedIn Profile Verifier Agent")
    
    verifier = LinkedInVerifier()
    summary = await verifier.verify_leads()
    
    if 'error' in summary:
        logger.error(f"❌ Verification failed: {summary['error']}")
        return False
    
    logger.info("✅ LinkedIn verification completed successfully")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)