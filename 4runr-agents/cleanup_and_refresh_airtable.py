#!/usr/bin/env python3
"""
Clean up Airtable - Remove old huge company CEOs and add good small company leads
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

# Import the Airtable client
from airtable_client import push_lead_to_airtable
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airtable-cleanup')

def get_huge_company_ceos():
    """List of huge company CEOs to remove from Airtable"""
    return [
        "Tobias Lütke",
        "Éric Martel", 
        "Guy Cormier",
        "Brian Hannasch",
        "Ian Edwards",
        "Marc Parent",
        "Laurent Ferreira",
        "Neil Rossy",
        "Philip Fayer",
        "Alain Bédard",
        "Sophie Brochu",
        "Eric La Flèche",
        "Lino Saputo Jr.",
        "Dax Dasilva",
        "George Schindler"
    ]

def load_promising_leads():
    """Load the promising small company leads"""
    shared_dir = Path(__file__).parent / "shared"
    leads_file = shared_dir / "promising_small_leads.json"
    
    if not leads_file.exists():
        logger.error("❌ promising_small_leads.json not found")
        return []
    
    with open(leads_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_airtable_records():
    """Get all records from Airtable"""
    try:
        # Get Airtable configuration
        AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
        AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
        AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
        
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {
            'Authorization': f'Bearer {AIRTABLE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('records', [])
        else:
            logger.error(f"❌ Failed to get records: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error getting records: {str(e)}")
        return []

def delete_airtable_record(record_id):
    """Delete a record from Airtable"""
    try:
        # Get Airtable configuration
        AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
        AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
        AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Table 1')
        
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
        headers = {
            'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        }
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"❌ Failed to delete record: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error deleting record: {str(e)}")
        return False

def cleanup_airtable():
    """Remove old huge company CEOs from Airtable"""
    logger.info("🧹 Starting Airtable cleanup...")
    
    try:
        # Get all current records
        all_records = get_airtable_records()
        logger.info(f"📋 Found {len(all_records)} total records in Airtable")
        
        huge_company_ceos = get_huge_company_ceos()
        deleted_count = 0
        
        for record in all_records:
            record_id = record.get('id')
            fields = record.get('fields', {})
            name = fields.get('Name', fields.get('Full Name', ''))
            company = fields.get('Company', '')
            
            # Check if this is a huge company CEO we want to remove
            if name in huge_company_ceos:
                logger.info(f"🗑️  Deleting: {name} ({company})")
                try:
                    delete_result = delete_airtable_record(record_id)
                    if delete_result:
                        deleted_count += 1
                        logger.info(f"✅ Deleted: {name}")
                    else:
                        logger.warning(f"⚠️ Failed to delete: {name}")
                except Exception as e:
                    logger.error(f"❌ Error deleting {name}: {str(e)}")
        
        logger.info(f"🧹 Cleanup complete: Deleted {deleted_count} huge company CEOs")
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        return 0

def add_promising_leads():
    """Add the new promising small company leads to Airtable"""
    logger.info("➕ Adding promising small company leads...")
    
    promising_leads = load_promising_leads()
    
    if not promising_leads:
        logger.error("❌ No promising leads found")
        return 0
    
    added_count = 0
    
    for lead in promising_leads:
        name = lead.get('full_name', '')
        company = lead.get('company', '')
        
        logger.info(f"➕ Adding: {name} ({company})")
        
        # Format lead for Airtable
        airtable_lead = {
            'name': name,
            'full_name': name,
            'title': lead.get('title', ''),
            'company': company,
            'linkedin_url': lead.get('linkedin_url', ''),
            'location': lead.get('location', 'Montreal, Quebec, Canada'),
            'status': 'Ready for Outreach',
            'lead_source': 'Small Montreal Companies Search',
            'company_size': lead.get('company_size', ''),
            'confidence': lead.get('confidence', ''),
            'why_good_target': lead.get('why_good', ''),
            'added_at': datetime.now().isoformat(),
            'ready_for_engagement': True
        }
        
        try:
            result = push_lead_to_airtable(airtable_lead)
            if result:
                added_count += 1
                logger.info(f"✅ Added: {name}")
            else:
                logger.warning(f"⚠️ Failed to add: {name}")
        except Exception as e:
            logger.error(f"❌ Error adding {name}: {str(e)}")
    
    logger.info(f"➕ Added {added_count} promising leads to Airtable")
    return added_count

def main():
    """Main function to cleanup and refresh Airtable"""
    logger.info("🚀 Starting Airtable cleanup and refresh...")
    
    print("\n" + "="*70)
    print("🧹 AIRTABLE CLEANUP & REFRESH")
    print("="*70)
    
    # Step 1: Remove old huge company CEOs
    print("\n1️⃣ REMOVING HUGE COMPANY CEOs (too big/unresponsive):")
    print("-" * 50)
    deleted_count = cleanup_airtable()
    
    # Step 2: Add promising small company leads
    print(f"\n2️⃣ ADDING PROMISING SMALL COMPANY LEADS:")
    print("-" * 50)
    added_count = add_promising_leads()
    
    # Summary
    print("\n" + "="*70)
    print("📊 CLEANUP SUMMARY:")
    print(f"   🗑️  Removed: {deleted_count} huge company CEOs")
    print(f"   ➕ Added: {added_count} promising small company leads")
    print(f"   📈 Net change: {added_count - deleted_count} leads")
    print("="*70)
    
    if added_count > 0:
        print("\n✅ SUCCESS! Your Airtable now has much better targets:")
        print("   • Small-medium companies (20-200 employees)")
        print("   • Founder/CEOs who are decision makers")
        print("   • Companies that actually need AI solutions")
        print("   • Much higher response rate expected")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Review the new leads in your Airtable")
    print("   2. Start with the high-confidence leads first")
    print("   3. Personalized LinkedIn outreach to these smaller companies")
    print("   4. Much better conversion potential!")

if __name__ == "__main__":
    main()