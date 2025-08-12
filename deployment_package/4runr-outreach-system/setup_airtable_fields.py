#!/usr/bin/env python3
"""
Setup Airtable Fields

This script adds the required fields to the Airtable table for the
4Runr outreach system to function properly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from shared.airtable_client import get_airtable_client
from shared.config import config

def main():
    """Setup the required Airtable fields."""
    print("🔧 Setting up Airtable Fields")
    print("=" * 30)
    
    print("⚠️  IMPORTANT NOTE:")
    print("This script cannot automatically create fields in Airtable.")
    print("You need to manually add these fields to your Airtable table.")
    print()
    
    try:
        # Get Airtable configuration
        airtable_config = config.get_airtable_config()
        print(f"📋 Airtable Configuration:")
        print(f"   Base ID: {airtable_config['base_id']}")
        print(f"   Table: {airtable_config['table_name']}")
        print()
        
        # Define required fields
        required_fields = [
            {
                'name': 'Engagement_Status',
                'type': 'Single select',
                'options': ['Auto-Send', 'Sent', 'Skipped', 'Needs Review', 'Error'],
                'description': 'Current engagement status of the lead'
            },
            {
                'name': 'Email_Confidence_Level',
                'type': 'Single select', 
                'options': ['Real', 'Pattern', 'Guess'],
                'description': 'Confidence level of the email address validity'
            },
            {
                'name': 'Level Engaged',
                'type': 'Single select',
                'options': ['', '1st degree', '2nd degree', '3rd degree', 'retry'],
                'description': 'Current engagement level/degree of contact'
            },
            {
                'name': 'Company',
                'type': 'Single line text',
                'description': 'Company name'
            },
            {
                'name': 'Title',
                'type': 'Single line text',
                'description': 'Job title of the contact'
            },
            {
                'name': 'Custom_Message',
                'type': 'Long text',
                'description': 'Generated personalized message'
            },
            {
                'name': 'Message_Preview',
                'type': 'Long text',
                'description': 'Preview of the message (first 500 chars)'
            },
            {
                'name': 'Last_Contacted_Date',
                'type': 'Date',
                'description': 'Date when the lead was last contacted'
            },
            {
                'name': 'company_website_url',
                'type': 'URL',
                'description': 'Company website URL for scraping'
            },
            {
                'name': 'Company_Description',
                'type': 'Long text',
                'description': 'Description of the company from website scraping'
            },
            {
                'name': 'Top_Services',
                'type': 'Long text',
                'description': 'Top services offered by the company'
            },
            {
                'name': 'Tone',
                'type': 'Single select',
                'options': ['Bold', 'Formal', 'Friendly', 'Casual', 'Professional'],
                'description': 'Tone to use for messaging'
            },
            {
                'name': 'Website_Insights',
                'type': 'Long text',
                'description': 'Insights gathered from website scraping'
            },
            {
                'name': 'Delivery_Method',
                'type': 'Single select',
                'options': ['Email', 'LinkedIn DM', 'Skipped'],
                'description': 'Method used to deliver the message'
            }
        ]
        
        print("📝 Required Fields to Add to Airtable:")
        print("=" * 50)
        
        for i, field in enumerate(required_fields, 1):
            print(f"\n{i:2d}. Field Name: {field['name']}")
            print(f"    Type: {field['type']}")
            if 'options' in field:
                print(f"    Options: {', '.join(field['options'])}")
            print(f"    Description: {field['description']}")
        
        print(f"\n🔧 Manual Setup Instructions:")
        print("=" * 50)
        print("1. Go to your Airtable base: https://airtable.com/")
        print(f"2. Open the base with ID: {airtable_config['base_id']}")
        print(f"3. Go to the '{airtable_config['table_name']}' table")
        print("4. For each field above:")
        print("   a. Click the '+' button to add a new field")
        print("   b. Enter the exact field name (case-sensitive)")
        print("   c. Select the field type")
        print("   d. Add the options if it's a single select field")
        print("   e. Add the description")
        print()
        
        print("🎯 Critical Fields for Basic Functionality:")
        critical_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
        for field in critical_fields:
            print(f"   ✅ {field}")
        
        print(f"\n⚡ Quick Test After Setup:")
        print("Run this command to test the Airtable connection:")
        print("   python check_airtable_field_names.py")
        print()
        print("Then test the engager agent:")
        print("   python -m engager.enhanced_engager_agent --dry-run --limit 1")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)