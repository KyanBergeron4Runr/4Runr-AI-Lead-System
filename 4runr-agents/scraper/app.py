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
logger = logging.getLogger('scraper-agent')

# Constants
SHARED_DIR = "/shared"
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

COMPANIES = [
    'Acme Corp', 'Globex', 'Initech', 'Umbrella Corp', 'Stark Industries',
    'Wayne Enterprises', 'Cyberdyne Systems', 'Soylent Corp', 'Massive Dynamic',
    'Hooli', 'Pied Piper', 'Dunder Mifflin', 'Wonka Industries', 'Oceanic Airlines'
]

TITLES = [
    'CEO', 'CTO', 'CFO', 'COO', 'VP of Sales', 'VP of Marketing',
    'Director of Engineering', 'Director of Product', 'Product Manager',
    'Software Engineer', 'Data Scientist', 'Marketing Manager',
    'Sales Representative', 'Customer Success Manager', 'HR Manager'
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
    """Generate a mock lead with realistic data"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    company = random.choice(COMPANIES)
    title = random.choice(TITLES)
    linkedin_url = generate_linkedin_url(first_name, last_name)
    
    return {
        "id": f"lead_{int(time.time())}_{random.randint(1000, 9999)}",
        "name": f"{first_name} {last_name}",
        "linkedin_url": linkedin_url,
        "company": company,
        "title": title,
        "scraped_at": datetime.now().isoformat(),
        "needs_enrichment": True
    }

def generate_mock_leads(count):
    """Generate multiple mock leads"""
    return [generate_mock_lead() for _ in range(count)]

def save_leads(leads):
    """Save leads to the shared output file"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Format leads for the shared file
    formatted_leads = []
    for lead in leads:
        formatted_lead = {
            "name": lead["name"],
            "linkedin_url": lead["linkedin_url"],
            "company": lead["company"],
            "title": lead["title"],
            "email": "",  # Empty email to be filled by enricher
            "status": "scraped",
            "scraped_at": datetime.now().isoformat()
        }
        formatted_leads.append(formatted_lead)
    
    # Read existing leads from the shared file
    shared_file = os.path.join(SHARED_DIR, "leads.json")
    existing_leads = []
    if os.path.exists(shared_file):
        try:
            with open(shared_file, 'r') as f:
                existing_leads = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {shared_file}, starting with empty leads list")
    
    # Combine existing and new leads
    all_leads = existing_leads + formatted_leads
    
    # Write all leads to the shared file
    with open(shared_file, 'w') as f:
        json.dump(all_leads, f, indent=2)
    
    # Write leads to the output file for backward compatibility
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(leads, f, indent=2)
    
    # Update control file to signal new data is available
    with open(CONTROL_FILE, 'w') as f:
        json.dump({
            "last_scrape": datetime.now().isoformat(),
            "lead_count": len(leads),
            "status": "ready_for_enrichment"
        }, f, indent=2)
    
    logger.info(f"Saved {len(formatted_leads)} new leads to {shared_file} (total: {len(all_leads)})")

def main():
    """Main function to run the scraper agent"""
    logger.info("Starting 4Runr Scraper Agent")
    
    try:
        # In a real implementation, this would connect to LinkedIn or a scraping tool
        # For now, we'll generate mock data
        logger.info("Simulating LinkedIn scraping...")
        time.sleep(2)  # Simulate work
        
        # Generate mock leads
        lead_count = int(os.environ.get('SCRAPER_LEAD_COUNT', '5'))
        logger.info(f"Generating {lead_count} mock leads")
        leads = generate_mock_leads(lead_count)
        
        # Log each lead that was generated
        for lead in leads:
            logger.info(f"[SCRAPER] Scraped lead: {lead['name']} from {lead['company']}")
        
        # Save the leads for the enricher
        save_leads(leads)
        
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
        main()
        logger.info("Scraper agent completed")
    else:
        # Run in a loop with a delay
        logger.info("Running scraper agent in a loop")
        while True:
            main()
            
            # Get the delay from environment variable or default to 3600 seconds (1 hour)
            delay = int(os.environ.get('SCRAPER_DELAY_SECONDS', '3600'))
            logger.info(f"Sleeping for {delay} seconds before next scrape")
            time.sleep(delay)