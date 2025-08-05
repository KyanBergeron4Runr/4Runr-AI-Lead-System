#!/usr/bin/env python3
"""
Airtable Client Module - Business-Focused

This module provides functions to interact with the Airtable API
focusing on core business data: Name, Email, Company, Role, LinkedIn URL
"""

import os
import json
import logging
import pathlib
import requests
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-client')

# Initialize production logging
try:
    from production_logger import log_production_event
    PRODUCTION_LOGGING_ENABLED = True
    logger.info("🏭 Production logging enabled for Airtable client")
except ImportError:
    logger.warning("⚠️ Production logging not available")
    PRODUCTION_LOGGING_ENABLED = False

# Find and load environment variables from .env file
script_dir = pathlib.Path(__file__).parent.absolute()
root_dir = script_dir.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Get Airtable configuration from environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')

# Check if Airtable configuration is available
if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    logger.warning("Airtable configuration not found. Using placeholder values.")
    AIRTABLE_API_KEY = 'placeholder_api_key'
    AIRTABLE_BASE_ID = 'placeholder_base_id'

# Constants
AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
FAILED_LEADS_FILE = os.path.join(os.path.dirname(__file__), "failed_leads.json")
PROCESSED_LEADS_FILE = os.path.join(os.path.dirname(__file__), "processed_leads.json")

def _format_date(date_string: str) -> str:
    """Format ISO datetime string to YYYY-MM-DD for Airtable"""
    if not date_string:
        return ""
    
    try:
        # Parse ISO datetime and extract date part
        from datetime import datetime
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return ""

def _map_source(source: str) -> str:
    """Map source values to valid Airtable options"""
    # Valid options: Search, Comment, Other
    source_lower = source.lower()
    
    if 'search' in source_lower or 'linkedin' in source_lower:
        return "Search"
    elif 'comment' in source_lower:
        return "Comment"
    else:
        return "Other"

def check_linkedin_url_exists(linkedin_url: str) -> bool:
    """Check if a LinkedIn URL already exists in Airtable"""
    if not linkedin_url:
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {AIRTABLE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Search for existing LinkedIn URL
        # Use filterByFormula to find exact match
        filter_formula = f"{{LinkedIn URL}} = '{linkedin_url}'"
        params = {
            'filterByFormula': filter_formula,
            'maxRecords': 1
        }
        
        response = requests.get(AIRTABLE_API_URL, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            
            if records:
                existing_lead = records[0]['fields']
                logger.info(f"🔍 Duplicate found: {existing_lead.get('Full Name', 'Unknown')} already exists")
                return True
            else:
                return False
        else:
            logger.warning(f"⚠️ Error checking duplicates: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking LinkedIn URL: {str(e)}")
        return False

def mark_lead_as_processed(lead: dict) -> None:
    """Mark a lead as processed by moving it to processed_leads.json"""
    try:
        # Load existing processed leads
        processed_leads = []
        if os.path.exists(PROCESSED_LEADS_FILE):
            with open(PROCESSED_LEADS_FILE, 'r', encoding='utf-8') as f:
                processed_leads = json.load(f)
        
        # Add current lead with processing timestamp
        processed_lead = lead.copy()
        processed_lead['processed_at'] = datetime.now().isoformat()
        processed_lead['processed_status'] = 'synced_to_airtable'
        
        processed_leads.append(processed_lead)
        
        # Save updated processed leads
        with open(PROCESSED_LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed_leads, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 Lead marked as processed: {lead.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Error marking lead as processed: {str(e)}")

def get_processed_linkedin_urls() -> set:
    """Get set of LinkedIn URLs that have already been processed"""
    try:
        if not os.path.exists(PROCESSED_LEADS_FILE):
            return set()
        
        with open(PROCESSED_LEADS_FILE, 'r', encoding='utf-8') as f:
            processed_leads = json.load(f)
        
        urls = set()
        for lead in processed_leads:
            linkedin_url = lead.get('linkedin_url')
            if linkedin_url:
                urls.add(linkedin_url)
        
        return urls
        
    except Exception as e:
        logger.error(f"❌ Error loading processed leads: {str(e)}")
        return set()

def _get_lead_status(lead: dict) -> str:
    """Determine lead status based on enrichment and engagement data"""
    if lead.get("engagement", {}).get("sent_at"):
        return "Contacted"
    elif lead.get("enriched"):
        return "Enriched"
    elif lead.get("verified"):
        return "Verified"
    else:
        return "New Lead"

def push_lead_to_airtable(lead: dict) -> bool:
    """
    Sends a lead to Airtable with core business data
    Includes de-duplication check to prevent repeat leads
    
    Args:
        lead: A dictionary containing lead information
        
    Returns:
        bool: True if the lead was successfully sent to Airtable, False otherwise
    """
    if AIRTABLE_API_KEY == 'placeholder_api_key':
        lead_name = lead.get('full_name', lead.get('name', 'Unknown'))
        logger.warning(f"[AIRTABLE] Using placeholder API key. Lead {lead_name} not sent to Airtable.")
        return False
    
    lead_name = lead.get('full_name', lead.get('name', 'Unknown'))
    linkedin_url = lead.get('linkedin_url', '')
    
    # De-duplication check: Skip if LinkedIn URL already exists in Airtable
    if linkedin_url and check_linkedin_url_exists(linkedin_url):
        logger.info(f"[AIRTABLE] 🔄 Skipping duplicate: {lead_name} (LinkedIn URL already exists)")
        return False
    
    # Also check if already processed locally
    processed_urls = get_processed_linkedin_urls()
    if linkedin_url and linkedin_url in processed_urls:
        logger.info(f"[AIRTABLE] 🔄 Skipping already processed: {lead_name}")
        return False
    
    # Use your exact Airtable field names
    airtable_data = {
        "fields": {
            "Full Name": lead.get("full_name", lead.get("name", "")),
            "LinkedIn URL": lead.get("linkedin_url", ""),
            "Job Title": lead.get("title", ""),
            "Company": lead.get("company", ""),
            "Email": lead.get("email", ""),
            "Source": _map_source(lead.get("source", "Search")),
            "Needs Enrichment": not lead.get("enriched", False),  # True if needs enrichment
            "Date Scraped": _format_date(lead.get("scraped_at", "")),
            "Date Enriched": _format_date(lead.get("enriched_at", "")),
            "Date Messaged": _format_date(lead.get("contacted_at", ""))
        }
    }
    
    # Remove empty fields to keep Airtable clean
    airtable_data["fields"] = {k: v for k, v in airtable_data["fields"].items() if v}
    
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
            logger.info(f"[AIRTABLE] ✅ Lead {lead_name} synced to Airtable successfully")
            
            # Log production data - successful sync
            if PRODUCTION_LOGGING_ENABLED:
                try:
                    sync_results = {
                        "success": True,
                        "record_id": response.json().get('id', 'unknown'),
                        "fields_synced": len(airtable_data["fields"]),
                        "response_code": response.status_code,
                        "sync_timestamp": datetime.now().isoformat()
                    }
                    
                    sync_decisions = {
                        "deduplication_check": True,
                        "field_mapping": list(airtable_data["fields"].keys()),
                        "empty_fields_removed": True,
                        "linkedin_url_validated": bool(linkedin_url)
                    }
                    
                    log_production_event(
                        "airtable_operation",
                        lead,
                        sync_results,
                        {"decisions": sync_decisions}
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Production logging failed: {e}")
            
            # Mark lead as processed to prevent future duplicates
            mark_lead_as_processed(lead)
            return True
        elif response.status_code == 422 and "UNKNOWN_FIELD_NAME" in response.text:
            # Try again with only the confirmed working fields
            logger.warning(f"[AIRTABLE] Some fields don't exist, retrying with basic fields for {lead_name}")
            
            basic_data = {
                "fields": {
                    "Full Name": lead.get("full_name", lead.get("name", "")),
                    "LinkedIn URL": lead.get("linkedin_url", ""),
                }
            }
            
            response = requests.post(AIRTABLE_API_URL, headers=headers, json=basic_data)
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"[AIRTABLE] ✅ Lead {lead_name} synced with basic fields only")
                logger.warning(f"[AIRTABLE] ⚠️  Missing business fields for {lead_name}: Email={lead.get('email', 'N/A')}, Company={lead.get('company', 'N/A')}, Title={lead.get('title', 'N/A')}")
                # Mark lead as processed to prevent future duplicates
                mark_lead_as_processed(lead)
                return True
            else:
                logger.error(f"[AIRTABLE] ❌ Failed to sync {lead_name} even with basic fields — HTTP {response.status_code}: {response.text}")
                save_failed_lead(lead)
                return False
        else:
            logger.error(f"[AIRTABLE] ❌ Failed to sync {lead_name} — HTTP {response.status_code}: {response.text}")
            save_failed_lead(lead)
            return False
    
    except Exception as e:
        logger.error(f"[AIRTABLE] ❌ Failed to sync {lead_name} — {str(e)}")
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
    
    lead_name = lead.get('full_name', lead.get('name', 'Unknown'))
    logger.info(f"[AIRTABLE] Lead {lead_name} saved to {FAILED_LEADS_FILE} for later retry")

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

def test_airtable_connection():
    """Test the Airtable connection with a sample lead"""
    logger.info("🧪 Testing Airtable connection...")
    
    # Create a test lead with all the business data you care about
    test_lead = {
        "full_name": "Test Business Lead",
        "linkedin_url": "https://linkedin.com/in/testbusinesslead",
        "company": "Test Corp",
        "title": "CEO",
        "email": "ceo@testcorp.com",
        "verified": True,
        "enriched": True,
        "source": "LinkedIn"
    }
    
    # Try to push the lead to Airtable
    result = push_lead_to_airtable(test_lead)
    
    if result:
        logger.info("✅ Test successful! Airtable integration working.")
    else:
        logger.warning("❌ Test failed. Check your Airtable configuration.")
    
    return result

if __name__ == "__main__":
    # Test the Airtable client
    test_airtable_connection()
    
    # Try to retry failed leads
    retried = retry_failed_leads()
    logger.info(f"Retried {retried} failed leads")