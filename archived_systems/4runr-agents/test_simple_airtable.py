#!/usr/bin/env python3
"""
Test Simple Airtable Integration
Focus on core business data: Name, Email, Company, Role, LinkedIn URL
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

print("🧪 Testing Simple Airtable Integration")
print("=" * 50)

# Test 1: Add record with only existing fields
print("📝 Test 1: Adding record with existing fields only...")
test_record_basic = {
    'fields': {
        'Full Name': 'John Smith',
        'LinkedIn URL': 'https://linkedin.com/in/johnsmith'
    }
}

response = requests.post(f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}', 
                        headers=headers, json=test_record_basic)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ SUCCESS: Basic record added")
    record_id = response.json().get('id')
    print(f"Record ID: {record_id}")
    
    # Clean up
    delete_response = requests.delete(f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}/{record_id}', 
                                     headers=headers)
    print(f"Cleanup status: {delete_response.status_code}")
else:
    print(f"❌ FAILED: {response.text}")

print()

# Test 2: Try to add more fields (this will likely fail but shows us what we need)
print("📝 Test 2: Trying to add business-critical fields...")
test_record_full = {
    'fields': {
        'Full Name': 'Jane Doe',
        'LinkedIn URL': 'https://linkedin.com/in/janedoe',
        'Email': 'jane@company.com',
        'Company': 'Acme Corp',
        'Title': 'CEO',
        'Status': 'New Lead',
        'Source': 'LinkedIn Scraper'
    }
}

response = requests.post(f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}', 
                        headers=headers, json=test_record_full)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ SUCCESS: Full record added")
    record_id = response.json().get('id')
    print(f"Record ID: {record_id}")
else:
    print(f"❌ EXPECTED FAILURE: {response.text}")
    print("This shows us which fields need to be added to Airtable")

print("\n🎯 Summary:")
print("For your business workflow, you need these fields in Airtable:")
print("✅ Full Name (exists)")
print("✅ LinkedIn URL (exists)")
print("❌ Email (needs to be added)")
print("❌ Company (needs to be added)")
print("❌ Title/Role (needs to be added)")
print("❌ Status (for enricher/engagement workflow)")
print("❌ Source (for tracking)")

print("\n💡 Next Steps:")
print("1. Add missing fields to your Airtable 'Table 1'")
print("2. Or work with existing fields and store additional data in JSON format")
print("3. Update the airtable_client.py to match your business needs")