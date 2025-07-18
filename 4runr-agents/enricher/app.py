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

# Constants
SHARED_DIR = "/shared"
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

def enrich_lead(lead):
    """Enrich a lead with additional information"""
    # In a real implementation, this would call APIs like Clearbit or Apollo
    # For now, we'll generate mock data
    
    # Add email
    lead["email"] = generate_email(lead["name"], lead["company"])
    
    # Add phone number (sometimes)
    if random.random() > 0.3:
        lead["phone"] = generate_phone()
    
    # Add company size (sometimes)
    if random.random() > 0.4:
        lead["company_size"] = random.choice(["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001+"])
    
    # Add company industry (sometimes)
    if random.random() > 0.3:
        lead["industry"] = random.choice([
            "Technology", "Finance", "Healthcare", "Education", "Manufacturing",
            "Retail", "Media", "Consulting", "Real Estate", "Energy"
        ])
    
    # Add location (sometimes)
    if random.random() > 0.2:
        lead["location"] = random.choice([
            "New York, NY", "San Francisco, CA", "Austin, TX", "Seattle, WA",
            "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO",
            "Atlanta, GA", "Miami, FL", "Portland, OR", "Nashville, TN"
        ])
    
    # Mark as enriched
    lead["needs_enrichment"] = False
    lead["enriched_at"] = datetime.now().isoformat()
    lead["ready_for_engagement"] = True
    
    return lead

def load_leads():
    """Load leads from the shared leads.json file"""
    shared_file = os.path.join(SHARED_DIR, "leads.json")
    if not os.path.exists(shared_file):
        logger.warning(f"Shared file {shared_file} not found")
        return []
    
    try:
        with open(shared_file, 'r') as f:
            leads = json.load(f)
            logger.info(f"Loaded {len(leads)} leads from {shared_file}")
            # Filter leads that need enrichment (status is 'scraped')
            leads_to_enrich = [lead for lead in leads if lead.get("status") == "scraped"]
            logger.info(f"Found {len(leads_to_enrich)} leads that need enrichment")
            return leads, leads_to_enrich
    except json.JSONDecodeError:
        logger.error(f"Could not parse {shared_file}")
        return [], []

def save_leads(all_leads, enriched_leads):
    """Save enriched leads to the shared leads.json file"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Update the status of enriched leads
    for lead in all_leads:
        for enriched_lead in enriched_leads:
            if lead.get("linkedin_url") == enriched_lead.get("linkedin_url"):
                lead.update(enriched_lead)
    
    # Write all leads to the shared file
    shared_file = os.path.join(SHARED_DIR, "leads.json")
    with open(shared_file, 'w') as f:
        json.dump(all_leads, f, indent=2)
    
    # Write enriched leads to the output file for backward compatibility
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_leads, f, indent=2)
    
    # Update control file to signal new data is available
    with open(CONTROL_FILE, 'w') as f:
        json.dump({
            "last_enrichment": datetime.now().isoformat(),
            "lead_count": len(enriched_leads),
            "status": "ready_for_engagement"
        }, f, indent=2)
    
    logger.info(f"Saved {len(enriched_leads)} enriched leads to {shared_file}")

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
        # Load leads from the shared file
        all_leads, leads_to_enrich = load_leads()
        
        if not leads_to_enrich:
            logger.info("No leads found that need enrichment")
            return
        
        logger.info(f"Found {len(leads_to_enrich)} leads to enrich")
        
        # Enrich each lead
        enriched_leads = []
        for lead in leads_to_enrich:
            logger.info(f"Enriching lead: {lead['name']}")
            time.sleep(0.5)  # Simulate API call delay
            
            # Update the lead with enriched data
            enriched_lead = lead.copy()
            enriched_lead["email"] = generate_email(lead["name"], lead["company"])
            
            # Add phone number (sometimes)
            if random.random() > 0.3:
                enriched_lead["phone"] = generate_phone()
            
            # Add company size (sometimes)
            if random.random() > 0.4:
                enriched_lead["company_size"] = random.choice(["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001+"])
            
            # Add company industry (sometimes)
            if random.random() > 0.3:
                enriched_lead["industry"] = random.choice([
                    "Technology", "Finance", "Healthcare", "Education", "Manufacturing",
                    "Retail", "Media", "Consulting", "Real Estate", "Energy"
                ])
            
            # Mark as enriched and ready for engagement
            enriched_lead["status"] = "enriched"
            enriched_lead["enriched_at"] = datetime.now().isoformat()
            
            # Log the enrichment
            logger.info(f"[ENRICHER] Enriched lead: {enriched_lead['name']} (company: {enriched_lead['company']}, email: {enriched_lead['email']})")
            
            enriched_leads.append(enriched_lead)
        
        # Save the enriched leads
        save_leads(all_leads, enriched_leads)
        
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