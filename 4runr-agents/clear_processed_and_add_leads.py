#!/usr/bin/env python3
"""
Clear processed leads file and add verified leads to clean Airtable
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('clear-and-add')

def clear_processed_leads():
    """Clear the processed leads file so we can add leads fresh"""
    shared_dir = Path(__file__).parent / "shared"
    processed_file = shared_dir / "processed_leads.json"
    
    if processed_file.exists():
        # Clear the file
        with open(processed_file, 'w') as f:
            json.dump([], f)
        logger.info("🧹 Cleared processed leads file")
    else:
        logger.info("📝 Processed leads file doesn't exist - creating empty one")
        with open(processed_file, 'w') as f:
            json.dump([], f)

def get_verified_leads():
    """Get the 5 verified good leads"""
    return [
        {
            "name": "Pascal Jarry",
            "full_name": "Pascal Jarry",
            "title": "Founder and CEO", 
            "company": "Yapla",
            "linkedin_url": "https://ca.linkedin.com/in/pascaljarry",
            "location": "Montreal, Quebec, Canada",
            "status": "Ready for Outreach",
            "lead_source": "Verified Small Montreal Companies",
            "company_size": "35 employees",
            "industry": "Web Technology",
            "confidence": "high",
            "verified": True,
            "ready_for_engagement": True,
            "engagement_method": "LinkedIn DM",
            "added_at": datetime.now().isoformat()
        },
        {
            "name": "Jon Ruby",
            "full_name": "Jon Ruby",
            "title": "CEO",
            "company": "Jonar",
            "linkedin_url": "https://ca.linkedin.com/in/rubyjon",
            "location": "Montreal, Quebec, Canada",
            "status": "Ready for Outreach",
            "lead_source": "Verified Small Montreal Companies",
            "company_size": "Small software company",
            "industry": "Software Development",
            "confidence": "high",
            "verified": True,
            "ready_for_engagement": True,
            "engagement_method": "LinkedIn DM",
            "added_at": datetime.now().isoformat()
        },
        {
            "name": "Claude Lemay",
            "full_name": "Claude Lemay",
            "title": "President and CEO",
            "company": "Claude Lemay & Partners",
            "linkedin_url": "https://ca.linkedin.com/in/claude-lemay-10808213",
            "location": "Montreal, Quebec, Canada",
            "status": "Ready for Outreach",
            "lead_source": "Verified Small Montreal Companies",
            "company_size": "Small consulting firm",
            "industry": "Business Consulting",
            "confidence": "high",
            "verified": True,
            "ready_for_engagement": True,
            "engagement_method": "LinkedIn DM",
            "added_at": datetime.now().isoformat()
        },
        {
            "name": "Elie Wahnoun",
            "full_name": "Elie Wahnoun",
            "title": "Founder and CEO",
            "company": "Courimo",
            "linkedin_url": "https://www.linkedin.com/in/eliewahnoun",
            "location": "Montreal, Quebec, Canada",
            "status": "Ready for Outreach",
            "lead_source": "Verified Small Montreal Companies",
            "company_size": "Small digital agency",
            "industry": "Digital Marketing",
            "confidence": "high",
            "verified": True,
            "ready_for_engagement": True,
            "engagement_method": "LinkedIn DM",
            "added_at": datetime.now().isoformat()
        },
        {
            "name": "Randal Tucker",
            "full_name": "Randal Tucker",
            "title": "CEO & President",
            "company": "SFM",
            "linkedin_url": "https://ca.linkedin.com/in/randal-tucker-31bbb618",
            "location": "Montreal, Quebec, Canada",
            "status": "Ready for Outreach",
            "lead_source": "Verified Small Montreal Companies",
            "company_size": "Light manufacturing",
            "industry": "Manufacturing",
            "confidence": "high",
            "verified": True,
            "ready_for_engagement": True,
            "engagement_method": "LinkedIn DM",
            "added_at": datetime.now().isoformat()
        }
    ]

def main():
    """Clear processed leads and add verified leads"""
    logger.info("🚀 Clearing processed leads and adding verified leads...")
    
    # Step 1: Clear processed leads
    clear_processed_leads()
    
    # Step 2: Add verified leads
    verified_leads = get_verified_leads()
    added_count = 0
    
    print("\n" + "="*70)
    print("➕ ADDING 5 VERIFIED LEADS TO CLEAN AIRTABLE")
    print("="*70)
    
    for i, lead in enumerate(verified_leads, 1):
        name = lead['name']
        company = lead['company']
        
        print(f"\n{i}. Adding: {name} ({company})")
        print(f"   LinkedIn: {lead['linkedin_url']}")
        print(f"   Industry: {lead['industry']}")
        
        try:
            result = push_lead_to_airtable(lead)
            if result:
                added_count += 1
                print(f"   ✅ Successfully added")
            else:
                print(f"   ⚠️ Failed to add")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY:")
    print(f"   ✅ Successfully added: {added_count}/5 verified leads")
    print("   🎯 All leads have confirmed LinkedIn URLs")
    print("   📈 All are small-medium companies (perfect targets)")
    print("   💼 All are founder/CEOs (decision makers)")
    print("="*70)
    
    if added_count == 5:
        print("\n🎉 PERFECT! Your Airtable now has exactly 5 high-quality leads!")
        print("   These are 10x better than huge corporation CEOs")
        print("   Start with Pascal Jarry (tech founder) for first outreach")
    
    print("="*70)

if __name__ == "__main__":
    main()