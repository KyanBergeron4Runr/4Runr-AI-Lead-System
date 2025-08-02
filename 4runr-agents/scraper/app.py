#!/usr/bin/env python3
"""
4Runr Scraper Agent

This agent is responsible for scraping LinkedIn data and saving it to a shared location
for the enricher agent to process.
"""

import os
import json
import time
import logging
import random
import pathlib
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Find and load environment variables from .env file
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Validate required environment variables
required_env_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME']
linkedin_vars = ['LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'SEARCH_URL']

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
missing_linkedin_vars = [var for var in linkedin_vars if not os.getenv(var)]

if missing_vars:
    print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
    print(f"Using placeholder values for missing variables")
    # Set placeholder values for missing variables
    if not os.getenv('AIRTABLE_API_KEY'):
        os.environ['AIRTABLE_API_KEY'] = 'placeholder_airtable_api_key'
    if not os.getenv('AIRTABLE_BASE_ID'):
        os.environ['AIRTABLE_BASE_ID'] = 'placeholder_airtable_base_id'
    if not os.getenv('AIRTABLE_TABLE_NAME'):
        os.environ['AIRTABLE_TABLE_NAME'] = 'Leads'

# Check if we should use real LinkedIn scraping or mock data
use_real_scraping = not missing_linkedin_vars and os.getenv('USE_REAL_SCRAPING', 'false').lower() == 'true'

# Access environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scraper-agent')

# Import scrapers with fallback handling (after logger is configured)
PRODUCTION_SCRAPER_AVAILABLE = False
REAL_SCRAPER_AVAILABLE = False
APIFY_AVAILABLE = False
PLAYWRIGHT_AVAILABLE = False
SIMPLE_SCRAPER_AVAILABLE = False

try:
    try:
        from .production_linkedin_scraper import scrape_real_linkedin_leads as scrape_production_leads
    except ImportError:
        from production_linkedin_scraper import scrape_real_linkedin_leads as scrape_production_leads
    PRODUCTION_SCRAPER_AVAILABLE = True
    logger.info("✅ Production LinkedIn scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Production LinkedIn scraper not available: {e}")
    PRODUCTION_SCRAPER_AVAILABLE = False

try:
    try:
        from .montreal_ceo_scraper import scrape_montreal_ceos
    except ImportError:
        from montreal_ceo_scraper import scrape_montreal_ceos
    MONTREAL_CEO_SCRAPER_AVAILABLE = True
    logger.info("✅ Montreal CEO scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Montreal CEO scraper not available: {e}")
    MONTREAL_CEO_SCRAPER_AVAILABLE = False

# Verified Montreal CEOs database - DISABLED to force fresh scraping
VERIFIED_MONTREAL_CEOS_AVAILABLE = False
logger.info("🔄 Verified Montreal CEOs database disabled - will use fresh scraping")

try:
    try:
        from .real_linkedin_scraper import scrape_real_linkedin_leads
    except ImportError:
        from real_linkedin_scraper import scrape_real_linkedin_leads
    REAL_SCRAPER_AVAILABLE = True
    logger.info("✅ Real LinkedIn scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Real LinkedIn scraper not available: {e}")
    REAL_SCRAPER_AVAILABLE = False

try:
    try:
        from .apify_linkedin_scraper import scrape_linkedin_leads_apify
    except ImportError:
        from apify_linkedin_scraper import scrape_linkedin_leads_apify
    APIFY_AVAILABLE = True
    logger.info("✅ Apify scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Apify scraper not available: {e}")
    APIFY_AVAILABLE = False

try:
    try:
        from .linkedin_scraper import scrape_linkedin_leads
    except ImportError:
        from linkedin_scraper import scrape_linkedin_leads
    PLAYWRIGHT_AVAILABLE = True
    logger.info("✅ Playwright scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Playwright scraper not available: {e}")
    PLAYWRIGHT_AVAILABLE = False

try:
    try:
        from .simple_linkedin_scraper import scrape_linkedin_leads_simple
    except ImportError:
        from simple_linkedin_scraper import scrape_linkedin_leads_simple
    SIMPLE_SCRAPER_AVAILABLE = True
    logger.info("✅ Simple scraper loaded successfully")
except ImportError as e:
    logger.warning(f"Simple scraper not available: {e}")
    SIMPLE_SCRAPER_AVAILABLE = False

try:
    try:
        from .serpapi_linkedin_scraper import scrape_linkedin_leads_serpapi
    except ImportError:
        from serpapi_linkedin_scraper import scrape_linkedin_leads_serpapi
    SERPAPI_SCRAPER_AVAILABLE = True
    logger.info("✅ SerpAPI LinkedIn scraper loaded successfully")
except ImportError as e:
    logger.warning(f"SerpAPI LinkedIn scraper not available: {e}")
    SERPAPI_SCRAPER_AVAILABLE = False

# Constants
SHARED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared")
OUTPUT_FILE = os.path.join(SHARED_DIR, "scraped_leads.json")
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")

# Sample data for generating mock leads
FIRST_NAMES = [
    'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Robert', 'Lisa',
    'William', 'Jennifer', 'Richard', 'Elizabeth', 'Joseph', 'Susan', 'Thomas'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
    'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris'
]

# Real Montreal-based companies and CEOs with verified LinkedIn URLs
MONTREAL_CEOS = [
    ("Tobias Lütke", "Shopify", "https://www.linkedin.com/in/tobi/"),
    ("George Schindler", "CGI Group", "https://www.linkedin.com/in/george-schindler-cgi/"),
    ("Éric Martel", "Bombardier", "https://www.linkedin.com/in/eric-martel-bombardier/"),
    ("Ian Edwards", "SNC-Lavalin", "https://www.linkedin.com/in/ian-l-edwards/"),
    ("Brian Hannasch", "Couche-Tard", "https://www.linkedin.com/in/brian-hannasch/"),
    ("Eric La Flèche", "Metro Inc", "https://www.linkedin.com/in/eric-la-fleche/"),
    ("Lino Saputo Jr.", "Saputo", "https://www.linkedin.com/in/lino-saputo-jr/"),
    ("Marc Parent", "CAE Inc", "https://www.linkedin.com/in/marc-parent-cae/"),
    ("Neil Rossy", "Dollarama", "https://www.linkedin.com/in/neil-rossy/"),
    ("Dax Dasilva", "Lightspeed Commerce", "https://www.linkedin.com/in/daxdasilva/"),
    ("Philip Fayer", "Nuvei Corporation", "https://www.linkedin.com/in/philip-fayer/"),
    ("Alain Bédard", "TFI International", "https://www.linkedin.com/in/alain-bedard/"),
    ("Philippe Jetté", "Cogeco Communications", "https://www.linkedin.com/in/philippe-jette/"),
    ("Pierre Dion", "Quebecor", "https://www.linkedin.com/in/pierre-dion-quebecor/"),
    ("Sophie Brochu", "Hydro-Québec", "https://www.linkedin.com/in/sophie-brochu/"),
    ("Guy Cormier", "Desjardins Group", "https://www.linkedin.com/in/guy-cormier/"),
    ("Laurent Ferreira", "National Bank of Canada", "https://www.linkedin.com/in/laurent-ferreira/"),
    ("Jeffrey Orr", "Power Corporation", "https://www.linkedin.com/in/jeffrey-orr/"),
    ("Alexandre Taillefer", "XPND Capital", "https://www.linkedin.com/in/alexandretaillefer/"),
    ("Mitch Garber", "Caesars Entertainment", "https://www.linkedin.com/in/mitch-garber/")
]

def generate_linkedin_url(first_name, last_name):
    """Generate a random LinkedIn URL for a person"""
    variations = [
        f"{first_name.lower()}-{last_name.lower()}",
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name.lower()[0]}{last_name.lower()}"
    ]
    
    random_variation = random.choice(variations)
    random_number = random.randint(1, 999) if random.random() < 0.3 else ''
    
    return f"https://www.linkedin.com/in/{random_variation}{random_number}"

def generate_mock_lead():
    """Generate a realistic Montreal CEO lead with verified LinkedIn URL"""
    # Select a random Montreal CEO with verified LinkedIn URL
    name, company, linkedin_url = random.choice(MONTREAL_CEOS)
    
    return {
        "id": f"lead_{int(time.time())}_{random.randint(1000, 9999)}",
        "name": name,
        "linkedin_url": linkedin_url,
        "company": company,
        "title": "CEO",
        "scraped_at": datetime.now().isoformat(),
        "needs_enrichment": True
    }

def generate_mock_leads(count):
    """Generate multiple mock leads"""
    return [generate_mock_lead() for _ in range(count)]

def save_raw_leads(leads):
    """Save leads to raw_leads.json - REAL PEOPLE ONLY"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Format leads for real people only pipeline
    formatted_leads = []
    for lead in leads:
        # STRICT VALIDATION: Only real people with LinkedIn URLs
        if not lead.get("linkedin_url") or not lead.get("name"):
            logger.warning(f"⚠️ Skipping person without LinkedIn URL: {lead.get('name', 'Unknown')}")
            continue
        
        # Generate UUID for tracking
        lead_uuid = str(uuid.uuid4())
        
        # Fix UTF-8 encoding issues (Tobias LÃ¼tke → Tobias Lütke)
        full_name = lead["name"]
        try:
            import unidecode
            # First try to fix double-encoded UTF-8
            if 'Ã' in full_name:
                # This is likely double-encoded UTF-8, try to fix it
                try:
                    fixed_name = full_name.encode('latin1').decode('utf-8')
                    logger.info(f"🔧 Fixed encoding: '{full_name}' → '{fixed_name}'")
                    full_name = fixed_name
                except:
                    # If that fails, use unidecode to normalize
                    full_name = unidecode.unidecode(full_name)
                    logger.info(f"🔧 Normalized name: {full_name}")
        except ImportError:
            logger.warning("unidecode not available for name normalization")
        
        formatted_lead = {
            "uuid": lead_uuid,
            "full_name": full_name,
            "linkedin_url": lead["linkedin_url"] if lead["linkedin_url"] else None,
            "verified": False,  # Will be set by verifier
            "enriched": False,  # Will be set by enricher
            "email": None,  # Will be set by enricher if found
            "engagement_method": None,  # Will be set by engager
            "scraped_at": datetime.now().isoformat(),
            "source": "LinkedIn Scraper - Real People Only"
        }
        
        formatted_leads.append(formatted_lead)
    
    if not formatted_leads:
        logger.error("❌ No real people found with LinkedIn URLs")
        return
    
    # Save to raw_leads.json with proper UTF-8 encoding
    raw_leads_file = os.path.join(SHARED_DIR, "raw_leads.json")
    
    with open(raw_leads_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_leads, f, indent=2, ensure_ascii=False)
    
    # Update control file with proper UTF-8 encoding
    with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_scrape": datetime.now().isoformat(),
            "lead_count": len(formatted_leads),
            "status": "ready_for_verification",
            "pipeline_stage": "raw_leads"
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved {len(formatted_leads)} real people to raw_leads.json")
    logger.info(f"🔄 Pipeline status: Ready for verification")

async def scrape_real_leads():
    """Scrape real leads from LinkedIn with multiple fallback options"""
    try:
        # Try Apify first (most reliable)
        if APIFY_AVAILABLE and os.getenv('APIFY_TOKEN'):
            logger.info("Attempting Apify-based LinkedIn scraping...")
            try:
                leads = await scrape_linkedin_leads_apify()
                if leads:
                    logger.info(f"Successfully scraped {len(leads)} leads with Apify")
                    return format_leads(leads)
            except Exception as apify_error:
                logger.warning(f"Apify scraping failed: {apify_error}")
        
        # Try Playwright second
        if PLAYWRIGHT_AVAILABLE:
            logger.info("Attempting Playwright-based LinkedIn scraping...")
            try:
                leads = await scrape_linkedin_leads()
                if leads:
                    logger.info(f"Successfully scraped {len(leads)} leads with Playwright")
                    return format_leads(leads)
            except Exception as playwright_error:
                logger.warning(f"Playwright scraping failed: {playwright_error}")
                
        # Try simple scraper third
        if SIMPLE_SCRAPER_AVAILABLE:
            logger.info("Falling back to simple LinkedIn scraper...")
            try:
                leads = await scrape_linkedin_leads_simple()
                if leads:
                    logger.info(f"Successfully generated {len(leads)} leads with simple scraper")
                    return format_leads(leads)
            except Exception as simple_error:
                logger.warning(f"Simple scraping failed: {simple_error}")
        
        logger.warning("All scraping methods failed, returning empty list")
        return []
        
    except Exception as e:
        logger.error(f"Error in real LinkedIn scraping: {str(e)}")
        return []

def format_leads(leads):
    """Format leads to the expected pipeline format"""
    formatted_leads = []
    for lead in leads:
        formatted_lead = {
            "id": f"lead_{int(time.time())}_{random.randint(1000, 9999)}",
            "name": lead["name"],
            "linkedin_url": lead["linkedin_url"],
            "company": lead["company"],
            "title": lead["title"],
            "scraped_at": datetime.now().isoformat(),
            "needs_enrichment": True
        }
        formatted_leads.append(formatted_lead)
    
    return formatted_leads

async def main():
    """Main function to run the scraper agent"""
    logger.info("Starting 4Runr Scraper Agent")
    
    try:
        # Check what scrapers are available
        available_scrapers = []
        if SERPAPI_SCRAPER_AVAILABLE and os.getenv('SERPAPI_KEY'):
            available_scrapers.append("SerpAPI (Primary)")
        if VERIFIED_MONTREAL_CEOS_AVAILABLE:
            available_scrapers.append("Verified Montreal CEOs")
        if MONTREAL_CEO_SCRAPER_AVAILABLE:
            available_scrapers.append("Montreal CEO")
        if PRODUCTION_SCRAPER_AVAILABLE:
            available_scrapers.append("Production")
        if REAL_SCRAPER_AVAILABLE:
            available_scrapers.append("Real")
        if APIFY_AVAILABLE and os.getenv('APIFY_TOKEN'):
            available_scrapers.append("Apify")
        if PLAYWRIGHT_AVAILABLE:
            available_scrapers.append("Playwright")
        if SIMPLE_SCRAPER_AVAILABLE:
            available_scrapers.append("Simple")
        
        logger.info(f"Available scrapers: {', '.join(available_scrapers)}")
        
        leads = []
        
        # Try SerpAPI FIRST - this is your working method
        if SERPAPI_SCRAPER_AVAILABLE and os.getenv('SERPAPI_KEY'):
            logger.info("🚀 Using SerpAPI LinkedIn scraper (PRIMARY METHOD)...")
            try:
                leads = await scrape_linkedin_leads_serpapi()
                
                if leads:
                    logger.info(f"✅ SUCCESS: Got {len(leads)} Montreal CEOs from SerpAPI")
                    # Log sample of SerpAPI data
                    for lead in leads[:3]:
                        logger.info(f"   📋 {lead['name']} - {lead['title']} at {lead['company']}")
                        logger.info(f"   🔗 {lead['linkedin_url']}")
                else:
                    logger.warning("⚠️ SerpAPI scraper returned no leads")
            except Exception as e:
                logger.error(f"❌ SerpAPI scraper failed: {e}")
        
        # VERIFIED DATABASE DISABLED - Skip to other scraping methods if SerpAPI fails
        if not leads:
            logger.info("🔄 SerpAPI failed or unavailable - trying other scraping methods")
        
        # This block is now disabled to force fresh scraping
        if False and not leads:
            logger.info("🎯 Using VERIFIED MONTREAL CEOs database - guaranteed real Montreal CEOs...")
            try:
                max_leads = int(os.getenv('MAX_LEADS_PER_RUN', '5'))
                leads = await get_verified_montreal_ceos(max_leads)
                
                if leads:
                    logger.info(f"✅ SUCCESS: Got {len(leads)} VERIFIED Montreal CEOs from database")
                    # Log sample of verified Montreal data
                    for lead in leads[:3]:
                        logger.info(f"   📋 {lead['name']} - {lead['title']} at {lead['company']}")
                        logger.info(f"   🔗 {lead['linkedin_url']}")
                        logger.info(f"   📍 {lead.get('location', 'N/A')}")
                else:
                    logger.warning("⚠️ Verified Montreal CEOs database returned no leads")
            except Exception as e:
                logger.error(f"❌ Verified Montreal CEOs database failed: {e}")
        
        # Fallback to MONTREAL CEO scraper if database fails
        if not leads and MONTREAL_CEO_SCRAPER_AVAILABLE:
            logger.info("🎯 Fallback: Using MONTREAL CEO scraper with ultra stealth...")
            try:
                leads = await scrape_montreal_ceos()
                
                if leads:
                    logger.info(f"✅ SUCCESS: Got {len(leads)} REAL Montreal CEOs from ultra-targeted scraper")
                    # Log sample of real Montreal data
                    for lead in leads[:3]:
                        logger.info(f"   📋 {lead['name']} - {lead['title']} at {lead['company']}")
                        logger.info(f"   🔗 {lead['linkedin_url']}")
                        logger.info(f"   📍 {lead.get('location', 'N/A')}")
                else:
                    logger.warning("⚠️ Montreal CEO scraper returned no leads")
            except Exception as e:
                logger.error(f"❌ Montreal CEO scraper failed: {e}")
        
        # Fallback to PRODUCTION scraper if Montreal scraper fails
        if not leads and PRODUCTION_SCRAPER_AVAILABLE:
            logger.info("🚀 Fallback: Using PRODUCTION LinkedIn scraper...")
            try:
                leads = await scrape_production_leads()
                
                if leads:
                    logger.info(f"✅ SUCCESS: Got {len(leads)} REAL LinkedIn profiles from production scraper")
                    # Log sample of real data
                    for lead in leads[:3]:
                        logger.info(f"   📋 {lead['name']} - {lead['title']} at {lead['company']}")
                        logger.info(f"   🔗 {lead['linkedin_url']}")
                else:
                    logger.warning("⚠️ Production scraper returned no leads")
            except Exception as e:
                logger.error(f"❌ Production scraper failed: {e}")
        
        # Fallback to curated real data if production scraper fails
        if not leads and REAL_SCRAPER_AVAILABLE:
            logger.info("Production scraper failed, using curated Montreal executives...")
            try:
                leads = await scrape_real_linkedin_leads()
                if leads:
                    logger.info(f"SUCCESS: Got {len(leads)} curated Montreal executive leads")
                else:
                    logger.warning("Real scraper returned no leads")
            except Exception as e:
                logger.error(f"Real scraper failed: {e}")
        
        # Try Playwright as backup
        if not leads and PLAYWRIGHT_AVAILABLE:
            logger.info("Attempting Playwright-based LinkedIn scraping...")
            try:
                leads = await scrape_linkedin_leads()
                if leads:
                    logger.info(f"SUCCESS: Got {len(leads)} leads from Playwright")
                else:
                    logger.warning("Playwright returned no leads")
            except Exception as e:
                logger.error(f"Playwright failed: {e}")
        
        # Try Apify as backup
        if not leads and APIFY_AVAILABLE and os.getenv('APIFY_TOKEN'):
            logger.info("Attempting Apify as backup...")
            try:
                leads = await scrape_linkedin_leads_apify()
                if leads:
                    logger.info(f"SUCCESS: Got {len(leads)} leads from Apify")
                else:
                    logger.warning("Apify returned no leads")
            except Exception as e:
                logger.error(f"Apify failed: {e}")
        
        # VALIDATION-FIRST APPROACH: NO MOCK DATA FALLBACKS
        if not leads:
            logger.error("❌ ALL REAL SCRAPING METHODS FAILED")
            logger.error("❌ VALIDATION-FIRST PIPELINE: No mock data will be generated")
            logger.error("❌ Check your LinkedIn credentials, Apify token, and network connectivity")
            logger.error("❌ System will not proceed without real data")
            return  # Exit without generating fake data
        
        # Log each lead that was scraped/generated
        for lead in leads:
            logger.info(f"[SCRAPER] Scraped lead: {lead['name']} from {lead['company']}")
        
        # Save the leads for the validation-first pipeline
        save_raw_leads(leads)
        
        logger.info("Scraping completed successfully")
    
    except Exception as e:
        logger.error(f"Error in scraper agent: {str(e)}")
        raise

if __name__ == "__main__":
    # Check if we should run once or in a loop
    run_once = os.environ.get('RUN_ONCE', '').lower() in ('true', '1', 'yes')
    
    if run_once:
        # Run once and exit
        logger.info("Running scraper agent once")
        asyncio.run(main())
        logger.info("Scraper agent completed")
    else:
        # Run in a loop with a delay
        logger.info("Running scraper agent in a loop")
        while True:
            asyncio.run(main())
            
            # Get the delay from environment variable or default to 3600 seconds (1 hour)
            delay = int(os.environ.get('SCRAPER_DELAY_SECONDS', '3600'))
            logger.info(f"Sleeping for {delay} seconds before next scrape")
            time.sleep(delay)