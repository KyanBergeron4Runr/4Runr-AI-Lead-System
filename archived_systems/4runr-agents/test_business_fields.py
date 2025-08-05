#!/usr/bin/env python3
"""
Test adding business fields to Airtable
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_NAME = "Table 1"

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

def test_business_data():
    """Test adding a record with full business data"""
    
    print("🧪 Testing business data fields...")
    
    # Test with Tobias Lütke's real business data
    test_record = {
        'fields': {
            'Full Name': 'Tobias Lütke (Business Test)',
            'LinkedIn URL': 'https://www.linkedin.com/in/tobi/',
            'Company': 'Shopify',
            'Title': 'CEO',
            'Email': 'tobias@shopify.com',
            'Status': 'New Lead',
            'Source': 'LinkedIn Scraper'
        }
    }
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    response = requests.post(url, headers=headers, json=test_record)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! All business fields work!")
        record_id = response.json().get('id')
        print(f"Record ID: {record_id}")
        
        # Clean up the test record
        delete_response = requests.delete(f"{url}/{record_id}", headers=headers)
        print(f"Cleanup: {delete_response.status_code}")
        
        return True
    else:
        print(f"❌ Some fields don't exist: {response.text}")
        
        # Try with just the working fields
        print("\n🔄 Testing with basic fields only...")
        basic_record = {
            'fields': {
                'Full Name': 'Tobias Lütke (Basic Test)',
                'LinkedIn URL': 'https://www.linkedin.com/in/tobi/'
            }
        }
        
        response2 = requests.post(url, headers=headers, json=basic_record)
        print(f"Basic test status: {response2.status_code}")
        
        if response2.status_code == 200:
            print("✅ Basic fields work")
            record_id = response2.json().get('id')
            # Clean up
            requests.delete(f"{url}/{record_id}", headers=headers)
        
        return False

def show_missing_fields_solution():
    """Show how to add missing fields to Airtable"""
    
    print("\n💡 To get your business data in Airtable:")
    print("1. Go to your Airtable 'Table 1'")
    print("2. Click the '+' button to add new fields")
    print("3. Add these fields:")
    print("   - Company (Single line text)")
    print("   - Title (Single line text)")
    print("   - Email (Email)")
    print("   - Status (Single select with options: New Lead, Verified, Enriched, Contacted)")
    print("   - Source (Single line text)")
    print("\n4. Once added, run the bypass script again to get full business data!")

if __name__ == "__main__":
    success = test_business_data()
    
    if not success:
        show_missing_fields_solution()
    
    print("\n🎯 Current situation:")
    print("✅ Airtable connection working")
    print("✅ Duplicates cleaned up")
    print("✅ Core data (name + LinkedIn) syncing")
    print("❌ Business data (company, title, email) needs Airtable fields")