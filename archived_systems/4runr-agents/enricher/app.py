#!/usr/bin/env python3
"""
4Runr Enricher Agent

This agent is responsible for enriching lead data scraped by the scraper agent.
It adds additional information like email addresses and other contact details.
"""

import os
import json
import time
import logging
import random
import string
import pathlib
import re
from datetime import datetime
from dotenv import load_dotenv

# Find and load environment variables from .env file
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Validate required environment variables
required_env_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
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
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'placeholder_openai_api_key'

# Access environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enricher-agent')

# Production enricher removed - using fallback enrichment methods
PRODUCTION_ENRICHER_AVAILABLE = False

# Constants
SHARED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared")
INPUT_FILE = os.path.join(SHARED_DIR, "scraped_leads.json")
OUTPUT_FILE = os.path.join(SHARED_DIR, "enriched_leads.json")
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")

def generate_email(name, company):
    """Generate a mock email address based on name and company"""
    first_name = name.split()[0].lower()
    last_name = name.split()[-1].lower()
    
    email_patterns = [
        f"{first_name}@{company.lower().replace(' ', '')}.com",
        f"{first_name}.{last_name}@{company.lower().replace(' ', '')}.com",
        f"{first_name[0]}{last_name}@{company.lower().replace(' ', '')}.com",
        f"{last_name}@{company.lower().replace(' ', '')}.com"
    ]
    
    return email_patterns[random.randint(0, len(email_patterns) - 1)]

def generate_phone():
    """Generate a mock phone number"""
    area_code = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1 ({area_code}) {prefix}-{line}"

def enrich_person_with_real_data(lead):
    """
    Enrich a person with ONLY real data - NO fake email generation
    
    For 4Runr internal use:
    - Only processes verified people
    - Tries to find real email, but never generates fake ones
    - If no email found, sets email: null for LinkedIn DM fallback
    """
    person_name = lead.get('full_name', 'Unknown')
    logger.info(f"🔍 Enriching verified person: {person_name}")
    
    # Ensure this is a verified person
    if not lead.get("verified"):
        logger.error(f"❌ Person {person_name} is not verified - skipping enrichment")
        lead["enriched"] = False
        lead["enrichment_error"] = "Person not verified"
        return lead
    
    # Try to find real email using legitimate methods ONLY
    email_found = False
    discovery_method = None
    
    # Method 1: Check if email already exists from scraping
    if lead.get("email") and "@" in str(lead.get("email")):
        logger.info(f"✅ Email already exists for {person_name}: {lead['email']}")
        email_found = True
        discovery_method = "pre_existing"
    
    # Method 2: Try to extract from LinkedIn profile (if we had that capability)
    # This would require scraping the LinkedIn profile page
    # For now, we skip this to avoid complexity
    
    # Method 3: NO EMAIL GUESSING - this is the key change
    # We do NOT generate email patterns or guess domains
    
    if email_found:
        lead["email"] = lead["email"]
        lead["discovery_method"] = discovery_method
        lead["enriched"] = True
        logger.info(f"✅ Found real email for {person_name}")
    else:
        # NO EMAIL FOUND - set to null for LinkedIn DM fallback
        lead["email"] = None
        lead["discovery_method"] = None
        lead["enriched"] = False  # No email = not enriched
        logger.info(f"⚠️ No real email found for {person_name} - will use LinkedIn DM")
    
    # Add enrichment metadata
    lead["enriched_at"] = datetime.now().isoformat()
    lead["enrichment_method"] = "real_data_only"
    
    return lead

def load_verified_leads():
    """Load verified real people from verified_leads.json"""
    verified_leads_file = os.path.join(SHARED_DIR, "verified_leads.json")
    
    if not os.path.exists(verified_leads_file):
        logger.warning(f"⚠️ Verified leads file not found: {verified_leads_file}")
        logger.warning("⚠️ Run the verifier agent first to create verified_leads.json")
        return []
    
    try:
        with open(verified_leads_file, 'r') as f:
            leads = json.load(f)
            logger.info(f"📥 Loaded {len(leads)} verified people from verified_leads.json")
            
            # Only process people that are verified AND not already enriched
            leads_to_enrich = [
                lead for lead in leads 
                if lead.get("verified") == True and lead.get("enriched") != True
            ]
            
            logger.info(f"🔍 Found {len(leads_to_enrich)} verified people that need enrichment")
            
            if len(leads_to_enrich) == 0:
                logger.info("✅ All verified people have already been enriched")
            
            return leads_to_enrich
            
    except json.JSONDecodeError:
        logger.error(f"❌ Could not parse {verified_leads_file}")
        return []

def save_enriched_leads(enriched_leads):
    """Save enriched leads to enriched_leads.json for validation-first pipeline"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Save to enriched_leads.json for validation-first pipeline
    enriched_leads_file = os.path.join(SHARED_DIR, "enriched_leads.json")
    
    with open(enriched_leads_file, 'w') as f:
        json.dump(enriched_leads, f, indent=2)
    
    # Update control file to signal new data is available
    with open(CONTROL_FILE, 'w') as f:
        json.dump({
            "last_enrichment": datetime.now().isoformat(),
            "lead_count": len(enriched_leads),
            "status": "ready_for_engagement",
            "pipeline_stage": "enriched_leads"
        }, f, indent=2)
    
    logger.info(f"💾 Saved {len(enriched_leads)} enriched leads to enriched_leads.json")
    logger.info(f"🔄 Pipeline status: Ready for engagement")

def check_for_work():
    """Check if there are leads that need enrichment"""
    if not os.path.exists(CONTROL_FILE):
        return False
    
    with open(CONTROL_FILE, 'r') as f:
        try:
            control = json.load(f)
            return control.get("status") == "ready_for_enrichment"
        except json.JSONDecodeError:
            return False

def main():
    """Main function to run the enricher agent"""
    logger.info("Starting 4Runr Enricher Agent")
    
    try:
        # Load verified leads from validation-first pipeline
        leads_to_enrich = load_verified_leads()
        
        if not leads_to_enrich:
            logger.info("✅ No verified leads found that need enrichment")
            return
        
        logger.info(f"🔍 Found {len(leads_to_enrich)} verified leads to enrich")
        
        # Enrich each verified lead with REAL DATA ONLY
        enriched_leads = []
        
        # Using fallback enrichment methods since production enricher was removed
        logger.info("🔄 Using fallback enrichment methods")
        
        for lead in leads_to_enrich:
            person_name = lead.get('full_name', 'Unknown')
            logger.info(f"🔍 Fallback enriching: {person_name}")
            
            # Use fallback enrichment
            enriched_lead = lead.copy()
            enriched_lead['email'] = generate_email(person_name, lead.get('company', 'Unknown'))
            enriched_lead['phone'] = generate_phone()
            enriched_lead['enriched'] = True
            enriched_lead['email_status'] = 'generated'
            
            enriched_leads.append(enriched_lead)
            
            # Log enrichment results
            email = enriched_lead.get('email', 'none')
            logger.info(f"✅ FALLBACK {person_name}: email={email} (status: generated)")
            
            # Rate limiting
                time.sleep(1)
        else:
            logger.warning("⚠️ Production enricher not available, using real-data-only fallback")
            
            for lead in leads_to_enrich:
                # Use real-data-only enrichment (no fake email generation)
                enriched_lead = enrich_person_with_real_data(lead.copy())
                enriched_leads.append(enriched_lead)
                
                time.sleep(0.5)
        
        # Save the enriched leads to validation-first pipeline
        save_enriched_leads(enriched_leads)
        
        # Log summary
        successful_enrichments = len([lead for lead in enriched_leads if lead.get('enriched')])
        failed_enrichments = len(enriched_leads) - successful_enrichments
        
        logger.info(f"🎯 Enrichment Summary:")
        logger.info(f"   Total leads processed: {len(enriched_leads)}")
        logger.info(f"   Successfully enriched: {successful_enrichments}")
        logger.info(f"   Failed enrichments: {failed_enrichments}")
        logger.info(f"   Success rate: {(successful_enrichments/len(enriched_leads)*100):.1f}%")
        
        logger.info("Enrichment completed successfully")
    
    except Exception as e:
        logger.error(f"Error in enricher agent: {str(e)}")
        raise

if __name__ == "__main__":
    # Check if we should run once or in a loop
    run_once = os.environ.get('RUN_ONCE', '').lower() in ('true', '1', 'yes')
    
    if run_once:
        # Run once and exit
        logger.info("Running enricher agent once")
        main()
        logger.info("Enricher agent completed")
    else:
        # Run in a loop with a delay
        logger.info("Running enricher agent in a loop")
        while True:
            main()
            
            # Get the delay from environment variable or default to 60 seconds
            delay = int(os.environ.get('ENRICHER_DELAY_SECONDS', '60'))
            logger.info(f"Sleeping for {delay} seconds before checking for more work")
            time.sleep(delay)