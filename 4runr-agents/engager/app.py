#!/usr/bin/env python3
"""
4Runr Engager Agent

This agent is responsible for sending outreach messages to leads
that have been enriched by the enricher agent.
"""

import os
import sys
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
logger = logging.getLogger('engager-agent')

# Constants
SHARED_DIR = "/shared"
INPUT_FILE = os.path.join(SHARED_DIR, "enriched_leads.json")
OUTPUT_FILE = os.path.join(SHARED_DIR, "engaged_leads.json")
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")

# Message templates for different industries
MESSAGE_TEMPLATES = {
    "Technology": [
        "Hi {first_name}, I noticed your work at {company} in the tech space. I'd love to connect and discuss how our AI solutions could help streamline your operations.",
        "Hello {first_name}, your experience as {title} at {company} caught my attention. Would you be open to a quick chat about AI-powered automation for your team?"
    ],
    "Finance": [
        "Hi {first_name}, I saw your profile and your work at {company}. Our AI solutions have helped similar financial firms increase efficiency by 30%. Would you be interested in learning more?",
        "Hello {first_name}, as {title} at {company}, I thought you might be interested in how our AI tools are helping finance professionals save time on analysis and reporting."
    ],
    "Healthcare": [
        "Hi {first_name}, I noticed your role at {company} in healthcare. Our AI solutions are helping medical professionals improve patient outcomes while reducing administrative burden.",
        "Hello {first_name}, given your position as {title} at {company}, I thought you might be interested in how our AI tools are transforming healthcare operations."
    ],
    "default": [
        "Hi {first_name}, I came across your profile and was impressed by your work at {company}. I'd love to connect and share how our AI solutions might benefit your team.",
        "Hello {first_name}, your experience as {title} caught my attention. I'd love to discuss how our AI platform could help drive results for {company}."
    ]
}

def generate_message(lead):
    """Generate a personalized message for a lead"""
    industry = lead.get("industry", "default")
    if industry not in MESSAGE_TEMPLATES:
        industry = "default"
    
    template = random.choice(MESSAGE_TEMPLATES[industry])
    first_name = lead["name"].split()[0]
    
    return template.format(
        first_name=first_name,
        company=lead["company"],
        title=lead["title"]
    )

def send_message(lead, message):
    """Simulate sending a message to a lead"""
    # In a real implementation, this would use LinkedIn API or email service
    # For now, we'll just simulate sending
    
    channel = "email" if "email" in lead else "linkedin"
    
    if channel == "email":
        logger.info(f"Sending email to {lead['email']}")
    else:
        logger.info(f"Sending LinkedIn message to {lead['linkedin_url']}")
    
    # Simulate sending delay
    time.sleep(1)
    
    # Add engagement information to the lead
    lead["engagement"] = {
        "channel": channel,
        "message": message,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"
    }
    
    return lead

def load_leads():
    """Load leads from the shared leads.json file"""
    shared_file = os.path.join(SHARED_DIR, "leads.json")
    if not os.path.exists(shared_file):
        logger.warning(f"Shared file {shared_file} not found")
        return [], []
    
    try:
        with open(shared_file, 'r') as f:
            leads = json.load(f)
            logger.info(f"Loaded {len(leads)} leads from {shared_file}")
            # Filter leads that need engagement (status is 'enriched')
            leads_to_engage = [lead for lead in leads if lead.get("status") == "enriched"]
            logger.info(f"Found {len(leads_to_engage)} leads that need engagement")
            return leads, leads_to_engage
    except json.JSONDecodeError:
        logger.error(f"Could not parse {shared_file}")
        return [], []

def save_leads(all_leads, engaged_leads):
    """Save engaged leads to the shared leads.json file"""
    # Ensure the shared directory exists
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Update the status of engaged leads
    for lead in all_leads:
        for engaged_lead in engaged_leads:
            if lead.get("linkedin_url") == engaged_lead.get("linkedin_url"):
                lead.update(engaged_lead)
    
    # Write all leads to the shared file
    shared_file = os.path.join(SHARED_DIR, "leads.json")
    with open(shared_file, 'w') as f:
        json.dump(all_leads, f, indent=2)
    
    # Write engaged leads to the output file for backward compatibility
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(engaged_leads, f, indent=2)
    
    # Update control file to signal engagement is complete
    with open(CONTROL_FILE, 'w') as f:
        json.dump({
            "last_engagement": datetime.now().isoformat(),
            "lead_count": len(engaged_leads),
            "status": "engagement_complete"
        }, f, indent=2)
    
    logger.info(f"Saved {len(engaged_leads)} engaged leads to {shared_file}")

def check_for_work():
    """Check if there are leads ready for engagement"""
    if not os.path.exists(CONTROL_FILE):
        return False
    
    with open(CONTROL_FILE, 'r') as f:
        try:
            control = json.load(f)
            return control.get("status") == "ready_for_engagement"
        except json.JSONDecodeError:
            return False

def main():
    """Main function to run the engager agent"""
    logger.info("Starting 4Runr Engager Agent")
    
    try:
        # Load leads from the shared file
        all_leads, leads_to_engage = load_leads()
        
        if not leads_to_engage:
            logger.info("No leads found that need engagement")
            return
        
        logger.info(f"Found {len(leads_to_engage)} leads to engage")
        
        # Engage with each lead
        engaged_leads = []
        for lead in leads_to_engage:
            logger.info(f"Engaging with lead: {lead['name']}")
            
            # Generate a personalized message
            message = generate_message(lead)
            
            # Send the message
            engaged_lead = lead.copy()
            
            # Determine channel (email or LinkedIn)
            channel = "email" if lead.get("email") else "linkedin"
            
            # Simulate sending the message
            time.sleep(1)  # Simulate API call delay
            
            # Update the lead with engagement information
            engaged_lead["status"] = "contacted"
            engaged_lead["engagement"] = {
                "channel": channel,
                "message": message,
                "sent_at": datetime.now().isoformat(),
                "status": "sent"
            }
            
            # Log the engagement
            if channel == "email":
                logger.info(f"[ENGAGER] Message sent to {lead['name']} via email: {lead.get('email')} (Status: contacted)")
            else:
                logger.info(f"[ENGAGER] Message sent to {lead['name']} via LinkedIn: {lead.get('linkedin_url')} (Status: contacted)")
            
            # Push the lead to Airtable
            try:
                # Import the Airtable client
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from shared.airtable_client import push_lead_to_airtable
                
                # Push the lead to Airtable
                if push_lead_to_airtable(engaged_lead):
                    engaged_lead["airtable_synced"] = True
                else:
                    engaged_lead["airtable_synced"] = False
            except Exception as e:
                logger.error(f"[AIRTABLE] Failed to import or use Airtable client: {str(e)}")
                engaged_lead["airtable_synced"] = False
            
            engaged_leads.append(engaged_lead)
        
        # Save the engaged leads
        save_leads(all_leads, engaged_leads)
        
        logger.info("Engagement completed successfully")
    
    except Exception as e:
        logger.error(f"Error in engager agent: {str(e)}")
        raise

if __name__ == "__main__":
    # Check if we should run once or in a loop
    run_once = os.environ.get('RUN_ONCE', '').lower() in ('true', '1', 'yes')
    
    if run_once:
        # Run once and exit
        logger.info("Running engager agent once")
        main()
        logger.info("Engager agent completed")
    else:
        # Run in a loop with a delay
        logger.info("Running engager agent in a loop")
        while True:
            main()
            
            # Get the delay from environment variable or default to 300 seconds (5 minutes)
            delay = int(os.environ.get('ENGAGER_DELAY_SECONDS', '300'))
            logger.info(f"Sleeping for {delay} seconds before checking for more work")
            time.sleep(delay)