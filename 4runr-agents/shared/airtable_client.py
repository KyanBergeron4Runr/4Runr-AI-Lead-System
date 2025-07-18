#!/usr/bin/env python3
"""
Airtable Client Module

This module provides functions to interact with the Airtable API.
"""

import os
import json
import logging
import pathlib
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-client')

# Find and load environment variables from .env file
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Get Airtable configuration from environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Leads')

# Check if Airtable configuration is available
if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    logger.warning("Airtable configuration not found. Using placeholder values.")
    AIRTABLE_API_KEY = 'placeholder_api_key'
    AIRTABLE_BASE_ID = 'placeholder_base_id'

# Constants
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
FAILED_LEADS_FILE = os.path.join(os.path.dirname(__file__), "failed_leads.json")

def push_lead_to_airtable(lead: dict) -> bool:
    """
    Sends a lead to Airtable
    
    Args:
        lead: A dictionary containing lead information
        
    Returns:
        bool: True if the lead was successfully sent to Airtable, False otherwise
    """
    if AIRTABLE_API_KEY == 'placeholder_api_key':
        logger.warning(f"[AIRTABLE] Using placeholder API key. Lead {lead.get('name')} not sent to Airtable.")
        return False
    
    # Prepare the data for Airtable
    airtable_data = {
        "fields": {
            "Name": lead.get("name", ""),
            "LinkedIn URL": lead.get("linkedin_url", ""),
            "Company": lead.get("company", ""),
            "Title": lead.get("title", ""),
            "Email": lead.get("email", ""),
            "Status": lead.get("status", ""),
            "Needs Enrichment": lead.get("status") != "contacted",
        }
    }
    
    # Add additional fields if they exist
    if "phone" in lead:
        airtable_data["fields"]["Phone"] = lead["phone"]
    
    if "industry" in lead:
        airtable_data["fields"]["Industry"] = lead["industry"]
    
    if "company_size" in lead:
        airtable_data["fields"]["Company Size"] = lead["company_size"]
    
    if "location" in lead:
        airtable_data["fields"]["Location"] = lead["location"]
    
    # Add engagement information if it exists
    if "engagement" in lead:
        engagement_info = lead["engagement"]
        airtable_data["fields"]["Engagement Channel"] = engagement_info.get("channel", "")
        airtable_data["fields"]["Engagement Date"] = engagement_info.get("sent_at", "")
        airtable_data["fields"]["Engagement Status"] = engagement_info.get("status", "")
    
    # Set up the headers
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Send the data to Airtable
        response = requests.post(
            AIRTABLE_API_URL,
            headers=headers,
            json=airtable_data
        )
        
        # Check if the request was successful
        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"[AIRTABLE] Lead {lead.get('name')} synced to Airtable ✅")
            return True
        else:
            logger.error(f"[AIRTABLE] Failed to sync {lead.get('name')} — HTTP {response.status_code}: {response.text}")
            save_failed_lead(lead)
            return False
    
    except Exception as e:
        logger.error(f"[AIRTABLE] Failed to sync {lead.get('name')} — {str(e)}")
        save_failed_lead(lead)
        return False

def save_failed_lead(lead: dict) -> None:
    """
    Saves a failed lead to a JSON file for later retry
    
    Args:
        lead: A dictionary containing lead information
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(FAILED_LEADS_FILE), exist_ok=True)
    
    # Load existing failed leads
    failed_leads = []
    if os.path.exists(FAILED_LEADS_FILE):
        try:
            with open(FAILED_LEADS_FILE, 'r') as f:
                failed_leads = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {FAILED_LEADS_FILE}, starting with empty list")
    
    # Add the new failed lead
    failed_leads.append(lead)
    
    # Save the updated list
    with open(FAILED_LEADS_FILE, 'w') as f:
        json.dump(failed_leads, f, indent=2)
    
    logger.info(f"[AIRTABLE] Lead {lead.get('name')} saved to {FAILED_LEADS_FILE} for later retry")

def retry_failed_leads() -> int:
    """
    Retries sending failed leads to Airtable
    
    Returns:
        int: The number of successfully retried leads
    """
    if not os.path.exists(FAILED_LEADS_FILE):
        logger.info(f"No failed leads to retry ({FAILED_LEADS_FILE} not found)")
        return 0
    
    try:
        # Load failed leads
        with open(FAILED_LEADS_FILE, 'r') as f:
            failed_leads = json.load(f)
        
        if not failed_leads:
            logger.info("No failed leads to retry")
            return 0
        
        logger.info(f"Retrying {len(failed_leads)} failed leads")
        
        # Retry each lead
        successful_retries = []
        still_failed = []
        
        for lead in failed_leads:
            if push_lead_to_airtable(lead):
                successful_retries.append(lead)
            else:
                still_failed.append(lead)
        
        # Save the remaining failed leads
        with open(FAILED_LEADS_FILE, 'w') as f:
            json.dump(still_failed, f, indent=2)
        
        logger.info(f"Successfully retried {len(successful_retries)} leads, {len(still_failed)} still failed")
        return len(successful_retries)
    
    except Exception as e:
        logger.error(f"Error retrying failed leads: {str(e)}")
        return 0

if __name__ == "__main__":
    # Test the Airtable client
    logger.info("Testing Airtable client...")
    
    # Create a test lead
    test_lead = {
        "name": "Test Lead",
        "linkedin_url": "https://linkedin.com/in/testlead",
        "company": "Test Company",
        "title": "Test Title",
        "email": "test@example.com",
        "status": "contacted",
        "engagement": {
            "channel": "email",
            "sent_at": "2023-01-01T00:00:00Z",
            "status": "sent"
        }
    }
    
    # Try to push the lead to Airtable
    result = push_lead_to_airtable(test_lead)
    
    if result:
        logger.info("Test successful!")
    else:
        logger.warning("Test failed. Check your Airtable configuration.")
    
    # Try to retry failed leads
    retried = retry_failed_leads()
    logger.info(f"Retried {retried} failed leads")